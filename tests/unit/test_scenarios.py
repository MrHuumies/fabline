from __future__ import annotations

import pytest

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS, generate_state
from fabline.worlds.factory.labels import bottleneck_label
from fabline.worlds.factory.state import EntityType, Item
from fabline.worlds.factory.world import FactoryWorld


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=300,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )


def test_scenarios_are_deterministic() -> None:
    config = FactoryConfig(
        width=32,
        height=16,
        ticks_per_episode=300,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )
    for scenario in SCENARIOS.values():
        first = generate_state(config, seed=7, scenario=scenario)
        second = generate_state(config, seed=7, scenario=scenario)
        assert first.state_hash() == second.state_hash()


def test_scenarios_change_line_composition() -> None:
    config = _config()
    ingot = generate_state(config, seed=3, scenario=SCENARIOS["ingot"])
    gear = generate_state(config, seed=3, scenario=SCENARIOS["gear"])
    assert not any(
        entity.type is EntityType.ASSEMBLER for entity in ingot.entities.values()
    )
    assert any(
        entity.type is EntityType.ASSEMBLER for entity in gear.entities.values()
    )


def test_scenario_outputs() -> None:
    config = _config()
    expectations = {
        "ingot": (1, 0),
        "gear": (0, 1),
        "extra_gear": (0, 1),
        "broken_gear": (0, 0),
    }
    for name, (ingots, gears) in expectations.items():
        world = FactoryWorld(config)
        world.reset(seed=5, scenario=SCENARIOS[name])
        world.run_ticks(300)
        delivered = world.state.delivered
        assert (delivered[Item.INGOT] > 0) == bool(ingots), name
        assert (delivered[Item.GEAR] > 0) == bool(gears), name


def test_bottleneck_label_on_a_working_line(line_world) -> None:
    line_world.run_ticks(100)
    label = bottleneck_label(line_world, horizon=30)
    assert label in {"miner", "belt", "furnace", "assembler"}


def test_bottleneck_label_on_broken_line() -> None:
    config = _config()
    world = FactoryWorld(config)
    world.reset(seed=5, scenario=SCENARIOS["broken_gear"])
    world.run_ticks(100)
    assert bottleneck_label(world, horizon=20) == "none"


def test_unknown_scenario_name_is_not_implicit() -> None:
    with pytest.raises(KeyError):
        SCENARIOS["does-not-exist"]
