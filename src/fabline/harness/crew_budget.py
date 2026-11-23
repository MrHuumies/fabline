"""Compare shared, budgeted, and private crew reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fabline.env.crew_replan import CrewReplanConfig, CrewReplanEnv
from fabline.env.crew_visibility import (
    BudgetVisibilityEnv,
    PrivateVisibilityEnv,
    VisibilityEnv,
)
from fabline.harness.crew_private import (
    CrewAwarePolicy,
    CrewGreedyPolicy,
    CrewNearestPolicy,
    PrivatePairPolicy,
)
from fabline.harness.crew_replan import (
    FixedTwoPolicy,
    ParallelGreedyPolicy,
    ParallelNearestPolicy,
    RecallAwarePolicy,
    _oracle_pair,
    _pool,
    evaluate_policy,
)
from fabline.worlds.factory.config import FactoryConfig


def _shared_result(
    env: Any,
    seeds: tuple[int, ...],
) -> dict[str, Any]:
    condition: dict[str, Any] = {}
    for name, policy in (
        ("nearest", ParallelNearestPolicy()),
        ("greedy", ParallelGreedyPolicy()),
        ("aware", RecallAwarePolicy()),
    ):
        condition[name] = _pool(
            [
                evaluate_policy(env, policy, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    oracle_metrics = []
    oracle_actions: dict[str, list[int]] = {}
    for seed in seeds:
        initial, replan_action = _oracle_pair(env, seed)
        oracle_actions[str(seed)] = [initial, replan_action]
        oracle_metrics.append(
            evaluate_policy(
                env,
                FixedTwoPolicy(initial, replan_action),
                episodes=1,
                seed=seed,
            )
        )
    condition["oracle"] = _pool(oracle_metrics)
    condition["oracle"]["actions"] = oracle_actions
    return condition


def run_crew_budget(
    config: FactoryConfig,
    replan: CrewReplanConfig | None = None,
    *,
    seeds: tuple[int, ...] = (16000,),
    radius: int = 16,
) -> dict[str, dict[str, Any]]:
    base = CrewReplanEnv(config, replan)
    results: dict[str, dict[str, Any]] = {}
    results["shared"] = _shared_result(
        VisibilityEnv(base, radius=radius, report_age=0), seeds
    )
    results["budget2"] = _shared_result(
        BudgetVisibilityEnv(
            base, radius=radius, reports_per_crew=2
        ),
        seeds,
    )
    results["budget1"] = _shared_result(
        BudgetVisibilityEnv(
            base, radius=radius, reports_per_crew=1
        ),
        seeds,
    )
    private: Any = PrivateVisibilityEnv(base, radius=radius)
    private_condition: dict[str, Any] = {}
    for name, policy in (
        (
            "nearest",
            PrivatePairPolicy(
                CrewNearestPolicy("a"), CrewNearestPolicy("b")
            ),
        ),
        (
            "greedy",
            PrivatePairPolicy(
                CrewGreedyPolicy("a"), CrewGreedyPolicy("b")
            ),
        ),
        (
            "aware",
            PrivatePairPolicy(
                CrewAwarePolicy("a"), CrewAwarePolicy("b")
            ),
        ),
    ):
        private_condition[name] = _pool(
            [
                evaluate_policy(private, policy, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    results["private"] = private_condition
    return results


def write_crew_budget_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "crew_budget_results.json").write_text(
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
        "# Crew report budget",
        "",
        f"Radius {config['radius']}; shared, 2 reports, 1 report, private; "
        f"success ≥ {config['success_score']}.",
        "",
        "| condition | policy | mean score | 95% CI | success |",
        "|---|---|---:|---:|---:|",
    ]
    for label, condition in results.items():
        for policy in ("nearest", "greedy", "aware", "oracle"):
            if policy not in condition:
                continue
            result = condition[policy]
            lines.append(
                f"| {label} | {policy} | {result['mean_score']:.2f} "
                f"[{result['score_ci'][0]:.2f}, "
                f"{result['score_ci'][1]:.2f}] | "
                f"{result['success_rate']:.2f} |"
            )
    (out / "crew_budget_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "crew_budget_report.md"
