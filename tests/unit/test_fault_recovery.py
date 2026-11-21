from __future__ import annotations

from fabline.env.fault_recovery import FaultRecoveryConfig, FaultRecoveryEnv
from fabline.harness.fault_recovery import (
    NoopPolicy,
    RepairNowPolicy,
    TabularQRecoveryPolicy,
    evaluate_policy,
    run_fault_recovery,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig


def _setup() -> tuple[FactoryConfig, FaultConfig, FaultRecoveryConfig]:
    config = FactoryConfig(
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
    faults = FaultConfig(
        enabled=True,
        wear_per_craft=1,
        fault_threshold=5,
        repair_ticks=10,
    )
    recovery = FaultRecoveryConfig(
        episode_ticks=500,
        decision_interval=10,
        repair_cost=1.0,
        success_score=250,
    )
    return config, faults, recovery


def test_repair_action_in_recovery_env() -> None:
    config, faults, recovery = _setup()
    env = FaultRecoveryEnv(config, recovery, faults)
    observation, info = env.reset(0)
    assert observation.shape == (13,)
    assert env.action_mask().tolist() == [True, False]

    while not env.action_mask()[1]:
        observation, _, terminated, truncated, info = env.step(0)
        assert not (terminated or truncated)
    assert info["faulted_count"] >= 1

    observation, reward, terminated, truncated, info = env.step(1)
    assert info["repairs"] == 1
    assert info["last_action"] == "repair"
    assert reward < info["score"]  # score delta minus the repair cost
    assert not (terminated or truncated)


def test_repair_now_beats_noop() -> None:
    config, faults, recovery = _setup()
    env = FaultRecoveryEnv(config, recovery, faults)
    noop = evaluate_policy(env, NoopPolicy(), episodes=2, seed=0)
    repair = evaluate_policy(env, RepairNowPolicy(), episodes=2, seed=0)
    assert repair.mean_score > noop.mean_score
    assert repair.mean_repairs > 0


def test_tabular_q_and_runner() -> None:
    config, faults, recovery = _setup()
    env = FaultRecoveryEnv(config, recovery, faults)
    policy = TabularQRecoveryPolicy()
    policy.train(env, episodes=20, seed=0)
    metrics = evaluate_policy(env, policy, episodes=1, seed=0)
    assert metrics.mean_score >= 0

    results = run_fault_recovery(
        config,
        faults,
        recovery,
        episodes=1,
        train_episodes=10,
        seeds=(0,),
    )
    assert set(results) == {"noop", "repair_now", "random", "tabular_q"}
    assert results["repair_now"]["mean_score"] > results["noop"]["mean_score"]
