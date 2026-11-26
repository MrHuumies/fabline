"""Finite-horizon order planning over recipe blocks."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.orders import (
    Order,
    OrderConfig,
    OrderControlConfig,
    OrderControlEnv,
    generate_orders,
)
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import Item

ORDER_PLANNING_TASK_ID = "factory.orders.plan.v1"


@dataclass(frozen=True)
class OrderPlanningConfig:
    episode_ticks: int = 300
    decision_interval: int = 10
    blocks: int = 5
    success_value: int = 160
    orders: OrderConfig = OrderConfig(enabled=True)
    population: int = 16
    elites: int = 4
    iterations: int = 4
    random_samples: int = 32

    def __post_init__(self) -> None:
        if self.blocks <= 0:
            raise ValueError("blocks must be positive")
        if self.episode_ticks % (self.decision_interval * self.blocks):
            raise ValueError("blocks must divide the decision horizon")
        if self.population <= 0 or self.elites <= 0:
            raise ValueError("population and elites must be positive")
        if self.elites > self.population:
            raise ValueError("elites cannot exceed population")
        if self.iterations <= 0 or self.random_samples <= 0:
            raise ValueError("iterations and random samples must be positive")
        if not self.orders.enabled:
            raise ValueError("order planning requires orders.enabled")

    @property
    def decisions_per_block(self) -> int:
        return self.episode_ticks // (self.decision_interval * self.blocks)

    def control(self) -> OrderControlConfig:
        return OrderControlConfig(
            episode_ticks=self.episode_ticks,
            decision_interval=self.decision_interval,
            success_value=self.success_value,
            orders=self.orders,
        )


def execute_plan(
    env: OrderControlEnv,
    plan: tuple[int, ...],
    seed: int,
) -> dict[str, Any]:
    observation, info = env.reset(seed)
    done = False
    step = 0
    per_block = env.order_config.episode_ticks // (
        env.order_config.decision_interval * len(plan)
    )
    while not done:
        block = min(len(plan) - 1, step // max(1, per_block))
        observation, _, terminated, truncated, info = env.step(plan[block])
        done = terminated or truncated
        step += 1
    return {
        "value": float(info["fulfilled_value"]),
        "success": bool(info["success"]),
        "failed": float(info["failed_units"]),
        "wasted": float(info["wasted"]),
        "switches": float(info["recipe_switches"]),
        "plan": list(plan),
    }


def _static_plan(
    orders: list[Order],
    blocks: int,
    policy: str,
    block_ticks: int,
) -> tuple[int, ...]:
    plan: list[int] = []
    for block in range(blocks):
        remaining = [
            order
            for order in orders
            if order.deadline > (block + 1) * block_ticks
            and order.remaining > 0
        ]
        if not remaining:
            plan.append(0)
            continue
        if policy == "edf":
            order = min(
                remaining, key=lambda item: (item.deadline, item.id)
            )
        else:
            order = max(
                remaining,
                key=lambda item: (
                    item.remaining * item.value_per_unit,
                    -item.deadline,
                ),
            )
        plan.append(0 if order.item is Item.GEAR else 1)
    return tuple(plan)


def _random_plan(rng: random.Random, blocks: int) -> tuple[int, ...]:
    return tuple(rng.randrange(2) for _ in range(blocks))


def _cem_plan(
    env: OrderControlEnv,
    cfg: OrderPlanningConfig,
    seed: int,
    rng: random.Random,
) -> tuple[float, tuple[int, ...], float]:
    probabilities = [np.ones(2) / 2.0 for _ in range(cfg.blocks)]
    best_value = -1.0
    best_plan = tuple(0 for _ in range(cfg.blocks))
    start = time.perf_counter()
    for _ in range(cfg.iterations):
        population: list[tuple[float, tuple[int, ...]]] = []
        for _ in range(cfg.population):
            plan = tuple(
                int(rng.choices((0, 1), weights=prob.tolist())[0])
                for prob in probabilities
            )
            result = execute_plan(env, plan, seed)
            value = result["value"]
            population.append((value, plan))
            if value > best_value:
                best_value = value
                best_plan = plan
        population.sort(reverse=True, key=lambda item: item[0])
        elites = population[: cfg.elites]
        for index in range(cfg.blocks):
            counts = np.ones(2, dtype=np.float64)
            for _, plan in elites:
                counts[plan[index]] += 1.0
            probabilities[index] = counts / counts.sum()
    return best_value, best_plan, time.perf_counter() - start


def _random_shooting(
    env: OrderControlEnv,
    cfg: OrderPlanningConfig,
    seed: int,
    rng: random.Random,
) -> tuple[float, tuple[int, ...], float]:
    best_value = -1.0
    best_plan = tuple(0 for _ in range(cfg.blocks))
    start = time.perf_counter()
    for _ in range(cfg.random_samples):
        plan = _random_plan(rng, cfg.blocks)
        value = execute_plan(env, plan, seed)["value"]
        if value > best_value:
            best_value = value
            best_plan = plan
    return best_value, best_plan, time.perf_counter() - start


def _oracle(
    env: OrderControlEnv,
    cfg: OrderPlanningConfig,
    seed: int,
) -> tuple[float, tuple[int, ...], float]:
    best_value = -1.0
    best_plan = tuple(0 for _ in range(cfg.blocks))
    start = time.perf_counter()
    for mask in range(2**cfg.blocks):
        plan = tuple((mask >> index) & 1 for index in range(cfg.blocks))
        value = execute_plan(env, plan, seed)["value"]
        if value > best_value:
            best_value = value
            best_plan = plan
    return best_value, best_plan, time.perf_counter() - start


def run_order_planning(
    config: FactoryConfig,
    cfg: OrderPlanningConfig | None = None,
    *,
    seeds: tuple[int, ...] = (73000, 73001, 73002, 73003, 73004),
) -> dict[str, Any]:
    cfg = cfg or OrderPlanningConfig()
    env = OrderControlEnv(config, orders=cfg.control())
    rng = random.Random(20261126)
    results: dict[str, dict[str, Any]] = {
        "always_gear": {"values": [], "successes": [], "plans": [], "seconds": []},
        "always_component": {
            "values": [],
            "successes": [],
            "plans": [],
            "seconds": [],
        },
        "edf_plan": {"values": [], "successes": [], "plans": [], "seconds": []},
        "value_plan": {"values": [], "successes": [], "plans": [], "seconds": []},
        "random_plan": {
            "values": [],
            "successes": [],
            "plans": [],
            "seconds": [],
        },
        "cem": {"values": [], "successes": [], "plans": [], "seconds": []},
        "oracle": {"values": [], "successes": [], "plans": [], "seconds": []},
    }
    for seed in seeds:
        orders = generate_orders(cfg.orders, seed, cfg.episode_ticks)
        for name, plan in (
            ("always_gear", (0,) * cfg.blocks),
            ("always_component", (1,) * cfg.blocks),
            (
                "edf_plan",
                _static_plan(
                    orders,
                    cfg.blocks,
                    "edf",
                    cfg.episode_ticks // cfg.blocks,
                ),
            ),
            (
                "value_plan",
                _static_plan(
                    orders,
                    cfg.blocks,
                    "value",
                    cfg.episode_ticks // cfg.blocks,
                ),
            ),
        ):
            start = time.perf_counter()
            result = execute_plan(env, plan, seed)
            results[name]["values"].append(result["value"])
            results[name]["successes"].append(1.0 if result["success"] else 0.0)
            results[name]["plans"].append(list(plan))
            results[name]["seconds"].append(time.perf_counter() - start)

        plan = _random_plan(rng, cfg.blocks)
        start = time.perf_counter()
        result = execute_plan(env, plan, seed)
        results["random_plan"]["values"].append(result["value"])
        results["random_plan"]["successes"].append(
            1.0 if result["success"] else 0.0
        )
        results["random_plan"]["plans"].append(list(plan))
        results["random_plan"]["seconds"].append(time.perf_counter() - start)

        value, plan, seconds = _cem_plan(env, cfg, seed, rng)
        results["cem"]["values"].append(value)
        results["cem"]["successes"].append(1.0 if value >= cfg.success_value else 0.0)
        results["cem"]["plans"].append(list(plan))
        results["cem"]["seconds"].append(seconds)

        value, plan, seconds = _oracle(env, cfg, seed)
        results["oracle"]["values"].append(value)
        results["oracle"]["successes"].append(
            1.0 if value >= cfg.success_value else 0.0
        )
        results["oracle"]["plans"].append(list(plan))
        results["oracle"]["seconds"].append(seconds)

    summary: dict[str, Any] = {}
    for name, payload in results.items():
        summary[name] = {
            "mean_value": float(np.mean(payload["values"])),
            "value_ci": list(bootstrap_mean_ci(payload["values"])),
            "success_rate": float(np.mean(payload["successes"])),
            "mean_seconds": float(np.mean(payload["seconds"])),
            "per_seed": [
                {
                    "value": value,
                    "success": success,
                    "plan": plan,
                }
                for value, success, plan in zip(
                    payload["values"],
                    payload["successes"],
                    payload["plans"],
                    strict=True,
                )
            ],
        }
    return {
        "task": ORDER_PLANNING_TASK_ID,
        "config": {
            "episode_ticks": cfg.episode_ticks,
            "decision_interval": cfg.decision_interval,
            "blocks": cfg.blocks,
            "success_value": cfg.success_value,
            "population": cfg.population,
            "elites": cfg.elites,
            "iterations": cfg.iterations,
            "random_samples": cfg.random_samples,
            "seeds": list(seeds),
        },
        "results": summary,
    }


def write_order_planning_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "order_planning_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Order planning",
        "",
        f"{report['config']['blocks']} blocks; success value "
        f"{report['config']['success_value']}; seeds "
        f"{report['config']['seeds'][0]}–{report['config']['seeds'][-1]}.",
        "",
        "| policy | mean value | 95% CI | success | seconds |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in report["results"].items():
        lines.append(
            f"| {name} | {row['mean_value']:.2f} "
            f"[{row['value_ci'][0]:.2f}, {row['value_ci'][1]:.2f}] | "
            f"{row['success_rate']:.2f} | {row['mean_seconds']:.3f} |"
        )
    lines.append("")
    for seed, row in zip(
        report["config"]["seeds"],
        report["results"]["cem"]["per_seed"],
        strict=True,
    ):
        lines.append(f"- CEM seed {seed}: value {row['value']}, plan {row['plan']}")
    (out / "order_planning_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "order_planning_report.md"
