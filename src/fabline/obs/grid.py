"""Dense grid observation."""

from __future__ import annotations

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import EntityType, WorldState

from .base import (
    ObservationSpec,
    craft_ticks,
    input_capacity,
    output_capacity,
)

CHANNELS = (
    "tile_type",
    "entity_type",
    "direction",
    "input_fill",
    "output_fill",
    "craft_progress",
)


class GridObservation:
    """A fixed-shape ``(H, W, 6)`` float32 view of the factory."""

    def __init__(self, config: FactoryConfig) -> None:
        self.config = config
        self.shape = (config.height, config.width, len(CHANNELS))
        self.spec = ObservationSpec(
            name="grid",
            version="0.1.0",
            shape=self.shape,
            feature_names=CHANNELS,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        out = np.zeros(self.shape, dtype=np.float32)
        for y in range(state.height):
            for x in range(state.width):
                tile = state.tile_at(x, y)
                out[y, x, 0] = int(tile) / 3.0
                entity = state.entity_at(x, y)
                if entity is None:
                    continue
                out[y, x, 1] = int(entity.type) / 5.0
                if entity.type is not EntityType.DEPOT:
                    out[y, x, 2] = (int(entity.direction) + 1) / 4.0
                in_cap = input_capacity(self.config, entity.type)
                out_cap = output_capacity(self.config, entity.type)
                if in_cap:
                    out[y, x, 3] = entity.total_input() / in_cap
                if out_cap:
                    out[y, x, 4] = entity.total_output() / out_cap
                ticks = craft_ticks(self.config, entity.type)
                if ticks:
                    out[y, x, 5] = entity.craft_progress / ticks
        return np.asarray(out, dtype=np.float32)
