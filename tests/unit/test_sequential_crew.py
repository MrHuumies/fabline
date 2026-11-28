from __future__ import annotations

import json

import pytest

from fabline.env.sequential_crew import (
    DELTAS,
    SequentialCrewConfig,
    SequentialCrewEnv,
)
from fabline.harness.sequential_crew import (
    RandomCrewPolicy,
    run_sequential_crew,
    sequential_gates,
    validate_seeds,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.world import FactoryWorld


def make_env(**crew_kwargs: object) -> SequentialCrewEnv:
    return SequentialCrewEnv(
        FactoryConfig(),
        SequentialCrewConfig(**crew_kwargs),  # type: ignore[arg-type]
    )


def test_reset_contract() -> None:
    env = make_env()
    observation, info = env.reset(seed=100000)
    assert observation.shape == (len(env.feature_names),)
    assert len(env.feature_names) == 20
    assert info["targets"] == 3
    assert all(info["target_failed"])
    assert info["success"] is False
    assert info["completion_tick"] is None
    assert env.joint_mask().shape == (36,)
    assert env.joint_mask().any()
    assert env.positions[0] != env.positions[1]


def test_action_mask_and_repair() -> None:
    env = make_env()
    env.reset(seed=100000)
    target = env.targets[0]
    env.positions[0] = (target.ax, target.ay)
    assert env.action_mask(0)[5]

    far_cell = None
    for y in range(env.world.state.height):
        for x in range(env.world.state.width):
            if not env._walkable(x, y) or (x, y) == env.positions[1]:
                continue
            if all(env.distance((x, y), item) > 1 for item in env.targets):
                far_cell = (x, y)
                break
        if far_cell is not None:
            break
    assert far_cell is not None
    env.positions[0] = far_cell
    assert not env.action_mask(0)[5]

    env.positions[0] = (target.ax, target.ay)
    for _ in range(env.crew.repair_ticks):
        env.step((5, 4))
    assert not target.failed
    assert env.repairs >= 1


def test_movement_changes_position() -> None:
    env = make_env()
    env.reset(seed=100000)
    for action in range(4):
        if not env.action_mask(0)[action]:
            continue
        before = env.positions[0]
        dx, dy = DELTAS[action]
        env.step((action, 4))
        assert env.positions[0] == (before[0] + dx, before[1] + dy)
        return
    raise AssertionError("no legal movement action")


def test_success_is_mission_completion() -> None:
    env = make_env()
    env.reset(seed=100000)
    for target in env.targets:
        target.failed = False
    env.repairs = len(env.targets)
    info = env.info()
    assert info["mission_complete"]
    assert info["success"]


def test_determinism_and_replay() -> None:
    first = make_env()
    second = make_env()
    first.reset(seed=100000)
    second.reset(seed=100000)
    policy = RandomCrewPolicy(0)
    for _ in range(5):
        action = policy.act(first)
        first.step(action)
        second.step(action)
        assert first.replay_state() == second.replay_state()
    json.dumps(first.replay_state())


def test_default_world_hash_unchanged() -> None:
    world = FactoryWorld(FactoryConfig())
    before = world.state_hash()
    env = make_env()
    env.reset(seed=100000)
    for _ in range(3):
        env.step((4, 4))
    assert world.state_hash() == before


def test_invalid_layout_and_seed_validation() -> None:
    with pytest.raises(RuntimeError, match="too few outage wires"):
        make_env(target_count=100)
    env = make_env()
    validate_seeds(env, (100000, 100001))
    with pytest.raises(RuntimeError, match="invalid sequential-crew seed 100004"):
        validate_seeds(env, (100004,))
    with pytest.raises(RuntimeError, match="invalid sequential-crew seed 100004"):
        run_sequential_crew(
            FactoryConfig(),
            SequentialCrewConfig(),
            seeds=(100003,),
            episodes=2,
            q_episodes=1,
            bc_episodes=1,
        )


def test_run_sequential_crew_smoke() -> None:
    results = run_sequential_crew(
        FactoryConfig(),
        SequentialCrewConfig(),
        seeds=(100000,),
        episodes=1,
        q_episodes=1,
        bc_episodes=1,
    )
    assert "queue_oracle" in results
    assert "independent_q" in results
    assert "bc" in results
    assert results["independent_q"]["model"]["table_entries"] >= 0
    assert results["bc"]["model"]["messages"] == 0
    gates = sequential_gates(results)
    assert gates["H5_cost_reported"] is True
    assert "challenge" in gates
