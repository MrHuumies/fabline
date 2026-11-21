"""Typed factory configuration and TOML loading."""

from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FactoryConfig:
    """Configuration for the factory MVP.

    Defaults are starting values, not sacred constants. They are chosen to make
    a small line that produces a measurable output within a few hundred ticks.
    """

    width: int = 32
    height: int = 32
    ticks_per_episode: int = 500
    decision_interval: int = 10
    entity_budget: int = 64

    miner_ticks_per_ore: int = 4
    miner_output_capacity: int = 1
    belt_capacity: int = 1

    furnace_ticks: int = 8
    furnace_input_capacity: int = 4
    furnace_output_capacity: int = 2

    assembler_ticks: int = 12
    assembler_ingot_cost: int = 2
    assembler_input_capacity: int = 6
    assembler_output_capacity: int = 2

    depot_ingot_score: int = 2
    depot_gear_score: int = 10

    rock_density: float = 0.06
    ore_patches: int = 4
    ore_patch_radius: int = 1
    starter_line: bool = True

    emit_events: bool = True
    max_events: int = 100_000
    history_window: int = 100

    def __post_init__(self) -> None:
        if self.width < 12 or self.height < 8:
            raise ValueError("world must be at least 12x8 for the starter line")
        if self.ticks_per_episode <= 0:
            raise ValueError("ticks_per_episode must be positive")
        if self.decision_interval <= 0:
            raise ValueError("decision_interval must be positive")
        if self.entity_budget < 8:
            raise ValueError("entity_budget must be at least 8")
        if self.miner_ticks_per_ore <= 0:
            raise ValueError("miner_ticks_per_ore must be positive")
        if self.miner_output_capacity <= 0 or self.belt_capacity <= 0:
            raise ValueError("capacities must be positive")
        if self.furnace_ticks <= 0 or self.assembler_ticks <= 0:
            raise ValueError("craft times must be positive")
        if self.furnace_input_capacity <= 0 or self.furnace_output_capacity <= 0:
            raise ValueError("furnace capacities must be positive")
        if self.assembler_input_capacity <= 0 or self.assembler_output_capacity <= 0:
            raise ValueError("assembler capacities must be positive")
        if self.assembler_ingot_cost <= 0:
            raise ValueError("assembler_ingot_cost must be positive")
        if self.depot_ingot_score < 0 or self.depot_gear_score < 0:
            raise ValueError("depot scores must be non-negative")
        if not 0.0 <= self.rock_density < 1.0:
            raise ValueError("rock_density must be in [0, 1)")
        if self.ore_patches < 1:
            raise ValueError("ore_patches must be at least 1")
        if self.ore_patch_radius < 0:
            raise ValueError("ore_patch_radius must be non-negative")
        if self.history_window <= 0:
            raise ValueError("history_window must be positive")
        if self.max_events <= 0:
            raise ValueError("max_events must be positive")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FactoryConfig:
        allowed = {field.name for field in fields(cls)}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        return cls(**data)

    @classmethod
    def from_toml(cls, path: str | Path) -> FactoryConfig:
        raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(raw)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_config(path: str | Path | None = None) -> FactoryConfig:
    """Load a config from TOML, or return the defaults."""

    if path is None:
        return FactoryConfig()
    return FactoryConfig.from_toml(path)
