"""Preventive wire maintenance.

A degraded wire has a scheduled failure. Repair can start before the failure;
if the repair completes in time, the outage is prevented. If the failure lands
mid-repair, the job aborts and the budget is spent. This gives a prediction a
reason and a timing cost.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import Entity, PowerWire
from fabline.worlds.factory.wire import entity_connected, reachable_cells
from fabline.worlds.factory.world import FactoryWorld

PREVENTIVE_WIRE_TASK_ID = "factory.power.wire-maintenance.v1"
PREVENTIVE_WIRE_TASK_VERSION = "0.1.0"

PREVENTIVE_WIRE_FEATURES = (
    "tick_norm",
    "score_norm",
    "outage_norm",
    "degraded",
    "failed",
    "time_to_failure_norm",
    "budget_norm",
    "repaired",
)


@dataclass(frozen=True)
class PreventiveWireConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    warning_tick: int = 60
    failure_tick: int = 220
    repair_ticks: int = 140
    repair_budget: int = 1
    repair_cost: float = 1.0
    prevention_reward: float = 15.0
    restoration_reward: float = 10.0
    success_score: int = 150
    power: PowerConfig = field(
        default_factory=lambda: PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=12,
            generator_radius=8,
            wire_redundancy=2,
        )
    )

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode_ticks and decision_interval must be positive")
        if not 0 < self.warning_tick < self.failure_tick:
            raise ValueError("warning_tick must be before failure_tick")
        if self.repair_ticks < 0:
            raise ValueError("repair_ticks must be non-negative")
        if self.repair_budget < 0:
            raise ValueError("repair_budget must be non-negative")
        if self.repair_cost < 0 or self.prevention_reward < 0:
            raise ValueError("rewards must be non-negative")
        if not self.power.enabled or self.power.topology != "wired":
            raise ValueError("preventive maintenance requires wired power")


class PreventiveWireEnv:
    """Two actions: wait, or start a repair on the watched wire."""

    n_actions = 2
    ACTION_NAMES = ("noop", "repair")

    def __init__(
        self,
        config: FactoryConfig,
        preventive: PreventiveWireConfig | None = None,
    ) -> None:
        self.config = config
        self.preventive = preventive or PreventiveWireConfig()
        if self.preventive.episode_ticks != self.config.ticks_per_episode:
            raise ValueError(
                "preventive.episode_ticks must equal config.ticks_per_episode"
            )
        self.world = FactoryWorld(config, power=self.preventive.power)
        self.reset(0)

    def _consumers(self) -> list[Entity]:
        return [
            entity
            for entity in sorted(
                self.world.state.entities.values(), key=lambda item: item.id
            )
            if self.preventive.power.demand(entity.type) > 0
        ]

    def _connected_ids(self) -> set[int]:
        wires = self.world.state.power_wires
        reachable = reachable_cells(
            self.world.state.power_sources[0], wires
        )
        return {
            entity.id
            for entity in self._consumers()
            if entity_connected(entity, reachable, wires)
        }

    def _outage(self, wire: PowerWire) -> int:
        before = self._connected_ids()
        wire.failed = True
        after = self._connected_ids()
        wire.failed = False
        return len(before - after)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed, SCENARIOS["gear"])
        self.total_reward = 0.0
        self.repairs = 0
        self.prevented = 0
        self.aborted = 0
        self.warned = False
        self.repaired = False
        self.steps = 0
        self.last_action = "noop"
        self.last_reward = 0.0
        outages = {
            wire.id: self._outage(wire)
            for wire in self.world.state.power_wires
        }
        positive = {
            wire_id: size for wire_id, size in outages.items() if size > 0
        }
        if not positive:
            raise RuntimeError("no wire has a positive outage")
        self.outage = max(positive.values())
        self.target_id = max(
            positive, key=lambda wire_id: (positive[wire_id], -wire_id)
        )
        self._target_failed_at = 0
        return self._observation(), self._info()

    def _target(self) -> PowerWire:
        return next(
            wire
            for wire in self.world.state.power_wires
            if wire.id == self.target_id
        )

    def action_mask(self) -> np.ndarray:
        wire = self._target()
        legal = self.repairs < self.preventive.repair_budget and (
            wire.degraded or wire.failed
        )
        return np.asarray([True, legal], dtype=bool)

    def _advance(self, ticks: int) -> None:
        for _ in range(ticks):
            if self.world.done:
                break
            next_tick = self.world.state.tick + 1
            if (
                not self.warned
                and next_tick == self.preventive.warning_tick
            ):
                self.world.degrade_wire(
                    self.target_id, self.preventive.failure_tick
                )
                self.warned = True
            self.world.tick()

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        legal = bool(self.action_mask()[action])
        reward = 0.0
        aborted = False
        if action == 1 and legal:
            wire = self._target()
            preventive = wire.degraded and not wire.failed
            self.repairs += 1
            self._advance(self.preventive.repair_ticks)
            wire = self._target()
            if preventive and wire.failed:
                aborted = True
                self.aborted += 1
            else:
                self.world.repair_wire(wire.id)
                self.repaired = True
                remaining = max(
                    0,
                    self.preventive.episode_ticks - self.world.state.tick,
                )
                if preventive:
                    self.prevented += 1
                    reward = (
                        self.outage * self.preventive.prevention_reward
                        - self.preventive.repair_cost
                    )
                else:
                    reward = (
                        self.outage
                        * self.preventive.restoration_reward
                        * remaining
                        / self.preventive.episode_ticks
                        - self.preventive.repair_cost
                    )
        else:
            self._advance(self.preventive.decision_interval)
        self.total_reward += reward
        self.steps += 1
        self.last_action = self.ACTION_NAMES[action]
        self.last_reward = reward
        info = self._info()
        info["illegal"] = not legal
        info["aborted_now"] = aborted
        info["reward"] = reward
        return self._observation(), reward, self.world.done, False, info

    def _observation(self) -> np.ndarray:
        wire = self._target()
        state = self.world.state
        remaining = (
            max(0, wire.failure_tick - state.tick) / self.preventive.episode_ticks
            if wire.degraded
            else 0.0
        )
        values = (
            state.tick / self.preventive.episode_ticks,
            state.score / 500.0,
            self.outage / max(1, len(self._consumers())),
            1.0 if wire.degraded else 0.0,
            1.0 if wire.failed else 0.0,
            remaining,
            max(
                0,
                self.preventive.repair_budget - self.repairs,
            )
            / max(1, self.preventive.repair_budget),
            1.0 if self.repaired else 0.0,
        )
        return np.asarray(values, dtype=np.float32)

    def _info(self) -> dict[str, Any]:
        wire = self._target()
        return {
            "score": self.world.state.score,
            "tick": self.world.state.tick,
            "target_id": self.target_id,
            "target_outage": self.outage,
            "degraded": wire.degraded,
            "failed": wire.failed,
            "failure_tick": wire.failure_tick,
            "repairs": self.repairs,
            "prevented": self.prevented,
            "aborted": self.aborted,
            "repaired": self.repaired,
            "total_reward": self.total_reward,
            "last_action": self.last_action,
            "last_reward": self.last_reward,
            "success": self.world.state.score >= self.preventive.success_score,
        }
