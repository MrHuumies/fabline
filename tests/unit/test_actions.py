from __future__ import annotations

import pytest

from fabline.worlds.factory.actions import (
    Action,
    ActionError,
    ActionOp,
    action_mask,
    action_to_index,
    index_to_action,
)
from fabline.worlds.factory.state import Direction, EntityType, TileType


def test_noop_is_legal(line_world) -> None:
    before = line_world.state_hash()
    line_world.apply_action(Action.noop())
    assert line_world.state_hash() == before


def test_build_miner_requires_ore(line_world) -> None:
    with pytest.raises(ActionError) as exc:
        line_world.apply_action(
            Action(ActionOp.BUILD, EntityType.MINER, 10, 6, Direction.EAST)
        )
    assert exc.value.code == "invalid_tile"

    line_world.state.set_tile(10, 6, TileType.ORE)
    line_world.apply_action(
        Action(ActionOp.BUILD, EntityType.MINER, 10, 6, Direction.EAST)
    )
    assert line_world.state.entity_at(10, 6).type is EntityType.MINER


def test_build_rejects_occupied(line_world) -> None:
    with pytest.raises(ActionError) as exc:
        line_world.apply_action(
            Action(ActionOp.BUILD, EntityType.BELT, 1, 4, Direction.EAST)
        )
    assert exc.value.code == "tile_occupied"


def test_remove_depot_rejected(line_world) -> None:
    with pytest.raises(ActionError) as exc:
        line_world.apply_action(Action(ActionOp.REMOVE, x=7, y=4))
    assert exc.value.code == "not_removable"


def test_rotate_changes_direction(line_world) -> None:
    belt = line_world.state.entity_at(2, 4)
    line_world.apply_action(
        Action(ActionOp.ROTATE, x=2, y=4, direction=Direction.SOUTH)
    )
    assert belt.direction is Direction.SOUTH


def test_budget_is_enforced() -> None:
    from fabline.worlds.factory.config import FactoryConfig
    from fabline.worlds.factory.world import FactoryWorld

    config = FactoryConfig(
        width=16,
        height=8,
        entity_budget=8,
        rock_density=0.0,
        starter_line=False,
    )
    world = FactoryWorld(config)
    world.reset(seed=1)
    state = world.state
    # Fill the budget with belts on empty tiles.
    built = len(state.entities)
    for y in range(1, state.height - 1):
        for x in range(1, state.width - 1):
            if built >= config.entity_budget:
                break
            if (x, y) in state.occupancy:
                continue
            if state.tile_at(x, y) is not TileType.EMPTY:
                continue
            world.apply_action(
                Action(ActionOp.BUILD, EntityType.BELT, x, y, Direction.EAST)
            )
            built += 1
        if built >= config.entity_budget:
            break
    with pytest.raises(ActionError) as exc:
        world.apply_action(
            Action(ActionOp.BUILD, EntityType.BELT, 14, 6, Direction.EAST)
        )
    assert exc.value.code == "budget_exhausted"


def test_action_mask_shape_and_contents(line_world) -> None:
    line_world.state.set_tile(10, 6, TileType.ORE)
    mask = action_mask(line_world.state, line_world.config)
    assert mask.shape == (5, 5, line_world.state.height, line_world.state.width, 4)
    assert mask[0, 0, 0, 0, 0]
    assert not mask[0, 0, 1, 1, 0]
    # Miner is legal only on an unoccupied ore tile; belt only on empty ground.
    assert mask[1, int(EntityType.MINER), 6, 10, 0]
    assert not mask[1, int(EntityType.MINER), 5, 9, 0]
    assert mask[1, int(EntityType.BELT), 5, 9, 0]
    assert not mask[1, int(EntityType.BELT), 6, 10, 0]
    # Remove and rotate are legal on the belt, not on the depot.
    assert mask[2, 0, 4, 2, 0]
    assert not mask[2, 0, 4, 7, 0]
    assert mask[3, 0, 4, 2, 0]


def test_action_index_roundtrip(line_world) -> None:
    actions = [
        Action(ActionOp.NOOP),
        Action(ActionOp.BUILD, EntityType.FURNACE, 10, 6, Direction.WEST),
        Action(ActionOp.REMOVE, x=2, y=4),
        Action(ActionOp.ROTATE, x=2, y=4, direction=Direction.SOUTH),
        Action(ActionOp.REPAIR, x=2, y=4),
    ]
    height, width = line_world.state.height, line_world.state.width
    for action in actions:
        index = action_to_index(action, height, width)
        decoded = index_to_action(index, height, width)
        assert decoded == action


def test_invalid_action_does_not_mutate(line_world) -> None:
    before = line_world.state_hash()
    with pytest.raises(ActionError):
        line_world.apply_action(
            Action(ActionOp.BUILD, EntityType.MINER, 10, 6, Direction.EAST)
        )
    assert line_world.state_hash() == before


def test_repair_action_clears_fault(line_world) -> None:
    belt = line_world.state.entity_at(2, 4)
    assert belt is not None
    belt.faulted = True
    belt.wear = 5
    belt.repair_progress = 3
    mask = action_mask(line_world.state, line_world.config)
    assert mask[ActionOp.REPAIR, 0, 4, 2, 0]

    line_world.apply_action(Action(ActionOp.REPAIR, x=2, y=4))
    assert not belt.faulted
    assert belt.wear == 0
    assert belt.repair_progress == 0
    assert any(
        event.kind == "fault_repaired" for event in line_world.state.events
    )


def test_repair_rejects_healthy_entity(line_world) -> None:
    with pytest.raises(ActionError) as exc:
        line_world.apply_action(Action(ActionOp.REPAIR, x=2, y=4))
    assert exc.value.code == "not_faulted"
