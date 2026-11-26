"""Baselines for the production-mix pilot."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.production_mix import ProductionMixConfig, ProductionMixEnv
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class ProductionPolicy(Protocol):
    name: str

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
    ) -> int: ...


class FixedPolicy:
    def __init__(self, recipe: int) -> None:
        self.recipe = recipe
        self.name = "always_gear" if recipe == 0 else "always_component"

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        return self.recipe


class AlternationPolicy:
    def __init__(self, period: int) -> None:
        if period <= 0:
            raise ValueError("period must be positive")
        self.period = period
        self.name = f"alternate_{period}"

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        return (int(info["tick"]) // 10 // self.period) % 2


class RandomPolicy:
    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        return self.rng.randrange(2)


class TabularQPolicy:
    name = "tabular_q"

    def __init__(self) -> None:
        self.q: dict[tuple[int, ...], np.ndarray] = {}

    def _key(self, info: dict[str, Any]) -> tuple[int, ...]:
        tick_bucket = min(4, int(info["tick"]) // 60)
        gear_bucket = min(3, int(info["gear"]) // 10)
        component_bucket = min(3, int(info["component"]) // 10)
        return (
            int(info["production_recipe"]),
            tick_bucket,
            gear_bucket,
            component_bucket,
        )

    def _values(self, key: tuple[int, ...]) -> np.ndarray:
        if key not in self.q:
            self.q[key] = np.zeros(2, dtype=np.float64)
        return self.q[key]

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        return int(np.argmax(self._values(self._key(info))))

    def train(
        self,
        env: ProductionMixEnv,
        episodes: int = 50,
        seed: int = 7000,
        alpha: float = 0.2,
        gamma: float = 0.95,
    ) -> None:
        rng = random.Random(0)
        for episode in range(episodes):
            observation, info = env.reset(seed=seed + episode)
            done = False
            epsilon = 1.0 - 0.95 * episode / max(1, episodes - 1)
            while not done:
                key = self._key(info)
                action = (
                    rng.randrange(2)
                    if rng.random() < epsilon
                    else self.act(observation, info)
                )
                observation, reward, terminated, truncated, info = env.step(
                    action
                )
                done = terminated or truncated
                target = reward
                if not done:
                    target += gamma * float(
                        np.max(self._values(self._key(info)))
                    )
                values = self._values(key)
                values[action] += alpha * (target - values[action])


@dataclass
class ProductionMetrics:
    mean_score: float
    mean_switches: float
    mean_gear: float
    mean_component: float
    success_rate: float
    scores: list[float]


def evaluate_production_policy(
    env: ProductionMixEnv,
    policy: ProductionPolicy,
    episodes: int = 5,
    seed: int = 70000,
    *,
    train_episodes: int = 0,
) -> ProductionMetrics:
    if train_episodes:
        if not isinstance(policy, TabularQPolicy):
            raise TypeError("only tabular Q can train")
        policy.train(env, episodes=train_episodes, seed=seed + 1000)
    scores: list[float] = []
    switches: list[float] = []
    gear: list[float] = []
    component: list[float] = []
    successes: list[float] = []
    for episode in range(episodes):
        observation, info = env.reset(seed=seed + episode)
        done = False
        while not done:
            action = policy.act(observation, info)
            observation, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        scores.append(float(info["score"]))
        switches.append(float(info["switches"]))
        gear.append(float(info["gear"]))
        component.append(float(info["component"]))
        successes.append(1.0 if info["success"] else 0.0)
    return ProductionMetrics(
        mean_score=float(np.mean(scores)),
        mean_switches=float(np.mean(switches)),
        mean_gear=float(np.mean(gear)),
        mean_component=float(np.mean(component)),
        success_rate=float(np.mean(successes)),
        scores=scores,
    )


def _pool(metrics: list[ProductionMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "mean_switches": float(
            np.mean([item.mean_switches for item in metrics])
        ),
        "mean_gear": float(np.mean([item.mean_gear for item in metrics])),
        "mean_component": float(
            np.mean([item.mean_component for item in metrics])
        ),
        "success_rate": float(
            np.mean([item.success_rate for item in metrics])
        ),
        "per_seed": [
            {
                "scores": item.scores,
                "success_rate": item.success_rate,
                "switches": item.mean_switches,
                "gear": item.mean_gear,
                "component": item.mean_component,
            }
            for item in metrics
        ],
    }


def run_production_mix(
    config: FactoryConfig,
    mix: ProductionMixConfig | None = None,
    *,
    seeds: tuple[int, ...] = (70000, 70001, 70002, 70003, 70004),
    episodes: int = 5,
    q_episodes: int = 50,
) -> dict[str, dict[str, Any]]:
    env = ProductionMixEnv(config, mix)
    results: dict[str, dict[str, Any]] = {}
    for name, policy in (
        ("always_gear", FixedPolicy(0)),
        ("always_component", FixedPolicy(1)),
        ("alternate_10", AlternationPolicy(10)),
        ("alternate_20", AlternationPolicy(20)),
        ("alternate_40", AlternationPolicy(40)),
        ("random", RandomPolicy(0)),
    ):
        results[name] = _pool(
            [
                evaluate_production_policy(
                    env,
                    policy,
                    episodes=episodes,
                    seed=seed,
                )
                for seed in seeds
            ]
        )
    q = TabularQPolicy()
    results["tabular_q"] = _pool(
        [
            evaluate_production_policy(
                env,
                q,
                episodes=episodes,
                seed=seed,
                train_episodes=q_episodes,
            )
            for seed in seeds
        ]
    )
    return results


def write_production_mix_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "production_mix_results.json").write_text(
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
        "# Production mix",
        "",
        f"Success ≥ {config['success_score']}; seeds "
        f"{config['seeds'][0]}–{config['seeds'][-1]}.",
        "",
        "| policy | mean score | 95% CI | gear | component | switches | success |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in results.items():
        lines.append(
            f"| {name} | {row['mean_score']:.2f} "
            f"[{row['score_ci'][0]:.2f}, {row['score_ci'][1]:.2f}] | "
            f"{row['mean_gear']:.1f} | {row['mean_component']:.1f} | "
            f"{row['mean_switches']:.1f} | {row['success_rate']:.2f} |"
        )
    (out / "production_mix_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "production_mix_report.md"
