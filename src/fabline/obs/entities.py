"""Entity/graph observation.

The raw view is a padded entity feature matrix, an entity mask, and an
adjacency matrix over the factory's push edges. Tabular baselines use
``flatten``; a GNN can consume the three arrays directly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import EntityType, WorldState

from .base import ObservationSpec, craft_ticks

ENTITY_FEATURES = (
    "type_miner",
    "type_belt",
    "type_furnace",
    "type_assembler",
    "type_depot",
    "x_norm",
    "y_norm",
    "dir_north",
    "dir_east",
    "dir_south",
    "dir_west",
    "input_total_norm",
    "output_total_norm",
    "craft_progress_norm",
    "blocked_norm",
    "built_tick_norm",
)

TYPE_ORDER = (
    EntityType.MINER,
    EntityType.BELT,
    EntityType.FURNACE,
    EntityType.ASSEMBLER,
    EntityType.DEPOT,
)


@dataclass(frozen=True)
class GraphObservation:
    entity_features: np.ndarray
    entity_mask: np.ndarray
    adjacency: np.ndarray
    feature_names: tuple[str, ...]

    def flatten(self) -> np.ndarray:
        return np.concatenate(
            [
                self.entity_features.reshape(-1),
                self.entity_mask.astype(np.float32),
                self.adjacency.reshape(-1),
            ]
        ).astype(np.float32)


class EntitiesObservation:
    """A padded entity graph with a fixed maximum size."""

    def __init__(self, config: FactoryConfig) -> None:
        self.config = config
        self.max_entities = min(config.entity_budget, 32)
        self.spec = ObservationSpec(
            name="entities",
            version="0.1.0",
            shape=None,
            feature_names=ENTITY_FEATURES,
            format="graph",
        )

    def observe(self, state: WorldState) -> GraphObservation:
        size = self.max_entities
        features = np.zeros((size, len(ENTITY_FEATURES)), dtype=np.float32)
        mask = np.zeros(size, dtype=bool)
        adjacency = np.zeros((size, size), dtype=np.float32)

        entities = sorted(state.entities.values(), key=lambda entity: entity.id)[:size]
        index_by_id = {entity.id: index for index, entity in enumerate(entities)}

        for index, entity in enumerate(entities):
            mask[index] = True
            features[index, int(entity.type) - 1] = 1.0
            features[index, 5] = entity.x / max(1, state.width - 1)
            features[index, 6] = entity.y / max(1, state.height - 1)
            features[index, 7 + int(entity.direction)] = 1.0
            features[index, 11] = entity.total_input() / 10.0
            features[index, 12] = entity.total_output() / 10.0
            ticks = craft_ticks(self.config, entity.type)
            if ticks:
                features[index, 13] = entity.craft_progress / ticks
            features[index, 14] = entity.blocked_ticks / 100.0
            features[index, 15] = entity.built_tick / max(1, state.tick)

            dx, dy = entity.direction.delta
            target = state.occupancy.get((entity.x + dx, entity.y + dy))
            if target is not None and target in index_by_id:
                adjacency[index, index_by_id[target]] = 1.0

        return GraphObservation(
            entity_features=features,
            entity_mask=mask,
            adjacency=adjacency,
            feature_names=ENTITY_FEATURES,
        )

    def flatten(self, observation: GraphObservation) -> np.ndarray:
        return observation.flatten()
