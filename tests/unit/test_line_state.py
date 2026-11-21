from __future__ import annotations

import numpy as np

from fabline.obs.base import build_observation
from fabline.obs.line import LineStateObservation
from fabline.worlds.factory.state import EntityType, Item


def test_line_state_observation(line_world) -> None:
    assembler = next(
        entity
        for entity in line_world.state.entities.values()
        if entity.type is EntityType.ASSEMBLER
    )
    furnace = next(
        entity
        for entity in line_world.state.entities.values()
        if entity.type is EntityType.FURNACE
    )
    miner = next(
        entity
        for entity in line_world.state.entities.values()
        if entity.type is EntityType.MINER
    )
    assembler.input_buffer[Item.INGOT] = 3
    assembler.craft_progress = 6
    furnace.output_buffer[Item.INGOT] = 1
    furnace.craft_progress = 4
    miner.output_buffer[Item.ORE] = 1

    view = LineStateObservation(line_world.config)
    values = view.observe(line_world.state)
    assert values.shape == (6,)
    assert view.spec.shape == (6,)
    assert 0.0 <= values.min() <= values.max() <= 1.0
    assert values[0] == 0.5  # assembler input 3 / capacity 6
    assert values[1] == 0.5  # furnace output 1 / capacity 2
    assert values[2] == 0.5  # assembler craft 6 / 12
    assert values[3] == 0.5  # furnace craft 4 / 8
    assert values[4] == 1.0  # miner output 1 / capacity 1
    assert values[5] == 0.0  # belts are not carrying

    assert isinstance(
        build_observation("line_state", line_world.config),
        LineStateObservation,
    )
    assert np.all(np.isfinite(values))
