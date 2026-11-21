from __future__ import annotations

from fabline.env.fault_power import FaultPowerConfig, FaultPowerEnv
from fabline.harness.fault_power import (
    AlternateRepairPolicy,
    NoopPolicy,
    TabularQPolicy,
    evaluate_policy,
    run_fault_power,
    write_fault_power_report,
)
from fabline.obs.base import build_observation
from fabline.obs.interaction import FaultPowerObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.power import PowerConfig


def _setup() -> tuple[FactoryConfig, FaultPowerConfig]:
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
    interaction = FaultPowerConfig(
        episode_ticks=500,
        decision_interval=10,
        repair_cost=1.0,
        success_score=90,
        faults=FaultConfig(
            enabled=True,
            wear_per_craft=1,
            fault_threshold=5,
            repair_ticks=30,
        ),
        power=PowerConfig(
            enabled=True,
            generator_count=1,
            generator_capacity=5,
            generator_radius=8,
        ),
    )
    return config, interaction


def test_fault_power_observation_shape_and_build() -> None:
    config, interaction = _setup()
    env = FaultPowerEnv(config, interaction)
    observation, info = env.reset(0)
    assert observation.shape == (24,)
    assert FaultPowerObservation(
        config, interaction.faults, interaction.power
    ).spec.shape == (24,)
    assert 0.0 <= observation.min() <= observation.max() <= 1.0
    assert isinstance(
        build_observation(
            "fault_power", config, interaction.faults, interaction.power
        ),
        FaultPowerObservation,
    )


def test_repair_action_clears_fault_and_costs() -> None:
    config, interaction = _setup()
    env = FaultPowerEnv(config, interaction)
    observation, info = env.reset(0)
    assert env.action_mask().tolist() == [True, True, True, False]
    furnace = next(
        entity
        for entity in env.world.state.entities.values()
        if entity.type.name == "FURNACE"
    )
    furnace.faulted = True
    furnace.wear = 5
    furnace.repair_progress = 3
    assert env.action_mask()[3]
    _, reward, _, _, info = env.step(3)
    assert not furnace.faulted
    assert furnace.wear == 0
    assert info["repairs"] == 1
    assert reward <= info["score"]  # score delta minus the repair cost


def test_alternate_repair_beats_noop() -> None:
    config, interaction = _setup()
    env = FaultPowerEnv(config, interaction)
    noop = evaluate_policy(env, NoopPolicy(), episodes=1, seed=0)
    alternate = evaluate_policy(env, AlternateRepairPolicy(), episodes=1, seed=0)
    assert alternate.mean_score > noop.mean_score
    assert alternate.mean_repairs > 0


def test_tabular_q_uses_repairs_and_beats_fixed() -> None:
    config, interaction = _setup()
    env = FaultPowerEnv(config, interaction)
    policy = TabularQPolicy()
    policy.train(env, episodes=100, seed=0)
    metrics = evaluate_policy(env, policy, episodes=1, seed=0)
    assert metrics.mean_score > 10.0
    assert metrics.mean_repairs > 0


def test_fault_power_runner_and_report(tmp_path) -> None:
    config, interaction = _setup()
    results = run_fault_power(
        config,
        interaction,
        episodes=1,
        train_episodes=5,
        seeds=(0,),
    )
    assert set(results) == {
        "noop",
        "favor_furnace",
        "favor_assembler",
        "repair_now",
        "alternate_repair",
        "random",
        "tabular_q",
    }
    report = write_fault_power_report(
        tmp_path,
        results,
        config={
            "generator_capacity": 5,
            "fault_threshold": 5,
            "repair_ticks": 30,
            "repair_cost": 1.0,
            "success_score": 90,
        },
    )
    assert report.exists()
    assert "Fault + power control report" in report.read_text(encoding="utf-8")
