"""Two-action fault-recovery environment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from fabline.obs.sensors import DiagnosticsObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.state import Entity
from fabline.worlds.factory.world import FactoryWorld


@dataclass(frozen=True)
class FaultRecoveryConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    repair_cost: float = 1.0
    success_score: int = 250

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode_ticks and decision_interval must be positive")
        if self.repair_cost < 0:
            raise ValueError("repair_cost must be non-negative")
        if self.success_score < 0:
            raise ValueError("success_score must be non-negative")


class FaultRecoveryEnv:
    """Choose between waiting and spending a repair action on a faulted line."""

    n_actions = 2
    ACTION_NAMES = ("noop", "repair")

    def __init__(
        self,
        config: FactoryConfig,
        recovery: FaultRecoveryConfig | None = None,
        faults: FaultConfig | None = None,
    ) -> None:
        self.config = config
        self.recovery = recovery or FaultRecoveryConfig()
        self.faults = faults or FaultConfig(enabled=True)
        if not self.config.starter_line:
            raise ValueError("fault recovery requires a starter line")
        if self.recovery.episode_ticks != self.config.ticks_per_episode:
            raise ValueError("recovery.episode_ticks must equal config.ticks_per_episode")
        if not self.faults.enabled:
            raise ValueError("fault recovery requires faults.enabled")
        self.world = FactoryWorld(self.config, self.faults)
        self.observation = DiagnosticsObservation(self.config, self.faults)
        self.reset(0)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed, SCENARIOS["gear"])
        self.total_reward = 0.0
        self.repairs = 0
        self.steps = 0
        self.last_action = "noop"
        self.last_reward = 0.0
        return self._observation(), self._info()

    def _faulted(self) -> list[Entity]:
        return sorted(
            (entity for entity in self.world.state.entities.values() if entity.faulted),
            key=lambda entity: entity.id,
        )

    def action_mask(self) -> np.ndarray:
        return np.asarray([True, bool(self._faulted())], dtype=bool)

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        faulted = self._faulted()
        legal = bool(self.action_mask()[action])
        score_before = self.world.state.score
        repair_cost = 0.0
        if action == 1 and legal:
            self.world.repair_entity(faulted[0])
            self.repairs += 1
            repair_cost = self.recovery.repair_cost

        self.world.run_ticks(self.recovery.decision_interval)
        score_after = self.world.state.score
        reward = float(score_after - score_before) - repair_cost
        self.total_reward += reward
        self.steps += 1
        self.last_action = self.ACTION_NAMES[action]
        self.last_reward = reward
        info = self._info()
        info["illegal"] = not legal
        return self._observation(), reward, self.world.done, False, info

    def _observation(self) -> np.ndarray:
        return self.observation.observe(self.world.state)

    def _info(self) -> dict[str, Any]:
        faulted = self._faulted()
        wear = [
            entity.wear / max(1, self.faults.fault_threshold)
            for entity in self.world.state.entities.values()
        ]
        return {
            "score": self.world.state.score,
            "tick": self.world.state.tick,
            "faulted_count": len(faulted),
            "mean_wear": float(np.mean(wear)) if wear else 0.0,
            "max_wear": float(np.max(wear)) if wear else 0.0,
            "repairs": self.repairs,
            "total_reward": self.total_reward,
            "last_action": self.last_action,
            "last_reward": self.last_reward,
            "success": self.world.state.score >= self.recovery.success_score,
        }
