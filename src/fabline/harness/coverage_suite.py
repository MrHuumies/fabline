"""The 0.5.0 coverage-suite orchestrator.

This is the frozen `factory-v0.4` coverage tier. It runs the public coverage
tasks that are available in this tree and writes one aggregate report. Task
status and gates are reported per task.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fabline.env.crew_replan import CrewReplanConfig
from fabline.env.crew_schedule import CrewScheduleConfig
from fabline.env.preventive_threshold import ThresholdConfig
from fabline.env.preventive_wire import PreventiveWireConfig
from fabline.env.recipe import RecipeEnvConfig
from fabline.harness.crew_multi_orphan import (
    run_crew_multi_orphan,
    write_crew_multi_orphan_report,
)
from fabline.harness.crew_schedule import (
    run_crew_schedule,
    write_crew_report,
)
from fabline.harness.factory_v02 import compare_expected_summary
from fabline.harness.partial_throughput import (
    PartialThroughputConfig,
    run_partial_throughput,
    write_partial_throughput_report,
)
from fabline.harness.preventive_threshold import (
    run_threshold_selection,
    write_threshold_report,
)
from fabline.harness.preventive_wire import (
    run_preventive_wire,
    write_preventive_wire_report,
)
from fabline.harness.recipe import run_recipe_choice, write_recipe_report
from fabline.harness.reliability_contract import (
    ReliabilityContractConfig,
    run_reliability_contract,
    write_reliability_contract_report,
)
from fabline.harness.wired_cascade import (
    WiredCascadeConfig,
    run_wired_cascade,
    write_wired_cascade_report,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.recipe import RecipeConfig

COVERAGE_SUITE_ID = "factory-v0.4-coverage"
COVERAGE_SUITE_VERSION = "0.4.0"
EXPECTED_TOLERANCE = {"rtol": 0.03, "atol": 0.02}

HEADLINE_TASKS = (
    "reliability-contract",
    "partial-throughput",
    "crew-schedule",
    "crew-triage",
    "preventive-wire",
    "recipe-choice",
    "maintenance-threshold",
)
DIAGNOSTIC_TASKS = ("wired-cascade",)
CHALLENGE_TASKS = (
    "crew-layouts",
    "decentralized-triage",
    "crew-replacement",
    "crew-replan-layouts",
    "maintenance-calibration",
)


@dataclass(frozen=True)
class CoverageSuiteConfig:
    fast: bool = False
    include_reliability: bool = True
    include_wired: bool = True
    include_partial: bool = True
    include_crew_schedule: bool = True
    include_crew_triage: bool = True
    include_preventive_wire: bool = True
    include_recipe_choice: bool = True
    include_maintenance_threshold: bool = True
    include_mpnn: bool = False
    include_sequence: bool = True


def _reliability_config(fast: bool) -> ReliabilityContractConfig:
    if not fast:
        return ReliabilityContractConfig()
    return ReliabilityContractConfig(
        train_blocks=(600, 602),
        test_blocks=(601, 603),
        episodes_per_block=2,
        bootstrap_samples=50,
        episode_ticks=200,
    )


def _wired_config(fast: bool) -> WiredCascadeConfig:
    if not fast:
        return WiredCascadeConfig()
    return WiredCascadeConfig(
        layouts=8,
        seed_start=500,
        max_faults_per_layout=3,
        warmup_ticks=10,
        mpnn_epochs=2,
        mpnn_hidden=8,
        mpnn_layers=1,
        mpnn_batch_size=4,
    )


def _partial_config(fast: bool) -> PartialThroughputConfig:
    if not fast:
        return PartialThroughputConfig()
    return PartialThroughputConfig(
        episodes=10,
        warmup_ticks=50,
        episode_ticks=150,
        horizon=30,
        window=4,
        sequence_epochs=2,
        sequence_hidden=8,
        sequence_layers=1,
        sequence_batch_size=4,
    )


def _schedule_factory_config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )


def _triage_factory_config() -> FactoryConfig:
    return FactoryConfig(
        width=32,
        height=16,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )


def _triage_config() -> CrewReplanConfig:
    return CrewReplanConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=90,
        small_failure_tick=110,
        large_failure_tick=130,
        recall_tick=100,
        job_failure_tick=100,
        replan_jobs=2,
        role_mode="three_positive",
        replan_mode="all_positive",
        success_score=300,
        randomize_crew_b=True,
        crew_b_min_distance=8,
        scenario="random_gear",
        power=PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=24,
            generator_radius=8,
            wire_redundancy=2,
        ),
    )


def _schedule_summary(
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    impact = float(results["impact_only"]["mean_score"])
    best_scripted = max(
        float(results["travel_aware"]["mean_score"]),
        float(results["nearest"]["mean_score"]),
        float(results["earliest_deadline"]["mean_score"]),
    )
    oracle = float(results["oracle"]["mean_score"])
    deadline = results["deadline_q"]
    gates = {
        "H1_travel_gain": best_scripted >= impact + 5.0,
        "H2_oracle_gap": oracle >= impact + 10.0,
        "H3_deadline_q": (
            float(deadline["mean_score"]) >= 0.85 * best_scripted
            and float(deadline["success_rate"]) >= 0.80
        ),
    }
    return {
        "task": {
            "id": "factory.power.crew-schedule.v1",
            "version": "0.1.0",
            "kind": "control",
        },
        "results": results,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _triage_summary(
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    best_scripted = max(
        float(results[name]["mean_score"])
        for name in ("nearest", "greedy", "aware")
    )
    oracle = float(results["oracle"]["mean_score"])
    single = float(results["single_edf"]["mean_score"])
    gates = {
        "H1_oracle_gap": oracle >= best_scripted + 10.0,
        "H2_coordination": best_scripted >= single + 10.0,
        "H3_nearest_sensitivity": float(results["nearest"]["mean_score"]) < oracle,
        "H4_success": float(results["oracle"]["success_rate"]) >= 0.60,
    }
    return {
        "task": {
            "id": "factory.power.crew-triage.v1",
            "version": "0.1.0",
            "kind": "control",
        },
        "results": results,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _preventive_wire_summary(
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    preventive = float(results["preventive"]["mean_score"])
    reactive = float(results["reactive"]["mean_score"])
    learned = float(results["tabular_q"]["mean_score"])
    gates = {
        "H1_prevention_gain": preventive >= reactive + 10.0,
        "H2_learned": learned >= reactive,
        "H3_success": float(results["preventive"]["success_rate"]) >= 0.60,
    }
    return {
        "task": {
            "id": "factory.power.wire-maintenance.v1",
            "version": "0.1.0",
            "kind": "control",
        },
        "results": results,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _recipe_summary(
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    buffer = results["buffer_aware"]
    gates = {
        "H1_queue_gain": (
            float(buffer["mean_score"])
            >= float(results["fast"]["mean_score"]) + 10.0
        ),
        "H2_planning": (
            float(buffer["mean_score"])
            >= float(results["lookahead"]["mean_score"]) + 10.0
        ),
        "H3_success": float(buffer["success_rate"]) >= 0.60,
    }
    return {
        "task": {
            "id": "factory.production.recipe-choice.v1",
            "version": "0.1.0",
            "kind": "control",
        },
        "results": results,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _threshold_summary(payload: dict[str, Any]) -> dict[str, Any]:
    best_fixed = max(
        float(row["mean_score"]) for row in payload["arms"].values()
    )
    learners = payload["learners"]
    best_learned = max(
        float(row["mean_score"]) for row in learners.values()
    )
    best_learned_success = max(
        float(row["success_rate"]) for row in learners.values()
    )
    gates = {
        "H1_spread": (
            best_fixed
            >= min(float(row["mean_score"]) for row in payload["arms"].values())
            + 10.0
        ),
        "H2_learned": best_learned >= best_fixed - 5.0,
        "H3_success": best_learned_success >= 0.60,
    }
    return {
        "task": {
            "id": "factory.fault.preventive-threshold.v1",
            "version": "0.1.0",
            "kind": "bandit",
        },
        "payload": payload,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _reliability_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "task": report["task"],
        "summary": report["summary"],
        "selected": report["selected"],
        "test_policy": report["test_policy"],
        "gates": report["gates"],
        "passed": all(bool(value) for value in report["gates"].values()),
    }


def _wired_summary(report: dict[str, Any]) -> dict[str, Any]:
    metrics = {
        name: row["test"]
        for name, row in report["metrics"].items()
        if "test" in row
    }
    return {
        "task": report["task"],
        "dataset": report["dataset"],
        "metrics": metrics,
        "gates": report["gates"],
        "passed": bool(report["gates"]["H1_graph_gain"]),
        "status": "diagnostic"
        if not bool(report["gates"]["H1_graph_gain"])
        else "candidate",
    }


def _partial_summary(report: dict[str, Any]) -> dict[str, Any]:
    tests: dict[str, Any] = {}
    for view, rows in report["views"].items():
        tests[view] = {
            name: row["test"]
            for name, row in rows.items()
            if "test" in row
        }
    return {
        "task": report["task"],
        "dataset": report["dataset"],
        "tests": tests,
        "gates": report["gates"],
        "passed": bool(
            report["gates"]["H1_mask_loss"]
            and report["gates"]["H2_window_recovery"]
            and report["gates"]["H3_no_leakage"]
        ),
    }


def _compact_rows(
    results: dict[str, dict[str, Any]],
    keys: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    return {
        name: {
            key: row[key]
            for key in keys
            if key in row
        }
        for name, row in results.items()
    }


def build_expected_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Build the compact, deterministic expected summary for factory-v0.4."""

    tasks: dict[str, Any] = {}
    reliability = report["tasks"].get("reliability-contract")
    if reliability is not None:
        tasks["reliability-contract"] = {
            "selected": reliability["selected"],
            "summary": reliability["summary"],
            "test_policy": reliability["test_policy"],
            "gates": reliability["gates"],
        }
    partial = report["tasks"].get("partial-throughput")
    if partial is not None:
        tasks["partial-throughput"] = {
            "dataset": partial["dataset"],
            "tests": {
                view: {
                    model: {
                        metric: values[metric]
                        for metric in ("r2", "mae", "mse", "cosine")
                        if metric in values
                    }
                    for model, values in rows.items()
                }
                for view, rows in partial["tests"].items()
                if view in {"current", "single", "window"}
            },
            "gates": partial["gates"],
        }
    wired = report["tasks"].get("wired-cascade")
    if wired is not None:
        tasks["wired-cascade"] = {
            "dataset": wired["dataset"],
            "metrics": {
                name: {
                    metric: values[metric]
                    for metric in ("r2", "mae")
                    if metric in values
                }
                for name, values in wired["metrics"].items()
            },
            "gates": wired["gates"],
        }
    for name in ("crew-schedule", "crew-triage", "preventive-wire"):
        task = report["tasks"].get(name)
        if task is not None:
            tasks[name] = {
                "results": _compact_rows(
                    task["results"],
                    (
                        "mean_score",
                        "score_ci",
                        "success_rate",
                        "mean_prevented",
                        "mean_aborted",
                        "mean_repairs",
                        "mean_travel",
                        "mean_switches",
                    ),
                ),
                "gates": task["gates"],
            }
    recipe = report["tasks"].get("recipe-choice")
    if recipe is not None:
        tasks["recipe-choice"] = {
            "results": _compact_rows(
                recipe["results"],
                ("mean_score", "score_ci", "success_rate", "mean_switches"),
            ),
            "gates": recipe["gates"],
        }
    threshold = report["tasks"].get("maintenance-threshold")
    if threshold is not None:
        payload = threshold["payload"]
        tasks["maintenance-threshold"] = {
            "arms": {
                key: {
                    metric: row[metric]
                    for metric in ("mean_score", "success_rate")
                    if metric in row
                }
                for key, row in payload["arms"].items()
            },
            "best_arm": payload["best_arm"],
            "learners": {
                name: {
                    metric: row[metric]
                    for metric in ("arm", "mean_score", "success_rate")
                    if metric in row
                }
                for name, row in payload["learners"].items()
            },
            "gates": threshold["gates"],
        }
    return {
        "benchmark": "factory-v0.4",
        "version": "0.4.0",
        "date": "2026-11-27",
        "world_version": "factory-0.1.0",
        "plan": "coverage-v0.4",
        "tolerance": EXPECTED_TOLERANCE,
        "headline_tasks": list(HEADLINE_TASKS),
        "diagnostics": list(DIAGNOSTIC_TASKS),
        "challenge_tasks": list(CHALLENGE_TASKS),
        "tasks": tasks,
    }


def compare_coverage_expected(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> list[str]:
    return compare_expected_summary(expected, actual)


def run_coverage_suite(
    out_dir: str | Path,
    config: CoverageSuiteConfig | None = None,
) -> dict[str, Any]:
    cfg = config or CoverageSuiteConfig()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tasks: dict[str, Any] = {}
    if cfg.include_reliability:
        reliability = run_reliability_contract(_reliability_config(cfg.fast))
        write_reliability_contract_report(out / "reliability-contract", reliability)
        tasks["reliability-contract"] = _reliability_summary(reliability)
    if cfg.include_wired:
        wired = run_wired_cascade(
            _wired_config(cfg.fast), include_mpnn=cfg.include_mpnn
        )
        write_wired_cascade_report(out / "wired-cascade", wired)
        tasks["wired-cascade"] = _wired_summary(wired)
    if cfg.include_partial:
        partial = run_partial_throughput(
            _partial_config(cfg.fast), include_sequence=cfg.include_sequence
        )
        write_partial_throughput_report(out / "partial-throughput", partial)
        tasks["partial-throughput"] = _partial_summary(partial)
    if cfg.include_crew_schedule:
        schedule_config = CrewScheduleConfig(
            loop_failure_tick=90,
            small_failure_tick=120,
            large_failure_tick=150,
            repair_budget=2,
            success_score=150,
        )
        schedule_seeds = (800, 801) if cfg.fast else (800, 801, 802, 803, 804)
        schedule_episodes = 1 if cfg.fast else 5
        schedule_train = 5 if cfg.fast else 100
        schedule = run_crew_schedule(
            _schedule_factory_config(),
            schedule_config,
            episodes=schedule_episodes,
            train_episodes=schedule_train,
            seeds=schedule_seeds,
        )
        write_crew_report(
            out / "crew-schedule",
            schedule,
            config={
                "warning_tick": schedule_config.warning_tick,
                "loop_failure_tick": schedule_config.loop_failure_tick,
                "small_failure_tick": schedule_config.small_failure_tick,
                "large_failure_tick": schedule_config.large_failure_tick,
                "repair_budget": schedule_config.repair_budget,
                "seeds": list(schedule_seeds),
            },
        )
        tasks["crew-schedule"] = _schedule_summary(schedule)
    if cfg.include_crew_triage:
        triage_config = _triage_config()
        triage_seeds = (12000,) if cfg.fast else (12000, 12001, 12002, 12003, 12004)
        triage = run_crew_multi_orphan(
            _triage_factory_config(),
            triage_config,
            seeds=triage_seeds,
        )
        write_crew_multi_orphan_report(
            out / "crew-triage",
            triage,
            config={
                "failure_tick": triage_config.job_failure_tick,
                "replan_jobs": triage_config.replan_jobs,
                "success_score": triage_config.success_score,
                "seeds": list(triage_seeds),
            },
            title="Three-bridge survivor triage",
        )
        tasks["crew-triage"] = _triage_summary(triage)
    if cfg.include_preventive_wire:
        preventive_config = PreventiveWireConfig()
        preventive_seeds = (0,) if cfg.fast else (0, 1, 2)
        preventive_episodes = 1 if cfg.fast else 5
        preventive_train = 5 if cfg.fast else 50
        preventive = run_preventive_wire(
            _schedule_factory_config(),
            preventive_config,
            episodes=preventive_episodes,
            train_episodes=preventive_train,
            seeds=preventive_seeds,
        )
        write_preventive_wire_report(
            out / "preventive-wire",
            preventive,
            config={
                "warning_tick": preventive_config.warning_tick,
                "failure_tick": preventive_config.failure_tick,
                "repair_ticks": preventive_config.repair_ticks,
                "repair_budget": preventive_config.repair_budget,
                "success_score": preventive_config.success_score,
                "seeds": list(preventive_seeds),
            },
        )
        tasks["preventive-wire"] = _preventive_wire_summary(preventive)
    if cfg.include_recipe_choice:
        recipe_config = RecipeEnvConfig(
            episode_ticks=500,
            decision_interval=10,
            scenario="gear",
            success_score=150,
            recipe=RecipeConfig(enabled=True),
            power=PowerConfig(),
        )
        recipe_seeds = (
            (37000, 37001) if cfg.fast else (37000, 37001, 37002, 37003, 37004)
        )
        recipe = run_recipe_choice(
            _schedule_factory_config(),
            recipe_config,
            seeds=recipe_seeds,
        )
        write_recipe_report(
            out / "recipe-choice",
            recipe,
            config={
                "fast_ticks": recipe_config.recipe.fast_ticks,
                "fast_cost": recipe_config.recipe.fast_cost,
                "slow_ticks": recipe_config.recipe.slow_ticks,
                "slow_cost": recipe_config.recipe.slow_cost,
                "success_score": recipe_config.success_score,
                "seeds": list(recipe_seeds),
            },
        )
        tasks["recipe-choice"] = _recipe_summary(recipe)
    if cfg.include_maintenance_threshold:
        threshold_config = ThresholdConfig()
        threshold_seeds = (700,) if cfg.fast else (700, 701, 702, 703, 704)
        threshold_episodes = 2 if cfg.fast else 50
        threshold = run_threshold_selection(
            _schedule_factory_config(),
            threshold_config,
            episodes=threshold_episodes,
            seeds=threshold_seeds,
        )
        write_threshold_report(out / "maintenance-threshold", threshold)
        tasks["maintenance-threshold"] = _threshold_summary(threshold)
    report = {
        "benchmark": COVERAGE_SUITE_ID,
        "version": COVERAGE_SUITE_VERSION,
        "status": "frozen",
        "config": asdict(cfg),
        "tasks": tasks,
        "summary": {
            "tasks": len(tasks),
            "passed": sum(1 for task in tasks.values() if task.get("passed")),
            "diagnostic": sum(
                1 for task in tasks.values() if task.get("status") == "diagnostic"
            ),
        },
    }
    (out / "coverage_suite_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (out / "coverage_suite_report.md").write_text(
        _render_report(report), encoding="utf-8"
    )
    return report


def _render_report(report: dict[str, Any]) -> str:
    lines = [
        "# factory-v0.4 coverage suite (frozen)",
        "",
        f"- status: {report['status']}",
        f"- tasks: {report['summary']['tasks']}",
        f"- passed: {report['summary']['passed']}",
        f"- diagnostics: {report['summary']['diagnostic']}",
        "",
        "| task | status | key result |",
        "|---|---|---|",
    ]
    for name, task in report["tasks"].items():
        if name == "reliability-contract":
            key = (
                f"CVaR gain {task['test_policy']['cvar_gain']:.2f} "
                f"[{task['test_policy']['cvar_gain_ci'][0]:.2f}, "
                f"{task['test_policy']['cvar_gain_ci'][1]:.2f}]"
            )
        elif name == "wired-cascade":
            key = (
                f"graph_mp R² "
                f"{task['metrics'].get('graph_mp', {}).get('r2', float('nan')):.3f}"
            )
        elif name == "partial-throughput":
            key = (
                "window GBDT R² "
                f"{task['tests'].get('window', {}).get('gbdt', {}).get('r2', float('nan')):.3f}"
            )
        elif name == "crew-schedule":
            key = (
                "deadline Q "
                f"{task['results']['deadline_q']['mean_score']:.1f}/"
                f"{task['results']['deadline_q']['success_rate']:.2f} vs EDF "
                f"{task['results']['earliest_deadline']['mean_score']:.1f}"
            )
        elif name == "crew-triage":
            key = (
                "oracle "
                f"{task['results']['oracle']['mean_score']:.1f} vs greedy "
                f"{task['results']['greedy']['mean_score']:.1f}"
            )
        elif name == "preventive-wire":
            key = (
                "preventive "
                f"{task['results']['preventive']['mean_score']:.1f} vs reactive "
                f"{task['results']['reactive']['mean_score']:.1f}"
            )
        elif name == "recipe-choice":
            key = (
                "buffer-aware "
                f"{task['results']['buffer_aware']['mean_score']:.1f} vs fast "
                f"{task['results']['fast']['mean_score']:.1f}"
            )
        elif name == "maintenance-threshold":
            learner_scores = [
                float(row["mean_score"])
                for row in task["payload"]["learners"].values()
            ]
            key = (
                "best fixed "
                f"{task['payload']['best_arm']} vs learner "
                f"{max(learner_scores):.1f}"
            )
        else:
            key = ""
        status = task.get("status", "pass" if task.get("passed") else "fail")
        lines.append(f"| {name} | {status} | {key} |")
    lines.extend(
        [
            "",
            "This coverage tier is frozen in `factory-v0.4`. See the task cards,",
            "the benchmark card, and the freeze review for gates and scope.",
            "",
        ]
    )
    return "\n".join(lines)
