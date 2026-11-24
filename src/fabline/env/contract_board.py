"""Seeded gear-contract board with recipe control.

The agent first chooses one of three contracts, then controls the fast/slow
recipe. The board is seeded; the best contract changes across episodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.env.recipe import RecipeEnv, RecipeEnvConfig
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.recipe import RecipeConfig
from fabline.worlds.factory.state import Item

CONTRACT_BOARD_TASK_ID = "factory.production.contract-board.v1"
CONTRACT_BOARD_TASK_VERSION = "0.1.0"

BOARD_FEATURES = (
    "phase",
    "selected_0",
    "selected_1",
    "selected_2",
    "target_norm",
    "deadline_norm",
    "reward_norm",
    "delivered_norm",
    "remaining_target_norm",
    "remaining_time_norm",
    "contract0_target_norm",
    "contract0_deadline_norm",
    "contract0_reward_norm",
    "contract1_target_norm",
    "contract1_deadline_norm",
    "contract1_reward_norm",
    "contract2_target_norm",
    "contract2_deadline_norm",
    "contract2_reward_norm",
)

DEFAULT_BOARDS = (
    ((14, 250, 60), (20, 350, 100), (33, 500, 150)),
    ((16, 200, 50), (18, 350, 90), (30, 500, 150)),
    ((14, 250, 60), (24, 350, 100), (34, 500, 150)),
)


@dataclass(frozen=True)
class ContractBoardConfig:
    boards: tuple[tuple[tuple[int, int, int], ...], ...] = DEFAULT_BOARDS
    recipe: RecipeConfig = field(
        default_factory=lambda: RecipeConfig(enabled=True)
    )
    power: PowerConfig = field(default_factory=PowerConfig)
    initial_input_max: int = 6

    def __post_init__(self) -> None:
        if not self.boards:
            raise ValueError("boards must be non-empty")
        if any(len(board) != 3 for board in self.boards):
            raise ValueError("each board needs three contracts")
        for board in self.boards:
            for target, deadline, reward in board:
                if target <= 0 or deadline <= 0 or reward <= 0:
                    raise ValueError("contract values must be positive")


class ContractBoardEnv:
    """Choose one contract, then control the recipe."""

    n_actions = 3
    ACTION_NAMES = ("contract0", "contract1", "contract2")

    def __init__(
        self,
        config: FactoryConfig,
        board: ContractBoardConfig | None = None,
    ) -> None:
        self.config = config
        self.board = board or ContractBoardConfig()
        self.recipe_env = RecipeEnv(
            config,
            RecipeEnvConfig(
                episode_ticks=config.ticks_per_episode,
                decision_interval=config.decision_interval,
                scenario="gear",
                success_score=0,
                initial_input_max=self.board.initial_input_max,
                recipe=self.board.recipe,
                power=self.board.power,
            ),
        )
        self.reset(0)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.contracts = self.board.boards[seed % len(self.board.boards)]
        self.phase = "choose"
        self.selected: int | None = None
        self.start_delivered = 0
        observation, info = self.recipe_env.reset(seed)
        self.start_delivered = int(info["delivered_gears"])
        return self._observation(observation), self._info(info)

    def action_mask(self) -> np.ndarray:
        if self.phase == "choose":
            return np.ones(3, dtype=bool)
        mask = np.zeros(3, dtype=bool)
        mask[:2] = True
        return mask

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if self.phase == "choose":
            if action < 0 or action > 2:
                raise ValueError("contract action must be 0, 1, or 2")
            self.selected = action
            self.phase = "control"
            info = self.recipe_env._info()
            return (
                self._observation(self.recipe_env._observation()),
                0.0,
                False,
                False,
                self._info(info),
            )
        if action > 1:
            raise ValueError("recipe action must be 0 or 1")
        observation, _, terminated, truncated, info = self.recipe_env.step(action)
        delivered = self._delivered
        if self.selected is None:
            raise RuntimeError("contract must be selected before control")
        target, deadline, reward = self.contracts[self.selected]
        tick = info["tick"]
        if delivered >= target and tick <= deadline:
            done = True
            total = float(reward)
        elif tick >= deadline:
            done = True
            total = 0.0
        else:
            done = terminated or truncated
            total = 0.0
        info = self._info(info)
        info["reward"] = total
        info["delivered"] = delivered
        info["success"] = delivered >= target and tick <= deadline
        return self._observation(observation), total, done, False, info

    def _observation(self, base: np.ndarray) -> np.ndarray:
        tick = self.recipe_env.world.state.tick
        if self.selected is None:
            target = deadline = reward = 0
            selected = [0.0, 0.0, 0.0]
            delivered = 0
        else:
            target, deadline, reward = self.contracts[self.selected]
            selected = [
                1.0 if index == self.selected else 0.0
                for index in range(3)
            ]
            delivered = self._delivered
        values = [
            1.0 if self.phase == "control" else 0.0,
            *selected,
            target / 40.0,
            deadline / 500.0,
            reward / 150.0,
            min(1.0, delivered / max(1, target)),
            max(0, target - delivered) / 40.0,
            max(0, deadline - tick) / 500.0,
        ]
        for contract_target, contract_deadline, contract_reward in self.contracts:
            values.extend(
                [
                    contract_target / 40.0,
                    contract_deadline / 500.0,
                    contract_reward / 150.0,
                ]
            )
        return np.concatenate(
            [base, np.asarray(values, dtype=np.float32)]
        )

    @property
    def _delivered(self) -> int:
        return int(
            self.recipe_env.world.state.delivered.get(Item.GEAR, 0)
        ) - self.start_delivered

    def _info(self, info: dict[str, Any]) -> dict[str, Any]:
        result = dict(info)
        target = deadline = reward = 0
        if self.selected is not None:
            target, deadline, reward = self.contracts[self.selected]
        result.update(
            {
                "phase": self.phase,
                "contracts": list(self.contracts),
                "selected": self.selected,
                "contract_target": target,
                "contract_deadline": deadline,
                "contract_reward": reward,
                "delivered": self._delivered,
                "contract_success": (
                    self.selected is not None
                    and self._delivered >= target
                    and info["tick"] <= deadline
                ),
            }
        )
        return result
