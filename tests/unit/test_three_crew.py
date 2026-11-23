from __future__ import annotations

from fabline.env.multi_crew import MultiCrewConfig
from fabline.env.three_crew import THREE_CREW_FEATURES, ThreeCrewEnv
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig


def _env() -> ThreeCrewEnv:
    return ThreeCrewEnv(
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
            success_score=600,
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


def test_three_crew_observation_and_mask() -> None:
    env = _env()
    observation, info = env.reset(21000)
    assert observation.shape == (len(THREE_CREW_FEATURES),)
    assert len(info["roles"]) == 3
    while info["tick"] < 40:
        observation, _, _, _, info = env.step(0)
    mask = env.action_mask()
    assert mask.sum() > 1
    assert not mask[21]  # all three choose the same positive bridge
    action = 27  # distinct targets: 1, 2, 3
    assert mask[action]
    observation, reward, terminated, truncated, info = env.step(action)
    assert terminated and not truncated
    assert observation.shape == (len(THREE_CREW_FEATURES),)
    assert info["score"] >= 0
