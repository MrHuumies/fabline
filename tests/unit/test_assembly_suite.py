from __future__ import annotations

from pathlib import Path

from fabline.harness.assembly_suite import (
    HEADLINE_TASKS,
    AssemblySuiteConfig,
    build_expected_summary,
    compare_assembly_expected,
    run_assembly_suite,
)


def test_assembly_suite_fast(tmp_path: Path) -> None:
    report = run_assembly_suite(tmp_path, AssemblySuiteConfig(fast=True))
    assert report["summary"]["tasks"] == 4
    assert set(report["tasks"]) == set(HEADLINE_TASKS)
    for name in HEADLINE_TASKS:
        assert (tmp_path / name).is_dir()
    summary = build_expected_summary(report)
    assert summary["benchmark"] == "factory-v0.5"
    assert summary["version"] == "0.5.0"
    assert summary["headline_tasks"] == list(HEADLINE_TASKS)
    assert set(summary["tasks"]) == set(HEADLINE_TASKS)
    assert compare_assembly_expected(summary, summary) == []
