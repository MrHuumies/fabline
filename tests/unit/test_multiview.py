from __future__ import annotations

import numpy as np
import pytest

from fabline.obs import (
    LineStateObservation,
    MultiviewFrame,
    MultiviewObservation,
    VectorObservation,
    build_observation,
    build_registered_view,
    flatten_observation,
    register_view,
)


def _views(line_world):
    return {
        "vector": VectorObservation(line_world.config),
        "line": LineStateObservation(line_world.config),
    }


def test_multiview_frame_mask_and_flatten(line_world) -> None:
    adapter = MultiviewObservation(
        line_world.config,
        _views(line_world),
        {"vector": True, "line": False},
    )
    frame = adapter.observe(line_world.state)
    assert isinstance(frame, MultiviewFrame)
    assert frame.view_mask == {"vector": True, "line": False}
    assert set(frame.views) == {"vector", "line"}
    values = adapter.flatten(frame)
    assert values.shape == (24,)
    assert values.dtype == np.float32
    assert np.any(values[:18])
    assert np.all(values[18:] == 0.0)
    assert adapter.spec.name == "multiview"
    assert adapter.spec.version == "1.0.0"
    assert adapter.spec.shape == (24,)


def test_multiview_dynamic_mask(line_world) -> None:
    adapter = MultiviewObservation(line_world.config, _views(line_world))
    frame = adapter.observe(line_world.state, view_mask={"line": False})
    assert frame.view_mask["vector"] is True
    assert frame.view_mask["line"] is False
    with pytest.raises(ValueError):
        adapter.observe(line_world.state, view_mask={"missing": True})


def test_build_multiview_and_flatten_helper(line_world) -> None:
    adapter = build_observation(
        "multiview",
        line_world.config,
        views=_views(line_world),
        view_mask={"vector": True, "line": True},
    )
    assert isinstance(adapter, MultiviewObservation)
    frame = adapter.observe(line_world.state)
    values = flatten_observation(adapter, frame)
    assert values.shape == (24,)
    line_values = LineStateObservation(line_world.config).observe(
        line_world.state
    ).reshape(-1)
    assert np.array_equal(values[18:], line_values)


def test_registered_view_factory(line_world) -> None:
    register_view(
        "test_vector_view",
        lambda config, _faults, _power: VectorObservation(config),
    )
    adapter = build_registered_view(
        "test_vector_view", line_world.config
    )
    assert isinstance(adapter, VectorObservation)


def test_multiview_rejects_unknown_mask(line_world) -> None:
    with pytest.raises(ValueError):
        MultiviewObservation(
            line_world.config,
            _views(line_world),
            {"missing": True},
        )
