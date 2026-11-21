"""Generate a small materialized dataset with the vector observation."""

from __future__ import annotations

import argparse
from pathlib import Path

from fabline.harness.data import load_dataset
from fabline.obs.base import build_observation
from fabline.record.replay import validate_replay
from fabline.record.writer import write_dataset
from fabline.tasks.meta import manifest_meta
from fabline.tasks.throughput import ThroughputConfig, ThroughputTask
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.world import FactoryWorld


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="datasets/example")
    parser.add_argument("--episodes", type=int, default=4)
    args = parser.parse_args()

    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )
    observation = build_observation("vector", config)
    task = ThroughputTask(
        config,
        ThroughputConfig(
            warmup_ticks=100,
            episode_ticks=300,
            sample_interval=10,
            horizon=50,
        ),
        observation,
    )
    episodes = task.generate(args.episodes, seed_start=0)
    manifest = write_dataset(
        args.out,
        "fabline-example",
        episodes,
        manifest_meta(config, task, observation, "future_score"),
    )

    world = FactoryWorld(config)
    for episode in episodes:
        validate_replay(
            world,
            {
                "seed": episode.seed,
                "sample_ticks": episode.sample_ticks,
                "state_hashes": episode.state_hashes,
                "actions": [],
            },
        )

    loaded = load_dataset(args.out)
    print(f"wrote {Path(args.out)}")
    print(f"episodes: {manifest['episodes']}")
    print(f"samples: {len(loaded.y)}")
    print(f"replays validated: {len(episodes)}")


if __name__ == "__main__":
    main()
