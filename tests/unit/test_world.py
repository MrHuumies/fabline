from __future__ import annotations

from fabline.worlds.factory.actions import Action, ActionOp
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import Direction, Entity, EntityType, Item, TileType
from fabline.worlds.factory.world import FactoryWorld


def _clear_world(world: FactoryWorld) -> None:
    state = world.state
    state.tiles = [TileType.EMPTY] * (state.width * state.height)
    state.entities.clear()
    state.occupancy.clear()
    state.events.clear()
    state.next_entity_id = 1
    state.delivered = {item: 0 for item in state.delivered}
    state.score = 0
    state.history.clear()


def _empty_world(config: FactoryConfig, seed: int = 0) -> FactoryWorld:
    world = FactoryWorld(config)
    world.reset(seed=seed)
    _clear_world(world)
    return world


def test_line_produces_output(line_world) -> None:
    line_world.run_ticks(200)
    assert line_world.state.score > 0
    assert line_world.state.delivered[Item.INGOT] + line_world.state.delivered[Item.GEAR] > 0


def test_machine_craft_timing() -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=50,
        rock_density=0.0,
        starter_line=False,
        emit_events=True,
    )
    world = _empty_world(config)
    world.state.entities[1] = Entity(
        id=1,
        type=EntityType.FURNACE,
        x=3,
        y=4,
        direction=Direction.EAST,
        input_buffer={Item.ORE: 1},
    )
    world.state.occupancy[(3, 4)] = 1
    world.state.next_entity_id = 2

    world.run_ticks(1)
    furnace = world.state.entities[1]
    assert furnace.craft_progress == config.furnace_ticks
    assert furnace.output_buffer == {}

    world.run_ticks(config.furnace_ticks - 1)
    assert furnace.craft_progress == 1
    assert furnace.output_buffer == {}

    world.run_ticks(1)
    assert furnace.craft_progress == 0
    assert furnace.output_buffer[Item.INGOT] == 1


def test_belt_capacity_is_respected(line_world) -> None:
    line_world.run_ticks(100)
    for entity in line_world.state.entities.values():
        if entity.type is EntityType.BELT:
            assert entity.total_output() <= line_world.config.belt_capacity


def test_push_conflict_lowest_id_wins() -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=50,
        rock_density=0.0,
        starter_line=False,
    )
    world = _empty_world(config)
    receiver = Entity(id=1, type=EntityType.BELT, x=2, y=4, direction=Direction.EAST)
    source_a = Entity(
        id=2,
        type=EntityType.BELT,
        x=1,
        y=4,
        direction=Direction.EAST,
        output_buffer={Item.ORE: 1},
    )
    source_b = Entity(
        id=3,
        type=EntityType.BELT,
        x=3,
        y=4,
        direction=Direction.WEST,
        output_buffer={Item.ORE: 1},
    )
    for entity in (receiver, source_a, source_b):
        world.state.entities[entity.id] = entity
        world.state.occupancy[(entity.x, entity.y)] = entity.id

    world.tick()

    assert receiver.output_buffer[Item.ORE] == 1
    assert source_a.output_buffer == {}
    assert source_b.output_buffer[Item.ORE] == 1
    assert source_b.blocked_ticks == 1


def test_determinism_with_actions() -> None:
    config = FactoryConfig(width=16, height=8, ticks_per_episode=100, starter_line=False)
    actions = [
        Action(ActionOp.BUILD, EntityType.BELT, 5, 5, Direction.EAST),
        Action(ActionOp.BUILD, EntityType.BELT, 6, 5, Direction.EAST),
        Action(ActionOp.ROTATE, x=6, y=5, direction=Direction.NORTH),
    ]

    def run() -> str:
        world = _empty_world(config, seed=11)
        for action in actions:
            world.apply_action(action)
        world.run_ticks(50)
        return world.state_hash()

    assert run() == run()


def test_episode_stops_at_limit() -> None:
    config = FactoryConfig(width=16, height=8, ticks_per_episode=10)
    world = FactoryWorld(config)
    world.reset(seed=1)
    world.run_ticks(50)
    assert world.state.tick == 10
    assert world.done


def test_buffers_never_negative(line_world) -> None:
    for _ in range(100):
        line_world.tick()
        for entity in line_world.state.entities.values():
            assert all(count >= 0 for count in entity.input_buffer.values())
            assert all(count >= 0 for count in entity.output_buffer.values())
        assert line_world.state.score >= 0


def test_history_window_is_bounded() -> None:
    config = FactoryConfig(width=16, height=8, ticks_per_episode=50, history_window=10)
    world = FactoryWorld(config)
    world.reset(seed=1)
    world.run_ticks(30)
    assert len(world.state.history) == 10
    assert world.state.history[-1][0] == 30
