"""Production-mix task observation."""

from __future__ import annotations

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import (
    EntityType,
    Item,
    WorldState,
    inventory_counts,
)

from .base import ObservationSpec

PRODUCTION_FEATURES = (
    "tick_norm",
    "score_norm",
    "delivered_gear_norm",
    "delivered_component_norm",
    "inventory_ingot_norm",
    "inventory_component_norm",
    "production_recipe",
    "assembler_craft_norm",
    "blocked_norm",
)


class ProductionObservation:
    """Small view for the opt-in gear/component production mix."""

    def __init__(self, config: FactoryConfig) -> None:
        self.config = config
        self.spec = ObservationSpec(
            name="production",
            version="0.1.0",
            shape=(len(PRODUCTION_FEATURES),),
            feature_names=PRODUCTION_FEATURES,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        inventory = inventory_counts(state)
        assembler_progress = max(
            (
                entity.craft_progress
                for entity in state.entities.values()
                if entity.type is EntityType.ASSEMBLER
            ),
            default=0,
        )
        blocked = sum(
            entity.blocked_ticks for entity in state.entities.values()
        )
        values = (
            state.tick / self.config.ticks_per_episode,
            state.score / 1000.0,
            state.delivered.get(Item.GEAR, 0) / 100.0,
            state.delivered.get(Item.COMPONENT, 0) / 100.0,
            inventory.get(Item.INGOT, 0) / 100.0,
            inventory.get(Item.COMPONENT, 0) / 100.0,
            float(state.production_recipe),
            assembler_progress / max(1, self.config.assembler_ticks),
            blocked / (max(1, len(state.entities)) * 100),
        )
        return np.asarray(values, dtype=np.float32)
