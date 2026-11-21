"""The ``fabline`` command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fabline import __version__
from fabline.env.control import ControlConfig
from fabline.env.fault_power import FaultPowerConfig
from fabline.env.fault_recovery import FaultRecoveryConfig
from fabline.env.power_allocation import PowerAllocationConfig
from fabline.env.wire_repair import WireRepairConfig
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
from fabline.harness.power import run_power_benchmark
from fabline.harness.power_allocation import (
    run_power_allocation,
    write_power_allocation_report,
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
    wire_repair.add_argument("--repair-cost", type=float, default=1.0)
    wire_repair.add_argument("--success-score", type=int, default=150)
    wire_repair.add_argument("--capacity", type=int, default=12)
    wire_repair.set_defaults(func=cmd_wire_repair)

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
