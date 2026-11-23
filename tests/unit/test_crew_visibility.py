from __future__ import annotations

from fabline.env.crew_replan import CrewReplanConfig, CrewReplanEnv
from fabline.env.crew_visibility import (
    BudgetVisibilityEnv,
    PrivateVisibilityEnv,
    VisibilityEnv,
)
from fabline.harness.crew_private import (
    CrewNearestPolicy,
    PrivatePairPolicy,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig


def _env() -> CrewReplanEnv:
    return CrewReplanEnv(
        FactoryConfig(
            width=48,
            height=24,
            ticks_per_episode=500,
            decision_interval=10,
            entity_budget=48,
            rock_density=0.0,
            ore_patches=1,
            starter_line=True,
            emit_events=True,
        ),
        CrewReplanConfig(
            randomize_crew_b=True,
            crew_b_min_distance=8,
            scenario="spread_gear",
            success_score=600,
            power=PowerConfig(
                enabled=True,
                topology="wired",
                generator_count=1,
                generator_capacity=48,
                generator_radius=8,
                wire_redundancy=2,
            ),
        ),
    )


def test_global_visibility_is_unchanged() -> None:
    env = _env()
    wrapper = VisibilityEnv(env, radius=999)
    observation, info = wrapper.reset(10000)
    assert wrapper.action_mask().tolist() == env.action_mask().tolist()
    assert observation.shape == env._observation().shape
    assert "visible_a" not in info["roles"]["small"]


def test_local_visibility_masks_unknown_targets() -> None:
    env = _env()
    wrapper = VisibilityEnv(env, radius=8)
    observation, info = wrapper.reset(10000)
    assert observation.shape == env._observation().shape
    while info["tick"] < 40:
        observation, _, _, _, info = wrapper.step(0)
    mask = wrapper.action_mask()
    for role in info["roles"]:
        data = info["roles"][role]
        if not data["known"]:
            assert data["outage"] == 0
            assert not data["degraded"]
    assert mask[0]
    for action in range(1, env.n_actions):
        if mask[action]:
            first, second = divmod(action, 4)
            if first > 0:
                assert info["roles"][env.roles[first - 1]]["known"]
            if second > 0:
                assert info["roles"][env.roles[second - 1]]["known"]


def test_private_views_and_pair_policy() -> None:
    env = PrivateVisibilityEnv(_env(), radius=16)
    observation, info = env.reset(14000)
    assert set(info["crew_roles"]) == {"a", "b"}
    while info["tick"] < 40:
        observation, _, _, _, info = env.step(0)
    policy = PrivatePairPolicy(
        CrewNearestPolicy("a"), CrewNearestPolicy("b")
    )
    action = policy.act(observation, info, env.action_mask())
    assert env.action_mask()[action]


def test_budget_reports_are_capped_and_shared() -> None:
    env = _env()
    budget = BudgetVisibilityEnv(
        env, radius=16, reports_per_crew=1
    )
    observation, info = budget.reset(16000)
    while info["tick"] < 40:
        observation, _, _, _, info = budget.step(0)
    assert len(info["reports"]["a"]) <= 1
    assert len(info["reports"]["b"]) <= 1
    known = set(info["reports"]["a"]) | set(info["reports"]["b"])
    mask = budget.action_mask()
    for action in range(env.n_actions):
        if not mask[action]:
            continue
        first, second = divmod(action, 4)
        if first > 0:
            assert env.roles[first - 1] in known
        if second > 0:
            assert env.roles[second - 1] in known
