"""Load shared episodes and project them into task tensors."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from fabline.obs.entities import ENTITY_FEATURES
from fabline.obs.vector import FEATURES

MASKED_GRID_PATCH = (3, 6, 2, 10)


@dataclass
class SharedDataset:
    views: dict[str, np.ndarray]
    targets: dict[str, np.ndarray]
    splits: np.ndarray
    scenarios: np.ndarray
    episode_ids: np.ndarray
    manifest: dict[str, Any]


@dataclass
class TaskProjection:
    name: str
    kind: str
    X: np.ndarray
    y: np.ndarray
    splits: np.ndarray
    feature_names: tuple[str, ...] | None = None
    target_names: tuple[str, ...] | None = None
    graph: dict[str, np.ndarray] | None = None


def load_shared_dataset(root: str | Path) -> SharedDataset:
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    episode_dirs = sorted((root / "episodes").iterdir())
    if not episode_dirs:
        raise ValueError(f"no episodes under {root}")

    views: dict[str, list[np.ndarray]] = {}
    targets: dict[str, list[np.ndarray]] = {}
    splits: list[np.ndarray] = []
    scenarios: list[np.ndarray] = []
    episode_ids: list[np.ndarray] = []

    for episode_dir in episode_dirs:
        if not episode_dir.is_dir():
            continue
        meta = json.loads((episode_dir / "meta.json").read_text(encoding="utf-8"))
        with np.load(episode_dir / "data.npz") as data:
            for key in ("vector", "grid", "entity_features", "entity_mask", "adjacency"):
                views.setdefault(key, []).append(data[key])
            for key in ("future_score", "bottleneck", "next_vector"):
                targets.setdefault(key, []).append(data[key])
            ticks = data["ticks"]
        count = len(ticks)
        splits.append(np.full(count, meta["split"], dtype=object))
        scenarios.append(np.full(count, meta["scenario"], dtype=object))
        episode_ids.append(np.full(count, meta["episode_id"], dtype=object))

    return SharedDataset(
        views={key: np.concatenate(value, axis=0) for key, value in views.items()},
        targets={
            key: np.concatenate(value, axis=0) for key, value in targets.items()
        },
        splits=np.concatenate(splits),
        scenarios=np.concatenate(scenarios),
        episode_ids=np.concatenate(episode_ids),
        manifest=manifest,
    )


def project_throughput_vector(dataset: SharedDataset) -> TaskProjection:
    return TaskProjection(
        name="throughput-vector",
        kind="supervised",
        X=dataset.views["vector"],
        y=dataset.targets["future_score"],
        splits=dataset.splits,
        feature_names=FEATURES,
    )


def project_throughput_grid(dataset: SharedDataset) -> TaskProjection:
    grid = dataset.views["grid"]
    return TaskProjection(
        name="throughput-grid",
        kind="supervised",
        X=grid.reshape(len(grid), -1),
        y=dataset.targets["future_score"],
        splits=dataset.splits,
        feature_names=None,
    )


def project_throughput_entities(dataset: SharedDataset) -> TaskProjection:
    features = dataset.views["entity_features"]
    mask = dataset.views["entity_mask"]
    adjacency = dataset.views["adjacency"]
    X = np.concatenate(
        [
            features.reshape(len(features), -1),
            mask.astype(np.float32),
            adjacency.reshape(len(features), -1),
        ],
        axis=1,
    )
    return TaskProjection(
        name="throughput-entities",
        kind="supervised",
        X=X,
        y=dataset.targets["future_score"],
        splits=dataset.splits,
        feature_names=ENTITY_FEATURES,
        graph={
            "entity_features": features,
            "entity_mask": mask,
            "adjacency": adjacency,
        },
    )


def project_next_state(dataset: SharedDataset) -> TaskProjection:
    return TaskProjection(
        name="next-state",
        kind="self_supervised",
        X=dataset.views["vector"],
        y=dataset.targets["next_vector"],
        splits=dataset.splits,
        feature_names=FEATURES,
        target_names=FEATURES,
    )


def project_bottleneck(dataset: SharedDataset) -> TaskProjection:
    return TaskProjection(
        name="bottleneck",
        kind="classification",
        X=dataset.views["vector"],
        y=dataset.targets["bottleneck"],
        splits=dataset.splits,
        feature_names=FEATURES,
    )


def project_masked_grid(dataset: SharedDataset) -> TaskProjection:
    grid = dataset.views["grid"]
    y0, y1, x0, x1 = MASKED_GRID_PATCH
    target = grid[:, y0:y1, x0:x1, :].reshape(len(grid), -1)
    masked = grid.copy()
    masked[:, y0:y1, x0:x1, :] = 0.0
    return TaskProjection(
        name="masked-grid",
        kind="self_supervised",
        X=masked.reshape(len(grid), -1),
        y=target,
        splits=dataset.splits,
        feature_names=None,
        target_names=None,
    )


def project_tasks(dataset: SharedDataset) -> dict[str, TaskProjection]:
    return {
        "throughput-vector": project_throughput_vector(dataset),
        "throughput-grid": project_throughput_grid(dataset),
        "throughput-entities": project_throughput_entities(dataset),
        "next-state": project_next_state(dataset),
        "bottleneck": project_bottleneck(dataset),
        "masked-grid": project_masked_grid(dataset),
    }
