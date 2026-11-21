"""Power-grid debug benchmark: vector vs power views."""

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
from fabline.tasks.meta import manifest_meta
from fabline.tasks.power import PowerBrownoutTask, PowerTaskConfig
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig
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
        raise ValueError("power dataset must contain train, val, and test")
    return (
        loaded.X[train],
        loaded.y[train],
        loaded.X[val],
        loaded.y[val],
        loaded.X[test],
        loaded.y[test],
    )


def run_power_benchmark(
    out_dir: str | Path,
    *,
    episodes: int = 40,
    seed_start: int = 0,
    config: FactoryConfig | None = None,
    power: PowerConfig | None = None,
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
    power = power or PowerConfig(
        enabled=True,
        generator_count=1,
        generator_capacity=9,
        generator_radius=8,
    )
    if not power.enabled:
        raise ValueError("power benchmark requires power.enabled")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {
        "benchmark": "power-debug-v0.1",
        "world_version": WORLD_VERSION,
        "config_hash": config_hash(config),
        "power": asdict(power),
        "episodes": episodes,
        "views": {},
    }

    for name in ("vector", "power"):
        adapter = build_observation(name, config, power=power)
        task = PowerBrownoutTask(
            config,
            PowerTaskConfig(power=power),
            adapter,
        )
        episodes_data = task.generate(episodes, seed_start=seed_start)
        dataset_dir = out / "datasets" / f"power-{name}"
        meta = manifest_meta(
            config,
            task,
            adapter,
            "brownout_within_horizon",
            power=power,
        )
        meta["scenario"] = "gear"
        write_dataset(dataset_dir, f"power-{name}-debug", episodes_data, meta)

        world = FactoryWorld(config, power=power)
        for episode in episodes_data:
            validate_replay(
                world,
                {
                    "seed": episode.seed,
                    "scenario": "gear",
                    "power": asdict(power),
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
        calibration = evaluate_calibration_baselines(
            X_train,
            y_train,
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
            "calibration": calibration,
        }

    (out / "power_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    _write_report(out / "power_report.md", results)
    return results


def _write_report(path: Path, results: dict[str, Any]) -> None:
    lines = [
        "# Power-grid benchmark",
        "",
        "This is a debug benchmark for the opt-in power mechanic, not a frozen "
        "release.",
        "",
        f"- world: `{results['world_version']}`",
        f"- power: `{results['power']}`",
        f"- episodes: {results['episodes']}",
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
            balanced = _cell(
                test["balanced_accuracy"], ci.get("balanced_accuracy")
            )
            lines.append(
                f"| {method} | {accuracy} | {balanced} | {test['macro_f1']:.4f} |"
            )
        lines.extend(
            [
                "",
                "### Calibration",
                "",
                "| method | Brier | NLL | ECE |",
                "|---|---:|---:|---:|",
            ]
        )
        for method, result in payload["calibration"].items():
            test = result["test"]
            ci = result.get("ci", {})
            lines.append(
                f"| {method} | {_cell(test['brier'], ci.get('brier'))} | "
                f"{_cell(test['nll'], ci.get('nll'))} | "
                f"{_cell(test['ece'], ci.get('ece'))} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Caveats",
            "",
            "- One fixed gear line, one generator layout, and one budget; not a "
            "benchmark release.",
            "- The vector view has no explicit power channels; the power view does.",
            "- Generators are pre-placed infrastructure; they are not buildable yet.",
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
