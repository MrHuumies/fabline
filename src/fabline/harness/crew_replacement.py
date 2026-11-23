"""Replacement-crew handoff on the three-bridge triage task."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.crew_replan import CrewReplanConfig, CrewReplanEnv
from fabline.env.multi_crew import ROLES
from fabline.harness.crew_multi_orphan import SequencePolicy, _oracle_sequence
from fabline.harness.crew_replan import (
    NoReplanPolicy,
    ParallelGreedyPolicy,
    ParallelNearestPolicy,
    RecallAwarePolicy,
    _pool,
    evaluate_policy,
)
from fabline.harness.multi_crew import NoopPolicy, SingleEDFPolicy
from fabline.worlds.factory.config import FactoryConfig


def _remaining(info: dict[str, Any]) -> list[str]:
    return [
        role
        for role in ROLES
        if info["roles"][role]["outage"] > 0
        and (
            info["roles"][role]["degraded"]
            or info["roles"][role]["failed"]
        )
    ]


def _pair_action(first: str | None, second: str | None) -> int:
    return (
        (ROLES.index(first) + 1 if first else 0) * 4
        + (ROLES.index(second) + 1 if second else 0)
    )


class ReplacementNearest:
    name = "replacement_nearest"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "initial":
            return ParallelNearestPolicy().act(observation, info, mask)
        roles = _remaining(info)
        if not roles:
            return 0
        first = min(
            roles, key=lambda role: info["roles"][role]["distance_a"]
        )
        rest = [role for role in roles if role != first]
        second = (
            min(rest, key=lambda role: info["roles"][role]["distance_b"])
            if rest
            else None
        )
        action = _pair_action(first, second)
        return action if mask[action] else 0


class ReplacementGreedy:
    name = "replacement_greedy"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "initial":
            return ParallelGreedyPolicy().act(observation, info, mask)
        roles = _remaining(info)
        best = (0.0, 0)
        for first in [None, *roles]:
            for second in [None, *roles]:
                if first is not None and first == second:
                    continue
                action = _pair_action(first, second)
                if not mask[action]:
                    continue
                value = 0.0
                if first is not None:
                    wire = info["roles"][first]
                    value += wire["outage"] / max(1, wire["service_a"])
                if second is not None:
                    wire = info["roles"][second]
                    value += wire["outage"] / max(1, wire["service_b"])
                if value > best[0]:
                    best = (value, action)
        return best[1]


class ReplacementAware:
    name = "replacement_aware"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "initial":
            return RecallAwarePolicy().act(observation, info, mask)
        roles = _remaining(info)
        if not roles:
            return 0
        first = min(
            roles, key=lambda role: info["roles"][role]["deadline"]
        )
        rest = [role for role in roles if role != first]
        second = (
            min(rest, key=lambda role: info["roles"][role]["deadline"])
            if rest
            else None
        )
        action = _pair_action(first, second)
        return action if mask[action] else 0


def _oracle_replacement(
    env: CrewReplanEnv,
    seed: int,
) -> tuple[int, int]:
    best = (-1.0, 0, 0)
    for initial in range(env.n_actions):
        for replan in range(env.n_actions):
            policy = SequencePolicy(initial, [replan])
            score = evaluate_policy(
                env, policy, episodes=1, seed=seed
            ).mean_score
            if score > best[0]:
                best = (score, initial, replan)
    return best[1], best[2]


def run_crew_replacement(
    config: FactoryConfig,
    replan: CrewReplanConfig,
    *,
    seeds: tuple[int, ...] = (19000,),
) -> dict[str, dict[str, Any]]:
    no_replacement = CrewReplanEnv(
        config,
        CrewReplanConfig(
            **{
                **replan.__dict__,
                "replacement": False,
                "replan_jobs": 2,
            }
        ),
    )
    replacement = CrewReplanEnv(
        config,
        CrewReplanConfig(
            **{
                **replan.__dict__,
                "replacement": True,
                "replan_jobs": 1,
            }
        ),
    )
    results: dict[str, dict[str, Any]] = {}
    no_policies: dict[str, Any] = {
        "noop": NoopPolicy(),
        "single_edf": SingleEDFPolicy(),
        "nearest": ParallelNearestPolicy(),
        "greedy": ParallelGreedyPolicy(),
        "aware": RecallAwarePolicy(),
        "no_replan": NoReplanPolicy(RecallAwarePolicy()),
    }
    replacement_policies: dict[str, Any] = {
        "nearest": ReplacementNearest(),
        "greedy": ReplacementGreedy(),
        "aware": ReplacementAware(),
    }
    for label, env, policies in (
        (
            "no_replacement",
            no_replacement,
            no_policies,
        ),
        (
            "replacement",
            replacement,
            replacement_policies,
        ),
    ):
        condition: dict[str, Any] = {}
        for name, policy in policies.items():
            condition[name] = _pool(
                [
                    evaluate_policy(env, policy, episodes=1, seed=seed)
                    for seed in seeds
                ]
            )
        if label == "no_replacement":
            oracle_metrics = []
            oracle_actions: dict[str, Any] = {}
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
        else:
            oracle_metrics = []
            oracle_actions = {}
            for seed in seeds:
                initial, replan_action = _oracle_replacement(env, seed)
                oracle_actions[str(seed)] = [initial, replan_action]
                oracle_metrics.append(
                    evaluate_policy(
                        env,
                        SequencePolicy(initial, [replan_action]),
                        episodes=1,
                        seed=seed,
                    )
                )
        condition["oracle"] = _pool(oracle_metrics)
        condition["oracle"]["actions"] = oracle_actions
        results[label] = condition
    return results


def write_crew_replacement_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "crew_replacement_results.json").write_text(
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
        "# Replacement crew handoff",
        "",
        f"Failure/recall {config['failure_tick']}; success ≥ "
        f"{config['success_score']}.",
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
            "no_replan",
            "oracle",
        ):
            if policy not in condition:
                continue
            result = condition[policy]
            lines.append(
                f"| {label} | {policy} | {result['mean_score']:.2f} "
                f"[{result['score_ci'][0]:.2f}, "
                f"{result['score_ci'][1]:.2f}] | "
                f"{result['success_rate']:.2f} |"
            )
    lines.extend(["", "Oracle actions:"])
    for label, condition in results.items():
        lines.append(f"- {label}: " + ", ".join(
            f"{seed}:{actions}"
            for seed, actions in condition["oracle"]["actions"].items()
        ))
    (out / "crew_replacement_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "crew_replacement_report.md"
