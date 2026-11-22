"""Threshold-selection task for preventive machine maintenance.

The per-step Q baseline collapses because the fault-avoidance benefit is far
delayed. This task chooses the maintenance threshold once per episode; a
scripted policy applies it. The decision variable is the actual policy knob,
not each noop/maintain step.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.env.preventive_fault import (
    PreventiveFaultConfig,
    PreventiveFaultEnv,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig

THRESHOLD_TASK_ID = "factory.fault.preventive-threshold.v1"
THRESHOLD_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class ThresholdConfig:
    arms: tuple[float, ...] = (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
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
        if not self.arms:
            raise ValueError("at least one threshold arm is required")
        if any(not 0.0 < arm <= 1.0 for arm in self.arms):
            raise ValueError("threshold arms must be in (0, 1]")
        if not self.faults.enabled:
            raise ValueError("threshold selection requires faults.enabled")


class PreventiveThresholdEnv:
    """One action per episode: choose a maintenance wear threshold."""

    def __init__(
        self,
        config: FactoryConfig,
        threshold: ThresholdConfig | None = None,
    ) -> None:
        self.config = config
        self.threshold = threshold or ThresholdConfig()
        self.inner = PreventiveFaultEnv(
            config,
            PreventiveFaultConfig(
                episode_ticks=config.ticks_per_episode,
                decision_interval=config.decision_interval,
                success_score=self.threshold.success_score,
                faults=self.threshold.faults,
            ),
        )
        self.n_actions = len(self.threshold.arms)
        self.seed = 0

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.seed = seed
        return np.zeros(1, dtype=np.float32), {
            "seed": seed,
            "arms": list(self.threshold.arms),
        }

    def action_mask(self) -> np.ndarray:
        return np.ones(self.n_actions, dtype=bool)

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError("action outside the threshold arms")
        threshold = self.threshold.arms[action]
        observation, info = self.inner.reset(seed=self.seed)
        done = False
        while not done:
            action_inner = 0
            if (
                info["max_wear"]
                >= threshold * self.threshold.faults.fault_threshold
                and self.inner.action_mask()[1]
            ):
                action_inner = 1
            observation, _, terminated, truncated, info = self.inner.step(
                action_inner
            )
            done = terminated or truncated
        info["threshold"] = threshold
        return (
            np.zeros(1, dtype=np.float32),
            float(info["score"]),
            True,
            False,
            info,
        )
