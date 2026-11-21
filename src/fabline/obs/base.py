"""Observation adapter protocol and shared helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import EntityType, WorldState


@dataclass(frozen=True)
class ObservationSpec:
    name: str
    version: str
    shape: tuple[int, ...] | None
    dtype: str = "float32"
    normalized: bool = True
    feature_names: tuple[str, ...] | None = None
    format: str = "tensor"


class ObservationAdapter(Protocol):
    spec: ObservationSpec

    def observe(self, state: WorldState) -> Any: ...


def flatten_observation(adapter: ObservationAdapter, observation: Any) -> np.ndarray:
    """Flatten any adapter output into a 1-D float32 vector for tabular models."""

    flatten = getattr(adapter, "flatten", None)
    if flatten is not None:
        return np.asarray(flatten(observation), dtype=np.float32)
    return np.asarray(observation, dtype=np.float32).reshape(-1)


def input_capacity(config: FactoryConfig, entity_type: EntityType) -> int:
    if entity_type is EntityType.FURNACE:
        return config.furnace_input_capacity
    if entity_type is EntityType.ASSEMBLER:
        return config.assembler_input_capacity
    return 0


def output_capacity(config: FactoryConfig, entity_type: EntityType) -> int:
    if entity_type is EntityType.MINER:
        return config.miner_output_capacity
    if entity_type is EntityType.BELT:
        return config.belt_capacity
    if entity_type is EntityType.FURNACE:
        return config.furnace_output_capacity
    if entity_type is EntityType.ASSEMBLER:
        return config.assembler_output_capacity
    return 0


def craft_ticks(config: FactoryConfig, entity_type: EntityType) -> int:
    if entity_type is EntityType.FURNACE:
        return config.furnace_ticks
    if entity_type is EntityType.ASSEMBLER:
        return config.assembler_ticks
    return 0


def build_observation(
    name: str,
    config: FactoryConfig,
    faults: FaultConfig | None = None,
    power: PowerConfig | None = None,
) -> ObservationAdapter:
    """Construct a built-in observation adapter by name.

    Fault-aware and power-aware adapters receive the opt-in configs.
    """

    if name == "grid":
        from .grid import GridObservation

        return GridObservation(config)
    if name == "vector":
        from .vector import VectorObservation

        return VectorObservation(config)
    if name == "entities":
        from .entities import EntitiesObservation

        return EntitiesObservation(config)
    if name == "line_state":
        from .line import LineStateObservation

        return LineStateObservation(config)
    if name == "grid_fog":
        from .grid import GridObservation
        from .partial import GridFogObservation

        return GridFogObservation(GridObservation(config), radius=3)
    if name == "vector_dropout":
        from .partial import FeatureDropoutObservation
        from .vector import VectorObservation

        return FeatureDropoutObservation(VectorObservation(config), dropout=0.2)
    if name in ("power", "power_grid", "power_control"):
        from .power import (
            PowerControlObservation,
            PowerGridObservation,
            PowerObservation,
        )

        power_config = power or PowerConfig()
        if name == "power":
            return PowerObservation(config, power_config)
        if name == "power_control":
            return PowerControlObservation(config, power_config)
        return PowerGridObservation(config, power_config)
    if name == "fault_power":
        from .interaction import FaultPowerObservation

        return FaultPowerObservation(
            config,
            faults or FaultConfig(),
            power or PowerConfig(),
        )
    if name in ("sensors", "diagnostics", "entity_sensors_top4"):
        from .sensors import (
            DiagnosticsObservation,
            SensorsObservation,
            TopKEntitySensorsObservation,
        )

        fault_config = faults or FaultConfig()
        if name == "sensors":
            return SensorsObservation(config, fault_config)
        if name == "entity_sensors_top4":
            return TopKEntitySensorsObservation(config, fault_config)
        return DiagnosticsObservation(config, fault_config)
    raise ValueError(f"unknown observation adapter: {name}")
