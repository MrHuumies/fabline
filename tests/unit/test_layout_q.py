from __future__ import annotations

from fabline.env.multi_crew import MultiCrewConfig, MultiCrewEnv
from fabline.harness.layout_q import CompactQPolicy
from fabline.harness.multi_crew import evaluate_policy
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig


def _env() -> MultiCrewEnv:
    return MultiCrewEnv(
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
        MultiCrewConfig(
            randomize_crew_b=True,
            crew_b_min_distance=8,
            scenario="random_gear",
            success_score=400,
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


def test_compact_q_key_and_legal_action() -> None:
    env = _env()
    policy = CompactQPolicy()
    observation, info = env.reset(8000)
    while info["tick"] < 40:
        observation, _, _, _, info = env.step(0)
    key = policy._key(info)
    assert key[0] == 0
    assert len(key) == 7
    action = policy.act(observation, info, env.action_mask())
    assert env.action_mask()[action]


def test_compact_q_short_training_runs() -> None:
    env = _env()
    policy = CompactQPolicy()
    policy.train(env, episodes=2, seed=0, train_seed_start=80000)
    metrics = evaluate_policy(env, policy, episodes=1, seed=8000)
    assert metrics.mean_score >= 0
    assert metrics.success_rate in (0.0, 1.0)
