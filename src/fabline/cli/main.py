"""The ``fabline`` command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fabline import __version__
from fabline.env.control import ControlConfig
from fabline.env.crew_replan import CrewReplanConfig
from fabline.env.crew_schedule import CrewScheduleConfig
from fabline.env.fault_power import FaultPowerConfig
from fabline.env.fault_recovery import FaultRecoveryConfig
from fabline.env.multi_crew import MultiCrewConfig
from fabline.env.power_allocation import PowerAllocationConfig
from fabline.env.preventive_fault import PreventiveFaultConfig
from fabline.env.preventive_threshold import ThresholdConfig
from fabline.env.preventive_wire import PreventiveWireConfig
from fabline.env.wire_repair import WireRepairConfig
from fabline.harness.crew_layout_q import (
    run_crew_layout_q,
    write_crew_layout_q_report,
)
from fabline.harness.crew_replan import (
    run_crew_replan,
    write_crew_replan_report,
)
from fabline.harness.crew_schedule import (
    run_crew_schedule,
    write_crew_report,
)
from fabline.harness.data import load_dataset
from fabline.harness.fault_power import (
    run_fault_power,
    write_fault_power_report,
)
from fabline.harness.fault_recovery import (
    run_fault_recovery,
    write_fault_recovery_report,
)
from fabline.harness.faults import run_fault_benchmark
from fabline.harness.human_demos import (
    make_scripted_demos,
    train_human_bc,
    write_human_bc_report,
)
from fabline.harness.multi_crew import (
    run_crew_robustness,
    run_multi_crew,
    write_crew_robustness_report,
    write_multi_crew_report,
)
from fabline.harness.power import run_power_benchmark
from fabline.harness.power_allocation import (
    run_power_allocation,
    write_power_allocation_report,
)
from fabline.harness.preventive_fault import (
    run_preventive_fault,
    write_preventive_fault_report,
)
from fabline.harness.preventive_threshold import (
    run_threshold_selection,
    write_threshold_report,
)
from fabline.harness.preventive_wire import (
    run_preventive_wire,
    write_preventive_wire_report,
)
from fabline.harness.runner import run_throughput_benchmark
from fabline.harness.shared_suite import SharedSuiteConfig, run_shared_suite
from fabline.harness.suite import SuiteConfig, run_suite
from fabline.harness.wire_repair import (
    run_wire_repair,
    write_wire_repair_report,
)
from fabline.obs.base import build_observation
from fabline.record.replay import validate_replay
from fabline.record.writer import write_dataset
from fabline.tasks.meta import manifest_meta
from fabline.tasks.throughput import ThroughputConfig, ThroughputTask
from fabline.worlds.factory.config import FactoryConfig, load_config
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.world import FactoryWorld


def cmd_smoke(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    ticks = min(args.ticks, config.ticks_per_episode)
    world = FactoryWorld(config)

    world.reset(args.seed)
    world.run_ticks(ticks)
    first_hash = world.state_hash()
    first_score = world.state.score
    first_entities = len(world.state.entities)

    world.reset(args.seed)
    world.run_ticks(ticks)
    second_hash = world.state_hash()

    summary = {
        "seed": args.seed,
        "ticks": ticks,
        "deterministic": first_hash == second_hash,
        "state_hash": first_hash,
        "score": first_score,
        "entities": first_entities,
        "delivered": {item.name: count for item, count in world.state.delivered.items()},
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if first_hash == second_hash else 1


def cmd_dataset(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    observation = build_observation(args.observation, config)
    task_config = ThroughputConfig(
        horizon=args.horizon,
        warmup_ticks=args.warmup,
        episode_ticks=args.ticks,
        sample_interval=args.interval,
    )
    task = ThroughputTask(config, task_config, observation)
    episodes = task.generate(args.episodes, args.seed_start)
    manifest = write_dataset(
        args.out,
        args.name,
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

    summary = {
        "dataset": str(Path(args.out)),
        "episodes": manifest["episodes"],
        "samples": manifest["stats"]["samples"],
        "splits": manifest["splits"],
        "labels": manifest["stats"]["labels"],
        "replays_validated": len(episodes),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.dataset)
    results = run_throughput_benchmark(dataset, args.out)
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


def cmd_suite(args: argparse.Namespace) -> int:
    suite = SuiteConfig(
        episodes=args.episodes,
        seed_start=args.seed_start,
        control_episodes=args.control_episodes,
        control_train_episodes=args.control_train_episodes,
    )
    results = run_suite(args.out, suite)
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


def cmd_shared_suite(args: argparse.Namespace) -> int:
    suite = SharedSuiteConfig(
        control_episodes=args.control_episodes,
        control_train_episodes=args.control_train_episodes,
        with_ci=not args.no_ci,
    )
    results = run_shared_suite(args.out, suite)
    summary = {
        "out": args.out,
        "dataset": results["dataset"]["stats"],
        "tasks": list(results["tasks"]),
        "duration_seconds": results["metadata"]["duration_seconds"],
        "replays_validated": results["metadata"]["replays_validated"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    try:
        from fabline.render.app import run_factory_viewer, run_replay_viewer
    except ImportError:
        print(
            "pygame is not installed; run "
            "`.venv/bin/pip install -e '.[render]'` or `make render-install`.",
            file=sys.stderr,
        )
        return 2

    config = load_config(args.config) if args.config else None
    faults = FaultConfig(enabled=True) if args.faults else FaultConfig()
    power = (
        PowerConfig(
            enabled=True,
            generator_count=1,
            generator_capacity=9,
            generator_radius=8,
        )
        if args.power
        else PowerConfig()
    )
    if args.screenshot:
        run_factory_viewer(
            config or FactoryConfig(),
            seed=args.seed,
            screenshot=args.screenshot,
            screenshot_ticks=args.ticks,
            faults=faults,
            power=power,
        )
    elif args.dataset and args.episode:
        run_replay_viewer(
            config,
            args.dataset,
            args.episode,
            ticks_per_second=args.tps,
        )
    else:
        run_factory_viewer(
            config or FactoryConfig(),
            seed=args.seed,
            ticks_per_second=args.tps,
            faults=faults,
            power=power,
        )
    return 0


def _control_setup(
    args: argparse.Namespace,
) -> tuple[FactoryConfig, ControlConfig]:
    config = (
        load_config(args.config)
        if args.config
        else FactoryConfig(
            width=16,
            height=8,
            ticks_per_episode=300,
            decision_interval=10,
            entity_budget=32,
            rock_density=0.0,
            starter_line=False,
        )
    )
    control = ControlConfig(episode_ticks=config.ticks_per_episode)
    return config, control


def cmd_play(args: argparse.Namespace) -> int:
    try:
        from fabline.render.app import run_control_play
    except ImportError:
        print(
            "pygame is not installed; run "
            "`.venv/bin/pip install -e '.[render]'` or `make render-install`.",
            file=sys.stderr,
        )
        return 2
    config, control = _control_setup(args)
    run_control_play(config, control, args.out, seed=args.seed)
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    config, control = _control_setup(args)
    demos = make_scripted_demos(
        config,
        control,
        episodes=args.episodes,
        seed=args.seed,
    )
    from fabline.record.human import write_human_demos

    manifest = write_human_demos(
        args.out,
        "scripted-control",
        demos,
        config,
        control,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def cmd_human_bc(args: argparse.Namespace) -> int:
    config, control = _control_setup(args)
    results = train_human_bc(
        args.dataset,
        config,
        control,
        episodes=args.episodes,
        seed=args.seed,
    )
    write_human_bc_report(args.out, results)
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


def cmd_fault_benchmark(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
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
        fault_threshold=args.threshold,
        repair_ticks=args.repair_ticks,
    )
    results = run_fault_benchmark(
        args.out,
        episodes=args.episodes,
        seed_start=args.seed_start,
        config=config,
        faults=faults,
    )
    summary = {
        "out": args.out,
        "views": {
            name: {
                "samples": payload["samples"],
                "positive_rate": payload["positive_rate"],
            }
            for name, payload in results["views"].items()
        },
        "report": str(Path(args.out) / "fault_report.md"),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def cmd_fault_power(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    interaction = FaultPowerConfig(
        episode_ticks=500,
        decision_interval=10,
        repair_cost=args.repair_cost,
        success_score=args.success_score,
        faults=FaultConfig(
            enabled=True,
            wear_per_craft=1,
            fault_threshold=args.threshold,
            repair_ticks=args.repair_ticks,
        ),
        power=PowerConfig(
            enabled=True,
            generator_count=1,
            generator_capacity=args.capacity,
            generator_radius=8,
        ),
    )
    results = run_fault_power(
        config,
        interaction,
        episodes=args.episodes,
        train_episodes=args.train_episodes,
    )
    report = write_fault_power_report(
        args.out,
        results,
        config={
            "generator_capacity": args.capacity,
            "fault_threshold": args.threshold,
            "repair_ticks": args.repair_ticks,
            "repair_cost": args.repair_cost,
            "success_score": args.success_score,
        },
    )
    print(json.dumps({"report": str(report), "results": results}, indent=2, sort_keys=True))
    return 0


def cmd_power_benchmark(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    power = PowerConfig(
        enabled=True,
        generator_count=args.generators,
        generator_capacity=args.capacity,
        generator_radius=args.radius,
        load_jitter=args.load_jitter,
        capacity_jitter=args.capacity_jitter,
        variation_period=args.variation_period,
    )
    results = run_power_benchmark(
        args.out,
        episodes=args.episodes,
        seed_start=args.seed_start,
        config=config,
        power=power,
    )
    summary = {
        "out": args.out,
        "views": {
            name: {
                "samples": payload["samples"],
                "positive_rate": payload["positive_rate"],
            }
            for name, payload in results["views"].items()
        },
        "report": str(Path(args.out) / "power_report.md"),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def cmd_fault_recovery(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
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
        fault_threshold=args.threshold,
        repair_ticks=args.repair_ticks,
    )
    recovery = FaultRecoveryConfig(
        episode_ticks=500,
        decision_interval=10,
        repair_cost=args.repair_cost,
        success_score=args.success_score,
    )
    results = run_fault_recovery(
        config,
        faults,
        recovery,
        episodes=args.episodes,
        train_episodes=args.train_episodes,
    )
    report = write_fault_recovery_report(
        args.out,
        results,
        config={
            "fault_threshold": args.threshold,
            "repair_ticks": args.repair_ticks,
            "repair_cost": args.repair_cost,
            "success_score": args.success_score,
        },
    )
    print(json.dumps({"report": str(report), "results": results}, indent=2, sort_keys=True))
    return 0


def cmd_power_allocation(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    allocation = PowerAllocationConfig(
        episode_ticks=500,
        decision_interval=10,
        success_score=args.success_score,
        power=PowerConfig(
            enabled=True,
            generator_count=1,
            generator_capacity=args.capacity,
            generator_radius=8,
            load_jitter=args.load_jitter,
            capacity_jitter=args.capacity_jitter,
            variation_period=args.variation_period,
        ),
    )
    results = run_power_allocation(
        config,
        allocation,
        episodes=args.episodes,
        train_episodes=args.train_episodes,
    )
    report = write_power_allocation_report(
        args.out,
        results,
        config={
            "generator_capacity": args.capacity,
            "success_score": args.success_score,
            "load_jitter": args.load_jitter,
            "capacity_jitter": args.capacity_jitter,
            "variation_period": args.variation_period,
        },
    )
    print(json.dumps({"report": str(report), "results": results}, indent=2, sort_keys=True))
    return 0


def cmd_wire_repair(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    repair = WireRepairConfig(
        episode_ticks=500,
        decision_interval=10,
        repair_budget=args.repair_budget,
        repair_ticks=args.repair_ticks,
        repair_cost=args.repair_cost,
        success_score=args.success_score,
        power=PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=args.capacity,
            generator_radius=8,
            wire_redundancy=2,
        ),
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_wire_repair(
        config,
        repair,
        episodes=args.episodes,
        train_episodes=args.train_episodes,
        seeds=seeds,
        train_seed_start=args.train_seed_start,
    )
    report = write_wire_repair_report(
        args.out,
        results,
        config={
            "repair_budget": args.repair_budget,
            "repair_ticks": args.repair_ticks,
            "repair_cost": args.repair_cost,
            "restoration_reward": repair.restoration_reward,
            "wasted_penalty": repair.wasted_penalty,
            "success_score": args.success_score,
            "generator_capacity": args.capacity,
            "fault_ticks": list(repair.fault_ticks),
            "seeds": list(seeds),
            "train_seed_start": args.train_seed_start,
            "train_episodes": args.train_episodes,
        },
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_multi_crew(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    multi = MultiCrewConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=args.loop_failure,
        small_failure_tick=args.small_failure,
        large_failure_tick=args.large_failure,
        success_score=args.success_score,
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_multi_crew(
        config,
        multi,
        episodes=args.episodes,
        train_episodes=args.train_episodes,
        seeds=seeds,
        train_seed_start=args.train_seed_start,
    )
    report = write_multi_crew_report(
        args.out,
        results,
        config={
            "warning_tick": multi.warning_tick,
            "loop_failure_tick": multi.loop_failure_tick,
            "small_failure_tick": multi.small_failure_tick,
            "large_failure_tick": multi.large_failure_tick,
            "success_score": multi.success_score,
            "seeds": list(seeds),
            "train_episodes": args.train_episodes,
            "train_seed_start": args.train_seed_start,
        },
    )
    print(json.dumps({"report": str(report), "results": results}, indent=2, sort_keys=True))
    return 0


def cmd_crew_layout_q(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=32,
        height=16,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    multi = MultiCrewConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=90,
        small_failure_tick=110,
        large_failure_tick=130,
        randomize_crew_b=True,
        crew_b_min_distance=8,
        scenario="random_gear",
        success_score=400,
        power=PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=24,
            generator_radius=8,
            wire_redundancy=2,
        ),
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    q_seeds = tuple(int(value) for value in args.q_seeds.split(","))
    results = run_crew_layout_q(
        config,
        multi,
        seeds=seeds,
        q_seeds=q_seeds,
        compact_episodes=args.compact_episodes,
        tabular_episodes=args.tabular_episodes,
        train_seed_start=args.train_seed_start,
    )
    report = write_crew_layout_q_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "scenario": multi.scenario,
            "seeds": list(seeds),
            "q_seeds": list(q_seeds),
            "compact_episodes": args.compact_episodes,
            "tabular_episodes": args.tabular_episodes,
            "train_seed_start": args.train_seed_start,
            "success_score": multi.success_score,
        },
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_crew_layouts(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=32,
        height=16,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    multi = MultiCrewConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=args.loop_failure,
        small_failure_tick=args.small_failure,
        large_failure_tick=args.large_failure,
        randomize_crew_b=True,
        crew_b_min_distance=8,
        scenario="random_gear",
        success_score=args.success_score,
        power=PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=24,
            generator_radius=8,
            wire_redundancy=2,
        ),
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_multi_crew(
        config,
        multi,
        episodes=1,
        train_episodes=args.train_episodes,
        seeds=seeds,
        train_seed_start=args.train_seed_start,
    )
    report = write_multi_crew_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "scenario": multi.scenario,
            "randomize_crew_b": multi.randomize_crew_b,
            "crew_b_min_distance": multi.crew_b_min_distance,
            "generator_capacity": 24,
            "warning_tick": multi.warning_tick,
            "loop_failure_tick": multi.loop_failure_tick,
            "small_failure_tick": multi.small_failure_tick,
            "large_failure_tick": multi.large_failure_tick,
            "success_score": multi.success_score,
            "seeds": list(seeds),
            "train_episodes": args.train_episodes,
            "train_seed_start": args.train_seed_start,
        },
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_crew_robustness(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    multi = MultiCrewConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=args.loop_failure,
        small_failure_tick=args.small_failure,
        large_failure_tick=args.large_failure,
        success_score=args.success_score,
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    q_seeds = tuple(int(value) for value in args.q_seeds.split(","))
    results = run_crew_robustness(
        config,
        multi,
        seeds=seeds,
        q_seeds=q_seeds,
        train_episodes=args.train_episodes,
        train_seed_start=args.train_seed_start,
    )
    report = write_crew_robustness_report(
        args.out,
        results,
        config={
            "warning_tick": multi.warning_tick,
            "loop_failure_tick": multi.loop_failure_tick,
            "small_failure_tick": multi.small_failure_tick,
            "large_failure_tick": multi.large_failure_tick,
            "success_score": multi.success_score,
            "seeds": list(seeds),
            "q_seeds": list(q_seeds),
            "train_episodes": args.train_episodes,
            "train_seed_start": args.train_seed_start,
        },
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_crew_replan_layouts(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=32,
        height=16,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
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
        success_score=400,
        randomize_crew_b=True,
        crew_b_min_distance=8,
        scenario="random_gear",
        power=PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=24,
            generator_radius=8,
            wire_redundancy=2,
        ),
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    q_seeds = tuple(int(value) for value in args.q_seeds.split(","))
    results = run_crew_replan(
        config,
        replan,
        train_episodes=args.train_episodes,
        seeds=seeds,
        q_seeds=q_seeds,
        train_seed_start=args.train_seed_start,
    )
    report = write_crew_replan_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "scenario": replan.scenario,
            "randomize_crew_b": replan.randomize_crew_b,
            "crew_b_min_distance": replan.crew_b_min_distance,
            "generator_capacity": 24,
            "warning_tick": replan.warning_tick,
            "loop_failure_tick": replan.loop_failure_tick,
            "small_failure_tick": replan.small_failure_tick,
            "large_failure_tick": replan.large_failure_tick,
            "recall_tick": replan.recall_tick,
            "success_score": replan.success_score,
            "seeds": list(seeds),
            "q_seeds": list(q_seeds),
            "train_episodes": args.train_episodes,
            "train_seed_start": args.train_seed_start,
        },
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_crew_replan(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    replan = CrewReplanConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=args.loop_failure,
        small_failure_tick=args.small_failure,
        large_failure_tick=args.large_failure,
        recall_tick=args.recall_tick,
        success_score=args.success_score,
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    q_seeds = tuple(int(value) for value in args.q_seeds.split(","))
    results = run_crew_replan(
        config,
        replan,
        train_episodes=args.train_episodes,
        seeds=seeds,
        q_seeds=q_seeds,
        train_seed_start=args.train_seed_start,
    )
    report = write_crew_replan_report(
        args.out,
        results,
        config={
            "warning_tick": replan.warning_tick,
            "loop_failure_tick": replan.loop_failure_tick,
            "small_failure_tick": replan.small_failure_tick,
            "large_failure_tick": replan.large_failure_tick,
            "recall_tick": replan.recall_tick,
            "success_score": replan.success_score,
            "seeds": list(seeds),
            "q_seeds": list(q_seeds),
            "train_episodes": args.train_episodes,
            "train_seed_start": args.train_seed_start,
        },
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_crew_schedule(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    crew = CrewScheduleConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=args.loop_failure,
        small_failure_tick=args.small_failure,
        large_failure_tick=args.large_failure,
        repair_budget=args.repair_budget,
        success_score=args.success_score,
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_crew_schedule(
        config,
        crew,
        episodes=args.episodes,
        train_episodes=args.train_episodes,
        seeds=seeds,
        train_seed_start=args.train_seed_start,
    )
    report = write_crew_report(
        args.out,
        results,
        config={
            "warning_tick": crew.warning_tick,
            "loop_failure_tick": crew.loop_failure_tick,
            "small_failure_tick": crew.small_failure_tick,
            "large_failure_tick": crew.large_failure_tick,
            "repair_budget": crew.repair_budget,
            "repair_ticks": crew.repair_ticks,
            "success_score": crew.success_score,
            "seeds": list(seeds),
            "train_episodes": args.train_episodes,
            "train_seed_start": args.train_seed_start,
        },
    )
    print(json.dumps({"report": str(report), "results": results}, indent=2, sort_keys=True))
    return 0


def cmd_preventive_threshold(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    threshold = ThresholdConfig(success_score=args.success_score)
    seeds = tuple(int(value) for value in args.seeds.split(","))
    payload = run_threshold_selection(
        config,
        threshold,
        episodes=args.train_episodes,
        seeds=seeds,
        train_seed_start=args.train_seed_start,
    )
    report = write_threshold_report(args.out, payload)
    print(json.dumps({"report": str(report), "results": payload}, indent=2, sort_keys=True))
    return 0


def cmd_preventive_fault(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
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
        fault_threshold=args.fault_threshold,
        repair_ticks=args.repair_ticks,
        maintenance_ticks=args.maintenance_ticks,
    )
    preventive = PreventiveFaultConfig(
        episode_ticks=500,
        decision_interval=10,
        success_score=args.success_score,
        faults=faults,
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_preventive_fault(
        config,
        preventive,
        episodes=args.episodes,
        train_episodes=args.train_episodes,
        seeds=seeds,
        train_seed_start=args.train_seed_start,
    )
    report = write_preventive_fault_report(
        args.out,
        results,
        config={
            "fault_threshold": args.fault_threshold,
            "repair_ticks": args.repair_ticks,
            "maintenance_ticks": args.maintenance_ticks,
            "success_score": args.success_score,
            "seeds": list(seeds),
            "train_episodes": args.train_episodes,
            "train_seed_start": args.train_seed_start,
        },
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_wire_maintenance(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    preventive = PreventiveWireConfig(
        episode_ticks=500,
        decision_interval=10,
        warning_tick=args.warning_tick,
        failure_tick=args.failure_tick,
        repair_ticks=args.repair_ticks,
        repair_budget=args.repair_budget,
        success_score=args.success_score,
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_preventive_wire(
        config,
        preventive,
        episodes=args.episodes,
        train_episodes=args.train_episodes,
        seeds=seeds,
        train_seed_start=args.train_seed_start,
    )
    report = write_preventive_wire_report(
        args.out,
        results,
        config={
            "warning_tick": args.warning_tick,
            "failure_tick": args.failure_tick,
            "repair_ticks": args.repair_ticks,
            "repair_budget": args.repair_budget,
            "success_score": args.success_score,
            "seeds": list(seeds),
            "train_episodes": args.train_episodes,
            "train_seed_start": args.train_seed_start,
        },
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    replay = json.loads(Path(args.replay).read_text(encoding="utf-8"))
    world = FactoryWorld(config)
    validate_replay(world, replay)
    print(json.dumps({"replay": args.replay, "valid": True}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fabline")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    smoke = subparsers.add_parser("smoke", help="run a short deterministic factory")
    smoke.add_argument("--config", type=str, default=None)
    smoke.add_argument("--seed", type=int, default=0)
    smoke.add_argument("--ticks", type=int, default=200)
    smoke.set_defaults(func=cmd_smoke)

    dataset = subparsers.add_parser("dataset", help="generate a debug dataset")
    dataset.add_argument("--config", type=str, default=None)
    dataset.add_argument("--episodes", type=int, default=100)
    dataset.add_argument("--seed-start", type=int, default=0)
    dataset.add_argument("--out", type=str, default="datasets/factory-debug-v0.1")
    dataset.add_argument("--name", type=str, default="factory-debug-v0.1")
    dataset.add_argument(
        "--observation",
        choices=["vector", "grid", "entities"],
        default="vector",
    )
    dataset.add_argument("--horizon", type=int, default=100)
    dataset.add_argument("--warmup", type=int, default=200)
    dataset.add_argument("--ticks", type=int, default=500)
    dataset.add_argument("--interval", type=int, default=10)
    dataset.set_defaults(func=cmd_dataset)

    benchmark = subparsers.add_parser("benchmark", help="run M1 baselines")
    benchmark.add_argument("--dataset", type=str, required=True)
    benchmark.add_argument("--out", type=str, default="results/m1-benchmark")
    benchmark.set_defaults(func=cmd_benchmark)

    suite = subparsers.add_parser("suite", help="run the M2 debug task suite")
    suite.add_argument("--out", type=str, default="results/m2-suite")
    suite.add_argument("--episodes", type=int, default=20)
    suite.add_argument("--seed-start", type=int, default=0)
    suite.add_argument("--control-episodes", type=int, default=5)
    suite.add_argument("--control-train-episodes", type=int, default=200)
    suite.set_defaults(func=cmd_suite)

    shared = subparsers.add_parser(
        "shared-suite",
        help="run the M3 shared-episode benchmark candidate",
    )
    shared.add_argument("--out", type=str, default="results/factory-v0.1")
    shared.add_argument("--control-episodes", type=int, default=5)
    shared.add_argument("--control-train-episodes", type=int, default=200)
    shared.add_argument("--no-ci", action="store_true")
    shared.set_defaults(func=cmd_shared_suite)

    render = subparsers.add_parser("render", help="watch a factory or replay")
    render.add_argument("--config", type=str, default=None)
    render.add_argument("--seed", type=int, default=0)
    render.add_argument("--dataset", type=str, default=None)
    render.add_argument("--episode", type=str, default=None)
    render.add_argument("--screenshot", type=str, default=None)
    render.add_argument("--ticks", type=int, default=200)
    render.add_argument("--tps", type=float, default=20.0)
    render.add_argument("--faults", action="store_true")
    render.add_argument("--power", action="store_true")
    render.set_defaults(func=cmd_render)

    play = subparsers.add_parser("play", help="play the control task and save demos")
    play.add_argument("--config", type=str, default=None)
    play.add_argument("--seed", type=int, default=0)
    play.add_argument("--out", type=str, default="datasets/human-control-v0.1")
    play.set_defaults(func=cmd_play)

    demo = subparsers.add_parser("demo", help="generate scripted control demos")
    demo.add_argument("--config", type=str, default=None)
    demo.add_argument("--seed", type=int, default=0)
    demo.add_argument("--episodes", type=int, default=10)
    demo.add_argument("--out", type=str, default="datasets/demo-control-v0.1")
    demo.set_defaults(func=cmd_demo)

    human_bc = subparsers.add_parser(
        "human-bc",
        help="train behavior cloning from a demo dataset",
    )
    human_bc.add_argument("--config", type=str, default=None)
    human_bc.add_argument("--dataset", type=str, required=True)
    human_bc.add_argument("--out", type=str, default="results/human-bc")
    human_bc.add_argument("--episodes", type=int, default=5)
    human_bc.add_argument("--seed", type=int, default=0)
    human_bc.set_defaults(func=cmd_human_bc)

    fault_benchmark = subparsers.add_parser(
        "fault-benchmark",
        help="run the opt-in fault-mechanic debug benchmark",
    )
    fault_benchmark.add_argument("--out", type=str, default="results/fault-benchmark")
    fault_benchmark.add_argument("--episodes", type=int, default=40)
    fault_benchmark.add_argument("--seed-start", type=int, default=0)
    fault_benchmark.add_argument("--threshold", type=int, default=20)
    fault_benchmark.add_argument("--repair-ticks", type=int, default=30)
    fault_benchmark.set_defaults(func=cmd_fault_benchmark)

    fault_power = subparsers.add_parser(
        "fault-power",
        help="run the fault + power interaction control benchmark",
    )
    fault_power.add_argument("--out", type=str, default="results/fault-power")
    fault_power.add_argument("--episodes", type=int, default=5)
    fault_power.add_argument("--train-episodes", type=int, default=100)
    fault_power.add_argument("--capacity", type=int, default=5)
    fault_power.add_argument("--threshold", type=int, default=5)
    fault_power.add_argument("--repair-ticks", type=int, default=10)
    fault_power.add_argument("--repair-cost", type=float, default=1.0)
    fault_power.add_argument("--success-score", type=int, default=100)
    fault_power.set_defaults(func=cmd_fault_power)

    power_benchmark = subparsers.add_parser(
        "power-benchmark",
        help="run the opt-in power-grid debug benchmark",
    )
    power_benchmark.add_argument("--out", type=str, default="results/power-benchmark")
    power_benchmark.add_argument("--episodes", type=int, default=40)
    power_benchmark.add_argument("--seed-start", type=int, default=0)
    power_benchmark.add_argument("--generators", type=int, default=1)
    power_benchmark.add_argument("--capacity", type=int, default=9)
    power_benchmark.add_argument("--radius", type=int, default=8)
    power_benchmark.add_argument("--load-jitter", type=int, default=0)
    power_benchmark.add_argument("--capacity-jitter", type=int, default=0)
    power_benchmark.add_argument("--variation-period", type=int, default=20)
    power_benchmark.set_defaults(func=cmd_power_benchmark)

    fault_recovery = subparsers.add_parser(
        "fault-recovery",
        help="run the noop-vs-repair fault recovery benchmark",
    )
    fault_recovery.add_argument("--out", type=str, default="results/fault-recovery")
    fault_recovery.add_argument("--episodes", type=int, default=5)
    fault_recovery.add_argument("--train-episodes", type=int, default=100)
    fault_recovery.add_argument("--threshold", type=int, default=20)
    fault_recovery.add_argument("--repair-ticks", type=int, default=30)
    fault_recovery.add_argument("--repair-cost", type=float, default=1.0)
    fault_recovery.add_argument("--success-score", type=int, default=250)
    fault_recovery.set_defaults(func=cmd_fault_recovery)

    power_allocation = subparsers.add_parser(
        "power-allocation",
        help="run the power-allocation control benchmark",
    )
    power_allocation.add_argument("--out", type=str, default="results/power-allocation")
    power_allocation.add_argument("--episodes", type=int, default=5)
    power_allocation.add_argument("--train-episodes", type=int, default=100)
    power_allocation.add_argument("--capacity", type=int, default=5)
    power_allocation.add_argument("--success-score", type=int, default=100)
    power_allocation.add_argument("--load-jitter", type=int, default=0)
    power_allocation.add_argument("--capacity-jitter", type=int, default=0)
    power_allocation.add_argument("--variation-period", type=int, default=20)
    power_allocation.set_defaults(func=cmd_power_allocation)

    wire_repair = subparsers.add_parser(
        "wire-repair",
        help="run the wired-power wire-repair control benchmark",
    )
    wire_repair.add_argument("--out", type=str, default="results/wire-repair")
    wire_repair.add_argument("--episodes", type=int, default=5)
    wire_repair.add_argument("--train-episodes", type=int, default=100)
    wire_repair.add_argument("--seeds", type=str, default="0,1,2")
    wire_repair.add_argument("--train-seed-start", type=int, default=1000)
    wire_repair.add_argument("--repair-budget", type=int, default=2)
    wire_repair.add_argument("--repair-ticks", type=int, default=60)
    wire_repair.add_argument("--repair-cost", type=float, default=1.0)
    wire_repair.add_argument("--success-score", type=int, default=150)
    wire_repair.add_argument("--capacity", type=int, default=12)
    wire_repair.set_defaults(func=cmd_wire_repair)

    multi_crew = subparsers.add_parser(
        "multi-crew",
        help="run the two-crew repair coordination benchmark",
    )
    multi_crew.add_argument("--out", type=str, default="results/multi-crew")
    multi_crew.add_argument("--episodes", type=int, default=5)
    multi_crew.add_argument("--train-episodes", type=int, default=500)
    multi_crew.add_argument(
        "--seeds", type=str, default="1000,1001,1002,1003,1004"
    )
    multi_crew.add_argument("--train-seed-start", type=int, default=30000)
    multi_crew.add_argument("--loop-failure", type=int, default=90)
    multi_crew.add_argument("--small-failure", type=int, default=110)
    multi_crew.add_argument("--large-failure", type=int, default=130)
    multi_crew.add_argument("--success-score", type=int, default=150)
    multi_crew.set_defaults(func=cmd_multi_crew)

    crew_layout_q = subparsers.add_parser(
        "crew-layout-q",
        help="compare compact and old tabular Q on twin-line layouts",
    )
    crew_layout_q.add_argument(
        "--out", type=str, default="results/crew-layout-q"
    )
    crew_layout_q.add_argument(
        "--seeds",
        type=str,
        default="8000,8001,8002,8003,8004,8005,8006,8007,8008,8009",
    )
    crew_layout_q.add_argument("--q-seeds", type=str, default="0,1,2")
    crew_layout_q.add_argument("--compact-episodes", type=int, default=2000)
    crew_layout_q.add_argument("--tabular-episodes", type=int, default=500)
    crew_layout_q.add_argument("--train-seed-start", type=int, default=80000)
    crew_layout_q.set_defaults(func=cmd_crew_layout_q)

    crew_layouts = subparsers.add_parser(
        "crew-layouts",
        help="run the two-crew task on twin-line randomized layouts",
    )
    crew_layouts.add_argument("--out", type=str, default="results/crew-layouts")
    crew_layouts.add_argument(
        "--seeds", type=str, default="6000,6001,6002,6003,6004,6005,6006,6007,6008,6009"
    )
    crew_layouts.add_argument("--train-episodes", type=int, default=500)
    crew_layouts.add_argument("--train-seed-start", type=int, default=55000)
    crew_layouts.add_argument("--loop-failure", type=int, default=90)
    crew_layouts.add_argument("--small-failure", type=int, default=110)
    crew_layouts.add_argument("--large-failure", type=int, default=130)
    crew_layouts.add_argument("--success-score", type=int, default=400)
    crew_layouts.set_defaults(func=cmd_crew_layouts)

    crew_robustness = subparsers.add_parser(
        "crew-robustness",
        help="run the two-crew task over a larger seed block",
    )
    crew_robustness.add_argument(
        "--out", type=str, default="results/crew-robustness"
    )
    crew_robustness.add_argument(
        "--seeds",
        type=str,
        default=",".join(str(seed) for seed in range(3000, 3040)),
    )
    crew_robustness.add_argument("--q-seeds", type=str, default="0,1,2,3,4")
    crew_robustness.add_argument("--train-episodes", type=int, default=500)
    crew_robustness.add_argument("--train-seed-start", type=int, default=40000)
    crew_robustness.add_argument("--loop-failure", type=int, default=90)
    crew_robustness.add_argument("--small-failure", type=int, default=110)
    crew_robustness.add_argument("--large-failure", type=int, default=130)
    crew_robustness.add_argument("--success-score", type=int, default=150)
    crew_robustness.set_defaults(func=cmd_crew_robustness)

    crew_replan_layouts = subparsers.add_parser(
        "crew-replan-layouts",
        help="run crew recall/replanning on twin-line layouts",
    )
    crew_replan_layouts.add_argument(
        "--out", type=str, default="results/crew-replan-layouts"
    )
    crew_replan_layouts.add_argument(
        "--seeds",
        type=str,
        default="7000,7001,7002,7003,7004,7005,7006,7007,7008,7009",
    )
    crew_replan_layouts.add_argument("--q-seeds", type=str, default="0,1,2")
    crew_replan_layouts.add_argument("--train-episodes", type=int, default=500)
    crew_replan_layouts.add_argument("--train-seed-start", type=int, default=65000)
    crew_replan_layouts.set_defaults(func=cmd_crew_replan_layouts)

    crew_replan = subparsers.add_parser(
        "crew-replan",
        help="run the crew recall and replanning benchmark",
    )
    crew_replan.add_argument("--out", type=str, default="results/crew-replan")
    crew_replan.add_argument(
        "--seeds", type=str, default="5000,5001,5002,5003,5004"
    )
    crew_replan.add_argument("--q-seeds", type=str, default="0,1,2,3,4")
    crew_replan.add_argument("--train-episodes", type=int, default=1000)
    crew_replan.add_argument("--train-seed-start", type=int, default=45000)
    crew_replan.add_argument("--loop-failure", type=int, default=90)
    crew_replan.add_argument("--small-failure", type=int, default=110)
    crew_replan.add_argument("--large-failure", type=int, default=130)
    crew_replan.add_argument("--recall-tick", type=int, default=100)
    crew_replan.add_argument("--success-score", type=int, default=150)
    crew_replan.set_defaults(func=cmd_crew_replan)

    crew_schedule = subparsers.add_parser(
        "crew-schedule",
        help="run the crew repair scheduling benchmark",
    )
    crew_schedule.add_argument("--out", type=str, default="results/crew-schedule")
    crew_schedule.add_argument("--episodes", type=int, default=5)
    crew_schedule.add_argument("--train-episodes", type=int, default=500)
    crew_schedule.add_argument("--seeds", type=str, default="800,801,802,803,804")
    crew_schedule.add_argument("--train-seed-start", type=int, default=12000)
    crew_schedule.add_argument("--loop-failure", type=int, default=90)
    crew_schedule.add_argument("--small-failure", type=int, default=120)
    crew_schedule.add_argument("--large-failure", type=int, default=150)
    crew_schedule.add_argument("--repair-budget", type=int, default=2)
    crew_schedule.add_argument("--success-score", type=int, default=150)
    crew_schedule.set_defaults(func=cmd_crew_schedule)

    preventive_threshold = subparsers.add_parser(
        "preventive-threshold",
        help="run the maintenance-threshold selection benchmark",
    )
    preventive_threshold.add_argument(
        "--out", type=str, default="results/preventive-threshold"
    )
    preventive_threshold.add_argument("--train-episodes", type=int, default=50)
    preventive_threshold.add_argument(
        "--seeds", type=str, default="700,701,702,703,704"
    )
    preventive_threshold.add_argument(
        "--train-seed-start", type=int, default=9000
    )
    preventive_threshold.add_argument("--success-score", type=int, default=240)
    preventive_threshold.set_defaults(func=cmd_preventive_threshold)

    preventive_fault = subparsers.add_parser(
        "preventive-fault",
        help="run the preventive machine-maintenance benchmark",
    )
    preventive_fault.add_argument(
        "--out", type=str, default="results/preventive-fault"
    )
    preventive_fault.add_argument("--episodes", type=int, default=5)
    preventive_fault.add_argument("--train-episodes", type=int, default=500)
    preventive_fault.add_argument("--seeds", type=str, default="0,1,2")
    preventive_fault.add_argument("--train-seed-start", type=int, default=7000)
    preventive_fault.add_argument("--fault-threshold", type=int, default=20)
    preventive_fault.add_argument("--repair-ticks", type=int, default=60)
    preventive_fault.add_argument("--maintenance-ticks", type=int, default=10)
    preventive_fault.add_argument("--success-score", type=int, default=240)
    preventive_fault.set_defaults(func=cmd_preventive_fault)

    wire_maintenance = subparsers.add_parser(
        "wire-maintenance",
        help="run the preventive wire-maintenance benchmark",
    )
    wire_maintenance.add_argument(
        "--out", type=str, default="results/wire-maintenance"
    )
    wire_maintenance.add_argument("--episodes", type=int, default=5)
    wire_maintenance.add_argument("--train-episodes", type=int, default=200)
    wire_maintenance.add_argument("--seeds", type=str, default="0,1,2")
    wire_maintenance.add_argument("--train-seed-start", type=int, default=6000)
    wire_maintenance.add_argument("--warning-tick", type=int, default=60)
    wire_maintenance.add_argument("--failure-tick", type=int, default=220)
    wire_maintenance.add_argument("--repair-ticks", type=int, default=140)
    wire_maintenance.add_argument("--repair-budget", type=int, default=1)
    wire_maintenance.add_argument("--success-score", type=int, default=150)
    wire_maintenance.set_defaults(func=cmd_wire_maintenance)

    replay = subparsers.add_parser("replay", help="validate a replay file")
    replay.add_argument("--replay", type=str, required=True)
    replay.add_argument("--config", type=str, default=None)
    replay.set_defaults(func=cmd_replay)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
