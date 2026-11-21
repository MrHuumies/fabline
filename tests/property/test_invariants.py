from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from fabline.worlds.factory.actions import Action, ActionError, ActionOp
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import Direction, EntityType
from fabline.worlds.factory.world import FactoryWorld

CONFIG = FactoryConfig(
    width=12,
    height=8,
    ticks_per_episode=80,
    entity_budget=16,
    rock_density=0.0,
    ore_patches=1,
    starter_line=False,
)

BUILD_ENTITIES = [
    EntityType.MINER,
    EntityType.BELT,
    EntityType.FURNACE,
    EntityType.ASSEMBLER,
]


def _check_invariants(world: FactoryWorld) -> None:
    state = world.state
    assert len(state.entities) == len(state.occupancy)
    assert state.score >= 0
    assert len(state.history) <= world.config.history_window
    for entity_id, entity in state.entities.items():
        assert state.in_bounds(entity.x, entity.y)
        assert state.occupancy[(entity.x, entity.y)] == entity_id
        assert all(count >= 0 for count in entity.input_buffer.values())
        assert all(count >= 0 for count in entity.output_buffer.values())
        if entity.type is EntityType.BELT:
            assert entity.total_output() <= world.config.belt_capacity


@settings(max_examples=30, deadline=None)
@given(
    seed=st.integers(min_value=0, max_value=1000),
    actions=st.lists(
        st.tuples(
            st.sampled_from(list(ActionOp)),
            st.sampled_from(BUILD_ENTITIES),
            st.integers(min_value=-1, max_value=13),
            st.integers(min_value=-1, max_value=9),
            st.sampled_from(list(Direction)),
        ),
        max_size=20,
    ),
)
def test_action_sequences_preserve_invariants(seed, actions) -> None:
    world = FactoryWorld(CONFIG)
    world.reset(seed)
    for op, entity, x, y, direction in actions:
        if op is ActionOp.BUILD:
            action = Action(op, entity, x, y, direction)
        elif op is ActionOp.REMOVE:
            action = Action(op, x=x, y=y)
        elif op is ActionOp.ROTATE:
            action = Action(op, x=x, y=y, direction=direction)
        elif op is ActionOp.REPAIR:
            action = Action(op, x=x, y=y)
        else:
            action = Action.noop()

        before = world.state_hash()
        try:
            world.apply_action(action)
        except ActionError:
            assert world.state_hash() == before
        _check_invariants(world)
    world.run_ticks(20)
    _check_invariants(world)


@settings(max_examples=20, deadline=None)
@given(seed=st.integers(min_value=0, max_value=10_000))
def test_generator_is_deterministic_for_any_seed(seed) -> None:
    config = FactoryConfig(width=12, height=8)
    first = FactoryWorld(config)
    second = FactoryWorld(config)
    first.reset(seed)
    second.reset(seed)
    assert first.state_hash() == second.state_hash()


@settings(max_examples=10, deadline=None)
@given(seed=st.integers(min_value=0, max_value=1000))
def test_items_never_negative(seed) -> None:
    world = FactoryWorld(CONFIG)
    world.reset(seed)
    for _ in range(30):
        world.tick()
        for entity in world.state.entities.values():
            assert all(count >= 0 for count in entity.input_buffer.values())
            assert all(count >= 0 for count in entity.output_buffer.values())
    assert world.state.score >= 0
