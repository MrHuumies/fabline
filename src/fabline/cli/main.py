"""The ``fabline`` command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fabline import __version__
from fabline.cli.browser import (
    find_replays,
    find_task_cards,
    format_replay_table,
    format_task_card_table,
    read_task_card,
    resolve_task_card,
    summarize_replay,
)
from fabline.cli.wizard import run_wizard
from fabline.env.contract_board import ContractBoardConfig, ContractBoardEnv
from fabline.env.control import ControlConfig
from fabline.env.crew_replan import CrewReplanConfig
from fabline.env.crew_schedule import CrewScheduleConfig
from fabline.env.fault_power import FaultPowerConfig
from fabline.env.fault_recovery import FaultRecoveryConfig
from fabline.env.multi_crew import MultiCrewConfig
from fabline.env.orders import OrderConfig, OrderControlConfig
from fabline.env.power_allocation import PowerAllocationConfig
from fabline.env.preventive_fault import PreventiveFaultConfig
from fabline.env.preventive_threshold import ThresholdConfig
from fabline.env.preventive_wire import PreventiveWireConfig
from fabline.env.production_mix import ProductionMixConfig
from fabline.env.recipe import RecipeEnvConfig
from fabline.env.three_crew_replan import ThreeCrewReplanConfig
from fabline.env.wire_repair import WireRepairConfig
from fabline.harness.causal_intervention import (
    CausalConfig,
    run_causal,
    write_causal_report,
)
from fabline.harness.contract_board import run_contract_board, write_board_report
from fabline.harness.crew_budget import (
    run_crew_budget,
    write_crew_budget_report,
)
from fabline.harness.crew_decentralized import (
    run_decentralized,
    run_decentralized_compact,
    run_decentralized_ctde,
    write_decentralized_compact_report,
    write_decentralized_ctde_report,
    write_decentralized_report,
)
from fabline.harness.crew_layout_ensemble import (
    run_crew_layout_ensemble,
    write_crew_layout_ensemble_report,
)
from fabline.harness.crew_layout_q import (
    run_crew_layout_q,
    write_crew_layout_q_report,
)
from fabline.harness.crew_multi_orphan import (
    run_crew_multi_orphan,
    write_crew_multi_orphan_report,
)
from fabline.harness.crew_private import (
    run_crew_private,
    write_crew_private_report,
)
from fabline.harness.crew_replacement import (
    run_crew_replacement,
    write_crew_replacement_report,
)
from fabline.harness.crew_replan import (
    run_crew_replan,
    write_crew_replan_report,
)
from fabline.harness.crew_schedule import (
    run_crew_schedule,
    write_crew_report,
)
from fabline.harness.crew_three import (
    run_three_crew,
    write_three_crew_report,
)
from fabline.harness.crew_three_replan import (
    run_three_crew_replan,
    write_three_crew_replan_report,
)
from fabline.harness.crew_visibility import (
    run_crew_visibility,
    write_crew_visibility_report,
)
from fabline.harness.data import load_dataset
from fabline.harness.efficiency import (
    EfficiencyConfig,
    run_efficiency,
    write_efficiency_report,
)
from fabline.harness.factory_v02 import (
    FactoryV02Config,
    build_expected_summary,
    compare_expected_summary,
    run_factory_v02,
    write_expected_summary,
    write_factory_v02_report,
)
from fabline.harness.factory_v03 import (
    FactoryV03Config,
    run_factory_v03,
    write_factory_v03_report,
)
from fabline.harness.factory_v03 import (
    build_expected_summary as build_v03_expected,
)
from fabline.harness.fault_calibration import (
    FaultCalibrationConfig,
    run_fault_calibration,
    write_fault_calibration_report,
)
from fabline.harness.fault_power import (
    run_fault_power,
    write_fault_power_report,
)
from fabline.harness.fault_recovery import (
    run_fault_recovery,
    write_fault_recovery_report,
)
from fabline.harness.faults import run_fault_benchmark
from fabline.harness.generative_audit import (
    GenerativeAuditConfig,
    run_generative_audit,
    write_generative_audit_report,
)
from fabline.harness.human_demos import (
    make_scripted_demos,
    train_human_bc,
    write_human_bc_report,
)
from fabline.harness.maintenance_calibration import (
    MaintenanceCalibrationConfig,
    run_maintenance_calibration,
    write_maintenance_calibration_report,
)
from fabline.harness.multi_crew import (
    run_crew_robustness,
    run_multi_crew,
    write_crew_robustness_report,
    write_multi_crew_report,
)
from fabline.harness.order_control import (
    run_order_control,
    write_order_control_report,
)
from fabline.harness.order_planning import (
    OrderPlanningConfig,
    run_order_planning,
    write_order_planning_report,
)
from fabline.harness.order_rl import (
    OrderRLConfig,
    run_order_rl,
    write_order_rl_report,
)
from fabline.harness.partial_throughput import (
    PartialThroughputConfig,
    run_partial_throughput,
    write_partial_throughput_report,
)
from fabline.harness.planning_transition import (
    TransitionEnsembleConfig,
    TransitionPlanningConfig,
    run_transition_ensemble,
    run_transition_planning,
    run_transition_two_step,
    write_transition_ensemble_report,
    write_transition_planning_report,
    write_transition_two_step_report,
)
from fabline.harness.planning_triage import (
    TriagePlanningConfig,
    run_triage_planning,
    write_triage_planning_report,
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
from fabline.harness.production_mix import (
    run_production_mix,
    write_production_mix_report,
)
from fabline.harness.recipe import run_recipe_choice, write_recipe_report
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
from fabline.worlds.factory.recipe import RecipeConfig
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


def cmd_efficiency(args: argparse.Namespace) -> int:
    report = run_efficiency(
        EfficiencyConfig(
            repeats=args.repeats,
            world_ticks=args.world_ticks,
        )
    )
    path = write_efficiency_report(args.out, report)
    print(
        json.dumps(
            {
                "report": str(path),
                "dataset": report["dataset"],
                "world_ticks_per_second": report["world"]["ticks_per_second"],
                "models": len(report["models"]),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_order_rl(args: argparse.Namespace) -> int:
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
    orders = OrderControlConfig(
        episode_ticks=300,
        decision_interval=10,
        success_value=args.success_value,
        orders=OrderConfig(enabled=True),
    )
    rl = OrderRLConfig(
        eval_seeds=tuple(int(value) for value in args.seeds.split(",")),
        ppo_seeds=tuple(
            int(value) for value in args.ppo_seeds.split(",")
        ),
        ppo_steps=args.ppo_steps,
        bc_episodes=args.bc_episodes,
    )
    report = run_order_rl(config, orders, rl)
    path = write_order_rl_report(args.out, report)
    print(json.dumps({"report": str(path), **report}, indent=2, sort_keys=True))
    return 0


def cmd_order_planning(args: argparse.Namespace) -> int:
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
    planning = OrderPlanningConfig(
        episode_ticks=300,
        decision_interval=10,
        success_value=args.success_value,
        blocks=args.blocks,
        population=args.population,
        elites=args.elites,
        iterations=args.iterations,
        random_samples=args.random_samples,
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    report = run_order_planning(config, planning, seeds=seeds)
    path = write_order_planning_report(args.out, report)
    print(json.dumps({"report": str(path), **report}, indent=2, sort_keys=True))
    return 0


def cmd_order_control(args: argparse.Namespace) -> int:
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
    orders = OrderControlConfig(
        episode_ticks=300,
        decision_interval=10,
        success_value=args.success_value,
        orders=OrderConfig(enabled=True),
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_order_control(
        config,
        orders,
        seeds=seeds,
        episodes=args.episodes,
        q_episodes=args.q_episodes,
    )
    report = write_order_control_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "seeds": list(seeds),
            "success_value": orders.success_value,
        },
    )
    print(json.dumps({"report": str(report), "results": results}, indent=2, sort_keys=True))
    return 0


def cmd_production_mix(args: argparse.Namespace) -> int:
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
    mix = ProductionMixConfig(
        episode_ticks=300,
        decision_interval=10,
        success_score=args.success_score,
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_production_mix(
        config,
        mix,
        seeds=seeds,
        episodes=args.episodes,
        q_episodes=args.q_episodes,
    )
    report = write_production_mix_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "seeds": list(seeds),
            "success_score": mix.success_score,
            "component_score": mix.production.component_score,
        },
    )
    print(json.dumps({"report": str(report), "results": results}, indent=2, sort_keys=True))
    return 0


def cmd_replay_browser(args: argparse.Namespace) -> int:
    if args.show:
        summary = summarize_replay(args.show)
        print(format_replay_table([summary]))
        return 0
    paths = find_replays(args.root)
    if not paths:
        print(f"no replay.json files under {args.root}")
        return 0
    summaries = [summarize_replay(path) for path in paths]
    print(format_replay_table(summaries, limit=args.limit))
    return 0


def cmd_task_cards(args: argparse.Namespace) -> int:
    cards = find_task_cards(args.root)
    if args.show:
        card = resolve_task_card(cards, args.show)
        if card is None:
            print(f"task card not found: {args.show}")
            return 1
        print(read_task_card(card))
        return 0
    if not cards:
        print(f"no task cards under {args.root}")
        return 0
    print(format_task_card_table(cards))
    return 0


def cmd_generative_audit(args: argparse.Namespace) -> int:
    report = run_generative_audit(
        GenerativeAuditConfig(
            seeds=args.seeds, seed_start=args.seed_start
        )
    )
    path = write_generative_audit_report(args.out, report)
    print(json.dumps({"report": str(path), **report}, indent=2, sort_keys=True))
    return 0


def cmd_benchmark_v03(args: argparse.Namespace) -> int:
    if args.expected and args.skip_v02_planning:
        print(
            "error: --expected requires the v0.2 planning block; remove "
            "--skip-v02-planning",
            file=sys.stderr,
        )
        return 2
    report = run_factory_v03(
        args.out,
        FactoryV03Config(),
        include_v02_planning=not args.skip_v02_planning,
        include_diagnostics=not args.skip_diagnostics,
        include_production_diagnostic=not args.skip_production,
    )
    path = write_factory_v03_report(args.out, report)
    payload: dict[str, object] = {
        "report": str(path),
        "core_episodes": report["blocks"]["core"]["episodes"],
        "core_hash": report["blocks"]["core"]["config_hash"],
        "order_control": report["blocks"]["order_control"]["value"]["mean_value"],
        "order_planning": report["blocks"]["order_planning"]["results"]["cem"]["mean_value"],
    }
    if args.expected:
        summary = build_v03_expected(report)
        expected_path = write_expected_summary(args.expected, summary)
        payload["expected"] = str(expected_path)
    if args.check_expected:
        try:
            expected = json.loads(
                Path(args.check_expected).read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"error: could not read expected summary "
                f"{args.check_expected}: {exc}",
                file=sys.stderr,
            )
            return 2
        actual = build_v03_expected(report)
        sections = None
        if args.skip_v02_planning:
            sections = tuple(key for key in actual if key != "planning")
        mismatches = compare_expected_summary(
            expected, actual, sections=sections
        )
        payload["check"] = {
            "ok": not mismatches,
            "mismatches": mismatches[:50],
            "mismatch_count": len(mismatches),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if not mismatches else 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_fault_calibration(args: argparse.Namespace) -> int:
    config = FaultCalibrationConfig(
        episodes=args.episodes,
        seed_start=args.seed_start,
        horizon=args.horizon,
        sample_interval=args.sample_interval,
        noise=args.noise,
    )
    results = run_fault_calibration(config)
    report = write_fault_calibration_report(args.out, results)
    print(json.dumps({"report": str(report), "results": results}, indent=2, sort_keys=True))
    return 0


def cmd_maintenance_calibration(args: argparse.Namespace) -> int:
    config = MaintenanceCalibrationConfig(
        episodes=args.episodes,
        seed_start=args.seed_start,
        horizon=args.horizon,
        maintenance_probability=args.maintenance_probability,
    )
    results = run_maintenance_calibration(config)
    report = write_maintenance_calibration_report(args.out, results)
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
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
        horizon=args.horizon,
        sample_interval=args.sample_interval,
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


def cmd_partial_throughput(args: argparse.Namespace) -> int:
    config = PartialThroughputConfig(
        episodes=args.episodes,
        warmup_ticks=args.warmup_ticks,
        episode_ticks=args.episode_ticks,
        sample_interval=args.sample_interval,
        horizon=args.horizon,
        dropout=args.dropout,
        window=args.window,
        sequence_epochs=args.sequence_epochs,
        sequence_hidden=args.sequence_hidden,
        sequence_layers=args.sequence_layers,
    )
    report = run_partial_throughput(
        config, include_sequence=not args.skip_sequence
    )
    path = write_partial_throughput_report(args.out, report)
    print(json.dumps({"report": str(path), "dataset": report["dataset"]}, indent=2, sort_keys=True))
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


def cmd_causal_remove(args: argparse.Namespace) -> int:
    config = CausalConfig(
        episodes=args.episodes,
        seed_start=args.seed_start,
    )
    report = run_causal(config)
    out = Path(args.out)
    write_causal_report(out, report)
    print(
        json.dumps(
            {"out": str(out), "rows": report["rows"], "views": report["views"]},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_benchmark_v02(args: argparse.Namespace) -> int:
    if args.expected and args.skip_planning:
        print(
            "error: --expected requires the planning block; remove "
            "--skip-planning",
            file=sys.stderr,
        )
        return 2
    config = FactoryV02Config()
    report = run_factory_v02(
        args.out,
        config,
        include_planning=not args.skip_planning,
        include_diagnostics=not args.skip_diagnostics,
    )
    path = write_factory_v02_report(args.out, report)
    payload: dict[str, object] = {
        "report": str(path),
        "core_episodes": report["blocks"]["core"]["episodes"],
        "core_hash": report["blocks"]["core"]["config_hash"],
    }
    if args.expected:
        summary = build_expected_summary(report)
        expected_path = write_expected_summary(args.expected, summary)
        payload["expected"] = str(expected_path)
    if args.check_expected:
        try:
            expected = json.loads(
                Path(args.check_expected).read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"error: could not read expected summary "
                f"{args.check_expected}: {exc}",
                file=sys.stderr,
            )
            return 2
        actual = build_expected_summary(report)
        sections = None
        if args.skip_planning:
            sections = tuple(key for key in actual if key != "planning")
        mismatches = compare_expected_summary(
            expected,
            actual,
            sections=sections,
        )
        payload["check"] = {
            "ok": not mismatches,
            "mismatches": mismatches[:50],
            "mismatch_count": len(mismatches),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if not mismatches else 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_wizard(args: argparse.Namespace) -> int:
    return run_wizard(dry_run=args.dry_run)


def cmd_crew_decentralized_ctde(args: argparse.Namespace) -> int:
    config, replan = _decentralized_task()
    seeds = tuple(int(value) for value in args.seeds.split(","))
    q_seeds = tuple(int(value) for value in args.q_seeds.split(","))
    results = run_decentralized_ctde(
        config,
        replan,
        seeds=seeds,
        q_seeds=q_seeds,
        train_episodes=args.train_episodes,
        train_seed_start=args.train_seed_start,
        warmup_episodes=args.warmup_episodes,
    )
    report = write_decentralized_ctde_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "radius": 16,
            "seeds": list(seeds),
            "q_seeds": list(q_seeds),
            "train_episodes": args.train_episodes,
            "train_seed_start": args.train_seed_start,
            "warmup_episodes": args.warmup_episodes,
            "success_score": replan.success_score,
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


def cmd_planning_triage(args: argparse.Namespace) -> int:
    config = TriagePlanningConfig(
        population=args.population,
        elites=args.elites,
        iterations=args.iterations,
        random_samples=args.random_samples,
        model_sequences=args.model_sequences,
        model_seeds=args.model_seeds,
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    report = run_triage_planning(
        config,
        seeds=seeds,
        model_seed_start=args.model_seed_start,
    )
    out = Path(args.out)
    write_triage_planning_report(report, out)
    print(
        json.dumps(
            {
                "task": report["task"],
                "out": str(out),
                "model_mse": report["model_mse"],
                "results": {
                    name: {
                        "mean_score": row["mean_score"],
                        "success_rate": row["success_rate"],
                        "mean_seconds": row["mean_seconds"],
                    }
                    for name, row in report["results"].items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_planning_transition(args: argparse.Namespace) -> int:
    config = TransitionPlanningConfig(
        population=args.population,
        elites=args.elites,
        iterations=args.iterations,
        random_samples=args.random_samples,
        train_seeds=args.train_seeds,
        eval_seeds=args.eval_seeds,
        ridge=args.ridge,
        max_sequences=args.max_sequences,
        train_seed_start=args.train_seed_start,
        eval_seed_start=args.eval_seed_start,
        planning_seeds=tuple(
            int(value) for value in args.seeds.split(",")
        ),
    )
    report = run_transition_planning(config)
    out = Path(args.out)
    write_transition_planning_report(out, report)
    print(
        json.dumps(
            {
                "task": report["task"],
                "out": str(out),
                "model": report["model"],
                "results": {
                    name: {
                        "mean_score": row["mean_score"],
                        "success_rate": row["success_rate"],
                        "mean_seconds": row["mean_seconds"],
                    }
                    for name, row in report["results"].items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_planning_transition_ensemble(args: argparse.Namespace) -> int:
    config = TransitionEnsembleConfig(
        population=args.population,
        elites=args.elites,
        iterations=args.iterations,
        random_samples=args.random_samples,
        train_seeds=args.train_seeds,
        eval_seeds=args.eval_seeds,
        ridge=args.ridge,
        max_sequences=args.max_sequences,
        train_seed_start=args.train_seed_start,
        eval_seed_start=args.eval_seed_start,
        planning_seeds=tuple(
            int(value) for value in args.seeds.split(",")
        ),
        members=args.members,
        beta=args.beta,
        ensemble_seed=args.ensemble_seed,
    )
    report = run_transition_ensemble(config)
    out = Path(args.out)
    write_transition_ensemble_report(out, report)
    print(
        json.dumps(
            {
                "task": report["task"],
                "out": str(out),
                "model": report["model"],
                "results": {
                    name: {
                        "mean_score": row["mean_score"],
                        "success_rate": row["success_rate"],
                        "mean_seconds": row["mean_seconds"],
                    }
                    for name, row in report["results"].items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_planning_transition_two_step(args: argparse.Namespace) -> int:
    config = TransitionPlanningConfig(
        population=args.population,
        elites=args.elites,
        iterations=args.iterations,
        random_samples=args.random_samples,
        train_seeds=args.train_seeds,
        eval_seeds=args.eval_seeds,
        ridge=args.ridge,
        max_sequences=args.max_sequences,
        train_seed_start=args.train_seed_start,
        eval_seed_start=args.eval_seed_start,
        planning_seeds=tuple(
            int(value) for value in args.seeds.split(",")
        ),
    )
    report = run_transition_two_step(config)
    out = Path(args.out)
    write_transition_two_step_report(out, report)
    print(
        json.dumps(
            {
                "task": report["task"],
                "out": str(out),
                "model": report["model"],
                "results": {
                    name: {
                        "mean_score": row["mean_score"],
                        "success_rate": row["success_rate"],
                        "mean_seconds": row["mean_seconds"],
                    }
                    for name, row in report["results"].items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_contract_board(args: argparse.Namespace) -> int:
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
    board = ContractBoardConfig(recipe=RecipeConfig(enabled=True))
    env = ContractBoardEnv(config, board)
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_contract_board(env, seeds=seeds)
    report = write_board_report(
        args.out,
        results,
        config={
            "boards": [
                [list(contract) for contract in variant]
                for variant in board.boards
            ],
            "seeds": list(seeds),
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


def cmd_recipe_choice(args: argparse.Namespace) -> int:
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
    recipe = RecipeConfig(
        enabled=True,
        fast_ticks=args.fast_ticks,
        fast_cost=args.fast_cost,
        slow_ticks=args.slow_ticks,
        slow_cost=args.slow_cost,
        byproduct_enabled=args.byproduct,
        byproduct_capacity=args.byproduct_capacity,
    )
    power = (
        PowerConfig(
            enabled=True,
            generator_count=1,
            generator_capacity=args.power_capacity,
            generator_radius=args.power_radius,
        )
        if args.power_capacity > 0
        else PowerConfig()
    )
    recipe_env = RecipeEnvConfig(
        episode_ticks=500,
        decision_interval=10,
        scenario="gear",
        success_score=args.success_score,
        recipe=recipe,
        power=power,
    )
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_recipe_choice(config, recipe_env, seeds=seeds)
    report = write_recipe_report(
        args.out,
        results,
        config={
            "fast_ticks": recipe.fast_ticks,
            "fast_cost": recipe.fast_cost,
            "slow_ticks": recipe.slow_ticks,
            "slow_cost": recipe.slow_cost,
            "byproduct_enabled": recipe.byproduct_enabled,
            "byproduct_capacity": recipe.byproduct_capacity,
            "success_score": recipe_env.success_score,
            "power_capacity": args.power_capacity,
            "power_radius": args.power_radius,
            "seeds": list(seeds),
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


def cmd_crew_triage(args: argparse.Namespace) -> int:
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
        job_failure_tick=100,
        replan_jobs=2,
        role_mode="three_positive",
        replan_mode="all_positive",
        success_score=300,
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
    results = run_crew_multi_orphan(config, replan, seeds=seeds)
    report = write_crew_multi_orphan_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "failure_tick": replan.job_failure_tick,
            "recall_tick": replan.recall_tick,
            "replan_jobs": replan.replan_jobs,
            "role_mode": replan.role_mode,
            "replan_mode": replan.replan_mode,
            "success_score": replan.success_score,
            "seeds": list(seeds),
        },
        title="Three-bridge survivor triage",
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_crew_costs(args: argparse.Namespace) -> int:
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
        job_failure_tick=100,
        replan_jobs=2,
        role_mode="three_positive",
        replan_mode="all_positive",
        success_score=300,
        randomize_crew_b=True,
        crew_b_min_distance=8,
        role_repair_ticks=(20, 40, 100),
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
    results = run_crew_multi_orphan(config, replan, seeds=seeds)
    report = write_crew_multi_orphan_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "failure_tick": replan.job_failure_tick,
            "recall_tick": replan.recall_tick,
            "replan_jobs": replan.replan_jobs,
            "role_mode": replan.role_mode,
            "replan_mode": replan.replan_mode,
            "role_repair_ticks": list(replan.role_repair_ticks or ()),
            "success_score": replan.success_score,
            "seeds": list(seeds),
        },
        title="Asymmetric repair-cost triage",
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_crew_topology(args: argparse.Namespace) -> int:
    config = FactoryConfig(
        width=48,
        height=24,
        ticks_per_episode=500,
        decision_interval=10,
        entity_budget=64,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    scenario = (
        "random_topology" if args.layout == "random" else "spread_gear"
    )
    replan = CrewReplanConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=90,
        small_failure_tick=110,
        large_failure_tick=130,
        recall_tick=100,
        job_failure_tick=100,
        replan_jobs=2,
        role_mode="three_positive",
        replan_mode="all_positive",
        success_score=300,
        randomize_crew_b=True,
        crew_b_min_distance=8,
        scenario=scenario,
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
    results = run_crew_multi_orphan(config, replan, seeds=seeds)
    report = write_crew_multi_orphan_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "scenario": scenario,
            "failure_tick": replan.job_failure_tick,
            "recall_tick": replan.recall_tick,
            "replan_jobs": replan.replan_jobs,
            "role_mode": replan.role_mode,
            "replan_mode": replan.replan_mode,
            "success_score": replan.success_score,
            "seeds": list(seeds),
        },
        title=(
            "Random-topology triage"
            if args.layout == "random"
            else "Spread-topology triage"
        ),
    )
    print(
        json.dumps(
            {"report": str(report), "results": results},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def cmd_crew_multi_orphan(args: argparse.Namespace) -> int:
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
        recall_tick=80,
        job_failure_tick=80,
        replan_jobs=2,
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
    results = run_crew_multi_orphan(config, replan, seeds=seeds)
    report = write_crew_multi_orphan_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "failure_tick": replan.job_failure_tick,
            "recall_tick": replan.recall_tick,
            "replan_jobs": replan.replan_jobs,
            "success_score": replan.success_score,
            "seeds": list(seeds),
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


def cmd_crew_three_replan(args: argparse.Namespace) -> int:
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
    replan = ThreeCrewReplanConfig(
        episode_ticks=500,
        decision_interval=10,
        loop_failure_tick=100,
        small_failure_tick=130,
        large_failure_tick=160,
        recall_tick=100,
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
    results = run_three_crew_replan(config, replan, seeds=seeds)
    report = write_three_crew_replan_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "scenario": replan.scenario,
            "recall_tick": replan.recall_tick,
            "success_score": replan.success_score,
            "seeds": list(seeds),
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


def cmd_crew_three(args: argparse.Namespace) -> int:
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
        loop_failure_tick=100,
        small_failure_tick=130,
        large_failure_tick=160,
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
    results = run_three_crew(config, multi, seeds=seeds)
    report = write_three_crew_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "scenario": multi.scenario,
            "success_score": multi.success_score,
            "seeds": list(seeds),
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


def cmd_crew_replacement(args: argparse.Namespace) -> int:
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
        job_failure_tick=100,
        replan_jobs=1,
        role_mode="three_positive",
        replan_mode="all_positive",
        replacement=True,
        success_score=300,
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
    results = run_crew_replacement(config, replan, seeds=seeds)
    report = write_crew_replacement_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "failure_tick": replan.job_failure_tick,
            "recall_tick": replan.recall_tick,
            "success_score": replan.success_score,
            "seeds": list(seeds),
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


def cmd_crew_budget(args: argparse.Namespace) -> int:
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
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_crew_budget(
        config,
        replan,
        seeds=seeds,
        radius=args.radius,
    )
    report = write_crew_budget_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "scenario": replan.scenario,
            "radius": args.radius,
            "seeds": list(seeds),
            "success_score": replan.success_score,
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


def cmd_crew_private(args: argparse.Namespace) -> int:
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
    seeds = tuple(int(value) for value in args.seeds.split(","))
    results = run_crew_private(
        config,
        replan,
        seeds=seeds,
        radius=args.radius,
        report_age=args.report_age,
    )
    report = write_crew_private_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "scenario": replan.scenario,
            "radius": args.radius,
            "report_age": args.report_age,
            "seeds": list(seeds),
            "success_score": replan.success_score,
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


def _decentralized_task() -> tuple[FactoryConfig, CrewReplanConfig]:
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
    return config, replan


def cmd_crew_decentralized(args: argparse.Namespace) -> int:
    config, replan = _decentralized_task()
    seeds = tuple(int(value) for value in args.seeds.split(","))
    q_seeds = tuple(int(value) for value in args.q_seeds.split(","))
    results = run_decentralized(
        config,
        replan,
        seeds=seeds,
        q_seeds=q_seeds,
        train_episodes=args.train_episodes,
    )
    report = write_decentralized_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "radius": 16,
            "seeds": list(seeds),
            "success_score": replan.success_score,
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


def cmd_crew_decentralized_compact(args: argparse.Namespace) -> int:
    config, replan = _decentralized_task()
    seeds = tuple(int(value) for value in args.seeds.split(","))
    q_seeds = tuple(int(value) for value in args.q_seeds.split(","))
    results = run_decentralized_compact(
        config,
        replan,
        seeds=seeds,
        q_seeds=q_seeds,
        train_episodes=args.train_episodes,
        train_seed_start=args.train_seed_start,
    )
    report = write_decentralized_compact_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "radius": 16,
            "seeds": list(seeds),
            "q_seeds": list(q_seeds),
            "train_episodes": args.train_episodes,
            "train_seed_start": args.train_seed_start,
            "success_score": replan.success_score,
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


def cmd_crew_visibility(args: argparse.Namespace) -> int:
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
    seeds = tuple(int(value) for value in args.seeds.split(","))
    ages = tuple(int(value) for value in args.ages.split(","))
    results = run_crew_visibility(
        config,
        replan,
        seeds=seeds,
        radius=args.radius,
        ages=ages,
    )
    report = write_crew_visibility_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "scenario": replan.scenario,
            "radius": args.radius,
            "ages": list(ages),
            "seeds": list(seeds),
            "success_score": replan.success_score,
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


def cmd_crew_layout_ensemble(args: argparse.Namespace) -> int:
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
    results = run_crew_layout_ensemble(
        config,
        multi,
        seeds=seeds,
        q_seeds=q_seeds,
        episodes=args.episodes,
        train_seed_start=args.train_seed_start,
    )
    report = write_crew_layout_ensemble_report(
        args.out,
        results,
        config={
            "width": config.width,
            "height": config.height,
            "scenario": multi.scenario,
            "seeds": list(seeds),
            "q_seeds": list(q_seeds),
            "episodes": args.episodes,
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

    order_planning = subparsers.add_parser(
        "order-planning",
        help="run order planning over recipe blocks",
    )
    order_planning.add_argument(
        "--out", type=str, default="results/order-planning"
    )
    order_planning.add_argument(
        "--seeds", type=str, default="73000,73001,73002,73003,73004"
    )
    order_planning.add_argument("--blocks", type=int, default=5)
    order_planning.add_argument("--population", type=int, default=16)
    order_planning.add_argument("--elites", type=int, default=4)
    order_planning.add_argument("--iterations", type=int, default=4)
    order_planning.add_argument("--random-samples", type=int, default=32)
    order_planning.add_argument("--success-value", type=int, default=160)
    order_planning.set_defaults(func=cmd_order_planning)

    order_rl = subparsers.add_parser(
        "order-rl",
        help="run BC/PPO baselines on order control",
    )
    order_rl.add_argument(
        "--out", type=str, default="results/order-rl"
    )
    order_rl.add_argument(
        "--seeds", type=str, default="76000,76001,76002,76003,76004"
    )
    order_rl.add_argument("--ppo-seeds", type=str, default="0,1,2")
    order_rl.add_argument("--ppo-steps", type=int, default=10000)
    order_rl.add_argument("--bc-episodes", type=int, default=100)
    order_rl.add_argument("--success-value", type=int, default=160)
    order_rl.set_defaults(func=cmd_order_rl)

    order_control = subparsers.add_parser(
        "order-control",
        help="run the seeded order-control pilot",
    )
    order_control.add_argument(
        "--out", type=str, default="results/order-control"
    )
    order_control.add_argument(
        "--seeds", type=str, default="71000,71001,71002,71003,71004"
    )
    order_control.add_argument("--episodes", type=int, default=5)
    order_control.add_argument("--q-episodes", type=int, default=100)
    order_control.add_argument("--success-value", type=int, default=160)
    order_control.set_defaults(func=cmd_order_control)

    production_mix = subparsers.add_parser(
        "production-mix",
        help="run the opt-in gear/component production-mix pilot",
    )
    production_mix.add_argument(
        "--out", type=str, default="results/production-mix"
    )
    production_mix.add_argument(
        "--seeds", type=str, default="70000,70001,70002,70003,70004"
    )
    production_mix.add_argument("--episodes", type=int, default=5)
    production_mix.add_argument("--q-episodes", type=int, default=50)
    production_mix.add_argument("--success-score", type=int, default=200)
    production_mix.set_defaults(func=cmd_production_mix)

    replay_browser = subparsers.add_parser(
        "replay-browser",
        help="list or summarize replay.json files",
    )
    replay_browser.add_argument("--root", type=str, default="datasets")
    replay_browser.add_argument("--show", type=str, default=None)
    replay_browser.add_argument("--limit", type=int, default=50)
    replay_browser.set_defaults(func=cmd_replay_browser)

    task_cards = subparsers.add_parser(
        "task-cards",
        help="list or print task cards",
    )
    task_cards.add_argument("--root", type=str, default="docs/tasks")
    task_cards.add_argument("--show", type=str, default=None)
    task_cards.set_defaults(func=cmd_task_cards)

    efficiency = subparsers.add_parser(
        "efficiency",
        help="build the cross-task efficiency table",
    )
    efficiency.add_argument(
        "--out", type=str, default="results/efficiency"
    )
    efficiency.add_argument("--repeats", type=int, default=3)
    efficiency.add_argument("--world-ticks", type=int, default=1000)
    efficiency.set_defaults(func=cmd_efficiency)

    generative_audit = subparsers.add_parser(
        "generative-audit",
        help="audit structural diversity for a generative pilot",
    )
    generative_audit.add_argument(
        "--out", type=str, default="results/generative-audit"
    )
    generative_audit.add_argument("--seeds", type=int, default=100)
    generative_audit.add_argument("--seed-start", type=int, default=0)
    generative_audit.set_defaults(func=cmd_generative_audit)

    benchmark_v03 = subparsers.add_parser(
        "benchmark-v03",
        help="run the factory-v0.3 benchmark candidate",
    )
    benchmark_v03.add_argument(
        "--out", type=str, default="results/factory-v0.3"
    )
    benchmark_v03.add_argument("--expected", type=str, default=None)
    benchmark_v03.add_argument("--check-expected", type=str, default=None)
    benchmark_v03.add_argument(
        "--skip-v02-planning",
        action="store_true",
        help="skip the expensive v0.2 planning block",
    )
    benchmark_v03.add_argument(
        "--skip-diagnostics",
        action="store_true",
        help="skip fault/power diagnostics",
    )
    benchmark_v03.add_argument(
        "--skip-production",
        action="store_true",
        help="skip the production-mix diagnostic",
    )
    benchmark_v03.set_defaults(func=cmd_benchmark_v03)

    fault_calibration = subparsers.add_parser(
        "fault-calibration",
        help="run fault calibration on hard onset views",
    )
    fault_calibration.add_argument(
        "--out", type=str, default="results/fault-calibration"
    )
    fault_calibration.add_argument("--episodes", type=int, default=40)
    fault_calibration.add_argument("--seed-start", type=int, default=55000)
    fault_calibration.add_argument("--horizon", type=int, default=10)
    fault_calibration.add_argument("--sample-interval", type=int, default=5)
    fault_calibration.add_argument("--noise", type=float, default=0.30)
    fault_calibration.set_defaults(func=cmd_fault_calibration)

    maintenance_calibration = subparsers.add_parser(
        "maintenance-calibration",
        help="run preventive-maintenance risk calibration",
    )
    maintenance_calibration.add_argument(
        "--out", type=str, default="results/maintenance-calibration"
    )
    maintenance_calibration.add_argument("--episodes", type=int, default=60)
    maintenance_calibration.add_argument(
        "--seed-start", type=int, default=61000
    )
    maintenance_calibration.add_argument("--horizon", type=int, default=10)
    maintenance_calibration.add_argument(
        "--maintenance-probability", type=float, default=0.05
    )
    maintenance_calibration.set_defaults(func=cmd_maintenance_calibration)

    fault_benchmark = subparsers.add_parser(
        "fault-benchmark",
        help="run the opt-in fault-mechanic debug benchmark",
    )
    fault_benchmark.add_argument("--out", type=str, default="results/fault-benchmark")
    fault_benchmark.add_argument("--episodes", type=int, default=40)
    fault_benchmark.add_argument("--seed-start", type=int, default=0)
    fault_benchmark.add_argument("--threshold", type=int, default=20)
    fault_benchmark.add_argument("--repair-ticks", type=int, default=30)
    fault_benchmark.add_argument("--horizon", type=int, default=50)
    fault_benchmark.add_argument("--sample-interval", type=int, default=10)
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

    partial_throughput = subparsers.add_parser(
        "partial-throughput",
        help="run the masked-window throughput benchmark",
    )
    partial_throughput.add_argument("--out", type=str, default="results/partial-throughput")
    partial_throughput.add_argument("--episodes", type=int, default=100)
    partial_throughput.add_argument("--warmup-ticks", type=int, default=150)
    partial_throughput.add_argument("--episode-ticks", type=int, default=300)
    partial_throughput.add_argument("--sample-interval", type=int, default=10)
    partial_throughput.add_argument("--horizon", type=int, default=50)
    partial_throughput.add_argument("--dropout", type=float, default=0.6)
    partial_throughput.add_argument("--window", type=int, default=4)
    partial_throughput.add_argument("--sequence-epochs", type=int, default=30)
    partial_throughput.add_argument("--sequence-hidden", type=int, default=16)
    partial_throughput.add_argument("--sequence-layers", type=int, default=1)
    partial_throughput.add_argument("--skip-sequence", action="store_true")
    partial_throughput.set_defaults(func=cmd_partial_throughput)

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

    causal_remove = subparsers.add_parser(
        "causal-remove",
        help="run counterfactual entity-removal prediction",
    )
    causal_remove.add_argument(
        "--out", type=str, default="results/causal-remove"
    )
    causal_remove.add_argument("--episodes", type=int, default=40)
    causal_remove.add_argument("--seed-start", type=int, default=57000)
    causal_remove.set_defaults(func=cmd_causal_remove)

    benchmark_v02 = subparsers.add_parser(
        "benchmark-v02",
        help="run the frozen factory-v0.2 benchmark",
    )
    benchmark_v02.add_argument(
        "--out", type=str, default="results/factory-v0.2"
    )
    benchmark_v02.add_argument(
        "--expected",
        type=str,
        default=None,
        help="write the compact frozen expected summary to this path",
    )
    benchmark_v02.add_argument(
        "--check-expected",
        type=str,
        default=None,
        help="compare the run against a frozen expected summary",
    )
    benchmark_v02.add_argument(
        "--skip-planning",
        action="store_true",
        help="skip the expensive planning block (cheap regression check)",
    )
    benchmark_v02.add_argument(
        "--skip-diagnostics",
        action="store_true",
        help="skip the fault/power diagnostic blocks",
    )
    benchmark_v02.set_defaults(func=cmd_benchmark_v02)

    wizard = subparsers.add_parser(
        "wizard",
        help="interactive wizard for common commands",
    )
    wizard.add_argument(
        "--dry-run",
        action="store_true",
        help="print the selected command without running it",
    )
    wizard.set_defaults(func=cmd_wizard)

    planning_triage = subparsers.add_parser(
        "planning-triage",
        help="run model-based planning on three-bridge triage",
    )
    planning_triage.add_argument(
        "--out", type=str, default="results/planning-triage"
    )
    planning_triage.add_argument(
        "--seeds", type=str, default="48000,48001,48002,48003,48004"
    )
    planning_triage.add_argument("--model-seed-start", type=int, default=50000)
    planning_triage.add_argument("--population", type=int, default=32)
    planning_triage.add_argument("--elites", type=int, default=8)
    planning_triage.add_argument("--iterations", type=int, default=6)
    planning_triage.add_argument("--random-samples", type=int, default=128)
    planning_triage.add_argument("--model-sequences", type=int, default=300)
    planning_triage.add_argument("--model-seeds", type=int, default=8)
    planning_triage.set_defaults(func=cmd_planning_triage)

    planning_transition = subparsers.add_parser(
        "planning-transition",
        help="run transition-model CEM on three-bridge triage",
    )
    planning_transition.add_argument(
        "--out", type=str, default="results/planning-transition"
    )
    planning_transition.add_argument(
        "--seeds", type=str, default="49000,49001,49002,49003,49004"
    )
    planning_transition.add_argument(
        "--train-seed-start", type=int, default=52000
    )
    planning_transition.add_argument(
        "--eval-seed-start", type=int, default=53000
    )
    planning_transition.add_argument("--train-seeds", type=int, default=8)
    planning_transition.add_argument("--eval-seeds", type=int, default=2)
    planning_transition.add_argument("--ridge", type=float, default=1.0)
    planning_transition.add_argument("--max-sequences", type=int, default=256)
    planning_transition.add_argument("--population", type=int, default=32)
    planning_transition.add_argument("--elites", type=int, default=8)
    planning_transition.add_argument("--iterations", type=int, default=6)
    planning_transition.add_argument(
        "--random-samples", type=int, default=128
    )
    planning_transition.set_defaults(func=cmd_planning_transition)

    planning_transition_ensemble = subparsers.add_parser(
        "planning-transition-ensemble",
        help="run uncertainty-aware transition-ensemble CEM",
    )
    planning_transition_ensemble.add_argument(
        "--out", type=str, default="results/planning-transition-ensemble"
    )
    planning_transition_ensemble.add_argument(
        "--seeds", type=str, default="49000,49001,49002,49003,49004"
    )
    planning_transition_ensemble.add_argument(
        "--train-seed-start", type=int, default=52000
    )
    planning_transition_ensemble.add_argument(
        "--eval-seed-start", type=int, default=53000
    )
    planning_transition_ensemble.add_argument(
        "--train-seeds", type=int, default=8
    )
    planning_transition_ensemble.add_argument(
        "--eval-seeds", type=int, default=2
    )
    planning_transition_ensemble.add_argument("--ridge", type=float, default=1.0)
    planning_transition_ensemble.add_argument(
        "--max-sequences", type=int, default=256
    )
    planning_transition_ensemble.add_argument(
        "--members", type=int, default=8
    )
    planning_transition_ensemble.add_argument("--beta", type=float, default=1.0)
    planning_transition_ensemble.add_argument(
        "--ensemble-seed", type=int, default=20261125
    )
    planning_transition_ensemble.add_argument(
        "--population", type=int, default=32
    )
    planning_transition_ensemble.add_argument("--elites", type=int, default=8)
    planning_transition_ensemble.add_argument(
        "--iterations", type=int, default=6
    )
    planning_transition_ensemble.add_argument(
        "--random-samples", type=int, default=128
    )
    planning_transition_ensemble.set_defaults(
        func=cmd_planning_transition_ensemble
    )

    planning_transition_two_step = subparsers.add_parser(
        "planning-transition-two-step",
        help="run two-step transition CEM on three-bridge triage",
    )
    planning_transition_two_step.add_argument(
        "--out", type=str, default="results/planning-transition-two-step"
    )
    planning_transition_two_step.add_argument(
        "--seeds", type=str, default="49000,49001,49002,49003,49004"
    )
    planning_transition_two_step.add_argument(
        "--train-seed-start", type=int, default=52000
    )
    planning_transition_two_step.add_argument(
        "--eval-seed-start", type=int, default=53000
    )
    planning_transition_two_step.add_argument(
        "--train-seeds", type=int, default=8
    )
    planning_transition_two_step.add_argument(
        "--eval-seeds", type=int, default=2
    )
    planning_transition_two_step.add_argument(
        "--ridge", type=float, default=1.0
    )
    planning_transition_two_step.add_argument(
        "--max-sequences", type=int, default=256
    )
    planning_transition_two_step.add_argument(
        "--population", type=int, default=32
    )
    planning_transition_two_step.add_argument("--elites", type=int, default=8)
    planning_transition_two_step.add_argument(
        "--iterations", type=int, default=6
    )
    planning_transition_two_step.add_argument(
        "--random-samples", type=int, default=128
    )
    planning_transition_two_step.set_defaults(
        func=cmd_planning_transition_two_step
    )

    contract_board = subparsers.add_parser(
        "contract-board",
        help="run the gear-contract board with recipe control",
    )
    contract_board.add_argument(
        "--out", type=str, default="results/contract-board"
    )
    contract_board.add_argument(
        "--seeds", type=str, default="44000,44001,44002,44003,44004"
    )
    contract_board.set_defaults(func=cmd_contract_board)

    recipe_choice = subparsers.add_parser(
        "recipe-choice",
        help="run the fast/expensive vs slow/cheap assembler recipe task",
    )
    recipe_choice.add_argument(
        "--out", type=str, default="results/recipe-choice"
    )
    recipe_choice.add_argument(
        "--seeds", type=str, default="36000,36001,36002,36003,36004"
    )
    recipe_choice.add_argument("--fast-ticks", type=int, default=12)
    recipe_choice.add_argument("--fast-cost", type=int, default=2)
    recipe_choice.add_argument("--slow-ticks", type=int, default=20)
    recipe_choice.add_argument("--slow-cost", type=int, default=1)
    recipe_choice.add_argument("--success-score", type=int, default=150)
    recipe_choice.add_argument("--power-capacity", type=int, default=0)
    recipe_choice.add_argument("--power-radius", type=int, default=8)
    recipe_choice.add_argument("--byproduct", action="store_true")
    recipe_choice.add_argument("--byproduct-capacity", type=int, default=2)
    recipe_choice.set_defaults(func=cmd_recipe_choice)

    crew_triage = subparsers.add_parser(
        "crew-triage",
        help="run three-bridge survivor triage on the twin-line layout",
    )
    crew_triage.add_argument(
        "--out", type=str, default="results/crew-triage"
    )
    crew_triage.add_argument(
        "--seeds", type=str, default="12000,12001,12002,12003,12004"
    )
    crew_triage.set_defaults(func=cmd_crew_triage)

    crew_costs = subparsers.add_parser(
        "crew-costs",
        help="run three-bridge triage with asymmetric repair costs",
    )
    crew_costs.add_argument(
        "--out", type=str, default="results/crew-costs"
    )
    crew_costs.add_argument(
        "--seeds", type=str, default="25000,25001,25002,25003,25004"
    )
    crew_costs.set_defaults(func=cmd_crew_costs)

    crew_topology = subparsers.add_parser(
        "crew-topology",
        help="run three-bridge triage on a random or spread topology",
    )
    crew_topology.add_argument(
        "--layout", choices=("random", "spread"), default="random"
    )
    crew_topology.add_argument(
        "--out", type=str, default="results/crew-topology"
    )
    crew_topology.add_argument(
        "--seeds", type=str, default="28000,28001,28002,28003,28004"
    )
    crew_topology.set_defaults(func=cmd_crew_topology)

    crew_multi_orphan = subparsers.add_parser(
        "crew-multi-orphan",
        help="run sequential survivor dispatch on the twin-line layout",
    )
    crew_multi_orphan.add_argument(
        "--out", type=str, default="results/crew-multi-orphan"
    )
    crew_multi_orphan.add_argument(
        "--seeds", type=str, default="11000,11001,11002,11003,11004"
    )
    crew_multi_orphan.set_defaults(func=cmd_crew_multi_orphan)

    crew_three_replan = subparsers.add_parser(
        "crew-three-replan",
        help="run three-crew assignment with recall and A/C recovery",
    )
    crew_three_replan.add_argument(
        "--out", type=str, default="results/crew-three-replan"
    )
    crew_three_replan.add_argument(
        "--seeds", type=str, default="23000,23001,23002,23003,23004"
    )
    crew_three_replan.set_defaults(func=cmd_crew_three_replan)

    crew_three = subparsers.add_parser(
        "crew-three",
        help="run three-crew assignment on the twin-line layout",
    )
    crew_three.add_argument(
        "--out", type=str, default="results/crew-three"
    )
    crew_three.add_argument(
        "--seeds", type=str, default="21000,21001,21002,21003,21004"
    )
    crew_three.set_defaults(func=cmd_crew_three)

    crew_replacement = subparsers.add_parser(
        "crew-replacement",
        help="run replacement crew handoff on the triage task",
    )
    crew_replacement.add_argument(
        "--out", type=str, default="results/crew-replacement"
    )
    crew_replacement.add_argument(
        "--seeds", type=str, default="19000,19001,19002,19003,19004"
    )
    crew_replacement.set_defaults(func=cmd_crew_replacement)

    crew_budget = subparsers.add_parser(
        "crew-budget",
        help="compare shared, budgeted, and private crew reports",
    )
    crew_budget.add_argument(
        "--out", type=str, default="results/crew-budget"
    )
    crew_budget.add_argument(
        "--seeds", type=str, default="16000,16001,16002,16003,16004"
    )
    crew_budget.add_argument("--radius", type=int, default=16)
    crew_budget.set_defaults(func=cmd_crew_budget)

    crew_private = subparsers.add_parser(
        "crew-private",
        help="compare private crew views with shared reports",
    )
    crew_private.add_argument(
        "--out", type=str, default="results/crew-private"
    )
    crew_private.add_argument(
        "--seeds", type=str, default="13000,13001,13002,13003,13004"
    )
    crew_private.add_argument("--radius", type=int, default=16)
    crew_private.add_argument("--report-age", type=int, default=60)
    crew_private.set_defaults(func=cmd_crew_private)

    crew_decentralized = subparsers.add_parser(
        "crew-decentralized",
        help="run per-crew private-view policies on the spread layout",
    )
    crew_decentralized.add_argument(
        "--out", type=str, default="results/crew-decentralized"
    )
    crew_decentralized.add_argument(
        "--seeds", type=str, default="52000,52001,52002,52003,52004"
    )
    crew_decentralized.add_argument("--q-seeds", type=str, default="0,1,2")
    crew_decentralized.add_argument("--train-episodes", type=int, default=500)
    crew_decentralized.set_defaults(func=cmd_crew_decentralized)

    crew_decentralized_compact = subparsers.add_parser(
        "crew-decentralized-compact",
        help="run compact relative-geometry Q on decentralized triage",
    )
    crew_decentralized_compact.add_argument(
        "--out", type=str, default="results/crew-decentralized-compact"
    )
    crew_decentralized_compact.add_argument(
        "--seeds", type=str, default="56000,56001,56002,56003,56004"
    )
    crew_decentralized_compact.add_argument(
        "--q-seeds", type=str, default="0,1,2"
    )
    crew_decentralized_compact.add_argument(
        "--train-episodes", type=int, default=1000
    )
    crew_decentralized_compact.add_argument(
        "--train-seed-start", type=int, default=60000
    )
    crew_decentralized_compact.set_defaults(
        func=cmd_crew_decentralized_compact
    )

    crew_decentralized_ctde = subparsers.add_parser(
        "crew-decentralized-ctde",
        help="run centralized training with decentralized actors on triage",
    )
    crew_decentralized_ctde.add_argument(
        "--out", type=str, default="results/crew-decentralized-ctde"
    )
    crew_decentralized_ctde.add_argument(
        "--seeds", type=str, default="56000,56001,56002,56003,56004"
    )
    crew_decentralized_ctde.add_argument(
        "--q-seeds", type=str, default="0,1,2"
    )
    crew_decentralized_ctde.add_argument(
        "--train-episodes", type=int, default=1000
    )
    crew_decentralized_ctde.add_argument(
        "--train-seed-start", type=int, default=60000
    )
    crew_decentralized_ctde.add_argument(
        "--warmup-episodes", type=int, default=50
    )
    crew_decentralized_ctde.set_defaults(func=cmd_crew_decentralized_ctde)

    crew_visibility = subparsers.add_parser(
        "crew-visibility",
        help="run local views and delayed reports on the spread layout",
    )
    crew_visibility.add_argument(
        "--out", type=str, default="results/crew-visibility"
    )
    crew_visibility.add_argument(
        "--seeds", type=str, default="10000,10001,10002,10003,10004"
    )
    crew_visibility.add_argument("--radius", type=int, default=16)
    crew_visibility.add_argument("--ages", type=str, default="30,60")
    crew_visibility.set_defaults(func=cmd_crew_visibility)

    crew_layout_ensemble = subparsers.add_parser(
        "crew-layout-ensemble",
        help="run the compact-Q ensemble on twin-line layouts",
    )
    crew_layout_ensemble.add_argument(
        "--out", type=str, default="results/crew-layout-ensemble"
    )
    crew_layout_ensemble.add_argument(
        "--seeds",
        type=str,
        default="9000,9001,9002,9003,9004,9005,9006,9007,9008,9009",
    )
    crew_layout_ensemble.add_argument("--q-seeds", type=str, default="0,1,2")
    crew_layout_ensemble.add_argument("--episodes", type=int, default=2000)
    crew_layout_ensemble.add_argument(
        "--train-seed-start", type=int, default=80000
    )
    crew_layout_ensemble.set_defaults(func=cmd_crew_layout_ensemble)

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
