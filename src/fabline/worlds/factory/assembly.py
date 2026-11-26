"""A fixed assembly-cell layout for the opt-in production tree.

The cell has two independent input lines into one assembly assembler:

- component line: miner -> belt -> furnace -> belt -> component assembler ->
  belts -> assembly assembler (from the north);
- ingot line: miner -> belt -> furnace -> belts -> assembly assembler (from the
  south);
- gear output: assembly assembler -> belt -> depot.

This is task content, not a new generator family. It keeps the default factory
and frozen benchmarks untouched.
"""

from __future__ import annotations

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import (
    Direction,
    Entity,
    EntityType,
    Item,
    TileType,
    WorldState,
    empty_delivered,
)

ASSEMBLY_CELL_WIDTH = 12
ASSEMBLY_CELL_HEIGHT = 8


def generate_assembly_state(
    config: FactoryConfig,
    seed: int = 0,
) -> WorldState:
    """Build the deterministic assembly-cell state."""

    if config.width < ASSEMBLY_CELL_WIDTH or config.height < ASSEMBLY_CELL_HEIGHT:
        raise ValueError("assembly cell needs at least a 12x8 world")
    width, height = config.width, config.height
    tiles = [TileType.EMPTY] * (width * height)
    for x, y in ((1, 1), (1, 5)):
        tiles[y * width + x] = TileType.ORE
    tiles[4 * width + 9] = TileType.DEPOT

    specs: list[tuple[EntityType, int, int, Direction, int]] = [
        # Component line.
        (EntityType.MINER, 1, 1, Direction.EAST, 0),
        (EntityType.BELT, 2, 1, Direction.EAST, 0),
        (EntityType.FURNACE, 3, 1, Direction.EAST, 0),
        (EntityType.BELT, 4, 1, Direction.EAST, 0),
        (EntityType.ASSEMBLER, 5, 1, Direction.EAST, 1),
        (EntityType.BELT, 6, 1, Direction.EAST, 0),
        (EntityType.BELT, 7, 1, Direction.SOUTH, 0),
        (EntityType.BELT, 7, 2, Direction.SOUTH, 0),
        (EntityType.BELT, 7, 3, Direction.SOUTH, 0),
        # Assembly cell.
        (EntityType.ASSEMBLER, 7, 4, Direction.EAST, 0),
        (EntityType.BELT, 8, 4, Direction.EAST, 0),
        (EntityType.DEPOT, 9, 4, Direction.EAST, 0),
        # Ingot line.
        (EntityType.MINER, 1, 5, Direction.EAST, 0),
        (EntityType.BELT, 2, 5, Direction.EAST, 0),
        (EntityType.FURNACE, 3, 5, Direction.EAST, 0),
        (EntityType.BELT, 4, 5, Direction.EAST, 0),
        (EntityType.BELT, 5, 5, Direction.EAST, 0),
        (EntityType.BELT, 6, 5, Direction.EAST, 0),
        (EntityType.BELT, 7, 5, Direction.NORTH, 0),
    ]
    entities: dict[int, Entity] = {}
    occupancy: dict[tuple[int, int], int] = {}
    for entity_id, (entity_type, x, y, direction, recipe) in enumerate(
        specs, start=1
    ):
        if (x, y) in occupancy:
            raise RuntimeError(f"assembly layout collision at {(x, y)}")
        entities[entity_id] = Entity(
            id=entity_id,
            type=entity_type,
            x=x,
            y=y,
            direction=direction,
            built_tick=0,
            recipe=recipe,
        )
        occupancy[(x, y)] = entity_id
    delivered = empty_delivered()
    delivered.setdefault(Item.COMPONENT, 0)
    return WorldState(
        tick=0,
        seed=seed,
        width=width,
        height=height,
        tiles=tiles,
        entities=entities,
        occupancy=occupancy,
        next_entity_id=max(entities) + 1,
        delivered=delivered,
        score=0,
        history=[],
        events=[],
    )
