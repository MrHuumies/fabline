"""Headless replay and task-card browsing helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReplaySummary:
    path: Path
    seed: int | None
    scenario: str
    actions: int
    hashes: int
    kind: str
    faults: bool
    power: bool
    control: bool
    world_version: str


@dataclass(frozen=True)
class TaskCardSummary:
    path: Path
    title: str
    task_id: str
    status: str


def find_replays(root: str | Path) -> list[Path]:
    path = Path(root)
    if not path.exists():
        return []
    candidates = {
        candidate.resolve()
        for candidate in path.rglob("replay.json")
        if candidate.is_file()
    }
    return sorted(candidates)


def summarize_replay(path: str | Path) -> ReplaySummary:
    replay_path = Path(path)
    data = json.loads(replay_path.read_text(encoding="utf-8"))
    actions = data.get("actions", [])
    hashes = data.get("state_hashes", [])
    if "control" in data:
        kind = "control"
    elif "sample_ticks" in data or hashes:
        kind = "factory"
    else:
        kind = "unknown"
    return ReplaySummary(
        path=replay_path,
        seed=int(data["seed"]) if "seed" in data else None,
        scenario=str(data.get("scenario", "")),
        actions=len(actions) if isinstance(actions, list) else 0,
        hashes=len(hashes) if isinstance(hashes, list) else 0,
        kind=kind,
        faults=bool(data.get("faults")),
        power=bool(data.get("power")),
        control=bool(data.get("control")),
        world_version=str(data.get("world_version", "")),
    )


def format_replay_table(
    replays: list[ReplaySummary],
    *,
    limit: int = 50,
) -> str:
    lines = [
        "replay | kind | seed | actions | hashes | scenario | flags",
        "---|---|---:|---:|---:|---|---",
    ]
    for replay in replays[:limit]:
        flags = []
        if replay.faults:
            flags.append("faults")
        if replay.power:
            flags.append("power")
        if replay.control:
            flags.append("control")
        lines.append(
            f"{replay.path} | {replay.kind} | "
            f"{'-' if replay.seed is None else replay.seed} | "
            f"{replay.actions} | {replay.hashes} | "
            f"{replay.scenario or '-'} | {','.join(flags) or '-'}"
        )
    if len(replays) > limit:
        lines.append(f"... {len(replays) - limit} more")
    return "\n".join(lines)


def find_task_cards(root: str | Path) -> list[TaskCardSummary]:
    path = Path(root)
    if not path.exists():
        return []
    cards: list[TaskCardSummary] = []
    for card_path in sorted(path.glob("*.md")):
        if not card_path.is_file() or card_path.name == "README.md":
            continue
        title = ""
        task_id = ""
        status = ""
        for line in card_path.read_text(encoding="utf-8").splitlines():
            if not title and line.startswith("# "):
                title = line[2:].strip()
            if line.startswith("- **Task ID:**"):
                task_id = line.split(":", 1)[1].strip(" *`")
            if line.startswith("- **Status:**"):
                status = line.split(":", 1)[1].strip(" *`")
        cards.append(
            TaskCardSummary(
                path=card_path,
                title=title or card_path.stem,
                task_id=task_id,
                status=status,
            )
        )
    return cards


def format_task_card_table(cards: list[TaskCardSummary]) -> str:
    lines = [
        "# | card | task | status",
        "---:|---|---|---",
    ]
    for index, card in enumerate(cards, start=1):
        lines.append(
            f"{index} | {card.path.stem} | {card.task_id or '-'} | "
            f"{card.status or '-'}"
        )
    return "\n".join(lines)


def resolve_task_card(
    cards: list[TaskCardSummary],
    query: str,
) -> TaskCardSummary | None:
    query = query.strip()
    if not query:
        return None
    if query.isdigit():
        index = int(query) - 1
        if 0 <= index < len(cards):
            return cards[index]
        return None
    for card in cards:
        if card.path.stem == query:
            return card
    for card in cards:
        if query in card.path.stem or query == card.task_id:
            return card
    return None


def read_task_card(card: TaskCardSummary) -> str:
    return card.path.read_text(encoding="utf-8")
