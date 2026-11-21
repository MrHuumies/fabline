"""Policies and evaluation for fault + power control."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.fault_power import FaultPowerConfig, FaultPowerEnv
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class InteractionPolicy(Protocol):
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


class FavorFurnacePolicy:
    name = "favor_furnace"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return 1


class FavorAssemblerPolicy:
    name = "favor_assembler"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return 2


class RepairNowPolicy:
    name = "repair_now"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return 3 if mask[3] else 0


class AlternateRepairPolicy:
    """Scripted: repair when useful, otherwise alternate priorities."""

    name = "alternate_repair"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if mask[3] and (
            info["assembler_craft"] > 0 or info["assembler_input"] >= 2
        ):
            return 3
        if info["faulted_count"] and info["assembler_input"] >= 2:
            return 3
        if info["assembler_craft"] > 0 or info["assembler_input"] >= 2:
            return 2
        return 1


class RandomInteractionPolicy:
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
        return int(self.rng.choice(legal.tolist()))


class TabularQPolicy:
    name = "tabular_q"

    def __init__(self) -> None:
        self.q: dict[tuple[int, ...], np.ndarray] = {}

    def _key(self, info: dict[str, Any]) -> tuple[int, ...]:
        return (
            min(3, int(info["assembler_input"]) // 2),
            int(info["assembler_craft"] > 0),
            min(2, int(info["furnace_output"])),
            int(info["furnace_craft"] > 0),
            min(2, int(info["faulted_count"])),
            int(bool(info["faulted_furnace"])),
            int(bool(info["faulted_assembler"])),
            min(2, int(float(info["repair_progress"]) * 2)),
            min(4, int(float(info["max_wear"]) * 4)),
            min(9, int(info["tick"]) // 50),
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
        env: FaultPowerEnv,
        episodes: int = 100,
        seed: int = 0,
        alpha: float = 0.2,
        gamma: float = 0.95,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            observation, info = env.reset(seed=episode)
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
                observation, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                next_key = self._key(info)
                target = reward
                if not done:
                    next_mask = env.action_mask()
                    target += gamma * float(
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
class InteractionMetrics:
    mean_score: float
    mean_reward: float
    mean_repairs: float
    success_rate: float
    scores: list[float]
    rewards: list[float]


def evaluate_policy(
    env: FaultPowerEnv,
    policy: InteractionPolicy,
    episodes: int = 5,
    seed: int = 0,
) -> InteractionMetrics:
    scores: list[float] = []
    rewards: list[float] = []
    repairs: list[float] = []
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
        successes.append(1.0 if info["success"] else 0.0)
    return InteractionMetrics(
        mean_score=float(np.mean(scores)),
        mean_reward=float(np.mean(rewards)),
        mean_repairs=float(np.mean(repairs)),
        success_rate=float(np.mean(successes)),
        scores=scores,
        rewards=rewards,
    )


def _pool(
    metrics: list[InteractionMetrics],
    seeds: tuple[int, ...],
) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    rewards = [value for item in metrics for value in item.rewards]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "mean_reward": float(np.mean(rewards)),
        "reward_ci": list(bootstrap_mean_ci(rewards)),
        "mean_repairs": float(np.mean([item.mean_repairs for item in metrics])),
        "success_rate": float(np.mean([item.success_rate for item in metrics])),
        "per_seed": {
            str(seed): {
                "mean_score": float(np.mean(item.scores)),
                "success_rate": float(item.success_rate),
            }
            for seed, item in zip(seeds, metrics, strict=True)
        },
    }


def run_fault_power(
    config: FactoryConfig,
    interaction: FaultPowerConfig | None = None,
    *,
    episodes: int = 5,
    train_episodes: int = 100,
    seeds: tuple[int, ...] = (0, 1, 2),
) -> dict[str, dict[str, Any]]:
    env = FaultPowerEnv(config, interaction)
    results: dict[str, dict[str, Any]] = {}
    for name, policy in (
        ("noop", NoopPolicy()),
        ("favor_furnace", FavorFurnacePolicy()),
        ("favor_assembler", FavorAssemblerPolicy()),
        ("repair_now", RepairNowPolicy()),
        ("alternate_repair", AlternateRepairPolicy()),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, policy, episodes=episodes, seed=seed)
                for seed in seeds
            ],
            seeds,
        )
    results["random"] = _pool(
        [
            evaluate_policy(
                env,
                RandomInteractionPolicy(seed=seed),
                episodes=episodes,
                seed=seed,
            )
            for seed in seeds
        ],
        seeds,
    )
    q_metrics = []
    for seed in seeds:
        q_policy = TabularQPolicy()
        q_policy.train(env, episodes=train_episodes, seed=seed)
        q_metrics.append(
            evaluate_policy(env, q_policy, episodes=episodes, seed=seed)
        )
    results["tabular_q"] = _pool(q_metrics, seeds)
    return results


def write_fault_power_report(
    out_dir: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(
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
        "# Fault + power control report",
        "",
        "Actions: noop, favor furnace, favor assembler, repair. "
        f"Repair cost is {config['repair_cost']}.",
        "",
        "| policy | mean score | mean reward | mean repairs | success |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['mean_reward']:.2f} | {result['mean_repairs']:.2f} | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Caveats",
            "",
            "- One fixed gear line, power budget, and fault regime.",
            "- The repair action targets the first faulted entity in id order.",
            "- The scripted policy is an oracle-style baseline.",
            "- Small evaluation budget; CIs are wide.",
            "",
        ]
    )
    path = out / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
