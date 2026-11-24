from __future__ import annotations

import json
from collections.abc import Callable, Iterator

from fabline.cli.wizard import run_wizard


def _inputs(values: list[str]) -> tuple[Callable[[str], str], list[str]]:
    iterator: Iterator[str] = iter(values)
    prompts: list[str] = []

    def read(prompt: str) -> str:
        prompts.append(prompt)
        try:
            return next(iterator)
        except StopIteration as exc:
            raise EOFError from exc

    return read, prompts


def test_wizard_smoke_dry_run() -> None:
    read, _ = _inputs(["1", "200"])
    lines: list[str] = []
    code = run_wizard(input_fn=read, output_fn=lines.append, dry_run=True)
    assert code == 0
    assert any("fabline smoke --ticks 200" in line for line in lines)
    assert any("dry run" in line for line in lines)


def test_wizard_benchmark_skips() -> None:
    read, _ = _inputs(["3", "", "n", "n"])
    lines: list[str] = []
    code = run_wizard(input_fn=read, output_fn=lines.append, dry_run=True)
    assert code == 0
    command = next(line for line in lines if "fabline benchmark-v02" in line)
    assert "--skip-planning" in command
    assert "--skip-diagnostics" in command


def test_wizard_runs_selected_command() -> None:
    read, _ = _inputs(["2", "results/custom", "y"])
    lines: list[str] = []
    calls: list[list[str]] = []

    def runner(argv) -> int:
        calls.append(list(argv))
        return 0

    code = run_wizard(input_fn=read, output_fn=lines.append, runner=runner)
    assert code == 0
    assert calls == [["shared-suite", "--out", "results/custom"]]


def test_wizard_summarizes_result(tmp_path) -> None:
    report = {
        "benchmark": "factory-v0.2",
        "status": "frozen",
        "blocks": {
            "core": {"episodes": 159, "samples": 2948},
            "planning": {
                "results": {
                    "cem_true": {"mean_score": 462},
                    "oracle": {"mean_score": 462},
                    "random": {"mean_score": 108},
                    "cem_learned": {"mean_score": 232},
                }
            },
            "calibration": {
                "primary": {
                    "views": {
                        "context_thermal_vibration_top4": {
                            "metrics": {
                                "gbdt": {"test": {"balanced_accuracy": 0.95}}
                            },
                            "calibration": {"gbdt": {"test": {"ece": 0.008}}},
                        }
                    }
                },
                "blocks": [],
            },
            "causal": {
                "primary": {"views": {"target": {"gbdt": {"r2": 0.9}}}},
                "blocks": [],
            },
        },
    }
    path = tmp_path / "result.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    read, _ = _inputs(["6", str(path)])
    lines: list[str] = []
    code = run_wizard(input_fn=read, output_fn=lines.append, dry_run=True)
    assert code == 0
    assert any("159 episodes" in line for line in lines)
    assert any("CEM true 462" in line for line in lines)
    assert any("balanced 0.950" in line for line in lines)
    assert any("0.900" in line for line in lines)


def test_wizard_check_expected() -> None:
    read, _ = _inputs(["5", ""])
    lines: list[str] = []
    code = run_wizard(input_fn=read, output_fn=lines.append, dry_run=True)
    assert code == 0
    command = next(line for line in lines if "fabline benchmark-v02" in line)
    assert "--check-expected" in command


def test_wizard_invalid_choice_then_quit() -> None:
    read, _ = _inputs(["nope", "7"])
    lines: list[str] = []
    code = run_wizard(input_fn=read, output_fn=lines.append, dry_run=True)
    assert code == 0
    assert any("Unknown choice" in line for line in lines)
    assert lines[-1] == "bye"


def test_wizard_cancels_on_eof() -> None:
    read, _ = _inputs([])
    lines: list[str] = []
    code = run_wizard(input_fn=read, output_fn=lines.append, dry_run=True)
    assert code == 1
    assert lines[-1] == "cancelled"
