from __future__ import annotations

import json

from fabline.cli.browser import (
    find_replays,
    find_task_cards,
    format_replay_table,
    format_task_card_table,
    resolve_task_card,
    summarize_replay,
)


def test_replay_browser_lists_and_summarizes(tmp_path) -> None:
    nested = tmp_path / "a"
    nested.mkdir()
    replay = nested / "replay.json"
    replay.write_text(
        json.dumps(
            {
                "seed": 7,
                "actions": [1, 2, 3],
                "state_hashes": ["a", "b", "c"],
                "sample_ticks": [0, 10, 20],
                "scenario": "gear",
            }
        ),
        encoding="utf-8",
    )
    paths = find_replays(tmp_path)
    assert paths == [replay.resolve()]
    summary = summarize_replay(replay)
    assert summary.seed == 7
    assert summary.actions == 3
    assert summary.kind == "factory"
    assert "gear" in format_replay_table([summary])


def test_task_card_browser_lists_and_resolves(tmp_path) -> None:
    card = tmp_path / "example.md"
    card.write_text(
        "# Task card — example\n\n"
        "- **Task ID:** `factory.example.v1`\n"
        "- **Status:** test\n",
        encoding="utf-8",
    )
    cards = find_task_cards(tmp_path)
    assert len(cards) == 1
    assert resolve_task_card(cards, "1") is cards[0]
    assert resolve_task_card(cards, "factory.example.v1") is cards[0]
    assert "example" in format_task_card_table(cards)
