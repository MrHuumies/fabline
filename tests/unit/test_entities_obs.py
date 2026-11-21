from __future__ import annotations

import numpy as np

from fabline.obs import EntitiesObservation, GraphObservation, build_observation
from fabline.obs.entities import ENTITY_FEATURES


def test_entities_observation_shapes(line_world) -> None:
    adapter = EntitiesObservation(line_world.config)
    obs = adapter.observe(line_world.state)
    assert isinstance(obs, GraphObservation)
    assert obs.entity_features.shape == (
        adapter.max_entities,
        len(ENTITY_FEATURES),
    )
    assert obs.entity_mask.shape == (adapter.max_entities,)
    assert obs.adjacency.shape == (adapter.max_entities, adapter.max_entities)
    assert obs.entity_mask.sum() == len(line_world.state.entities)
    assert obs.entity_features.dtype == np.float32


def test_entities_observation_adjacency(line_world) -> None:
    adapter = EntitiesObservation(line_world.config)
    obs = adapter.observe(line_world.state)
    # Entities are sorted by id: depot=1, miner=2, belt=3, ...
    # The miner points east into the belt, so index 1 -> index 2.
    assert obs.adjacency[1, 2] == 1.0


def test_entities_observation_is_pure(line_world) -> None:
    adapter = EntitiesObservation(line_world.config)
    before = line_world.state_hash()
    first = adapter.observe(line_world.state)
    second = adapter.observe(line_world.state)
    assert np.array_equal(first.entity_features, second.entity_features)
    assert np.array_equal(first.adjacency, second.adjacency)
    assert line_world.state_hash() == before


def test_entities_flatten_shape(line_world) -> None:
    adapter = EntitiesObservation(line_world.config)
    obs = adapter.observe(line_world.state)
    flat = adapter.flatten(obs)
    expected = (
        adapter.max_entities * len(ENTITY_FEATURES)
        + adapter.max_entities
        + adapter.max_entities * adapter.max_entities
    )
    assert flat.shape == (expected,)
    assert flat.dtype == np.float32


def test_build_entities_observation(small_config) -> None:
    adapter = build_observation("entities", small_config)
    assert isinstance(adapter, EntitiesObservation)
