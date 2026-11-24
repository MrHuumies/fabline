from __future__ import annotations

import numpy as np

from fabline.env.crew_decentralized import DecentralizedVisibilityEnv
from fabline.env.crew_replan import CrewReplanConfig
from fabline.harness.crew_decentralized import (
    CompactIndependentQPolicy,
    IndependentQEnsemblePolicy,
    LocalGreedyPolicy,
    evaluate_crew_policy,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=48,
        height=24,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=48,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )


def _replan() -> CrewReplanConfig:
    return CrewReplanConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=90,
        small_failure_tick=110,
        large_failure_tick=130,
        recall_tick=100,
        success_score=600,
        randomize_crew_b=True,
        crew_b_min_distance=8,
        scenario="spread_gear",
        power=PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=48,
            generator_radius=8,
            wire_redundancy=2,
        ),
    )


def test_decentralized_masks_and_step() -> None:
    env = DecentralizedVisibilityEnv(_config(), _replan(), radius=16)
    info = env.reset(0)
    assert info["tick"] == 0
    assert env.agent_mask("a", info).tolist() == [True, False, False, False]
    assert env.agent_mask("b", info).tolist() == [True, False, False, False]
    info, _, terminated, truncated, _ = env.step({"a": 0, "b": 0})
    assert info["tick"] == 10
    assert not terminated and not truncated


def test_local_greedy_policy_runs() -> None:
    env = DecentralizedVisibilityEnv(_config(), _replan(), radius=16)
    metrics = evaluate_crew_policy(env, LocalGreedyPolicy(), seed=0)
    assert metrics.mean_score >= 0.0
    assert 0.0 <= metrics.success_rate <= 1.0
    assert np.isfinite(metrics.mean_score)


def test_compact_q_key_is_relative() -> None:
    env = DecentralizedVisibilityEnv(_config(), _replan(), radius=16)
    info = env.reset(0)
    policy = CompactIndependentQPolicy()
    key = policy._key("a", env.agent_info("a", info))
    assert len(key) == 16
    assert key[0] == 0
    assert key[1] == 1
    assert key[3] == 0

    replan = dict(info)
    replan["phase"] = "replan"
    replan["tick"] = 150
    key = policy._key("a", env.agent_info("a", replan))
    assert key[0] == 1
    assert key[3] == 2


def test_compact_q_trains_and_acts() -> None:
    env = DecentralizedVisibilityEnv(_config(), _replan(), radius=16)
    policy = CompactIndependentQPolicy()
    policy.train(env, episodes=2, seed=0, train_seed_start=60000)
    metrics = evaluate_crew_policy(env, policy, seed=0)
    assert np.isfinite(metrics.mean_score)
    assert 0.0 <= metrics.success_rate <= 1.0


def test_compact_q_ensemble_acts() -> None:
    env = DecentralizedVisibilityEnv(_config(), _replan(), radius=16)
    info = env.reset(0)
    ensemble = IndependentQEnsemblePolicy(
        [CompactIndependentQPolicy(), CompactIndependentQPolicy()]
    )
    for crew in ("a", "b"):
        action = ensemble.act(
            crew,
            env.agent_info(crew, info),
            env.agent_mask(crew, info),
        )
        assert 0 <= action < 4
