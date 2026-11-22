from __future__ import annotations

from fabline.env.crew_schedule import (
    CREW_FEATURES,
    CrewScheduleConfig,
    CrewScheduleEnv,
)
from fabline.harness.crew_schedule import (
    EarliestDeadlinePolicy,
    ImpactOnlyPolicy,
    SequencePolicy,
    TabularQPolicy,
    _oracle_actions,
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


def _env() -> CrewScheduleEnv:
    return CrewScheduleEnv(
        _config(),
        CrewScheduleConfig(
            success_score=150,
            loop_failure_tick=90,
            small_failure_tick=120,
            large_failure_tick=150,
        ),
    )


def test_roles_observation_and_mask() -> None:
    env = _env()
    observation, info = env.reset(0)
    assert observation.shape == (len(CREW_FEATURES),)
    assert set(info["roles"]) == {"loop", "small", "large"}
    assert env.action_mask().tolist() == [True, False, False, False]
    while info["tick"] < 40:
        _, _, _, _, info = env.step(0)
    assert env.action_mask()[1:].any()


def test_deadline_policy_beats_impact_only() -> None:
    env = _env()
    impact = evaluate_policy(env, ImpactOnlyPolicy(), episodes=1, seed=0)
    deadline = evaluate_policy(
        env, EarliestDeadlinePolicy(), episodes=1, seed=0
    )
    assert deadline.mean_score == 260
    assert impact.mean_score < deadline.mean_score
    assert deadline.mean_prevented == 2


def test_oracle_matches_deadline_order() -> None:
    env = _env()
    actions = _oracle_actions(env, 0)
    oracle = evaluate_policy(
        env, SequencePolicy(actions), episodes=1, seed=0
    )
    assert oracle.mean_score == 260


def test_budget_and_observation_after_service() -> None:
    env = _env()
    _, info = env.reset(0)
    while info["tick"] < 40:
        _, _, _, _, info = env.step(0)
    _, _, _, _, info = env.step(2)
    assert info["repairs"] == 1
    assert info["budget_remaining"] == 1
    assert info["crew"] != (0, 0)


def test_q_trains_legal_actions() -> None:
    env = _env()
    policy = TabularQPolicy()
    policy.train(env, episodes=5, seed=0, train_seed_start=14000)
    metrics = evaluate_policy(env, policy, episodes=1, seed=0)
    assert metrics.mean_score >= 0
