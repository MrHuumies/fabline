"""Canonical factory state.

The state is the source of truth. Observations and labels are derived from it.
All fields that affect future transitions are included in the state hash.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from fabline.core.events import Event
from fabline.core.hashing import canonical_hash


class TileType(IntEnum):
    EMPTY = 0
    ROCK = 1
    ORE = 2
    DEPOT = 3


class EntityType(IntEnum):
    MINER = 1
    BELT = 2
    FURNACE = 3
    ASSEMBLER = 4
    DEPOT = 5


class Direction(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    @property
    def delta(self) -> tuple[int, int]:
        if self is Direction.NORTH:
            return (0, -1)
        if self is Direction.EAST:
            return (1, 0)
        if self is Direction.SOUTH:
            return (0, 1)
        return (-1, 0)


class Item(IntEnum):
    ORE = 0
    INGOT = 1
    GEAR = 2


@dataclass(frozen=True)
class PowerSource:
    """A pre-placed generator. It is infrastructure, not an entity."""

    id: int
    x: int
    y: int
    capacity: int


@dataclass
class PowerWire:
    """An orthogonal wire edge between two adjacent cells.

    Wires are infrastructure, not entities: they do not occupy the entity grid.
    A failed wire is removed from the connectivity graph.
    """

    id: int
    ax: int
    ay: int
    bx: int
    by: int
    failed: bool = False
    degraded: bool = False
    failure_tick: int = 0

    def cells(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return (self.ax, self.ay), (self.bx, self.by)


@dataclass
class Entity:
    id: int
    type: EntityType
    x: int
    y: int
    direction: Direction = Direction.EAST
    built_tick: int = 0
    input_buffer: dict[Item, int] = field(default_factory=dict)
    output_buffer: dict[Item, int] = field(default_factory=dict)
    craft_progress: int = 0
    blocked_ticks: int = 0
    wear: int = 0
    faulted: bool = False
    repair_progress: int = 0
    maintenance_remaining: int = 0
    temperature: int = 0
    vibration: int = 0
    acoustic: int = 0
    powered: bool = False
    brownout_ticks: int = 0

    def total_input(self) -> int:
        return sum(self.input_buffer.values())

    def total_output(self) -> int:
        return sum(self.output_buffer.values())

    def canonical(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "type": int(self.type),
            "x": self.x,
            "y": self.y,
            "direction": int(self.direction),
            "built_tick": self.built_tick,
            "input": sorted([int(k), v] for k, v in self.input_buffer.items()),
            "output": sorted([int(k), v] for k, v in self.output_buffer.items()),
            "craft_progress": self.craft_progress,
            "blocked_ticks": self.blocked_ticks,
        }
        # Keep fault-free hashes identical to the frozen factory-v0.1 format.
        if (
            self.wear
            or self.faulted
            or self.repair_progress
            or self.maintenance_remaining
            or self.temperature
            or self.vibration
            or self.acoustic
            or self.powered
            or self.brownout_ticks
        ):
            result["wear"] = self.wear
            result["faulted"] = self.faulted
            result["repair_progress"] = self.repair_progress
            result["maintenance_remaining"] = self.maintenance_remaining
            result["temperature"] = self.temperature
            result["vibration"] = self.vibration
            result["acoustic"] = self.acoustic
            result["powered"] = self.powered
            result["brownout_ticks"] = self.brownout_ticks
        return result


@dataclass
class WorldState:
    tick: int
    seed: int
    width: int
    height: int
    tiles: list[TileType]
    entities: dict[int, Entity]
    occupancy: dict[tuple[int, int], int]
    next_entity_id: int
    delivered: dict[Item, int]
    score: int
    history: list[tuple[int, int, int]]
    events: list[Event]
    power_sources: list[PowerSource] = field(default_factory=list)
    power_wires: list[PowerWire] = field(default_factory=list)
    power_load_factors: list[int] = field(default_factory=list)
    power_capacity_factors: list[int] = field(default_factory=list)
    power_priority: int = 0
    recipe_index: int = 0

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile_at(self, x: int, y: int) -> TileType:
        return self.tiles[y * self.width + x]

    def set_tile(self, x: int, y: int, tile: TileType) -> None:
        self.tiles[y * self.width + x] = tile

    def entity_at(self, x: int, y: int) -> Entity | None:
        entity_id = self.occupancy.get((x, y))
        if entity_id is None:
            return None
        return self.entities[entity_id]

    def clone(self, keep_events: bool = False) -> WorldState:
        clone = copy.deepcopy(self)
        if not keep_events:
            clone.events = []
        return clone

    def canonical(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "tick": self.tick,
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "tiles": [int(t) for t in self.tiles],
            "entities": [
                self.entities[eid].canonical() for eid in sorted(self.entities)
            ],
            "next_entity_id": self.next_entity_id,
            "delivered": sorted([int(k), v] for k, v in self.delivered.items()),
            "score": self.score,
            "history": [list(row) for row in self.history],
        }
        # Keep power-free hashes identical to the frozen format.
        if self.power_sources:
            result["power_sources"] = [
                {
                    "id": source.id,
                    "x": source.x,
                    "y": source.y,
                    "capacity": source.capacity,
                }
                for source in sorted(self.power_sources, key=lambda item: item.id)
            ]
        if self.power_wires:
            result["power_wires"] = [
                {
                    "id": wire.id,
                    "ax": wire.ax,
                    "ay": wire.ay,
                    "bx": wire.bx,
                    "by": wire.by,
                    "failed": wire.failed,
                    "degraded": wire.degraded,
                    "failure_tick": wire.failure_tick,
                }
                for wire in sorted(self.power_wires, key=lambda item: item.id)
            ]
        if self.power_load_factors or self.power_capacity_factors:
            result["power_load_factors"] = list(self.power_load_factors)
            result["power_capacity_factors"] = list(
                self.power_capacity_factors
            )
        if self.power_priority:
            result["power_priority"] = self.power_priority
        if self.recipe_index:
            result["recipe_index"] = self.recipe_index
        return result

    def state_hash(self) -> str:
        return canonical_hash(self.canonical())


def empty_delivered() -> dict[Item, int]:
    return {Item.ORE: 0, Item.INGOT: 0, Item.GEAR: 0}


def inventory_counts(state: WorldState) -> dict[Item, int]:
    """Count items currently held by entities (inputs and outputs)."""

    counts = empty_delivered()
    for entity in state.entities.values():
        for item, count in entity.input_buffer.items():
            counts[item] += count
        for item, count in entity.output_buffer.items():
            counts[item] += count
    return counts


def entity_counts(state: WorldState) -> dict[EntityType, int]:
    counts = {entity_type: 0 for entity_type in EntityType}
    for entity in state.entities.values():
        counts[entity.type] += 1
    return counts


def tile_counts(state: WorldState) -> dict[TileType, int]:
    counts = {tile_type: 0 for tile_type in TileType}
    for tile in state.tiles:
        counts[tile] += 1
    return counts
