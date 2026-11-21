from __future__ import annotations

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import generate_state
from fabline.worlds.factory.state import EntityType, TileType


def test_generator_is_deterministic() -> None:
    config = FactoryConfig(width=16, height=8)
    first = generate_state(config, seed=7)
    second = generate_state(config, seed=7)
    third = generate_state(config, seed=8)
    assert first.state_hash() == second.state_hash()
    assert first.state_hash() != third.state_hash()


def test_generator_has_depot_and_ore() -> None:
    config = FactoryConfig(width=16, height=8)
    state = generate_state(config, seed=3)
    assert any(entity.type is EntityType.DEPOT for entity in state.entities.values())
    assert TileType.ORE in state.tiles
    assert TileType.DEPOT in state.tiles


def test_generator_has_no_overlap_and_in_bounds() -> None:
    config = FactoryConfig(width=16, height=8)
    state = generate_state(config, seed=5)
    assert len(state.occupancy) == len(state.entities)
    for entity_id, entity in state.entities.items():
        assert state.in_bounds(entity.x, entity.y)
        assert state.occupancy[(entity.x, entity.y)] == entity_id
