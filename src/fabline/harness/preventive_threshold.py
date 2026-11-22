"""Bandit policies for maintenance-threshold selection."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.preventive_threshold import (
    PreventiveThresholdEnv,
    ThresholdConfig,
)
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class ThresholdPolicy(Protocol):
    name: str

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int: ...


class FixedThresholdPolicy:
    def __init__(self, arm: int) -> None:
        self.arm = arm
        self.name = f"fixed_{arm}"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return self.arm


class UCBPolicy:
    name = "ucb"

    def __init__(self) -> None:
        self.counts: np.ndarray | None = None
        self.means: np.ndarray | None = None
        self.arm = 0

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        assert self.counts is not None
        assert self.means is not None
        untried = np.flatnonzero(self.counts == 0)
        if len(untried):
            return int(untried[0])
        total = int(self.counts.sum())
        scores = self.means + np.sqrt(
            2.0 * math.log(max(1, total)) / self.counts
        )
        return int(np.argmax(scores))

    def train(
        self,
        env: PreventiveThresholdEnv,
        episodes: int = 50,
        train_seed_start: int = 9000,
    ) -> None:
        self.counts = np.zeros(env.n_actions, dtype=np.float64)
        self.means = np.zeros(env.n_actions, dtype=np.float64)
        for episode in range(episodes):
            observation, info = env.reset(
                seed=train_seed_start + episode
            )
            action = self.act(observation, info, env.action_mask())
            _, reward, _, _, _ = env.step(action)
            self.counts[action] += 1
            self.means[action] += (
                reward - self.means[action]
            ) / self.counts[action]
        assert self.means is not None
        self.arm = int(np.argmax(self.means))


class EpsilonGreedyPolicy:
    name = "epsilon_greedy"

    def __init__(self, epsilon: float = 0.1, seed: int = 0) -> None:
        self.epsilon = epsilon
        self.rng = random.Random(seed)
        self.counts: np.ndarray | None = None
        self.means: np.ndarray | None = None
        self.arm = 0

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        assert self.means is not None
        if self.rng.random() < self.epsilon:
            return self.rng.randrange(len(self.means))
        return int(np.argmax(self.means))

    def train(
        self,
        env: PreventiveThresholdEnv,
        episodes: int = 50,
        train_seed_start: int = 9000,
    ) -> None:
        self.counts = np.zeros(env.n_actions, dtype=np.float64)
        self.means = np.zeros(env.n_actions, dtype=np.float64)
        for episode in range(episodes):
            observation, info = env.reset(
                seed=train_seed_start + episode
            )
            action = self.act(observation, info, env.action_mask())
            _, reward, _, _, _ = env.step(action)
            self.counts[action] += 1
            self.means[action] += (
                reward - self.means[action]
            ) / self.counts[action]
        assert self.means is not None
        self.arm = int(np.argmax(self.means))


@dataclass
class ArmMetrics:
    scores: list[float]
    successes: list[float]
    maintenance: list[float]
    faults: list[float]

    @property
    def mean_score(self) -> float:
        return float(np.mean(self.scores))


def evaluate_arm(
    env: PreventiveThresholdEnv,
    arm: int,
    seeds: tuple[int, ...],
) -> ArmMetrics:
    scores: list[float] = []
    successes: list[float] = []
    maintenance: list[float] = []
    faults: list[float] = []
    for seed in seeds:
        env.reset(seed)
        _, reward, _, _, info = env.step(arm)
        scores.append(float(reward))
        successes.append(1.0 if info["success"] else 0.0)
        maintenance.append(float(info["maintenance"]))
        faults.append(float(info["fault_events"]))
    return ArmMetrics(scores, successes, maintenance, faults)


def run_threshold_selection(
    config: FactoryConfig,
    threshold: ThresholdConfig | None = None,
    *,
    episodes: int = 50,
    seeds: tuple[int, ...] = (700, 701, 702, 703, 704),
    train_seed_start: int = 9000,
) -> dict[str, Any]:
    env = PreventiveThresholdEnv(config, threshold)
    arms = list(env.threshold.arms)
    rows: dict[str, dict[str, Any]] = {}
    for arm, value in enumerate(arms):
        metrics = evaluate_arm(env, arm, seeds)
        rows[str(value)] = {
            "mean_score": metrics.mean_score,
            "score_ci": list(bootstrap_mean_ci(metrics.scores)),
            "success_rate": float(np.mean(metrics.successes)),
            "maintenance": float(np.mean(metrics.maintenance)),
            "faults": float(np.mean(metrics.faults)),
        }
    best_arm = max(
        range(len(arms)),
        key=lambda arm: float(rows[str(arms[arm])]["mean_score"]),
    )
    ucb = UCBPolicy()
    ucb.train(env, episodes=episodes, train_seed_start=train_seed_start)
    epsilon = EpsilonGreedyPolicy()
    epsilon.train(
        env, episodes=episodes, train_seed_start=train_seed_start
    )
    learners = {}
    for policy in (ucb, epsilon):
        metrics = evaluate_arm(env, policy.arm, seeds)
        learners[policy.name] = {
            "arm": arms[policy.arm],
            "arm_index": policy.arm,
            "mean_score": metrics.mean_score,
            "score_ci": list(bootstrap_mean_ci(metrics.scores)),
            "success_rate": float(np.mean(metrics.successes)),
            "maintenance": float(np.mean(metrics.maintenance)),
            "faults": float(np.mean(metrics.faults)),
        }
    return {
        "arms": rows,
        "best_arm": arms[best_arm],
        "learners": learners,
        "training_episodes": episodes,
        "train_seed_start": train_seed_start,
        "seeds": list(seeds),
    }


def write_threshold_report(
    out: str | Path,
    payload: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "threshold_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Maintenance-threshold selection",
        "",
        f"Training episodes: {payload['training_episodes']}; "
        f"evaluation seeds: {payload['seeds']}.",
        "",
        "| threshold | mean score | maintenance | faults | success |",
        "|---:|---:|---:|---:|---:|",
    ]
    for value, row in payload["arms"].items():
        lines.append(
            f"| {value} | {row['mean_score']:.2f} | "
            f"{row['maintenance']:.2f} | {row['faults']:.2f} | "
            f"{row['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            f"Best fixed arm: **{payload['best_arm']}**.",
            "",
            "| learner | arm | mean score | success |",
            "|---|---:|---:|---:|",
        ]
    )
    for name, row in payload["learners"].items():
        lines.append(
            f"| {name} | {row['arm']} | {row['mean_score']:.2f} | "
            f"{row['success_rate']:.2f} |"
        )
    (out / "threshold_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "threshold_report.md"
