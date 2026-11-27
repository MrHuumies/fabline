"""The 0.5.0 coverage-suite orchestrator.

This is a draft `factory-v0.4` coverage tier. It runs the public coverage tasks
that are available in this tree and writes one aggregate report. It is not a
frozen benchmark; task status and gates are reported per task.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fabline.env.crew_replan import CrewReplanConfig
from fabline.env.crew_schedule import CrewScheduleConfig
from fabline.harness.crew_multi_orphan import (
    run_crew_multi_orphan,
    write_crew_multi_orphan_report,
)
from fabline.harness.crew_schedule import (
    run_crew_schedule,
    write_crew_report,
)
from fabline.harness.partial_throughput import (
    PartialThroughputConfig,
    run_partial_throughput,
    write_partial_throughput_report,
)
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

COVERAGE_SUITE_ID = "factory-v0.4-coverage"
COVERAGE_SUITE_VERSION = "0.1.0"


@dataclass(frozen=True)
class CoverageSuiteConfig:
    fast: bool = False
    include_reliability: bool = True
    include_wired: bool = True
    include_partial: bool = True
    include_crew_schedule: bool = True
    include_crew_triage: bool = True
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
    report = {
        "benchmark": COVERAGE_SUITE_ID,
        "version": COVERAGE_SUITE_VERSION,
        "status": "candidate",
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
        "# factory-v0.4 coverage suite (draft)",
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
        else:
            key = ""
        status = task.get("status", "pass" if task.get("passed") else "fail")
        lines.append(f"| {name} | {status} | {key} |")
    lines.extend(
        [
            "",
            "This is a draft coverage tier, not a frozen benchmark. See the task",
            "cards and the 0.5.0 roadmap for gates and promotion decisions.",
            "",
        ]
    )
    return "\n".join(lines)
