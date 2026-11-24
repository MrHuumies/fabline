from __future__ import annotations

import pytest

from fabline.env.contract_board import (
    BOARD_FEATURES,
    ContractBoardConfig,
    ContractBoardEnv,
)
from fabline.env.recipe import RECIPE_FEATURES
from fabline.worlds.factory.config import FactoryConfig


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )


def test_contract_board_choose_then_control() -> None:
    env = ContractBoardEnv(_config())
    observation, info = env.reset(0)
    assert observation.shape == (len(RECIPE_FEATURES) + len(BOARD_FEATURES),)
    assert info["phase"] == "choose"
    assert info["selected"] is None
    observation, reward, terminated, truncated, info = env.step(0)
    assert info["phase"] == "control"
    assert info["selected"] == 0
    assert reward == 0.0
    assert not terminated and not truncated
    assert env.action_mask().tolist() == [True, True, False]
    done = False
    total = 0.0
    while not done:
        observation, reward, terminated, truncated, info = env.step(0)
        total += reward
        done = terminated or truncated
    assert info["selected"] == 0
    if info["success"]:
        assert total == info["contract_reward"]
    else:
        assert total == 0.0


def test_contract_board_validation() -> None:
    with pytest.raises(ValueError):
        ContractBoardConfig(boards=())
    with pytest.raises(ValueError):
        ContractBoardConfig(boards=(((12, 250, 60),),))
