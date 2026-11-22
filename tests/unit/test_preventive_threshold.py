from __future__ import annotations

from fabline.env.preventive_threshold import (
    PreventiveThresholdEnv,
    ThresholdConfig,
)
from fabline.harness.preventive_threshold import (
    EpsilonGreedyPolicy,
    UCBPolicy,
    evaluate_arm,
)
from fabline.worlds.factory.config import FactoryConfig


def _env() -> PreventiveThresholdEnv:
    return PreventiveThresholdEnv(
        FactoryConfig(
            width=16,
            height=8,
            ticks_per_episode=500,
            decision_interval=10,
            entity_budget=32,
            rock_density=0.0,
            ore_patches=1,
            starter_line=True,
            emit_events=True,
        ),
        ThresholdConfig(success_score=240),
    )


def test_arms_and_single_step_episode() -> None:
    env = _env()
    observation, info = env.reset(0)
    assert observation.shape == (1,)
    assert len(info["arms"]) == 7
    assert env.action_mask().all()
    _, reward, terminated, truncated, info = env.step(3)
    assert terminated is True
    assert truncated is False
    assert reward == 250.0
    assert info["success"] is True


def test_fixed_arm_ordering() -> None:
    env = _env()
    low = evaluate_arm(env, 0, (700,))
    best = evaluate_arm(env, 3, (700,))
    never = evaluate_arm(env, 6, (700,))
    assert best.mean_score > low.mean_score > never.mean_score


def test_ucb_and_epsilon_find_a_best_arm() -> None:
    env = _env()
    ucb = UCBPolicy()
    ucb.train(env, episodes=50, train_seed_start=9000)
    epsilon = EpsilonGreedyPolicy()
    epsilon.train(env, episodes=50, train_seed_start=9000)
    for policy in (ucb, epsilon):
        assert policy.arm in {3, 4, 5}
        metrics = evaluate_arm(env, policy.arm, (700, 701))
        assert metrics.mean_score == 250.0
