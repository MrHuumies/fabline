from __future__ import annotations

import numpy as np
import pytest

from fabline.harness.layout_shift import (
    LayoutShiftConfig,
    LayoutSpec,
    ShiftSpec,
    layout_shift_gates,
    run_layout_shift,
)
from fabline.harness.models import torch_available
from fabline.obs.layout import LayoutSummaryObservation, PaddedGridObservation
from fabline.obs.vector import VectorObservation
from fabline.tasks.throughput import ThroughputConfig, ThroughputTask
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.world import FactoryWorld


def test_layout_summary_observation_shape() -> None:
    config = FactoryConfig(
        width=20,
        height=12,
        ticks_per_episode=100,
        entity_budget=48,
        rock_density=0.04,
        ore_patches=3,
    )
    observation = LayoutSummaryObservation(config, line_count=2)
    world = FactoryWorld(config)
    world.reset(7)
    values = observation.observe(world.state)
    assert values.shape == observation.spec.shape
    assert len(observation.spec.feature_names or ()) == values.shape[0]
    assert values.shape[0] == 25
    assert np.isfinite(values).all()


def test_throughput_scenario_hook() -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=100,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.02,
        ore_patches=2,
    )
    task = ThroughputTask(
        config,
        ThroughputConfig(
            horizon=20,
            warmup_ticks=20,
            episode_ticks=100,
            sample_interval=20,
        ),
        VectorObservation(config),
        scenario=SCENARIOS["gear"],
    )
    episode = task.generate_episode(11)
    assert episode.observations.ndim == 2
    assert episode.observations.shape[1] == 18
    assert len(episode.labels) == len(episode.observations)
    assert episode.meta["scenario"] == "gear"


def _synthetic_results(base_r2: float, shift_r2: float) -> tuple[dict, dict]:
    base = {
        name: {"test": {"r2": base_r2}, "shift": {"r2": shift_r2}}
        for name in ("linear", "gradient_boosting", "mlp")
    }
    shift = {
        "large": {
            name: {"test": {"r2": base_r2}, "shift": {"r2": shift_r2}}
            for name in ("linear", "gradient_boosting", "mlp")
        }
    }
    return base, shift


def test_layout_shift_gates() -> None:
    cfg = LayoutShiftConfig(
        base_specs=(
            LayoutSpec(
                "base",
                16,
                8,
                "gear",
                0.02,
                2,
                32,
            ),
        ),
        shifts=(
            ShiftSpec(
                LayoutSpec(
                    "large",
                    32,
                    24,
                    "spread_gear",
                    0.06,
                    4,
                    64,
                ),
                seed_start=100,
                count=1,
            ),
        ),
        train_seeds=(1, 2),
        val_seeds=(3,),
        test_seeds=(4,),
    )
    base, shift = _synthetic_results(0.8, 0.2)
    gates = layout_shift_gates(base, shift, cfg)
    assert gates["H1_base_skill"]
    assert gates["H2_ood_gap"]
    assert gates["H3_no_seed_leakage"]
    assert gates["H4_metrics_complete"]
    assert gates["base_model"] == "linear"


def test_layout_shift_gates_detect_seed_leakage() -> None:
    cfg = LayoutShiftConfig(
        base_specs=(
            LayoutSpec("base", 16, 8, "gear", 0.02, 2, 32),
        ),
        shifts=(
            ShiftSpec(
                LayoutSpec("large", 32, 24, "spread_gear", 0.06, 4, 64),
                seed_start=4,
                count=1,
            ),
        ),
        train_seeds=(1, 2),
        val_seeds=(3,),
        test_seeds=(4,),
    )
    base, shift = _synthetic_results(0.8, 0.2)
    gates = layout_shift_gates(base, shift, cfg)
    assert not gates["H3_no_seed_leakage"]


def test_run_layout_shift_smoke() -> None:
    cfg = LayoutShiftConfig(
        base_specs=(
            LayoutSpec("base", 16, 8, "gear", 0.02, 2, 32),
        ),
        shifts=(
            ShiftSpec(
                LayoutSpec("large", 32, 24, "spread_gear", 0.06, 4, 64),
                seed_start=300,
                count=1,
            ),
        ),
        train_seeds=(101, 102, 103),
        val_seeds=(104,),
        test_seeds=(105,),
        task_config=ThroughputConfig(
            horizon=20,
            warmup_ticks=20,
            episode_ticks=100,
            sample_interval=20,
        ),
        observation="layout-summary",
        normalize_target=True,
    )
    report = run_layout_shift(cfg)
    assert report["dataset"]["train"] > 0
    assert "large" in report["dataset"]["shift"]
    assert "base" in report["metrics"]
    assert "large" in report["metrics"]["shift"]
    assert "gates" in report


def test_padded_grid_observation_shape() -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=100,
        entity_budget=32,
        rock_density=0.02,
        ore_patches=2,
    )
    observation = PaddedGridObservation(config, line_count=1)
    world = FactoryWorld(config)
    world.reset(7)
    values = observation.observe(world.state)
    assert values.shape == observation.spec.shape == (24, 32, 14)
    assert float(values[:8, :16, 6].sum()) == 8 * 16
    assert float(values[8:, :, :6].sum()) == 0.0
    assert np.allclose(values[:, :, 7], 16.0 / 32.0)


def test_throughput_padded_grid() -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=100,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.02,
        ore_patches=2,
    )
    task = ThroughputTask(
        config,
        ThroughputConfig(
            horizon=20,
            warmup_ticks=20,
            episode_ticks=100,
            sample_interval=20,
        ),
        PaddedGridObservation(config, line_count=1),
        scenario=SCENARIOS["gear"],
        flatten=False,
    )
    episode = task.generate_episode(11)
    assert episode.observations.shape[1:] == (24, 32, 14)
    assert len(episode.labels) == len(episode.observations)


@pytest.mark.skipif(not torch_available(), reason="torch is not installed")
def test_layout_shift_cnn_smoke() -> None:
    base = LayoutSpec("base", 16, 8, "gear", 0.02, 2, 32)
    shift = ShiftSpec(
        LayoutSpec("large", 32, 24, "spread_gear", 0.06, 4, 64),
        seed_start=300,
        count=1,
    )
    cfg = LayoutShiftConfig(
        base_specs=(base,),
        shifts=(shift,),
        train_seeds=(101, 102, 103),
        val_seeds=(104,),
        test_seeds=(105,),
        task_config=ThroughputConfig(
            horizon=10,
            warmup_ticks=10,
            episode_ticks=50,
            sample_interval=10,
        ),
        observation="padded-grid",
        normalize_target=True,
        cnn_epochs=2,
        cnn_hidden=8,
    )
    report = run_layout_shift(cfg)
    assert "cnn" in report["metrics"]["base"]
    assert "cnn" in report["metrics"]["shift"]["large"]
