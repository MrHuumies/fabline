"""Two-crew parallel repair assignment."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import Entity, EntityType, PowerWire, TileType
from fabline.worlds.factory.wire import entity_connected, reachable_cells
from fabline.worlds.factory.world import FactoryWorld

MULTI_CREW_TASK_ID = "factory.power.crew-coordination.v1"
MULTI_CREW_TASK_VERSION = "0.1.0"

ROLES = ("loop", "small", "large")
CHOICES = 4  # noop, loop, small, large

MULTI_CREW_FEATURES = (
    "tick_norm",
    "score_norm",
    "crew_a_x_norm",
    "crew_a_y_norm",
    "crew_b_x_norm",
    "crew_b_y_norm",
    *(
        f"{role}_{name}"
        for role in ROLES
        for name in (
            "outage_norm",
            "state",
            "deadline_norm",
            "distance_a_norm",
            "distance_b_norm",
        )
    ),
)


@dataclass(frozen=True)
class MultiCrewConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    warning_tick: int = 40
    loop_failure_tick: int = 90
    small_failure_tick: int = 110
    large_failure_tick: int = 130
    repair_ticks: int = 40
    travel_ticks_per_cell: int = 2
    randomize_crew_b: bool = False
    crew_b_min_distance: int = 6
    scenario: str = "gear"
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
        if self.crew_b_min_distance < 0:
            raise ValueError("crew_b_min_distance must be non-negative")
        if self.scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario: {self.scenario}")
        if not self.power.enabled or self.power.topology != "wired":
            raise ValueError("crew coordination requires wired power")


class MultiCrewEnv:
    """One action assigns a target to each crew; jobs run in parallel."""

    n_actions = CHOICES * CHOICES
    ACTION_NAMES = tuple(
        f"a{first}_b{second}"
        for first in range(CHOICES)
        for second in range(CHOICES)
    )

    def __init__(
        self,
        config: FactoryConfig,
        multi: MultiCrewConfig | None = None,
        roles: tuple[str, ...] = ROLES,
    ) -> None:
        if len(roles) != CHOICES - 1:
            raise ValueError("crew tasks need three target roles")
        self.config = config
        self.multi = multi or MultiCrewConfig()
        self.roles = roles
        if self.multi.episode_ticks != self.config.ticks_per_episode:
            raise ValueError("multi.episode_ticks must equal config.ticks_per_episode")
        self.world = FactoryWorld(config, power=self.multi.power)
        self.reset(0)

    def _random_crew_b(self, seed: int) -> tuple[int, int]:
        rng = random.Random(seed * 104729 + 7)
        state = self.world.state
        occupied = {
            (entity.x, entity.y) for entity in state.entities.values()
        }
        candidates = [
            (x, y)
            for y in range(1, state.height - 1)
            for x in range(1, state.width - 1)
            if (x, y) not in occupied
            and state.tiles[y * state.width + x] is TileType.EMPTY
            and abs(x - self.crew_a[0]) + abs(y - self.crew_a[1])
            >= self.multi.crew_b_min_distance
        ]
        if not candidates:
            raise RuntimeError("no eligible random crew B base")
        return rng.choice(candidates)

    def _consumers(self) -> list[Entity]:
        return [
            entity
            for entity in sorted(
                self.world.state.entities.values(), key=lambda item: item.id
            )
            if self.multi.power.demand(entity.type) > 0
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

    def _nearest_endpoint(
        self, wire: PowerWire, crew: tuple[int, int]
    ) -> tuple[int, int]:
        endpoints = ((wire.ax, wire.ay), (wire.bx, wire.by))
        return min(
            endpoints,
            key=lambda cell: abs(cell[0] - crew[0])
            + abs(cell[1] - crew[1]),
        )

    def _distance(
        self, wire: PowerWire, crew: tuple[int, int]
    ) -> int:
        x, y = self._nearest_endpoint(wire, crew)
        return abs(x - crew[0]) + abs(y - crew[1])

    def _service_ticks(
        self, wire: PowerWire, crew: tuple[int, int]
    ) -> int:
        return (
            self._distance(wire, crew) * self.multi.travel_ticks_per_cell
            + self.multi.repair_ticks
        )

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed, SCENARIOS[self.multi.scenario])
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
        self.crew_a = (depot.x, depot.y) if depot else (1, 1)
        self.crew_b = (
            self.world.state.width - 2,
            self.world.state.height - 2,
        )
        if self.multi.randomize_crew_b:
            self.crew_b = self._random_crew_b(seed)
        outages = {
            wire.id: self._outage(wire)
            for wire in self.world.state.power_wires
        }
        (
            self.role_wires,
            self.role_outages,
            self.failure_ticks,
        ) = self._select_roles(outages)
        return self._observation(), self._info()

    def _select_roles(
        self,
        outages: dict[int, int],
    ) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
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
            raise RuntimeError("multi-crew task needs a loop and two bridges")
        return (
            {
                "loop": loops[0],
                "small": positive[0][1],
                "large": positive[-1][1],
            },
            {
                "loop": 0,
                "small": positive[0][0],
                "large": positive[-1][0],
            },
            {
                "loop": self.multi.loop_failure_tick,
                "small": self.multi.small_failure_tick,
                "large": self.multi.large_failure_tick,
            },
        )

    def action_mask(self) -> np.ndarray:
        mask = np.zeros(self.n_actions, dtype=bool)
        if not self.warned:
            mask[0] = True
            return mask
        for action in range(self.n_actions):
            first, second = divmod(action, CHOICES)
            if first > 0 and first == second:
                continue
            mask[action] = True
        return mask

    def _advance(self, ticks: int) -> None:
        for _ in range(ticks):
            if self.world.done:
                break
            next_tick = self.world.state.tick + 1
            if not self.warned and next_tick == self.multi.warning_tick:
                for role in self.roles:
                    self.world.degrade_wire(
                        self.role_wires[role],
                        self.failure_ticks[role],
                    )
                self.warned = True
            self.world.tick()

    def _job(
        self,
        choice: int,
        crew: tuple[int, int],
    ) -> dict[str, Any] | None:
        if choice == 0:
            return None
        role = self.roles[choice - 1]
        wire = self._wire(self.role_wires[role])
        return {
            "role": role,
            "wire": wire,
            "crew": crew,
            "preventive": wire.degraded and not wire.failed,
            "outage": self.role_outages[role],
            "distance": self._distance(wire, crew),
            "duration": self._service_ticks(wire, crew),
        }

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        legal = bool(self.action_mask()[action])
        if not self.warned or not legal:
            self._advance(self.multi.decision_interval)
            self.steps += 1
            info = self._info()
            info["illegal"] = not legal
            info["reward"] = 0.0
            return self._observation(), 0.0, self.world.done, False, info

        first, second = divmod(action, CHOICES)
        jobs = [
            job
            for job in (
                self._job(first, self.crew_a),
                self._job(second, self.crew_b),
            )
            if job is not None
        ]
        score_before = self.world.state.score
        self.repairs += len(jobs)
        for job in jobs:
            self.travel_ticks += (
                job["distance"] * self.multi.travel_ticks_per_cell
            )
        elapsed = 0
        remaining_jobs = list(jobs)
        while remaining_jobs and not self.world.done:
            self._advance(1)
            elapsed += 1
            for job in list(remaining_jobs):
                if elapsed < job["duration"]:
                    continue
                wire = self._wire(self.role_wires[job["role"]])
                if job["preventive"] and wire.failed:
                    self.aborted += 1
                else:
                    self.world.repair_wire(wire.id)
                    endpoint = self._nearest_endpoint(
                        wire, job["crew"]
                    )
                    if job["crew"] == self.crew_a:
                        self.crew_a = endpoint
                    else:
                        self.crew_b = endpoint
                    if job["preventive"]:
                        self.prevented += 1
                remaining_jobs.remove(job)
        self._advance(max(0, self.multi.episode_ticks - self.world.state.tick))
        score_after = self.world.state.score
        reward = float(score_after - score_before)
        self.steps += 1
        self.last_action = self.ACTION_NAMES[action]
        self.last_reward = reward
        info = self._info()
        info["illegal"] = False
        info["reward"] = reward
        info["jobs"] = [
            {
                "role": job["role"],
                "distance": job["distance"],
                "duration": job["duration"],
            }
            for job in jobs
        ]
        return self._observation(), reward, True, False, info

    def _observation(self) -> np.ndarray:
        state = self.world.state
        consumers = max(1, len(self._consumers()))
        values: list[float] = [
            state.tick / self.multi.episode_ticks,
            state.score / 500.0,
            self.crew_a[0] / max(1, state.width - 1),
            self.crew_a[1] / max(1, state.height - 1),
            self.crew_b[0] / max(1, state.width - 1),
            self.crew_b[1] / max(1, state.height - 1),
        ]
        for role in self.roles:
            wire = self._wire(self.role_wires[role])
            state_value = 1.0 if wire.failed else 0.5 if wire.degraded else 0.0
            deadline = (
                max(0, wire.failure_tick - state.tick)
                / self.multi.episode_ticks
                if wire.degraded
                else 0.0
            )
            values.extend(
                [
                    self.role_outages[role] / consumers,
                    state_value,
                    deadline,
                    self._distance(wire, self.crew_a)
                    / max(1, state.width + state.height),
                    self._distance(wire, self.crew_b)
                    / max(1, state.width + state.height),
                ]
            )
        return np.asarray(values, dtype=np.float32)

    def _info(self) -> dict[str, Any]:
        roles = {}
        for role in self.roles:
            wire = self._wire(self.role_wires[role])
            roles[role] = {
                "wire_id": wire.id,
                "outage": self.role_outages[role],
                "degraded": wire.degraded,
                "failed": wire.failed,
                "deadline": wire.failure_tick,
                "distance_a": self._distance(wire, self.crew_a),
                "distance_b": self._distance(wire, self.crew_b),
                "service_a": self._service_ticks(wire, self.crew_a),
                "service_b": self._service_ticks(wire, self.crew_b),
            }
        return {
            "score": self.world.state.score,
            "tick": self.world.state.tick,
            "roles": roles,
            "crew_a": self.crew_a,
            "crew_b": self.crew_b,
            "repairs": self.repairs,
            "prevented": self.prevented,
            "aborted": self.aborted,
            "travel_ticks": self.travel_ticks,
            "last_action": self.last_action,
            "last_reward": self.last_reward,
            "success": self.world.state.score >= self.multi.success_score,
        }
