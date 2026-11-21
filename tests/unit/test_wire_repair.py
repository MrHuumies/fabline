from __future__ import annotations

import numpy as np

from fabline.env.wire_repair import (
    WIRE_REPAIR_FEATURES,
    WireRepairConfig,
    WireRepairEnv,
)
from fabline.harness.wire_repair import (
    NoopPolicy,
    RepairLargestPolicy,
    RepairNowPolicy,
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


def _env() -> WireRepairEnv:
    return WireRepairEnv(
        _config(), WireRepairConfig(success_score=150)
    )


def test_wire_repair_schedule_is_deterministic() -> None:
    first = _env()
    second = _env()
    _, first_info = first.reset(0)
    _, second_info = second.reset(0)
    assert first_info["fault_schedule"] == second_info["fault_schedule"]
    assert len(first_info["fault_schedule"]) == 3
    assert first_info["slot_outages"] == []


def test_repair_policies_rank_impact_and_waste_loops() -> None:
    env = _env()
    noop = evaluate_policy(env, NoopPolicy(), episodes=2, seed=0)
    now = evaluate_policy(env, RepairNowPolicy(), episodes=2, seed=0)
    largest = evaluate_policy(env, RepairLargestPolicy(), episodes=2, seed=0)
    assert noop.mean_score < now.mean_score < largest.mean_score
    assert now.mean_wasted == 1.0
    assert largest.mean_wasted == 0.0
    assert largest.success_rate == 1.0


def test_observation_and_mask_shapes() -> None:
    env = _env()
    observation, info = env.reset(0)
    assert observation.shape == (len(WIRE_REPAIR_FEATURES),)
    assert env.action_mask().tolist() == [True, False, False, False]
    env.step(0)
    assert info["tick"] == 0


def test_fail_and_repair_wire_events_and_hash() -> None:
    env = _env()
    env.reset(0)
    wire = env.world.state.power_wires[0]
    before = env.world.state.state_hash()
    assert env.world.fail_wire(wire.id)
    assert wire.failed
    assert not env.world.fail_wire(wire.id)
    assert env.world.state.state_hash() != before
    assert env.world.repair_wire(wire.id)
    assert not wire.failed
    kinds = [event.kind for event in env.world.state.events]
    assert "power_wire_fault" in kinds
    assert "power_wire_repair" in kinds
    assert env.world.state.state_hash() == before


def test_budget_exhaustion_masks_repairs() -> None:
    env = _env()
    env.reset(0)
    env.repairs = env.repair.repair_budget
    assert env.action_mask().tolist() == [True, False, False, False]


def test_repair_observation_is_finite() -> None:
    env = _env()
    observation, _ = env.reset(0)
    env.step(0)
    assert np.isfinite(observation).all()
