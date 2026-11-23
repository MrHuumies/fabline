"""Opt-in assembler recipe-choice task.

The agent chooses between a fast/expensive recipe and a slow/cheap recipe. Both
produce gears; the trade-off depends on the ingot queue. The frozen default
world keeps the original recipe and is unchanged.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.obs.vector import FEATURES, VectorObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.recipe import RecipeConfig
from fabline.worlds.factory.state import Entity, EntityType, Item
from fabline.worlds.factory.world import FactoryWorld

RECIPE_TASK_ID = "factory.production.recipe-choice.v1"
RECIPE_TASK_VERSION = "0.1.0"

RECIPE_FEATURES = (
    *FEATURES,
    "recipe_fast",
    "recipe_slow",
    "assembler_input_norm",
    "assembler_output_norm",
)


@dataclass(frozen=True)
class RecipeEnvConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    scenario: str = "gear"
    success_score: int = 150
    initial_input_max: int = 6
    recipe: RecipeConfig = field(default_factory=RecipeConfig)

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode ticks and decision interval must be positive")
        if self.scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario: {self.scenario}")
        if self.success_score < 0:
            raise ValueError("success score must be non-negative")
        if not self.recipe.enabled:
            raise ValueError("recipe env requires an enabled RecipeConfig")
        if self.initial_input_max < 0:
            raise ValueError("initial input max must be non-negative")


class RecipeEnv:
    """Choose fast or slow assembler recipe at each decision interval."""

    n_actions = 2
    ACTION_NAMES = ("fast", "slow")

    def __init__(
        self,
        config: FactoryConfig,
        recipe: RecipeEnvConfig | None = None,
    ) -> None:
        self.config = config
        self.recipe = recipe or RecipeEnvConfig()
        if config.ticks_per_episode != self.recipe.episode_ticks:
            raise ValueError("recipe episode ticks must match config")
        self.vector = VectorObservation(config)
        self.world = FactoryWorld(config, recipe=self.recipe.recipe)
        self.reset(0)

    def _assembler(self) -> Entity:
        for entity in self.world.state.entities.values():
            if entity.type is EntityType.ASSEMBLER:
                return entity
        raise RuntimeError("recipe task requires an assembler")

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed, SCENARIOS[self.recipe.scenario])
        self.world.state.recipe_index = 0
        rng = random.Random(seed * 104729 + 19)
        initial = rng.randint(
            0,
            min(
                self.recipe.initial_input_max,
                self.config.assembler_input_capacity,
            ),
        )
        self._assembler().input_buffer[Item.INGOT] = initial
        self.score_start = self.world.state.score
        self.steps = 0
        self.switches = 0
        self.last_action = 0
        self.initial_input = initial
        return self._observation(), self._info()

    def action_mask(self) -> np.ndarray:
        return np.ones(self.n_actions, dtype=bool)

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        if action != self.world.state.recipe_index:
            self.switches += 1
        self.world.state.recipe_index = action
        self.last_action = action
        before = self.world.state.score
        self.world.run_ticks(self.recipe.decision_interval)
        reward = float(self.world.state.score - before)
        self.steps += 1
        info = self._info()
        info["reward"] = reward
        return self._observation(), reward, self.world.done, False, info

    def _observation(self) -> np.ndarray:
        assembler = self._assembler()
        base = self.vector.observe(self.world.state)
        extra = np.asarray(
            [
                1.0 if self.world.state.recipe_index == 0 else 0.0,
                1.0 if self.world.state.recipe_index == 1 else 0.0,
                assembler.total_input()
                / max(1, self.config.assembler_input_capacity),
                assembler.total_output()
                / max(1, self.config.assembler_output_capacity),
            ],
            dtype=np.float32,
        )
        return np.concatenate([base, extra])

    def _info(self) -> dict[str, Any]:
        assembler = self._assembler()
        return {
            "score": self.world.state.score,
            "tick": self.world.state.tick,
            "recipe": self.world.state.recipe_index,
            "recipe_name": self.ACTION_NAMES[self.world.state.recipe_index],
            "delivered_gears": self.world.state.delivered.get(Item.GEAR, 0),
            "assembler_input": assembler.total_input(),
            "initial_input": self.initial_input,
            "assembler_output": assembler.total_output(),
            "switches": self.switches,
            "steps": self.steps,
            "last_action": self.last_action,
            "success": self.world.state.score >= self.recipe.success_score,
        }
