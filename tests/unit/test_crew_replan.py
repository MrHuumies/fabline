from __future__ import annotations

from fabline.env.crew_replan import (
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
