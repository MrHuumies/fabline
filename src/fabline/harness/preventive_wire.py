"""Policies and evaluation for preventive wire maintenance."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.preventive_wire import PreventiveWireConfig, PreventiveWireEnv
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class PreventiveWirePolicy(Protocol):
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


class PreventivePolicy:
    name = "preventive"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if mask[1] and info["degraded"] and not info["failed"]:
            return 1
        return 0


class ReactivePolicy:
    name = "reactive"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if mask[1] and info["failed"]:
            return 1
        return 0


class LatePolicy:
    """Start after the warning window has shrunk too far."""

    name = "late"

    def __init__(self, delay: int = 40) -> None:
        self.delay = delay

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if (
            mask[1]
            and info["degraded"]
            and not info["failed"]
            and info["tick"] >= 60 + self.delay
            and not info["repaired"]
        ):
            return 1
        return 0


class RandomPreventivePolicy:
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


class TabularQPreventivePolicy:
    name = "tabular_q"

    def __init__(self) -> None:
        self.q: dict[tuple[int, ...], np.ndarray] = {}

    def _key(self, info: dict[str, Any]) -> tuple[int, ...]:
        return (
            int(info["degraded"]),
            int(info["failed"]),
            min(9, int(info["tick"]) // 50),
            int(info["repairs"]),
            int(info["repaired"]),
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
        env: PreventiveWireEnv,
        episodes: int = 200,
        seed: int = 0,
        train_seed_start: int = 6000,
        alpha: float = 0.2,
        gamma: float = 0.95,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            try:
                observation, info = env.reset(
                    seed=train_seed_start + episode
                )
            except RuntimeError:
                # Layouts without a single-wire bridge have no preventive task.
                continue
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
class PreventiveWireMetrics:
    mean_score: float
    mean_reward: float
    mean_prevented: float
    mean_aborted: float
    success_rate: float
    scores: list[float]
    rewards: list[float]


def evaluate_policy(
    env: PreventiveWireEnv,
    policy: PreventiveWirePolicy,
    episodes: int = 5,
    seed: int = 0,
) -> PreventiveWireMetrics:
    scores: list[float] = []
    rewards: list[float] = []
    prevented: list[float] = []
    aborted: list[float] = []
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
        prevented.append(float(info["prevented"]))
        aborted.append(float(info["aborted"]))
        successes.append(1.0 if info["success"] else 0.0)
    return PreventiveWireMetrics(
        mean_score=float(np.mean(scores)),
        mean_reward=float(np.mean(rewards)),
        mean_prevented=float(np.mean(prevented)),
        mean_aborted=float(np.mean(aborted)),
        success_rate=float(np.mean(successes)),
        scores=scores,
        rewards=rewards,
    )


def _pool(metrics: list[PreventiveWireMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    rewards = [value for item in metrics for value in item.rewards]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "mean_reward": float(np.mean(rewards)),
        "reward_ci": list(bootstrap_mean_ci(rewards)),
        "mean_prevented": float(
            np.mean([item.mean_prevented for item in metrics])
        ),
        "mean_aborted": float(
            np.mean([item.mean_aborted for item in metrics])
        ),
        "success_rate": float(np.mean([item.success_rate for item in metrics])),
        "per_seed": [
            {
                "scores": item.scores,
                "success_rate": item.success_rate,
                "prevented": item.mean_prevented,
                "aborted": item.mean_aborted,
            }
            for item in metrics
        ],
    }


def run_preventive_wire(
    config: FactoryConfig,
    preventive: PreventiveWireConfig | None = None,
    *,
    episodes: int = 5,
    train_episodes: int = 200,
    seeds: tuple[int, ...] = (0, 1, 2),
    train_seed_start: int = 6000,
) -> dict[str, dict[str, Any]]:
    env = PreventiveWireEnv(config, preventive)
    results: dict[str, dict[str, Any]] = {}
    for name, baseline in (
        ("noop", NoopPolicy()),
        ("preventive", PreventivePolicy()),
        ("reactive", ReactivePolicy()),
        ("late", LatePolicy()),
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
                RandomPreventivePolicy(seed=seed),
                episodes=episodes,
                seed=seed,
            )
            for seed in seeds
        ]
    )
    q_metrics = []
    for seed in seeds:
        q_policy = TabularQPreventivePolicy()
        q_policy.train(
            env,
            episodes=train_episodes,
            seed=seed,
            train_seed_start=train_seed_start + seed * 500,
        )
        q_metrics.append(
            evaluate_policy(env, q_policy, episodes=episodes, seed=seed)
        )
    results["tabular_q"] = _pool(q_metrics)
    return results


def write_preventive_wire_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"config": config, "results": results}
    (out / "preventive_wire_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Preventive wire maintenance",
        "",
        f"Warning {config['warning_tick']}; failure "
        f"{config['failure_tick']}; repair {config['repair_ticks']} ticks; "
        f"budget {config['repair_budget']}; success ≥ "
        f"{config['success_score']}.",
        "",
        "| policy | mean score | prevented | aborted | success |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['mean_prevented']:.2f} | "
            f"{result['mean_aborted']:.2f} | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            "Preventive repair starts at the warning; late repair aborts when "
            "the wire fails mid-job.",
        ]
    )
    (out / "preventive_wire_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "preventive_wire_report.md"
