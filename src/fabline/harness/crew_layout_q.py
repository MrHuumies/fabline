"""Evaluate compact and old tabular Q on the twin-line crew task."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.multi_crew import MultiCrewConfig, MultiCrewEnv
from fabline.harness.layout_q import CompactQPolicy
from fabline.harness.multi_crew import (
    NoopPolicy,
    ParallelGreedyPolicy,
    ParallelNearestPolicy,
    RandomPolicy,
    SingleEDFPolicy,
    TabularQPolicy,
    _FixedActionPolicy,
    _oracle_action,
    evaluate_policy,
)
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


def _pool(metrics: list[Any]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "min_score": float(np.min(scores)),
        "max_score": float(np.max(scores)),
        "mean_prevented": float(
            np.mean([item.mean_prevented for item in metrics])
        ),
        "mean_aborted": float(
            np.mean([item.mean_aborted for item in metrics])
        ),
        "mean_travel": float(
            np.mean([item.mean_travel for item in metrics])
        ),
        "success_rate": float(
            np.mean([item.success_rate for item in metrics])
        ),
        "per_seed": [
            {
                "scores": item.scores,
                "success_rate": item.success_rate,
                "prevented": item.mean_prevented,
                "aborted": item.mean_aborted,
                "travel": item.mean_travel,
            }
            for item in metrics
        ],
    }


def run_crew_layout_q(
    config: FactoryConfig,
    multi: MultiCrewConfig | None = None,
    *,
    seeds: tuple[int, ...] = (8000,),
    q_seeds: tuple[int, ...] = (0, 1, 2),
    compact_episodes: int = 2000,
    tabular_episodes: int = 500,
    train_seed_start: int = 80000,
) -> dict[str, dict[str, Any]]:
    env = MultiCrewEnv(config, multi)
    results: dict[str, dict[str, Any]] = {}
    for name, baseline in (
        ("noop", NoopPolicy()),
        ("single_edf", SingleEDFPolicy()),
        ("parallel_nearest", ParallelNearestPolicy()),
        ("parallel_greedy", ParallelGreedyPolicy()),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, baseline, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    results["random"] = _pool(
        [
            evaluate_policy(
                env, RandomPolicy(seed=seed), episodes=1, seed=seed
            )
            for seed in seeds
        ]
    )
    oracle_metrics = []
    oracle_actions: dict[str, int] = {}
    for seed in seeds:
        action = _oracle_action(env, seed)
        oracle_actions[str(seed)] = action
        oracle_metrics.append(
            evaluate_policy(
                env,
                _FixedActionPolicy(action),
                episodes=1,
                seed=seed,
            )
        )
    results["oracle"] = _pool(oracle_metrics)
    results["oracle"]["actions"] = oracle_actions

    old_metrics = []
    for q_seed in q_seeds:
        old_policy = TabularQPolicy()
        old_policy.train(
            env,
            episodes=tabular_episodes,
            seed=q_seed,
            train_seed_start=train_seed_start + q_seed * 1000,
        )
        old_metrics.extend(
            [
                evaluate_policy(env, old_policy, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    results["tabular_q"] = _pool(old_metrics)

    compact_metrics = []
    compact_per_policy: dict[str, dict[str, Any]] = {}
    for q_seed in q_seeds:
        compact_policy = CompactQPolicy()
        compact_policy.train(
            env,
            episodes=compact_episodes,
            seed=q_seed,
            train_seed_start=train_seed_start + q_seed * 1000,
        )
        metrics = [
            evaluate_policy(env, compact_policy, episodes=1, seed=seed)
            for seed in seeds
        ]
        compact_metrics.extend(metrics)
        compact_per_policy[str(q_seed)] = _pool(metrics)
    results["compact_q"] = _pool(compact_metrics)
    results["compact_q"]["per_policy"] = compact_per_policy
    return results


def write_crew_layout_q_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "crew_layout_q_results.json").write_text(
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
        "# Twin-line crew assignment — layout-aware Q",
        "",
        f"Evaluation seeds {config['seeds'][0]}–{config['seeds'][-1]} "
        f"({len(config['seeds'])} seeds); success ≥ "
        f"{config['success_score']}.",
        "",
        "| policy | mean score | 95% CI | min | max | success |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in (
        "noop",
        "single_edf",
        "random",
        "parallel_nearest",
        "parallel_greedy",
        "tabular_q",
        "compact_q",
        "oracle",
    ):
        result = results[name]
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['min_score']:.0f} | {result['max_score']:.0f} | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Compact Q per policy",
            "",
            "| Q seed | mean score | success |",
            "|---|---:|---:|",
        ]
    )
    for q_seed, result in results["compact_q"][
        "per_policy"
    ].items():
        lines.append(
            f"| {q_seed} | {result['mean_score']:.2f} | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Per-seed scores",
            "",
            "| seed | old Q mean | compact Q mean | oracle |",
            "|---:|---:|---:|---:|",
        ]
    )
    n_seeds = len(config["seeds"])
    q_count = max(1, len(results["tabular_q"]["per_seed"]) // n_seeds)
    for index, seed in enumerate(config["seeds"]):
        old_scores = [
            results["tabular_q"]["per_seed"][q * n_seeds + index][
                "scores"
            ][0]
            for q in range(q_count)
        ]
        compact_scores = [
            results["compact_q"]["per_seed"][q * n_seeds + index][
                "scores"
            ][0]
            for q in range(q_count)
        ]
        oracle_score = results["oracle"]["per_seed"][index]["scores"][0]
        lines.append(
            f"| {seed} | {float(np.mean(old_scores)):.1f} | "
            f"{float(np.mean(compact_scores)):.1f} | "
            f"{oracle_score:.0f} |"
        )
    lines.extend(
        [
            "",
            "Oracle pairs: "
            + ", ".join(
                f"{seed}:{action}"
                for seed, action in results["oracle"]["actions"].items()
            ),
        ]
    )
    (out / "crew_layout_q_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "crew_layout_q_report.md"
