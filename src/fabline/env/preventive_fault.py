"""Preventive maintenance for the normal machine-wear fault mechanic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.obs.sensors import DiagnosticsObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.state import Entity
from fabline.worlds.factory.world import FactoryWorld

PREVENTIVE_FAULT_TASK_ID = "factory.fault.preventive.v1"
PREVENTIVE_FAULT_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class PreventiveFaultConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    success_score: int = 240
    faults: FaultConfig = field(
        default_factory=lambda: FaultConfig(
            enabled=True,
            wear_per_craft=1,
            miner_wear_per_ore=0,
            fault_threshold=20,
            repair_ticks=60,
            maintenance_ticks=10,
        )
    )

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode_ticks and decision_interval must be positive")
        if not self.faults.enabled:
            raise ValueError("preventive maintenance requires faults.enabled")
        if self.success_score < 0:
            raise ValueError("success_score must be non-negative")


class PreventiveFaultEnv:
    """Choose between waiting and maintaining the most worn machine."""

    n_actions = 2
    ACTION_NAMES = ("noop", "maintain")

    def __init__(
        self,
        config: FactoryConfig,
        preventive: PreventiveFaultConfig | None = None,
    ) -> None:
        self.config = config
        self.preventive = preventive or PreventiveFaultConfig()
        if self.preventive.episode_ticks != self.config.ticks_per_episode:
            raise ValueError(
                "preventive.episode_ticks must equal config.ticks_per_episode"
            )
        if not self.config.starter_line:
            raise ValueError("preventive maintenance requires a starter line")
        self.world = FactoryWorld(config, faults=self.preventive.faults)
        self.observation = DiagnosticsObservation(
            config, self.preventive.faults
        )
        self.reset(0)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed, SCENARIOS["gear"])
        self.total_reward = 0.0
        self.maintenance = 0
        self.steps = 0
        self.last_action = "noop"
        self.last_reward = 0.0
        return self._observation(), self._info()

    def _worn(self) -> list[Entity]:
        return sorted(
            (
                entity
                for entity in self.world.state.entities.values()
                if not entity.faulted
                and entity.maintenance_remaining == 0
                and entity.wear > 0
            ),
            key=lambda entity: (-entity.wear, entity.id),
        )

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
        return np.asarray([True, bool(self._worn())], dtype=bool)

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        legal = bool(self.action_mask()[action])
        if action == 1 and legal:
            target = self._worn()[0]
            self.world.maintain_entity(target)
            self.maintenance += 1
        score_before = self.world.state.score
        self.world.run_ticks(self.preventive.decision_interval)
        reward = float(self.world.state.score - score_before)
        self.total_reward += reward
        self.steps += 1
        self.last_action = self.ACTION_NAMES[action]
        self.last_reward = reward
        info = self._info()
        info["illegal"] = not legal
        return self._observation(), reward, self.world.done, False, info

    def _observation(self) -> np.ndarray:
        diagnostics = self.observation.observe(self.world.state)
        maintenance = max(
            (
                entity.maintenance_remaining
                for entity in self.world.state.entities.values()
            ),
            default=0,
        )
        extras = np.asarray(
            [
                self.maintenance / 100.0,
                maintenance
                / max(1, self.preventive.faults.maintenance_ticks),
            ],
            dtype=np.float32,
        )
        return np.concatenate([diagnostics, extras]).astype(np.float32)

    def _info(self) -> dict[str, Any]:
        worn = self._worn()
        return {
            "score": self.world.state.score,
            "tick": self.world.state.tick,
            "max_wear": (
                max(
                    entity.wear
                    for entity in self.world.state.entities.values()
                )
                if self.world.state.entities
                else 0
            ),
            "faulted_count": len(self._faulted()),
            "fault_events": sum(
                1
                for event in self.world.state.events
                if event.kind == "fault_started"
            ),
            "maintenance": self.maintenance,
            "maintenance_remaining": max(
                (
                    entity.maintenance_remaining
                    for entity in self.world.state.entities.values()
                ),
                default=0,
            ),
            "worn_count": len(worn),
            "total_reward": self.total_reward,
            "last_action": self.last_action,
            "last_reward": self.last_reward,
            "success": self.world.state.score >= self.preventive.success_score,
        }
