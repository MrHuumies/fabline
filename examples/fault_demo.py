"""Run a short episode with the opt-in fault mechanic."""

from __future__ import annotations

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.world import FactoryWorld


def main() -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=300,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    faults = FaultConfig(
        enabled=True,
        wear_per_craft=1,
        fault_threshold=5,
        repair_ticks=10,
    )
    world = FactoryWorld(config, faults)
    world.reset(seed=0, scenario=SCENARIOS["gear"])

    for _ in range(200):
        world.tick()
        if any(event.kind == "fault_started" for event in world.state.events):
            break

    fault_events = [
        event for event in world.state.events if event.kind.startswith("fault")
    ]
    print(f"tick: {world.state.tick}")
    print(f"faults: {[event.to_dict() for event in fault_events]}")
    print(f"state hash: {world.state_hash()}")


if __name__ == "__main__":
    main()
