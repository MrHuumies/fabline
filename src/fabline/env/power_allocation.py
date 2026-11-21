"""Power-allocation control on a fixed gear line."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.obs.power import PowerControlObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import Entity, EntityType
from fabline.worlds.factory.world import FactoryWorld

POWER_ALLOCATION_TASK_ID = "factory.power.allocate.v1"
POWER_ALLOCATION_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class PowerAllocationConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    success_score: int = 100
    power: PowerConfig = field(
        default_factory=lambda: PowerConfig(
            enabled=True,
            generator_count=1,
            generator_capacity=5,
            generator_radius=8,
        )
    )

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode_ticks and decision_interval must be positive")
        if self.success_score < 0:
            raise ValueError("success_score must be non-negative")
        if not self.power.enabled:
            raise ValueError("power allocation requires power.enabled")


class PowerAllocationEnv:
    """Choose a power priority each decision interval.

    Capacity is too small to run the furnace and assembler together, so the
    agent must build ingot buffers and alternate priorities.
    """

    n_actions = 3
    ACTION_NAMES = ("default", "favor_furnace", "favor_assembler")

    def __init__(
        self,
        config: FactoryConfig,
        allocation: PowerAllocationConfig | None = None,
    ) -> None:
        self.config = config
        self.allocation = allocation or PowerAllocationConfig()
        if self.allocation.episode_ticks != config.ticks_per_episode:
            raise ValueError(
                "allocation.episode_ticks must equal config.ticks_per_episode"
            )
        if not self.allocation.power.enabled:
            raise ValueError("power allocation requires power.enabled")
        self.world = FactoryWorld(config, power=self.allocation.power)
        self.observation = PowerControlObservation(
            config, self.allocation.power
        )
        self.reset(0)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed, SCENARIOS["gear"])
        self.world.state.power_priority = 0
        self.total_reward = 0.0
        self.steps = 0
        self.last_action = "default"
        self.last_reward = 0.0
        return self._observation(), self._info()

    def action_mask(self) -> np.ndarray:
        return np.ones(self.n_actions, dtype=bool)

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        score_before = self.world.state.score
        self.world.state.power_priority = action
        self.world.run_ticks(self.allocation.decision_interval)
        score_after = self.world.state.score
        reward = float(score_after - score_before)
        self.total_reward += reward
        self.steps += 1
        self.last_action = self.ACTION_NAMES[action]
        self.last_reward = reward
        info = self._info()
        info["last_action"] = self.last_action
        info["last_reward"] = self.last_reward
        return self._observation(), reward, self.world.done, False, info

    def _entity(self, entity_type: EntityType) -> Entity | None:
        return next(
            (
                entity
                for entity in self.world.state.entities.values()
                if entity.type is entity_type
            ),
            None,
        )

    def _observation(self) -> np.ndarray:
        return self.observation.observe(self.world.state)

    def _info(self) -> dict[str, Any]:
        assembler = self._entity(EntityType.ASSEMBLER)
        furnace = self._entity(EntityType.FURNACE)
        miner = self._entity(EntityType.MINER)
        return {
            "score": self.world.state.score,
            "tick": self.world.state.tick,
            "priority": self.world.state.power_priority,
            "assembler_input": (
                assembler.total_input() if assembler else 0
            ),
            "assembler_craft": (
                assembler.craft_progress if assembler else 0
            ),
            "furnace_output": furnace.total_output() if furnace else 0,
            "furnace_craft": furnace.craft_progress if furnace else 0,
            "miner_output": miner.total_output() if miner else 0,
            "assembler_powered": bool(assembler and assembler.powered),
            "furnace_powered": bool(furnace and furnace.powered),
            "total_reward": self.total_reward,
            "success": (
                self.world.state.score >= self.allocation.success_score
            ),
        }
