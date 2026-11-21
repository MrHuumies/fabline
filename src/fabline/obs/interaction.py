"""Fault + power interaction observation."""

from __future__ import annotations

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import EntityType, WorldState

from .base import ObservationSpec
from .line import LineStateObservation
from .power import PowerObservation

FAULT_POWER_FEATURES = (
    "faulted_ratio",
    "mean_wear",
    "max_wear",
    "furnace_faulted",
    "assembler_faulted",
    "mean_repair_progress",
)


class FaultPowerObservation:
    """Power view + line buffers + aggregate fault state (24 features)."""

    def __init__(
        self,
        config: FactoryConfig,
        faults: FaultConfig,
        power: PowerConfig,
    ) -> None:
        self.config = config
        self.faults = faults
        self.power = power
        self.power_view = PowerObservation(config, power)
        self.line_view = LineStateObservation(config)
        self.spec = ObservationSpec(
            name="fault_power",
            version="0.1.0",
            shape=(12 + 6 + 6,),
            feature_names=(
                *(self.power_view.spec.feature_names or ()),
                *(self.line_view.spec.feature_names or ()),
                *FAULT_POWER_FEATURES,
            ),
        )

    def observe(self, state: WorldState) -> np.ndarray:
        entities = [
            entity
            for entity in state.entities.values()
            if entity.type is not EntityType.DEPOT
        ]
        count = max(1, len(entities))
        faulted = [entity for entity in entities if entity.faulted]
        threshold = max(1, self.faults.fault_threshold)
        repair_ticks = max(1, self.faults.repair_ticks)
        wears = [entity.wear / threshold for entity in entities]
        furnace = next(
            (
                entity
                for entity in entities
                if entity.type is EntityType.FURNACE
            ),
            None,
        )
        assembler = next(
            (
                entity
                for entity in entities
                if entity.type is EntityType.ASSEMBLER
            ),
            None,
        )
        fault_features = np.asarray(
            [
                len(faulted) / count,
                float(np.mean(wears)) if wears else 0.0,
                float(np.max(wears)) if wears else 0.0,
                1.0 if furnace is not None and furnace.faulted else 0.0,
                1.0 if assembler is not None and assembler.faulted else 0.0,
                (
                    float(
                        np.mean(
                            [
                                entity.repair_progress / repair_ticks
                                for entity in faulted
                            ]
                        )
                    )
                    if faulted
                    else 0.0
                ),
            ],
            dtype=np.float32,
        )
        return np.concatenate(
            [
                self.power_view.observe(state),
                self.line_view.observe(state),
                fault_features,
            ]
        ).astype(np.float32)
