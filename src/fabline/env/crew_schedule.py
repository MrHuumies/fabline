"""Repair-crew scheduling with travel time on the wired power grid."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import Entity, EntityType, PowerWire
from fabline.worlds.factory.wire import entity_connected, reachable_cells
from fabline.worlds.factory.world import FactoryWorld

CREW_TASK_ID = "factory.power.crew-schedule.v1"
CREW_TASK_VERSION = "0.1.0"

CREW_FEATURES = (
    "tick_norm",
    "score_norm",
    "budget_norm",
    "crew_x_norm",
    "crew_y_norm",
    *(
        f"{role}_{name}"
        for role in ("loop", "small", "large")
        for name in (
            "outage_norm",
            "state",
            "distance_norm",
            "service_time_norm",
            "deadline_norm",
        )
    ),
)

ROLES = ("loop", "small", "large")


@dataclass(frozen=True)
class CrewScheduleConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    warning_tick: int = 40
    loop_failure_tick: int = 220
    small_failure_tick: int = 280
    large_failure_tick: int = 340
    repair_ticks: int = 40
    travel_ticks_per_cell: int = 2
    repair_budget: int = 2
    service_cost: float = 1.0
    reward: float = 10.0
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
            raise ValueError("episode ticks must be positive")
        if not 0 < self.warning_tick < self.loop_failure_tick:
            raise ValueError("warning must precede the first failure")
        if not (
            self.loop_failure_tick
            < self.small_failure_tick
            < self.large_failure_tick
        ):
            raise ValueError("failure ticks must increase")
        if self.repair_ticks < 0 or self.repair_budget < 0:
            raise ValueError("repair time and budget must be non-negative")
        if not self.power.enabled or self.power.topology != "wired":
            raise ValueError("crew scheduling requires wired power")


class CrewScheduleEnv:
    """Choose noop or service one of three role wires."""

    n_actions = 4
    ACTION_NAMES = ("noop", "service_loop", "service_small", "service_large")

    def __init__(
        self,
        config: FactoryConfig,
        crew: CrewScheduleConfig | None = None,
    ) -> None:
        self.config = config
        self.crew = crew or CrewScheduleConfig()
        if self.crew.episode_ticks != self.config.ticks_per_episode:
            raise ValueError("crew.episode_ticks must equal config.ticks_per_episode")
        self.world = FactoryWorld(config, power=self.crew.power)
        self.reset(0)

    def _consumers(self) -> list[Entity]:
        return [
            entity
            for entity in sorted(
                self.world.state.entities.values(), key=lambda item: item.id
            )
            if self.crew.power.demand(entity.type) > 0
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

    def _wire(self, wire_id: int) -> PowerWire:
        return next(
            wire
            for wire in self.world.state.power_wires
            if wire.id == wire_id
        )

    def _nearest_endpoint(self, wire: PowerWire) -> tuple[int, int]:
        endpoints = ((wire.ax, wire.ay), (wire.bx, wire.by))
        return min(
            endpoints,
            key=lambda cell: abs(cell[0] - self.crew_x)
            + abs(cell[1] - self.crew_y),
        )

    def _distance(self, wire: PowerWire) -> int:
        x, y = self._nearest_endpoint(wire)
        return abs(x - self.crew_x) + abs(y - self.crew_y)

    def _service_ticks(self, wire: PowerWire) -> int:
        return (
            self._distance(wire) * self.crew.travel_ticks_per_cell
            + self.crew.repair_ticks
        )

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed, SCENARIOS["gear"])
        self.total_reward = 0.0
        self.repairs = 0
        self.prevented = 0
        self.aborted = 0
        self.travel_ticks = 0
        self.warned = False
        self.steps = 0
        self.last_action = "noop"
        self.last_reward = 0.0
        depot = next(
            (
                entity
                for entity in self.world.state.entities.values()
                if entity.type is EntityType.DEPOT
            ),
            None,
        )
        self.crew_x, self.crew_y = (
            (depot.x, depot.y) if depot is not None else (1, 1)
        )
        outages = {
            wire.id: self._outage(wire)
            for wire in self.world.state.power_wires
        }
        positive = sorted(
            (
                (size, wire_id)
                for wire_id, size in outages.items()
                if size > 0
            ),
            key=lambda item: (item[0], item[1]),
        )
        loops = sorted(
            wire_id for wire_id, size in outages.items() if size == 0
        )
        if len(positive) < 2 or not loops:
            raise RuntimeError("crew task needs a loop and two positive wires")
        self.role_wires = {
            "loop": loops[0],
            "small": positive[0][1],
            "large": positive[-1][1],
        }
        self.role_outages = {
            "loop": 0,
            "small": positive[0][0],
            "large": positive[-1][0],
        }
        self.failure_ticks = {
            "loop": self.crew.loop_failure_tick,
            "small": self.crew.small_failure_tick,
            "large": self.crew.large_failure_tick,
        }
        return self._observation(), self._info()

    def _available(self, role: str) -> bool:
        wire = self._wire(self.role_wires[role])
        return self.repairs < self.crew.repair_budget and (
            wire.degraded or wire.failed
        )

    def action_mask(self) -> np.ndarray:
        return np.asarray(
            [True] + [self._available(role) for role in ROLES],
            dtype=bool,
        )

    def _advance(self, ticks: int) -> None:
        for _ in range(ticks):
            if self.world.done:
                break
            next_tick = self.world.state.tick + 1
            if not self.warned and next_tick == self.crew.warning_tick:
                for role in ROLES:
                    self.world.degrade_wire(
                        self.role_wires[role],
                        self.failure_ticks[role],
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
        if action > 0 and legal:
            role = ROLES[action - 1]
            wire = self._wire(self.role_wires[role])
            preventive = wire.degraded and not wire.failed
            outage = self.role_outages[role]
            distance = self._distance(wire)
            service_ticks = self._service_ticks(wire)
            self.travel_ticks += distance * self.crew.travel_ticks_per_cell
            self.repairs += 1
            self._advance(service_ticks)
            wire = self._wire(self.role_wires[role])
            if preventive and wire.failed:
                aborted = True
                self.aborted += 1
            else:
                self.world.repair_wire(wire.id)
                endpoint = self._nearest_endpoint(wire)
                self.crew_x, self.crew_y = endpoint
                remaining = max(
                    0, self.crew.episode_ticks - self.world.state.tick
                )
                reward = (
                    outage
                    * self.crew.reward
                    * remaining
                    / self.crew.episode_ticks
                    - self.crew.service_cost
                )
                if preventive:
                    self.prevented += 1
        else:
            self._advance(self.crew.decision_interval)
        self.total_reward += reward
        self.steps += 1
        self.last_action = self.ACTION_NAMES[action]
        self.last_reward = reward
        info = self._info()
        info["illegal"] = not legal
        info["aborted"] = aborted
        info["aborted_count"] = self.aborted
        info["reward"] = reward
        return self._observation(), reward, self.world.done, False, info

    def _observation(self) -> np.ndarray:
        state = self.world.state
        consumers = max(1, len(self._consumers()))
        values: list[float] = [
            state.tick / self.crew.episode_ticks,
            state.score / 500.0,
            max(0, self.crew.repair_budget - self.repairs)
            / max(1, self.crew.repair_budget),
            self.crew_x / max(1, state.width - 1),
            self.crew_y / max(1, state.height - 1),
        ]
        for role in ROLES:
            wire = self._wire(self.role_wires[role])
            degraded = wire.degraded
            failed = wire.failed
            state_value = 1.0 if failed else 0.5 if degraded else 0.0
            deadline = (
                max(0, wire.failure_tick - state.tick)
                / self.crew.episode_ticks
                if degraded
                else 0.0
            )
            values.extend(
                [
                    self.role_outages[role] / consumers,
                    state_value,
                    self._distance(wire)
                    / max(1, state.width + state.height),
                    self._service_ticks(wire) / 100.0,
                    deadline,
                ]
            )
        return np.asarray(values, dtype=np.float32)

    def _info(self) -> dict[str, Any]:
        roles = {}
        for role in ROLES:
            wire = self._wire(self.role_wires[role])
            roles[role] = {
                "wire_id": wire.id,
                "outage": self.role_outages[role],
                "degraded": wire.degraded,
                "failed": wire.failed,
                "distance": self._distance(wire),
                "service_ticks": self._service_ticks(wire),
                "deadline": wire.failure_tick,
            }
        return {
            "score": self.world.state.score,
            "tick": self.world.state.tick,
            "budget_remaining": max(
                0, self.crew.repair_budget - self.repairs
            ),
            "roles": roles,
            "repairs": self.repairs,
            "prevented": self.prevented,
            "aborted": self.aborted,
            "travel_ticks": self.travel_ticks,
            "crew": (self.crew_x, self.crew_y),
            "total_reward": self.total_reward,
            "last_action": self.last_action,
            "last_reward": self.last_reward,
            "success": self.world.state.score >= self.crew.success_score,
        }
