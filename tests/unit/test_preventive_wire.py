from __future__ import annotations

from fabline.env.preventive_wire import (
    PREVENTIVE_WIRE_FEATURES,
    PreventiveWireConfig,
    PreventiveWireEnv,
)
from fabline.harness.preventive_wire import (
    LatePolicy,
    NoopPolicy,
    PreventivePolicy,
    ReactivePolicy,
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


def _env() -> PreventiveWireEnv:
    return PreventiveWireEnv(
        _config(), PreventiveWireConfig(success_score=150)
    )


def test_warning_and_failure_schedule() -> None:
    env = _env()
    observation, info = env.reset(0)
    assert observation.shape == (len(PREVENTIVE_WIRE_FEATURES),)
    assert info["degraded"] is False
    assert env.action_mask().tolist() == [True, False]
    while info["tick"] < 60:
        _, _, _, _, info = env.step(0)
    assert info["tick"] == 60
    assert info["degraded"] is True
    assert env.action_mask().tolist() == [True, True]
    while info["tick"] < 220:
        _, _, _, _, info = env.step(0)
    assert info["tick"] == 220
    assert info["failed"] is True
    assert info["degraded"] is False


def test_preventive_beats_reactive_and_late() -> None:
    noop = evaluate_policy(_env(), NoopPolicy(), episodes=2, seed=0)
    preventive = evaluate_policy(
        _env(), PreventivePolicy(), episodes=2, seed=0
    )
    reactive = evaluate_policy(_env(), ReactivePolicy(), episodes=2, seed=0)
    late = evaluate_policy(_env(), LatePolicy(), episodes=2, seed=0)
    assert preventive.mean_score > reactive.mean_score > noop.mean_score
    assert late.mean_score == noop.mean_score
    assert preventive.mean_prevented == 1.0
    assert preventive.success_rate == 1.0
    assert late.mean_aborted == 1.0


def test_degraded_repair_cancels_failure() -> None:
    env = _env()
    env.reset(0)
    wire = env._target()
    env.world.degrade_wire(wire.id, 220)
    assert wire.degraded and wire.failure_tick == 220
    env.world.repair_wire(wire.id)
    assert not wire.failed
    assert not wire.degraded
    assert wire.failure_tick == 0
    kinds = [event.kind for event in env.world.state.events]
    assert "power_wire_degraded" in kinds
    assert "power_wire_repair" in kinds


def test_aborted_preventive_job_spends_budget() -> None:
    env = _env()
    env.reset(0)
    while env.world.state.tick < 100:
        env.step(0)
    assert env._target().degraded
    _, _, _, _, info = env.step(1)
    assert info["aborted"] == 1
    assert info["repairs"] == 1
    assert info["failed"] is True
    assert env.action_mask().tolist() == [True, False]
