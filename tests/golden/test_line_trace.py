from __future__ import annotations

from fabline.worlds.factory.state import Item


def test_known_line_trace(line_world) -> None:
    """A fixed line should produce a known, stable trace.

    This is intentionally a golden test: if tick ordering, crafting, or
    logistics change, this test should fail and force an explicit update.
    """

    line_world.run_ticks(100)

    assert line_world.state.score == 40
    assert line_world.state.delivered[Item.GEAR] == 4
    assert line_world.state.delivered[Item.INGOT] == 0
    assert line_world.state.state_hash() == (
        "00341ed3aeb75fe4d1649e706cf7e94bac134858420d0b7f6c37168192ced2de"
    )

    delivered = [event.tick for event in line_world.state.events if event.kind == "item_delivered"]
    assert delivered == [38, 56, 74, 92]

    started = [event.tick for event in line_world.state.events if event.kind == "craft_started"]
    assert started[:4] == [6, 15, 24, 25]
