from __future__ import annotations

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS, generate_state
from fabline.worlds.factory.power import PowerConfig
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


def test_random_gear_places_two_lines_and_wires() -> None:
    config = FactoryConfig(width=32, height=16, ore_patches=1)
    power = PowerConfig(
        enabled=True,
        topology="wired",
        generator_count=1,
        generator_capacity=24,
        generator_radius=8,
        wire_redundancy=2,
    )
    state = generate_state(
        config, seed=6000, scenario=SCENARIOS["random_gear"], power=power
    )
    types = [entity.type for entity in state.entities.values()]
    assert types.count(EntityType.MINER) == 2
    assert types.count(EntityType.DEPOT) == 2
    assert len(state.power_wires) > 0
    assert len(state.power_sources) == 1


def test_spread_gear_places_three_lines() -> None:
    config = FactoryConfig(width=48, height=24, ore_patches=1)
    power = PowerConfig(
        enabled=True,
        topology="wired",
        generator_count=1,
        generator_capacity=48,
        generator_radius=8,
        wire_redundancy=2,
    )
    state = generate_state(
        config, seed=10000, scenario=SCENARIOS["spread_gear"], power=power
    )
    types = [entity.type for entity in state.entities.values()]
    assert types.count(EntityType.MINER) == 3
    assert types.count(EntityType.DEPOT) == 3
    assert len(state.power_wires) > 0
    second = generate_state(
        config, seed=10000, scenario=SCENARIOS["spread_gear"], power=power
    )
    assert state.state_hash() == second.state_hash()
