"""Finite-horizon planning on the assembly-edge production cell."""

from __future__ import annotations

import itertools
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.assembly import AssemblyControlConfig, AssemblyControlEnv
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig

ASSEMBLY_PLANNING_TASK_ID = "factory.assembly.plan.v1"
ASSEMBLY_PLANNING_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class AssemblyPlanningConfig:
    blocks: int = 5
    block_ticks: int = 100
    population: int = 16
    elites: int = 4
    iterations: int = 4
    random_plans: int = 32
    success_score: int = 100

    def __post_init__(self) -> None:
        if self.blocks <= 0:
            raise ValueError("blocks must be positive")
        if self.block_ticks <= 0:
            raise ValueError("block_ticks must be positive")
        if self.population <= 0 or self.elites <= 0:
            raise ValueError("population and elites must be positive")
        if self.elites > self.population:
            raise ValueError("elites cannot exceed population")
        if self.iterations <= 0 or self.random_plans <= 0:
            raise ValueError("iteration/random budgets must be positive")
        if self.success_score < 0:
            raise ValueError("success_score must be non-negative")


def _control_config(
    planning: AssemblyPlanningConfig,
) -> AssemblyControlConfig:
    return AssemblyControlConfig(
        episode_ticks=planning.blocks * planning.block_ticks,
        decision_interval=10,
        success_score=planning.success_score,
    )


def evaluate_plan(
    env: AssemblyControlEnv,
    plan: tuple[int, ...],
    planning: AssemblyPlanningConfig,
    *,
    seed: int,
) -> float:
    if len(plan) != planning.blocks:
        raise ValueError("plan length must equal blocks")
    steps = planning.block_ticks // env.assembly.decision_interval
    if steps * env.assembly.decision_interval != planning.block_ticks:
        raise ValueError("block_ticks must be a multiple of decision_interval")
    env.reset(seed=seed)
    done = False
    for action in plan:
        for _ in range(steps):
            if done:
                break
            _, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
    return float(env.world.state.score)


def _scripted_plans(blocks: int) -> dict[str, tuple[int, ...]]:
    return {
        "always_gear": (0,) * blocks,
        "always_assembly": (1,) * blocks,
        "alternate": tuple(index % 2 for index in range(blocks)),
        "batch_3": tuple(1 if index >= 3 else 0 for index in range(blocks)),
        "frontload": tuple([0, 0, 1, 1, 1][:blocks])
        if blocks >= 5
        else tuple(1 if index >= 2 else 0 for index in range(blocks)),
    }


def _cem_plan(
    env: AssemblyControlEnv,
    planning: AssemblyPlanningConfig,
    *,
    seed: int,
) -> tuple[tuple[int, ...], float]:
    rng = random.Random(seed)
    probabilities = np.full(planning.blocks, 0.5, dtype=np.float64)
    best_plan: tuple[int, ...] = tuple(0 for _ in range(planning.blocks))
    best_score = float("-inf")
    for _ in range(planning.iterations):
        population = [
            tuple(
                1 if rng.random() < probability else 0
                for probability in probabilities
            )
            for _ in range(planning.population)
        ]
        scored = [
            (evaluate_plan(env, plan, planning, seed=seed), plan)
            for plan in population
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        for score, plan in scored:
            if score > best_score:
                best_score, best_plan = score, plan
        elites = scored[: planning.elites]
        probabilities = np.mean(
            np.asarray([plan for _, plan in elites], dtype=np.float64), axis=0
        )
        probabilities = np.clip(probabilities, 0.05, 0.95)
    return best_plan, best_score


def _oracle_plan(
    env: AssemblyControlEnv,
    planning: AssemblyPlanningConfig,
    *,
    seed: int,
) -> tuple[tuple[int, ...], float]:
    best_plan: tuple[int, ...] = tuple(0 for _ in range(planning.blocks))
    best_score = float("-inf")
    for bits in itertools.product((0, 1), repeat=planning.blocks):
        score = evaluate_plan(env, bits, planning, seed=seed)
        if score > best_score:
            best_score, best_plan = score, bits
    return best_plan, best_score


def _random_plan_score(
    env: AssemblyControlEnv,
    planning: AssemblyPlanningConfig,
    *,
    seed: int,
) -> tuple[float, list[float]]:
    rng = random.Random(seed)
    scores = []
    for _ in range(planning.random_plans):
        plan = tuple(rng.randrange(2) for _ in range(planning.blocks))
        scores.append(evaluate_plan(env, plan, planning, seed=seed))
    return float(np.mean(scores)), scores


def _pool(values: list[float], success_score: int) -> dict[str, Any]:
    return {
        "mean_score": float(np.mean(values)),
        "score_ci": list(bootstrap_mean_ci(values)),
        "success_rate": float(
            np.mean([value >= success_score for value in values])
        ),
    }


def run_assembly_planning(
    config: FactoryConfig,
    planning: AssemblyPlanningConfig,
    *,
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4),
) -> dict[str, Any]:
    env = AssemblyControlEnv(config, _control_config(planning))
    results: dict[str, Any] = {}
    for name, plan in _scripted_plans(planning.blocks).items():
        results[name] = _pool(
            [
                evaluate_plan(env, plan, planning, seed=seed)
                for seed in seeds
            ],
            planning.success_score,
        )
    results["random"] = _pool(
        [
            _random_plan_score(env, planning, seed=seed)[0]
            for seed in seeds
        ],
        planning.success_score,
    )
    cem_scores: list[float] = []
    cem_plans: dict[str, list[int]] = {}
    for seed in seeds:
        plan, score = _cem_plan(env, planning, seed=seed)
        cem_plans[str(seed)] = list(plan)
        cem_scores.append(score)
    results["cem"] = _pool(cem_scores, planning.success_score)
    results["cem"]["plans"] = cem_plans
    oracle_scores: list[float] = []
    oracle_plans: dict[str, list[int]] = {}
    for seed in seeds:
        plan, score = _oracle_plan(env, planning, seed=seed)
        oracle_plans[str(seed)] = list(plan)
        oracle_scores.append(score)
    results["oracle"] = _pool(oracle_scores, planning.success_score)
    results["oracle"]["plans"] = oracle_plans
    return results


def write_assembly_planning_report(
    out: str | Path,
    results: dict[str, Any],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "assembly_planning_results.json").write_text(
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
        "# Assembly-edge planning",
        "",
        f"- blocks: {config['blocks']} x {config['block_ticks']} ticks",
        f"- CEM: population {config['population']}, elites {config['elites']}, "
        f"iterations {config['iterations']}",
        "",
        "| policy | mean score | 95% CI |",
        "|---|---:|---:|",
    ]
    for name in (
        "always_gear",
        "always_assembly",
        "alternate",
        "batch_3",
        "frontload",
        "random",
        "cem",
        "oracle",
    ):
        row = results[name]
        lines.append(
            f"| {name} | {row['mean_score']:.2f} "
            f"[{row['score_ci'][0]:.2f}, {row['score_ci'][1]:.2f}] |"
        )
    lines.append("")
    (out / "assembly_planning_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "assembly_planning_report.md"
