"""Per-crew decentralized actions on the private-view triage task."""

from __future__ import annotations

from typing import Any

import numpy as np

from fabline.env.crew_replan import CrewReplanConfig, CrewReplanEnv
from fabline.env.crew_visibility import PrivateVisibilityEnv
from fabline.env.multi_crew import ROLES

DECENTRALIZED_TASK_ID = "factory.multiagent.decentralized.v1"
DECENTRALIZED_TASK_VERSION = "0.1.0"


class DecentralizedVisibilityEnv:
    """Expose separate A/B choices over a private radius-16 view."""

    def __init__(
        self,
        config: Any,
        replan: CrewReplanConfig,
        *,
        radius: int = 16,
    ) -> None:
        self.base = CrewReplanEnv(config, replan)
        self.env = PrivateVisibilityEnv(self.base, radius=radius)
        self.radius = radius
        self.n_actions = 4
        self.reset(0)

    def reset(self, seed: int = 0) -> dict[str, Any]:
        _, info = self.env.reset(seed)
        return info

    def agent_info(self, crew: str, info: dict[str, Any]) -> dict[str, Any]:
        local = dict(info)
        local["roles"] = info["crew_roles"][crew]
        local["crew"] = crew
        return local

    def agent_mask(self, crew: str, info: dict[str, Any]) -> np.ndarray:
        mask = np.zeros(4, dtype=bool)
        mask[0] = True
        if info["tick"] < self.base.replan.warning_tick:
            return mask
        if info["phase"] == "replan" and crew == "b":
            return mask
        roles = info["crew_roles"][crew]
        for index, role in enumerate(ROLES):
            data = roles[role]
            if not data["known"] or data["outage"] <= 0:
                continue
            if info["phase"] == "initial":
                if data["degraded"]:
                    mask[index + 1] = True
            elif data["degraded"] or data["failed"]:
                mask[index + 1] = True
        return mask

    def step(
        self,
        choices: dict[str, int],
    ) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        a = int(choices["a"])
        b = int(choices["b"])
        if a < 0 or a > 3 or b < 0 or b > 3:
            raise ValueError("crew choice must be in 0..3")
        joint = a * 4 + b
        _, reward, terminated, truncated, info = self.env.step(joint)
        return info, reward, terminated, truncated, info
