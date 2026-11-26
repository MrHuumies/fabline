from __future__ import annotations

import numpy as np
import pytest

from fabline.env.production_mix import ProductionMixConfig, ProductionMixEnv
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.production import ProductionConfig
from fabline.worlds.factory.state import Item
from fabline.worlds.factory.world import FactoryWorld


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )


def test_production_config_validation() -> None:
    with pytest.raises(ValueError):
        ProductionConfig(component_ticks=0)
    with pytest.raises(ValueError):
        ProductionConfig(component_ingot_cost=0)
    with pytest.raises(ValueError):
        ProductionConfig(component_score=-1)


def test_default_state_hash_is_unchanged() -> None:
    world = FactoryWorld(_config())
    world.reset(0, SCENARIOS["gear"])
    world.run_ticks(50)
    assert (
        world.state_hash()
        == "4f333f4099d6bb2a5a2dfa5078c431ceb22b50d0a0eea788411260763cc59c27"
    )


def test_component_recipe_produces_deliverable() -> None:
    world = FactoryWorld(
        _config(), production=ProductionConfig(enabled=True)
    )
    world.reset(0, SCENARIOS["gear"])
    assert Item.COMPONENT in world.state.delivered
    world.state.production_recipe = 1
    world.run_ticks(200)
    assert world.state.delivered[Item.COMPONENT] > 0
    assert world.state.score > 0


def test_production_mix_env_runs() -> None:
    env = ProductionMixEnv(
        _config(), ProductionMixConfig(episode_ticks=200)
    )
    observation, info = env.reset(0)
    assert observation.shape == (9,)
    assert info["score"] == 0
    observation, reward, terminated, truncated, info = env.step(1)
    assert observation.shape == (9,)
    assert np.isfinite(reward)
    assert not terminated and not truncated
    assert info["production_recipe"] == 1
