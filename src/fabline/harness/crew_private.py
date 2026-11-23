"""Private per-crew policies and comparison on the spread layout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.crew_replan import CrewReplanConfig, CrewReplanEnv
from fabline.env.crew_visibility import (
    PrivateVisibilityEnv,
    VisibilityEnv,
)
from fabline.env.multi_crew import ROLES
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


def _view(info: dict[str, Any], crew: str) -> dict[str, Any]:
    return dict(info["crew_roles"][crew])


class CrewNearestPolicy:
    """Nearest visible target for one crew, returned as a choice index."""

    def __init__(self, crew: str) -> None:
        self.crew = crew

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        view = _view(info, self.crew)
        roles = [
            role
            for role in ROLES
            if view[role]["outage"] > 0
            and view[role]["degraded"]
            and view[role]["known"]
        ]
        if not roles:
            return 0
        key = "distance_a" if self.crew == "a" else "distance_b"
        role = min(roles, key=lambda item: view[item][key])
        return ROLES.index(role) + 1


class CrewGreedyPolicy:
    def __init__(self, crew: str) -> None:
        self.crew = crew

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        view = _view(info, self.crew)
        roles = [
            role
            for role in ROLES
            if view[role]["outage"] > 0
            and view[role]["degraded"]
            and view[role]["known"]
        ]
        if not roles:
            return 0
        key = "service_a" if self.crew == "a" else "service_b"
        role = max(
            roles,
            key=lambda item: view[item]["outage"]
            / max(1, view[item][key]),
        )
        return ROLES.index(role) + 1


class CrewAwarePolicy:
    def __init__(self, crew: str) -> None:
        self.crew = crew

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        view = _view(info, self.crew)
        roles = [
            role
            for role in ROLES
            if view[role]["outage"] > 0
            and view[role]["degraded"]
            and view[role]["known"]
        ]
        if not roles:
            return 0
        role = min(roles, key=lambda item: view[item]["deadline"])
        return ROLES.index(role) + 1


class PrivatePairPolicy:
    """Compose two independent crew policies; duplicates fall back to noop."""

    name = "private_pair"

    def __init__(
        self,
        a_policy: Any,
        b_policy: Any,
    ) -> None:
        self.a_policy = a_policy
        self.b_policy = b_policy

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        a_choice = self.a_policy.act(observation, info, mask)
        if info.get("phase") == "replan":
            b_choice = 0
        else:
            b_choice = self.b_policy.act(observation, info, mask)
        if a_choice > 0 and a_choice == b_choice:
            b_choice = 0
        action = a_choice * 4 + b_choice
        if mask[action]:
            return int(action)
        if mask[a_choice * 4]:
            return int(a_choice * 4)
        if mask[b_choice]:
            return int(b_choice)
        return 0


def run_crew_private(
    config: FactoryConfig,
    replan: CrewReplanConfig | None = None,
    *,
    seeds: tuple[int, ...] = (13000,),
    radius: int = 16,
    report_age: int = 60,
) -> dict[str, dict[str, Any]]:
    base = CrewReplanEnv(config, replan)
    conditions: dict[str, tuple[Any, bool]] = {
        "global": (base, False),
        "shared_local": (
            VisibilityEnv(base, radius=radius, report_age=0),
            False,
        ),
        "shared_delayed": (
            VisibilityEnv(base, radius=radius, report_age=report_age),
            False,
        ),
        "private": (
            PrivateVisibilityEnv(base, radius=radius),
            True,
        ),
    }
    results: dict[str, dict[str, Any]] = {}
    for label, (env, private) in conditions.items():
        condition: dict[str, Any] = {}
        policies: dict[str, Any]
        if private:
            policies = {
                "nearest": PrivatePairPolicy(
                    CrewNearestPolicy("a"), CrewNearestPolicy("b")
                ),
                "greedy": PrivatePairPolicy(
                    CrewGreedyPolicy("a"), CrewGreedyPolicy("b")
                ),
                "aware": PrivatePairPolicy(
                    CrewAwarePolicy("a"), CrewAwarePolicy("b")
                ),
            }
        else:
            policies = {
                "nearest": ParallelNearestPolicy(),
                "greedy": ParallelGreedyPolicy(),
                "aware": RecallAwarePolicy(),
            }
        for name, policy in policies.items():
            condition[name] = _pool(
                [
                    evaluate_policy(env, policy, episodes=1, seed=seed)
                    for seed in seeds
                ]
            )
        if not private:
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


def write_crew_private_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "crew_private_results.json").write_text(
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
        "# Private crew views versus shared reports",
        "",
        f"Radius {config['radius']}; report age {config['report_age']}; "
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
    (out / "crew_private_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "crew_private_report.md"
