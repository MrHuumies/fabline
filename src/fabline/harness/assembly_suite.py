"""The frozen ``factory-v0.5`` assembly-edge suite orchestrator.

The suite publishes four tasks on the opt-in production tree:

- assembly control (online recipe choice),
- assembly planning (finite-horizon recipe plan),
- BOM output forecast (state-to-output regression),
- recipe-switch intervention (counterfactual effect estimation).

It writes one aggregate report and a compact expected summary.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fabline.env.assembly import AssemblyControlConfig
from fabline.harness.assembly_bom import (
    AssemblyBOMConfig,
    run_assembly_bom,
    write_assembly_bom_report,
)
from fabline.harness.assembly_control import (
    assembly_gates,
    run_assembly_control,
    write_assembly_control_report,
)
from fabline.harness.assembly_intervention import (
    AssemblyInterventionConfig,
    run_assembly_intervention,
    write_assembly_intervention_report,
)
from fabline.harness.assembly_planning import (
    AssemblyPlanningConfig,
    run_assembly_planning,
    write_assembly_planning_report,
)
from fabline.harness.factory_v02 import compare_expected_summary
from fabline.worlds.factory.config import FactoryConfig

ASSEMBLY_SUITE_ID = "factory-v0.5-assembly"
ASSEMBLY_SUITE_VERSION = "0.5.0"
EXPECTED_TOLERANCE = {"rtol": 0.03, "atol": 0.02}

HEADLINE_TASKS = (
    "assembly-control",
    "assembly-planning",
    "assembly-bom",
    "assembly-intervention",
)


@dataclass(frozen=True)
class AssemblySuiteConfig:
    fast: bool = False


def assembly_factory_config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=False,
    )


def _control_config(fast: bool) -> tuple[AssemblyControlConfig, int, int]:
    if fast:
        return (
            AssemblyControlConfig(
                episode_ticks=500,
                decision_interval=10,
                success_score=100,
            ),
            2,
            50,
        )
    return (
        AssemblyControlConfig(
            episode_ticks=500,
            decision_interval=10,
            success_score=100,
        ),
        5,
        500,
    )


def _planning_config(fast: bool) -> AssemblyPlanningConfig:
    if fast:
        return AssemblyPlanningConfig(
            blocks=5,
            block_ticks=100,
            population=6,
            elites=2,
            iterations=2,
            random_plans=8,
            success_score=100,
        )
    return AssemblyPlanningConfig()


def _bom_config(fast: bool) -> AssemblyBOMConfig:
    if fast:
        return AssemblyBOMConfig(episodes=12)
    return AssemblyBOMConfig()


def _intervention_config(fast: bool) -> AssemblyInterventionConfig:
    if fast:
        return AssemblyInterventionConfig(episodes=20)
    return AssemblyInterventionConfig()


def _planning_gates(results: dict[str, dict[str, Any]]) -> dict[str, bool]:
    scripted = max(
        float(results[name]["mean_score"])
        for name in ("always_gear", "always_assembly", "alternate", "batch_3", "frontload")
    )
    oracle = float(results["oracle"]["mean_score"])
    cem = results["cem"]
    return {
        "H1_planning_gap": oracle >= scripted + 10.0,
        "H2_cem_over_random": (
            float(cem["mean_score"])
            >= float(results["random"]["mean_score"]) + 10.0
        ),
        "H3_cem_quality": float(cem["mean_score"]) >= oracle - 10.0,
        "H4_success": float(cem["success_rate"]) >= 0.60,
    }


def _control_summary(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    gates = assembly_gates(results)
    return {
        "results": results,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _planning_summary(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    gates = _planning_gates(results)
    return {
        "results": results,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _regression_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset": report["dataset"],
        "metrics": report["metrics"],
        "gates": report["gates"],
        "passed": not bool(report["diagnostic"]),
    }


def _intervention_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset": report["dataset"],
        "metrics": report["metrics"],
        "decisions": report["decisions"],
        "gates": report["gates"],
        "passed": not bool(report["diagnostic"]),
    }


def _compact_rows(
    rows: dict[str, dict[str, Any]],
    keys: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    return {
        name: {key: row[key] for key in keys if key in row}
        for name, row in rows.items()
    }


def build_expected_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Build the compact, deterministic expected summary for factory-v0.5."""

    tasks: dict[str, Any] = {}
    control = report["tasks"].get("assembly-control")
    if control is not None:
        tasks["assembly-control"] = {
            "results": _compact_rows(
                control["results"],
                (
                    "mean_score",
                    "score_ci",
                    "success_rate",
                    "mean_switches",
                ),
            ),
            "gates": control["gates"],
        }
    planning = report["tasks"].get("assembly-planning")
    if planning is not None:
        tasks["assembly-planning"] = {
            "results": _compact_rows(
                planning["results"],
                ("mean_score", "score_ci", "success_rate"),
            ),
            "gates": planning["gates"],
        }
    bom = report["tasks"].get("assembly-bom")
    if bom is not None:
        tasks["assembly-bom"] = {
            "dataset": bom["dataset"],
            "metrics": {
                name: {
                    metric: values["test"][metric]
                    for metric in ("r2", "mae")
                    if metric in values.get("test", {})
                }
                for name, values in bom["metrics"].items()
                if "test" in values
            },
            "gates": bom["gates"],
        }
    intervention = report["tasks"].get("assembly-intervention")
    if intervention is not None:
        tasks["assembly-intervention"] = {
            "dataset": intervention["dataset"],
            "metrics": {
                name: {
                    metric: values["test"][metric]
                    for metric in ("r2", "mae")
                    if metric in values.get("test", {})
                }
                for name, values in intervention["metrics"].items()
                if "test" in values
            },
            "decisions": {
                key: intervention["decisions"][key]
                for key in (
                    "policy_value",
                    "oracle_value",
                    "always_switch",
                    "always_continue",
                    "regret",
                    "oracle_gain",
                    "model_gain",
                )
            },
            "gates": intervention["gates"],
        }
    return {
        "benchmark": "factory-v0.5",
        "version": "0.5.0",
        "date": "2026-11-27",
        "world_version": "factory-0.1.0",
        "plan": "assembly-v0.5",
        "tolerance": EXPECTED_TOLERANCE,
        "headline_tasks": list(HEADLINE_TASKS),
        "tasks": tasks,
    }


def compare_assembly_expected(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> list[str]:
    return compare_expected_summary(expected, actual)


def run_assembly_suite(
    out_dir: str | Path,
    config: AssemblySuiteConfig | None = None,
) -> dict[str, Any]:
    cfg = config or AssemblySuiteConfig()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    factory = assembly_factory_config()
    tasks: dict[str, Any] = {}

    control_config, episodes, q_episodes = _control_config(cfg.fast)
    control = run_assembly_control(
        factory,
        control_config,
        episodes=episodes,
        q_episodes=q_episodes,
    )
    write_assembly_control_report(
        out / "assembly-control",
        control,
        config={
            "success_score": control_config.success_score,
            "seeds": [0, 1, 2, 3, 4] if not cfg.fast else [0, 1],
            "episodes": episodes,
            "q_episodes": q_episodes,
        },
    )
    tasks["assembly-control"] = _control_summary(control)

    planning_config = _planning_config(cfg.fast)
    planning = run_assembly_planning(factory, planning_config)
    write_assembly_planning_report(
        out / "assembly-planning",
        planning,
        config={
            "blocks": planning_config.blocks,
            "block_ticks": planning_config.block_ticks,
            "population": planning_config.population,
            "elites": planning_config.elites,
            "iterations": planning_config.iterations,
            "random_plans": planning_config.random_plans,
            "success_score": planning_config.success_score,
        },
    )
    tasks["assembly-planning"] = _planning_summary(planning)

    bom_config = _bom_config(cfg.fast)
    bom = run_assembly_bom(factory, bom_config)
    write_assembly_bom_report(out / "assembly-bom", bom)
    tasks["assembly-bom"] = _regression_summary(bom)

    intervention_config = _intervention_config(cfg.fast)
    intervention = run_assembly_intervention(factory, intervention_config)
    write_assembly_intervention_report(
        out / "assembly-intervention", intervention
    )
    tasks["assembly-intervention"] = _intervention_summary(intervention)

    report = {
        "benchmark": ASSEMBLY_SUITE_ID,
        "version": ASSEMBLY_SUITE_VERSION,
        "status": "frozen",
        "config": asdict(cfg),
        "tasks": tasks,
        "summary": {
            "tasks": len(tasks),
            "passed": sum(1 for task in tasks.values() if task.get("passed")),
        },
    }
    (out / "assembly_suite_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (out / "assembly_suite_report.md").write_text(
        _render_report(report), encoding="utf-8"
    )
    return report


def _render_report(report: dict[str, Any]) -> str:
    lines = [
        "# factory-v0.5 assembly suite (frozen)",
        "",
        f"- tasks: {report['summary']['tasks']}",
        f"- passed: {report['summary']['passed']}",
        "",
        "| task | status | key result |",
        "|---|---|---|",
    ]
    for name, task in report["tasks"].items():
        if name == "assembly-control":
            key = (
                "Q "
                f"{task['results']['tabular_q']['mean_score']:.1f} vs random "
                f"{task['results']['random']['mean_score']:.1f}, gear "
                f"{task['results']['always_gear']['mean_score']:.1f}"
            )
        elif name == "assembly-planning":
            key = (
                f"CEM {task['results']['cem']['mean_score']:.1f} vs oracle "
                f"{task['results']['oracle']['mean_score']:.1f}, frontload "
                f"{task['results']['frontload']['mean_score']:.1f}"
            )
        elif name == "assembly-bom":
            key = (
                "GBDT R² "
                f"{task['metrics']['gbdt']['test']['r2']:.3f}, linear "
                f"{task['metrics']['linear']['test']['r2']:.3f}"
            )
        elif name == "assembly-intervention":
            key = (
                "GBDT R² "
                f"{task['metrics']['gbdt']['test']['r2']:.3f}; gain "
                f"{task['decisions']['model_gain']:+.2f} of "
                f"{task['decisions']['oracle_gain']:+.2f}"
            )
        else:
            key = ""
        status = "pass" if task.get("passed") else "fail"
        lines.append(f"| {name} | {status} | {key} |")
    lines.extend(
        [
            "",
            "The assembly edge is opt-in; frozen v0.1-v0.4 assets are unchanged.",
            "See `benchmarks/factory-v0.5/` for the card, spec, and expected",
            "summary.",
            "",
        ]
    )
    return "\n".join(lines)
