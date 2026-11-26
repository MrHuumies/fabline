"""Interactive, stdlib-only wizard for common FABLINE commands."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from fabline.cli.browser import (
    find_replays,
    find_task_cards,
    format_replay_table,
    format_task_card_table,
    read_task_card,
    resolve_task_card,
    summarize_replay,
)

OutputFn = Callable[[str], None]
InputFn = Callable[[str], str]
Runner = Callable[[Sequence[str]], int]


class WizardAbort(Exception):
    """Raised when the user cancels or input ends."""


def _run_command(argv: Sequence[str]) -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "fabline", *argv],
        check=False,
    )
    return int(completed.returncode)


def _ask(
    prompt: str,
    *,
    default: str,
    input_fn: InputFn,
) -> str:
    suffix = f" [{default}]" if default else ""
    try:
        value = input_fn(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt) as exc:
        raise WizardAbort from exc
    return value or default


def _ask_int(
    prompt: str,
    *,
    default: int,
    input_fn: InputFn,
    minimum: int = 1,
) -> int:
    while True:
        raw = _ask(prompt, default=str(default), input_fn=input_fn)
        try:
            value = int(raw)
        except ValueError:
            continue
        if value >= minimum:
            return value


def _ask_yes_no(
    prompt: str,
    *,
    default: bool,
    input_fn: InputFn,
) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        try:
            raw = input_fn(f"{prompt} [{hint}]: ").strip().lower()
        except (EOFError, KeyboardInterrupt) as exc:
            raise WizardAbort from exc
        if raw == "":
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False


def _print_menu(output_fn: OutputFn) -> None:
    output_fn("")
    output_fn("FABLINE wizard")
    output_fn("  1. smoke a short run (fast)")
    output_fn("  2. shared-suite benchmark (factory-v0.1)")
    output_fn("  3. factory-v0.2 benchmark (long)")
    output_fn("  4. build a debug dataset")
    output_fn("  5. check factory-v0.2 against its expected summary")
    output_fn("  6. summarize a factory-v0.2 result file")
    output_fn("  7. browse replay files")
    output_fn("  8. view a task card")
    output_fn("  9. quit")
    output_fn("")


def _prompt_choice(input_fn: InputFn, output_fn: OutputFn) -> str:
    while True:
        _print_menu(output_fn)
        try:
            choice = input_fn("select> ").strip().lower()
        except (EOFError, KeyboardInterrupt) as exc:
            raise WizardAbort from exc
        if choice in {"1", "smoke"}:
            return "smoke"
        if choice in {"2", "shared", "shared-suite"}:
            return "shared"
        if choice in {"3", "v02", "benchmark-v02"}:
            return "benchmark"
        if choice in {"4", "dataset"}:
            return "dataset"
        if choice in {"5", "check"}:
            return "check"
        if choice in {"6", "summary"}:
            return "summary"
        if choice in {"7", "replay", "replays"}:
            return "replays"
        if choice in {"8", "card", "cards"}:
            return "task_card"
        if choice in {"9", "q", "quit", "exit"}:
            return "quit"
        output_fn(f"Unknown choice: {choice!r}")


def _smoke(input_fn: InputFn) -> list[str]:
    ticks = _ask_int("ticks", default=200, input_fn=input_fn)
    return ["smoke", "--ticks", str(ticks)]


def _shared(input_fn: InputFn) -> list[str]:
    out = _ask(
        "output directory",
        default="results/factory-v0.1",
        input_fn=input_fn,
    )
    return ["shared-suite", "--out", out]


def _benchmark(input_fn: InputFn) -> list[str]:
    out = _ask(
        "output directory",
        default="results/factory-v0.2",
        input_fn=input_fn,
    )
    argv = ["benchmark-v02", "--out", out]
    if not _ask_yes_no(
        "include the planning block (long)?",
        default=True,
        input_fn=input_fn,
    ):
        argv.append("--skip-planning")
    if not _ask_yes_no(
        "include fault/power diagnostics?",
        default=True,
        input_fn=input_fn,
    ):
        argv.append("--skip-diagnostics")
    return argv


def _dataset(input_fn: InputFn) -> list[str]:
    episodes = _ask_int("episodes", default=100, input_fn=input_fn)
    out = _ask(
        "output directory",
        default="datasets/factory-debug-v0.1",
        input_fn=input_fn,
    )
    return ["dataset", "--episodes", str(episodes), "--out", out]


def _check(input_fn: InputFn) -> list[str]:
    out = _ask(
        "run output directory",
        default="results/factory-v0.2",
        input_fn=input_fn,
    )
    return [
        "benchmark-v02",
        "--out",
        out,
        "--check-expected",
        "benchmarks/factory-v0.2/expected/summary.json",
    ]


def _replays(input_fn: InputFn, output_fn: OutputFn) -> int:
    root = _ask("replay root", default="datasets", input_fn=input_fn)
    paths = find_replays(root)
    if not paths:
        output_fn(f"no replay.json files under {root}")
        return 0
    summaries = [summarize_replay(path) for path in paths]
    output_fn(format_replay_table(summaries, limit=20))
    query = _ask(
        "replay number or path (blank to stop)",
        default="",
        input_fn=input_fn,
    )
    if not query:
        return 0
    if query.isdigit():
        index = int(query) - 1
        if not 0 <= index < len(paths):
            output_fn(f"no replay at index {query}")
            return 1
        path = paths[index]
    else:
        path = Path(query)
    if not path.exists():
        output_fn(f"not found: {path}")
        return 1
    output_fn(format_replay_table([summarize_replay(path)]))
    return 0


def _task_card(input_fn: InputFn, output_fn: OutputFn) -> int:
    root = _ask("task-card root", default="docs/tasks", input_fn=input_fn)
    cards = find_task_cards(root)
    if not cards:
        output_fn(f"no task cards under {root}")
        return 0
    output_fn(format_task_card_table(cards))
    query = _ask(
        "card number or name (blank to stop)",
        default="",
        input_fn=input_fn,
    )
    if not query:
        return 0
    card = resolve_task_card(cards, query)
    if card is None:
        output_fn(f"task card not found: {query}")
        return 1
    output_fn("")
    output_fn(read_task_card(card))
    return 0


def _summarize(input_fn: InputFn, output_fn: OutputFn) -> int:
    path = _ask(
        "result JSON",
        default="results/factory-v0.2/factory_v02_results.json",
        input_fn=input_fn,
    )
    result_path = Path(path)
    if not result_path.exists():
        output_fn(f"not found: {path}")
        return 1
    try:
        report = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        output_fn(f"could not read {path}: {exc}")
        return 1
    blocks = report.get("blocks", {})
    core = blocks.get("core", {})
    output_fn(
        f"{report.get('benchmark', '?')} ({report.get('status', '?')}): "
        f"{core.get('episodes', '?')} episodes, "
        f"{core.get('samples', '?')} samples"
    )
    planning = blocks.get("planning", {}).get("results", {})
    if planning:
        output_fn(
            "planning: "
            f"CEM true {planning.get('cem_true', {}).get('mean_score', '?')}, "
            f"oracle {planning.get('oracle', {}).get('mean_score', '?')}, "
            f"random {planning.get('random', {}).get('mean_score', '?')}, "
            f"CEM learned {planning.get('cem_learned', {}).get('mean_score', '?')}"
        )
    calibration = blocks.get("calibration", {})
    calibration_blocks = [
        calibration.get("primary"),
        *calibration.get("blocks", []),
    ]
    top4 = [
        block["views"]["context_thermal_vibration_top4"]
        for block in calibration_blocks
        if block and "context_thermal_vibration_top4" in block.get("views", {})
    ]
    if top4:
        ece = [
            block["calibration"]["gbdt"]["test"]["ece"] for block in top4
        ]
        balanced = [
            block["metrics"]["gbdt"]["test"]["balanced_accuracy"]
            for block in top4
        ]
        output_fn(
            "calibration top-4 GBDT: "
            f"balanced {sum(balanced) / len(balanced):.3f}, "
            f"ECE {sum(ece) / len(ece):.3f} (mean of {len(top4)} blocks)"
        )
    causal = blocks.get("causal", {})
    causal_blocks = [causal.get("primary"), *causal.get("blocks", [])]
    target = [
        block["views"]["target"]["gbdt"]["r2"]
        for block in causal_blocks
        if block and "target" in block.get("views", {})
    ]
    if target:
        output_fn(
            f"causal target GBDT R²: {sum(target) / len(target):.3f} "
            f"(mean of {len(target)} blocks)"
        )
    return 0


def run_wizard(
    *,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
    runner: Runner = _run_command,
    dry_run: bool = False,
) -> int:
    """Run the interactive wizard. Returns the last command's exit code."""

    try:
        choice = _prompt_choice(input_fn, output_fn)
        if choice == "quit":
            output_fn("bye")
            return 0
        if choice == "summary":
            return _summarize(input_fn, output_fn)
        if choice == "replays":
            return _replays(input_fn, output_fn)
        if choice == "task_card":
            return _task_card(input_fn, output_fn)
        if choice == "smoke":
            argv = _smoke(input_fn)
        elif choice == "shared":
            argv = _shared(input_fn)
        elif choice == "benchmark":
            argv = _benchmark(input_fn)
        elif choice == "dataset":
            argv = _dataset(input_fn)
        else:
            argv = _check(input_fn)
        output_fn("")
        command = " ".join(shlex.quote(part) for part in argv)
        output_fn(f"command: fabline {command}")
        if dry_run:
            output_fn("dry run: not executed")
            return 0
        if not _ask_yes_no("run it?", default=True, input_fn=input_fn):
            output_fn("not run")
            return 0
        output_fn("")
        return int(runner(argv))
    except WizardAbort:
        output_fn("cancelled")
        return 1
