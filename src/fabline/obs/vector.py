"""Fixed-size aggregate vector observation."""

from __future__ import annotations

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import (
    EntityType,
    Item,
    TileType,
    WorldState,
    entity_counts,
    inventory_counts,
    tile_counts,
)

from .base import ObservationSpec

FEATURES = (
    "tick_norm",
    "score_norm",
    "score_last_window_norm",
    "gears_last_window_norm",
    "ingots_last_window_norm",
    "miner_count_norm",
    "belt_count_norm",
    "furnace_count_norm",
    "assembler_count_norm",
    "delivered_gears_norm",
    "delivered_ingots_norm",
    "inventory_ore_norm",
    "inventory_ingot_norm",
    "inventory_gear_norm",
    "ore_tiles_norm",
    "empty_tiles_norm",
    "rock_tiles_norm",
    "blocked_ticks_norm",
)


class VectorObservation:
    """An 18-float aggregate view of the factory."""

    def __init__(self, config: FactoryConfig) -> None:
        self.config = config
        self.spec = ObservationSpec(
            name="vector",
            version="0.1.0",
            shape=(len(FEATURES),),
            feature_names=FEATURES,
        )

    def observe(self, state: WorldState) -> np.ndarray:
        entities = entity_counts(state)
        inventory = inventory_counts(state)
        tiles = tile_counts(state)
        cells = state.width * state.height
        window = state.history
        score_last = sum(
            self.config.depot_ingot_score * ingots + self.config.depot_gear_score * gears
            for _, ingots, gears in window
        )
        gears_last = sum(gears for _, _, gears in window)
        ingots_last = sum(ingots for _, ingots, _ in window)
        blocked = sum(entity.blocked_ticks for entity in state.entities.values())
        blocked_denom = max(1, len(state.entities)) * 100

        values = (
            state.tick / self.config.ticks_per_episode,
            state.score / 1000.0,
            score_last / 1000.0,
            gears_last / 10.0,
            ingots_last / 20.0,
            entities[EntityType.MINER] / self.config.entity_budget,
            entities[EntityType.BELT] / self.config.entity_budget,
            entities[EntityType.FURNACE] / self.config.entity_budget,
            entities[EntityType.ASSEMBLER] / self.config.entity_budget,
            state.delivered[Item.GEAR] / 100.0,
            state.delivered[Item.INGOT] / 100.0,
            inventory[Item.ORE] / 100.0,
            inventory[Item.INGOT] / 100.0,
            inventory[Item.GEAR] / 100.0,
            tiles[TileType.ORE] / cells,
            tiles[TileType.EMPTY] / cells,
            tiles[TileType.ROCK] / cells,
            blocked / blocked_denom,
        )
        return np.asarray(values, dtype=np.float32)

    def feature_index(self, name: str) -> int:
        return FEATURES.index(name)
