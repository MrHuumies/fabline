"""Evaluate local views and delayed reports on the spread crew layout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fabline.env.crew_replan import CrewReplanConfig, CrewReplanEnv
from fabline.env.crew_visibility import VisibilityEnv
from fabline.harness.crew_replan import (
    FixedTwoPolicy,
    ParallelGreedyPolicy,
    ParallelNearestPolicy,
    RecallAwarePolicy,
    _oracle_pair,
    _pool,
    evaluate_policy,
)
from fabline.harness.multi_crew import NoopPolicy, SingleEDFPolicy
from fabline.worlds.factory.config import FactoryConfig


def run_crew_visibility(
    config: FactoryConfig,
    replan: CrewReplanConfig | None = None,
    *,
    seeds: tuple[int, ...] = (10000,),
    radius: int = 16,
    ages: tuple[int, ...] = (30, 60),
) -> dict[str, dict[str, Any]]:
    base = CrewReplanEnv(config, replan)
    conditions: list[tuple[str, int | None]] = [
        ("global", None),
        ("local", 0),
        *[(f"delayed{age}", age) for age in ages],
    ]
    results: dict[str, dict[str, Any]] = {}
    for label, age in conditions:
        env: Any = (
            base
            if age is None
            else VisibilityEnv(base, radius=radius, report_age=age)
        )
        condition: dict[str, Any] = {}
        for name, policy in (
            ("noop", NoopPolicy()),
            ("single_edf", SingleEDFPolicy()),
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
        results[label] = condition
    return results


def write_crew_visibility_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "crew_visibility_results.json").write_text(
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
        "# Crew visibility and delayed reports",
        "",
        f"Map {config['width']}×{config['height']}; radius "
        f"{config['radius']}; report ages {config['ages']}; "
        f"success ≥ {config['success_score']}.",
        "",
        "| condition | policy | mean score | 95% CI | success |",
        "|---|---|---:|---:|---:|",
    ]
    for label, condition in results.items():
        for policy in (
            "noop",
            "single_edf",
            "nearest",
            "greedy",
            "aware",
            "oracle",
        ):
            result = condition[policy]
            lines.append(
                f"| {label} | {policy} | {result['mean_score']:.2f} "
                f"[{result['score_ci'][0]:.2f}, "
                f"{result['score_ci'][1]:.2f}] | "
                f"{result['success_rate']:.2f} |"
            )
    lines.extend(
        [
            "",
            "Oracle actions (initial, replan):",
        ]
    )
    for label, condition in results.items():
        lines.append(f"- {label}: " + ", ".join(
            f"{seed}:{actions}"
            for seed, actions in condition["oracle"]["actions"].items()
        ))
    (out / "crew_visibility_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "crew_visibility_report.md"
