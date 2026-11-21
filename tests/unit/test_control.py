from __future__ import annotations

import numpy as np
import pytest

from fabline.env.control import ControlConfig, ControlEnv, MacroAction
from fabline.harness.control import (
    BehaviorCloningPolicy,
    RandomControlPolicy,
    ScriptedControlPolicy,
    TabularQPolicy,
    evaluate_control_policies,
    evaluate_policy,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import EntityType, TileType


@pytest.fixture
def control_config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=300,
        rock_density=0.0,
        starter_line=False,
    )


@pytest.fixture
def control_env(control_config) -> ControlEnv:
    return ControlEnv(control_config, ControlConfig(episode_ticks=300))


def test_reset_builds_a_clean_path(control_env) -> None:
    observation, info = control_env.reset(0)
    assert observation.shape == (49,)
    assert info["path_index"] == 0
    assert info["path_types"] == [0, 0, 0, 0, 0, 0]
    assert control_env.world.state.entity_at(1, 4) is None
    assert control_env.world.state.tile_at(1, 4) is TileType.ORE
    assert control_env.world.state.tile_at(7, 4) is TileType.DEPOT
    assert control_env.world.state.entity_at(7, 4).type is EntityType.DEPOT
    mask = control_env.action_mask()
    assert mask[MacroAction.NOOP]
    assert mask[MacroAction.BUILD_MINER]
    assert not mask[MacroAction.BUILD_BELT]
    assert not mask[MacroAction.REMOVE]


def test_scripted_policy_solves(control_env) -> None:
    metrics = evaluate_policy(
        control_env,
        ScriptedControlPolicy(),
        episodes=2,
        seed=0,
    )
    assert metrics.success_rate == 1.0
    assert metrics.path_complete_rate == 1.0
    assert metrics.mean_score > 0


def test_random_policy_is_worse_than_scripted(control_env) -> None:
    scripted = evaluate_policy(
        control_env,
        ScriptedControlPolicy(),
        episodes=3,
        seed=0,
    )
    random_policy = evaluate_policy(
        control_env,
        RandomControlPolicy(seed=0),
        episodes=3,
        seed=0,
    )
    assert random_policy.mean_score < scripted.mean_score


def test_mask_after_build_and_remove(control_env) -> None:
    observation, info = control_env.reset(0)
    assert not control_env.action_mask()[MacroAction.REMOVE]
    observation, _, _, _, info = control_env.step(MacroAction.BUILD_MINER)
    assert info["path_index"] == 1
    mask = control_env.action_mask()
    assert mask[MacroAction.BUILD_BELT]
    assert mask[MacroAction.BUILD_FURNACE]
    assert mask[MacroAction.BUILD_ASSEMBLER]
    assert mask[MacroAction.REMOVE]
    observation, _, _, _, info = control_env.step(MacroAction.REMOVE)
    assert info["path_index"] == 0


def test_illegal_action_advances_without_mutation(control_env) -> None:
    control_env.reset(0)
    before = control_env.world.state_hash()
    observation, reward, _, _, info = control_env.step(MacroAction.BUILD_BELT)
    assert info["illegal"] is True
    assert control_env.world.state.tick == control_env.control.decision_interval
    assert len(control_env.world.state.entities) == 1
    assert 1 in control_env.world.state.entities
    assert before != control_env.world.state_hash()
    assert reward < 0


def test_control_is_deterministic(control_env) -> None:
    def run() -> tuple[np.ndarray, int, str]:
        observation, _ = control_env.reset(0)
        for action in (
            MacroAction.BUILD_MINER,
            MacroAction.BUILD_BELT,
            MacroAction.BUILD_FURNACE,
            MacroAction.BUILD_BELT,
            MacroAction.BUILD_ASSEMBLER,
            MacroAction.BUILD_BELT,
        ):
            observation, _, _, _, info = control_env.step(action)
        return observation, info["score"], control_env.world.state_hash()

    first_obs, first_score, first_hash = run()
    second_obs, second_score, second_hash = run()
    assert np.array_equal(first_obs, second_obs)
    assert first_score == second_score
    assert first_hash == second_hash


def test_behavior_cloning_solves(control_env) -> None:
    policy = BehaviorCloningPolicy(seed=0)
    policy.collect(control_env, episodes=20, seed=0)
    metrics = evaluate_policy(control_env, policy, episodes=2, seed=0)
    assert metrics.success_rate == 1.0


def test_tabular_q_learns(control_env) -> None:
    policy = TabularQPolicy()
    policy.train(control_env, episodes=200, seed=0)
    metrics = evaluate_policy(control_env, policy, episodes=2, seed=0)
    assert metrics.success_rate == 1.0


def test_evaluate_control_policies(control_config) -> None:
    results = evaluate_control_policies(
        control_config,
        ControlConfig(episode_ticks=300),
        episodes=1,
        train_episodes=50,
        seeds=(0,),
    )
    assert set(results) == {"scripted", "random", "tabular_q", "behavior_cloning"}
    assert results["scripted"]["success_rate"] == 1.0
    assert "mean_score" in results["random"]
