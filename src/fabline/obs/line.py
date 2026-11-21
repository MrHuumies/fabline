"""Line-buffer observation for production and allocation tasks."""

from __future__ import annotations

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import Entity, EntityType, WorldState

from .base import ObservationSpec, craft_ticks, input_capacity, output_capacity

LINE_STATE_FEATURES = (
    "assembler_input_norm",
    "furnace_output_norm",
    "assembler_craft_norm",
    "furnace_craft_norm",
    "miner_output_norm",
    "belts_carrying_norm",
)


class LineStateObservation:
    """A 6-feature view of the gear line's buffers and craft progress."""

    def __init__(self, config: FactoryConfig) -> None:
        self.config = config
        self.spec = ObservationSpec(
            name="line_state",
            version="0.1.0",
            shape=(len(LINE_STATE_FEATURES),),
            feature_names=LINE_STATE_FEATURES,
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
        assembler = self._entity(state, EntityType.ASSEMBLER)
        furnace = self._entity(state, EntityType.FURNACE)
        miner = self._entity(state, EntityType.MINER)
        belts = [
            entity
            for entity in state.entities.values()
            if entity.type is EntityType.BELT
        ]
        carrying = sum(1 for entity in belts if entity.output_buffer)
        values = (
            (
                assembler.total_input()
                / max(1, input_capacity(self.config, EntityType.ASSEMBLER))
                if assembler
                else 0.0
            ),
            (
                furnace.total_output()
                / max(1, output_capacity(self.config, EntityType.FURNACE))
                if furnace
                else 0.0
            ),
            (
                assembler.craft_progress
                / max(1, craft_ticks(self.config, EntityType.ASSEMBLER))
                if assembler
                else 0.0
            ),
            (
                furnace.craft_progress
                / max(1, craft_ticks(self.config, EntityType.FURNACE))
                if furnace
                else 0.0
            ),
            (
                miner.total_output()
                / max(1, output_capacity(self.config, EntityType.MINER))
                if miner
                else 0.0
            ),
            carrying / len(belts) if belts else 0.0,
        )
        return np.asarray(values, dtype=np.float32)
