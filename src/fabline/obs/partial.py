"""Partial-observability wrappers for existing observation adapters."""

from __future__ import annotations

import random
from collections import deque

import numpy as np

from fabline.obs.base import ObservationAdapter, ObservationSpec, flatten_observation
from fabline.worlds.factory.state import WorldState


class FeatureDropoutObservation:
    """Zero a deterministic fraction of an observation's elements.

    The mask is derived from the seed and the state tick, so the same state
    always produces the same corrupted observation. This is a dataset-level
    corruption, not a world mechanic.
    """

    def __init__(
        self,
        base: ObservationAdapter,
        *,
        dropout: float = 0.2,
        seed: int = 0,
    ) -> None:
        if not 0.0 <= dropout <= 1.0:
            raise ValueError("dropout must be in [0, 1]")
        self.base = base
        self.dropout = dropout
        self.seed = seed
        self.spec = ObservationSpec(
            name=f"{base.spec.name}_dropout",
            version="0.1.0",
            shape=base.spec.shape,
            feature_names=base.spec.feature_names,
            format=base.spec.format,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        observation = np.asarray(self.base.observe(state), dtype=np.float32)
        if self.dropout <= 0.0:
            return observation
        rng = random.Random(self.seed * 1000003 + state.tick)
        mask = np.asarray(
            [rng.random() < self.dropout for _ in range(observation.size)],
            dtype=bool,
        ).reshape(observation.shape)
        return np.where(mask, 0.0, observation).astype(np.float32)

    def flatten(self, observation: np.ndarray) -> np.ndarray:
        return flatten_observation(self.base, observation)


class GridFogObservation:
    """A moving visibility window over a grid observation.

    Cells outside a Manhattan radius around a patrol center are zeroed. The
    patrol is deterministic from the tick, so replay and regeneration match.
    """

    def __init__(
        self,
        base: ObservationAdapter,
        *,
        radius: int = 3,
        seed: int = 0,
    ) -> None:
        if radius < 0:
            raise ValueError("radius must be non-negative")
        self.base = base
        self.radius = radius
        self.seed = seed
        self.spec = ObservationSpec(
            name=f"{base.spec.name}_fog",
            version="0.1.0",
            shape=base.spec.shape,
            feature_names=base.spec.feature_names,
            format=base.spec.format,
        )

    def _center(self, state: WorldState) -> tuple[int, int]:
        width = state.width
        height = state.height
        span = max(1, width - 4)
        x = 2 + (state.tick // 10 + self.seed) % span
        y = height // 2
        return x, y

    def observe(self, state: WorldState) -> np.ndarray:
        observation = np.asarray(self.base.observe(state), dtype=np.float32)
        if observation.ndim != 3 or self.radius < 0:
            return observation
        center_x, center_y = self._center(state)
        out = observation.copy()
        for y in range(observation.shape[0]):
            for x in range(observation.shape[1]):
                if abs(x - center_x) + abs(y - center_y) > self.radius:
                    out[y, x, :] = 0.0
        return out

    def flatten(self, observation: np.ndarray) -> np.ndarray:
        return flatten_observation(self.base, observation)


class DelayedObservation:
    """Return an observation delayed by a fixed number of calls.

    The wrapper is stateful. Call ``reset()`` at episode boundaries. It is
    intended for dataset generation and environment wrappers, not canonical
    state.
    """

    def __init__(
        self,
        base: ObservationAdapter,
        *,
        delay: int = 1,
    ) -> None:
        if delay < 0:
            raise ValueError("delay must be non-negative")
        self.base = base
        self.delay = delay
        self.history: deque[np.ndarray] = deque(maxlen=delay + 1)
        self.spec = ObservationSpec(
            name=f"{base.spec.name}_delayed",
            version="0.1.0",
            shape=base.spec.shape,
            feature_names=base.spec.feature_names,
            format=base.spec.format,
        )

    def reset(self) -> None:
        self.history.clear()

    def observe(self, state: WorldState) -> np.ndarray:
        observation = np.asarray(self.base.observe(state), dtype=np.float32)
        self.history.append(observation.copy())
        return self.history[0]

    def flatten(self, observation: np.ndarray) -> np.ndarray:
        return flatten_observation(self.base, observation)
