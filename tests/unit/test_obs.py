from __future__ import annotations

import numpy as np
import pytest

from fabline.obs import (
    GridObservation,
    VectorObservation,
    build_observation,
)
from fabline.worlds.factory.state import EntityType


def test_grid_observation_shape_and_range(line_world) -> None:
    obs = GridObservation(line_world.config)
    values = obs.observe(line_world.state)
    assert values.shape == (line_world.state.height, line_world.state.width, 6)
    assert values.dtype == np.float32
    assert values.min() >= 0.0
    assert values.max() <= 1.0
    assert values[4, 1, 1] == pytest.approx(int(EntityType.MINER) / 5.0)


def test_grid_observation_is_pure(line_world) -> None:
    adapter = GridObservation(line_world.config)
    before = line_world.state_hash()
    first = adapter.observe(line_world.state)
    second = adapter.observe(line_world.state)
    assert np.array_equal(first, second)
    assert line_world.state_hash() == before


def test_vector_observation_shape_and_features(line_world) -> None:
    adapter = VectorObservation(line_world.config)
    values = adapter.observe(line_world.state)
    assert values.shape == (len(adapter.spec.feature_names),)
    assert values.dtype == np.float32
    assert adapter.feature_index("tick_norm") == 0
    assert adapter.feature_index("score_last_window_norm") == 2


def test_vector_observation_updates(line_world) -> None:
    adapter = VectorObservation(line_world.config)
    first = adapter.observe(line_world.state)
    line_world.run_ticks(50)
    second = adapter.observe(line_world.state)
    assert second[0] > first[0]
    assert second[2] >= first[2]


def test_build_observation() -> None:
    from fabline.worlds.factory.config import FactoryConfig

    config = FactoryConfig(width=16, height=8)
    assert isinstance(build_observation("vector", config), VectorObservation)
    assert isinstance(build_observation("grid", config), GridObservation)
    with pytest.raises(ValueError):
        build_observation("unknown", config)
