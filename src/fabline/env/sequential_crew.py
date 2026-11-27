"""Deterministic sequential two-crew repair control.

Crews are task-layer actors on a wired-power factory layout. Each crew moves one
cell per decision, repairs a failed wire from an adjacent cell, or waits. Wires
are failed at reset; repairing them restores production.

The canonical factory hash is unchanged: crew positions and repair progress are
task-layer state. The world state and the crew state are both serializable for
replay.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import Entity, PowerWire, TileType
from fabline.worlds.factory.wire import entity_connected, reachable_cells
from fabline.worlds.factory.world import FactoryWorld

SEQUENTIAL_CREW_TASK_ID = "factory.power.crew-sequential.v1"
SEQUENTIAL_CREW_TASK_VERSION = "0.1.0"

CREW_ACTIONS = ("north", "east", "south", "west", "wait", "repair")
N_CREW_ACTIONS = len(CREW_ACTIONS)
N_CREWS = 2
TARGETS = 3

DELTAS = {
    0: (0, -1),
    1: (1, 0),
    2: (0, 1),
    3: (-1, 0),
}


@dataclass(frozen=True)
class SequentialCrewConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    target_count: int = TARGETS
    repair_ticks: int = 6
    repair_bonus: float = 5.0
    progress_bonus: float = 0.2
    success_score: int = 150
    power: PowerConfig = field(
        default_factory=lambda: PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=12,
            generator_radius=8,
            wire_redundancy=1,
        )
    )

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode ticks and decision interval must be positive")
        if self.target_count <= 0:
            raise ValueError("target_count must be positive")
        if self.repair_ticks <= 0:
            raise ValueError("repair_ticks must be positive")
        if self.repair_bonus < 0 or self.progress_bonus < 0:
            raise ValueError("repair bonuses must be non-negative")
        if self.success_score < 0:
            raise ValueError("success_score must be non-negative")
        if not self.power.enabled or self.power.topology != "wired":
            raise ValueError("sequential crews require wired power")


def crew_feature_names(targets: int = TARGETS) -> tuple[str, ...]:
    names = ["tick_norm", "score_norm"]
    names.extend(
        f"crew_{index}_{axis}_norm"
        for index in range(N_CREWS)
        for axis in ("x", "y")
    )
    names.extend(
        f"target_{index}_{name}"
        for index in range(targets)
        for name in (
            "failed",
            "distance_a_norm",
            "distance_b_norm",
            "progress_norm",
        )
    )
    names.extend(
        [
            "repaired_fraction",
            "budget_norm",
        ]
    )
    return tuple(names)


class SequentialCrewEnv:
    """Two-crew sequential movement and repair on a wired-power line."""

    n_crews = N_CREWS
    n_actions_per_crew = N_CREW_ACTIONS
    n_actions = N_CREW_ACTIONS**N_CREWS
    ACTION_NAMES = CREW_ACTIONS
    JOINT_ACTION_NAMES = tuple(
        f"a{first}_b{second}"
        for first in range(N_CREW_ACTIONS)
        for second in range(N_CREW_ACTIONS)
    )

    def __init__(
        self,
        config: FactoryConfig,
        crew: SequentialCrewConfig | None = None,
    ) -> None:
        self.config = config
        self.crew = crew or SequentialCrewConfig()
        if self.crew.episode_ticks != self.config.ticks_per_episode:
            raise ValueError("crew episode ticks must match config")
        self.world = FactoryWorld(config, power=self.crew.power)
        self._feature_names = crew_feature_names(self.crew.target_count)
        self.reset(0)

    @property
    def feature_names(self) -> tuple[str, ...]:
        return self._feature_names

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
        source = self.world.state.power_sources[0]
        reachable = reachable_cells(source, wires)
        return {
            entity.id
            for entity in self._consumers()
            if entity_connected(entity, reachable, wires)
        }

    def _connected_with(self, failed_ids: set[int]) -> set[int]:
        wires = self.world.state.power_wires
        saved = {wire.id: wire.failed for wire in wires}
        for wire in wires:
            wire.failed = wire.id in failed_ids
        connected = self._connected_ids()
        for wire in wires:
            wire.failed = saved[wire.id]
        return connected

    def _outage(self, wire: PowerWire) -> int:
        before = self._connected_with(set())
        after = self._connected_with({wire.id})
        return len(before - after)

    def _target_wires(self, seed: int) -> list[PowerWire]:
        rng = random.Random(seed * 104_729 + 113)
        wires = sorted(self.world.state.power_wires, key=lambda item: item.id)
        scored = [
            (self._outage(wire), rng.random(), wire)
            for wire in wires
        ]
        scored.sort(key=lambda item: (-item[0], item[1]))
        eligible = [wire for outage, _, wire in scored if outage > 0]
        if len(eligible) < self.crew.target_count:
            raise RuntimeError("layout has too few outage wires")
        return eligible[: self.crew.target_count]

    def _walkable(self, x: int, y: int) -> bool:
        if not 0 <= x < self.world.state.width:
            return False
        if not 0 <= y < self.world.state.height:
            return False
        return (
            self.world.state.tiles[y * self.world.state.width + x]
            is not TileType.ROCK
        )

    def _start_cell(self, preferred_x: int, preferred_y: int) -> tuple[int, int]:
        cells = [
            (x, y)
            for y in range(self.world.state.height)
            for x in range(self.world.state.width)
            if self._walkable(x, y)
        ]
        return min(
            cells,
            key=lambda cell: (
                abs(cell[0] - preferred_x) + abs(cell[1] - preferred_y),
                cell[1],
                cell[0],
            ),
        )

    def _wire(self, wire_id: int) -> PowerWire:
        return next(
            wire
            for wire in self.world.state.power_wires
            if wire.id == wire_id
        )

    @property
    def targets(self) -> list[PowerWire]:
        return [self._wire(wire_id) for wire_id in self.target_ids]

    def _endpoints(self, target: PowerWire) -> tuple[tuple[int, int], ...]:
        return ((target.ax, target.ay), (target.bx, target.by))

    def distance(self, position: tuple[int, int], target: PowerWire) -> int:
        return min(
            abs(x - position[0]) + abs(y - position[1])
            for x, y in self._endpoints(target)
        )

    def adjacent(self, crew_index: int, target_index: int) -> bool:
        target = self.targets[target_index]
        return (
            target.failed
            and self.distance(self.positions[crew_index], target) <= 1
        )

    def action_mask(self, crew_index: int) -> np.ndarray:
        mask = np.zeros(N_CREW_ACTIONS, dtype=bool)
        x, y = self.positions[crew_index]
        other = self.positions[1 - crew_index]
        for action, (dx, dy) in DELTAS.items():
            nx, ny = x + dx, y + dy
            if self._walkable(nx, ny) and (nx, ny) != other:
                mask[action] = True
        mask[4] = True
        mask[5] = any(
            self.adjacent(crew_index, target_index)
            for target_index in range(len(self.targets))
        )
        return mask

    def joint_mask(self) -> np.ndarray:
        first = self.action_mask(0)
        second = self.action_mask(1)
        return np.asarray(
            [first[a] and second[b] for a in range(N_CREW_ACTIONS) for b in range(N_CREW_ACTIONS)],
            dtype=bool,
        )

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.seed = seed
        self.world.reset(seed, SCENARIOS["gear"])
        wires = self._target_wires(seed)
        self.target_ids = [wire.id for wire in wires]
        for target in self.targets:
            target.failed = True
        self.positions = [
            self._start_cell(1, 1),
            self._start_cell(self.world.state.width - 2, self.world.state.height - 2),
        ]
        if self.positions[0] == self.positions[1]:
            self.positions[1] = self._start_cell(
                self.world.state.width - 2, 1
            )
        self.repair_progress = [0 for _ in self.targets]
        self.repairs = 0
        self.repair_steps = 0
        self.steps = 0
        self.total_reward = 0.0
        self.last_reward = 0.0
        self.last_action = (4, 4)
        return self.observe(), self.info()

    def _move(self, crew_index: int, action: int) -> None:
        dx, dy = DELTAS[action]
        x, y = self.positions[crew_index]
        nx, ny = x + dx, y + dy
        other = self.positions[1 - crew_index]
        if self._walkable(nx, ny) and (nx, ny) != other:
            self.positions[crew_index] = (nx, ny)

    def _repair(self, crew_index: int) -> None:
        for target_index, target in enumerate(self.targets):
            if not self.adjacent(crew_index, target_index):
                continue
            self.repair_steps += 1
            self.repair_progress[target_index] += 1
            if self.repair_progress[target_index] >= self.crew.repair_ticks:
                target.failed = False
                self.repair_progress[target_index] = 0
                self.repairs += 1
            break

    def step(
        self, action: tuple[int, int] | int
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if isinstance(action, int):
            if action < 0 or action >= self.n_actions:
                raise ValueError("joint action is outside the action space")
            first, second = divmod(action, N_CREW_ACTIONS)
        else:
            first, second = action
        for value in (first, second):
            if value < 0 or value >= N_CREW_ACTIONS:
                raise ValueError("crew action is outside the action space")
        if not self.action_mask(0)[first] or not self.action_mask(1)[second]:
            raise ValueError("joint action is masked")
        before = self.world.state.score
        repair_steps_before = self.repair_steps
        repairs_before = self.repairs
        for crew_index, value in enumerate((first, second)):
            if value < 4:
                self._move(crew_index, value)
            elif value == 5:
                self._repair(crew_index)
        self.world.run_ticks(self.crew.decision_interval)
        reward = (
            float(self.world.state.score - before)
            + (self.repair_steps - repair_steps_before)
            * self.crew.progress_bonus
            + (self.repairs - repairs_before) * self.crew.repair_bonus
        )
        self.total_reward += reward
        self.steps += 1
        self.last_action = (first, second)
        self.last_reward = reward
        return (
            self.observe(),
            reward,
            False,
            self.world.done,
            self.info(),
        )

    def observe(self) -> np.ndarray:
        state = self.world.state
        values: list[float] = [
            state.tick / max(1, self.crew.episode_ticks),
            state.score / 500.0,
        ]
        for x, y in self.positions:
            values.extend(
                [
                    x / max(1, state.width - 1),
                    y / max(1, state.height - 1),
                ]
            )
        for target_index, target in enumerate(self.targets):
            values.extend(
                [
                    1.0 if target.failed else 0.0,
                    self.distance(self.positions[0], target)
                    / max(1, state.width + state.height),
                    self.distance(self.positions[1], target)
                    / max(1, state.width + state.height),
                    self.repair_progress[target_index]
                    / max(1, self.crew.repair_ticks),
                ]
            )
        values.extend(
            [
                self.repairs / max(1, len(self.targets)),
                (self.crew.episode_ticks - state.tick)
                / max(1, self.crew.episode_ticks),
            ]
        )
        return np.asarray(values, dtype=np.float32)

    def info(self) -> dict[str, Any]:
        state = self.world.state
        return {
            "tick": state.tick,
            "score": state.score,
            "repairs": self.repairs,
            "targets": len(self.targets),
            "target_ids": [target.id for target in self.targets],
            "target_failed": [target.failed for target in self.targets],
            "positions": list(self.positions),
            "repair_progress": list(self.repair_progress),
            "repair_steps": self.repair_steps,
            "steps": self.steps,
            "mission_complete": all(
                not target.failed for target in self.targets
            ),
            "success": (
                self.repairs == len(self.targets)
                and state.score >= self.crew.success_score
            ),
        }

    def clone(self) -> SequentialCrewEnv:
        clone = object.__new__(SequentialCrewEnv)
        clone.config = self.config
        clone.crew = self.crew
        clone.world = self.world.clone()
        clone._feature_names = self._feature_names
        clone.seed = self.seed
        clone.target_ids = list(self.target_ids)
        clone.positions = list(self.positions)
        clone.repair_progress = list(self.repair_progress)
        clone.repairs = self.repairs
        clone.repair_steps = self.repair_steps
        clone.steps = self.steps
        clone.total_reward = self.total_reward
        clone.last_reward = self.last_reward
        clone.last_action = self.last_action
        return clone

    def replay_state(self) -> dict[str, Any]:
        return {
            "world": self.world.state.canonical(),
            "positions": [list(position) for position in self.positions],
            "target_ids": list(self.target_ids),
            "repair_progress": list(self.repair_progress),
            "repairs": self.repairs,
            "repair_steps": self.repair_steps,
            "steps": self.steps,
        }
