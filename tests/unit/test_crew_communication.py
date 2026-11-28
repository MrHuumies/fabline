from __future__ import annotations

import json

import pytest

from fabline.env.crew_communication import (
    CrewCommConfig,
    CrewCommEnv,
)
from fabline.env.sequential_crew import SequentialCrewConfig
from fabline.harness.crew_communication import (
    RandomCommPolicy,
    communication_gates,
    run_crew_communication,
    validate_seeds,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.world import FactoryWorld


def make_env(**comm_kwargs: object) -> CrewCommEnv:
    return CrewCommEnv(
        FactoryConfig(),
        SequentialCrewConfig(target_count=5),
        CrewCommConfig(**comm_kwargs),  # type: ignore[arg-type]
    )


def test_local_observation_contract() -> None:
    env = make_env()
    observations, info = env.reset(seed=120010)
    assert len(env.feature_names) == 56
    assert observations[0].shape == (56,)
    assert observations[1].shape == (56,)
    assert env.action_mask(0).shape == (7,)
    assert env.joint_mask().shape == (49,)
    assert info["messages_used"] == 0
    assert info["report_budget"] == [2, 2]


def test_report_budget_and_delay() -> None:
    env = make_env(report_budget=1, report_delay=1, report_cost=0.5)
    env.reset(seed=120010)
    target = env.base.targets[0]
    env.base.positions[0] = (target.ax, target.ay)
    assert env.action_mask(0)[6]
    env.step((6, 4))
    assert env.report_budget[0] == 0
    assert env.messages_used == 1
    assert env.pending
    assert env.reports[0] is None
    env.step((4, 4))
    assert env.reports[0] is not None
    assert env.reports[0]["failed"] == target.failed
    assert env.reports_delivered >= 1


def test_report_masked_without_visibility_or_budget() -> None:
    env = make_env(report_budget=1, visibility_radius=1)
    env.reset(seed=120010)
    target = env.base.targets[0]
    env.base.positions[0] = (target.ax, target.ay)
    assert env.action_mask(0)[6]
    env.report_budget[0] = 0
    assert not env.action_mask(0)[6]


def test_determinism_and_replay() -> None:
    first = make_env()
    second = make_env()
    first.reset(seed=120010)
    second.reset(seed=120010)
    policy = RandomCommPolicy(0)
    for _ in range(3):
        action = policy.act(first)
        first.step(action)
        second.step(action)
        assert first.replay_state() == second.replay_state()
    json.dumps(first.replay_state())


def test_default_world_hash_unchanged() -> None:
    world = FactoryWorld(FactoryConfig())
    before = world.state_hash()
    env = make_env()
    env.reset(seed=120010)
    for _ in range(2):
        env.step((4, 4))
    assert world.state_hash() == before


def test_invalid_layout_and_seed_validation() -> None:
    with pytest.raises(RuntimeError, match="too few outage wires"):
        CrewCommEnv(
            FactoryConfig(),
            SequentialCrewConfig(target_count=100),
            CrewCommConfig(),
        )
    env = make_env()
    validate_seeds(env, (120010, 120011), 2)
    with pytest.raises(RuntimeError, match="invalid communication seed 110011"):
        validate_seeds(env, (110011,), 1)


def test_scripted_communication_smoke() -> None:
    results = run_crew_communication(
        FactoryConfig(),
        SequentialCrewConfig(target_count=5),
        CrewCommConfig(),
        seeds=(120010,),
        episodes=1,
    )
    assert set(results) == {
        "shared",
        "local_no_report",
        "local_report",
        "random",
    }
    assert results["shared"]["mean_messages"] == 0
    gates = communication_gates(results)
    assert "H1_communication_gain" in gates
    assert "challenge" in gates
