"""Supervised labels derived from a factory state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .state import EntityType, Item

if TYPE_CHECKING:
    from .world import FactoryWorld


def future_score(world: FactoryWorld, horizon: int = 100) -> int:
    """Depot score gained over the next ``horizon`` ticks with no actions."""

    clone = world.clone()
    start = clone.state.score
    clone.run_ticks(horizon)
    return clone.state.score - start


def future_delivered(world: FactoryWorld, item: Item, horizon: int = 100) -> int:
    """Items delivered to the depot over the next ``horizon`` ticks."""

    clone = world.clone()
    start = clone.state.delivered[item]
    clone.run_ticks(horizon)
    return clone.state.delivered[item] - start


def future_fault(world: FactoryWorld, horizon: int = 50) -> int:
    """Return 1 if a new fault starts within the next ``horizon`` ticks."""

    before = sum(event.kind == "fault_started" for event in world.state.events)
    clone = world.clone(keep_events=True)
    clone.run_ticks(horizon)
    after = sum(event.kind == "fault_started" for event in clone.state.events)
    return int(after > before)


def future_brownout(world: FactoryWorld, horizon: int = 5) -> int:
    """Return 1 if a new brownout starts within the next ``horizon`` ticks."""

    if not world.power.enabled:
        return 0
    before = sum(
        event.kind == "power_brownout" for event in world.state.events
    )
    clone = world.clone(keep_events=True)
    clone.run_ticks(horizon)
    after = sum(
        event.kind == "power_brownout" for event in clone.state.events
    )
    return int(after > before)


def bottleneck_label(world: FactoryWorld, horizon: int = 30) -> str:
    """Return the entity type whose removal most reduces future score.

    This is a counterfactual label. It removes each non-depot entity in a clone
    and compares the future score to the unmodified baseline. Ties and
    zero-output states return ``"none"``.
    """

    baseline_clone = world.clone()
    start = baseline_clone.state.score
    baseline_clone.run_ticks(horizon)
    baseline = baseline_clone.state.score - start

    best_drop = 0
    best_type = "none"
    for entity in sorted(world.state.entities.values(), key=lambda item: item.id):
        if entity.type is EntityType.DEPOT:
            continue
        clone = world.clone()
        clone.state.entities.pop(entity.id, None)
        clone.state.occupancy.pop((entity.x, entity.y), None)
        start = clone.state.score
        clone.run_ticks(horizon)
        drop = baseline - (clone.state.score - start)
        if drop > best_drop:
            best_drop = drop
            best_type = entity.type.name.lower()
    return best_type
