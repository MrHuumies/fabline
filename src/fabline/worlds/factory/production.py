"""Opt-in multi-item production settings.

The default factory remains a single gear recipe. Enabling this config adds a
component deliverable and a recipe-switch control surface without changing the
frozen default state.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionConfig:
    enabled: bool = False
    component_ticks: int = 8
    component_ingot_cost: int = 1
    component_score: int = 6

    def __post_init__(self) -> None:
        if self.component_ticks <= 0:
            raise ValueError("component_ticks must be positive")
        if self.component_ingot_cost <= 0:
            raise ValueError("component_ingot_cost must be positive")
        if self.component_score < 0:
            raise ValueError("component_score must be non-negative")
