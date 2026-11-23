"""Three-crew one-shot assignment on the twin-line layout."""

from __future__ import annotations

import random
from typing import Any

import numpy as np

from fabline.env.multi_crew import (
    CHOICES,
    MULTI_CREW_FEATURES,
    MultiCrewConfig,
    MultiCrewEnv,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import TileType

THREE_CREW_TASK_ID = "factory.power.crew-three.v1"
THREE_CREW_TASK_VERSION = "0.1.0"

THREE_CREW_FEATURES = (
    *MULTI_CREW_FEATURES,
    "crew_c_x_norm",
    "crew_c_y_norm",
    *(f"{role}_distance_c_norm" for role in ("loop", "small", "large")),
)


class ThreeCrewEnv(MultiCrewEnv):
    """Three crews choose one bridge each; duplicates are masked."""

    n_actions = CHOICES * CHOICES * CHOICES
    ACTION_NAMES = tuple(
        f"a{first}_b{second}_c{third}"
        for first in range(CHOICES)
        for second in range(CHOICES)
        for third in range(CHOICES)
    )

    def __init__(
        self,
        config: FactoryConfig,
        multi: MultiCrewConfig | None = None,
    ) -> None:
        self.crew_c = (0, 0)
        super().__init__(config, multi)

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
        if len(positive) < 3:
            raise RuntimeError("three-crew task needs three positive wires")
        small = positive[0]
        large = positive[-1]
        middle = [
            item
            for item in positive
            if item[1] not in {small[1], large[1]}
        ]
        if not middle:
            raise RuntimeError("three-crew task needs three distinct wires")
        medium = middle[len(middle) // 2]
        return (
            {
                "loop": medium[1],
                "small": small[1],
                "large": large[1],
            },
            {
                "loop": medium[0],
                "small": small[0],
                "large": large[0],
            },
            {
                "loop": self.multi.loop_failure_tick,
                "small": self.multi.small_failure_tick,
                "large": self.multi.large_failure_tick,
            },
        )

    def _random_crew_c(self, seed: int) -> tuple[int, int]:
        rng = random.Random(seed * 130363 + 11)
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
            and abs(x - self.crew_b[0]) + abs(y - self.crew_b[1])
            >= self.multi.crew_b_min_distance
        ]
        if not candidates:
            raise RuntimeError("no eligible random crew C base")
        return rng.choice(candidates)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        _, _ = super().reset(seed)
        self.crew_c = self._random_crew_c(seed)
        self.score_start = self.world.state.score
        return self._observation(), self._info()

    def action_mask(self) -> np.ndarray:
        mask = np.zeros(self.n_actions, dtype=bool)
        if not self.warned:
            mask[0] = True
            return mask
        for action in range(self.n_actions):
            first = action // 16
            second = (action // 4) % 4
            third = action % 4
            positives = [value for value in (first, second, third) if value > 0]
            if len(set(positives)) != len(positives):
                continue
            mask[action] = True
        return mask

    def _run_jobs(self, jobs: list[dict[str, Any]]) -> None:
        remaining = list(jobs)
        elapsed = 0
        while remaining and not self.world.done:
            self._advance(1)
            elapsed += 1
            for job in list(remaining):
                if elapsed < job["duration"]:
                    continue
                wire = self._wire(self.role_wires[job["role"]])
                if job["preventive"] and wire.failed:
                    self.aborted += 1
                else:
                    self.world.repair_wire(wire.id)
                    endpoint = self._nearest_endpoint(wire, job["crew"])
                    if job["crew_id"] == "a":
                        self.crew_a = endpoint
                    elif job["crew_id"] == "b":
                        self.crew_b = endpoint
                    else:
                        self.crew_c = endpoint
                    if job["preventive"]:
                        self.prevented += 1
                remaining.remove(job)

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
        first = action // 16
        second = (action // 4) % 4
        third = action % 4
        jobs: list[dict[str, Any]] = []
        for choice, crew, crew_id in (
            (first, self.crew_a, "a"),
            (second, self.crew_b, "b"),
            (third, self.crew_c, "c"),
        ):
            job = self._job(choice, crew)
            if job is not None:
                job["crew_id"] = crew_id
                jobs.append(job)
                self.repairs += 1
                self.travel_ticks += (
                    job["distance"] * self.multi.travel_ticks_per_cell
                )
        self.last_action = self.ACTION_NAMES[action]
        self._run_jobs(jobs)
        self._advance(max(0, self.multi.episode_ticks - self.world.state.tick))
        reward = float(self.world.state.score - self.score_start)
        self.steps += 1
        self.last_reward = reward
        info = self._info()
        info["illegal"] = False
        info["reward"] = reward
        info["jobs"] = [
            {
                "role": job["role"],
                "crew": job["crew_id"],
                "distance": job["distance"],
                "duration": job["duration"],
            }
            for job in jobs
        ]
        return self._observation(), reward, True, False, info

    def _observation(self) -> np.ndarray:
        base = super()._observation()
        state = self.world.state
        scale = max(1, state.width + state.height)
        extra = [
            self.crew_c[0] / max(1, state.width - 1),
            self.crew_c[1] / max(1, state.height - 1),
        ]
        for role in self.roles:
            wire = self._wire(self.role_wires[role])
            extra.append(self._distance(wire, self.crew_c) / scale)
        return np.concatenate(
            [base, np.asarray(extra, dtype=np.float32)]
        )

    def _info(self) -> dict[str, Any]:
        info = super()._info()
        info["crew_c"] = self.crew_c
        for role in self.roles:
            wire = self._wire(self.role_wires[role])
            info["roles"][role]["distance_c"] = self._distance(
                wire, self.crew_c
            )
            info["roles"][role]["service_c"] = self._service_ticks(
                wire, self.crew_c
            )
        return info
