from __future__ import annotations

import pytest

pytest.importorskip("torch")

from fabline.env.orders import OrderControlConfig  # noqa: E402
from fabline.harness.order_rl import OrderRLConfig, run_order_rl  # noqa: E402
from fabline.worlds.factory.config import FactoryConfig  # noqa: E402


def test_order_rl_smoke() -> None:
    config = FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=120,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )
    orders = OrderControlConfig(
        episode_ticks=120,
        decision_interval=10,
        success_value=60,
    )
    report = run_order_rl(
        config,
        orders,
        OrderRLConfig(
            eval_seeds=(76000,),
            ppo_seeds=(0,),
            ppo_steps=64,
            ppo_rollout=64,
            bc_episodes=2,
            bc_epochs=1,
        ),
    )
    assert "bc" in report["results"]
    assert "ppo" in report["results"]
    assert report["results"]["bc"]["model"]["parameters"] > 0
