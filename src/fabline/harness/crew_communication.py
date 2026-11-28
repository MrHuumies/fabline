"""Scripted baselines for local-view crew communication."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from fabline.env.crew_communication import (
    N_COMM_ACTIONS,
    CrewCommConfig,
    CrewCommEnv,
)
from fabline.env.sequential_crew import SequentialCrewConfig
from fabline.harness.sequential_crew import _distinct_pair, _pursue
from fabline.harness.stats import bootstrap_mean_ci
from fabline.worlds.factory.config import FactoryConfig


class CommPolicy(Protocol):
    name: str

    def act(self, env: CrewCommEnv) -> tuple[int, int]: ...


class SharedAssignedPolicy:
    """Full-information Phase 1 assignment; never reports."""

    name = "shared"

    def act(self, env: CrewCommEnv) -> tuple[int, int]:
        base = env.base
        failed = [
            index
            for index, target in enumerate(base.targets)
            if target.failed
        ]
        first, second = _distinct_pair(base, failed)
        actions = [4, 4]
        if first is not None:
            actions[0] = _pursue(base, 0, first)
        if second is not None:
            actions[1] = _pursue(base, 1, second)
        return actions[0], actions[1]


class LocalCommPolicy:
    """Local-view policy; optionally reports discovered failures."""

    def __init__(self, *, report: bool, name: str) -> None:
        self.report = report
        self.name = name

    def _act_one(self, env: CrewCommEnv, crew_index: int) -> int:
        base = env.base
        visible_failed = [
            index
            for index in range(len(base.targets))
            if env._visible(crew_index, index)
            and base.targets[index].failed
        ]
        if self.report and env.report_budget[crew_index] > 0:
            for index in visible_failed:
                if env.has_pending_report(crew_index, index):
                    continue
                report = env.reports[index]
                if report is None or not report["failed"]:
                    return 6
        reported_failed = [
            index
            for index in range(len(base.targets))
            if not env._visible(crew_index, index)
            and _report_failed(env, index)
            and base.targets[index].failed
        ]
        known = visible_failed + reported_failed
        if known:
            index = min(
                known,
                key=lambda item: (
                    base.distance(
                        base.positions[crew_index], base.targets[item]
                    ),
                    item,
                ),
            )
            if base.adjacent(crew_index, index):
                return 5
            return _pursue(base, crew_index, index)
        unknown = [
            index
            for index in range(len(base.targets))
            if not env._visible(crew_index, index)
            and env.reports[index] is None
        ]
        if unknown:
            index = min(
                unknown,
                key=lambda item: (
                    base.distance(
                        base.positions[crew_index], base.targets[item]
                    ),
                    item,
                ),
            )
            return _pursue(base, crew_index, index)
        index = min(
            range(len(base.targets)),
            key=lambda item: base.distance(
                base.positions[crew_index], base.targets[item]
            ),
        )
        return _pursue(base, crew_index, index)

    def act(self, env: CrewCommEnv) -> tuple[int, int]:
        return (
            self._act_one(env, 0),
            self._act_one(env, 1),
        )


class RandomCommPolicy:
    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    def act(self, env: CrewCommEnv) -> tuple[int, int]:
        indices = np.flatnonzero(env.joint_mask())
        index = int(self.rng.choice(indices.tolist()))
        return divmod(index, N_COMM_ACTIONS)


@dataclass
class CommMetrics:
    mean_score: float
    success_rate: float
    mean_repairs: float
    mean_steps: float
    mean_messages: float
    mean_delivered: float
    scores: list[float]
    successes: list[float]
    repairs: list[float]
    steps: list[float]
    messages: list[float]
    delivered: list[float]


def evaluate_policy(
    env: CrewCommEnv,
    policy: CommPolicy,
    *,
    episodes: int = 5,
    seed: int = 0,
) -> CommMetrics:
    scores: list[float] = []
    successes: list[float] = []
    repairs: list[float] = []
    steps: list[float] = []
    messages: list[float] = []
    delivered: list[float] = []
    for episode in range(episodes):
        env.reset(seed=seed + episode)
        done = False
        while not done:
            _, _, terminated, truncated, info = env.step(policy.act(env))
            done = terminated or truncated
        scores.append(float(info["score"]))
        successes.append(1.0 if info["success"] else 0.0)
        repairs.append(float(info["repairs"]))
        steps.append(float(info["steps"]))
        messages.append(float(info["messages_used"]))
        delivered.append(float(info["reports_delivered"]))
    return CommMetrics(
        mean_score=float(np.mean(scores)),
        success_rate=float(np.mean(successes)),
        mean_repairs=float(np.mean(repairs)),
        mean_steps=float(np.mean(steps)),
        mean_messages=float(np.mean(messages)),
        mean_delivered=float(np.mean(delivered)),
        scores=scores,
        successes=successes,
        repairs=repairs,
        steps=steps,
        messages=messages,
        delivered=delivered,
    )


def _report_failed(env: CrewCommEnv, index: int) -> bool:
    report = env.reports[index]
    return report is not None and bool(report["failed"])


def _pool(metrics: list[CommMetrics]) -> dict[str, Any]:
    scores = [value for item in metrics for value in item.scores]
    successes = [value for item in metrics for value in item.successes]
    repairs = [value for item in metrics for value in item.repairs]
    steps = [value for item in metrics for value in item.steps]
    messages = [value for item in metrics for value in item.messages]
    delivered = [value for item in metrics for value in item.delivered]
    return {
        "mean_score": float(np.mean(scores)),
        "score_ci": list(bootstrap_mean_ci(scores)),
        "success_rate": float(np.mean(successes)),
        "success_ci": list(bootstrap_mean_ci(successes)),
        "mean_repairs": float(np.mean(repairs)),
        "mean_steps": float(np.mean(steps)),
        "mean_messages": float(np.mean(messages)),
        "mean_delivered": float(np.mean(delivered)),
        "per_seed": [item.mean_score for item in metrics],
    }


def validate_seeds(
    env: CrewCommEnv,
    seeds: tuple[int, ...],
    episodes: int,
) -> None:
    for seed in seeds:
        for episode in range(episodes):
            actual = seed + episode
            try:
                env.reset(seed=actual)
            except RuntimeError as exc:
                raise RuntimeError(
                    f"invalid communication seed {actual}: {exc}"
                ) from exc


def run_crew_communication(
    config: FactoryConfig,
    crew: SequentialCrewConfig,
    comm: CrewCommConfig | None = None,
    *,
    seeds: tuple[int, ...] = (120000, 120001, 120002, 120003, 120004),
    episodes: int = 5,
) -> dict[str, dict[str, Any]]:
    env = CrewCommEnv(config, crew, comm)
    validate_seeds(env, seeds, episodes)
    results: dict[str, dict[str, Any]] = {}
    policies: tuple[tuple[str, CommPolicy], ...] = (
        ("shared", SharedAssignedPolicy()),
        (
            "local_no_report",
            LocalCommPolicy(report=False, name="local_no_report"),
        ),
        (
            "local_report",
            LocalCommPolicy(report=True, name="local_report"),
        ),
    )
    for name, policy in policies:
        results[name] = _pool(
            [
                evaluate_policy(env, policy, episodes=episodes, seed=seed)
                for seed in seeds
            ]
        )
    results["random"] = _pool(
        [
            evaluate_policy(
                env,
                RandomCommPolicy(seed),
                episodes=episodes,
                seed=seed,
            )
            for seed in seeds
        ]
    )
    return results


def communication_gates(
    results: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    local = float(results["local_no_report"]["mean_score"])
    report = float(results["local_report"]["mean_score"])
    random_score = float(results["random"]["mean_score"])
    h1 = report >= local + 10.0
    h2 = float(results["shared"]["success_rate"]) >= 0.60
    h3 = report >= random_score + 10.0
    h4 = float(results["local_report"]["success_rate"]) >= 0.60
    return {
        "H1_communication_gain": h1,
        "H2_shared_success": h2,
        "H3_report_over_random": h3,
        "H4_report_success": h4,
        "H5_cost_reported": True,
        "challenge": bool(h1 and h2 and not h4),
    }


def write_crew_communication_report(
    out: str | Path,
    results: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    gates = communication_gates(results)
    payload = {"config": config, "results": results, "gates": gates}
    (out / "crew_communication_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Crew communication",
        "",
        f"- local radius: {config['visibility_radius']}",
        f"- report budget: {config['report_budget']}",
        f"- report delay: {config['report_delay']}",
        f"- report cost: {config['report_cost']}",
        f"- seeds: {config['seeds']}",
        "",
        "| policy | score | success | messages | delivered |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in results.items():
        lines.append(
            f"| {name} | {row['mean_score']:.2f} "
            f"[{row['score_ci'][0]:.2f}, {row['score_ci'][1]:.2f}] | "
            f"{row['success_rate']:.2f} | {row['mean_messages']:.2f} | "
            f"{row['mean_delivered']:.2f} |"
        )
    lines.extend(["", "## Gates", "", "| Gate | Result |", "|---|---|"])
    for name, passed in gates.items():
        result = "yes" if name == "challenge" and passed else (
            "no" if name == "challenge" else ("pass" if passed else "fail")
        )
        lines.append(f"| {name} | {result} |")
    lines.append("")
    path = out / "crew_communication_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
