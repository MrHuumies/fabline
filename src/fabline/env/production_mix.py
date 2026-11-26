"""Opt-in gear/component production-mix control task."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from fabline.obs.production import ProductionObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.production import ProductionConfig
from fabline.worlds.factory.state import Item
from fabline.worlds.factory.world import FactoryWorld

PRODUCTION_MIX_TASK_ID = "factory.production.mix.v1"
PRODUCTION_MIX_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class ProductionMixConfig:
    episode_ticks: int = 300
    decision_interval: int = 10
    success_score: int = 200
    production: ProductionConfig = ProductionConfig(enabled=True)

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode ticks and decision interval must be positive")
        if self.success_score < 0:
            raise ValueError("success score must be non-negative")
        if not self.production.enabled:
            raise ValueError("production mix requires production.enabled")


class ProductionMixEnv:
    """Choose gear or component at each decision boundary."""

    n_actions = 2
    ACTION_NAMES = ("gear", "component")

    def __init__(
        self,
        config: FactoryConfig,
        mix: ProductionMixConfig | None = None,
    ) -> None:
        self.config = config
        self.mix = mix or ProductionMixConfig()
        if self.mix.episode_ticks != self.config.ticks_per_episode:
            raise ValueError(
                "mix.episode_ticks must equal config.ticks_per_episode"
            )
        self.world = FactoryWorld(
            config, production=self.mix.production
        )
        self.observation = ProductionObservation(config)
        self.reset(0)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed, SCENARIOS["gear"])
        self.world.state.production_recipe = 0
        self.total_reward = 0.0
        self.switches = 0
        self.steps = 0
        self.last_action = "gear"
        self.last_reward = 0.0
        return self.observation.observe(self.world.state), self._info()

    def action_mask(self) -> np.ndarray:
        return np.asarray([True, True], dtype=bool)

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        previous = self.world.state.production_recipe
        self.world.state.production_recipe = action
        if previous != action:
            self.switches += 1
        score_before = self.world.state.score
        self.world.run_ticks(self.mix.decision_interval)
        reward = float(self.world.state.score - score_before)
        self.total_reward += reward
        self.steps += 1
        self.last_action = self.ACTION_NAMES[action]
        self.last_reward = reward
        info = self._info()
        return (
            self.observation.observe(self.world.state),
            reward,
            self.world.done,
            False,
            info,
        )

    def _info(self) -> dict[str, Any]:
        state = self.world.state
        return {
            "tick": state.tick,
            "score": state.score,
            "gear": state.delivered.get(Item.GEAR, 0),
            "component": state.delivered.get(Item.COMPONENT, 0),
            "production_recipe": state.production_recipe,
            "switches": self.switches,
            "success": state.score >= self.mix.success_score,
            "total_reward": self.total_reward,
            "last_action": self.last_action,
            "last_reward": self.last_reward,
        }
