"""Policies and evaluation for preventive machine maintenance."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.preventive_fault import (
    PreventiveFaultConfig,
    PreventiveFaultEnv,
)
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class PreventiveFaultPolicy(Protocol):
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


class ThresholdPolicy:
    def __init__(self, threshold: float) -> None:
        self.threshold = threshold
        self.name = f"maintain_{threshold:.1f}"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if mask[1] and info["max_wear"] >= self.threshold * 20:
            return 1
        return 0


class AlwaysPolicy:
    name = "always"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return 1 if mask[1] else 0


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


class TabularQPolicy:
    name = "tabular_q"

    def __init__(self) -> None:
        self.q: dict[tuple[int, ...], np.ndarray] = {}

    def _key(self, info: dict[str, Any]) -> tuple[int, ...]:
        wear = float(info["max_wear"]) / 20.0
        if wear <= 0:
            bucket = 0
        elif wear < 0.5:
            bucket = 1
        elif wear < 0.7:
            bucket = 2
        elif wear < 0.9:
            bucket = 3
        else:
            bucket = 4
        return (
            bucket,
            min(2, int(info["faulted_count"])),
            int(info["maintenance_remaining"] > 0),
        )

    def _values(self, key: tuple[int, ...]) -> np.ndarray:
        if key not in self.q:
            self.q[key] = np.zeros(2, dtype=np.float64)
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
        env: PreventiveFaultEnv,
        episodes: int = 100,
        seed: int = 0,
        train_seed_start: int = 7000,
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
class PreventiveFaultMetrics:
    mean_score: float
    mean_reward: float
    mean_maintenance: float
    mean_faults: float
    success_rate: float
    scores: list[float]
    rewards: list[float]


def evaluate_policy(
    env: PreventiveFaultEnv,
    policy: PreventiveFaultPolicy,
    episodes: int = 5,
    seed: int = 0,
) -> PreventiveFaultMetrics:
    scores: list[float] = []
    rewards: list[float] = []
    maintenance: list[float] = []
    faults: list[float] = []
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
        maintenance.append(float(info["maintenance"]))
        faults.append(float(info["fault_events"]))
        successes.append(1.0 if info["success"] else 0.0)
    return PreventiveFaultMetrics(
        mean_score=float(np.mean(scores)),
        mean_reward=float(np.mean(rewards)),
        mean_maintenance=float(np.mean(maintenance)),
        mean_faults=float(np.mean(faults)),
        success_rate=float(np.mean(successes)),
        scores=scores,
        rewards=rewards,
    )


def _pool(metrics: list[PreventiveFaultMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    rewards = [value for item in metrics for value in item.rewards]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "mean_reward": float(np.mean(rewards)),
        "reward_ci": list(bootstrap_mean_ci(rewards)),
        "mean_maintenance": float(
            np.mean([item.mean_maintenance for item in metrics])
        ),
        "mean_faults": float(np.mean([item.mean_faults for item in metrics])),
        "success_rate": float(np.mean([item.success_rate for item in metrics])),
        "per_seed": [
            {
                "scores": item.scores,
                "success_rate": item.success_rate,
                "maintenance": item.mean_maintenance,
                "faults": item.mean_faults,
            }
            for item in metrics
        ],
    }


def run_preventive_fault(
    config: FactoryConfig,
    preventive: PreventiveFaultConfig | None = None,
    *,
    episodes: int = 5,
    train_episodes: int = 500,
    seeds: tuple[int, ...] = (0, 1, 2),
    train_seed_start: int = 7000,
) -> dict[str, dict[str, Any]]:
    env = PreventiveFaultEnv(config, preventive)
    results: dict[str, dict[str, Any]] = {}
    for name, baseline in (
        ("noop", NoopPolicy()),
        ("maintain_0.5", ThresholdPolicy(0.5)),
        ("maintain_0.7", ThresholdPolicy(0.7)),
        ("maintain_0.9", ThresholdPolicy(0.9)),
        ("always", AlwaysPolicy()),
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
    return results


def write_preventive_fault_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"config": config, "results": results}
    (out / "preventive_fault_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Preventive machine maintenance",
        "",
        f"Wear threshold {config['fault_threshold']}; repair "
        f"{config['repair_ticks']} ticks; maintenance "
        f"{config['maintenance_ticks']} ticks; success ≥ "
        f"{config['success_score']}.",
        "",
        "| policy | mean score | maintenance | faults | success |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['mean_maintenance']:.2f} | "
            f"{result['mean_faults']:.2f} | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            "Maintenance resets wear and takes the machine offline; waiting "
            "leads to a fault and a longer auto-repair.",
        ]
    )
    (out / "preventive_fault_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "preventive_fault_report.md"
