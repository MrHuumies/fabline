"""Policies and evaluation for wired-wire repair control."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.wire_repair import WireRepairConfig, WireRepairEnv
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class WireRepairPolicy(Protocol):
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


class RepairNowPolicy:
    name = "repair_now"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return 1 if mask[1] else 0


class RepairLargestPolicy:
    """Repair the highest-impact failed wire, but never a zero-impact loop."""

    name = "repair_largest"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        outages = info["slot_outages"]
        if mask[1] and outages and outages[0] > 0:
            return 1
        return 0


class RandomWireRepairPolicy:
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


class TabularQWireRepairPolicy:
    name = "tabular_q"

    def __init__(self) -> None:
        self.q: dict[tuple[int, ...], np.ndarray] = {}

    def _key(self, info: dict[str, Any]) -> tuple[int, ...]:
        outages = list(info["slot_outages"])[:3]
        outages += [0] * (3 - len(outages))
        return (
            min(2, int(info["budget_remaining"])),
            min(3, int(info["failed_count"])),
            min(9, int(info["tick"]) // 50),
            *(min(3, int(value)) for value in outages),
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
        env: WireRepairEnv,
        episodes: int = 100,
        seed: int = 0,
        train_seed_start: int = 1000,
        alpha: float = 0.2,
        gamma: float = 0.95,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            observation, info = env.reset(
                seed=train_seed_start + episode
            )
            done = False
            epsilon = epsilon_start + (epsilon_end - epsilon_start) * (
                episode / max(1, episodes - 1)
            )
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


@dataclass
class WireRepairMetrics:
    mean_score: float
    mean_reward: float
    mean_repairs: float
    mean_wasted: float
    success_rate: float
    scores: list[float]
    rewards: list[float]


def evaluate_policy(
    env: WireRepairEnv,
    policy: WireRepairPolicy,
    episodes: int = 5,
    seed: int = 0,
) -> WireRepairMetrics:
    scores: list[float] = []
    rewards: list[float] = []
    repairs: list[float] = []
    wasted: list[float] = []
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
        wasted.append(float(info["wasted_repairs"]))
        successes.append(1.0 if info["success"] else 0.0)
    return WireRepairMetrics(
        mean_score=float(np.mean(scores)),
        mean_reward=float(np.mean(rewards)),
        mean_repairs=float(np.mean(repairs)),
        mean_wasted=float(np.mean(wasted)),
        success_rate=float(np.mean(successes)),
        scores=scores,
        rewards=rewards,
    )


def _pool(metrics: list[WireRepairMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    rewards = [value for item in metrics for value in item.rewards]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "mean_reward": float(np.mean(rewards)),
        "reward_ci": list(bootstrap_mean_ci(rewards)),
        "mean_repairs": float(np.mean([item.mean_repairs for item in metrics])),
        "mean_wasted": float(np.mean([item.mean_wasted for item in metrics])),
        "success_rate": float(np.mean([item.success_rate for item in metrics])),
        "per_seed": [
            {
                "scores": item.scores,
                "success_rate": item.success_rate,
                "wasted": item.mean_wasted,
                "repairs": item.mean_repairs,
            }
            for item in metrics
        ],
    }


def run_wire_repair(
    config: FactoryConfig,
    repair: WireRepairConfig | None = None,
    *,
    episodes: int = 5,
    train_episodes: int = 100,
    seeds: tuple[int, ...] = (0, 1, 2),
    train_seed_start: int = 1000,
) -> dict[str, dict[str, Any]]:
    env = WireRepairEnv(config, repair)
    results: dict[str, dict[str, Any]] = {}
    for name, baseline in (
        ("noop", NoopPolicy()),
        ("repair_now", RepairNowPolicy()),
        ("repair_largest", RepairLargestPolicy()),
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
                env,
                RandomWireRepairPolicy(seed=seed),
                episodes=episodes,
                seed=seed,
            )
            for seed in seeds
        ]
    )
    q_metrics = []
    for seed in seeds:
        q_policy = TabularQWireRepairPolicy()
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
    return results


def write_wire_repair_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"config": config, "results": results}
    (out / "wire_repair_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Wire-repair control",
        "",
        f"Budget: {config['repair_budget']}; success ≥ "
        f"{config['success_score']}; fault ticks {config['fault_ticks']}.",
        "",
        "| policy | mean score | mean repairs | wasted | success |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['mean_repairs']:.2f} | {result['mean_wasted']:.2f} | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            "Slots are ranked by restoration impact. Repairing a zero-impact "
            "loop wastes a repair.",
        ]
    )
    (out / "wire_repair_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "wire_repair_report.md"
