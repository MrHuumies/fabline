from __future__ import annotations

import numpy as np
import pytest

from fabline.env.orders import (
    OrderConfig,
    OrderControlConfig,
    OrderControlEnv,
    generate_orders,
)
from fabline.worlds.factory.config import FactoryConfig


def _config() -> FactoryConfig:
    return FactoryConfig(
        width=16,
        height=8,
        ticks_per_episode=300,
        decision_interval=10,
        entity_budget=32,
        rock_density=0.0,
        ore_patches=1,
        starter_line=True,
        emit_events=True,
    )


def test_order_config_validation() -> None:
    with pytest.raises(ValueError):
        OrderConfig(order_count=0)
    with pytest.raises(ValueError):
        OrderConfig(quantity_min=5, quantity_max=3)
    with pytest.raises(ValueError):
        OrderConfig(deadline_min=300, deadline_max=100)


def test_generate_orders_is_deterministic() -> None:
    cfg = OrderConfig(enabled=True)
    first = generate_orders(cfg, 71000, 300)
    second = generate_orders(cfg, 71000, 300)
    assert [(o.item, o.quantity, o.deadline, o.value_per_unit) for o in first] == [
        (o.item, o.quantity, o.deadline, o.value_per_unit) for o in second
    ]
    assert len(first) == cfg.order_count
    assert all(order.quantity > 0 for order in first)


def test_order_control_env_runs() -> None:
    env = OrderControlEnv(
        _config(),
        orders=OrderControlConfig(episode_ticks=300, success_value=100),
    )
    observation, info = env.reset(0)
    assert observation.shape == (16,)
    assert len(info["orders"]) == 4
    observation, reward, terminated, truncated, info = env.step(0)
    assert observation.shape == (16,)
    assert np.isfinite(reward)
    assert not truncated
    assert info["tick"] == 10
