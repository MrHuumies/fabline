"""Three-crew initial assignment with A/C recovery baselines."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.multi_crew import ROLES
from fabline.env.three_crew_replan import ThreeCrewReplanEnv
from fabline.harness.crew_replan import _pool, evaluate_policy
from fabline.harness.crew_three import (
    ThreeAware,
    ThreeGreedy,
    ThreeNearest,
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


class ThreeReplanNearest:
    name = "three_nearest"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "initial":
            return ThreeNearest().act(observation, info, mask)
        roles = _remaining(info)
        if not roles:
            return 0
        first = min(roles, key=lambda role: info["roles"][role]["distance_a"])
        rest = [role for role in roles if role != first]
        second = (
            min(rest, key=lambda role: info["roles"][role]["distance_c"])
            if rest
            else None
        )
        action = _pair_action(first, second)
        return action if mask[action] else 0


class ThreeReplanGreedy:
    name = "three_greedy"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "initial":
            return ThreeGreedy().act(observation, info, mask)
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
                    value += wire["outage"] / max(1, wire["service_c"])
                if value > best[0]:
                    best = (value, action)
        return best[1]


class ThreeReplanAware:
    name = "three_aware"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "initial":
            return ThreeAware().act(observation, info, mask)
        roles = _remaining(info)
        if not roles:
            return 0
        first = min(roles, key=lambda role: info["roles"][role]["deadline"])
        rest = [role for role in roles if role != first]
        second = (
            min(rest, key=lambda role: info["roles"][role]["deadline"])
            if rest
            else None
        )
        action = _pair_action(first, second)
        return action if mask[action] else 0


class ThreeNoReplan:
    name = "three_no_replan"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "replan":
            return 0
        return ThreeGreedy().act(observation, info, mask)


class ThreeSequence:
    name = "three_sequence"

    def __init__(self, initial: int, replan: int) -> None:
        self.initial = initial
        self.replan = replan

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        if info["phase"] == "initial":
            return self.initial if mask[self.initial] else 0
        return self.replan if mask[self.replan] else 0


def _oracle_replan(env: Any, seed: int) -> tuple[int, int]:
    best = (-1.0, 0, 0)
    for initial in range(64):
        for replan in range(16):
            score = evaluate_policy(
                env,
                ThreeSequence(initial, replan),
                episodes=1,
                seed=seed,
            ).mean_score
            if score > best[0]:
                best = (score, initial, replan)
    return best[1], best[2]


def run_three_crew_replan(
    config: FactoryConfig,
    replan: Any,
    *,
    seeds: tuple[int, ...] = (23000,),
) -> dict[str, dict[str, Any]]:
    env: Any = ThreeCrewReplanEnv(config, replan)
    results: dict[str, dict[str, Any]] = {}
    for name, policy in (
        ("noop", NoopPolicy()),
        ("single_edf", SingleEDFPolicy()),
        ("three_nearest", ThreeReplanNearest()),
        ("three_greedy", ThreeReplanGreedy()),
        ("three_aware", ThreeReplanAware()),
        ("three_no_replan", ThreeNoReplan()),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, policy, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    metrics = []
    actions: dict[str, Any] = {}
    for seed in seeds:
        initial, replan_action = _oracle_replan(env, seed)
        actions[str(seed)] = [initial, replan_action]
        metrics.append(
            evaluate_policy(
                env,
                ThreeSequence(initial, replan_action),
                episodes=1,
                seed=seed,
            )
        )
    results["oracle"] = _pool(metrics)
    results["oracle"]["actions"] = actions
    return results


def write_three_crew_replan_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "three_crew_replan_results.json").write_text(
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
        "# Three-crew assignment with recall",
        "",
        f"Recall {config['recall_tick']}; success ≥ "
        f"{config['success_score']}.",
        "",
        "| policy | mean score | 95% CI | success |",
        "|---|---:|---:|---:|",
    ]
    for name, result in results.items():
        lines.append(
            f"| {name} | {result['mean_score']:.2f} "
            f"[{result['score_ci'][0]:.2f}, {result['score_ci'][1]:.2f}] | "
            f"{result['success_rate']:.2f} |"
        )
    lines.extend(["", "Oracle actions (initial, replan):"])
    for seed, actions in results["oracle"]["actions"].items():
        lines.append(f"- {seed}: {actions}")
    (out / "three_crew_replan_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "three_crew_replan_report.md"
