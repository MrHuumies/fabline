"""Observation for the constrained line-building control task."""

from __future__ import annotations

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import EntityType, WorldState

from .base import ObservationSpec
from .vector import FEATURES, VectorObservation

PATH_CLASSES = ("empty", "miner", "belt", "furnace", "assembler")
_PATH_CLASS_INDEX = {
    EntityType.MINER: 1,
    EntityType.BELT: 2,
    EntityType.FURNACE: 3,
    EntityType.ASSEMBLER: 4,
}


class ControlObservation:
    """Vector statistics plus a one-hot encoding of the fixed build path."""

    def __init__(
        self,
        config: FactoryConfig,
        path: list[tuple[int, int]],
    ) -> None:
        self.config = config
        self.path = path
        self.vector = VectorObservation(config)
        self.shape = (len(FEATURES) + len(path) * len(PATH_CLASSES) + 1,)
        names = list(FEATURES)
        for index in range(len(path)):
            names.extend(f"path_{index}_{name}" for name in PATH_CLASSES)
        names.append("path_progress")
        self.spec = ObservationSpec(
            name="control",
            version="0.1.0",
            shape=self.shape,
            feature_names=tuple(names),
        )

    def observe(self, state: WorldState) -> np.ndarray:
        base = self.vector.observe(state)
        path_features = np.zeros((len(self.path), len(PATH_CLASSES)), dtype=np.float32)
        next_index = len(self.path)
        for index, (x, y) in enumerate(self.path):
            entity = state.entity_at(x, y)
            if entity is None:
                if next_index == len(self.path):
                    next_index = index
                continue
            class_index = _PATH_CLASS_INDEX.get(entity.type, 0)
            path_features[index, class_index] = 1.0
        progress = np.array([next_index / max(1, len(self.path))], dtype=np.float32)
        return np.concatenate([base, path_features.reshape(-1), progress]).astype(
            np.float32
        )
