from __future__ import annotations

from fabline.env.power_allocation import PowerAllocationConfig, PowerAllocationEnv
from fabline.harness.power_allocation import (
    AlternatePolicy,
    DefaultPolicy,
    FavorAssemblerPolicy,
    FavorFurnacePolicy,
    TabularQPolicy,
    evaluate_policy,
)
from fabline.obs.power import PowerControlObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig


def _setup() -> tuple[FactoryConfig, PowerAllocationConfig]:
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
    allocation = PowerAllocationConfig(
        episode_ticks=500,
        decision_interval=10,
        success_score=100,
        power=PowerConfig(
            enabled=True,
            generator_count=1,
            generator_capacity=5,
            generator_radius=8,
        ),
    )
    return config, allocation


def test_power_control_observation_shape() -> None:
    config, allocation = _setup()
    env = PowerAllocationEnv(config, allocation)
    observation, info = env.reset(0)
    assert observation.shape == (18,)
    assert PowerControlObservation(config, allocation.power).spec.shape == (18,)
    assert 0.0 <= observation.min() <= observation.max() <= 1.0
    assert info["priority"] == 0


def test_priority_action_sets_state_and_reward() -> None:
    config, allocation = _setup()
    env = PowerAllocationEnv(config, allocation)
    env.reset(0)
    observation, reward, terminated, truncated, info = env.step(1)
    assert info["priority"] == 1
    assert info["last_action"] == "favor_furnace"
    assert reward == info["score"]
    assert not (terminated or truncated)


def test_alternate_beats_fixed_policies() -> None:
    config, allocation = _setup()
    env = PowerAllocationEnv(config, allocation)
    default = evaluate_policy(env, DefaultPolicy(), episodes=1, seed=0)
    furnace = evaluate_policy(env, FavorFurnacePolicy(), episodes=1, seed=0)
    assembler = evaluate_policy(env, FavorAssemblerPolicy(), episodes=1, seed=0)
    alternate = evaluate_policy(env, AlternatePolicy(), episodes=1, seed=0)
    assert alternate.mean_score > default.mean_score
    assert alternate.mean_score > furnace.mean_score
    assert alternate.mean_score > assembler.mean_score
    assert alternate.success_rate == 1.0


def test_tabular_q_learns() -> None:
    config, allocation = _setup()
    env = PowerAllocationEnv(config, allocation)
    policy = TabularQPolicy()
    policy.train(env, episodes=30, seed=0)
    metrics = evaluate_policy(env, policy, episodes=1, seed=0)
    assert metrics.mean_score > 50.0


def test_priority_changes_hash() -> None:
    config, allocation = _setup()
    env = PowerAllocationEnv(config, allocation)
    env.reset(0)
    before = env.world.state_hash()
    env.world.state.power_priority = 1
    assert env.world.state_hash() != before
    env.world.state.power_priority = 0
    assert env.world.state_hash() == before


def test_done_at_episode_end() -> None:
    config, allocation = _setup()
    env = PowerAllocationEnv(config, allocation)
    env.reset(0)
    done = False
    steps = 0
    while not done:
        _, _, terminated, truncated, _ = env.step(0)
        done = terminated or truncated
        steps += 1
    assert steps == 50
    assert env.world.state.tick == 500


def test_power_allocation_runner_and_report(tmp_path) -> None:
    from fabline.harness.power_allocation import (
        run_power_allocation,
        write_power_allocation_report,
    )

    config, allocation = _setup()
    results = run_power_allocation(
        config,
        allocation,
        episodes=1,
        train_episodes=5,
        seeds=(0,),
    )
    assert set(results) == {
        "default",
        "favor_furnace",
        "favor_assembler",
        "alternate",
        "random",
        "tabular_q",
    }
    report = write_power_allocation_report(
        tmp_path,
        results,
        config={"generator_capacity": 5, "success_score": 100},
    )
    assert report.exists()
    assert "Power-allocation control report" in report.read_text(encoding="utf-8")
