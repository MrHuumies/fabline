"""Calibration on preventive-maintenance fault risk."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from fabline.env.preventive_fault import PreventiveFaultConfig, PreventiveFaultEnv
from fabline.harness.baselines import (
    evaluate_calibration_baselines,
    evaluate_classification_baselines,
)
from fabline.tasks.splits import assign_split
from fabline.worlds.factory.config import FactoryConfig

MAINTENANCE_CALIBRATION_TASK_ID = "factory.fault.maintenance_calibration.v1"
MAINTENANCE_CALIBRATION_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class MaintenanceCalibrationConfig:
    episodes: int = 60
    seed_start: int = 61000
    warmup_ticks: int = 100
    horizon: int = 10
    maintenance_probability: float = 0.05
    behavior_offset: int = 3
    preventive: PreventiveFaultConfig = field(
        default_factory=PreventiveFaultConfig
    )

    def __post_init__(self) -> None:
        if self.episodes <= 0:
            raise ValueError("episodes must be positive")
        if self.warmup_ticks < 0 or self.horizon <= 0:
            raise ValueError("warmup and horizon must be positive")
        if not 0.0 <= self.maintenance_probability <= 1.0:
            raise ValueError("maintenance probability must be in [0, 1]")
        if not self.preventive.faults.enabled:
            raise ValueError("maintenance calibration requires faults")


def _factory_config() -> FactoryConfig:
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


def generate_maintenance_calibration(
    cfg: MaintenanceCalibrationConfig,
) -> dict[str, np.ndarray]:
    config = _factory_config()
    env = PreventiveFaultEnv(config, cfg.preventive)
    rows: list[np.ndarray] = []
    labels: list[int] = []
    splits: list[str] = []
    for offset in range(cfg.episodes):
        seed = cfg.seed_start + offset
        split = assign_split(seed)
        rng = random.Random(seed * 104729 + cfg.behavior_offset)
        observation, info = env.reset(seed)
        done = False
        while not done:
            if int(info["tick"]) >= cfg.warmup_ticks:
                clone = env.world.clone(keep_events=True)
                clone.run_ticks(cfg.horizon)
                label = any(
                    event.kind == "fault_started"
                    for event in clone.state.events
                )
                rows.append(observation.copy())
                labels.append(1 if label else 0)
                splits.append(split)
            action = (
                1
                if env.action_mask()[1]
                and rng.random() < cfg.maintenance_probability
                else 0
            )
            observation, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated
    return {
        "observation": np.stack(rows),
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
        raise ValueError("maintenance calibration needs train and test splits")
    return (
        features[train],
        data["label"][train],
        features[val],
        data["label"][val],
        features[test],
        data["label"][test],
    )


def run_maintenance_calibration(
    cfg: MaintenanceCalibrationConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or MaintenanceCalibrationConfig()
    data = generate_maintenance_calibration(cfg)
    views = {
        "diagnostics": data["observation"][:, :13],
        "diagnostics_maintenance": data["observation"],
    }
    results: dict[str, Any] = {
        "task": MAINTENANCE_CALIBRATION_TASK_ID,
        "config": {
            "episodes": cfg.episodes,
            "seed_start": cfg.seed_start,
            "warmup_ticks": cfg.warmup_ticks,
            "horizon": cfg.horizon,
            "maintenance_probability": cfg.maintenance_probability,
        },
        "samples": int(len(data["label"])),
        "positive_rate": float(np.mean(data["label"])),
        "splits": {
            name: int(np.sum(data["split"] == name))
            for name in ("train", "val", "test")
        },
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


def write_maintenance_calibration_report(
    out: str | Path,
    results: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "maintenance_calibration_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Maintenance-risk calibration",
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
                "| method | balanced | Brier | NLL | ECE |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for method in ("gbdt", "mlp"):
            test = payload["metrics"][method]["test"]
            calibration = payload["calibration"][method]["test"]
            lines.append(
                f"| {method} | {test['balanced_accuracy']:.4f} | "
                f"{calibration['brier']:.4f} | {calibration['nll']:.4f} | "
                f"{calibration['ece']:.4f} |"
            )
        lines.append("")
    (out / "maintenance_calibration_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return out / "maintenance_calibration_report.md"
