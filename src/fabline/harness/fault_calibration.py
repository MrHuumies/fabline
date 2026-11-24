"""Calibration on the hard fault-onset views (context + thermal/vibration)."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from fabline.harness.baselines import (
    evaluate_calibration_baselines,
    evaluate_classification_baselines,
)
from fabline.obs.sensors import DiagnosticsObservation, TopKEntitySensorsObservation
from fabline.obs.vector import VectorObservation
from fabline.tasks.splits import assign_split
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.labels import future_fault
from fabline.worlds.factory.world import FactoryWorld

CONTEXT_INDEX = [5, 6, 7, 8, 14, 15, 16]


@dataclass(frozen=True)
class FaultCalibrationConfig:
    episodes: int = 40
    seed_start: int = 55000
    warmup_ticks: int = 100
    episode_ticks: int = 500
    sample_interval: int = 5
    horizon: int = 10
    noise: float = 0.30
    faults: FaultConfig = field(
        default_factory=lambda: FaultConfig(
            enabled=True,
            wear_per_craft=1,
            fault_threshold=20,
            repair_ticks=30,
        )
    )

    def __post_init__(self) -> None:
        if self.episodes <= 0:
            raise ValueError("episodes must be positive")
        if self.sample_interval <= 0 or self.horizon <= 0:
            raise ValueError("sample interval and horizon must be positive")
        if self.noise < 0.0:
            raise ValueError("noise must be non-negative")
        if not self.faults.enabled:
            raise ValueError("fault calibration requires faults.enabled")


def _config() -> FactoryConfig:
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


def generate_fault_calibration(
    cfg: FaultCalibrationConfig,
) -> dict[str, np.ndarray]:
    config = _config()
    vector = VectorObservation(config)
    diagnostics = DiagnosticsObservation(config, cfg.faults)
    top4 = TopKEntitySensorsObservation(config, cfg.faults)
    context_rows: list[np.ndarray] = []
    thermal_rows: list[np.ndarray] = []
    vibration_rows: list[np.ndarray] = []
    top4_rows: list[np.ndarray] = []
    labels: list[int] = []
    splits: list[str] = []
    for offset in range(cfg.episodes):
        seed = cfg.seed_start + offset
        split = assign_split(seed)
        rng = random.Random(seed * 104729 + 53)
        world = FactoryWorld(config, cfg.faults)
        world.reset(seed, SCENARIOS["gear"])
        world.run_ticks(cfg.warmup_ticks)
        while world.state.tick + cfg.horizon <= cfg.episode_ticks:
            base = vector.observe(world.state)
            context_rows.append(base[CONTEXT_INDEX].copy())
            values = diagnostics.observe(world.state)
            thermal_rows.append(
                np.clip(
                    values[5:7]
                    + np.asarray(
                        [rng.gauss(0.0, cfg.noise) for _ in range(2)],
                        dtype=np.float32,
                    ),
                    0.0,
                    1.0,
                )
            )
            vibration_rows.append(
                np.clip(
                    values[7:9]
                    + np.asarray(
                        [rng.gauss(0.0, cfg.noise) for _ in range(2)],
                        dtype=np.float32,
                    ),
                    0.0,
                    1.0,
                )
            )
            top4_rows.append(top4.observe(world.state).reshape(-1).copy())
            labels.append(future_fault(world, cfg.horizon))
            splits.append(split)
            if (
                world.state.tick
                + cfg.sample_interval
                + cfg.horizon
                > cfg.episode_ticks
            ):
                break
            world.run_ticks(cfg.sample_interval)
    return {
        "context": np.stack(context_rows),
        "thermal": np.stack(thermal_rows),
        "vibration": np.stack(vibration_rows),
        "top4": np.stack(top4_rows),
        "label": np.asarray(labels, dtype=np.float32),
        "split": np.asarray(splits),
    }


def _partition(
    data: dict[str, np.ndarray],
    features: np.ndarray,
) -> tuple[np.ndarray, ...]:
    splits = data["split"]
    train = splits == "train"
    val = splits == "val"
    test = splits == "test"
    if not train.any() or not test.any():
        raise ValueError("fault calibration needs train and test splits")
    return (
        features[train],
        data["label"][train],
        features[val],
        data["label"][val],
        features[test],
        data["label"][test],
    )


def run_fault_calibration(
    cfg: FaultCalibrationConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or FaultCalibrationConfig()
    data = generate_fault_calibration(cfg)
    views = {
        "context_thermal": np.concatenate(
            [data["context"], data["thermal"]], axis=1
        ),
        "context_thermal_vibration": np.concatenate(
            [data["context"], data["thermal"], data["vibration"]],
            axis=1,
        ),
        "context_thermal_vibration_top4": np.concatenate(
            [data["context"], data["thermal"], data["vibration"], data["top4"]],
            axis=1,
        ),
    }
    results: dict[str, Any] = {
        "task": "factory.fault.calibration.v1",
        "config": {
            "episodes": cfg.episodes,
            "seed_start": cfg.seed_start,
            "horizon": cfg.horizon,
            "sample_interval": cfg.sample_interval,
            "noise": cfg.noise,
        },
        "samples": int(len(data["label"])),
        "positive_rate": float(np.mean(data["label"])),
        "views": {},
    }
    for name, features in views.items():
        train_x, train_y, val_x, val_y, test_x, test_y = _partition(
            data, features
        )
        results["views"][name] = {
            "metrics": evaluate_classification_baselines(
                train_x,
                train_y,
                val_x,
                val_y,
                test_x,
                test_y,
                with_ci=True,
            ),
            "calibration": evaluate_calibration_baselines(
                train_x,
                train_y,
                test_x,
                test_y,
                with_ci=True,
            ),
        }
    return results


def write_fault_calibration_report(
    out: str | Path,
    results: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "fault_calibration_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Fault calibration",
        "",
        f"Horizon {results['config']['horizon']}; samples "
        f"{results['samples']}; positive rate "
        f"{results['positive_rate']:.3f}.",
        "",
    ]
    for name, payload in results["views"].items():
        lines.extend(
            [
                f"## {name}",
                "",
                "| method | accuracy | Brier | NLL | ECE |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for method in payload["calibration"]:
            test = payload["metrics"][method]["test"]
            calibration = payload["calibration"][method]["test"]
            lines.append(
                f"| {method} | {test['accuracy']:.4f} | "
                f"{calibration['brier']:.4f} | {calibration['nll']:.4f} | "
                f"{calibration['ece']:.4f} |"
            )
        lines.append("")
    (out / "fault_calibration_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "fault_calibration_report.md"
