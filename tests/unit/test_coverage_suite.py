from __future__ import annotations

from pathlib import Path

from fabline.harness.coverage_suite import (
    CoverageSuiteConfig,
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
    assert report["status"] == "candidate"
    assert set(report["tasks"]) == {
        "reliability-contract",
        "wired-cascade",
        "partial-throughput",
    }
    assert report["summary"]["tasks"] == 3
    assert 0 <= report["summary"]["passed"] <= 3
    assert (tmp_path / "coverage_suite_results.json").exists()
    assert (tmp_path / "coverage_suite_report.md").exists()
    assert (tmp_path / "reliability-contract").is_dir()
    assert (tmp_path / "wired-cascade").is_dir()
    assert (tmp_path / "partial-throughput").is_dir()
