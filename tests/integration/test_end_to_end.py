from __future__ import annotations

import json

import pytest

from fabline.cli.main import main
from fabline.core.hashing import config_hash
from fabline.harness.data import load_dataset
from fabline.harness.runner import run_throughput_benchmark
from fabline.obs.vector import FEATURES, VectorObservation
from fabline.record.replay import ReplayMismatch, action_from_dict, validate_replay
from fabline.record.writer import write_dataset
from fabline.tasks.throughput import ThroughputConfig, ThroughputTask
from fabline.version import WORLD_VERSION
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import TileType
from fabline.worlds.factory.world import FactoryWorld


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=200,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.02,
        ore_patches=2,
        starter_line=True,
    )


def test_generate_write_load_and_benchmark(tmp_path) -> None:
    config = _config()
    adapter = VectorObservation(config)
    task = ThroughputTask(
        config,
        ThroughputConfig(horizon=50, warmup_ticks=50, episode_ticks=200),
        adapter,
    )
    episodes = task.generate(12, seed_start=0)
    manifest = write_dataset(
        tmp_path / "dataset",
        "test-dataset",
        episodes,
        {
            "world_version": WORLD_VERSION,
            "config_hash": config_hash(config),
            "task_id": task.id,
            "task_version": task.version,
            "observation": {
                "name": adapter.spec.name,
                "version": adapter.spec.version,
                "shape": list(adapter.spec.shape),
                "feature_names": list(adapter.spec.feature_names),
            },
        },
    )
    assert manifest["episodes"] == 12
    assert manifest["stats"]["samples"] > 0
    assert (tmp_path / "dataset" / "manifest.json").exists()
    assert (tmp_path / "dataset" / "dataset_card.md").exists()

    loaded = load_dataset(tmp_path / "dataset")
    assert loaded.X.shape[1] == len(FEATURES)
    assert loaded.y.shape[0] == loaded.X.shape[0]
    assert set(loaded.splits) == {"train", "val", "test"}
    assert loaded.feature_names == FEATURES

    results = run_throughput_benchmark(loaded, tmp_path / "report")
    assert set(results) == {"mean", "persistence", "linear"}
    report = (tmp_path / "report" / "report.md").read_text()
    assert "Benchmark report" in report
    assert "persistence" in report


def test_replays_validate_and_fail_loudly(tmp_path) -> None:
    config = _config()
    adapter = VectorObservation(config)
    task = ThroughputTask(
        config,
        ThroughputConfig(horizon=50, warmup_ticks=50, episode_ticks=200),
        adapter,
    )
    episode = task.generate_episode(3)
    replay = {
        "seed": episode.seed,
        "sample_ticks": episode.sample_ticks,
        "state_hashes": episode.state_hashes,
        "actions": [],
    }
    world = FactoryWorld(config)
    validate_replay(world, replay)

    broken = dict(replay)
    broken["state_hashes"] = list(replay["state_hashes"])
    broken["state_hashes"][0] = "0" * 64
    with pytest.raises(ReplayMismatch):
        validate_replay(world, broken)


def test_replay_with_an_action() -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=20,
        rock_density=0.0,
        ore_patches=1,
        ore_patch_radius=0,
        starter_line=False,
    )
    world = FactoryWorld(config)
    world.reset(seed=0)
    empty = next(
        (x, y)
        for y in range(1, config.height - 1)
        for x in range(1, config.width - 1)
        if (x, y) not in world.state.occupancy
        and world.state.tile_at(x, y) is TileType.EMPTY
    )
    action = {
        "t": 0,
        "op": "build",
        "entity": "belt",
        "x": empty[0],
        "y": empty[1],
        "direction": "east",
    }

    replay = {"seed": 0, "sample_ticks": [0, 1, 5], "state_hashes": [], "actions": [action]}
    replay["state_hashes"].append(world.state_hash())

    world.apply_action(action_from_dict(action))
    world.tick()
    replay["state_hashes"].append(world.state_hash())
    world.run_ticks(4)
    replay["state_hashes"].append(world.state_hash())

    validate_replay(world, replay)


def test_cli_smoke_and_dataset(tmp_path, capsys) -> None:
    assert main(["smoke", "--ticks", "20", "--seed", "1"]) == 0
    smoke = json.loads(capsys.readouterr().out)
    assert smoke["deterministic"] is True
    assert smoke["ticks"] == 20

    out = tmp_path / "cli-dataset"
    assert (
        main(
            [
                "dataset",
                "--episodes",
                "12",
                "--seed-start",
                "0",
                "--warmup",
                "20",
                "--horizon",
                "20",
                "--ticks",
                "80",
                "--interval",
                "10",
                "--out",
                str(out),
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["episodes"] == 12
    assert summary["replays_validated"] == 12
    assert (out / "manifest.json").exists()

    report = tmp_path / "cli-report"
    assert main(["benchmark", "--dataset", str(out), "--out", str(report)]) == 0
    assert (report / "report.md").exists()
