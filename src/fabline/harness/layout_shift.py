"""Layout-shift pilot: train on base layouts, test on larger/random layouts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from fabline.harness.baselines import evaluate_baselines
from fabline.obs import build_observation
from fabline.obs.layout import LayoutSummaryObservation
from fabline.tasks.throughput import ThroughputConfig, ThroughputTask
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS


@dataclass(frozen=True)
class LayoutSpec:
    name: str
    width: int
    height: int
    scenario: str
    rock_density: float
    ore_patches: int
    entity_budget: int

    def line_count(self) -> int:
        scenario = SCENARIOS[self.scenario]
        if scenario.line_count > 1:
            return scenario.line_count
        return 2 if scenario.twin_line else 1

    def factory_config(self) -> FactoryConfig:
        return FactoryConfig(
            width=self.width,
            height=self.height,
            ticks_per_episode=500,
            decision_interval=10,
            entity_budget=self.entity_budget,
            rock_density=self.rock_density,
            ore_patches=self.ore_patches,
            starter_line=True,
            emit_events=True,
        )


@dataclass(frozen=True)
class ShiftSpec:
    layout: LayoutSpec
    seed_start: int
    count: int


@dataclass(frozen=True)
class LayoutShiftConfig:
    base_specs: tuple[LayoutSpec, ...] = (
        LayoutSpec(
            name="base-16x8",
            width=16,
            height=8,
            scenario="gear",
            rock_density=0.02,
            ore_patches=2,
            entity_budget=32,
        ),
        LayoutSpec(
            name="base-20x12",
            width=20,
            height=12,
            scenario="gear",
            rock_density=0.04,
            ore_patches=3,
            entity_budget=48,
        ),
        LayoutSpec(
            name="base-24x16-twin",
            width=24,
            height=16,
            scenario="random_gear",
            rock_density=0.06,
            ore_patches=3,
            entity_budget=64,
        ),
    )
    shifts: tuple[ShiftSpec, ...] = (
        ShiftSpec(
            LayoutSpec(
                name="large-32x24",
                width=32,
                height=24,
                scenario="spread_gear",
                rock_density=0.06,
                ore_patches=4,
                entity_budget=64,
            ),
            seed_start=210_000,
            count=8,
        ),
        ShiftSpec(
            LayoutSpec(
                name="random-24x20",
                width=24,
                height=20,
                scenario="random_gear",
                rock_density=0.10,
                ore_patches=3,
                entity_budget=64,
            ),
            seed_start=220_000,
            count=8,
        ),
        ShiftSpec(
            LayoutSpec(
                name="obstacles-24x20",
                width=24,
                height=20,
                scenario="shift_gear",
                rock_density=0.15,
                ore_patches=1,
                entity_budget=64,
            ),
            seed_start=230_000,
            count=8,
        ),
    )
    train_seeds: tuple[int, ...] = tuple(range(200_000, 200_012))
    val_seeds: tuple[int, ...] = tuple(range(200_012, 200_016))
    test_seeds: tuple[int, ...] = tuple(range(200_016, 200_020))
    task_config: ThroughputConfig = field(
        default_factory=lambda: ThroughputConfig(
            horizon=100,
            warmup_ticks=200,
            episode_ticks=500,
            sample_interval=10,
        )
    )
    observation: str = "vector"
    normalize_target: bool = False

    def __post_init__(self) -> None:
        if not self.base_specs:
            raise ValueError("at least one base layout is required")
        if not self.train_seeds or not self.val_seeds or not self.test_seeds:
            raise ValueError("base seed splits must not be empty")
        if not self.shifts:
            raise ValueError("at least one shift layout is required")


def _adapter(spec: LayoutSpec, config: LayoutShiftConfig) -> Any:
    factory_config = spec.factory_config()
    if config.observation == "layout-summary":
        return LayoutSummaryObservation(
            factory_config, line_count=spec.line_count()
        )
    return build_observation(config.observation, factory_config)


def _collect(
    spec: LayoutSpec,
    seeds: tuple[int, ...],
    split: str,
    config: LayoutShiftConfig,
) -> tuple[np.ndarray, np.ndarray]:
    factory_config = spec.factory_config()
    adapter = _adapter(spec, config)
    task = ThroughputTask(
        factory_config,
        config.task_config,
        adapter,
        scenario=SCENARIOS[spec.scenario],
    )
    observations: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    for seed in seeds:
        episode = task.generate_episode(seed, split=split)
        observations.append(episode.observations)
        labels.append(episode.labels)
    y = np.concatenate(labels)
    if config.normalize_target:
        y = y / max(1, spec.line_count())
    return np.concatenate(observations), y


def _best_model(
    results: dict[str, dict[str, Any]],
    names: tuple[str, ...],
) -> tuple[str, float]:
    available = [name for name in names if name in results]
    if not available:
        raise RuntimeError("no regression models were available")
    name = max(
        available,
        key=lambda item: float(results[item]["test"]["r2"]),
    )
    return name, float(results[name]["test"]["r2"])


def run_layout_shift(
    config: LayoutShiftConfig | None = None,
) -> dict[str, Any]:
    cfg = config or LayoutShiftConfig()
    train_parts: list[np.ndarray] = []
    train_labels: list[np.ndarray] = []
    for spec in cfg.base_specs:
        x, y = _collect(spec, cfg.train_seeds, "train", cfg)
        train_parts.append(x)
        train_labels.append(y)
    val_parts: list[np.ndarray] = []
    val_labels: list[np.ndarray] = []
    for spec in cfg.base_specs:
        x, y = _collect(spec, cfg.val_seeds, "val", cfg)
        val_parts.append(x)
        val_labels.append(y)
    test_parts: list[np.ndarray] = []
    test_labels: list[np.ndarray] = []
    for spec in cfg.base_specs:
        x, y = _collect(spec, cfg.test_seeds, "test", cfg)
        test_parts.append(x)
        test_labels.append(y)
    train_x = np.concatenate(train_parts)
    train_y = np.concatenate(train_labels)
    val_x = np.concatenate(val_parts)
    val_y = np.concatenate(val_labels)
    test_x = np.concatenate(test_parts)
    test_y = np.concatenate(test_labels)
    adapter = _adapter(cfg.base_specs[0], cfg)
    feature_names = adapter.spec.feature_names
    base_results = evaluate_baselines(
        train_x,
        train_y,
        val_x,
        val_y,
        test_x,
        test_y,
        feature_names,
        include_models=True,
    )
    shift_results: dict[str, dict[str, Any]] = {}
    shift_sizes: dict[str, int] = {}
    for shift in cfg.shifts:
        seeds = tuple(
            range(shift.seed_start, shift.seed_start + shift.count)
        )
        shift_x, shift_y = _collect(
            shift.layout, seeds, "shift", cfg
        )
        shift_sizes[shift.layout.name] = int(len(shift_y))
        shift_results[shift.layout.name] = evaluate_baselines(
            train_x,
            train_y,
            val_x,
            val_y,
            test_x,
            test_y,
            feature_names,
            include_models=True,
            X_extra=shift_x,
            y_extra=shift_y,
        )
    gates = layout_shift_gates(
        base_results, shift_results, cfg
    )
    return {
        "config": {
            "base": [spec.name for spec in cfg.base_specs],
            "observation": cfg.observation,
            "target": "score_per_line" if cfg.normalize_target else "score",
            "train_seeds": list(cfg.train_seeds),
            "val_seeds": list(cfg.val_seeds),
            "test_seeds": list(cfg.test_seeds),
            "shifts": [
                {
                    "name": shift.layout.name,
                    "seed_start": shift.seed_start,
                    "count": shift.count,
                }
                for shift in cfg.shifts
            ],
            "task": {
                "horizon": cfg.task_config.horizon,
                "warmup_ticks": cfg.task_config.warmup_ticks,
                "episode_ticks": cfg.task_config.episode_ticks,
                "sample_interval": cfg.task_config.sample_interval,
            },
        },
        "dataset": {
            "train": int(len(train_y)),
            "val": int(len(val_y)),
            "test": int(len(test_y)),
            "shift": shift_sizes,
            "features": len(feature_names) if feature_names else 0,
        },
        "metrics": {
            "base": base_results,
            "shift": shift_results,
        },
        "gates": gates,
    }


def layout_shift_gates(
    base_results: dict[str, dict[str, Any]],
    shift_results: dict[str, dict[str, Any]],
    config: LayoutShiftConfig,
) -> dict[str, Any]:
    base_model, base_r2 = _best_model(
        base_results, ("linear", "gradient_boosting", "mlp")
    )
    gaps = {
        name: base_r2
        - float(results[base_model]["shift"]["r2"])
        for name, results in shift_results.items()
    }
    train = set(config.train_seeds)
    val = set(config.val_seeds)
    test = set(config.test_seeds)
    shift = {
        seed
        for spec in config.shifts
        for seed in range(spec.seed_start, spec.seed_start + spec.count)
    }
    no_leakage = (
        train.isdisjoint(val)
        and train.isdisjoint(test)
        and train.isdisjoint(shift)
        and val.isdisjoint(test)
        and val.isdisjoint(shift)
        and test.isdisjoint(shift)
    )
    complete = all(
        base_model in results for results in shift_results.values()
    )
    return {
        "H1_base_skill": base_r2 >= 0.20,
        "H2_ood_gap": max(gaps.values()) >= 0.10,
        "H3_no_seed_leakage": no_leakage,
        "H4_metrics_complete": complete,
        "base_model": base_model,
        "gaps": gaps,
    }


def write_layout_shift_report(
    out: str | Path, report: dict[str, Any]
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "layout_shift_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Layout shift pilot",
        "",
        f"- base: {', '.join(report['config']['base'])}",
        f"- observation: {report['config']['observation']}",
        f"- train/val/test: {report['dataset']['train']}/"
        f"{report['dataset']['val']}/{report['dataset']['test']}",
        "",
        "| layout | model | test R² | shift R² | gap |",
        "|---|---|---:|---:|---:|",
    ]
    base = report["metrics"]["base"]
    for name, row in report["metrics"]["shift"].items():
        for model in ("linear", "gradient_boosting", "mlp"):
            if model not in row:
                continue
            lines.append(
                f"| {name} | {model} | "
                f"{base[model]['test']['r2']:.3f} | "
                f"{row[model]['shift']['r2']:.3f} | "
                f"{base[model]['test']['r2'] - row[model]['shift']['r2']:.3f} |"
            )
    lines.extend(["", "## Gates", "", "| Gate | Result |", "|---|---|"])
    for name, value in report["gates"].items():
        if isinstance(value, bool):
            lines.append(f"| {name} | {'pass' if value else 'fail'} |")
    lines.append("")
    path = out / "layout_shift_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
