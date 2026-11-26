from __future__ import annotations

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.production import ProductionConfig
from fabline.worlds.factory.state import Entity, EntityType, Item
from fabline.worlds.factory.world import FactoryWorld


def _world() -> FactoryWorld:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
    )
    return FactoryWorld(
        config,
        production=ProductionConfig(enabled=True, assembly_enabled=True),
    )


def _assembler(world: FactoryWorld) -> Entity:
    return next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.ASSEMBLER
    )


def test_component_recipe_produces_component() -> None:
    world = _world()
    world.reset(0, SCENARIOS["gear"])
    assembler = _assembler(world)
    assembler.recipe = 1
    assembler.input_buffer[Item.INGOT] = 4
    world.run_ticks(40)
    assert world.state.delivered.get(Item.COMPONENT, 0) > 0


def test_assembly_recipe_consumes_component_and_makes_gear() -> None:
    world = _world()
    world.reset(0, SCENARIOS["gear"])
    assembler = _assembler(world)
    assembler.recipe = 2
    assembler.input_buffer[Item.INGOT] = 1
    assembler.input_buffer[Item.COMPONENT] = 1
    before = world.state.delivered.get(Item.GEAR, 0)
    world.run_ticks(40)
    assert world.state.delivered.get(Item.GEAR, 0) > before
    assert assembler.input_buffer.get(Item.COMPONENT, 0) == 0


def test_logistics_accepts_component_into_assembly_assembler() -> None:
    world = _world()
    world.reset(0, SCENARIOS["gear"])
    assembler = _assembler(world)
    assembler.recipe = 2
    belt = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.BELT
        and entity.x + 1 == assembler.x
        and entity.y == assembler.y
        and entity.direction.name == "EAST"
    )
    belt.output_buffer[Item.COMPONENT] = 1
    world.tick()
    assert assembler.input_buffer.get(Item.COMPONENT, 0) == 1


def test_logistics_buffers_component_while_making_direct_gear() -> None:
    world = _world()
    world.reset(0, SCENARIOS["gear"])
    assembler = _assembler(world)
    assembler.recipe = 0
    belt = next(
        entity
        for entity in world.state.entities.values()
        if entity.type is EntityType.BELT
        and entity.x + 1 == assembler.x
        and entity.y == assembler.y
        and entity.direction.name == "EAST"
    )
    belt.output_buffer[Item.COMPONENT] = 1
    world.tick()
    assert assembler.input_buffer.get(Item.COMPONENT, 0) == 1


def test_recipe_is_hashed_only_when_nonzero() -> None:
    world = _world()
    world.reset(0, SCENARIOS["gear"])
    assembler = _assembler(world)
    base = world.state_hash()
    assembler.recipe = 1
    assert world.state_hash() != base
