"""Power-grid observation views."""

from __future__ import annotations

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import Entity, EntityType, WorldState
from fabline.worlds.factory.wire import (
    entity_connected,
    reachable_cells,
    wire_summary,
)

from .base import ObservationSpec, craft_ticks, input_capacity, output_capacity

POWER_FEATURES = (
    "tick_norm",
    "capacity_norm",
    "demand_ratio",
    "powered_ratio",
    "brownout_ratio",
    "mean_brownout_ticks_norm",
    "miner_powered_ratio",
    "belt_powered_ratio",
    "furnace_powered_ratio",
    "assembler_powered_ratio",
    "headroom_norm",
    "source_count_norm",
)

POWER_GRID_CHANNELS = ("supply", "demand", "powered")


def _factor(factors: list[int], tick: int) -> int:
    if not factors:
        return 100
    return factors[min(len(factors) - 1, max(0, tick - 1))]


def _active(entities: list[Entity], power: PowerConfig) -> list[Entity]:
    return [
        entity
        for entity in entities
        if power.active_demand(entity) > 0 and not entity.faulted
    ]


class PowerObservation:
    """A 12-feature aggregate view of the power grid."""

    def __init__(self, config: FactoryConfig, power: PowerConfig) -> None:
        self.config = config
        self.power = power
        self.spec = ObservationSpec(
            name="power",
            version="0.1.0",
            shape=(len(POWER_FEATURES),),
            feature_names=POWER_FEATURES,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        if not self.power.enabled:
            return np.zeros(len(POWER_FEATURES), dtype=np.float32)
        entities = list(state.entities.values())
        active = _active(entities, self.power)
        load_factor = _factor(state.power_load_factors, state.tick)
        capacity_factor = _factor(state.power_capacity_factors, state.tick)
        capacity = sum(
            source.capacity * capacity_factor // 100
            for source in state.power_sources
        )
        demand = sum(
            self.power.scaled_demand(entity, load_factor)
            for entity in active
        )
        powered = [entity for entity in active if entity.powered]
        brownouts = [entity for entity in active if not entity.powered]
        max_capacity = max(
            1, self.power.generator_count * self.power.generator_capacity
        )
        demand_ratio = min(1.0, demand / capacity) if capacity else 0.0
        powered_ratio = len(powered) / len(active) if active else 0.0
        brownout_ratio = len(brownouts) / len(active) if active else 0.0
        mean_brownout = (
            float(np.mean([entity.brownout_ticks for entity in active]))
            / max(1, self.config.ticks_per_episode)
            if active
            else 0.0
        )
        per_type = []
        for entity_type in (
            EntityType.MINER,
            EntityType.BELT,
            EntityType.FURNACE,
            EntityType.ASSEMBLER,
        ):
            group = [entity for entity in active if entity.type is entity_type]
            per_type.append(
                sum(1 for entity in group if entity.powered) / len(group)
                if group
                else 0.0
            )
        headroom = (
            max(0, capacity - demand) / capacity if capacity else 0.0
        )
        values = (
            state.tick / self.config.ticks_per_episode,
            min(1.0, capacity / max_capacity),
            demand_ratio,
            powered_ratio,
            brownout_ratio,
            mean_brownout,
            *per_type,
            headroom,
            min(1.0, len(state.power_sources) / self.power.generator_count),
        )
        return np.asarray(values, dtype=np.float32)


class PowerGridObservation:
    """A `(H, W, 3)` spatial view: supply coverage, demand, powered."""

    def __init__(self, config: FactoryConfig, power: PowerConfig) -> None:
        self.config = config
        self.power = power
        self.shape = (config.height, config.width, len(POWER_GRID_CHANNELS))
        self.spec = ObservationSpec(
            name="power_grid",
            version="0.1.0",
            shape=self.shape,
            feature_names=POWER_GRID_CHANNELS,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        out = np.zeros(self.shape, dtype=np.float32)
        if not self.power.enabled:
            return out
        max_capacity = max(1, self.power.generator_capacity)
        capacity_factor = _factor(state.power_capacity_factors, state.tick)
        for source in state.power_sources:
            supply = source.capacity * capacity_factor / 100 / max_capacity
            for y in range(state.height):
                for x in range(state.width):
                    if abs(x - source.x) + abs(y - source.y) <= (
                        self.power.generator_radius
                    ):
                        out[y, x, 0] = min(1.0, out[y, x, 0] + supply)
        max_demand = max(1, self.power.max_demand())
        load_factor = _factor(state.power_load_factors, state.tick)
        for entity in state.entities.values():
            demand = self.power.scaled_demand(entity, load_factor)
            out[entity.y, entity.x, 1] = demand / max_demand
            powered = entity.powered and not entity.faulted
            out[entity.y, entity.x, 2] = 1.0 if powered else 0.0
        return out


class PowerControlObservation:
    """Power features plus the line buffers needed for allocation control.

    18 features: the 12 aggregate power features, then assembler input,
    furnace output, assembler craft progress, furnace craft progress, miner
    output, and score.
    """

    def __init__(self, config: FactoryConfig, power: PowerConfig) -> None:
        self.config = config
        self.power = power
        self.power_view = PowerObservation(config, power)
        self.shape = (len(POWER_FEATURES) + 6,)
        self.spec = ObservationSpec(
            name="power_control",
            version="0.1.0",
            shape=self.shape,
            feature_names=(
                *POWER_FEATURES,
                "assembler_input_norm",
                "furnace_output_norm",
                "assembler_craft_norm",
                "furnace_craft_norm",
                "miner_output_norm",
                "score_norm",
            ),
        )

    def _entity(self, state: WorldState, entity_type: EntityType) -> Entity | None:
        return next(
            (
                entity
                for entity in state.entities.values()
                if entity.type is entity_type
            ),
            None,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        power = self.power_view.observe(state)
        assembler = self._entity(state, EntityType.ASSEMBLER)
        furnace = self._entity(state, EntityType.FURNACE)
        miner = self._entity(state, EntityType.MINER)
        assembler_input = (
            assembler.total_input()
            / max(1, input_capacity(self.config, EntityType.ASSEMBLER))
            if assembler
            else 0.0
        )
        furnace_output = (
            furnace.total_output()
            / max(1, output_capacity(self.config, EntityType.FURNACE))
            if furnace
            else 0.0
        )
        assembler_craft = (
            assembler.craft_progress
            / max(1, craft_ticks(self.config, EntityType.ASSEMBLER))
            if assembler
            else 0.0
        )
        furnace_craft = (
            furnace.craft_progress
            / max(1, craft_ticks(self.config, EntityType.FURNACE))
            if furnace
            else 0.0
        )
        miner_output = (
            miner.total_output()
            / max(1, output_capacity(self.config, EntityType.MINER))
            if miner
            else 0.0
        )
        extras = np.asarray(
            [
                assembler_input,
                furnace_output,
                assembler_craft,
                furnace_craft,
                miner_output,
                state.score / 500.0,
            ],
            dtype=np.float32,
        )
        return np.concatenate([power, extras]).astype(np.float32)


POWER_TOPOLOGY_FEATURES = (
    "wire_count_norm",
    "failed_wire_ratio",
    "connected_ratio",
    "disconnected_ratio",
    "component_count_norm",
    "max_component_ratio",
    "redundancy_ratio",
    "fault_marker",
)

POWER_WIRE_CHANNELS = (
    "horizontal_wire",
    "vertical_wire",
    "failed_wire",
    "connected_wire",
)


class PowerTopologyObservation:
    """Aggregate wire-graph features for the wired topology."""

    def __init__(self, config: FactoryConfig, power: PowerConfig) -> None:
        self.config = config
        self.power = power
        self.spec = ObservationSpec(
            name="power_topology",
            version="0.1.0",
            shape=(len(POWER_TOPOLOGY_FEATURES),),
            feature_names=POWER_TOPOLOGY_FEATURES,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        if not self.power.enabled or not state.power_wires:
            return np.zeros(len(POWER_TOPOLOGY_FEATURES), dtype=np.float32)
        summary = wire_summary(state.power_wires)
        wires = state.power_wires
        active = _active(list(state.entities.values()), self.power)
        reachable: set[tuple[int, int]] = set()
        for source in state.power_sources:
            reachable |= reachable_cells(source, state.power_wires)
        connected = sum(
            1 for entity in active if entity_connected(entity, reachable, wires)
        )
        connected_ratio = connected / len(active) if active else 0.0
        values = (
            summary.wire_count / max(1, state.width * state.height),
            (
                summary.failed_wire_count / summary.wire_count
                if summary.wire_count
                else 0.0
            ),
            connected_ratio,
            1.0 - connected_ratio,
            (
                summary.component_count / summary.wire_count
                if summary.wire_count
                else 0.0
            ),
            (
                summary.max_component_size / summary.node_count
                if summary.node_count
                else 0.0
            ),
            (
                summary.redundancy / summary.wire_count
                if summary.wire_count
                else 0.0
            ),
            1.0 if summary.failed_wire_count else 0.0,
        )
        return np.asarray(values, dtype=np.float32)


class PowerWiresObservation:
    """A `(H, W, 4)` view of horizontal, vertical, failed, and live wires."""

    def __init__(self, config: FactoryConfig, power: PowerConfig) -> None:
        self.config = config
        self.power = power
        self.shape = (config.height, config.width, len(POWER_WIRE_CHANNELS))
        self.spec = ObservationSpec(
            name="power_wires",
            version="0.1.0",
            shape=self.shape,
            feature_names=POWER_WIRE_CHANNELS,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        out = np.zeros(self.shape, dtype=np.float32)
        if not self.power.enabled or not state.power_wires:
            return out
        reachable: set[tuple[int, int]] = set()
        for source in state.power_sources:
            reachable |= reachable_cells(source, state.power_wires)
        for wire in state.power_wires:
            channel = 0 if wire.ay == wire.by else 1
            cells = ((wire.ax, wire.ay), (wire.bx, wire.by))
            for x, y in cells:
                out[y, x, channel] = 1.0
                if wire.failed:
                    out[y, x, 2] = 1.0
                if not wire.failed and all(
                    cell in reachable for cell in cells
                ):
                    out[y, x, 3] = 1.0
        return out
