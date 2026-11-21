"""Deterministic procedural generation for the factory MVP."""

from __future__ import annotations

import random
from dataclasses import dataclass

from .config import FactoryConfig
from .power import PowerConfig
from .state import (
    Direction,
    Entity,
    EntityType,
    PowerSource,
    TileType,
    WorldState,
    empty_delivered,
)
from .wire import generate_wires


@dataclass(frozen=True)
class Scenario:
    """A controlled layout family for splits and benchmark tasks."""

    name: str
    include_assembler: bool
    extra_belt: bool = False
    break_line: bool = False
    ore_patches: int | None = None
    rock_density: float | None = None


SCENARIOS: dict[str, Scenario] = {
    "ingot": Scenario("ingot", include_assembler=False),
    "extra_ingot": Scenario("extra_ingot", include_assembler=False, extra_belt=True),
    "gear": Scenario("gear", include_assembler=True),
    "extra_gear": Scenario("extra_gear", include_assembler=True, extra_belt=True),
    "broken_gear": Scenario("broken_gear", include_assembler=True, break_line=True),
    "shift_gear": Scenario(
        "shift_gear",
        include_assembler=True,
        ore_patches=1,
        rock_density=0.15,
    ),
}


def _line_types(
    rng: random.Random,
    scenario: Scenario | None = None,
) -> list[EntityType | None]:
    """Build a short east-facing production line.

    The line is deliberately simple: miner -> belt -> furnace -> belt ->
    (optional assembler -> belt) -> depot. Extra belts add length; a gap creates
    a broken line and a zero-output scenario.
    """

    line: list[EntityType | None] = [
        EntityType.MINER,
        EntityType.BELT,
        EntityType.FURNACE,
        EntityType.BELT,
    ]
    if scenario is None:
        if rng.random() < 0.75:
            line.extend([EntityType.ASSEMBLER, EntityType.BELT])
        if rng.random() < 0.25:
            line.insert(rng.randrange(1, len(line)), EntityType.BELT)
        if rng.random() < 0.15:
            # Never break the miner; a gap after it can still leave a valid
            # prefix line, but nothing reaches the depot.
            line[rng.randrange(2, len(line))] = None
    else:
        if scenario.include_assembler:
            line.extend([EntityType.ASSEMBLER, EntityType.BELT])
        if scenario.extra_belt:
            line.insert(rng.randrange(1, len(line)), EntityType.BELT)
        if scenario.break_line:
            line[rng.randrange(2, len(line))] = None
    line.append(EntityType.DEPOT)
    return line


def generate_state(
    config: FactoryConfig,
    seed: int,
    scenario: Scenario | None = None,
    power: PowerConfig | None = None,
) -> WorldState:
    """Generate a layout, entities, and an initial state for a seed."""

    rng = random.Random(seed)
    width, height = config.width, config.height
    tiles = [TileType.EMPTY] * (width * height)
    reserved: set[tuple[int, int]] = set()
    ore_patches = (
        config.ore_patches if scenario is None or scenario.ore_patches is None
        else scenario.ore_patches
    )
    rock_density = (
        config.rock_density if scenario is None or scenario.rock_density is None
        else scenario.rock_density
    )

    def set_tile(x: int, y: int, tile: TileType) -> None:
        tiles[y * width + x] = tile

    line_y = rng.randrange(3, max(4, height - 3))
    line: list[EntityType | None] = (
        _line_types(rng, scenario) if config.starter_line else []
    )

    # Reserve the line row so rocks and ore patches do not intrude.
    if line:
        for i in range(len(line)):
            reserved.add((1 + i, line_y))

    # Place the line first.
    entity_specs: list[tuple[EntityType, int, int, Direction]] = []
    if line:
        for i, entity_type in enumerate(line):
            x = 1 + i
            if entity_type is None:
                continue
            if entity_type is EntityType.MINER:
                set_tile(x, line_y, TileType.ORE)
            elif entity_type is EntityType.DEPOT:
                set_tile(x, line_y, TileType.DEPOT)
            entity_specs.append((entity_type, x, line_y, Direction.EAST))
    else:
        depot_x, depot_y = width - 2, height // 2
        set_tile(depot_x, depot_y, TileType.DEPOT)
        reserved.add((depot_x, depot_y))
        entity_specs.append((EntityType.DEPOT, depot_x, depot_y, Direction.EAST))

    # Ore patches away from the line.
    for _ in range(ore_patches):
        cx = rng.randrange(2, width - 2)
        cy = rng.randrange(2, height - 2)
        if line and abs(cy - line_y) <= 1:
            continue
        for dy in range(-config.ore_patch_radius, config.ore_patch_radius + 1):
            for dx in range(-config.ore_patch_radius, config.ore_patch_radius + 1):
                x, y = cx + dx, cy + dy
                if not (1 <= x < width - 1 and 1 <= y < height - 1):
                    continue
                if (x, y) in reserved:
                    continue
                if tiles[y * width + x] is TileType.EMPTY:
                    set_tile(x, y, TileType.ORE)
                    reserved.add((x, y))

    # Rocks fill the remaining empty space.
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if (x, y) in reserved:
                continue
            if tiles[y * width + x] is not TileType.EMPTY:
                continue
            if rng.random() < rock_density:
                set_tile(x, y, TileType.ROCK)

    # Guarantee at least one ore tile.
    if TileType.ORE not in tiles:
        x, y = (1, line_y) if line else (2, 2)
        set_tile(x, y, TileType.ORE)
        reserved.add((x, y))

    entities: dict[int, Entity] = {}
    occupancy: dict[tuple[int, int], int] = {}
    for entity_id, (entity_type, x, y, direction) in enumerate(entity_specs, start=1):
        if (x, y) in occupancy:
            raise RuntimeError(f"generator placed two entities at {(x, y)}")
        entity = Entity(
            id=entity_id,
            type=entity_type,
            x=x,
            y=y,
            direction=direction,
            built_tick=0,
        )
        entities[entity_id] = entity
        occupancy[(x, y)] = entity_id

    power_sources: list[PowerSource] = []
    if power is not None and power.enabled:
        candidates: list[tuple[int, int]] = []
        if line:
            for dy in (-2, 2):
                y = line_y + dy
                if 1 <= y < height - 1:
                    candidates.extend([(1, y), (width - 2, y)])
        for y in sorted(range(1, height - 1), key=lambda value: abs(value - line_y)):
            for x in range(1, width - 1):
                candidates.append((x, y))
        seen: set[tuple[int, int]] = set()
        for x, y in candidates:
            if len(power_sources) >= power.generator_count:
                break
            if (x, y) in seen or (x, y) in occupancy:
                continue
            seen.add((x, y))
            if tiles[y * width + x] is not TileType.EMPTY:
                continue
            power_sources.append(
                PowerSource(
                    id=len(power_sources) + 1,
                    x=x,
                    y=y,
                    capacity=power.generator_capacity,
                )
            )
        if len(power_sources) < power.generator_count:
            raise RuntimeError("not enough empty tiles for power generators")

    power_wires = (
        generate_wires(
            width,
            height,
            tiles,
            occupancy,
            power_sources,
            entities,
            power,
            seed,
        )
        if power is not None and power.enabled
        else []
    )

    load_factors: list[int] = []
    capacity_factors: list[int] = []
    if (
        power is not None
        and power.enabled
        and (power.load_jitter or power.capacity_jitter)
    ):
        variation_rng = random.Random(seed * 1009 + 17)
        remaining = config.ticks_per_episode
        while remaining > 0:
            load = 100 + variation_rng.randint(
                -power.load_jitter, power.load_jitter
            )
            capacity = 100 + variation_rng.randint(
                -power.capacity_jitter, power.capacity_jitter
            )
            block = min(remaining, power.variation_period)
            load_factors.extend([load] * block)
            capacity_factors.extend([capacity] * block)
            remaining -= block

    return WorldState(
        tick=0,
        seed=seed,
        width=width,
        height=height,
        tiles=tiles,
        entities=entities,
        occupancy=occupancy,
        next_entity_id=len(entities) + 1,
        delivered=empty_delivered(),
        score=0,
        history=[],
        events=[],
        power_sources=power_sources,
        power_wires=power_wires,
        power_load_factors=load_factors,
        power_capacity_factors=capacity_factors,
    )


def generated_ore_tiles(state: WorldState) -> int:
    return sum(1 for tile in state.tiles if tile is TileType.ORE)
