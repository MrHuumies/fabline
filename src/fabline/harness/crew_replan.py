"""Policies and evaluation for the crew recall/replanning task."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.crew_replan import CrewReplanConfig, CrewReplanEnv
from fabline.env.multi_crew import CHOICES, ROLES
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class CrewReplanPolicy(Protocol):
    name: str

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int: ...


def _orphan_action(info: dict[str, Any], mask: np.ndarray) -> int:
    if info["phase"] != "replan":
        return 0
    choices = [
        role
        for role in ROLES
        if info["roles"][role]["outage"] > 0
        and mask[(ROLES.index(role) + 1) * CHOICES]
    ]
    if not choices:
        return 0
    role = max(
        choices,
        key=lambda item: (
            info["roles"][item]["outage"],
            -info["roles"][item]["deadline"],
        ),
    )
    return (ROLES.index(role) + 1) * CHOICES


class NoopPolicy:
    name = "noop"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return 0


class SingleEDFPolicy:
    name = "single_edf"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "replan":
            return 0
        available = [
            (info["roles"][role]["deadline"], index + 1)
            for index, role in enumerate(ROLES)
            if info["roles"][role]["outage"] > 0
            and info["roles"][role]["degraded"]
        ]
        first = min(available)[1] if available else 0
        return first * CHOICES


class ParallelNearestPolicy:
    name = "parallel_nearest"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "replan":
            if info["orphaned_role"] is None:
                return 0
            roles = [
                role
                for role in ROLES
                if info["roles"][role]["outage"] > 0
                and (
                    info["roles"][role]["degraded"]
                    or info["roles"][role]["failed"]
                )
            ]
            if not roles:
                return 0
            role = min(
                roles, key=lambda item: info["roles"][item]["distance_a"]
            )
            return (ROLES.index(role) + 1) * CHOICES
        roles = [
            role
            for role in ROLES
            if info["roles"][role]["outage"] > 0
            and info["roles"][role]["degraded"]
        ]
        if not roles:
            return 0
        first = min(
            roles, key=lambda role: info["roles"][role]["distance_a"]
        )
        remaining = [role for role in roles if role != first]
        second = (
            min(
                remaining,
                key=lambda role: info["roles"][role]["distance_b"],
            )
            if remaining
            else None
        )
        return (ROLES.index(first) + 1) * CHOICES + (
            ROLES.index(second) + 1 if second is not None else 0
        )


class ParallelGreedyPolicy:
    name = "parallel_greedy"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "replan":
            if info["orphaned_role"] is None:
                return 0
            best = (0.0, 0)
            for role in ROLES:
                wire = info["roles"][role]
                value = wire["outage"] / max(1, wire["service_a"])
                action = (ROLES.index(role) + 1) * CHOICES
                if mask[action] and value > best[0]:
                    best = (value, action)
            return best[1]
        roles = [
            role
            for role in ROLES
            if info["roles"][role]["outage"] > 0
            and info["roles"][role]["degraded"]
        ]
        best = (0.0, 0)
        for first in [0, *[ROLES.index(role) + 1 for role in roles]]:
            for second in [0, *[ROLES.index(role) + 1 for role in roles]]:
                if first > 0 and first == second:
                    continue
                action = first * CHOICES + second
                if not mask[action]:
                    continue
                value = 0.0
                if first > 0:
                    wire = info["roles"][ROLES[first - 1]]
                    value += wire["outage"] / max(1, wire["service_a"])
                if second > 0:
                    wire = info["roles"][ROLES[second - 1]]
                    value += wire["outage"] / max(1, wire["service_b"])
                if value > best[0]:
                    best = (value, action)
        return best[1]


class RecallAwarePolicy:
    """Crew A takes the earliest bridge; crew B takes the other one."""

    name = "recall_aware"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "replan":
            return _orphan_action(info, mask)
        positives = [
            role
            for role in ROLES
            if info["roles"][role]["outage"] > 0
            and info["roles"][role]["degraded"]
        ]
        if not positives:
            return 0
        first = min(
            positives, key=lambda role: info["roles"][role]["deadline"]
        )
        remaining = [role for role in positives if role != first]
        second = remaining[0] if remaining else None
        return (ROLES.index(first) + 1) * CHOICES + (
            ROLES.index(second) + 1 if second is not None else 0
        )


class NoReplanPolicy:
    name = "recall_aware_no_replan"

    def __init__(self, initial: CrewReplanPolicy) -> None:
        self.initial = initial

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "replan":
            return 0
        return self.initial.act(observation, info, mask)


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


class FixedTwoPolicy:
    name = "fixed_two"

    def __init__(self, initial: int, replan: int) -> None:
        self.initial = initial
        self.replan = replan

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "initial":
            return self.initial if mask[self.initial] else 0
        return self.replan if mask[self.replan] else 0


class TabularQPolicy:
    name = "tabular_q"

    def __init__(self, scripted_replan: bool = False) -> None:
        self.q: dict[tuple[int, ...], np.ndarray] = {}
        self.scripted_replan = scripted_replan

    def _key(self, info: dict[str, Any]) -> tuple[int, ...]:
        def state(role: str) -> int:
            wire = info["roles"][role]
            if wire["failed"]:
                return 2
            return 1 if wire["degraded"] else 0

        small = info["roles"]["small"]
        large = info["roles"]["large"]
        orphan = info["orphaned_role"]
        return (
            1 if info["phase"] == "replan" else 0,
            min(4, int(info["tick"]) // 50),
            state("loop"),
            state("small"),
            state("large"),
            min(3, int(small["distance_a"]) // 5),
            min(3, int(small["distance_b"]) // 5),
            min(3, int(large["distance_a"]) // 5),
            min(3, int(large["distance_b"]) // 5),
            1 if info["crew_b_available"] else 0,
            min(
                3,
                max(0, int(info["recall_tick"]) - int(info["tick"])) // 10,
            ),
            -1 if orphan is None else ROLES.index(orphan),
        )

    def _values(self, key: tuple[int, ...]) -> np.ndarray:
        if key not in self.q:
            self.q[key] = np.zeros(16, dtype=np.float64)
        return self.q[key]

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if self.scripted_replan and info["phase"] == "replan":
            return _orphan_action(info, mask)
        values = np.where(mask, self._values(self._key(info)), -np.inf)
        return int(np.argmax(values))

    def train(
        self,
        env: CrewReplanEnv,
        episodes: int = 500,
        seed: int = 0,
        train_seed_start: int = 45000,
        alpha: float = 0.2,
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
                    target = reward + float(
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
class CrewReplanMetrics:
    mean_score: float
    mean_reward: float
    mean_prevented: float
    mean_aborted: float
    mean_b_aborted: float
    mean_travel: float
    success_rate: float
    scores: list[float]
    rewards: list[float]
    replan_actions: list[int]


def evaluate_policy(
    env: CrewReplanEnv,
    policy: CrewReplanPolicy,
    episodes: int = 5,
    seed: int = 0,
) -> CrewReplanMetrics:
    scores: list[float] = []
    rewards: list[float] = []
    prevented: list[float] = []
    aborted: list[float] = []
    b_aborted: list[float] = []
    travel: list[float] = []
    successes: list[float] = []
    replan_actions: list[int] = []
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
        prevented.append(float(info["prevented"]))
        aborted.append(float(info["aborted"]))
        b_aborted.append(float(info["b_aborted"]))
        travel.append(float(info["travel_ticks"]))
        successes.append(1.0 if info["success"] else 0.0)
        replan_actions.append(int(info["replan_action"]))
    return CrewReplanMetrics(
        mean_score=float(np.mean(scores)),
        mean_reward=float(np.mean(rewards)),
        mean_prevented=float(np.mean(prevented)),
        mean_aborted=float(np.mean(aborted)),
        mean_b_aborted=float(np.mean(b_aborted)),
        mean_travel=float(np.mean(travel)),
        success_rate=float(np.mean(successes)),
        scores=scores,
        rewards=rewards,
        replan_actions=replan_actions,
    )


def _pool(metrics: list[CrewReplanMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "min_score": float(np.min(scores)),
        "max_score": float(np.max(scores)),
        "mean_reward": float(np.mean([item.mean_reward for item in metrics])),
        "mean_prevented": float(
            np.mean([item.mean_prevented for item in metrics])
        ),
        "mean_aborted": float(
            np.mean([item.mean_aborted for item in metrics])
        ),
        "mean_b_aborted": float(
            np.mean([item.mean_b_aborted for item in metrics])
        ),
        "mean_travel": float(
            np.mean([item.mean_travel for item in metrics])
        ),
        "success_rate": float(
            np.mean([item.success_rate for item in metrics])
        ),
        "per_seed": [
            {
                "scores": item.scores,
                "replan_actions": item.replan_actions,
                "success_rate": item.success_rate,
                "prevented": item.mean_prevented,
                "aborted": item.mean_aborted,
                "b_aborted": item.mean_b_aborted,
                "travel": item.mean_travel,
            }
            for item in metrics
        ],
    }


def _run_fixed(
    env: CrewReplanEnv,
    seed: int,
    initial: int,
    replan: int,
) -> float:
    metrics = evaluate_policy(
        env,
        FixedTwoPolicy(initial, replan),
        episodes=1,
        seed=seed,
    )
    return metrics.mean_score


def _oracle_pair(env: CrewReplanEnv, seed: int) -> tuple[int, int]:
    best = (-1.0, 0, 0)
    for initial in range(env.n_actions):
        for replan in range(CHOICES):
            score = _run_fixed(env, seed, initial, replan * CHOICES)
            if score > best[0]:
                best = (score, initial, replan * CHOICES)
    return best[1], best[2]


def run_crew_replan(
    config: FactoryConfig,
    replan: CrewReplanConfig | None = None,
    *,
    train_episodes: int = 500,
    seeds: tuple[int, ...] = (0, 1, 2),
    q_seeds: tuple[int, ...] = (0, 1, 2, 3, 4),
    train_seed_start: int = 45000,
) -> dict[str, dict[str, Any]]:
    env = CrewReplanEnv(config, replan)
    results: dict[str, dict[str, Any]] = {}
    for name, baseline in (
        ("noop", NoopPolicy()),
        ("single_edf", SingleEDFPolicy()),
        ("parallel_nearest", ParallelNearestPolicy()),
        ("parallel_greedy", ParallelGreedyPolicy()),
        ("recall_aware", RecallAwarePolicy()),
        (
            "recall_aware_no_replan",
            NoReplanPolicy(RecallAwarePolicy()),
        ),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, baseline, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    results["random"] = _pool(
        [
            evaluate_policy(
                env, RandomPolicy(seed=seed), episodes=1, seed=seed
            )
            for seed in seeds
        ]
    )
    oracle_metrics = []
    oracle_actions: dict[str, list[int]] = {}
    for seed in seeds:
        initial, replan_action = _oracle_pair(env, seed)
        oracle_actions[str(seed)] = [initial, replan_action]
        oracle_metrics.append(
            evaluate_policy(
                env,
                FixedTwoPolicy(initial, replan_action),
                episodes=1,
                seed=seed,
            )
        )
    results["oracle"] = _pool(oracle_metrics)
    results["oracle"]["actions"] = oracle_actions
    q_metrics = []
    for q_seed in q_seeds:
        policy = TabularQPolicy()
        policy.train(
            env,
            episodes=train_episodes,
            seed=q_seed,
            train_seed_start=train_seed_start + q_seed * 1000,
        )
        q_metrics.extend(
            [
                evaluate_policy(env, policy, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    results["tabular_q"] = _pool(q_metrics)
    return results


def write_crew_replan_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "crew_replan_results.json").write_text(
        json.dumps(
            {"config": config, "results": results},
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Crew recall and replanning",
        "",
        f"Warning {config['warning_tick']}; failures "
        f"{config['loop_failure_tick']}/{config['small_failure_tick']}/"
        f"{config['large_failure_tick']}; recall {config['recall_tick']}.",
        "",
        "| policy | mean score | 95% CI | min | max | success | B aborted | replan |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in (
        "noop",
        "single_edf",
        "random",
        "parallel_nearest",
        "parallel_greedy",
        "recall_aware",
        "recall_aware_no_replan",
        "tabular_q",
        "oracle",
    ):
        result = results[name]
        replans = [
            action
            for item in result["per_seed"]
            for action in item["replan_actions"]
            if action > 0
        ]
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['min_score']:.0f} | {result['max_score']:.0f} | "
            f"{result['success_rate']:.2f} | "
            f"{result['mean_b_aborted']:.2f} | "
            f"{len(replans)} |"
        )
    lines.extend(["", "Oracle actions (initial, replan):"])
    for seed, actions in results["oracle"].get("actions", {}).items():
        lines.append(f"- {seed}: {actions}")
    (out / "crew_replan_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "crew_replan_report.md"
