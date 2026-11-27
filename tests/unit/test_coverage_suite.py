from __future__ import annotations

from pathlib import Path

from fabline.harness.coverage_suite import (
    CoverageSuiteConfig,
    build_expected_summary,
    compare_coverage_expected,
    run_coverage_suite,
)


def test_coverage_suite_fast(tmp_path: Path) -> None:
    report = run_coverage_suite(
        tmp_path,
        CoverageSuiteConfig(
            fast=True,
            include_mpnn=False,
            include_sequence=False,
        ),
    )
    assert report["benchmark"] == "factory-v0.4-coverage"
    assert report["status"] == "frozen"
    assert set(report["tasks"]) == {
        "reliability-contract",
        "wired-cascade",
        "partial-throughput",
        "crew-schedule",
        "crew-triage",
        "preventive-wire",
        "recipe-choice",
        "maintenance-threshold",
    }
    assert report["summary"]["tasks"] == 8
    assert 0 <= report["summary"]["passed"] <= 8
    assert (tmp_path / "coverage_suite_results.json").exists()
    assert (tmp_path / "coverage_suite_report.md").exists()
    for name in (
        "reliability-contract",
        "wired-cascade",
        "partial-throughput",
        "crew-schedule",
        "crew-triage",
        "preventive-wire",
        "recipe-choice",
        "maintenance-threshold",
    ):
        assert (tmp_path / name).is_dir()
    summary = build_expected_summary(report)
    assert summary["benchmark"] == "factory-v0.4"
    assert summary["headline_tasks"] == [
        "reliability-contract",
        "partial-throughput",
        "crew-schedule",
        "crew-triage",
        "preventive-wire",
        "recipe-choice",
        "maintenance-threshold",
    ]
    assert summary["diagnostics"] == ["wired-cascade"]
    assert compare_coverage_expected(summary, summary) == []
