"""Fixed-size layout summary for layout-shift tasks.

The base factory vector does not expose layout size or line count, so a model
trained on small layouts cannot scale its prediction on larger ones. This view
appends the layout descriptors while keeping a fixed feature width.
"""

from __future__ import annotations

import numpy as np

from fabline.obs.base import ObservationSpec
from fabline.obs.grid import CHANNELS, GridObservation
from fabline.obs.vector import FEATURES, VectorObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import WorldState

LAYOUT_FEATURES = (
    "width_norm",
    "height_norm",
    "line_count_norm",
    "entity_budget_norm",
    "rock_density",
    "ore_patches_norm",
    "cells_norm",
)


class PaddedGridObservation:
    """A fixed 24x32 grid with a valid mask and layout descriptors."""

    def __init__(
        self,
        config: FactoryConfig,
        *,
        line_count: int,
        canvas_height: int = 24,
        canvas_width: int = 32,
    ) -> None:
        if config.width > canvas_width or config.height > canvas_height:
            raise ValueError("layout is larger than the padded grid canvas")
        self.config = config
        self.line_count = line_count
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.base = GridObservation(config)
        self._shape = (
            canvas_height,
            canvas_width,
            len(CHANNELS) + 1 + len(LAYOUT_FEATURES),
        )
        self.spec = ObservationSpec(
            name="padded-grid",
            version="0.1.0",
            shape=self._shape,
            feature_names=CHANNELS + ("valid",) + LAYOUT_FEATURES,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        grid = self.base.observe(state)
        out = np.zeros(self._shape, dtype=np.float32)
        height = min(grid.shape[0], self.canvas_height)
        width = min(grid.shape[1], self.canvas_width)
        out[:height, :width, : len(CHANNELS)] = grid[:height, :width]
        out[:height, :width, len(CHANNELS)] = 1.0
        cells = max(1, self.config.width * self.config.height)
        descriptors = np.asarray(
            (
                self.config.width / 32.0,
                self.config.height / 32.0,
                self.line_count / 3.0,
                self.config.entity_budget / 64.0,
                self.config.rock_density,
                self.config.ore_patches / 4.0,
                cells / 1024.0,
            ),
            dtype=np.float32,
        )
        out[:, :, len(CHANNELS) + 1 :] = descriptors
        return out


class LayoutSummaryObservation:
    """Vector observation plus fixed layout descriptors."""

    def __init__(
        self,
        config: FactoryConfig,
        *,
        line_count: int,
    ) -> None:
        self.config = config
        self.line_count = line_count
        self.base = VectorObservation(config)
        self.spec = ObservationSpec(
            name="layout-summary",
            version="0.1.0",
            shape=(len(FEATURES) + len(LAYOUT_FEATURES),),
            feature_names=FEATURES + LAYOUT_FEATURES,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        cells = max(1, self.config.width * self.config.height)
        extra = (
            self.config.width / 32.0,
            self.config.height / 32.0,
            self.line_count / 3.0,
            self.config.entity_budget / 64.0,
            self.config.rock_density,
            self.config.ore_patches / 4.0,
            cells / 1024.0,
        )
        return np.concatenate(
            [self.base.observe(state), np.asarray(extra, dtype=np.float32)]
        )
