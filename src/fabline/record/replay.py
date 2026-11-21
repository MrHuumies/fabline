"""Replay validation from seed plus actions."""

from __future__ import annotations

from typing import Any

from fabline.worlds.factory.actions import Action, ActionOp
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import Direction, EntityType
from fabline.worlds.factory.world import FactoryWorld


class ReplayMismatch(RuntimeError):
    def __init__(self, tick: int, expected: str, actual: str) -> None:
        super().__init__(
            f"replay mismatch at tick {tick}: expected {expected}, got {actual}"
        )
        self.tick = tick
        self.expected = expected
        self.actual = actual


def action_from_dict(data: dict[str, Any]) -> Action:
    op = ActionOp[str(data["op"]).upper()]
    if op is ActionOp.NOOP:
        return Action(ActionOp.NOOP)
    if op is ActionOp.BUILD:
        return Action(
            ActionOp.BUILD,
            entity=EntityType[str(data["entity"]).upper()],
            x=int(data["x"]),
            y=int(data["y"]),
            direction=Direction[str(data["direction"]).upper()],
        )
    if op is ActionOp.REMOVE:
        return Action(ActionOp.REMOVE, x=int(data["x"]), y=int(data["y"]))
    if op is ActionOp.ROTATE:
        return Action(
            ActionOp.ROTATE,
            x=int(data["x"]),
            y=int(data["y"]),
            direction=Direction[str(data["direction"]).upper()],
        )
    if op is ActionOp.REPAIR:
        return Action(ActionOp.REPAIR, x=int(data["x"]), y=int(data["y"]))
    raise ValueError(f"unknown action op: {data['op']}")


def validate_replay(world: FactoryWorld, replay: dict[str, Any]) -> None:
    """Re-run an episode and compare state hashes at the sampled ticks."""

    seed = int(replay["seed"])
    sample_ticks = [int(tick) for tick in replay["sample_ticks"]]
    state_hashes = list(replay["state_hashes"])
    if len(sample_ticks) != len(state_hashes):
        raise ValueError("sample_ticks and state_hashes must have the same length")

    targets = dict(zip(sample_ticks, state_hashes, strict=True))
    actions_by_tick: dict[int, list[Action]] = {}
    for entry in replay.get("actions", []):
        tick = int(entry.get("t", 0))
        actions_by_tick.setdefault(tick, []).append(action_from_dict(entry))

    scenario_name = replay.get("scenario")
    scenario = SCENARIOS[scenario_name] if scenario_name else None
    fault_data = replay.get("faults")
    if fault_data is not None:
        world.faults = FaultConfig.from_dict(fault_data)
    power_data = replay.get("power")
    if power_data is not None:
        world.power = PowerConfig.from_dict(power_data)
    world.reset(seed, scenario)

    def check_current() -> None:
        expected = targets.get(world.state.tick)
        if expected is None:
            return
        actual = world.state_hash()
        if actual != expected:
            raise ReplayMismatch(world.state.tick, expected, actual)

    check_current()
    if not sample_ticks:
        return

    max_tick = max(sample_ticks)
    while world.state.tick < max_tick:
        for action in actions_by_tick.get(world.state.tick, []):
            world.apply_action(action)
        world.tick()
        check_current()
