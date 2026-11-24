from __future__ import annotations

import numpy as np
import pytest

from fabline.harness.causal_intervention import CausalConfig, generate_causal


def test_causal_config_validation() -> None:
    with pytest.raises(ValueError):
        CausalConfig(episodes=0)
    with pytest.raises(ValueError):
        CausalConfig(sample_ticks=())
    with pytest.raises(ValueError):
        CausalConfig(horizon=0)


def test_causal_generation_pair_shapes() -> None:
    data = generate_causal(
        CausalConfig(
            episodes=2,
            seed_start=58000,
            sample_ticks=(150,),
            horizon=20,
        )
    )
    assert data["target_a"].shape[1] == 8
    assert data["target_b"].shape[1] == 8
    assert data["state"].shape[1] == 18
    assert len(data["label"]) == len(data["split"])
    assert np.isfinite(data["label"]).all()
