"""Run a short episode with the opt-in power grid."""

from __future__ import annotations

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
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
    power = PowerConfig(
        enabled=True,
        generator_count=1,
        generator_capacity=9,
        generator_radius=8,
    )
    world = FactoryWorld(config, power=power)
    world.reset(seed=0, scenario=SCENARIOS["gear"])
    world.run_ticks(200)

    brownouts = [
        event for event in world.state.events if event.kind == "power_brownout"
    ]
    active = [
        entity
        for entity in world.state.entities.values()
        if power.active_demand(entity) > 0 and not entity.faulted
    ]
    print(f"tick: {world.state.tick}")
    print(f"sources: {world.state.power_sources}")
    print(f"powered: {sum(1 for entity in active if entity.powered)}/{len(active)}")
    print(f"brownout events: {len(brownouts)}")
    print(f"state hash: {world.state_hash()}")


if __name__ == "__main__":
    main()
