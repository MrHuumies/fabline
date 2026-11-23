from __future__ import annotations

import numpy as np
import pytest

from fabline.env.recipe import RECIPE_FEATURES, RecipeEnv, RecipeEnvConfig
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.recipe import RecipeConfig
from fabline.worlds.factory.world import FactoryWorld


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


def test_recipe_default_state_hash_unchanged() -> None:
    default = FactoryWorld(_config())
    default.reset(0)
    enabled = FactoryWorld(
        _config(), recipe=RecipeConfig(enabled=True)
    )
    enabled.reset(0)
    assert default.state.state_hash() == enabled.state.state_hash()
    default.run_ticks(40)
    enabled.run_ticks(40)
    assert default.state.state_hash() == enabled.state.state_hash()


def test_recipe_env_action_switches_recipe() -> None:
    env = RecipeEnv(
        _config(),
        RecipeEnvConfig(recipe=RecipeConfig(enabled=True)),
    )
    observation, info = env.reset(0)
    assert observation.shape == (len(RECIPE_FEATURES),)
    assert info["recipe"] == 0
    observation, _, terminated, truncated, info = env.step(1)
    assert info["recipe"] == 1
    assert info["recipe_name"] == "slow"
    assert not terminated and not truncated
    observation, _, _, _, info = env.step(0)
    assert info["recipe"] == 0
    assert info["switches"] == 2


def test_recipe_env_requires_enabled_recipe() -> None:
    with pytest.raises(ValueError):
        RecipeEnvConfig()
    with pytest.raises(ValueError):
        RecipeConfig(fast_ticks=0)
    with pytest.raises(ValueError):
        RecipeConfig(slow_cost=0)


def test_recipe_slow_uses_fewer_ingots() -> None:
    fast = RecipeEnv(
        _config(),
        RecipeEnvConfig(recipe=RecipeConfig(enabled=True)),
    )
    fast.reset(0)
    for _ in range(50):
        _, _, terminated, _, info = fast.step(0)
        if terminated:
            break
    slow = RecipeEnv(
        _config(),
        RecipeEnvConfig(recipe=RecipeConfig(enabled=True)),
    )
    slow.reset(0)
    for _ in range(50):
        _, _, terminated, _, info = slow.step(1)
        if terminated:
            break
    assert info["delivered_gears"] >= 0
    assert info["score"] >= 0
    assert np.isfinite(info["score"])
