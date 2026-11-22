from __future__ import annotations

from fabline.env.preventive_fault import (
    PreventiveFaultConfig,
    PreventiveFaultEnv,
)
from fabline.harness.preventive_fault import (
    NoopPolicy,
    ThresholdPolicy,
    evaluate_policy,
)
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


def _env() -> PreventiveFaultEnv:
    return PreventiveFaultEnv(
        _config(), PreventiveFaultConfig(success_score=240)
    )


def test_observation_and_mask() -> None:
    env = _env()
    observation, info = env.reset(0)
    assert observation.shape == (15,)
    assert info["max_wear"] == 0
    assert env.action_mask().tolist() == [True, False]


def test_maintenance_resets_wear_after_window() -> None:
    env = _env()
    env.reset(0)
    env.world.run_ticks(60)
    worn = env._worn()
    assert worn
    entity = worn[0]
    before = entity.wear
    assert env.world.maintain_entity(entity)
    assert entity.maintenance_remaining == 10
    assert "maintenance_remaining" in env.world.state.canonical()["entities"][0]
    env.world.run_ticks(5)
    assert entity.maintenance_remaining == 5
    assert entity.wear == before
    env.world.run_ticks(5)
    assert entity.maintenance_remaining == 0
    assert entity.wear == 0


def test_preventive_threshold_beats_noop() -> None:
    noop = evaluate_policy(_env(), NoopPolicy(), episodes=2, seed=0)
    early = evaluate_policy(
        _env(), ThresholdPolicy(0.5), episodes=2, seed=0
    )
    best = evaluate_policy(
        _env(), ThresholdPolicy(0.7), episodes=2, seed=0
    )
    assert best.mean_score > early.mean_score > noop.mean_score
    assert best.mean_faults == 0
    assert noop.mean_faults > 0
    assert best.success_rate == 1.0
