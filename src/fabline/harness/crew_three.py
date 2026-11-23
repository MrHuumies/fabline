"""Three-crew assignment baselines and evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.multi_crew import ROLES, MultiCrewConfig
from fabline.env.three_crew import ThreeCrewEnv
from fabline.harness.multi_crew import (
    NoopPolicy,
    SingleEDFPolicy,
    _pool,
    evaluate_policy,
)
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


def _action(first: str | None, second: str | None, third: str | None) -> int:
    def choice(role: str | None) -> int:
        return 0 if role is None else ROLES.index(role) + 1

    return (
        choice(first) * 16
        + choice(second) * 4
        + choice(third)
    )


class ThreeNearest:
    name = "three_nearest"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        roles = _remaining(info)
        picks: list[str | None] = []
        for crew in ("a", "b", "c"):
            if not roles:
                picks.append(None)
                continue
            key = f"distance_{crew}"
            role = min(roles, key=lambda item: info["roles"][item][key])
            picks.append(role)
            roles = [item for item in roles if item != role]
        action = _action(*picks)
        return action if mask[action] else 0


class ThreeAware:
    name = "three_aware"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        roles = _remaining(info)
        picks: list[str | None] = []
        for _crew in ("a", "b", "c"):
            if not roles:
                picks.append(None)
                continue
            role = min(
                roles, key=lambda item: info["roles"][item]["deadline"]
            )
            picks.append(role)
            roles = [item for item in roles if item != role]
        action = _action(*picks)
        return action if mask[action] else 0


class ThreeGreedy:
    name = "three_greedy"

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        best = (0.0, 0)
        for action in np.flatnonzero(mask):
            first = int(action) // 16
            second = (int(action) // 4) % 4
            third = int(action) % 4
            value = 0.0
            for choice, crew in (
                (first, "a"),
                (second, "b"),
                (third, "c"),
            ):
                if choice == 0:
                    continue
                wire = info["roles"][ROLES[choice - 1]]
                service = wire[f"service_{crew}"]
                value += wire["outage"] / max(1, service)
            if value > best[0]:
                best = (value, int(action))
        return best[1]


class TwoCrewPolicy:
    name = "two_crew"

    def __init__(self, mode: str = "nearest") -> None:
        self.mode = mode

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        roles = _remaining(info)
        if not roles:
            return 0
        first: str | None
        second: str | None
        if self.mode == "nearest":
            first = min(
                roles,
                key=lambda item: info["roles"][item]["distance_a"],
            )
            rest = [item for item in roles if item != first]
            second = (
                min(
                    rest,
                    key=lambda item: info["roles"][item]["distance_b"],
                )
                if rest
                else None
            )
        else:
            best = (0.0, 0, None)
            for first in [None, *roles]:
                for second in [None, *roles]:
                    if first is not None and first == second:
                        continue
                    value = 0.0
                    if first is not None:
                        wire = info["roles"][first]
                        value += wire["outage"] / max(1, wire["service_a"])
                    if second is not None:
                        wire = info["roles"][second]
                        value += wire["outage"] / max(1, wire["service_b"])
                    if value > best[0]:
                        best = (value, _action(first, second, None), None)
            return int(best[1])
        action = _action(first, second, None)
        return action if mask[action] else 0


def _oracle_action(
    env: ThreeCrewEnv,
    seed: int,
    *,
    crews: int = 3,
) -> int:
    best = (-1.0, 0)
    for action in range(env.n_actions):
        if crews == 2 and action % 4 != 0:
            continue
        observation, info = env.reset(seed)
        done = False
        while not done and not env.action_mask()[action]:
            observation, _, terminated, truncated, info = env.step(0)
            done = terminated or truncated
        if not done:
            _, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        if info["score"] > best[0]:
            best = (float(info["score"]), action)
    return best[1]


def run_three_crew(
    config: FactoryConfig,
    multi: MultiCrewConfig | None = None,
    *,
    seeds: tuple[int, ...] = (0,),
) -> dict[str, dict[str, Any]]:
    env = ThreeCrewEnv(config, multi)
    results: dict[str, dict[str, Any]] = {}
    for name, policy in (
        ("noop", NoopPolicy()),
        ("single_edf", SingleEDFPolicy()),
        ("two_nearest", TwoCrewPolicy("nearest")),
        ("two_greedy", TwoCrewPolicy("greedy")),
        ("three_nearest", ThreeNearest()),
        ("three_greedy", ThreeGreedy()),
        ("three_aware", ThreeAware()),
    ):
        results[name] = _pool(
            [
                evaluate_policy(env, policy, episodes=1, seed=seed)
                for seed in seeds
            ]
        )
    for name, crews in (("two_oracle", 2), ("three_oracle", 3)):
        metrics = []
        actions: dict[str, int] = {}
        for seed in seeds:
            action = _oracle_action(env, seed, crews=crews)
            actions[str(seed)] = action
            metrics.append(
                evaluate_policy(
                    env,
                    _FixedActionPolicy(action),
                    episodes=1,
                    seed=seed,
                )
            )
        results[name] = _pool(metrics)
        results[name]["actions"] = actions
    return results


class _FixedActionPolicy:
    name = "fixed"

    def __init__(self, action: int) -> None:
        self.action = action

    def act(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
        mask: np.ndarray,
    ) -> int:
        return self.action if mask[self.action] else 0


def write_three_crew_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "three_crew_results.json").write_text(
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
        "# Three-crew assignment",
        "",
        f"Success ≥ {config['success_score']}; seeds "
        f"{config['seeds'][0]}–{config['seeds'][-1]}.",
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
    lines.extend(["", "Oracle actions:"])
    for name in ("two_oracle", "three_oracle"):
        lines.append(
            f"- {name}: "
            + ", ".join(
                f"{seed}:{action}"
                for seed, action in results[name]["actions"].items()
            )
        )
    (out / "three_crew_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "three_crew_report.md"
