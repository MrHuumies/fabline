from __future__ import annotations

import numpy as np

from fabline.obs.base import build_observation, flatten_observation
from fabline.obs.grid import GridObservation
from fabline.obs.partial import (
    DelayedObservation,
    FeatureDropoutObservation,
    GridFogObservation,
)
from fabline.obs.vector import VectorObservation


def test_feature_dropout_is_deterministic(line_world) -> None:
    view = FeatureDropoutObservation(
        VectorObservation(line_world.config),
        dropout=0.5,
        seed=7,
    )
    first = view.observe(line_world.state)
    second = view.observe(line_world.state)
    assert np.array_equal(first, second)
    assert first.shape == (18,)
    assert np.any(first == 0.0)
    assert view.spec.name == "vector_dropout"
    assert flatten_observation(view, first).shape == (18,)


def test_grid_fog_hides_distant_cells(line_world) -> None:
    view = GridFogObservation(
        GridObservation(line_world.config),
        radius=2,
        seed=0,
    )
    line_world.run_ticks(15)
    observation = view.observe(line_world.state)
    assert observation.shape == (8, 16, 6)
    center_x, center_y = view._center(line_world.state)
    for y in range(observation.shape[0]):
        for x in range(observation.shape[1]):
            if abs(x - center_x) + abs(y - center_y) > view.radius:
                assert not observation[y, x, :].any()
    assert view.spec.name == "grid_fog"


def test_delayed_observation_returns_history(line_world) -> None:
    base = VectorObservation(line_world.config)
    view = DelayedObservation(base, delay=2)
    view.reset()
    direct = []
    delayed = []
    for _ in range(4):
        direct.append(base.observe(line_world.state))
        delayed.append(view.observe(line_world.state))
        line_world.tick()
    assert np.array_equal(delayed[0], direct[0])
    assert np.array_equal(delayed[1], direct[0])
    assert np.array_equal(delayed[2], direct[0])
    assert np.array_equal(delayed[3], direct[1])


def test_build_partial_observations(line_world) -> None:
    assert isinstance(
        build_observation("grid_fog", line_world.config),
        GridFogObservation,
    )
    assert isinstance(
        build_observation("vector_dropout", line_world.config),
        FeatureDropoutObservation,
    )
