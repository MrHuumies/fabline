from __future__ import annotations

from fabline.env.three_crew_replan import (
    THREE_CREW_REPLAN_FEATURES,
    ThreeCrewReplanConfig,
    ThreeCrewReplanEnv,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig


def _env() -> ThreeCrewReplanEnv:
    return ThreeCrewReplanEnv(
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
        ThreeCrewReplanConfig(
            loop_failure_tick=100,
            small_failure_tick=130,
            large_failure_tick=160,
            recall_tick=100,
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


def test_three_crew_replan_phase_and_mask() -> None:
    env = _env()
    observation, info = env.reset(0)
    assert observation.shape == (len(THREE_CREW_REPLAN_FEATURES),)
    while info["tick"] < 40:
        observation, _, _, _, info = env.step(0)
    observation, _, terminated, truncated, info = env.step(27)
    assert not terminated and not truncated
    assert info["phase"] == "replan"
    assert not info["crew_b_available"]
    mask = env.action_mask()
    assert mask[:16].any()
    action = next(
        index for index in range(16) if mask[index] and index != 0
    )
    observation, _, terminated, truncated, info = env.step(action)
    assert terminated and not truncated
    assert info["score"] >= 0
