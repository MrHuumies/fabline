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

COVERAGE_SUITE_ID = "factory-v0.4-coverage"
COVERAGE_SUITE_VERSION = "0.1.0"


@dataclass(frozen=True)
class CoverageSuiteConfig:
    fast: bool = False
    include_reliability: bool = True
    include_wired: bool = True
    include_partial: bool = True
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
