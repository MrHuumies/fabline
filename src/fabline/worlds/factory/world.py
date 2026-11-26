"""The deterministic factory tick loop."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from fabline.core.events import Event

from .actions import Action, action_mask, apply_action
from .actions import repair_entity as repair_state_entity
from .config import FactoryConfig
from .faults import FaultConfig
from .generator import Scenario, generate_state
from .power import PowerConfig
from .production import ProductionConfig
from .recipe import RecipeConfig
from .state import Entity, EntityType, Item, WorldState
from .wire import entity_connected, reachable_cells


class FactoryWorld:
    """A small, deterministic factory.

    The world owns the canonical state and advances it in fixed phases:
    machines, logistics, metrics. It does not know about observations or ML.
    """

    def __init__(
        self,
        config: FactoryConfig | None = None,
        faults: FaultConfig | None = None,
        power: PowerConfig | None = None,
        recipe: RecipeConfig | None = None,
        production: ProductionConfig | None = None,
    ) -> None:
        self.config = config or FactoryConfig()
        self.faults = faults or FaultConfig()
        self.power = power or PowerConfig()
        self.recipe = recipe
        self.production = production
        self.state = generate_state(self.config, seed=0, power=self.power)
        self._enable_production_state()
        self._tick_delivered: dict[Item, int] = {Item.INGOT: 0, Item.GEAR: 0}
        self._suppress_events = False

    def reset(self, seed: int, scenario: Scenario | None = None) -> WorldState:
        self.state = generate_state(self.config, seed, scenario, self.power)
        self._enable_production_state()
        self._tick_delivered = {Item.INGOT: 0, Item.GEAR: 0}
        self._suppress_events = False
        return self.state

    def _enable_production_state(self) -> None:
        if self.production is not None and self.production.enabled:
            self.state.delivered.setdefault(Item.COMPONENT, 0)

    @property
    def done(self) -> bool:
        return self.state.tick >= self.config.ticks_per_episode

    def tick(self) -> None:
        if self.done:
            return
        self.state.tick += 1
        self._tick_delivered = {Item.INGOT: 0, Item.GEAR: 0}
        self._telemetry()
        self._power()
        self._machines()
        self._logistics()
        self._finish_tick()

    def run_ticks(self, ticks: int) -> None:
        for _ in range(ticks):
            if self.done:
                break
            self.tick()

    def apply_action(self, action: Action) -> None:
        apply_action(self.state, self.config, action)

    def action_mask(self) -> np.ndarray:
        return action_mask(self.state, self.config)

    def repair_entity(self, entity: Entity) -> bool:
        return repair_state_entity(self.state, self.config, entity)

    def clone(self, keep_events: bool = False) -> FactoryWorld:
        clone = object.__new__(FactoryWorld)
        clone.config = self.config
        clone.faults = self.faults
        clone.power = self.power
        clone.recipe = self.recipe
        clone.production = self.production
        clone.state = self.state.clone(keep_events=keep_events)
        clone._tick_delivered = dict(self._tick_delivered)
        clone._suppress_events = not keep_events
        return clone

    def state_hash(self) -> str:
        return self.state.state_hash()

    def score_last_window(self) -> int:
        return sum(
            self.config.depot_ingot_score * ingots + self.config.depot_gear_score * gears
            for _, ingots, gears in self.state.history
        )

    # -- phases ---------------------------------------------------------

    def _telemetry(self) -> None:
        """Decay and warm sensor state. Explicitly before machine work."""

        if not self.faults.enabled:
            return
        threshold = max(1, self.faults.fault_threshold)
        for entity in sorted(self.state.entities.values(), key=lambda item: item.id):
            wear = min(100, entity.wear * 100 // threshold)
            target = min(
                100,
                wear * 40 // 100
                + (20 if entity.craft_progress > 0 else 0)
                + (40 if entity.faulted else 0),
            )
            entity.temperature = (15 * entity.temperature + target) // 16
            entity.vibration = 3 * entity.vibration // 4
            entity.acoustic = 7 * entity.acoustic // 8

    def _sensor_impulse(self, entity: Entity, channel: str, amount: int) -> None:
        if not self.faults.enabled or amount <= 0:
            return
        current = getattr(entity, channel)
        setattr(entity, channel, min(100, current + amount))

    def _load_factor(self) -> int:
        factors = self.state.power_load_factors
        if not factors:
            return 100
        index = min(len(factors) - 1, max(0, self.state.tick - 1))
        return factors[index]

    def _capacity_factor(self) -> int:
        factors = self.state.power_capacity_factors
        if not factors:
            return 100
        index = min(len(factors) - 1, max(0, self.state.tick - 1))
        return factors[index]

    def fail_wire(self, wire_id: int) -> bool:
        """Mark a wire failed and emit the transition once."""

        wire = next(
            (item for item in self.state.power_wires if item.id == wire_id),
            None,
        )
        if wire is None:
            raise RuntimeError(f"wire {wire_id} does not exist")
        if wire.failed:
            return False
        wire.failed = True
        wire.degraded = False
        wire.failure_tick = 0
        self._emit(
            "power_wire_fault",
            {
                "wire_id": wire.id,
                "ax": wire.ax,
                "ay": wire.ay,
                "bx": wire.bx,
                "by": wire.by,
            },
        )
        return True

    def degrade_wire(self, wire_id: int, failure_tick: int) -> bool:
        """Mark a wire degraded with a scheduled failure tick."""

        wire = next(
            (item for item in self.state.power_wires if item.id == wire_id),
            None,
        )
        if wire is None:
            raise RuntimeError(f"wire {wire_id} does not exist")
        if wire.failed or (
            failure_tick != 0 and failure_tick <= self.state.tick
        ):
            return False
        wire.degraded = True
        wire.failure_tick = failure_tick
        self._emit(
            "power_wire_degraded",
            {
                "wire_id": wire.id,
                "failure_tick": failure_tick,
            },
        )
        return True

    def repair_wire(self, wire_id: int) -> bool:
        """Mark a wire repaired and emit the transition once."""

        wire = next(
            (item for item in self.state.power_wires if item.id == wire_id),
            None,
        )
        if wire is None:
            raise RuntimeError(f"wire {wire_id} does not exist")
        if not wire.failed and not wire.degraded:
            return False
        wire.failed = False
        wire.degraded = False
        wire.failure_tick = 0
        self._emit(
            "power_wire_repair",
            {
                "wire_id": wire.id,
                "ax": wire.ax,
                "ay": wire.ay,
                "bx": wire.bx,
                "by": wire.by,
            },
        )
        return True

    def _apply_wire_fault(self) -> None:
        """Fail the configured wire once, before connectivity is computed."""

        if self.power.topology != "wired":
            return
        if (
            self.power.wire_fault_tick <= 0
            or self.state.tick != self.power.wire_fault_tick
        ):
            return
        self.fail_wire(self.power.wire_fault_id)

    def _apply_wire_degradation(self) -> None:
        """Fail any degraded wire whose scheduled failure tick arrived."""

        for wire in self.state.power_wires:
            if (
                wire.degraded
                and not wire.failed
                and wire.failure_tick
                and self.state.tick >= wire.failure_tick
            ):
                self.fail_wire(wire.id)

    def _power(self) -> None:
        """Allocate generator capacity and update powered/brownout state."""

        if not self.power.enabled:
            return
        self._apply_wire_degradation()
        self._apply_wire_fault()
        entities = sorted(self.state.entities.values(), key=lambda item: item.id)
        previous = {entity.id: entity.powered for entity in entities}
        load_factor = self._load_factor()
        capacity_factor = self._capacity_factor()
        wired = self.power.topology == "wired"

        for entity in entities:
            if self.power.scaled_demand(entity, load_factor) == 0:
                entity.powered = True
            else:
                entity.powered = False

        consumers = [
            entity
            for entity in entities
            if self.power.scaled_demand(entity, load_factor) > 0
            and not entity.faulted
        ]
        priority = self.state.power_priority
        if priority == 1:
            consumers.sort(
                key=lambda entity: (
                    0 if entity.type is EntityType.FURNACE else 1,
                    entity.id,
                )
            )
        elif priority == 2:
            consumers.sort(
                key=lambda entity: (
                    0 if entity.type is EntityType.ASSEMBLER else 1,
                    entity.id,
                )
            )
        wires = self.state.power_wires
        for source in sorted(
            self.state.power_sources, key=lambda item: item.id
        ):
            remaining = source.capacity * capacity_factor // 100
            reachable = (
                reachable_cells(source, self.state.power_wires)
                if wired
                else None
            )
            for entity in consumers:
                if entity.powered:
                    continue
                if wired:
                    assert reachable is not None
                    if not entity_connected(entity, reachable, wires):
                        continue
                else:
                    distance = abs(entity.x - source.x) + abs(
                        entity.y - source.y
                    )
                    if distance > self.power.generator_radius:
                        continue
                demand = self.power.scaled_demand(entity, load_factor)
                if demand <= remaining:
                    entity.powered = True
                    remaining -= demand

        for entity in entities:
            demand = self.power.scaled_demand(entity, load_factor)
            if demand == 0:
                continue
            if entity.faulted:
                entity.powered = False
                continue
            if entity.powered:
                if entity.id in previous and not previous[entity.id]:
                    self._emit(
                        "power_restored",
                        {"entity_id": entity.id, "type": entity.type.name},
                    )
            else:
                entity.brownout_ticks += 1
                if entity.id in previous and previous[entity.id]:
                    self._emit(
                        "power_brownout",
                        {"entity_id": entity.id, "type": entity.type.name},
                    )

    def _has_power(self, entity: Entity) -> bool:
        if not self.power.enabled:
            return True
        return (
            entity.powered
            or self.power.scaled_demand(entity, self._load_factor()) == 0
        )

    def maintain_entity(self, entity: Entity) -> bool:
        """Take a non-faulted machine offline for preventive maintenance."""

        if entity.faulted or entity.maintenance_remaining > 0:
            return False
        entity.maintenance_remaining = self.faults.maintenance_ticks
        self._emit(
            "maintenance_started",
            {"entity_id": entity.id, "type": entity.type.name},
        )
        return True

    def _maintenance(self) -> None:
        for entity in sorted(
            self.state.entities.values(), key=lambda item: item.id
        ):
            if entity.maintenance_remaining <= 0:
                continue
            entity.maintenance_remaining -= 1
            if entity.maintenance_remaining == 0:
                entity.wear = 0
                self._emit(
                    "maintenance_completed",
                    {"entity_id": entity.id, "type": entity.type.name},
                )

    def _machines(self) -> None:
        for entity in sorted(self.state.entities.values(), key=lambda item: item.id):
            if entity.maintenance_remaining > 0:
                continue
            if entity.type is EntityType.MINER:
                if self._fault_tick(entity):
                    continue
                if not self._has_power(entity):
                    continue
                elapsed = self.state.tick - entity.built_tick
                if (
                    elapsed > 0
                    and elapsed % self.config.miner_ticks_per_ore == 0
                    and entity.total_output() < self.config.miner_output_capacity
                ):
                    entity.output_buffer[Item.ORE] = (
                        entity.output_buffer.get(Item.ORE, 0) + 1
                    )
                    self._wear(entity, self.faults.miner_wear_per_ore)
                    self._sensor_impulse(entity, "vibration", 50)
                    self._emit(
                        "item_spawned",
                        {"entity_id": entity.id, "item": Item.ORE.name},
                    )
            elif entity.type is EntityType.FURNACE:
                self._advance_machine(
                    entity,
                    inputs={Item.ORE: 1},
                    output=Item.INGOT,
                    craft_ticks=self.config.furnace_ticks,
                    input_capacity=self.config.furnace_input_capacity,
                    output_capacity=self.config.furnace_output_capacity,
                )
            elif entity.type is EntityType.ASSEMBLER:
                byproduct = None
                if (
                    self.production is not None
                    and self.production.enabled
                    and self.state.production_recipe
                ):
                    inputs = {
                        Item.INGOT: self.production.component_ingot_cost
                    }
                    craft_ticks = self.production.component_ticks
                    output = Item.COMPONENT
                elif (
                    self.recipe is not None
                    and self.recipe.enabled
                    and self.state.recipe_index
                ):
                    inputs = {Item.INGOT: self.recipe.slow_cost}
                    craft_ticks = self.recipe.slow_ticks
                    if self.recipe.byproduct_enabled:
                        byproduct = (
                            self.recipe.byproduct_per_slow,
                            self.recipe.byproduct_capacity,
                        )
                else:
                    inputs = {Item.INGOT: self.config.assembler_ingot_cost}
                    craft_ticks = self.config.assembler_ticks
                if not (
                    self.production is not None
                    and self.production.enabled
                    and self.state.production_recipe
                ):
                    output = Item.GEAR
                self._advance_machine(
                    entity,
                    inputs=inputs,
                    output=output,
                    craft_ticks=craft_ticks,
                    input_capacity=self.config.assembler_input_capacity,
                    output_capacity=self.config.assembler_output_capacity,
                    byproduct=byproduct,
                )

    def _advance_machine(
        self,
        entity: Entity,
        *,
        inputs: Mapping[Item, int],
        output: Item,
        craft_ticks: int,
        input_capacity: int,
        output_capacity: int,
        byproduct: tuple[int, int] | None = None,
    ) -> None:
        if self._fault_tick(entity):
            return
        if not self._has_power(entity):
            return

        output_count = entity.output_buffer.get(output, 0)

        if entity.craft_progress > 0:
            entity.craft_progress -= 1
            if entity.craft_progress == 0:
                entity.output_buffer[output] = output_count + 1
                if byproduct is not None:
                    entity.byproduct += byproduct[0]
                self._wear(entity, self.faults.wear_per_craft)
                self._emit(
                    "craft_completed",
                    {"entity_id": entity.id, "item": output.name},
                )
            return

        if output_count + 1 > output_capacity:
            return
        if byproduct is not None and entity.byproduct >= byproduct[1]:
            return
        for item, need in inputs.items():
            if entity.input_buffer.get(item, 0) < need:
                return
        for item, need in inputs.items():
            remaining = entity.input_buffer[item] - need
            if remaining:
                entity.input_buffer[item] = remaining
            else:
                del entity.input_buffer[item]
        entity.craft_progress = craft_ticks
        self._sensor_impulse(entity, "vibration", 70)
        self._emit(
            "craft_started",
            {"entity_id": entity.id, "item": output.name},
        )

    def _logistics(self) -> None:
        intents: list[tuple[Entity, Item]] = []
        for entity in sorted(self.state.entities.values(), key=lambda item: item.id):
            if entity.type is EntityType.DEPOT or not entity.output_buffer:
                continue
            if (
                self.power.enabled
                and not entity.powered
                and not entity.faulted
            ):
                continue
            item = min(entity.output_buffer, key=int)
            intents.append((entity, item))

        accepted_belts: set[int] = set()
        reserved: dict[int, dict[Item, int]] = {}

        for entity, item in intents:
            dx, dy = entity.direction.delta
            tx, ty = entity.x + dx, entity.y + dy
            if not self.state.in_bounds(tx, ty):
                self._block(entity, item, "out_of_bounds")
                continue
            receiver_id = self.state.occupancy.get((tx, ty))
            if receiver_id is None:
                self._block(entity, item, "no_receiver")
                continue
            receiver = self.state.entities[receiver_id]

            accept = False
            if receiver.type is EntityType.BELT:
                accept = not receiver.output_buffer and receiver.id not in accepted_belts
            elif receiver.type is EntityType.FURNACE:
                if item is Item.ORE:
                    already = reserved.get(receiver.id, {}).get(Item.ORE, 0)
                    accept = (
                        receiver.input_buffer.get(Item.ORE, 0) + already
                        < self.config.furnace_input_capacity
                    )
            elif receiver.type is EntityType.ASSEMBLER:
                if item is Item.INGOT:
                    already = reserved.get(receiver.id, {}).get(Item.INGOT, 0)
                    accept = (
                        receiver.input_buffer.get(Item.INGOT, 0) + already
                        < self.config.assembler_input_capacity
                    )
            elif receiver.type is EntityType.DEPOT:
                accept = item in (Item.INGOT, Item.GEAR)
                if (
                    item is Item.COMPONENT
                    and self.production is not None
                    and self.production.enabled
                ):
                    accept = True

            if not accept:
                self._block(entity, item, "receiver_full")
                continue

            count = entity.output_buffer[item]
            if count <= 1:
                del entity.output_buffer[item]
            else:
                entity.output_buffer[item] = count - 1

            if receiver.type is EntityType.DEPOT:
                self.state.delivered[item] += 1
                self.state.score += self._score_for_item(item)
                self._tick_delivered[item] = self._tick_delivered.get(item, 0) + 1
                self._emit(
                    "item_delivered",
                    {"entity_id": receiver.id, "item": item.name},
                )
            elif receiver.type is EntityType.BELT:
                receiver.output_buffer[item] = receiver.output_buffer.get(item, 0) + 1
                accepted_belts.add(receiver.id)
                self._emit(
                    "item_moved",
                    {"from": entity.id, "to": receiver.id, "item": item.name},
                )
            else:
                receiver.input_buffer[item] = receiver.input_buffer.get(item, 0) + 1
                reserved.setdefault(receiver.id, {})
                reserved[receiver.id][item] = reserved[receiver.id].get(item, 0) + 1
                self._emit(
                    "item_moved",
                    {"from": entity.id, "to": receiver.id, "item": item.name},
                )

    def _block(self, entity: Entity, item: Item, reason: str) -> None:
        entity.blocked_ticks += 1
        self._sensor_impulse(entity, "acoustic", 40)
        self._emit(
            "item_blocked",
            {"entity_id": entity.id, "item": item.name, "reason": reason},
        )

    def _fault_tick(self, entity: Entity) -> bool:
        """Advance a faulted entity's repair timer. True means skip its work."""

        if not self.faults.enabled or not entity.faulted:
            return False
        entity.repair_progress += 1
        if entity.repair_progress >= self.faults.repair_ticks:
            entity.faulted = False
            entity.repair_progress = 0
            entity.wear = 0
            self._emit(
                "fault_repaired",
                {"entity_id": entity.id, "type": entity.type.name},
            )
        return True

    def _wear(self, entity: Entity, amount: int) -> None:
        if not self.faults.enabled or amount <= 0:
            return
        entity.wear += amount
        if entity.wear >= self.faults.fault_threshold and not entity.faulted:
            entity.faulted = True
            entity.repair_progress = 0
            self._sensor_impulse(entity, "acoustic", 80)
            self._emit(
                "fault_started",
                {"entity_id": entity.id, "type": entity.type.name},
            )

    def _finish_tick(self) -> None:
        self._maintenance()
        self.state.history.append(
            (
                self.state.tick,
                self._tick_delivered.get(Item.INGOT, 0),
                self._tick_delivered.get(Item.GEAR, 0),
            )
        )
        overflow = len(self.state.history) - self.config.history_window
        if overflow > 0:
            del self.state.history[:overflow]

    def _score_for_item(self, item: Item) -> int:
        if item is Item.INGOT:
            return self.config.depot_ingot_score
        if item is Item.GEAR:
            return self.config.depot_gear_score
        if (
            item is Item.COMPONENT
            and self.production is not None
            and self.production.enabled
        ):
            return self.production.component_score
        return 0

    def _emit(self, kind: str, data: dict[str, Any]) -> None:
        if self._suppress_events or not self.config.emit_events:
            return
        self.state.events.append(Event(tick=self.state.tick, kind=kind, data=data))
        if len(self.state.events) > self.config.max_events:
            del self.state.events[: len(self.state.events) - self.config.max_events]
