"""Build/remove/rotate actions and their legality mask."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

import numpy as np

from .config import FactoryConfig
from .state import Direction, Entity, EntityType, TileType, WorldState


class ActionOp(IntEnum):
    NOOP = 0
    BUILD = 1
    REMOVE = 2
    ROTATE = 3
    REPAIR = 4


class ActionError(ValueError):
    """A typed action failure. The state is never partially mutated."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Action:
    op: ActionOp
    entity: EntityType | None = None
    x: int | None = None
    y: int | None = None
    direction: Direction | None = None

    @classmethod
    def noop(cls) -> Action:
        return cls(ActionOp.NOOP)


_BUILDABLE = {
    EntityType.BELT,
    EntityType.FURNACE,
    EntityType.ASSEMBLER,
}


def _require(value: object, name: str) -> None:
    if value is None:
        raise ActionError("missing_field", f"{name} is required for this action")


def validate_action(state: WorldState, config: FactoryConfig, action: Action) -> None:
    """Validate an action without mutating the state."""

    if action.op is ActionOp.NOOP:
        return

    if action.op is ActionOp.BUILD:
        _require(action.entity, "entity")
        _require(action.x, "x")
        _require(action.y, "y")
        _require(action.direction, "direction")
        assert action.entity is not None and action.x is not None
        assert action.y is not None and action.direction is not None
        if action.entity is EntityType.DEPOT:
            raise ActionError("invalid_entity", "depots are not buildable")
        if not state.in_bounds(action.x, action.y):
            raise ActionError("out_of_bounds", f"({action.x}, {action.y}) is outside the grid")
        if (action.x, action.y) in state.occupancy:
            raise ActionError("tile_occupied", f"({action.x}, {action.y}) is occupied")
        if len(state.entities) >= config.entity_budget:
            raise ActionError("budget_exhausted", "entity budget is exhausted")
        tile = state.tile_at(action.x, action.y)
        if action.entity is EntityType.MINER:
            if tile is not TileType.ORE:
                raise ActionError("invalid_tile", "miners require an ore tile")
        elif action.entity in _BUILDABLE:
            if tile is not TileType.EMPTY:
                raise ActionError(
                    "invalid_tile",
                    f"{action.entity.name.lower()} requires empty ground",
                )
        else:
            raise ActionError("invalid_entity", f"cannot build {action.entity.name}")
        return

    if action.op is ActionOp.REMOVE:
        _require(action.x, "x")
        _require(action.y, "y")
        assert action.x is not None and action.y is not None
        if not state.in_bounds(action.x, action.y):
            raise ActionError("out_of_bounds", f"({action.x}, {action.y}) is outside the grid")
        entity = state.entity_at(action.x, action.y)
        if entity is None:
            raise ActionError("empty_tile", f"({action.x}, {action.y}) has no entity")
        if entity.type is EntityType.DEPOT:
            raise ActionError("not_removable", "depots are fixed")
        return

    if action.op is ActionOp.ROTATE:
        _require(action.x, "x")
        _require(action.y, "y")
        _require(action.direction, "direction")
        assert action.x is not None and action.y is not None
        if not state.in_bounds(action.x, action.y):
            raise ActionError("out_of_bounds", f"({action.x}, {action.y}) is outside the grid")
        entity = state.entity_at(action.x, action.y)
        if entity is None:
            raise ActionError("empty_tile", f"({action.x}, {action.y}) has no entity")
        if entity.type is EntityType.DEPOT:
            raise ActionError("not_rotatable", "depots have no direction")
        return

    if action.op is ActionOp.REPAIR:
        _require(action.x, "x")
        _require(action.y, "y")
        assert action.x is not None and action.y is not None
        if not state.in_bounds(action.x, action.y):
            raise ActionError("out_of_bounds", f"({action.x}, {action.y}) is outside the grid")
        entity = state.entity_at(action.x, action.y)
        if entity is None:
            raise ActionError("empty_tile", f"({action.x}, {action.y}) has no entity")
        if entity.type is EntityType.DEPOT:
            raise ActionError("not_repairable", "depots cannot be repaired")
        if not entity.faulted:
            raise ActionError("not_faulted", "entity is not faulted")
        return

    raise ActionError("invalid_op", f"unknown action op {action.op}")


def apply_action(state: WorldState, config: FactoryConfig, action: Action) -> None:
    """Validate and apply an action. Raises before mutating on failure."""

    validate_action(state, config, action)

    if action.op is ActionOp.NOOP:
        return

    if action.op is ActionOp.BUILD:
        assert action.entity is not None and action.x is not None
        assert action.y is not None and action.direction is not None
        entity = Entity(
            id=state.next_entity_id,
            type=action.entity,
            x=action.x,
            y=action.y,
            direction=action.direction,
            built_tick=state.tick,
        )
        state.entities[entity.id] = entity
        state.occupancy[(entity.x, entity.y)] = entity.id
        state.next_entity_id += 1
        _emit(state, config, "build", {"entity_id": entity.id, "type": entity.type.name})
        return

    if action.op is ActionOp.REMOVE:
        assert action.x is not None and action.y is not None
        target = state.entity_at(action.x, action.y)
        assert target is not None
        for item, count in list(target.input_buffer.items()) + list(target.output_buffer.items()):
            if count:
                _emit(
                    state,
                    config,
                    "item_destroyed",
                    {"entity_id": target.id, "item": item.name, "count": count},
                )
        del state.entities[target.id]
        del state.occupancy[(target.x, target.y)]
        _emit(state, config, "remove", {"entity_id": target.id, "type": target.type.name})
        return

    if action.op is ActionOp.ROTATE:
        assert action.x is not None and action.y is not None
        target = state.entity_at(action.x, action.y)
        assert target is not None and action.direction is not None
        target.direction = action.direction
        _emit(
            state,
            config,
            "rotate",
            {"entity_id": target.id, "direction": target.direction.name},
        )
        return

    if action.op is ActionOp.REPAIR:
        assert action.x is not None and action.y is not None
        target = state.entity_at(action.x, action.y)
        assert target is not None
        repair_entity(state, config, target)
        return


def repair_entity(state: WorldState, config: FactoryConfig, entity: Entity) -> bool:
    """Clear a fault and wear. Returns False if the entity was not faulted."""

    if not entity.faulted:
        return False
    entity.faulted = False
    entity.repair_progress = 0
    entity.wear = 0
    _emit(
        state,
        config,
        "fault_repaired",
        {"entity_id": entity.id, "type": entity.type.name},
    )
    return True


def _emit(
    state: WorldState,
    config: FactoryConfig,
    kind: str,
    data: dict[str, Any],
) -> None:
    if not config.emit_events:
        return
    # Imported lazily to keep this module usable in isolation.
    from fabline.core.events import Event

    state.events.append(Event(tick=state.tick, kind=kind, data=data))
    if len(state.events) > config.max_events:
        del state.events[: len(state.events) - config.max_events]


def action_mask(state: WorldState, config: FactoryConfig) -> np.ndarray:
    """Boolean mask over the compact action space.

    Shape: ``(4, 5, H, W, 4)`` = (op, entity, y, x, direction). ``entity`` 0 is
    used by noop/remove/rotate; build uses 1..4. Only one canonical noop entry
    is true; the caller can short-circuit it.
    """

    height, width = state.height, state.width
    mask = np.zeros((5, 5, height, width, 4), dtype=bool)
    mask[int(ActionOp.NOOP), 0, 0, 0, 0] = True

    if len(state.entities) < config.entity_budget:
        for y in range(height):
            for x in range(width):
                if (x, y) in state.occupancy:
                    continue
                tile = state.tile_at(x, y)
                if tile is TileType.ORE:
                    mask[int(ActionOp.BUILD), int(EntityType.MINER), y, x, :] = True
                elif tile is TileType.EMPTY:
                    for entity_type in _BUILDABLE:
                        mask[int(ActionOp.BUILD), int(entity_type), y, x, :] = True

    for entity in state.entities.values():
        if entity.type is EntityType.DEPOT:
            continue
        mask[int(ActionOp.REMOVE), 0, entity.y, entity.x, 0] = True
        mask[int(ActionOp.ROTATE), 0, entity.y, entity.x, :] = True
        if entity.faulted:
            mask[int(ActionOp.REPAIR), 0, entity.y, entity.x, 0] = True

    return mask


def action_to_index(action: Action, height: int, width: int) -> int:
    entity = int(action.entity) if action.entity is not None else 0
    x = action.x if action.x is not None else 0
    y = action.y if action.y is not None else 0
    direction = int(action.direction) if action.direction is not None else 0
    return ((((int(action.op) * 5) + entity) * height + y) * width + x) * 4 + direction


def index_to_action(index: int, height: int, width: int) -> Action:
    direction = index % 4
    index //= 4
    x = index % width
    index //= width
    y = index % height
    index //= height
    entity = index % 5
    op = index // 5
    if op == int(ActionOp.NOOP):
        return Action(ActionOp.NOOP)
    if op == int(ActionOp.BUILD):
        return Action(
            ActionOp.BUILD,
            entity=EntityType(entity),
            x=x,
            y=y,
            direction=Direction(direction),
        )
    if op == int(ActionOp.REMOVE):
        return Action(ActionOp.REMOVE, x=x, y=y)
    if op == int(ActionOp.ROTATE):
        return Action(ActionOp.ROTATE, x=x, y=y, direction=Direction(direction))
    if op == int(ActionOp.REPAIR):
        return Action(ActionOp.REPAIR, x=x, y=y)
    raise ValueError(f"action index {index} is out of range")
