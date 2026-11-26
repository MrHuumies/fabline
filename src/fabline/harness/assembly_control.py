"""Policies and evaluation for assembly-edge production control."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.assembly import AssemblyControlConfig, AssemblyControlEnv
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class AssemblyPolicy(Protocol):
    name: str

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
    ) -> int: ...


class AlwaysPolicy:
    def __init__(self, action: int) -> None:
        self.action = action
        self.name = "always_gear" if action == 0 else "always_assembly"

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        return self.action


class BufferAwarePolicy:
    name = "buffer_aware"

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        if info["assembly_component"] >= 1 and info["assembly_ingot"] >= 1:
            return 1
        return 0


class BatchPolicy:
    """Buffer component while making direct gear, then assemble a batch."""

    name = "batch_aware"

    def __init__(self, threshold: int = 3) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        self.threshold = threshold

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        component = int(info["assembly_component"])
        ingot = int(info["assembly_ingot"])
        if info["recipe"] == 0:
            return 1 if component >= self.threshold and ingot >= 1 else 0
        return 1 if component >= 1 and ingot >= 1 else 0


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
        return (
            min(6, int(info["assembly_ingot"])),
            min(6, int(info["assembly_component"])),
            min(2, int(info["component_output"])),
            int(info["recipe"]),
        )

    def _values(self, key: tuple[int, ...]) -> np.ndarray:
        if key not in self.q:
            self.q[key] = np.zeros(2, dtype=np.float64)
        return self.q[key]

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        return int(np.argmax(self._values(self._key(info))))

    def train(
        self,
        env: AssemblyControlEnv,
        episodes: int = 100,
        seed: int = 1000,
        alpha: float = 0.2,
        gamma: float = 0.95,
    ) -> None:
        rng = random.Random(seed)
        for episode in range(episodes):
            _, info = env.reset(seed=seed + episode)
            done = False
            epsilon = 1.0 - 0.95 * episode / max(1, episodes - 1)
            while not done:
                key = self._key(info)
                action = (
                    rng.randrange(2)
                    if rng.random() < epsilon
                    else self.act(np.empty(0), info)
                )
                _, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                target = reward
                if not done:
                    target += gamma * float(np.max(self._values(self._key(info))))
                values = self._values(key)
                values[action] += alpha * (target - values[action])


@dataclass
class AssemblyMetrics:
    mean_score: float
    success_rate: float
    mean_switches: float
    scores: list[float]
    successes: list[float]
    switches: list[float]


def evaluate_policy(
    env: AssemblyControlEnv,
    policy: AssemblyPolicy,
    *,
    episodes: int = 5,
    seed: int = 0,
) -> AssemblyMetrics:
    scores: list[float] = []
    successes: list[float] = []
    switches: list[float] = []
    for episode in range(episodes):
        observation, info = env.reset(seed=seed + episode)
        done = False
        while not done:
            action = policy.act(observation, info)
            observation, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        scores.append(float(info["score"]))
        successes.append(1.0 if info["success"] else 0.0)
        switches.append(float(info["switches"]))
    return AssemblyMetrics(
        mean_score=float(np.mean(scores)),
        success_rate=float(np.mean(successes)),
        mean_switches=float(np.mean(switches)),
        scores=scores,
        successes=successes,
        switches=switches,
    )


def _pool(metrics: list[AssemblyMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    successes = [value for item in metrics for value in item.successes]
    switches = [value for item in metrics for value in item.switches]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "success_rate": float(np.mean(successes)),
        "success_ci": list(bootstrap_mean_ci(successes)),
        "mean_switches": float(np.mean(switches)),
        "per_seed": [item.mean_score for item in metrics],
    }


def run_assembly_control(
    config: FactoryConfig,
    assembly: AssemblyControlConfig,
    *,
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4),
    episodes: int = 5,
    q_episodes: int = 500,
) -> dict[str, dict[str, Any]]:
    env = AssemblyControlEnv(config, assembly)
    results: dict[str, dict[str, Any]] = {}
    for name, policy in (
        ("always_gear", AlwaysPolicy(0)),
        ("always_assembly", AlwaysPolicy(1)),
        ("buffer_aware", BufferAwarePolicy()),
        ("batch_aware", BatchPolicy()),
        ("random", RandomPolicy(0)),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, policy, episodes=episodes, seed=seed)
                for seed in seeds
            ]
        )
    # Train Q on a disjoint block, then evaluate on the formal seeds.
    q = TabularQPolicy()
    q.train(env, episodes=q_episodes, seed=10_000)
    results["tabular_q"] = _pool(
        [
            evaluate_policy(env, q, episodes=episodes, seed=seed)
            for seed in seeds
        ]
    )
    return results


def assembly_gates(
    results: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    base = float(results["always_gear"]["mean_score"])
    scripted = max(
        float(results["always_assembly"]["mean_score"]),
        float(results["buffer_aware"]["mean_score"]),
        float(results["batch_aware"]["mean_score"]),
    )
    random_score = float(results["random"]["mean_score"])
    learned = results["tabular_q"]
    return {
        "H1_scripted_gap": scripted >= base + 10.0,
        "H2_learned_gap": float(learned["mean_score"]) >= random_score + 10.0,
        "H3_success": float(learned["success_rate"]) >= 0.60,
    }


def write_assembly_control_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    gates = assembly_gates(results)
    (out / "assembly_control_results.json").write_text(
        json.dumps(
            {"config": config, "results": results, "gates": gates},
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Assembly-edge control",
        "",
        f"- success score: {config['success_score']}",
        f"- seeds: {config['seeds']}",
        "",
        "| policy | score | success | switches |",
        "|---|---:|---:|---:|",
    ]
    for name, row in results.items():
        lines.append(
            f"| {name} | {row['mean_score']:.2f} "
            f"[{row['score_ci'][0]:.2f}, {row['score_ci'][1]:.2f}] | "
            f"{row['success_rate']:.2f} | {row['mean_switches']:.1f} |"
        )
    lines.extend(["", "## Gates", "", "| Gate | Result |", "|---|---|"])
    for name, passed in gates.items():
        lines.append(f"| {name} | {'pass' if passed else 'fail'} |")
    lines.append("")
    (out / "assembly_control_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "assembly_control_report.md"
