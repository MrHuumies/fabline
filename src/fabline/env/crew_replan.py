"""Two-crew repair assignment with a known crew recall and replanning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from fabline.env.multi_crew import (
    CHOICES,
    MULTI_CREW_FEATURES,
    MultiCrewConfig,
    MultiCrewEnv,
)
from fabline.worlds.factory.config import FactoryConfig

CREW_REPLAN_TASK_ID = "factory.power.crew-replan.v1"
CREW_REPLAN_TASK_VERSION = "0.1.0"

CREW_REPLAN_FEATURES = (
    *MULTI_CREW_FEATURES,
    "phase",
    "crew_b_available",
    "recall_remaining_norm",
    "orphaned_role_norm",
)


@dataclass(frozen=True)
class CrewReplanConfig(MultiCrewConfig):
    """Two-crew task plus the tick at which crew B is recalled."""

    recall_tick: int = 100
    job_failure_tick: int = 0
    replan_jobs: int = 1
    role_mode: str = "loop"
    replan_mode: str = "orphan"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.warning_tick < self.recall_tick < self.episode_ticks:
            raise ValueError("recall must follow the warning and precede the end")
        if self.job_failure_tick and not (
            self.warning_tick < self.job_failure_tick < self.episode_ticks
        ):
            raise ValueError("job failure must follow the warning and precede end")
        if self.replan_jobs <= 0:
            raise ValueError("replan_jobs must be positive")
        if self.role_mode not in {"loop", "three_positive"}:
            raise ValueError("role_mode must be loop or three_positive")
        if self.replan_mode not in {"orphan", "all_positive"}:
            raise ValueError("replan_mode must be orphan or all_positive")


class CrewReplanEnv(MultiCrewEnv):
    """One initial pair assignment, then a second dispatch for crew A."""

    def __init__(
        self,
        config: FactoryConfig,
        replan: CrewReplanConfig | None = None,
    ) -> None:
        self.replan = replan or CrewReplanConfig()
        super().__init__(config, self.replan)

    def _select_roles(
        self,
        outages: dict[int, int],
    ) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        if self.replan.role_mode != "three_positive":
            return super()._select_roles(outages)
        positive = sorted(
            (
                (size, wire_id)
                for wire_id, size in outages.items()
                if size > 0
            ),
            key=lambda item: (item[0], item[1]),
        )
        if len(positive) < 3:
            raise RuntimeError("triage task needs three positive wires")
        small = positive[0]
        large = positive[-1]
        middle = [
            item for item in positive
            if item[1] not in {small[1], large[1]}
        ]
        if not middle:
            raise RuntimeError("triage task needs three distinct wires")
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

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.phase = "initial"
        self.recall_tick = self.replan.recall_tick
        self.crew_b_available = True
        self.orphaned_role: str | None = None
        self.orphaned_roles: set[str] = set()
        self.job_failure_done = False
        self.replan_jobs_done = 0
        self.b_aborted = 0
        self.initial_action = -1
        self.replan_action = -1
        _, _ = super().reset(seed)
        self.score_start = self.world.state.score
        return self._observation(), self._info()

    def _remaining_targets(self) -> list[str]:
        if self.replan.replan_mode == "all_positive":
            return [
                role
                for role in self.roles
                if self.role_outages[role] > 0
                and (
                    self._wire(self.role_wires[role]).degraded
                    or self._wire(self.role_wires[role]).failed
                )
            ]
        return [
            role for role in self.orphaned_roles
            if self.role_outages[role] > 0
        ]

    def action_mask(self) -> np.ndarray:
        if self.phase == "replan":
            mask = np.zeros(self.n_actions, dtype=bool)
            mask[0] = True
            for role in self._remaining_targets():
                choice = self.roles.index(role) + 1
                mask[choice * CHOICES] = True
            return mask
        return super().action_mask()

    def _mark_orphan(self, role: str) -> None:
        self.orphaned_roles.add(role)
        if self.orphaned_role is None:
            self.orphaned_role = role

    def _run_jobs(
        self,
        jobs: list[dict[str, Any]],
        *,
        handle_recall: bool,
    ) -> None:
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
                    if job["crew_id"] == "b":
                        self.b_aborted += 1
                    self._mark_orphan(job["role"])
                else:
                    self.world.repair_wire(wire.id)
                    endpoint = self._nearest_endpoint(wire, job["crew"])
                    if job["crew_id"] == "a":
                        self.crew_a = endpoint
                    else:
                        self.crew_b = endpoint
                    if job["preventive"]:
                        self.prevented += 1
                remaining.remove(job)
            if (
                handle_recall
                and self.replan.job_failure_tick
                and not self.job_failure_done
                and self.world.state.tick >= self.replan.job_failure_tick
            ):
                self.job_failure_done = True
                for job in list(remaining):
                    remaining.remove(job)
                    self.aborted += 1
                    if job["crew_id"] == "b":
                        self.b_aborted += 1
                    self._mark_orphan(job["role"])
            if (
                handle_recall
                and self.crew_b_available
                and self.world.state.tick >= self.recall_tick
            ):
                self.crew_b_available = False
                for job in list(remaining):
                    if job["crew_id"] == "b":
                        remaining.remove(job)
                        self.aborted += 1
                        self.b_aborted += 1
                        self._mark_orphan(job["role"])

    def _finish_initial(
        self,
        jobs: list[dict[str, Any]],
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        self.repairs += len(jobs)
        for job in jobs:
            self.travel_ticks += (
                job["distance"] * self.multi.travel_ticks_per_cell
            )
        self._run_jobs(jobs, handle_recall=True)
        if not self.world.done and self.crew_b_available:
            self._advance(max(0, self.recall_tick - self.world.state.tick))
            if self.world.state.tick >= self.recall_tick:
                self.crew_b_available = False
        if self.world.done:
            self.steps += 1
            reward = float(self.world.state.score - self.score_start)
            info = self._info()
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
        info["jobs"] = [
            {
                "role": job["role"],
                "crew": job["crew_id"],
                "distance": job["distance"],
                "duration": job["duration"],
            }
            for job in jobs
        ]
        info["reward"] = 0.0
        return self._observation(), 0.0, False, False, info

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
        first, second = divmod(action, CHOICES)
        jobs: list[dict[str, Any]] = []
        for choice, crew, crew_id in (
            (first, self.crew_a, "a"),
            (second, self.crew_b, "b"),
        ):
            job = self._job(choice, crew)
            if job is not None:
                job["crew_id"] = crew_id
                jobs.append(job)
        self.initial_action = action
        self.last_action = self.ACTION_NAMES[action]
        return self._finish_initial(jobs)

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
        choice = action // CHOICES
        self.replan_action = action
        self.last_action = self.ACTION_NAMES[action]
        jobs: list[dict[str, Any]] = []
        job = self._job(choice, self.crew_a)
        if job is not None:
            job["crew_id"] = "a"
            job["preventive"] = False
            jobs.append(job)
            self.repairs += 1
            self.travel_ticks += (
                job["distance"] * self.multi.travel_ticks_per_cell
            )
            self._run_jobs(jobs, handle_recall=False)
        if job is not None:
            self.orphaned_roles.discard(job["role"])
            self.replan_jobs_done += 1
        remaining = self._remaining_targets()
        if (
            job is not None
            and remaining
            and self.replan_jobs_done < self.replan.replan_jobs
            and not self.world.done
            and self.world.state.tick < self.multi.episode_ticks
        ):
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
                (
                    (self.roles.index(self.orphaned_role) + 1)
                    / len(self.roles)
                    if self.orphaned_role is not None
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
                "orphaned_role": self.orphaned_role,
                "orphaned_roles": sorted(self.orphaned_roles),
                "b_aborted": self.b_aborted,
                "initial_action": self.initial_action,
                "replan_action": self.replan_action,
            }
        )
        return info
