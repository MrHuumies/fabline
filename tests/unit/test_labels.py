from __future__ import annotations

from fabline.worlds.factory.labels import future_delivered, future_score
from fabline.worlds.factory.state import Item


def test_future_score_matches_manual_rollout(line_world) -> None:
    line_world.run_ticks(60)
    clone = line_world.clone()
    start = clone.state.score
    clone.run_ticks(50)
    expected = clone.state.score - start
    assert future_score(line_world, horizon=50) == expected


def test_future_score_is_pure(line_world) -> None:
    before = line_world.state_hash()
    future_score(line_world, horizon=30)
    assert line_world.state_hash() == before


def test_future_delivered(line_world) -> None:
    line_world.run_ticks(60)
    clone = line_world.clone()
    start = clone.state.delivered[Item.GEAR]
    clone.run_ticks(50)
    expected = clone.state.delivered[Item.GEAR] - start
    assert future_delivered(line_world, Item.GEAR, horizon=50) == expected


def test_labels_are_non_negative(line_world) -> None:
    for _ in range(20):
        line_world.run_ticks(10)
        assert future_score(line_world, horizon=20) >= 0
