"""A constrained line-building control environment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

import numpy as np

from fabline.obs.control import ControlObservation
from fabline.worlds.factory.actions import Action, ActionError, ActionOp
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import (
    Direction,
    Entity,
    EntityType,
    TileType,
    empty_delivered,
)
from fabline.worlds.factory.world import FactoryWorld

CONTROL_TASK_ID = "factory.expand.control.v1"
CONTROL_TASK_VERSION = "0.1.0"


class MacroAction(IntEnum):
    NOOP = 0
    BUILD_MINER = 1
    BUILD_BELT = 2
    BUILD_FURNACE = 3
    BUILD_ASSEMBLER = 4
    REMOVE = 5


_BUILD_MAP = {
    MacroAction.BUILD_MINER: EntityType.MINER,
    MacroAction.BUILD_BELT: EntityType.BELT,
    MacroAction.BUILD_FURNACE: EntityType.FURNACE,
    MacroAction.BUILD_ASSEMBLER: EntityType.ASSEMBLER,
}


@dataclass(frozen=True)
class ControlConfig:
    episode_ticks: int = 300
    decision_interval: int = 10
    build_penalty: float = 0.05
    success_score: int = 20
    path_start_x: int = 1
    path_y: int = 4
    path_length: int = 6
    depot_x: int = 7

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0:
            raise ValueError("episode_ticks must be positive")
        if self.decision_interval <= 0:
            raise ValueError("decision_interval must be positive")
        if self.path_length <= 0:
            raise ValueError("path_length must be positive")
        if self.depot_x != self.path_start_x + self.path_length:
            raise ValueError("depot_x must immediately follow the path")
        if self.success_score < 0:
            raise ValueError("success_score must be non-negative")


class ControlEnv:
    """Build a line on a fixed path by choosing the next entity type.

    Actions are macro actions, not raw grid coordinates. The next path tile is
    determined by the state; the agent chooses what to put there or removes the
    most recent entity to retry.
    """

    n_actions = len(MacroAction)

    def __init__(
        self,
        config: FactoryConfig,
        control: ControlConfig | None = None,
    ) -> None:
        self.config = config
        self.control = control or ControlConfig()
        if self.control.episode_ticks != config.ticks_per_episode:
            raise ValueError("control.episode_ticks must equal config.ticks_per_episode")
        if self.control.depot_x >= config.width or self.control.path_y >= config.height:
            raise ValueError("control path does not fit in the world")
        self.path = [
            (self.control.path_start_x + index, self.control.path_y)
            for index in range(self.control.path_length)
        ]
        self.depot = (self.control.depot_x, self.control.path_y)
        self.observation = ControlObservation(config, self.path)
        self.world = FactoryWorld(config)
        self.total_reward = 0.0
        self.steps = 0
        self.reset(0)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed)
        state = self.world.state
        state.tiles = [TileType.EMPTY] * (self.config.width * self.config.height)
        state.entities.clear()
        state.occupancy.clear()
        state.events.clear()
        state.delivered = empty_delivered()
        state.score = 0
        state.history.clear()
        state.next_entity_id = 2

        state.set_tile(self.path[0][0], self.path[0][1], TileType.ORE)
        state.set_tile(self.depot[0], self.depot[1], TileType.DEPOT)
        depot = Entity(
            id=1,
            type=EntityType.DEPOT,
            x=self.depot[0],
            y=self.depot[1],
        )
        state.entities[1] = depot
        state.occupancy[self.depot] = 1

        self.total_reward = 0.0
        self.steps = 0
        return self._observation(), self._info()

    def _path_entities(self) -> list[Entity | None]:
        return [self.world.state.entity_at(x, y) for x, y in self.path]

    def _next_index(self) -> int:
        for index, entity in enumerate(self._path_entities()):
            if entity is None:
                return index
        return len(self.path)

    def action_mask(self) -> np.ndarray:
        mask = np.zeros(self.n_actions, dtype=bool)
        mask[MacroAction.NOOP] = True
        next_index = self._next_index()
        if next_index < len(self.path):
            if next_index == 0:
                mask[MacroAction.BUILD_MINER] = True
            else:
                mask[MacroAction.BUILD_BELT] = True
                mask[MacroAction.BUILD_FURNACE] = True
                mask[MacroAction.BUILD_ASSEMBLER] = True
        if next_index > 0:
            mask[MacroAction.REMOVE] = True
        return mask

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        mask = self.action_mask()
        legal = bool(mask[action])
        score_before = self.world.state.score
        illegal = False

        if legal:
            try:
                self._apply_macro(MacroAction(action))
            except ActionError:
                illegal = True
        else:
            illegal = True

        self.world.run_ticks(self.control.decision_interval)
        score_after = self.world.state.score
        penalty = self.control.build_penalty if action != MacroAction.NOOP else 0.0
        if illegal:
            penalty += self.control.build_penalty
        reward = float(score_after - score_before) - penalty
        self.total_reward += reward
        self.steps += 1

        terminated = self.world.done
        info = self._info()
        info["illegal"] = illegal
        info["score_delta"] = score_after - score_before
        return self._observation(), reward, terminated, False, info

    def _apply_macro(self, action: MacroAction) -> None:
        next_index = self._next_index()
        if action is MacroAction.NOOP:
            return
        if action is MacroAction.REMOVE:
            if next_index == 0:
                raise ActionError("empty_path", "nothing to remove")
            x, y = self.path[next_index - 1]
            self.world.apply_action(Action(ActionOp.REMOVE, x=x, y=y))
            return
        entity_type = _BUILD_MAP[action]
        if next_index >= len(self.path):
            raise ActionError("path_complete", "the path is already full")
        x, y = self.path[next_index]
        self.world.apply_action(
            Action(
                ActionOp.BUILD,
                entity=entity_type,
                x=x,
                y=y,
                direction=Direction.EAST,
            )
        )

    def _observation(self) -> np.ndarray:
        return self.observation.observe(self.world.state)

    def _info(self) -> dict[str, Any]:
        entities = self._path_entities()
        path_types = [
            0 if entity is None else int(entity.type) for entity in entities
        ]
        next_index = self._next_index()
        return {
            "path_index": next_index,
            "path_types": path_types,
            "path_complete": next_index == len(self.path),
            "score": self.world.state.score,
            "tick": self.world.state.tick,
            "total_reward": self.total_reward,
            "success": self.world.state.score >= self.control.success_score,
        }
