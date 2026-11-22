"""Policies and evaluation for crew repair scheduling."""

from __future__ import annotations

import itertools
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.crew_schedule import ROLES, CrewScheduleConfig, CrewScheduleEnv
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class CrewPolicy(Protocol):
    name: str

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int: ...


class NoopPolicy:
    name = "noop"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return 0


class ImpactOnlyPolicy:
    name = "impact_only"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        available = [
            (info["roles"][role]["outage"], index + 1)
            for index, role in enumerate(ROLES)
            if mask[index + 1] and info["roles"][role]["outage"] > 0
        ]
        return max(available)[1] if available else 0


class NearestPolicy:
    name = "nearest"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        available = [
            (info["roles"][role]["distance"], index + 1)
            for index, role in enumerate(ROLES)
            if mask[index + 1] and info["roles"][role]["outage"] > 0
        ]
        return min(available)[1] if available else 0


class EarliestDeadlinePolicy:
    name = "earliest_deadline"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        available = [
            (info["roles"][role]["deadline"], index + 1)
            for index, role in enumerate(ROLES)
            if mask[index + 1] and info["roles"][role]["outage"] > 0
        ]
        return min(available)[1] if available else 0


class TravelAwarePolicy:
    name = "travel_aware"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        available = [
            (
                info["roles"][role]["outage"]
                / max(1, info["roles"][role]["service_ticks"]),
                index + 1,
            )
            for index, role in enumerate(ROLES)
            if mask[index + 1] and info["roles"][role]["outage"] > 0
        ]
        return max(available)[1] if available else 0


class RandomPolicy:
    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        legal = np.flatnonzero(mask)
        return int(self.rng.choice(legal.tolist())) if len(legal) else 0


class SequencePolicy:
    """Replay a precomputed service sequence; noop afterwards."""

    name = "oracle"

    def __init__(self, actions: tuple[int, ...]) -> None:
        self.actions = actions
        self.index = 0

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if self.index >= len(self.actions):
            return 0
        action = self.actions[self.index]
        if not mask[action]:
            return 0
        self.index += 1
        return action


class TabularQPolicy:
    name = "tabular_q"

    def __init__(self) -> None:
        self.q: dict[tuple[int, ...], np.ndarray] = {}

    def _key(self, info: dict[str, Any]) -> tuple[int, ...]:
        states = []
        for role in ROLES:
            wire = info["roles"][role]
            states.append(0 if not wire["degraded"] and not wire["failed"] else 1)
        small = info["roles"]["small"]
        large = info["roles"]["large"]
        return (
            min(2, int(info["budget_remaining"])),
            min(4, int(info["tick"]) // 100),
            *states,
            min(3, int(small["distance"]) // 5),
            min(3, int(large["distance"]) // 5),
        )

    def _values(self, key: tuple[int, ...]) -> np.ndarray:
        if key not in self.q:
            self.q[key] = np.zeros(4, dtype=np.float64)
        return self.q[key]

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        values = np.where(mask, self._values(self._key(info)), -np.inf)
        return int(np.argmax(values))

    def train(
        self,
        env: CrewScheduleEnv,
        episodes: int = 200,
        seed: int = 0,
        train_seed_start: int = 10000,
        alpha: float = 0.2,
        gamma: float = 0.95,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            try:
                observation, info = env.reset(
                    seed=train_seed_start + episode
                )
            except RuntimeError:
                continue
            done = False
            epsilon = 1.0 - 0.95 * episode / max(1, episodes - 1)
            while not done:
                mask = env.action_mask()
                key = self._key(info)
                if rng.random() < epsilon:
                    legal = np.flatnonzero(mask)
                    action = int(rng.choice(legal.tolist()))
                else:
                    action = self.act(observation, info, mask)
                observation, reward, terminated, truncated, info = env.step(
                    action
                )
                done = terminated or truncated
                next_key = self._key(info)
                target = reward
                if not done:
                    next_mask = env.action_mask()
                    target += gamma * float(
                        np.max(
                            np.where(
                                next_mask, self._values(next_key), -np.inf
                            )
                        )
                    )
                values = self._values(key)
                values[action] += alpha * (target - values[action])


class DeadlineQPolicy(TabularQPolicy):
    """Episodic Q with role distances and deadline buckets."""

    name = "deadline_q"

    def _key(self, info: dict[str, Any]) -> tuple[int, ...]:
        def state(role: str) -> int:
            wire = info["roles"][role]
            if wire["failed"]:
                return 2
            return 1 if wire["degraded"] else 0

        def deadline_bucket(role: str) -> int:
            wire = info["roles"][role]
            remaining = max(0, int(wire["deadline"]) - int(info["tick"]))
            return min(5, remaining // 20) if wire["degraded"] else 0

        return (
            min(2, int(info["budget_remaining"])),
            min(4, int(info["tick"]) // 50),
            state("loop"),
            state("small"),
            state("large"),
            min(3, int(info["roles"]["small"]["distance"]) // 5),
            min(3, int(info["roles"]["large"]["distance"]) // 5),
            deadline_bucket("small"),
            deadline_bucket("large"),
        )

    def train(
        self,
        env: CrewScheduleEnv,
        episodes: int = 500,
        seed: int = 0,
        train_seed_start: int = 20000,
        alpha: float = 0.2,
        gamma: float = 1.0,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            try:
                observation, info = env.reset(
                    seed=train_seed_start + episode
                )
            except RuntimeError:
                continue
            done = False
            epsilon = 1.0 - 0.95 * episode / max(1, episodes - 1)
            while not done:
                mask = env.action_mask()
                key = self._key(info)
                if rng.random() < epsilon:
                    legal = np.flatnonzero(mask)
                    action = int(rng.choice(legal.tolist()))
                else:
                    action = self.act(observation, info, mask)
                observation, reward, terminated, truncated, info = env.step(
                    action
                )
                done = terminated or truncated
                if done:
                    target = reward
                else:
                    next_key = self._key(info)
                    next_mask = env.action_mask()
                    target = reward + gamma * float(
                        np.max(
                            np.where(
                                next_mask,
                                self._values(next_key),
                                -np.inf,
                            )
                        )
                    )
                values = self._values(key)
                values[action] += alpha * (target - values[action])


@dataclass
class CrewMetrics:
    mean_score: float
    mean_reward: float
    mean_repairs: float
    mean_prevented: float
    mean_aborted: float
    mean_travel: float
    success_rate: float
    scores: list[float]
    rewards: list[float]


def evaluate_policy(
    env: CrewScheduleEnv,
    policy: CrewPolicy,
    episodes: int = 5,
    seed: int = 0,
) -> CrewMetrics:
    scores: list[float] = []
    rewards: list[float] = []
    repairs: list[float] = []
    prevented: list[float] = []
    aborted: list[float] = []
    travel: list[float] = []
    successes: list[float] = []
    for episode in range(episodes):
        observation, info = env.reset(seed=seed + episode)
        done = False
        total_reward = 0.0
        while not done:
            action = policy.act(observation, info, env.action_mask())
            observation, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            done = terminated or truncated
        scores.append(float(info["score"]))
        rewards.append(total_reward)
        repairs.append(float(info["repairs"]))
        prevented.append(float(info["prevented"]))
        aborted.append(float(info["aborted"]))
        travel.append(float(info["travel_ticks"]))
        successes.append(1.0 if info["success"] else 0.0)
    return CrewMetrics(
        mean_score=float(np.mean(scores)),
        mean_reward=float(np.mean(rewards)),
        mean_repairs=float(np.mean(repairs)),
        mean_prevented=float(np.mean(prevented)),
        mean_aborted=float(np.mean(aborted)),
        mean_travel=float(np.mean(travel)),
        success_rate=float(np.mean(successes)),
        scores=scores,
        rewards=rewards,
    )


def _pool(metrics: list[CrewMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    rewards = [value for item in metrics for value in item.rewards]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "mean_reward": float(np.mean(rewards)),
        "mean_repairs": float(np.mean([item.mean_repairs for item in metrics])),
        "mean_prevented": float(np.mean([item.mean_prevented for item in metrics])),
        "mean_aborted": float(np.mean([item.mean_aborted for item in metrics])),
        "mean_travel": float(np.mean([item.mean_travel for item in metrics])),
        "success_rate": float(np.mean([item.success_rate for item in metrics])),
        "per_seed": [
            {
                "scores": item.scores,
                "success_rate": item.success_rate,
                "prevented": item.mean_prevented,
                "aborted": item.mean_aborted,
                "travel": item.mean_travel,
            }
            for item in metrics
        ],
    }


def _run_sequence(
    env: CrewScheduleEnv,
    seed: int,
    actions: tuple[int, ...],
) -> float:
    observation, info = env.reset(seed=seed)
    done = False
    for action in actions:
        while not done and not env.action_mask()[action]:
            observation, _, terminated, truncated, info = env.step(0)
            done = terminated or truncated
        if done:
            break
        observation, _, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        if done:
            break
    while not done:
        observation, _, terminated, truncated, info = env.step(0)
        done = terminated or truncated
    return float(info["score"])


def _oracle_actions(
    env: CrewScheduleEnv,
    seed: int,
) -> tuple[int, ...]:
    candidates: list[tuple[int, ...]] = [()]
    candidates += [(action,) for action in (1, 2, 3)]
    candidates += list(itertools.permutations((1, 2, 3), 2))
    return max(candidates, key=lambda actions: _run_sequence(env, seed, actions))


def run_crew_schedule(
    config: FactoryConfig,
    crew: CrewScheduleConfig | None = None,
    *,
    episodes: int = 5,
    train_episodes: int = 200,
    seeds: tuple[int, ...] = (0, 1, 2),
    train_seed_start: int = 10000,
) -> dict[str, dict[str, Any]]:
    env = CrewScheduleEnv(config, crew)
    results: dict[str, dict[str, Any]] = {}
    for name, baseline in (
        ("noop", NoopPolicy()),
        ("impact_only", ImpactOnlyPolicy()),
        ("nearest", NearestPolicy()),
        ("earliest_deadline", EarliestDeadlinePolicy()),
        ("travel_aware", TravelAwarePolicy()),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, baseline, episodes=episodes, seed=seed)
                for seed in seeds
            ]
        )
    results["random"] = _pool(
        [
            evaluate_policy(
                env, RandomPolicy(seed=seed), episodes=episodes, seed=seed
            )
            for seed in seeds
        ]
    )
    oracle_metrics = []
    oracle_actions = {}
    for seed in seeds:
        action = _oracle_actions(env, seed)
        oracle_actions[str(seed)] = list(action)
        oracle_metrics.append(
            evaluate_policy(
                env,
                SequencePolicy(action),
                episodes=1,
                seed=seed,
            )
        )
    results["oracle"] = _pool(oracle_metrics)
    results["oracle"]["actions"] = oracle_actions
    q_metrics = []
    for seed in seeds:
        q_policy = TabularQPolicy()
        q_policy.train(
            env,
            episodes=train_episodes,
            seed=seed,
            train_seed_start=train_seed_start + seed * 1000,
        )
        q_metrics.append(
            evaluate_policy(env, q_policy, episodes=episodes, seed=seed)
        )
    results["tabular_q"] = _pool(q_metrics)
    deadline_metrics = []
    for seed in seeds:
        policy = DeadlineQPolicy()
        policy.train(
            env,
            episodes=train_episodes,
            seed=seed,
            train_seed_start=train_seed_start + seed * 1500,
        )
        deadline_metrics.append(
            evaluate_policy(env, policy, episodes=episodes, seed=seed)
        )
    results["deadline_q"] = _pool(deadline_metrics)
    return results


def write_crew_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"config": config, "results": results}
    (out / "crew_schedule_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Crew repair scheduling",
        "",
        f"Warning {config['warning_tick']}; failures "
        f"{config['loop_failure_tick']}/{config['small_failure_tick']}/"
        f"{config['large_failure_tick']}; budget {config['repair_budget']}.",
        "",
        "| policy | mean score | prevented | aborted | travel | success |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['mean_prevented']:.2f} | "
            f"{result['mean_aborted']:.2f} | "
            f"{result['mean_travel']:.1f} | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            "Oracle sequences: "
            + ", ".join(
                f"{seed}:{actions}"
                for seed, actions in results["oracle"].get(
                    "actions", {}
                ).items()
            ),
        ]
    )
    (out / "crew_schedule_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "crew_schedule_report.md"
