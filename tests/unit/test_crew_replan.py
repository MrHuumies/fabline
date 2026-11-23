from __future__ import annotations

from fabline.env.crew_replan import (
    CREW_COST_FEATURES,
    CREW_REPLAN_FEATURES,
    CrewReplanConfig,
    CrewReplanEnv,
)
from fabline.harness.crew_replan import (
    NoReplanPolicy,
    RecallAwarePolicy,
    SingleEDFPolicy,
    evaluate_policy,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig


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


def _env() -> CrewReplanEnv:
    return CrewReplanEnv(_config(), CrewReplanConfig())


def test_phase_transition_and_replan_mask() -> None:
    env = _env()
    observation, info = env.reset(0)
    assert observation.shape == (len(CREW_REPLAN_FEATURES),)
    assert info["phase"] == "initial"
    assert env.action_mask().tolist() == [True] + [False] * 15
    while info["tick"] < 40:
        _, _, _, _, info = env.step(0)
    assert env.action_mask().sum() > 1
    assert info["phase"] == "initial"
    observation, reward, terminated, truncated, info = env.step(11)
    assert not terminated and not truncated
    assert reward == 0.0
    assert info["phase"] == "replan"
    assert info["orphaned_role"] == "large"
    assert env.action_mask().tolist() == [
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
    ]
    observation, reward, terminated, truncated, info = env.step(12)
    assert terminated and not truncated
    assert observation.shape == (len(CREW_REPLAN_FEATURES),)
    assert info["score"] == 260


def test_role_cost_observation_features() -> None:
    env = CrewReplanEnv(
        _config(),
        CrewReplanConfig(role_repair_ticks=(20, 40, 100)),
    )
    observation, info = env.reset(0)
    assert observation.shape == (len(CREW_COST_FEATURES),)
    assert len(CREW_COST_FEATURES) == len(CREW_REPLAN_FEATURES) + 6
    assert info["phase"] == "initial"


def test_recall_replan_beats_no_replan_and_single_crew() -> None:
    env = _env()
    single = evaluate_policy(env, SingleEDFPolicy(), episodes=1, seed=0)
    aware = evaluate_policy(env, RecallAwarePolicy(), episodes=1, seed=0)
    no_replan = evaluate_policy(
        env,
        NoReplanPolicy(RecallAwarePolicy()),
        episodes=1,
        seed=0,
    )
    assert single.mean_score == 60
    assert aware.mean_score == 260
    assert aware.mean_score >= no_replan.mean_score + 10
    assert aware.mean_b_aborted == 1


def _multi_env() -> CrewReplanEnv:
    return CrewReplanEnv(
        FactoryConfig(
            width=32,
            height=16,
            ticks_per_episode=500,
            decision_interval=10,
            entity_budget=32,
            rock_density=0.0,
            ore_patches=1,
            starter_line=True,
            emit_events=True,
        ),
        CrewReplanConfig(
            warning_tick=40,
            recall_tick=80,
            job_failure_tick=80,
            replan_jobs=2,
            success_score=400,
            randomize_crew_b=True,
            crew_b_min_distance=8,
            scenario="random_gear",
            power=PowerConfig(
                enabled=True,
                topology="wired",
                generator_count=1,
                generator_capacity=24,
                generator_radius=8,
                wire_redundancy=2,
            ),
        ),
    )


def test_sequential_replan_recovers_two_orphans() -> None:
    env = _multi_env()
    observation, info = env.reset(0)
    while info["tick"] < 40:
        observation, _, _, _, info = env.step(0)
    observation, reward, terminated, truncated, info = env.step(11)
    assert not terminated and not truncated
    assert info["phase"] == "replan"
    assert set(info["orphaned_roles"]) == {"small", "large"}
    observation, reward, terminated, truncated, info = env.step(12)
    assert not terminated and not truncated
    assert info["phase"] == "replan"
    assert info["orphaned_roles"] == ["small"]
    assert info["score"] > 0
    observation, reward, terminated, truncated, info = env.step(8)
    assert terminated and not truncated
    assert info["score"] > 300


def test_triage_has_three_positive_targets() -> None:
    env = CrewReplanEnv(
        FactoryConfig(
            width=32,
            height=16,
            ticks_per_episode=500,
            decision_interval=10,
            entity_budget=32,
            rock_density=0.0,
            ore_patches=1,
            starter_line=True,
            emit_events=True,
        ),
        CrewReplanConfig(
            recall_tick=100,
            job_failure_tick=100,
            replan_jobs=2,
            role_mode="three_positive",
            replan_mode="all_positive",
            success_score=300,
            randomize_crew_b=True,
            crew_b_min_distance=8,
            scenario="random_gear",
            power=PowerConfig(
                enabled=True,
                topology="wired",
                generator_count=1,
                generator_capacity=24,
                generator_radius=8,
                wire_redundancy=2,
            ),
        ),
    )
    observation, info = env.reset(0)
    while info["tick"] < 40:
        observation, _, _, _, info = env.step(0)
    positive = [
        role for role in info["roles"]
        if info["roles"][role]["outage"] > 0
    ]
    assert len(positive) == 3
    observation, _, _, _, info = env.step(11)
    assert info["phase"] == "replan"
    mask = env.action_mask()
    assert any(mask[choice * 4] for choice in (1, 2, 3))


def test_replacement_crew_enters_after_recall() -> None:
    env = CrewReplanEnv(
        FactoryConfig(
            width=32,
            height=16,
            ticks_per_episode=500,
            decision_interval=10,
            entity_budget=32,
            rock_density=0.0,
            ore_patches=1,
            starter_line=True,
            emit_events=True,
        ),
        CrewReplanConfig(
            recall_tick=100,
            job_failure_tick=100,
            replan_jobs=1,
            role_mode="three_positive",
            replan_mode="all_positive",
            replacement=True,
            success_score=300,
            randomize_crew_b=True,
            crew_b_min_distance=8,
            scenario="random_gear",
            power=PowerConfig(
                enabled=True,
                topology="wired",
                generator_count=1,
                generator_capacity=24,
                generator_radius=8,
                wire_redundancy=2,
            ),
        ),
    )
    observation, info = env.reset(0)
    while info["tick"] < 40:
        observation, _, _, _, info = env.step(0)
    observation, _, terminated, truncated, info = env.step(11)
    assert not terminated and not truncated
    assert info["phase"] == "replan"
    assert info["replacement_arrived"]
    assert any(env.action_mask()[action] for action in range(1, 16))
    observation, _, terminated, truncated, info = env.step(11)
    assert terminated and not truncated
    assert info["score"] > 0
