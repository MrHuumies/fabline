from __future__ import annotations

import json

from fabline.env.control import ControlConfig
from fabline.harness.human_demos import (
    make_scripted_demos,
    train_human_bc,
)
from fabline.record.human import (
    load_human_demos,
    validate_control_replay,
    write_human_demos,
)
from fabline.worlds.factory.config import FactoryConfig


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=300,
        rock_density=0.0,
        starter_line=False,
    )


def test_scripted_demos_roundtrip_validate_and_clone(tmp_path) -> None:
    config = _config()
    control = ControlConfig(episode_ticks=300)
    demos = make_scripted_demos(config, control, episodes=5, seed=0)
    manifest = write_human_demos(
        tmp_path / "demos",
        "demo-test",
        demos,
        config,
        control,
    )
    assert manifest["demos"] == 5
    assert manifest["transitions"] == 150
    assert manifest["success_rate"] == 1.0

    dataset = load_human_demos(tmp_path / "demos")
    assert dataset.X.shape == (150, 49)
    assert dataset.actions.shape == (150,)
    assert set(dataset.sources) == {"scripted"}

    from fabline.env.control import ControlEnv

    env = ControlEnv(config, control)
    for demo in demos:
        replay = json.loads(
            (
                tmp_path
                / "demos"
                / "demos"
                / demo.demo_id
                / "replay.json"
            ).read_text(encoding="utf-8")
        )
        validate_control_replay(env, replay)

    results = train_human_bc(
        tmp_path / "demos",
        config,
        control,
        episodes=2,
        seed=0,
    )
    assert results["metrics"]["success_rate"] == 1.0


def test_demo_writer_appends_across_calls(tmp_path) -> None:
    config = _config()
    control = ControlConfig(episode_ticks=300)
    first = make_scripted_demos(config, control, episodes=2, seed=0)
    write_human_demos(tmp_path / "demos", "append-test", first, config, control)
    second = make_scripted_demos(config, control, episodes=3, seed=10)
    manifest = write_human_demos(
        tmp_path / "demos",
        "append-test",
        second,
        config,
        control,
    )
    assert manifest["demos"] == 5
    assert manifest["sources"] == {"scripted": 5}
