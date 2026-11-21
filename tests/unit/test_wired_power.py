from __future__ import annotations

from fabline.obs.power import (
    POWER_TOPOLOGY_FEATURES,
    POWER_WIRE_CHANNELS,
    PowerTopologyObservation,
    PowerWiresObservation,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import EntityType, Item
from fabline.worlds.factory.wire import (
    entity_connected,
    reachable_cells,
    wire_summary,
)
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


def _power(**kwargs) -> PowerConfig:
    defaults = {
        "enabled": True,
        "topology": "wired",
        "generator_count": 1,
        "generator_capacity": 5,
        "generator_radius": 8,
        "wire_redundancy": 2,
    }
    defaults.update(kwargs)
    return PowerConfig(**defaults)


def _world(power: PowerConfig | None = None) -> FactoryWorld:
    world = FactoryWorld(_config(), power=power or _power())
    world.reset(0, SCENARIOS["gear"])
    return world


def _consumers(world: FactoryWorld):
    return [
        entity
        for entity in sorted(
            world.state.entities.values(), key=lambda item: item.id
        )
        if world.power.demand(entity.type) > 0
    ]


def _base_connected(world: FactoryWorld) -> dict[int, bool]:
    wires = world.state.power_wires
    reachable = reachable_cells(world.state.power_sources[0], wires)
    return {
        entity.id: entity_connected(entity, reachable, wires)
        for entity in _consumers(world)
    }


def _outage(world: FactoryWorld, wire_id: int) -> list[int]:
    base = _base_connected(world)
    wire = next(
        item for item in world.state.power_wires if item.id == wire_id
    )
    wire.failed = True
    wires = world.state.power_wires
    reachable = reachable_cells(world.state.power_sources[0], wires)
    lost = [
        entity.id
        for entity in _consumers(world)
        if base[entity.id] and not entity_connected(entity, reachable, wires)
    ]
    wire.failed = False
    return lost


def test_wired_generation_is_deterministic_and_connected() -> None:
    first = _world()
    second = _world()
    assert first.state.power_wires
    assert [
        (wire.ax, wire.ay, wire.bx, wire.by)
        for wire in first.state.power_wires
    ] == [
        (wire.ax, wire.ay, wire.bx, wire.by)
        for wire in second.state.power_wires
    ]
    assert first.state.state_hash() == second.state.state_hash()
    summary = wire_summary(first.state.power_wires)
    assert summary.wire_count > 0
    assert summary.component_count == 1
    assert summary.redundancy >= 1
    assert all(_base_connected(first).values())


def test_wire_faults_split_bridges_and_reroute_loops() -> None:
    world = _world()
    outages = {
        wire.id: _outage(world, wire.id)
        for wire in world.state.power_wires
    }
    assert any(outages.values())
    assert any(not lost for lost in outages.values())
    assert len({tuple(lost) for lost in outages.values()}) > 2


def test_scheduled_wire_fault_browns_out_downstream_consumer() -> None:
    world = _world()
    losing = {
        wire.id: _outage(world, wire.id)
        for wire in world.state.power_wires
    }
    wire_id = next(
        wire_id for wire_id, lost in losing.items() if lost
    )
    world = FactoryWorld(
        _config(),
        power=_power(wire_fault_tick=1, wire_fault_id=wire_id),
    )
    world.reset(0, SCENARIOS["gear"])
    for entity in world.state.entities.values():
        if entity.type is EntityType.BELT:
            entity.output_buffer[Item.INGOT] = 1
        elif entity.type in (EntityType.FURNACE, EntityType.ASSEMBLER):
            entity.craft_progress = 1
    downstream = set(losing[wire_id])
    world.run_ticks(1)
    assert next(
        wire
        for wire in world.state.power_wires
        if wire.id == wire_id
    ).failed
    for entity in _consumers(world):
        if entity.id in downstream:
            assert entity.powered is False
            assert entity.brownout_ticks > 0
    assert any(
        event.kind == "power_wire_fault" for event in world.state.events
    )


def test_wire_observations_shapes_and_ranges() -> None:
    world = _world()
    topology = PowerTopologyObservation(
        world.config, world.power
    ).observe(world.state)
    assert topology.shape == (len(POWER_TOPOLOGY_FEATURES),)
    assert 0.0 <= float(topology.min()) <= float(topology.max()) <= 1.0
    wires = PowerWiresObservation(world.config, world.power).observe(
        world.state
    )
    assert wires.shape == (
        world.state.height,
        world.state.width,
        len(POWER_WIRE_CHANNELS),
    )
    assert 0.0 <= float(wires.min()) <= float(wires.max()) <= 1.0
    assert wires[..., 3].any()


def test_radius_mode_has_no_wires() -> None:
    world = _world(
        _power(topology="radius", generator_count=2, generator_capacity=12)
    )
    assert world.state.power_wires == []
    assert "power_wires" not in world.state.canonical()
