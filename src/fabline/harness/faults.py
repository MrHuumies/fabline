"""Fault-mechanic benchmark: vector vs diagnostic sensor views."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from fabline.core.hashing import config_hash
from fabline.harness.baselines import (
    evaluate_calibration_baselines,
    evaluate_classification_baselines,
)
from fabline.harness.data import LoadedDataset, load_dataset
from fabline.obs.base import build_observation
from fabline.record.replay import validate_replay
from fabline.record.writer import write_dataset
from fabline.tasks.fault_prediction import FaultPredictionTask, FaultTaskConfig
from fabline.tasks.meta import manifest_meta
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.world import FactoryWorld


def _split_xy(
    loaded: LoadedDataset,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    splits = np.asarray(loaded.splits)
    train = splits == "train"
    val = splits == "val"
    test = splits == "test"
    if not train.any() or not val.any() or not test.any():
        raise ValueError("fault dataset must contain train, val, and test")
    return (
        loaded.X[train],
        loaded.y[train],
        loaded.X[val],
        loaded.y[val],
        loaded.X[test],
        loaded.y[test],
    )


def run_fault_benchmark(
    out_dir: str | Path,
    *,
    episodes: int = 40,
    seed_start: int = 0,
    config: FactoryConfig | None = None,
    faults: FaultConfig | None = None,
    horizon: int = 50,
    sample_interval: int = 10,
) -> dict[str, Any]:
    config = config or FactoryConfig(
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
    faults = faults or FaultConfig(
        enabled=True,
        wear_per_craft=1,
        fault_threshold=20,
        repair_ticks=30,
    )
    if not faults.enabled:
        raise ValueError("fault benchmark requires faults.enabled")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {
        "benchmark": "fault-debug-v0.1",
        "world_version": WORLD_VERSION,
        "config_hash": config_hash(config),
        "faults": asdict(faults),
        "episodes": episodes,
        "horizon": horizon,
        "sample_interval": sample_interval,
        "views": {},
    }

    for name in ("vector", "diagnostics"):
        adapter = build_observation(name, config, faults)
        task = FaultPredictionTask(
            config,
            FaultTaskConfig(
                faults=faults,
                horizon=horizon,
                sample_interval=sample_interval,
            ),
            adapter,
        )
        episodes_data = task.generate(episodes, seed_start=seed_start)
        dataset_dir = out / "datasets" / f"fault-{name}"
        meta = manifest_meta(config, task, adapter, "fault_within_horizon")
        meta["faults"] = asdict(faults)
        meta["scenario"] = "gear"
        write_dataset(dataset_dir, f"fault-{name}-debug", episodes_data, meta)

        world = FactoryWorld(config, faults)
        for episode in episodes_data:
            validate_replay(
                world,
                {
                    "seed": episode.seed,
                    "scenario": "gear",
                    "faults": asdict(faults),
                    "sample_ticks": episode.sample_ticks,
                    "state_hashes": episode.state_hashes,
                    "actions": [],
                },
            )

        loaded = load_dataset(dataset_dir)
        X_train, y_train, X_val, y_val, X_test, y_test = _split_xy(loaded)
        metrics = evaluate_classification_baselines(
            X_train,
            y_train,
            X_val,
            y_val,
            X_test,
            y_test,
            with_ci=True,
        )
        results["views"][name] = {
            "dataset": str(dataset_dir),
            "episodes": len(episodes_data),
            "samples": int(len(loaded.y)),
            "positive_rate": float(np.mean(loaded.y)),
            "metrics": metrics,
            "calibration": evaluate_calibration_baselines(
                X_train,
                y_train,
                X_test,
                y_test,
                with_ci=True,
            ),
        }

    (out / "fault_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    _write_report(out / "fault_report.md", results)
    return results


def _write_report(path: Path, results: dict[str, Any]) -> None:
    lines = [
        "# Fault-mechanic benchmark",
        "",
        "This is a debug benchmark for the opt-in fault mechanic, not a frozen "
        "release.",
        "",
        f"- world: `{results['world_version']}`",
        f"- faults: `{results['faults']}`",
        f"- episodes: {results['episodes']}",
        f"- horizon: {results['horizon']} ticks; sample interval "
        f"{results['sample_interval']}",
        "",
    ]
    for name, payload in results["views"].items():
        lines.extend(
            [
                f"## {name} view",
                "",
                f"- samples: {payload['samples']}",
                f"- positive rate: {payload['positive_rate']:.3f}",
                "",
                "| method | test accuracy | test balanced | test macro F1 |",
                "|---|---:|---:|---:|",
            ]
        )
        for method, result in payload["metrics"].items():
            test = result["test"]
            ci = result.get("ci", {}).get("test", {})
            accuracy = _cell(test["accuracy"], ci.get("accuracy"))
            balanced = _cell(test["balanced_accuracy"], ci.get("balanced_accuracy"))
            lines.append(
                f"| {method} | {accuracy} | {balanced} | {test['macro_f1']:.4f} |"
            )
        lines.extend(
            [
                "",
                "| method | Brier | NLL | ECE |",
                "|---|---:|---:|---:|",
            ]
        )
        for method, result in payload["calibration"].items():
            test = result["test"]
            lines.append(
                f"| {method} | {test['brier']:.4f} | "
                f"{test['nll']:.4f} | {test['ece']:.4f} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Caveats",
            "",
            "- One fixed gear line and one fault threshold; not a benchmark release.",
            "- The task predicts faults; repair is a separate recovery task.",
            "- The vector view has no explicit wear/fault channels; diagnostics does.",
            "- Small debug budgets; CIs are wide.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _cell(
    value: float,
    interval: tuple[float, float] | list[float] | None,
) -> str:
    if interval is None:
        return f"{value:.4f}"
    low, high = interval[0], interval[1]
    return f"{value:.4f} [{low:.4f}, {high:.4f}]"
