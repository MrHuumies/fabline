from __future__ import annotations

import pytest

from fabline.obs.power import PowerGridObservation, PowerObservation
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.labels import future_brownout
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import EntityType, Item
from fabline.worlds.factory.world import FactoryWorld


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )


def _power_world(**kwargs) -> FactoryWorld:
    defaults = {
        "enabled": True,
        "generator_count": 2,
        "generator_capacity": 12,
        "generator_radius": 8,
    }
    defaults.update(kwargs)
    world = FactoryWorld(_config(), power=PowerConfig(**defaults))
    world.reset(0, SCENARIOS["gear"])
    return world


def _activate_line(world: FactoryWorld) -> None:
    for entity in world.state.entities.values():
        if entity.type is EntityType.BELT:
            entity.output_buffer[Item.INGOT] = 1
        elif entity.type in (EntityType.FURNACE, EntityType.ASSEMBLER):
            entity.craft_progress = 1


def test_power_config_validation() -> None:
    with pytest.raises(ValueError):
        PowerConfig(generator_count=0)
    with pytest.raises(ValueError):
        PowerConfig(generator_capacity=0)
    with pytest.raises(ValueError):
        PowerConfig(generator_radius=-1)
    with pytest.raises(ValueError):
        PowerConfig(furnace_demand=-1)


def test_power_sources_are_deterministic_and_free() -> None:
    first = _power_world()
    second = _power_world()
    assert first.state.power_sources
    assert first.state.power_sources == second.state.power_sources
    for source in first.state.power_sources:
        assert 0 <= source.x < first.state.width
        assert 0 <= source.y < first.state.height
        assert (source.x, source.y) not in first.state.occupancy


def test_power_free_world_has_no_sources_or_power_fields() -> None:
    world = FactoryWorld(_config())
    world.reset(0, SCENARIOS["gear"])
    assert world.state.power_sources == []
    world.run_ticks(20)
    assert all(entity.brownout_ticks == 0 for entity in world.state.entities.values())
    observation = PowerObservation(world.config, world.power).observe(world.state)
    assert not observation.any()
    grid = PowerGridObservation(world.config, world.power).observe(world.state)
    assert not grid.any()


def test_allocation_respects_capacity_and_id_order() -> None:
    world = _power_world(generator_count=1, generator_capacity=5, generator_radius=8)
    _activate_line(world)
    world._power()
    entities = sorted(world.state.entities.values(), key=lambda entity: entity.id)
    powered = {entity.id for entity in entities if entity.powered}
    # miner 2 + belt 1 + belt 1 + belt 1 fits; the furnace's 3 does not.
    assert entities[0].type is EntityType.MINER
    assert entities[0].id in powered
    assert entities[1].type is EntityType.BELT
    assert entities[1].id in powered
    assert entities[2].type is EntityType.FURNACE
    assert entities[2].id not in powered
    assert entities[2].brownout_ticks == 1


def test_idle_entities_draw_no_power() -> None:
    world = _power_world(generator_count=1, generator_capacity=2, generator_radius=8)
    world._power()
    furnace = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.FURNACE
    )
    assert furnace.powered
    assert world.power.active_demand(furnace) == 0


def test_radius_excludes_distant_entities() -> None:
    world = _power_world(generator_count=1, generator_capacity=12, generator_radius=0)
    _activate_line(world)
    source = world.state.power_sources[0]
    world._power()
    for entity in world.state.entities.values():
        if world.power.active_demand(entity) == 0:
            continue
        distance = abs(entity.x - source.x) + abs(entity.y - source.y)
        assert entity.powered == (distance == 0)


def test_brownout_event_and_work_stop() -> None:
    world = _power_world(generator_count=1, generator_capacity=2, generator_radius=8)
    furnace = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.FURNACE
    )
    furnace.craft_progress = 1
    furnace.powered = True
    world.tick()
    assert not furnace.powered
    assert any(event.kind == "power_brownout" for event in world.state.events)
    assert furnace.craft_progress == 1


def test_faulted_entity_frees_capacity() -> None:
    world = _power_world(generator_count=1, generator_capacity=8, generator_radius=8)
    _activate_line(world)
    furnace = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.FURNACE
    )
    assembler = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.ASSEMBLER
    )
    furnace.faulted = True
    world._power()
    assert not furnace.powered
    assert assembler.powered


def test_power_observations() -> None:
    world = _power_world(generator_count=1, generator_capacity=3, generator_radius=8)
    furnace = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.FURNACE
    )
    furnace.craft_progress = 1
    world._power()
    aggregate = PowerObservation(world.config, world.power)
    grid = PowerGridObservation(world.config, world.power)
    assert aggregate.spec.shape == (12,)
    assert grid.spec.shape == (world.state.height, world.state.width, 3)
    values = aggregate.observe(world.state)
    spatial = grid.observe(world.state)
    assert values.shape == (12,)
    assert 0.0 <= values.min() <= values.max() <= 1.0
    assert 0.0 <= spatial.min() <= spatial.max() <= 1.0
    assert values[4] > 0.0  # brownout ratio


def test_power_changes_state_hash() -> None:
    powered = _power_world()
    powered.tick()
    before = powered.state_hash()
    entity = next(iter(powered.state.entities.values()))
    entity.brownout_ticks += 1
    assert powered.state_hash() != before
    entity.brownout_ticks -= 1
    assert powered.state_hash() == before


def test_future_brownout_label() -> None:
    tight = _power_world(generator_count=1, generator_capacity=2, generator_radius=8)
    furnace = next(
        entity
        for entity in tight.state.entities.values()
        if entity.type is EntityType.FURNACE
    )
    furnace.craft_progress = 1
    assert future_brownout(tight, horizon=5) == 1
    ample = _power_world(generator_count=2, generator_capacity=12, generator_radius=12)
    _activate_line(ample)
    assert future_brownout(ample, horizon=5) == 0


def test_power_priority_changes_allocation_order() -> None:
    world = _power_world(generator_count=1, generator_capacity=5, generator_radius=8)
    _activate_line(world)
    furnace = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.FURNACE
    )
    assembler = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.ASSEMBLER
    )

    world.state.power_priority = 1
    world._power()
    assert furnace.powered
    assert not assembler.powered

    world.state.power_priority = 2
    world._power()
    assert assembler.powered
    assert not furnace.powered


def test_stochastic_power_config_validation() -> None:
    with pytest.raises(ValueError):
        PowerConfig(load_jitter=-1)
    with pytest.raises(ValueError):
        PowerConfig(capacity_jitter=101)
    with pytest.raises(ValueError):
        PowerConfig(variation_period=0)


def test_stochastic_schedule_deterministic_and_hashed() -> None:
    first = _power_world(
        load_jitter=40,
        capacity_jitter=30,
        variation_period=10,
    )
    second = _power_world(
        load_jitter=40,
        capacity_jitter=30,
        variation_period=10,
    )
    assert first.state.power_load_factors == second.state.power_load_factors
    assert (
        first.state.power_capacity_factors
        == second.state.power_capacity_factors
    )
    assert len(first.state.power_load_factors) == 200
    assert all(
        60 <= value <= 140 for value in first.state.power_load_factors
    )
    assert all(
        70 <= value <= 130 for value in first.state.power_capacity_factors
    )

    deterministic = _power_world()
    assert deterministic.state.power_load_factors == []
    assert first.state_hash() != deterministic.state_hash()

    other = FactoryWorld(
        _config(),
        power=PowerConfig(
            enabled=True,
            generator_count=2,
            generator_capacity=12,
            generator_radius=8,
            load_jitter=40,
            capacity_jitter=30,
            variation_period=10,
        ),
    )
    other.reset(1, SCENARIOS["gear"])
    assert other.state.power_load_factors != first.state.power_load_factors


def test_stochastic_factors_scale_demand_and_capacity() -> None:
    world = _power_world(
        generator_count=1,
        generator_capacity=9,
        load_jitter=40,
        capacity_jitter=30,
        variation_period=10,
    )
    world.state.power_load_factors = [50] * 200
    world.state.power_capacity_factors = [50] * 200
    miner = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.MINER
    )
    assert world.power.active_demand(miner) == 2
    assert world.power.scaled_demand(miner, 50) == 1
    world._power()
    assert world.state.power_sources[0].capacity == 9


def test_stochastic_observation_uses_factors() -> None:
    world = _power_world(
        generator_count=1,
        generator_capacity=9,
        load_jitter=40,
        capacity_jitter=30,
        variation_period=10,
    )
    world.state.power_load_factors = [50] * 200
    world.state.power_capacity_factors = [50] * 200
    furnace = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.FURNACE
    )
    furnace.craft_progress = 1
    world._power()
    values = PowerObservation(world.config, world.power).observe(world.state)
    assert 0.0 <= values.min() <= values.max() <= 1.0
    grid = PowerGridObservation(world.config, world.power).observe(world.state)
    assert 0.0 <= grid.min() <= grid.max() <= 1.0


def test_replay_with_stochastic_power() -> None:
    from dataclasses import asdict

    from fabline.record.replay import validate_replay

    power = PowerConfig(
        enabled=True,
        generator_count=1,
        generator_capacity=9,
        generator_radius=8,
        load_jitter=40,
        capacity_jitter=30,
        variation_period=10,
    )
    world = FactoryWorld(_config(), power=power)
    world.reset(0, SCENARIOS["gear"])
    sample_ticks = [0, 10, 20]
    hashes = []
    for tick in range(21):
        if tick in sample_ticks:
            hashes.append(world.state_hash())
        world.tick()
    replay = {
        "seed": 0,
        "scenario": "gear",
        "power": asdict(power),
        "sample_ticks": sample_ticks,
        "state_hashes": hashes,
        "actions": [],
    }
    validate_replay(FactoryWorld(_config(), power=power), replay)
