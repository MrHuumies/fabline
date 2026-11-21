"""Run a short deterministic factory episode."""

from __future__ import annotations

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.world import FactoryWorld


def main() -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
    )
    world = FactoryWorld(config)
    world.reset(seed=0)
    world.run_ticks(100)
    print(f"tick: {world.state.tick}")
    print(f"score: {world.state.score}")
    print(f"delivered: {dict(world.state.delivered)}")
    print(f"state hash: {world.state_hash()}")


if __name__ == "__main__":
    main()
