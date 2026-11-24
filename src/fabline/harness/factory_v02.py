"""The `factory-v0.2` benchmark orchestrator and freeze checks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any

from fabline.harness.causal_intervention import CausalConfig, run_causal
from fabline.harness.fault_calibration import (
    FaultCalibrationConfig,
    run_fault_calibration,
)
from fabline.harness.faults import run_fault_benchmark
from fabline.harness.planning_triage import (
    TriagePlanningConfig,
    run_triage_planning,
)
from fabline.harness.power import run_power_benchmark
from fabline.harness.shared_suite import (
    SharedSuiteConfig,
    run_shared_suite,
)
from fabline.tasks.shared import SharedEpisodeConfig
from fabline.tasks.splits import SplitPlan
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.power import PowerConfig

BENCHMARK_ID = "factory-v0.2"
BENCHMARK_VERSION = "0.2.0"
BENCHMARK_DATE = "2026-11-24"

HEADLINE_CORE_TASKS = (
    "throughput-vector",
    "throughput-grid",
    "throughput-entities",
    "masked-grid",
    "bottleneck",
    "expand-control",
    "control-dynamics",
)

HEADLINE_TASKS = HEADLINE_CORE_TASKS + (
    "planning-triage",
    "fault-calibration",
    "causal-removal",
)

DIAGNOSTIC_TASKS = ("fault-prediction", "power-brownout", "next-state")

# The frozen summary is compared with a small tolerance so that minor
# scikit-learn / NumPy differences do not turn a deterministic benchmark into
# a library-version test.
EXPECTED_TOLERANCE = {"rtol": 0.03, "atol": 0.02}


@dataclass(frozen=True)
class FactoryV02Config:
    core_train_per_scenario: int = 33
    core_val_per_scenario: int = 10
    core_test_episodes: int = 20
    core_shift_episodes: int = 20
    control_episodes: int = 10
    control_train_episodes: int = 300
    control_seeds: tuple[int, ...] = (0, 1, 2, 3, 4)
    fault_episodes: int = 40
    fault_seed_start: int = 60000
    power_episodes: int = 40
    power_seed_start: int = 61000
    planning_seeds: tuple[int, ...] = (62000, 62001, 62002, 62003, 62004)
    calibration_seeds: tuple[int, ...] = (63000, 63100, 63200)
    calibration_episodes: int = 40
    causal_seeds: tuple[int, ...] = (64000, 64100, 64200)
    causal_episodes: int = 40

    def __post_init__(self) -> None:
        if self.core_train_per_scenario <= 0:
            raise ValueError("core train episodes must be positive")
        if self.core_val_per_scenario <= 0:
            raise ValueError("core val episodes must be positive")
        if self.core_test_episodes <= 0 or self.core_shift_episodes <= 0:
            raise ValueError("core test/shift episodes must be positive")
        if self.control_episodes <= 0 or self.control_train_episodes <= 0:
            raise ValueError("control budgets must be positive")
        if not self.control_seeds:
            raise ValueError("control seeds must not be empty")
        if self.fault_episodes <= 0 or self.power_episodes <= 0:
            raise ValueError("fault/power episodes must be positive")
        if not self.planning_seeds:
            raise ValueError("planning seeds must not be empty")
        if not self.calibration_seeds or self.calibration_episodes <= 0:
            raise ValueError("calibration blocks must be positive")
        if not self.causal_seeds or self.causal_episodes <= 0:
            raise ValueError("causal blocks must be positive")


def v02_plan(config: FactoryV02Config | None = None) -> SplitPlan:
    config = config or FactoryV02Config()
    return SplitPlan(
        name="compositional-v0.2",
        scenarios={
            "train": ("ingot", "gear", "extra_ingot"),
            "val": ("ingot", "gear"),
            "test": ("extra_gear",),
            "shift": ("shift_gear",),
        },
        episodes_per_scenario={
            "train": config.core_train_per_scenario,
            "val": config.core_val_per_scenario,
            "test": config.core_test_episodes,
            "shift": config.core_shift_episodes,
        },
        metadata={
            "held_out": "extra_gear is the test combination",
            "shift": "shift_gear is the layout shift",
            "excluded": "next-state is a diagnostic, not a headline task",
        },
    )


def _core_summary(core: dict[str, Any]) -> dict[str, Any]:
    stats = core["dataset"]["stats"]
    return {
        "config_hash": core["metadata"]["config_hash"],
        "episodes": stats["episodes"],
        "samples": stats["samples"],
        "splits": stats["splits"],
        "scenarios": stats["scenarios"],
        "tasks": {
            name: {
                "kind": payload["kind"],
                "samples": payload["samples"],
                "metrics": payload["metrics"],
            }
            for name, payload in core["tasks"].items()
        },
    }


def _diagnostic_fault_summary(fault: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": "diagnostic; not frozen",
        "episodes": fault["episodes"],
        "horizon": fault["horizon"],
        "views": {
            name: {
                "samples": payload["samples"],
                "positive_rate": payload["positive_rate"],
                "metrics": payload["metrics"],
                "calibration": payload["calibration"],
            }
            for name, payload in fault["views"].items()
        },
    }


def _diagnostic_power_summary(power: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": "diagnostic; not frozen",
        "episodes": power["episodes"],
        "views": {
            name: {
                "samples": payload["samples"],
                "positive_rate": payload["positive_rate"],
                "metrics": payload["metrics"],
                "calibration": payload.get("calibration"),
            }
            for name, payload in power["views"].items()
        },
    }


def run_factory_v02(
    out_dir: str | Path,
    config: FactoryV02Config | None = None,
    *,
    include_planning: bool = True,
    include_diagnostics: bool = True,
) -> dict[str, Any]:
    cfg = config or FactoryV02Config()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    core = run_shared_suite(
        out / "core",
        SharedSuiteConfig(
            plan=v02_plan(cfg),
            episode_config=SharedEpisodeConfig(),
            control_episodes=cfg.control_episodes,
            control_train_episodes=cfg.control_train_episodes,
            control_seeds=cfg.control_seeds,
        ),
    )
    blocks: dict[str, Any] = {"core": _core_summary(core)}
    if include_diagnostics:
        fault = run_fault_benchmark(
            out / "fault",
            episodes=cfg.fault_episodes,
            seed_start=cfg.fault_seed_start,
        )
        power = run_power_benchmark(
            out / "power",
            episodes=cfg.power_episodes,
            seed_start=cfg.power_seed_start,
            power=PowerConfig(
                enabled=True,
                generator_count=1,
                generator_capacity=9,
                generator_radius=8,
                load_jitter=60,
                capacity_jitter=40,
                variation_period=10,
            ),
        )
        blocks["fault"] = _diagnostic_fault_summary(fault)
        blocks["power"] = _diagnostic_power_summary(power)
    if include_planning:
        blocks["planning"] = run_triage_planning(
            TriagePlanningConfig(), seeds=cfg.planning_seeds
        )
    calibration_blocks = [
        run_fault_calibration(
            FaultCalibrationConfig(
                seed_start=seed,
                episodes=cfg.calibration_episodes,
            )
        )
        for seed in cfg.calibration_seeds
    ]
    causal_blocks = [
        run_causal(
            CausalConfig(
                seed_start=seed,
                episodes=cfg.causal_episodes,
            )
        )
        for seed in cfg.causal_seeds
    ]
    blocks["calibration"] = {
        "primary": calibration_blocks[0],
        "blocks": calibration_blocks[1:],
    }
    blocks["causal"] = {
        "primary": causal_blocks[0],
        "blocks": causal_blocks[1:],
    }
    report = {
        "benchmark": BENCHMARK_ID,
        "status": "frozen",
        "config": asdict(cfg),
        "blocks": blocks,
    }
    (out / "factory_v02_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return report


def _compact_core_task(payload: dict[str, Any]) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for method, row in payload["metrics"].items():
        if not isinstance(row, dict):
            continue
        if "skipped" in row:
            metrics[method] = {"skipped": row["skipped"]}
            continue
        if "test" in row or "shift" in row:
            metrics[method] = {
                split: row[split]
                for split in ("test", "shift")
                if split in row
            }
            continue
        metrics[method] = {
            key: row[key]
            for key in (
                "success_rate",
                "mean_score",
                "mean_reward",
                "path_complete_rate",
                "mean_steps",
            )
            if key in row
        }
    return {
        "kind": payload["kind"],
        "samples": payload["samples"],
        "metrics": metrics,
    }


def _compact_calibration_block(block: dict[str, Any]) -> dict[str, Any]:
    views: dict[str, Any] = {}
    for view, payload in block["views"].items():
        methods: dict[str, Any] = {}
        for method in ("gbdt", "mlp"):
            calibration = payload["calibration"][method]["test"]
            metrics = payload["metrics"][method]["test"]
            methods[method] = {
                "balanced_accuracy": metrics["balanced_accuracy"],
                "brier": calibration["brier"],
                "nll": calibration["nll"],
                "ece": calibration["ece"],
            }
        views[view] = methods
    return {
        "seed_start": block["config"]["seed_start"],
        "samples": block["samples"],
        "positive_rate": block["positive_rate"],
        "views": views,
    }


def _calibration_blocks(report: dict[str, Any]) -> list[dict[str, Any]]:
    payload = report["blocks"]["calibration"]
    return [payload["primary"], *payload["blocks"]]


def _causal_blocks(report: dict[str, Any]) -> list[dict[str, Any]]:
    payload = report["blocks"]["causal"]
    return [payload["primary"], *payload["blocks"]]


def _compact_causal_block(block: dict[str, Any]) -> dict[str, Any]:
    views: dict[str, Any] = {}
    for view, methods in block["views"].items():
        views[view] = {
            method: {
                "r2": metrics["r2"],
                "mae": metrics["mae"],
            }
            for method, metrics in methods.items()
        }
    return {
        "seed_start": block["config"]["seed_start"],
        "rows": block["rows"],
        "label_mean": block["label_mean"],
        "views": views,
    }


def _aggregate_calibration(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    compact = [_compact_calibration_block(block) for block in blocks]
    views: dict[str, Any] = {}
    for view in compact[0]["views"]:
        views[view] = {}
        for method in compact[0]["views"][view]:
            views[view][method] = {}
            for metric in ("balanced_accuracy", "brier", "nll", "ece"):
                values = [
                    block["views"][view][method][metric] for block in compact
                ]
                views[view][method][metric] = {
                    "mean": float(fmean(values)),
                    "std": float(pstdev(values)),
                }
    return {"blocks": compact, "mean_std": views}


def _aggregate_causal(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    compact = [_compact_causal_block(block) for block in blocks]
    views: dict[str, Any] = {}
    for view in compact[0]["views"]:
        views[view] = {}
        for method in compact[0]["views"][view]:
            views[view][method] = {}
            for metric in ("r2", "mae"):
                values = [
                    block["views"][view][method][metric] for block in compact
                ]
                views[view][method][metric] = {
                    "mean": float(fmean(values)),
                    "std": float(pstdev(values)),
                }
    return {"blocks": compact, "mean_std": views}


def _compact_planning(planning: dict[str, Any]) -> dict[str, Any]:
    return {
        "config": planning["config"],
        "seeds": planning["seeds"],
        "model_mse": planning["model_mse"],
        "observation_features": planning["observation_features"],
        "results": {
            name: {
                "mean_score": row["mean_score"],
                "success_rate": row["success_rate"],
                "scores": row["scores"],
            }
            for name, row in planning["results"].items()
        },
    }


def build_expected_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Build the compact, frozen summary used by the CI regression check."""

    core = report["blocks"]["core"]
    expected: dict[str, Any] = {
        "benchmark": BENCHMARK_ID,
        "version": BENCHMARK_VERSION,
        "date": BENCHMARK_DATE,
        "world_version": WORLD_VERSION,
        "plan": "compositional-v0.2",
        "tolerance": EXPECTED_TOLERANCE,
        "headline_tasks": list(HEADLINE_TASKS),
        "diagnostics": list(DIAGNOSTIC_TASKS),
        "core": {
            "config_hash": core["config_hash"],
            "episodes": core["episodes"],
            "samples": core["samples"],
            "splits": core["splits"],
            "scenarios": core["scenarios"],
            "tasks": {
                name: _compact_core_task(core["tasks"][name])
                for name in HEADLINE_CORE_TASKS
            },
        },
        "calibration": _aggregate_calibration(_calibration_blocks(report)),
        "causal": _aggregate_causal(_causal_blocks(report)),
    }
    if "planning" in report["blocks"]:
        expected["planning"] = _compact_planning(report["blocks"]["planning"])
    return expected


def _format_path(path: tuple[str, ...]) -> str:
    return ".".join(path)


def compare_expected_summary(
    expected: dict[str, Any],
    actual: dict[str, Any],
    *,
    sections: tuple[str, ...] | None = None,
) -> list[str]:
    """Return human-readable mismatches between two expected summaries."""

    tolerance = expected.get("tolerance", EXPECTED_TOLERANCE)
    rtol = float(tolerance["rtol"])
    atol = float(tolerance["atol"])
    ignored = {"status", "date", "version", "tolerance", "freeze_note"}
    mismatches: list[str] = []

    def walk(expected_value: Any, actual_value: Any, path: tuple[str, ...]) -> None:
        if path and path[-1] in ignored:
            return
        if isinstance(expected_value, dict):
            if not isinstance(actual_value, dict):
                mismatches.append(
                    f"{_format_path(path)}: expected dict, got "
                    f"{type(actual_value).__name__}"
                )
                return
            for key, value in expected_value.items():
                child = (*path, str(key))
                if key not in actual_value:
                    mismatches.append(f"{_format_path(child)}: missing")
                    continue
                walk(value, actual_value[key], child)
            return
        if isinstance(expected_value, list):
            if not isinstance(actual_value, list):
                mismatches.append(
                    f"{_format_path(path)}: expected list, got "
                    f"{type(actual_value).__name__}"
                )
                return
            if len(expected_value) != len(actual_value):
                mismatches.append(
                    f"{_format_path(path)}: length {len(actual_value)} != "
                    f"{len(expected_value)}"
                )
            for index, (left, right) in enumerate(
                zip(expected_value, actual_value, strict=False)
            ):
                walk(left, right, (*path, str(index)))
            return
        if isinstance(expected_value, bool):
            if expected_value != actual_value:
                mismatches.append(
                    f"{_format_path(path)}: {actual_value!r} != "
                    f"{expected_value!r}"
                )
            return
        if isinstance(expected_value, (int, float)):
            if not isinstance(actual_value, (int, float)):
                mismatches.append(
                    f"{_format_path(path)}: expected number, got "
                    f"{type(actual_value).__name__}"
                )
                return
            allowed = max(atol, rtol * abs(float(expected_value)))
            if abs(float(actual_value) - float(expected_value)) > allowed:
                mismatches.append(
                    f"{_format_path(path)}: {actual_value:.6g} != "
                    f"{expected_value:.6g} (tol {allowed:.3g})"
                )
            return
        if expected_value != actual_value:
            mismatches.append(
                f"{_format_path(path)}: {actual_value!r} != "
                f"{expected_value!r}"
            )

    keys = sections if sections is not None else tuple(expected)
    for key in keys:
        if key not in expected:
            continue
        if key not in actual:
            mismatches.append(f"{key}: missing section")
            continue
        walk(expected[key], actual[key], (key,))
    return mismatches


def write_expected_summary(path: str | Path, summary: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def write_factory_v02_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    lines = [
        "# factory-v0.2",
        "",
        f"- status: {report['status']}",
        f"- core episodes: {report['blocks']['core']['episodes']}",
        f"- core samples: {report['blocks']['core']['samples']}",
        f"- core config hash: `{report['blocks']['core']['config_hash']}`",
        "",
        "## Blocks",
        "",
    ]
    if "planning" in report["blocks"]:
        lines.append(
            f"- planning: "
            f"{report['blocks']['planning']['results']['cem_true']['mean_score']:.1f} "
            "CEM true"
        )
    lines.extend(
        [
            f"- calibration: {len(_calibration_blocks(report))} blocks",
            f"- causal: {len(_causal_blocks(report))} blocks",
            (
                f"- diagnostics: {', '.join(DIAGNOSTIC_TASKS)}"
                if "fault" in report["blocks"]
                else "- diagnostics: skipped"
            ),
            "",
            "The frozen expected summary is checked by "
            "`fabline benchmark-v02 --check-expected`.",
            "",
        ]
    )
    path = out / "factory_v02_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
