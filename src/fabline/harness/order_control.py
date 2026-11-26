"""Policies and reports for the order-control task."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.orders import OrderControlConfig, OrderControlEnv
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class OrderPolicy(Protocol):
    name: str

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
    ) -> int: ...


def _active(info: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        order
        for order in info["orders"]
        if order["fulfilled"] + order["failed"] < order["quantity"]
    ]


class AlwaysPolicy:
    def __init__(self, action: int) -> None:
        self.action = action
        self.name = "always_gear" if action == 0 else "always_component"

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        return self.action


class EDFPolicy:
    name = "edf"

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        active = _active(info)
        if not active:
            return 0
        order = min(active, key=lambda item: (item["deadline"], item["id"]))
        return 0 if order["item"] == "GEAR" else 1


class ValuePolicy:
    name = "value"

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        active = _active(info)
        if not active:
            return 0
        order = max(
            active,
            key=lambda item: (
                (item["quantity"] - item["fulfilled"] - item["failed"])
                * item["value"]
                / max(1, item["deadline"] - int(info["tick"]))
            ),
        )
        return 0 if order["item"] == "GEAR" else 1


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
        active = _active(info)
        nearest = (
            min(order["deadline"] for order in active) - int(info["tick"])
            if active
            else 999
        )
        gear = sum(
            order["quantity"] - order["fulfilled"] - order["failed"]
            for order in active
            if order["item"] == "GEAR"
        )
        component = sum(
            order["quantity"] - order["fulfilled"] - order["failed"]
            for order in active
            if order["item"] == "COMPONENT"
        )
        return (
            int(info["production_recipe"]),
            min(4, int(info["tick"]) // 60),
            min(4, max(0, nearest) // 40),
            min(3, gear // 4),
            min(3, component // 4),
        )

    def _values(self, key: tuple[int, ...]) -> np.ndarray:
        if key not in self.q:
            self.q[key] = np.zeros(2, dtype=np.float64)
        return self.q[key]

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> int:
        return int(np.argmax(self._values(self._key(info))))

    def train(
        self,
        env: OrderControlEnv,
        episodes: int = 100,
        seed: int = 71000,
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
class OrderMetrics:
    mean_value: float
    mean_failed: float
    mean_wasted: float
    mean_switches: float
    success_rate: float
    values: list[float]


def evaluate_order_policy(
    env: OrderControlEnv,
    policy: OrderPolicy,
    episodes: int = 5,
    seed: int = 71000,
    *,
    train_episodes: int = 0,
) -> OrderMetrics:
    if train_episodes:
        if not isinstance(policy, TabularQPolicy):
            raise TypeError("only tabular Q can train")
        policy.train(env, episodes=train_episodes, seed=seed + 1000)
    values: list[float] = []
    failed: list[float] = []
    wasted: list[float] = []
    switches: list[float] = []
    successes: list[float] = []
    for episode in range(episodes):
        observation, info = env.reset(seed=seed + episode)
        done = False
        while not done:
            action = policy.act(observation, info)
            observation, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        values.append(float(info["fulfilled_value"]))
        failed.append(float(info["failed_units"]))
        wasted.append(float(info["wasted"]))
        switches.append(float(info["recipe_switches"]))
        successes.append(1.0 if info["success"] else 0.0)
    return OrderMetrics(
        mean_value=float(np.mean(values)),
        mean_failed=float(np.mean(failed)),
        mean_wasted=float(np.mean(wasted)),
        mean_switches=float(np.mean(switches)),
        success_rate=float(np.mean(successes)),
        values=values,
    )


def _pool(metrics: list[OrderMetrics]) -> dict[str, Any]:
    values = [value for item in metrics for value in item.values]
    return {
        "mean_value": float(np.mean(values)),
        "value_ci": list(bootstrap_mean_ci(values)),
        "mean_failed": float(np.mean([item.mean_failed for item in metrics])),
        "mean_wasted": float(np.mean([item.mean_wasted for item in metrics])),
        "mean_switches": float(
            np.mean([item.mean_switches for item in metrics])
        ),
        "success_rate": float(np.mean([item.success_rate for item in metrics])),
        "per_seed": [
            {
                "values": item.values,
                "success_rate": item.success_rate,
                "failed": item.mean_failed,
                "wasted": item.mean_wasted,
                "switches": item.mean_switches,
            }
            for item in metrics
        ],
    }


def run_order_control(
    config: FactoryConfig,
    orders: OrderControlConfig | None = None,
    *,
    seeds: tuple[int, ...] = (71000, 71001, 71002, 71003, 71004),
    episodes: int = 5,
    q_episodes: int = 100,
) -> dict[str, dict[str, Any]]:
    env = OrderControlEnv(config, orders=orders)
    results: dict[str, dict[str, Any]] = {}
    for name, policy in (
        ("always_gear", AlwaysPolicy(0)),
        ("always_component", AlwaysPolicy(1)),
        ("edf", EDFPolicy()),
        ("value", ValuePolicy()),
        ("random", RandomPolicy(0)),
    ):
        results[name] = _pool(
            [
                evaluate_order_policy(
                    env, policy, episodes=episodes, seed=seed
                )
                for seed in seeds
            ]
        )
    q = TabularQPolicy()
    results["tabular_q"] = _pool(
        [
            evaluate_order_policy(
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


def write_order_control_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "order_control_results.json").write_text(
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
        "# Order control",
        "",
        f"Success value ≥ {config['success_value']}; seeds "
        f"{config['seeds'][0]}–{config['seeds'][-1]}.",
        "",
        "| policy | value | 95% CI | failed | wasted | switches | success |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in results.items():
        lines.append(
            f"| {name} | {row['mean_value']:.2f} "
            f"[{row['value_ci'][0]:.2f}, {row['value_ci'][1]:.2f}] | "
            f"{row['mean_failed']:.1f} | {row['mean_wasted']:.1f} | "
            f"{row['mean_switches']:.1f} | {row['success_rate']:.2f} |"
        )
    (out / "order_control_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "order_control_report.md"
