from __future__ import annotations

from fabline.worlds.factory.state import (
    Direction,
    EntityType,
    Item,
    TileType,
    entity_counts,
    inventory_counts,
    tile_counts,
)


def test_direction_deltas() -> None:
    assert Direction.NORTH.delta == (0, -1)
    assert Direction.EAST.delta == (1, 0)
    assert Direction.SOUTH.delta == (0, 1)
    assert Direction.WEST.delta == (-1, 0)


def test_entity_lookup_and_bounds(line_world) -> None:
    state = line_world.state
    assert state.in_bounds(0, 0)
    assert not state.in_bounds(-1, 0)
    assert not state.in_bounds(state.width, 0)
    assert state.entity_at(1, 4).type is EntityType.MINER
    assert state.entity_at(0, 0) is None
    assert state.tile_at(1, 4) is TileType.ORE
    assert state.tile_at(7, 4) is TileType.DEPOT


def test_clone_is_independent(line_world) -> None:
    clone = line_world.state.clone()
    clone.tick = 999
    clone.score = 123
    assert line_world.state.tick != 999
    assert line_world.state.score != 123


def test_clone_drops_events_by_default(line_world) -> None:
    line_world.run_ticks(10)
    assert line_world.state.events
    clone = line_world.state.clone()
    assert clone.events == []
    kept = line_world.state.clone(keep_events=True)
    assert len(kept.events) == len(line_world.state.events)


def test_state_hash_is_stable_and_sensitive(line_world) -> None:
    first = line_world.state_hash()
    second = line_world.state.clone().state_hash()
    assert first == second
    line_world.state.score += 1
    assert line_world.state_hash() != first


def test_inventory_and_counts(line_world) -> None:
    state = line_world.state
    counts = entity_counts(state)
    assert counts[EntityType.MINER] == 1
    assert counts[EntityType.BELT] == 3
    assert counts[EntityType.FURNACE] == 1
    assert counts[EntityType.ASSEMBLER] == 1
    assert counts[EntityType.DEPOT] == 1

    state.entity_at(2, 4).output_buffer[Item.ORE] = 1
    assert inventory_counts(state)[Item.ORE] == 1
    tiles = tile_counts(state)
    assert tiles[TileType.ORE] == 1
    assert tiles[TileType.DEPOT] == 1
