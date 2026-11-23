"""Three-crew initial assignment with a recall and A/C recovery pair."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from fabline.env.multi_crew import (
    CHOICES,
    MultiCrewConfig,
)
from fabline.env.three_crew import THREE_CREW_FEATURES, ThreeCrewEnv
from fabline.worlds.factory.config import FactoryConfig

THREE_CREW_REPLAN_TASK_ID = "factory.power.crew-three-replan.v1"
THREE_CREW_REPLAN_TASK_VERSION = "0.1.0"

THREE_CREW_REPLAN_FEATURES = (
    *THREE_CREW_FEATURES,
    "phase",
    "crew_b_available",
    "recall_remaining_norm",
)


@dataclass(frozen=True)
class ThreeCrewReplanConfig(MultiCrewConfig):
    recall_tick: int = 100

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.warning_tick < self.recall_tick < self.episode_ticks:
            raise ValueError("recall must follow warning and precede end")


class ThreeCrewReplanEnv(ThreeCrewEnv):
    """Three-crew initial assignment, then A/C recovery after B is recalled."""

    n_actions = CHOICES * CHOICES * CHOICES

    def __init__(
        self,
        config: FactoryConfig,
        replan: ThreeCrewReplanConfig | None = None,
    ) -> None:
        self.three_replan = replan or ThreeCrewReplanConfig()
        super().__init__(config, self.three_replan)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.phase = "initial"
        self.recall_tick = self.three_replan.recall_tick
        self.crew_b_available = True
        self.orphaned_roles: set[str] = set()
        self.initial_action = -1
        self.replan_action = -1
        self.b_aborted = 0
        _, _ = super().reset(seed)
        self.score_start = self.world.state.score
        return self._observation(), self._info()

    def _remaining_targets(self) -> list[str]:
        return [
            role
            for role in self.roles
            if self.role_outages[role] > 0
            and (
                self._wire(self.role_wires[role]).degraded
                or self._wire(self.role_wires[role]).failed
            )
        ]

    def action_mask(self) -> np.ndarray:
        if self.phase == "initial":
            return super().action_mask()
        mask = np.zeros(self.n_actions, dtype=bool)
        mask[0] = True
        remaining = {
            self.roles.index(role) + 1
            for role in self._remaining_targets()
        }
        for first in [0, *sorted(remaining)]:
            for second in [0, *sorted(remaining)]:
                if first > 0 and first == second:
                    continue
                action = first * 4 + second
                mask[action] = True
        return mask

    def _mark_orphan(self, role: str) -> None:
        self.orphaned_roles.add(role)

    def _run_initial_jobs(self, jobs: list[dict[str, Any]]) -> None:
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
                    self._mark_orphan(job["role"])
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
            if (
                self.crew_b_available
                and self.world.state.tick >= self.recall_tick
            ):
                self.crew_b_available = False
                for job in list(remaining):
                    if job["crew_id"] == "b":
                        remaining.remove(job)
                        self.aborted += 1
                        self.b_aborted += 1
                        self._mark_orphan(job["role"])
        if not self.world.done and self.crew_b_available:
            self._advance(
                max(0, self.recall_tick - self.world.state.tick)
            )
            if self.world.state.tick >= self.recall_tick:
                self.crew_b_available = False

    def _step_initial(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
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
        self.initial_action = action
        self.last_action = self.ACTION_NAMES[action]
        self._run_initial_jobs(jobs)
        if self.world.done:
            self.steps += 1
            reward = float(self.world.state.score - self.score_start)
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
        self.phase = "replan"
        self.steps += 1
        info = self._info()
        info["illegal"] = False
        info["reward"] = 0.0
        info["jobs"] = [
            {
                "role": job["role"],
                "crew": job["crew_id"],
                "distance": job["distance"],
                "duration": job["duration"],
            }
            for job in jobs
        ]
        return self._observation(), 0.0, False, False, info

    def _step_replan(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        legal = bool(self.action_mask()[action])
        if not legal:
            self._advance(self.multi.decision_interval)
            self.steps += 1
            info = self._info()
            info["illegal"] = True
            info["reward"] = 0.0
            return self._observation(), 0.0, self.world.done, False, info
        first = action // 4
        second = action % 4
        jobs: list[dict[str, Any]] = []
        for choice, crew, crew_id in (
            (first, self.crew_a, "a"),
            (second, self.crew_c, "c"),
        ):
            job = self._job(choice, crew)
            if job is not None:
                job["crew_id"] = crew_id
                job["preventive"] = False
                jobs.append(job)
                self.repairs += 1
                self.travel_ticks += (
                    job["distance"] * self.multi.travel_ticks_per_cell
                )
        self.replan_action = action
        self.last_action = self.ACTION_NAMES[action]
        self._run_initial_jobs(jobs)
        for job in jobs:
            self.orphaned_roles.discard(job["role"])
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

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        if self.phase == "initial":
            return self._step_initial(action)
        return self._step_replan(action)

    def _observation(self) -> np.ndarray:
        base = super()._observation()
        tick = self.world.state.tick
        extra = np.asarray(
            [
                1.0 if self.phase == "replan" else 0.0,
                1.0 if self.crew_b_available else 0.0,
                (
                    max(0, self.recall_tick - tick)
                    / self.multi.episode_ticks
                    if self.crew_b_available
                    else 0.0
                ),
            ],
            dtype=np.float32,
        )
        return np.concatenate([base, extra])

    def _info(self) -> dict[str, Any]:
        info = super()._info()
        info.update(
            {
                "phase": self.phase,
                "recall_tick": self.recall_tick,
                "crew_b_available": self.crew_b_available,
                "orphaned_roles": sorted(self.orphaned_roles),
                "initial_action": self.initial_action,
                "replan_action": self.replan_action,
                "b_aborted": self.b_aborted,
            }
        )
        return info
