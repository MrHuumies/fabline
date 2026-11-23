"""Policies and evaluation for the opt-in recipe-choice task."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.recipe import RecipeEnv, RecipeEnvConfig
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import EntityType


class RecipePolicy(Protocol):
    name: str

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int: ...


class FixedRecipePolicy:
    def __init__(self, action: int, name: str) -> None:
        self.action = action
        self.name = name

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return self.action if mask[self.action] else 0


class AlternateRecipePolicy:
    name = "alternate"

    def __init__(self) -> None:
        self.index = 0

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        action = self.index % 2
        self.index += 1
        return action if mask[action] else 0


class BufferAwarePolicy:
    name = "buffer_aware"

    def __init__(self, threshold: int = 2) -> None:
        self.threshold = threshold

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        action = 0 if info["assembler_input"] >= self.threshold else 1
        return action if mask[action] else 0


class PowerAwarePolicy:
    name = "power_aware"

    def __init__(self, threshold: int = 2, headroom: float = 0.15) -> None:
        self.threshold = threshold
        self.headroom = headroom

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        action = (
            0
            if info["assembler_input"] >= self.threshold
            and info["power_headroom"] >= self.headroom
            else 1
        )
        return action if mask[action] else 0


class PowerSaverPolicy:
    name = "power_saver"

    def __init__(self, threshold: int = 2) -> None:
        self.threshold = threshold

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["brownout_ratio"] > 0.0:
            action = 1
        else:
            action = 0 if info["assembler_input"] >= self.threshold else 1
        return action if mask[action] else 0


class PurgeAwarePolicy:
    name = "purge_aware"

    def __init__(self, threshold: int = 2) -> None:
        self.threshold = threshold

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["assembler_byproduct"] >= info["byproduct_capacity"]:
            action = 2
        else:
            action = 0 if info["assembler_input"] >= self.threshold else 1
        return action if mask[action] else 0


class SlowPurgePolicy:
    name = "slow_purge"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        action = (
            2
            if info["assembler_byproduct"] >= info["byproduct_capacity"]
            else 1
        )
        return action if mask[action] else 0


class RandomRecipePolicy:
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


@dataclass
class RecipeMetrics:
    mean_score: float
    mean_reward: float
    mean_gears: float
    mean_switches: float
    success_rate: float
    scores: list[float]
    gears: list[float]
    switches: list[float]


def evaluate_policy(
    env: RecipeEnv,
    policy: RecipePolicy,
    episodes: int = 5,
    seed: int = 0,
) -> RecipeMetrics:
    scores: list[float] = []
    rewards: list[float] = []
    gears: list[float] = []
    switches: list[float] = []
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
        gears.append(float(info["delivered_gears"]))
        switches.append(float(info["switches"]))
        successes.append(1.0 if info["success"] else 0.0)
    return RecipeMetrics(
        mean_score=float(np.mean(scores)),
        mean_reward=float(np.mean(rewards)),
        mean_gears=float(np.mean(gears)),
        mean_switches=float(np.mean(switches)),
        success_rate=float(np.mean(successes)),
        scores=scores,
        gears=gears,
        switches=switches,
    )


def evaluate_lookahead(
    env: RecipeEnv,
    episodes: int = 5,
    seed: int = 0,
) -> RecipeMetrics:
    """One-step greedy lookahead over the two recipes."""

    scores: list[float] = []
    rewards: list[float] = []
    gears: list[float] = []
    switches: list[float] = []
    successes: list[float] = []
    for episode in range(episodes):
        observation, info = env.reset(seed=seed + episode)
        done = False
        total_reward = 0.0
        while not done:
            best_action = 0
            best_delta = -1.0
            for action in range(env.n_actions):
                clone = env.world.clone()
                if action == 2:
                    for entity in clone.state.entities.values():
                        if entity.type is EntityType.ASSEMBLER:
                            entity.byproduct = 0
                else:
                    clone.state.recipe_index = action
                before = clone.state.score
                clone.run_ticks(env.recipe.decision_interval)
                delta = float(clone.state.score - before)
                if delta > best_delta:
                    best_delta = delta
                    best_action = action
            observation, reward, terminated, truncated, info = env.step(
                best_action
            )
            total_reward += reward
            done = terminated or truncated
        scores.append(float(info["score"]))
        rewards.append(total_reward)
        gears.append(float(info["delivered_gears"]))
        switches.append(float(info["switches"]))
        successes.append(1.0 if info["success"] else 0.0)
    return RecipeMetrics(
        mean_score=float(np.mean(scores)),
        mean_reward=float(np.mean(rewards)),
        mean_gears=float(np.mean(gears)),
        mean_switches=float(np.mean(switches)),
        success_rate=float(np.mean(successes)),
        scores=scores,
        gears=gears,
        switches=switches,
    )


def _pool(metrics: list[RecipeMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "min_score": float(np.min(scores)),
        "max_score": float(np.max(scores)),
        "mean_reward": float(np.mean([item.mean_reward for item in metrics])),
        "mean_gears": float(np.mean([item.mean_gears for item in metrics])),
        "mean_switches": float(
            np.mean([item.mean_switches for item in metrics])
        ),
        "success_rate": float(
            np.mean([item.success_rate for item in metrics])
        ),
        "per_seed": [
            {
                "scores": item.scores,
                "gears": item.gears,
                "switches": item.switches,
            }
            for item in metrics
        ],
    }


def run_recipe_choice(
    config: FactoryConfig,
    recipe: RecipeEnvConfig | None = None,
    *,
    seeds: tuple[int, ...] = (0, 1, 2),
) -> dict[str, dict[str, Any]]:
    env = RecipeEnv(config, recipe)
    results: dict[str, dict[str, Any]] = {}
    for name, policy in (
        ("fast", FixedRecipePolicy(0, "fast")),
        ("slow", FixedRecipePolicy(1, "slow")),
        ("alternate", AlternateRecipePolicy()),
        ("buffer_aware", BufferAwarePolicy(2)),
        ("buffer_aware4", BufferAwarePolicy(4)),
        ("power_aware", PowerAwarePolicy(2, 0.15)),
        ("power_saver", PowerSaverPolicy(2)),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, policy, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    results["random"] = _pool(
        [
            evaluate_policy(
                env, RandomRecipePolicy(seed=seed), episodes=1, seed=seed
            )
            for seed in seeds
        ]
    )
    if env.byproduct_enabled:
        for name, extra_policy in (
            ("purge_aware", PurgeAwarePolicy(2)),
            ("slow_purge", SlowPurgePolicy()),
        ):
            results[name] = _pool(
                [
                    evaluate_policy(env, extra_policy, episodes=1, seed=seed)
                    for seed in seeds
                ]
            )
    results["lookahead"] = _pool(
        [
            evaluate_lookahead(env, episodes=1, seed=seed)
            for seed in seeds
        ]
    )
    return results


def write_recipe_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "recipe_results.json").write_text(
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
        "# Recipe choice",
        "",
        f"Fast {config['fast_ticks']} ticks/{config['fast_cost']} ingots; "
        f"slow {config['slow_ticks']} ticks/{config['slow_cost']} ingots.",
        "",
        "| policy | mean score | 95% CI | success | gears | switches |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['success_rate']:.2f} | "
            f"{result['mean_gears']:.2f} | "
            f"{result['mean_switches']:.2f} |"
        )
    (out / "recipe_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "recipe_report.md"
