"""Fault + power interaction control on a gear line."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.obs.interaction import FaultPowerObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import Entity, EntityType
from fabline.worlds.factory.world import FactoryWorld

FAULT_POWER_TASK_ID = "factory.fault_power.control.v1"
FAULT_POWER_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class FaultPowerConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    repair_cost: float = 1.0
    success_score: int = 100
    faults: FaultConfig = field(
        default_factory=lambda: FaultConfig(
            enabled=True,
            wear_per_craft=1,
            fault_threshold=5,
            repair_ticks=10,
        )
    )
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
        if self.repair_cost < 0:
            raise ValueError("repair_cost must be non-negative")
        if self.success_score < 0:
            raise ValueError("success_score must be non-negative")
        if not self.faults.enabled or not self.power.enabled:
            raise ValueError("fault power control requires faults and power")


class FaultPowerEnv:
    """Choose a power priority or repair a faulted machine."""

    n_actions = 4
    ACTION_NAMES = ("noop", "favor_furnace", "favor_assembler", "repair")

    def __init__(
        self,
        config: FactoryConfig,
        interaction: FaultPowerConfig | None = None,
    ) -> None:
        self.config = config
        self.interaction = interaction or FaultPowerConfig()
        if self.interaction.episode_ticks != config.ticks_per_episode:
            raise ValueError(
                "interaction.episode_ticks must equal config.ticks_per_episode"
            )
        self.world = FactoryWorld(
            config,
            self.interaction.faults,
            self.interaction.power,
        )
        self.observation = FaultPowerObservation(
            config,
            self.interaction.faults,
            self.interaction.power,
        )
        self.reset(0)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed, SCENARIOS["gear"])
        self.world.state.power_priority = 0
        self.total_reward = 0.0
        self.repairs = 0
        self.steps = 0
        self.last_action = "noop"
        self.last_reward = 0.0
        return self._observation(), self._info()

    def _faulted(self) -> list[Entity]:
        return sorted(
            (
                entity
                for entity in self.world.state.entities.values()
                if entity.faulted
            ),
            key=lambda entity: entity.id,
        )

    def action_mask(self) -> np.ndarray:
        return np.asarray(
            [True, True, True, bool(self._faulted())],
            dtype=bool,
        )

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        mask = self.action_mask()
        legal = bool(mask[action])
        faulted = self._faulted()
        score_before = self.world.state.score
        repair_cost = 0.0
        if action == 3 and legal:
            self.world.repair_entity(faulted[0])
            self.repairs += 1
            repair_cost = self.interaction.repair_cost
        elif action in (0, 1, 2):
            self.world.state.power_priority = action

        self.world.run_ticks(self.interaction.decision_interval)
        score_after = self.world.state.score
        reward = float(score_after - score_before) - repair_cost
        self.total_reward += reward
        self.steps += 1
        self.last_action = self.ACTION_NAMES[action]
        self.last_reward = reward
        info = self._info()
        info["illegal"] = not legal
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
        faulted = self._faulted()
        threshold = max(1, self.interaction.faults.fault_threshold)
        repair_ticks = max(1, self.interaction.faults.repair_ticks)
        return {
            "score": self.world.state.score,
            "tick": self.world.state.tick,
            "priority": self.world.state.power_priority,
            "faulted_count": len(faulted),
            "faulted_furnace": any(
                entity.type is EntityType.FURNACE for entity in faulted
            ),
            "faulted_assembler": any(
                entity.type is EntityType.ASSEMBLER for entity in faulted
            ),
            "repair_progress": (
                max(
                    entity.repair_progress / repair_ticks
                    for entity in faulted
                )
                if faulted
                else 0.0
            ),
            "max_wear": max(
                (
                    entity.wear / threshold
                    for entity in self.world.state.entities.values()
                ),
                default=0.0,
            ),
            "repairs": self.repairs,
            "assembler_input": (
                assembler.total_input() if assembler else 0
            ),
            "assembler_craft": (
                assembler.craft_progress if assembler else 0
            ),
            "furnace_output": furnace.total_output() if furnace else 0,
            "furnace_craft": furnace.craft_progress if furnace else 0,
            "total_reward": self.total_reward,
            "success": (
                self.world.state.score >= self.interaction.success_score
            ),
        }
