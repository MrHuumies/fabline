from __future__ import annotations

from pathlib import Path

from fabline.harness.reliability_contract import (
    ReliabilityContractConfig,
    run_reliability_contract,
    write_reliability_contract_report,
)


def _config(**overrides: object) -> ReliabilityContractConfig:
    values: dict[str, object] = {
        "train_blocks": (0, 2),
        "test_blocks": (1, 3),
        "episodes_per_block": 2,
        "tiers": (10, 20, 30),
        "bootstrap_samples": 20,
        "episode_ticks": 200,
    }
    values.update(overrides)
    return ReliabilityContractConfig(**values)  # type: ignore[arg-type]


def test_reliability_contract_runs() -> None:
    report = run_reliability_contract(_config())
    assert report["task"]["id"] == "factory.power.contract.v1"
    assert report["summary"]["train_episodes"] == 4
    assert report["summary"]["test_episodes"] == 4
    assert report["selected"]["mean_tier"] in (10, 20, 30)
    assert report["selected"]["cvar_tier"] in (10, 20, 30)
    assert len(report["test_policy"]["cvar_gain_ci"]) == 2
    assert set(report["gates"]) == {
        "H1_tradeoff",
        "H2_mean_cost",
        "H3_tail_gain",
        "H4_direction",
        "H5_no_free_lunch",
    }
    assert all(isinstance(value, bool) for value in report["gates"].values())


def test_reliability_contract_report(tmp_path: Path) -> None:
    report = run_reliability_contract(_config())
    path = write_reliability_contract_report(tmp_path, report)
    assert path.exists()
    assert "Reliability contract" in path.read_text(encoding="utf-8")
    assert (tmp_path / "reliability_contract_results.json").exists()
