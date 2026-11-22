"""Evaluate a compact-Q ensemble on the twin-line crew task."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fabline.env.multi_crew import MultiCrewConfig, MultiCrewEnv
from fabline.harness.crew_layout_q import _pool
from fabline.harness.layout_q import CompactQPolicy, EnsembleQPolicy
from fabline.harness.multi_crew import (
    NoopPolicy,
    ParallelGreedyPolicy,
    ParallelNearestPolicy,
    RandomPolicy,
    SingleEDFPolicy,
    _FixedActionPolicy,
    _oracle_action,
    evaluate_policy,
)
from fabline.worlds.factory.config import FactoryConfig


def run_crew_layout_ensemble(
    config: FactoryConfig,
    multi: MultiCrewConfig | None = None,
    *,
    seeds: tuple[int, ...] = (9000,),
    q_seeds: tuple[int, ...] = (0, 1, 2),
    episodes: int = 2000,
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

    policies: list[CompactQPolicy] = []
    single_metrics = []
    single_per_policy: dict[str, dict[str, Any]] = {}
    for q_seed in q_seeds:
        policy = CompactQPolicy()
        policy.train(
            env,
            episodes=episodes,
            seed=q_seed,
            train_seed_start=train_seed_start + q_seed * 1000,
        )
        policies.append(policy)
        metrics = [
            evaluate_policy(env, policy, episodes=1, seed=seed)
            for seed in seeds
        ]
        single_metrics.extend(metrics)
        single_per_policy[str(q_seed)] = _pool(metrics)
    results["compact_q_single"] = _pool(single_metrics)
    results["compact_q_single"]["per_policy"] = single_per_policy

    mean_policy = EnsembleQPolicy(policies, mode="mean")
    vote_policy = EnsembleQPolicy(policies, mode="vote")
    results["ensemble_mean"] = _pool(
        [
            evaluate_policy(env, mean_policy, episodes=1, seed=seed)
            for seed in seeds
        ]
    )
    results["ensemble_vote"] = _pool(
        [
            evaluate_policy(env, vote_policy, episodes=1, seed=seed)
            for seed in seeds
        ]
    )
    return results


def write_crew_layout_ensemble_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "crew_layout_ensemble_results.json").write_text(
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
        "# Twin-line crew assignment — compact Q ensemble",
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
        "compact_q_single",
        "ensemble_mean",
        "ensemble_vote",
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
            "## Single compact Q per policy",
            "",
            "| Q seed | mean score | success |",
            "|---|---:|---:|",
        ]
    )
    for q_seed, result in results["compact_q_single"][
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
            "| seed | single mean | ensemble mean | ensemble vote | oracle |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    n_seeds = len(config["seeds"])
    q_count = max(
        1, len(results["compact_q_single"]["per_seed"]) // n_seeds
    )
    for index, seed in enumerate(config["seeds"]):
        single = [
            results["compact_q_single"]["per_seed"][
                q * n_seeds + index
            ]["scores"][0]
            for q in range(q_count)
        ]
        lines.append(
            f"| {seed} | {sum(single) / q_count:.1f} | "
            f"{results['ensemble_mean']['per_seed'][index]['scores'][0]:.0f} | "
            f"{results['ensemble_vote']['per_seed'][index]['scores'][0]:.0f} | "
            f"{results['oracle']['per_seed'][index]['scores'][0]:.0f} |"
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
    (out / "crew_layout_ensemble_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "crew_layout_ensemble_report.md"
