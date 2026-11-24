from __future__ import annotations

import json

from fabline.env.crew_replan import CrewReplanConfig
from fabline.harness.crew_decentralized import (
    run_decentralized_compact,
    write_decentralized_compact_report,
)
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.power import PowerConfig


def test_compact_decentralized_smoke(tmp_path) -> None:
    config = FactoryConfig(
        width=48,
        height=24,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=48,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    replan = CrewReplanConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=90,
        small_failure_tick=110,
        large_failure_tick=130,
        recall_tick=100,
        success_score=600,
        randomize_crew_b=True,
        crew_b_min_distance=8,
        scenario="spread_gear",
        power=PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=48,
            generator_radius=8,
            wire_redundancy=2,
        ),
    )
    results = run_decentralized_compact(
        config,
        replan,
        seeds=(56000,),
        q_seeds=(0,),
        train_episodes=2,
    )
    assert set(results) == {
        "local_nearest",
        "local_greedy",
        "local_aware",
        "private_q_1000",
        "compact_q",
        "compact_ensemble",
        "global_oracle",
    }
    assert "per_policy" in results["compact_q"]
    report = write_decentralized_compact_report(
        tmp_path,
        results,
        config={
            "width": 48,
            "height": 24,
            "radius": 16,
            "seeds": [56000],
            "q_seeds": [0],
            "train_episodes": 2,
            "train_seed_start": 60000,
            "success_score": 600,
        },
    )
    assert report.exists()
    payload = json.loads(
        (tmp_path / "decentralized_compact_results.json").read_text()
    )
    assert payload["results"]["global_oracle"]["mean_score"] > 0
