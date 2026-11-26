"""A small, reproducible cross-task efficiency table."""

from __future__ import annotations

import json
import pickle
import platform
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

from fabline.harness.baselines import (
    CopyBaseline,
    GradientBoostingBaseline,
    GradientBoostingClassifierBaseline,
    LinearBaseline,
    MajorityBaseline,
    MeanBaseline,
    MLPBaseline,
    MLPClassifierBaseline,
)
from fabline.harness.shared_data import project_tasks
from fabline.obs.entities import EntitiesObservation
from fabline.obs.grid import GridObservation
from fabline.obs.vector import VectorObservation
from fabline.tasks.shared import (
    SharedEpisodeConfig,
    generate_shared_dataset,
)
from fabline.tasks.splits import SplitPlan
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS, generate_state
from fabline.worlds.factory.world import FactoryWorld

EFFICIENCY_TASK_ID = "factory.efficiency.v1"


@dataclass(frozen=True)
class EfficiencyConfig:
    repeats: int = 3
    world_ticks: int = 1000
    observation_repeats: int = 500
    seed: int = 0
    train_episodes: int = 6
    val_episodes: int = 2
    test_episodes: int = 2
    shift_episodes: int = 2
    episode_ticks: int = 200
    sample_interval: int = 10

    def __post_init__(self) -> None:
        if self.repeats <= 0:
            raise ValueError("repeats must be positive")
        if self.world_ticks <= 0:
            raise ValueError("world ticks must be positive")
        if self.observation_repeats <= 0:
            raise ValueError("observation repeats must be positive")
        for name in (
            "train_episodes",
            "val_episodes",
            "test_episodes",
            "shift_episodes",
            "episode_ticks",
            "sample_interval",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")


def _factory_config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )


def _plan(cfg: EfficiencyConfig) -> SplitPlan:
    return SplitPlan(
        name="efficiency",
        scenarios={
            "train": ("ingot", "gear"),
            "val": ("ingot",),
            "test": ("extra_gear",),
            "shift": ("shift_gear",),
        },
        episodes_per_scenario={
            "train": cfg.train_episodes,
            "val": cfg.val_episodes,
            "test": cfg.test_episodes,
            "shift": cfg.shift_episodes,
        },
    )


def _measure_world(cfg: EfficiencyConfig) -> dict[str, Any]:
    config = FactoryConfig(
        width=32,
        height=32,
        ticks_per_episode=10_000,
        decision_interval=10,
        entity_budget=64,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )
    world = FactoryWorld(config)
    world.reset(seed=cfg.seed)
    start = time.perf_counter()
    world.run_ticks(cfg.world_ticks)
    elapsed = time.perf_counter() - start
    return {
        "ticks": cfg.world_ticks,
        "seconds": elapsed,
        "ticks_per_second": cfg.world_ticks / max(elapsed, 1e-12),
        "width": config.width,
        "height": config.height,
    }


def _measure_observations(cfg: EfficiencyConfig) -> dict[str, Any]:
    config = _factory_config()
    state = generate_state(config, cfg.seed, SCENARIOS["gear"])
    adapters: dict[str, Any] = {
        "vector": VectorObservation(config),
        "grid": GridObservation(config),
        "entities": EntitiesObservation(config),
    }
    results: dict[str, Any] = {}
    for name, adapter in adapters.items():
        start = time.perf_counter()
        for _ in range(cfg.observation_repeats):
            adapter.observe(state)
        elapsed = time.perf_counter() - start
        results[name] = {
            "observations": cfg.observation_repeats,
            "seconds": elapsed,
            "observations_per_second": cfg.observation_repeats
            / max(elapsed, 1e-12),
        }
    return results


def _partition(projection: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    splits = projection.splits
    train = splits == "train"
    test = splits == "test"
    if not train.any() or not test.any():
        raise ValueError(f"task {projection.name} needs train/test")
    x_train = np.asarray(projection.X[train]).reshape(int(train.sum()), -1)
    x_test = np.asarray(projection.X[test]).reshape(int(test.sum()), -1)
    y_train = projection.y[train]
    y_test = projection.y[test]
    return x_train, y_train, x_test, y_test


def _label_codes(
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    labels, encoded = np.unique(y_train, return_inverse=True)
    mapping = {label: index for index, label in enumerate(labels)}
    train_codes = encoded.astype(np.int64)
    test_codes = np.asarray(
        [mapping.get(label, 0) for label in y_test], dtype=np.int64
    )
    return train_codes, test_codes


def _artifact_bytes(model: Any) -> int:
    return len(pickle.dumps(model))


def _measure_model(
    task: str,
    model_name: str,
    factory: Any,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    *,
    repeats: int,
) -> dict[str, Any]:
    fit_seconds: list[float] = []
    predict_seconds: list[float] = []
    artifact_bytes: list[int] = []
    peak_bytes: list[int] = []
    for _ in range(repeats):
        tracemalloc.start()
        model = factory()
        start = time.perf_counter()
        model.fit(x_train, y_train)
        fit_seconds.append(time.perf_counter() - start)
        start = time.perf_counter()
        model.predict(x_test)
        predict_seconds.append(time.perf_counter() - start)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        artifact_bytes.append(_artifact_bytes(model))
        peak_bytes.append(int(peak))
    return {
        "task": task,
        "model": model_name,
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "features": int(x_train.shape[1]),
        "fit_seconds": float(median(fit_seconds)),
        "predict_seconds": float(median(predict_seconds)),
        "predict_microseconds_per_row": (
            1e6 * median(predict_seconds) / max(1, len(x_test))
        ),
        "artifact_bytes": int(median(artifact_bytes)),
        "peak_bytes": int(median(peak_bytes)),
    }


def run_efficiency(
    cfg: EfficiencyConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or EfficiencyConfig()
    config = _factory_config()
    episodes = generate_shared_dataset(
        config,
        _plan(cfg),
        SharedEpisodeConfig(
            warmup_ticks=20,
            episode_ticks=cfg.episode_ticks,
            sample_interval=cfg.sample_interval,
            horizon=20,
            bottleneck_horizon=10,
        ),
    )
    dataset = {
        "episodes": len(episodes),
        "samples": int(sum(len(episode.views["vector"]) for episode in episodes)),
        "config_hash": episodes[0].meta["config_hash"] if episodes else None,
    }
    projections = project_tasks(
        _dataset_from_episodes(episodes)
    )
    models: list[dict[str, Any]] = []

    x_train, y_train, x_test, y_test = _partition(
        projections["throughput-vector"]
    )
    for name, vector_factory in (
        ("mean", MeanBaseline),
        ("linear", LinearBaseline),
        ("gbdt", GradientBoostingBaseline),
        ("mlp", MLPBaseline),
    ):
        models.append(
            _measure_model(
                "throughput-vector",
                name,
                vector_factory,
                x_train,
                y_train,
                x_test,
                repeats=cfg.repeats,
            )
        )

    x_train, y_train, x_test, y_test = _partition(
        projections["bottleneck"]
    )
    train_codes, test_codes = _label_codes(y_train, y_test)
    for name, classifier_factory in (
        ("majority", MajorityBaseline),
        ("gbdt", GradientBoostingClassifierBaseline),
        ("mlp", MLPClassifierBaseline),
    ):
        models.append(
            _measure_model(
                "bottleneck",
                name,
                classifier_factory,
                x_train,
                train_codes,
                x_test,
                repeats=cfg.repeats,
            )
        )

    x_train, y_train, x_test, _ = _partition(
        projections["masked-grid"]
    )
    for name, grid_factory in (
        ("copy", CopyBaseline),
        ("linear", LinearBaseline),
        ("mlp", MLPBaseline),
    ):
        models.append(
            _measure_model(
                "masked-grid",
                name,
                grid_factory,
                x_train,
                y_train,
                x_test,
                repeats=cfg.repeats,
            )
        )

    return {
        "task": EFFICIENCY_TASK_ID,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor() or "unknown",
            "numpy": np.__version__,
        },
        "config": {
            "repeats": cfg.repeats,
            "world_ticks": cfg.world_ticks,
            "observation_repeats": cfg.observation_repeats,
            "seed": cfg.seed,
        },
        "dataset": dataset,
        "world": _measure_world(cfg),
        "observations": _measure_observations(cfg),
        "models": models,
        "caveats": [
            "Descriptive, not a leaderboard; timings are machine-dependent.",
            "Small fixed dataset; fit time is not a converged training budget.",
            "Artifact bytes are a pickle-size proxy, not deployment memory.",
            "No GPU and no Torch baselines in this slice.",
        ],
    }


def _dataset_from_episodes(episodes: list[Any]) -> Any:
    from fabline.harness.shared_data import SharedDataset

    views: dict[str, list[np.ndarray]] = {}
    targets: dict[str, list[np.ndarray]] = {}
    splits: list[np.ndarray] = []
    scenarios: list[np.ndarray] = []
    episode_ids: list[np.ndarray] = []
    for episode in episodes:
        for key in ("vector", "grid", "entity_features", "entity_mask", "adjacency"):
            views.setdefault(key, []).append(episode.views[key])
        for key in ("future_score", "bottleneck", "next_vector"):
            targets.setdefault(key, []).append(episode.targets[key])
        count = len(episode.sample_ticks)
        splits.append(np.full(count, episode.split, dtype=object))
        scenarios.append(np.full(count, episode.meta["scenario"], dtype=object))
        episode_ids.append(np.full(count, episode.episode_id, dtype=object))
    return SharedDataset(
        views={key: np.concatenate(value) for key, value in views.items()},
        targets={key: np.concatenate(value) for key, value in targets.items()},
        splits=np.concatenate(splits),
        scenarios=np.concatenate(scenarios),
        episode_ids=np.concatenate(episode_ids),
        manifest={},
    )


def write_efficiency_report(
    out: str | Path,
    report: dict[str, Any],
) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "efficiency_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    world = report["world"]
    environment = report["environment"]
    lines = [
        "# FABLINE efficiency table",
        "",
        f"Generated with `fabline efficiency`; Python {environment['python']}, "
        f"NumPy {environment['numpy']}, processor {environment['processor']}.",
        "",
        f"Dataset: {report['dataset']['episodes']} episodes, "
        f"{report['dataset']['samples']} samples. "
        f"Repeats: {report['config']['repeats']}. "
        "Descriptive only; timings are machine-dependent.",
        "",
        "## World and observations",
        "",
        "| path | rate |",
        "|---|---:|",
        f"| world ticks | {world['ticks_per_second']:.0f}/s |",
    ]
    for name, row in report["observations"].items():
        lines.append(
            f"| {name} observation | "
            f"{row['observations_per_second']:.0f}/s |"
        )
    lines.extend(
        [
            "",
            "## Models",
            "",
            "| task | model | rows | features | fit (s) | "
            "predict (µs/row) | artifact (KB) | peak (MB) |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["models"]:
        lines.append(
            f"| {row['task']} | {row['model']} | {row['train_rows']} | "
            f"{row['features']} | {row['fit_seconds']:.4f} | "
            f"{row['predict_microseconds_per_row']:.2f} | "
            f"{row['artifact_bytes'] / 1024:.1f} | "
            f"{row['peak_bytes'] / 1e6:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Caveats",
            "",
            *[f"- {caveat}" for caveat in report["caveats"]],
            "",
        ]
    )
    path = out / "efficiency.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
