"""Local-view two-crew repair with a report action.

Phase 2 composes the frozen Phase 1 ``SequentialCrewEnv`` and replaces the
shared observation with per-crew local views plus budgeted, delayed reports.
The Phase 1 task and ``factory-v0.6`` are unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from fabline.env.sequential_crew import (
    N_CREWS,
    SequentialCrewConfig,
    SequentialCrewEnv,
)
from fabline.worlds.factory.config import FactoryConfig

CREW_COMM_TASK_ID = "factory.power.crew-communication.v1"
CREW_COMM_TASK_VERSION = "0.1.0"

COMM_ACTION_NAMES = (
    "north",
    "east",
    "south",
    "west",
    "wait",
    "repair",
    "report",
)
N_COMM_ACTIONS = len(COMM_ACTION_NAMES)


@dataclass(frozen=True)
class CrewCommConfig:
    visibility_radius: int = 6
    report_budget: int = 2
    report_delay: int = 1
    report_cost: float = 0.5

    def __post_init__(self) -> None:
        if self.visibility_radius <= 0:
            raise ValueError("visibility_radius must be positive")
        if self.report_budget < 0:
            raise ValueError("report_budget must be non-negative")
        if self.report_delay < 0:
            raise ValueError("report_delay must be non-negative")
        if self.report_cost < 0:
            raise ValueError("report_cost must be non-negative")


def comm_feature_names(targets: int = 5) -> tuple[str, ...]:
    names = [
        "tick_norm",
        "score_norm",
        "own_x_norm",
        "own_y_norm",
        "other_x_norm",
        "other_y_norm",
        "other_visible",
        "repaired_fraction",
        "report_budget_norm",
        "messages_used_norm",
        "clock_remaining",
    ]
    for index in range(targets):
        names.extend(
            f"target_{index}_{name}"
            for name in (
                "visible",
                "known",
                "failed",
                "dx_norm",
                "dy_norm",
                "distance_norm",
                "progress_norm",
                "report_age_norm",
                "report_failed",
            )
        )
    return tuple(names)


class CrewCommEnv:
    """Local-view repair task with budgeted, delayed team reports."""

    n_crews = N_CREWS
    n_actions_per_crew = N_COMM_ACTIONS
    n_actions = N_COMM_ACTIONS**N_CREWS
    ACTION_NAMES = COMM_ACTION_NAMES

    def __init__(
        self,
        config: FactoryConfig,
        crew: SequentialCrewConfig | None = None,
        comm: CrewCommConfig | None = None,
        *,
        seed: int = 0,
    ) -> None:
        self.base = SequentialCrewEnv(config, crew)
        self.comm = comm or CrewCommConfig()
        self._feature_names = comm_feature_names(
            self.base.crew.target_count
        )
        self.reset(seed)

    @property
    def feature_names(self) -> tuple[str, ...]:
        return self._feature_names

    @property
    def crew(self) -> SequentialCrewConfig:
        return self.base.crew

    @property
    def world(self) -> Any:
        return self.base.world

    @property
    def positions(self) -> list[tuple[int, int]]:
        return self.base.positions

    @property
    def targets(self) -> Any:
        return self.base.targets

    @property
    def seed(self) -> int:
        return self.base.seed

    @property
    def steps(self) -> int:
        return self.base.steps

    @property
    def repairs(self) -> int:
        return self.base.repairs

    def _visible(self, crew_index: int, target_index: int) -> bool:
        return (
            self.base.distance(
                self.base.positions[crew_index],
                self.base.targets[target_index],
            )
            <= self.comm.visibility_radius
        )

    def action_mask(self, crew_index: int) -> np.ndarray:
        base_mask = self.base.action_mask(crew_index)
        visible = any(
            self._visible(crew_index, index)
            for index in range(len(self.base.targets))
        )
        report_legal = (
            self.report_budget[crew_index] > 0 and visible
        )
        return np.concatenate(
            [base_mask, np.asarray([report_legal], dtype=bool)]
        )

    def joint_mask(self) -> np.ndarray:
        first = self.action_mask(0)
        second = self.action_mask(1)
        return np.asarray(
            [
                first[a] and second[b]
                for a in range(N_COMM_ACTIONS)
                for b in range(N_COMM_ACTIONS)
            ],
            dtype=bool,
        )

    def reset(self, seed: int = 0) -> tuple[tuple[np.ndarray, ...], dict[str, Any]]:
        self.base.reset(seed)
        self.report_budget = [
            self.comm.report_budget for _ in range(N_CREWS)
        ]
        self.reports: list[dict[str, Any] | None] = [
            None for _ in range(len(self.base.targets))
        ]
        self.pending: list[dict[str, Any]] = []
        self.messages_used = 0
        self.reports_delivered = 0
        self.report_cost_paid = 0.0
        return self.observe_all(), self.info()

    def _deliver_reports(self) -> None:
        remaining: list[dict[str, Any]] = []
        for message in self.pending:
            if message["deliver_at"] > self.base.steps:
                remaining.append(message)
                continue
            previous = self.reports[message["target"]]
            if previous is not None and previous["tick"] > message["tick"]:
                continue
            self.reports[message["target"]] = {
                "failed": bool(message["failed"]),
                "tick": int(message["tick"]),
                "source": int(message["source"]),
                "delivered_at": int(self.base.steps),
            }
            self.reports_delivered += 1
        self.pending = remaining

    def _report(self, crew_index: int) -> int:
        if self.report_budget[crew_index] <= 0:
            return 0
        visible = [
            index
            for index in range(len(self.base.targets))
            if self._visible(crew_index, index)
        ]
        if not visible:
            return 0
        for index in visible:
            target = self.base.targets[index]
            self.pending.append(
                {
                    "target": index,
                    "failed": bool(target.failed),
                    "tick": int(self.base.world.state.tick),
                    "source": crew_index,
                    "deliver_at": self.base.steps + self.comm.report_delay,
                }
            )
        self.report_budget[crew_index] -= 1
        self.messages_used += 1
        self.report_cost_paid += self.comm.report_cost
        return 1

    def has_pending_report(self, crew_index: int, target_index: int) -> bool:
        return any(
            message["source"] == crew_index
            and message["target"] == target_index
            for message in self.pending
        )

    def step(
        self, action: tuple[int, int] | int
    ) -> tuple[tuple[np.ndarray, ...], float, bool, bool, dict[str, Any]]:
        self._deliver_reports()
        if isinstance(action, int):
            if action < 0 or action >= self.n_actions:
                raise ValueError("joint action is outside the action space")
            first, second = divmod(action, N_COMM_ACTIONS)
        else:
            first, second = action
        for value in (first, second):
            if value < 0 or value >= N_COMM_ACTIONS:
                raise ValueError("crew action is outside the action space")
        if not self.action_mask(0)[first] or not self.action_mask(1)[second]:
            raise ValueError("joint action is masked")
        before_score = self.base.world.state.score
        repair_steps_before = self.base.repair_steps
        repairs_before = self.base.repairs
        messages_before = self.messages_used
        for crew_index, value in enumerate((first, second)):
            if value < 4:
                self.base._move(crew_index, value)
            elif value == 5:
                self.base._repair(crew_index)
            elif value == 6:
                self._report(crew_index)
        self.base.world.run_ticks(self.base.crew.decision_interval)
        reward = (
            float(self.base.world.state.score - before_score)
            + (self.base.repair_steps - repair_steps_before)
            * self.base.crew.progress_bonus
            + (self.base.repairs - repairs_before)
            * self.base.crew.repair_bonus
            - (self.messages_used - messages_before)
            * self.comm.report_cost
        )
        self.base.total_reward += reward
        self.base.last_reward = reward
        self.base.last_action = (first, second)
        self.base.steps += 1
        return (
            self.observe_all(),
            reward,
            False,
            self.base.world.done,
            self.info(),
        )

    def _target_features(
        self, crew_index: int, target_index: int
    ) -> list[float]:
        state = self.base.world.state
        target = self.base.targets[target_index]
        position = self.base.positions[crew_index]
        visible = self._visible(crew_index, target_index)
        report = self.reports[target_index]
        known = visible or report is not None
        if visible:
            endpoint = min(
                self.base._endpoints(target),
                key=lambda cell: abs(cell[0] - position[0])
                + abs(cell[1] - position[1]),
            )
            return [
                1.0,
                1.0,
                1.0 if target.failed else 0.0,
                (endpoint[0] - position[0])
                / max(1, state.width - 1),
                (endpoint[1] - position[1])
                / max(1, state.height - 1),
                self.base.distance(position, target)
                / max(1, state.width + state.height),
                self.base.repair_progress[target_index]
                / max(1, self.base.crew.repair_ticks),
                0.0,
                0.0,
            ]
        age = 0.0
        report_failed = 0.0
        if report is not None:
            age = (
                state.tick - int(report["tick"])
            ) / max(1, self.base.crew.episode_ticks)
            report_failed = 1.0 if report["failed"] else 0.0
        return [
            0.0,
            1.0 if known else 0.0,
            1.0 if (report is not None and report["failed"]) else 0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            age,
            report_failed,
        ]

    def observe_crew(self, crew_index: int) -> np.ndarray:
        state = self.base.world.state
        own = self.base.positions[crew_index]
        other = self.base.positions[1 - crew_index]
        other_visible = (
            abs(other[0] - own[0]) + abs(other[1] - own[1])
            <= self.comm.visibility_radius
        )
        values: list[float] = [
            state.tick / max(1, self.base.crew.episode_ticks),
            state.score / 500.0,
            own[0] / max(1, state.width - 1),
            own[1] / max(1, state.height - 1),
            (other[0] / max(1, state.width - 1)) if other_visible else 0.0,
            (other[1] / max(1, state.height - 1)) if other_visible else 0.0,
            1.0 if other_visible else 0.0,
            self.base.repairs / max(1, len(self.base.targets)),
            self.report_budget[crew_index]
            / max(1, self.comm.report_budget),
            self.messages_used
            / max(1, self.comm.report_budget * N_CREWS),
            (self.base.crew.episode_ticks - state.tick)
            / max(1, self.base.crew.episode_ticks),
        ]
        for target_index in range(len(self.base.targets)):
            values.extend(self._target_features(crew_index, target_index))
        return np.asarray(values, dtype=np.float32)

    def observe_all(self) -> tuple[np.ndarray, ...]:
        return tuple(
            self.observe_crew(crew_index)
            for crew_index in range(N_CREWS)
        )

    def observe(self) -> np.ndarray:
        """Shared Phase 1 observation, for a full-information baseline."""
        return self.base.observe()

    def info(self) -> dict[str, Any]:
        info = self.base.info()
        info.update(
            {
                "messages_used": self.messages_used,
                "reports_delivered": self.reports_delivered,
                "report_budget": list(self.report_budget),
                "report_cost_paid": self.report_cost_paid,
                "reports": [
                    None if report is None else dict(report)
                    for report in self.reports
                ],
            }
        )
        return info

    def replay_state(self) -> dict[str, Any]:
        state = self.base.replay_state()
        state["comm"] = {
            "report_budget": list(self.report_budget),
            "reports": [
                None if report is None else dict(report)
                for report in self.reports
            ],
            "pending": [dict(message) for message in self.pending],
            "messages_used": self.messages_used,
            "reports_delivered": self.reports_delivered,
        }
        return state
