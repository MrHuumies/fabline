"""Sequential survivor dispatch on the twin-line layout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.crew_replan import CrewReplanConfig, CrewReplanEnv
from fabline.harness.crew_replan import (
    NoReplanPolicy,
    ParallelGreedyPolicy,
    ParallelNearestPolicy,
    RecallAwarePolicy,
    SingleEDFPolicy,
    _pool,
    evaluate_policy,
)
from fabline.harness.multi_crew import NoopPolicy
from fabline.worlds.factory.config import FactoryConfig


class SequencePolicy:
    """Fixed initial action followed by a sequence of survivor actions."""

    name = "sequence"

    def __init__(self, initial: int, replans: list[int]) -> None:
        self.initial = initial
        self.replans = replans
        self.index = 0

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "initial":
            return self.initial if mask[self.initial] else 0
        if self.index < len(self.replans):
            action = self.replans[self.index]
            self.index += 1
            return action if mask[action] else 0
        return 0


def _oracle_sequence(
    env: CrewReplanEnv,
    seed: int,
) -> tuple[int, list[int]]:
    best = (-1.0, 0, [0, 0])
    for initial in range(env.n_actions):
        for first in range(4):
            for second in range(4):
                policy = SequencePolicy(
                    initial, [first * 4, second * 4]
                )
                score = evaluate_policy(
                    env, policy, episodes=1, seed=seed
                ).mean_score
                if score > best[0]:
                    best = (score, initial, [first * 4, second * 4])
    return best[1], best[2]


def run_crew_multi_orphan(
    config: FactoryConfig,
    replan: CrewReplanConfig | None = None,
    *,
    seeds: tuple[int, ...] = (11000,),
) -> dict[str, dict[str, Any]]:
    env = CrewReplanEnv(config, replan)
    results: dict[str, dict[str, Any]] = {}
    for name, baseline in (
        ("noop", NoopPolicy()),
        ("single_edf", SingleEDFPolicy()),
        ("nearest", ParallelNearestPolicy()),
        ("greedy", ParallelGreedyPolicy()),
        ("aware", RecallAwarePolicy()),
        (
            "no_replan",
            NoReplanPolicy(RecallAwarePolicy()),
        ),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, baseline, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    oracle_metrics = []
    oracle_actions: dict[str, list[Any]] = {}
    for seed in seeds:
        initial, replans = _oracle_sequence(env, seed)
        oracle_actions[str(seed)] = [initial, *replans]
        oracle_metrics.append(
            evaluate_policy(
                env,
                SequencePolicy(initial, replans),
                episodes=1,
                seed=seed,
            )
        )
    results["oracle"] = _pool(oracle_metrics)
    results["oracle"]["actions"] = oracle_actions
    return results


def write_crew_multi_orphan_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "crew_multi_orphan_results.json").write_text(
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
        "# Sequential survivor dispatch",
        "",
        f"Failure/recall {config['failure_tick']}; replan jobs "
        f"{config['replan_jobs']}; success ≥ {config['success_score']}.",
        "",
        "| policy | mean score | 95% CI | success |",
        "|---|---:|---:|---:|",
    ]
    for name in (
        "noop",
        "single_edf",
        "nearest",
        "greedy",
        "aware",
        "no_replan",
        "oracle",
    ):
        result = results[name]
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, "
            f"{result['score_ci'][1]:.2f}] | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(["", "Oracle sequences (initial, replan1, replan2):"])
    for seed, actions in results["oracle"]["actions"].items():
        lines.append(f"- {seed}: {actions}")
    (out / "crew_multi_orphan_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "crew_multi_orphan_report.md"
