from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fabline.worlds.factory.actions import Action, ActionOp
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import (
    Direction,
    Entity,
    EntityType,
    TileType,
)
from fabline.worlds.factory.world import FactoryWorld


@pytest.fixture
def small_config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )


@pytest.fixture
def line_world() -> FactoryWorld:
    """A known miner -> belt -> furnace -> belt -> assembler -> belt -> depot line."""

    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        ore_patch_radius=0,
        starter_line=False,
        emit_events=True,
    )
    world = FactoryWorld(config)
    world.reset(seed=0)
    state = world.state
    state.tiles = [TileType.EMPTY] * (config.width * config.height)
    state.entities.clear()
    state.occupancy.clear()
    state.events.clear()
    state.next_entity_id = 1
    state.delivered = {item: 0 for item in state.delivered}
    state.score = 0
    state.history.clear()

    state.set_tile(7, 4, TileType.DEPOT)
    state.entities[1] = Entity(id=1, type=EntityType.DEPOT, x=7, y=4)
    state.occupancy[(7, 4)] = 1
    state.next_entity_id = 2

    state.set_tile(1, 4, TileType.ORE)
    actions = [
        Action(ActionOp.BUILD, EntityType.MINER, 1, 4, Direction.EAST),
        Action(ActionOp.BUILD, EntityType.BELT, 2, 4, Direction.EAST),
        Action(ActionOp.BUILD, EntityType.FURNACE, 3, 4, Direction.EAST),
        Action(ActionOp.BUILD, EntityType.BELT, 4, 4, Direction.EAST),
        Action(ActionOp.BUILD, EntityType.ASSEMBLER, 5, 4, Direction.EAST),
        Action(ActionOp.BUILD, EntityType.BELT, 6, 4, Direction.EAST),
    ]
    for action in actions:
        world.apply_action(action)
    state.events.clear()
    return world
