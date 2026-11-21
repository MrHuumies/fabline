"""Opt-in power grid configuration.

Power is deliberately separate from ``FactoryConfig`` so the frozen
``factory-v0.1`` benchmark and its config hash stay unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .state import Entity, EntityType


@dataclass(frozen=True)
class PowerConfig:
    enabled: bool = False
    generator_count: int = 2
    generator_capacity: int = 12
    generator_radius: int = 6
    miner_demand: int = 2
    belt_demand: int = 1
    furnace_demand: int = 3
    assembler_demand: int = 4
    depot_demand: int = 0
    load_jitter: int = 0
    capacity_jitter: int = 0
    variation_period: int = 20

    def __post_init__(self) -> None:
        if self.generator_count <= 0:
            raise ValueError("generator_count must be positive")
        if self.generator_capacity <= 0:
            raise ValueError("generator_capacity must be positive")
        if self.generator_radius < 0:
            raise ValueError("generator_radius must be non-negative")
        for name in (
            "miner_demand",
            "belt_demand",
            "furnace_demand",
            "assembler_demand",
            "depot_demand",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if not 0 <= self.load_jitter <= 100:
            raise ValueError("load_jitter must be in [0, 100]")
        if not 0 <= self.capacity_jitter <= 100:
            raise ValueError("capacity_jitter must be in [0, 100]")
        if self.variation_period <= 0:
            raise ValueError("variation_period must be positive")

    def demand(self, entity_type: EntityType) -> int:
        if entity_type is EntityType.MINER:
            return self.miner_demand
        if entity_type is EntityType.BELT:
            return self.belt_demand
        if entity_type is EntityType.FURNACE:
            return self.furnace_demand
        if entity_type is EntityType.ASSEMBLER:
            return self.assembler_demand
        return self.depot_demand

    def active_demand(self, entity: Entity) -> int:
        """Rated demand while the entity is doing work, else zero.

        Miners draw continuously. Belts draw while carrying an item.
        Furnaces and assemblers draw while a craft is in progress. Idle
        machines are treated as ready; their demand appears when they start.
        """

        rated = self.demand(entity.type)
        if rated == 0:
            return 0
        if entity.type is EntityType.BELT:
            return rated if entity.output_buffer else 0
        if entity.type in (EntityType.FURNACE, EntityType.ASSEMBLER):
            return rated if entity.craft_progress > 0 else 0
        return rated

    def scaled_demand(self, entity: Entity, load_factor: int) -> int:
        demand = self.active_demand(entity)
        if demand <= 0:
            return 0
        return max(1, demand * load_factor // 100)

    def max_demand(self) -> int:
        return max(
            self.miner_demand,
            self.belt_demand,
            self.furnace_demand,
            self.assembler_demand,
            self.depot_demand,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PowerConfig:
        return cls(**data)
