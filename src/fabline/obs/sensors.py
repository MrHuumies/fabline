"""Diagnostic sensor views for the opt-in fault mechanic."""

from __future__ import annotations

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.state import Entity, EntityType, WorldState

from .base import ObservationSpec

SENSOR_CHANNELS = ("wear", "temperature", "vibration", "acoustic", "faulted")

TOP_K_ENTITY_SENSORS = 4

TOP_K_ENTITY_FEATURES = (
    "mask",
    "acoustic",
    "vibration",
    "temperature",
    "wear",
    "faulted",
    "crafting",
    "type_norm",
)

DIAGNOSTIC_FEATURES = (
    "tick_norm",
    "score_norm",
    "faulted_count_norm",
    "mean_wear",
    "max_wear",
    "mean_temperature",
    "max_temperature",
    "mean_vibration",
    "max_vibration",
    "mean_acoustic",
    "max_acoustic",
    "machine_count_norm",
    "blocked_norm",
)


def entity_sensors(
    entity: Entity,
    faults: FaultConfig,
) -> tuple[float, float, float, float, float]:
    if not faults.enabled:
        return (0.0, 0.0, 0.0, 0.0, 0.0)
    threshold = max(1, faults.fault_threshold)
    wear = min(1.0, entity.wear / threshold)
    faulted = 1.0 if entity.faulted else 0.0
    return (
        wear,
        entity.temperature / 100.0,
        entity.vibration / 100.0,
        entity.acoustic / 100.0,
        faulted,
    )


class SensorsObservation:
    """A `(H, W, 5)` diagnostic field over entity tiles."""

    def __init__(self, config: FactoryConfig, faults: FaultConfig) -> None:
        self.config = config
        self.faults = faults
        self.shape = (config.height, config.width, len(SENSOR_CHANNELS))
        self.spec = ObservationSpec(
            name="sensors",
            version="0.2.0",
            shape=self.shape,
            feature_names=SENSOR_CHANNELS,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        out = np.zeros(self.shape, dtype=np.float32)
        for entity in state.entities.values():
            out[entity.y, entity.x, :] = entity_sensors(entity, self.faults)
        return out


class TopKEntitySensorsObservation:
    """A `(k, 8)` view of the top-k machines by acoustic level.

    The aggregate diagnostics reduce every machine to a mean and a max. This
    view keeps the loudest machines and their joint sensor state, so a model can
    see which machine spiked and whether its vibration, temperature, wear, and
    fault state moved with it.
    """

    def __init__(
        self,
        config: FactoryConfig,
        faults: FaultConfig,
        top_k: int = TOP_K_ENTITY_SENSORS,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        self.config = config
        self.faults = faults
        self.top_k = top_k
        self.shape = (top_k, len(TOP_K_ENTITY_FEATURES))
        self.spec = ObservationSpec(
            name=f"entity_sensors_top{top_k}",
            version="0.1.0",
            shape=self.shape,
            feature_names=tuple(
                f"{name}_{index}"
                for index in range(top_k)
                for name in TOP_K_ENTITY_FEATURES
            ),
        )

    def observe(self, state: WorldState) -> np.ndarray:
        out = np.zeros(self.shape, dtype=np.float32)
        if not self.faults.enabled:
            return out
        threshold = max(1, self.faults.fault_threshold)
        entities = sorted(
            state.entities.values(),
            key=lambda entity: (-entity.acoustic, entity.id),
        )[: self.top_k]
        for index, entity in enumerate(entities):
            out[index, 0] = 1.0
            out[index, 1] = entity.acoustic / 100.0
            out[index, 2] = entity.vibration / 100.0
            out[index, 3] = entity.temperature / 100.0
            out[index, 4] = min(1.0, entity.wear / threshold)
            out[index, 5] = 1.0 if entity.faulted else 0.0
            out[index, 6] = 1.0 if entity.craft_progress > 0 else 0.0
            out[index, 7] = int(entity.type) / len(EntityType)
        return out

    def flatten(self, observation: np.ndarray) -> np.ndarray:
        return observation.reshape(-1)


class DiagnosticsObservation:
    """Aggregate fault diagnostics for tabular models."""

    def __init__(self, config: FactoryConfig, faults: FaultConfig) -> None:
        self.config = config
        self.faults = faults
        self.spec = ObservationSpec(
            name="diagnostics",
            version="0.2.0",
            shape=(len(DIAGNOSTIC_FEATURES),),
            feature_names=DIAGNOSTIC_FEATURES,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        sensors = [
            entity_sensors(entity, self.faults)
            for entity in state.entities.values()
        ]
        count = max(1, len(sensors))
        wear = [values[0] for values in sensors]
        temperature = [values[1] for values in sensors]
        vibration = [values[2] for values in sensors]
        acoustic = [values[3] for values in sensors]
        faulted = [values[4] for values in sensors]
        machines = sum(
            1
            for entity in state.entities.values()
            if entity.type in (EntityType.MINER, EntityType.FURNACE, EntityType.ASSEMBLER)
        )
        blocked = sum(entity.blocked_ticks for entity in state.entities.values())
        values = (
            state.tick / self.config.ticks_per_episode,
            state.score / 1000.0,
            sum(faulted) / count,
            sum(wear) / count,
            max(wear, default=0.0),
            sum(temperature) / count,
            max(temperature, default=0.0),
            sum(vibration) / count,
            max(vibration, default=0.0),
            sum(acoustic) / count,
            max(acoustic, default=0.0),
            machines / self.config.entity_budget,
            blocked / (count * 100),
        )
        return np.asarray(values, dtype=np.float32)
