from __future__ import annotations

from fabline.env.multi_crew import (
    MULTI_CREW_FEATURES,
    MultiCrewConfig,
    MultiCrewEnv,
)
from fabline.harness.multi_crew import (
    ParallelNearestPolicy,
    SingleEDFPolicy,
    _FixedActionPolicy,
    _oracle_action,
    evaluate_policy,
    run_crew_robustness,
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


def _env() -> MultiCrewEnv:
    return MultiCrewEnv(
        _config(),
        MultiCrewConfig(success_score=150),
    )


def test_observation_and_pair_mask() -> None:
    env = _env()
    observation, info = env.reset(0)
    assert observation.shape == (len(MULTI_CREW_FEATURES),)
    assert set(info["roles"]) == {"loop", "small", "large"}
    assert env.action_mask().tolist() == [True] + [False] * 15
    while info["tick"] < 40:
        _, _, _, _, info = env.step(0)
    assert env.action_mask().sum() > 1


def test_two_crew_oracle_beats_single_crew() -> None:
    env = _env()
    single = evaluate_policy(env, SingleEDFPolicy(), episodes=1, seed=0)
    nearest = evaluate_policy(
        env, ParallelNearestPolicy(), episodes=1, seed=0
    )
    action = _oracle_action(env, 0)
    oracle = evaluate_policy(
        env, _FixedActionPolicy(action), episodes=1, seed=0
    )
    assert oracle.mean_score == 260
    assert oracle.mean_score > single.mean_score
    assert oracle.mean_score >= nearest.mean_score


def test_crew_robustness_structure() -> None:
    results = run_crew_robustness(
        _config(),
        MultiCrewConfig(success_score=150),
        seeds=(3000, 3001),
        q_seeds=(),
    )
    policies = results["policies"]
    assert set(policies) == {
        "noop",
        "single_edf",
        "random",
        "parallel_nearest",
        "parallel_greedy",
        "oracle",
        "tabular_q",
    }
    assert len(policies["oracle"]["per_seed"]) == 2
    assert len(policies["parallel_nearest"]["per_seed"]) == 2
    assert policies["oracle"]["mean_score"] > policies["single_edf"][
        "mean_score"
    ]
    assert results["paired"]["oracle_minus_parallel_nearest"]["mean"] >= 0


def test_random_crew_b_is_deterministic_and_separated() -> None:
    config = FactoryConfig(
        width=32,
        height=16,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    multi = MultiCrewConfig(
        randomize_crew_b=True,
        crew_b_min_distance=8,
        scenario="random_gear",
    )
    first = MultiCrewEnv(config, multi)
    first.reset(6000)
    second = MultiCrewEnv(config, multi)
    second.reset(6000)
    assert first.crew_b == second.crew_b
    assert (
        abs(first.crew_b[0] - first.crew_a[0])
        + abs(first.crew_b[1] - first.crew_a[1])
        >= 8
    )
