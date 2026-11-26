from __future__ import annotations

import pytest

from fabline.harness.generative_audit import (
    GenerativeAuditConfig,
    run_generative_audit,
)


def test_generative_audit_config_validation() -> None:
    with pytest.raises(ValueError):
        GenerativeAuditConfig(seeds=0)
    with pytest.raises(ValueError):
        GenerativeAuditConfig(scenarios=("missing",))


def test_generative_audit_runs() -> None:
    report = run_generative_audit(
        GenerativeAuditConfig(seeds=2, seed_start=1000)
    )
    assert report["lines"] > 0
    assert report["unique_sequences"] >= 1
    assert 0.0 <= report["diversity"] <= 1.0
    assert report["unique_positions"] > 0
