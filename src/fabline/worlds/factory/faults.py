"""Opt-in machine wear and fault configuration.

Faults are deliberately separate from FactoryConfig so the frozen
`factory-v0.1` benchmark and its config hash stay unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FaultConfig:
    enabled: bool = False
    wear_per_craft: int = 1
    miner_wear_per_ore: int = 0
    fault_threshold: int = 20
    repair_ticks: int = 30

    def __post_init__(self) -> None:
        if self.wear_per_craft < 0 or self.miner_wear_per_ore < 0:
            raise ValueError("wear rates must be non-negative")
        if self.fault_threshold <= 0:
            raise ValueError("fault_threshold must be positive")
        if self.repair_ticks <= 0:
            raise ValueError("repair_ticks must be positive")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FaultConfig:
        return cls(**data)
