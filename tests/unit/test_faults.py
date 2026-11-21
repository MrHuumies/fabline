from __future__ import annotations

import numpy as np

from fabline.obs.sensors import (
    DiagnosticsObservation,
    SensorsObservation,
    TopKEntitySensorsObservation,
)
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.state import EntityType


def _faulty_world(line_world):
    line_world.faults = FaultConfig(
        enabled=True,
        wear_per_craft=1,
        fault_threshold=3,
        repair_ticks=5,
    )
    return line_world


def test_fault_starts_then_repairs(line_world) -> None:
    world = _faulty_world(line_world)
    entity = None
    for _ in range(200):
        faulted = [e for e in world.state.entities.values() if e.faulted]
        if faulted:
            entity = faulted[0]
            break
        world.tick()
    assert entity is not None
    assert entity.wear >= 3
    assert any(
        event.kind == "fault_started" for event in world.state.events
    )
    world.run_ticks(5)
    assert not entity.faulted
    assert entity.wear == 0
    assert any(event.kind == "fault_repaired" for event in world.state.events)


def test_fault_free_world_has_no_fault_events(line_world) -> None:
    line_world.run_ticks(120)
    assert not any(
        event.kind in ("fault_started", "fault_repaired")
        for event in line_world.state.events
    )
    assert all(entity.wear == 0 for entity in line_world.state.entities.values())
    assert all(
        (entity.temperature, entity.vibration, entity.acoustic) == (0, 0, 0)
        for entity in line_world.state.entities.values()
    )
    sensors = SensorsObservation(line_world.config, line_world.faults).observe(
        line_world.state
    )
    assert not sensors.any()
    top = TopKEntitySensorsObservation(
        line_world.config, line_world.faults
    ).observe(line_world.state)
    assert not top.any()


def test_top_k_entity_sensors_order_and_features(line_world) -> None:
    line_world.faults = FaultConfig(enabled=True)
    furnace = line_world.state.entity_at(3, 4)
    assembler = line_world.state.entity_at(5, 4)
    miner = line_world.state.entity_at(1, 4)
    assert furnace is not None and assembler is not None and miner is not None
    furnace.acoustic = 90
    furnace.wear = 10
    furnace.faulted = True
    assembler.acoustic = 60
    miner.acoustic = 30

    view = TopKEntitySensorsObservation(line_world.config, line_world.faults)
    observation = view.observe(line_world.state)
    assert observation.shape == (4, 8)
    assert view.flatten(observation).shape == (32,)
    assert view.spec.version == "0.1.0"
    assert view.spec.name == "entity_sensors_top4"

    assert observation[0, 0] == 1.0
    assert observation[0, 1] == 0.9
    assert observation[0, 4] == 0.5  # wear / threshold
    assert observation[0, 5] == 1.0
    assert observation[0, 7] == int(EntityType.FURNACE) / 5
    assert observation[1, 1] == 0.6
    assert observation[1, 7] == int(EntityType.ASSEMBLER) / 5
    assert observation[2, 1] == 0.3
    assert observation[2, 7] == int(EntityType.MINER) / 5


def test_sensor_state_changes_hash(line_world) -> None:
    before = line_world.state_hash()
    entity = next(iter(line_world.state.entities.values()))
    entity.temperature = 1
    assert line_world.state_hash() != before
    entity.temperature = 0
    assert line_world.state_hash() == before


def test_sensor_dynamics_decay_and_warm(line_world) -> None:
    line_world.faults = FaultConfig(
        enabled=True,
        wear_per_craft=1,
        fault_threshold=3,
        repair_ticks=5,
    )
    belt = line_world.state.entity_at(2, 4)
    assert belt is not None
    belt.temperature = 100
    belt.vibration = 100
    belt.acoustic = 100

    line_world.tick()
    assert belt.temperature == 93  # (15 * 100 + 0) // 16
    assert belt.vibration == 75  # 3 * 100 // 4
    assert belt.acoustic == 87  # 7 * 100 // 8

    world = _faulty_world(line_world)
    for _ in range(200):
        world.tick()
        if any(entity.faulted for entity in world.state.entities.values()):
            break
    faulted = next(
        entity for entity in world.state.entities.values() if entity.faulted
    )
    assert faulted.temperature > 0
    assert faulted.acoustic > 0
    assert any(
        event.kind == "craft_started" for event in world.state.events
    )
    assert any(
        entity.vibration > 0 for entity in world.state.entities.values()
    )


def test_fault_fields_change_hash(line_world) -> None:
    before = line_world.state_hash()
    entity = next(iter(line_world.state.entities.values()))
    entity.wear = 1
    assert line_world.state_hash() != before
    entity.wear = 0
    assert line_world.state_hash() == before


def test_sensor_views_show_fault(line_world) -> None:
    world = _faulty_world(line_world)
    faulted = None
    for _ in range(200):
        candidates = [e for e in world.state.entities.values() if e.faulted]
        if candidates:
            faulted = candidates[0]
            break
        world.tick()
    assert faulted is not None
    sensors_view = SensorsObservation(world.config, world.faults)
    assert sensors_view.spec.version == "0.2.0"
    sensors = sensors_view.observe(world.state)
    assert sensors.shape == (world.state.height, world.state.width, 5)
    assert sensors[faulted.y, faulted.x, 4] == 1.0
    assert 0.0 <= sensors.min() <= sensors.max() <= 1.0
    assert sensors[faulted.y, faulted.x, 1] == faulted.temperature / 100.0
    assert sensors[faulted.y, faulted.x, 2] == faulted.vibration / 100.0
    assert sensors[faulted.y, faulted.x, 3] == faulted.acoustic / 100.0

    diagnostics_view = DiagnosticsObservation(world.config, world.faults)
    assert diagnostics_view.spec.version == "0.2.0"
    diagnostics = diagnostics_view.observe(world.state)
    assert diagnostics.shape == (13,)
    assert diagnostics[2] > 0.0
    assert np.all(np.isfinite(diagnostics))


def test_fault_prediction_task_labels(small_config) -> None:
    from fabline.tasks.fault_prediction import FaultPredictionTask, FaultTaskConfig

    config = small_config
    config = type(config)(
        **{**config.as_dict(), "ticks_per_episode": 500, "starter_line": True}
    )
    faults = FaultConfig(
        enabled=True,
        wear_per_craft=1,
        fault_threshold=5,
        repair_ticks=10,
    )
    task = FaultPredictionTask(
        config,
        FaultTaskConfig(
            warmup_ticks=50,
            episode_ticks=400,
            sample_interval=10,
            horizon=30,
            faults=faults,
        ),
        DiagnosticsObservation(config, faults),
    )
    episodes = task.generate(4)
    labels = np.concatenate([episode.labels for episode in episodes])
    assert set(np.unique(labels).tolist()) <= {0.0, 1.0}
    assert labels.max() == 1.0
    assert episodes[0].observations.shape[1] == 13
    assert episodes[0].meta["faults"]["enabled"] is True
