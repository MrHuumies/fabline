"""Per-crew visibility and shared-report wrapper for crew tasks."""

from __future__ import annotations

from typing import Any

import numpy as np

from fabline.env.multi_crew import (
    CHOICES,
    MULTI_CREW_FEATURES,
    ROLES,
    MultiCrewEnv,
)


class VisibilityEnv:
    """Wrap a crew env with a visibility radius and report-age memory."""

    def __init__(
        self,
        env: MultiCrewEnv,
        *,
        radius: int,
        report_age: int = 0,
    ) -> None:
        if radius <= 0:
            raise ValueError("visibility radius must be positive")
        if report_age < 0:
            raise ValueError("report age must be non-negative")
        self.env = env
        self.radius = radius
        self.report_age = report_age
        self.n_actions = env.n_actions
        self.memory: dict[str, dict[str, Any]] = {}
        self._base_len = len(MULTI_CREW_FEATURES)

    def _wire(self, role: str) -> Any:
        return self.env._wire(self.env.role_wires[role])

    def _visible(self, role: str, crew: str) -> bool:
        wire = self._wire(role)
        position = self.env.crew_a if crew == "a" else self.env.crew_b
        return self.env._distance(wire, position) <= self.radius

    def _capture(self, info: dict[str, Any]) -> None:
        tick = int(info["tick"])
        for role in self.env.roles:
            if self._visible(role, "a") or self._visible(role, "b"):
                self.memory[role] = {
                    "tick": tick,
                    "data": dict(info["roles"][role]),
                }

    def _role_data(
        self,
        info: dict[str, Any],
        role: str,
    ) -> dict[str, Any]:
        visible_a = self._visible(role, "a")
        visible_b = self._visible(role, "b")
        tick = int(info["tick"])
        memory = self.memory.get(role)
        age = None if memory is None else tick - int(memory["tick"])
        if visible_a or visible_b:
            data = dict(info["roles"][role])
            source = "current"
        elif memory is not None and age is not None and age <= self.report_age:
            data = dict(memory["data"])
            source = "report"
        else:
            data = {
                "wire_id": info["roles"][role]["wire_id"],
                "outage": 0,
                "degraded": False,
                "failed": False,
                "deadline": 0,
                "distance_a": 0,
                "distance_b": 0,
                "service_a": 0,
                "service_b": 0,
            }
            source = "unknown"
        data["visible_a"] = visible_a
        data["visible_b"] = visible_b
        data["known"] = source != "unknown"
        data["report_age"] = 0 if age is None else age
        data["source"] = source
        return data

    def _mask_info(self, info: dict[str, Any]) -> dict[str, Any]:
        if self.radius >= 999:
            return info
        masked = dict(info)
        masked["roles"] = {
            role: self._role_data(info, role) for role in self.env.roles
        }
        return masked

    def _mask_observation(
        self,
        observation: np.ndarray,
        info: dict[str, Any],
    ) -> np.ndarray:
        if self.radius >= 999:
            return observation
        state = self.env.world.state
        consumers = max(1, len(self.env._consumers()))
        episode = max(1, int(self.env.multi.episode_ticks))
        scale = max(1, state.width + state.height)
        values: list[float] = [
            state.tick / episode,
            state.score / 500.0,
            self.env.crew_a[0] / max(1, state.width - 1),
            self.env.crew_a[1] / max(1, state.height - 1),
            self.env.crew_b[0] / max(1, state.width - 1),
            self.env.crew_b[1] / max(1, state.height - 1),
        ]
        for role in self.env.roles:
            data = self._role_data(info, role)
            state_value = (
                1.0
                if data["failed"]
                else 0.5 if data["degraded"] else 0.0
            )
            deadline = (
                max(0, int(data["deadline"]) - state.tick) / episode
                if data["degraded"]
                else 0.0
            )
            values.extend(
                [
                    float(data["outage"]) / consumers,
                    state_value,
                    deadline,
                    float(data["distance_a"]) / scale,
                    float(data["distance_b"]) / scale,
                ]
            )
        extra = observation[self._base_len :]
        return np.concatenate(
            [np.asarray(values, dtype=np.float32), extra]
        )

    def _known(self, role: str, crew: str) -> bool:
        if self._visible(role, crew):
            return True
        memory = self.memory.get(role)
        if memory is None:
            return False
        age = int(self.env.world.state.tick) - int(memory["tick"])
        return age <= self.report_age

    def action_mask(self) -> np.ndarray:
        mask = self.env.action_mask().copy()
        if self.radius >= 999:
            return mask
        for action in np.flatnonzero(mask):
            first, second = divmod(int(action), CHOICES)
            if first > 0 and not self._known(ROLES[first - 1], "a"):
                mask[action] = False
            if second > 0 and not self._known(ROLES[second - 1], "b"):
                mask[action] = False
        return mask

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        observation, info = self.env.reset(seed)
        self.memory = {}
        self._capture(info)
        return (
            self._mask_observation(observation, info),
            self._mask_info(info),
        )

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        observation, reward, terminated, truncated, info = self.env.step(
            action
        )
        self._capture(info)
        return (
            self._mask_observation(observation, info),
            reward,
            terminated,
            truncated,
            self._mask_info(info),
        )
