"""Load a materialized FABLINE dataset."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class LoadedDataset:
    X: np.ndarray
    y: np.ndarray
    splits: np.ndarray
    episode_ids: list[str]
    observation_name: str
    feature_names: tuple[str, ...] | None
    manifest: dict[str, Any]


def load_dataset(root: str | Path) -> LoadedDataset:
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    episode_dirs = sorted((root / "episodes").iterdir())
    if not episode_dirs:
        raise ValueError(f"no episodes found under {root}")

    observations: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    splits: list[np.ndarray] = []
    episode_ids: list[str] = []

    for episode_dir in episode_dirs:
        if not episode_dir.is_dir():
            continue
        meta = json.loads((episode_dir / "meta.json").read_text(encoding="utf-8"))
        with np.load(episode_dir / "steps.npz") as steps:
            episode_observations = steps["observations"]
            episode_labels = steps["labels"]
        observations.append(episode_observations)
        labels.append(episode_labels)
        splits.append(
            np.full(len(episode_labels), meta["split"], dtype=object)
        )
        episode_ids.append(meta["episode_id"])

    if not observations:
        raise ValueError(f"no readable episodes found under {root}")

    observation = manifest.get("observation", {})
    feature_names = observation.get("feature_names")
    return LoadedDataset(
        X=np.concatenate(observations, axis=0),
        y=np.concatenate(labels, axis=0),
        splits=np.concatenate(splits),
        episode_ids=episode_ids,
        observation_name=observation.get("name", "unknown"),
        feature_names=tuple(feature_names) if feature_names else None,
        manifest=manifest,
    )
