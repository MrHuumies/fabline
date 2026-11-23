"""Opt-in assembler recipe settings.

Kept outside ``FactoryConfig`` so the frozen `factory-v0.1` config hash and
state hash remain unchanged. A world without a ``RecipeConfig`` uses the
original 2-ingot/12-tick gear recipe.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecipeConfig:
    enabled: bool = False
    fast_ticks: int = 12
    fast_cost: int = 2
    slow_ticks: int = 20
    slow_cost: int = 1
    byproduct_enabled: bool = False
    byproduct_per_slow: int = 1
    byproduct_capacity: int = 2

    def __post_init__(self) -> None:
        if self.fast_ticks <= 0 or self.slow_ticks <= 0:
            raise ValueError("recipe craft times must be positive")
        if self.fast_cost <= 0 or self.slow_cost <= 0:
            raise ValueError("recipe ingot costs must be positive")
        if self.byproduct_enabled:
            if self.byproduct_per_slow <= 0:
                raise ValueError("byproduct per slow craft must be positive")
            if self.byproduct_capacity <= 0:
                raise ValueError("byproduct capacity must be positive")
