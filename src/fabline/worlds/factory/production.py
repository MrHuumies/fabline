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
    assembly_enabled: bool = False
    assembly_ticks: int = 16
    assembly_ingot_cost: int = 1
    assembly_component_cost: int = 1
    assembly_score: int = 10

    def __post_init__(self) -> None:
        if self.component_ticks <= 0:
            raise ValueError("component_ticks must be positive")
        if self.component_ingot_cost <= 0:
            raise ValueError("component_ingot_cost must be positive")
        if self.component_score < 0:
            raise ValueError("component_score must be non-negative")
        if self.assembly_ticks <= 0:
            raise ValueError("assembly_ticks must be positive")
        if self.assembly_ingot_cost <= 0:
            raise ValueError("assembly_ingot_cost must be positive")
        if self.assembly_component_cost <= 0:
            raise ValueError("assembly_component_cost must be positive")
        if self.assembly_score < 0:
            raise ValueError("assembly_score must be non-negative")
        if self.assembly_enabled and not self.enabled:
            raise ValueError("assembly requires production.enabled")
