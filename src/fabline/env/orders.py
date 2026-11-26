"""Seeded production orders and the order-control task."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.env.production_mix import ProductionMixConfig, ProductionMixEnv
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.state import Item

ORDER_CONTROL_TASK_ID = "factory.orders.control.v1"
ORDER_CONTROL_TASK_VERSION = "0.1.0"


@dataclass(frozen=True)
class OrderConfig:
    enabled: bool = False
    order_count: int = 4
    quantity_min: int = 3
    quantity_max: int = 8
    deadline_min: int = 100
    deadline_max: int = 280
    value_min: int = 10
    value_max: int = 25
    failed_penalty_fraction: float = 0.5
    seed_offset: int = 41

    def __post_init__(self) -> None:
        if self.order_count <= 0:
            raise ValueError("order_count must be positive")
        if not 0 < self.quantity_min <= self.quantity_max:
            raise ValueError("invalid quantity range")
        if not 0 < self.deadline_min <= self.deadline_max:
            raise ValueError("invalid deadline range")
        if not 0 <= self.value_min <= self.value_max:
            raise ValueError("invalid value range")
        if not 0.0 <= self.failed_penalty_fraction <= 1.0:
            raise ValueError("failed penalty fraction must be in [0, 1]")


@dataclass
class Order:
    id: int
    item: Item
    quantity: int
    deadline: int
    value_per_unit: int
    fulfilled: int = 0
    failed: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.quantity - self.fulfilled - self.failed)

    @property
    def fulfilled_value(self) -> int:
        return self.fulfilled * self.value_per_unit


@dataclass(frozen=True)
class OrderControlConfig:
    episode_ticks: int = 300
    decision_interval: int = 10
    success_value: int = 160
    orders: OrderConfig = field(
        default_factory=lambda: OrderConfig(enabled=True)
    )

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode ticks and decision interval must be positive")
        if self.success_value < 0:
            raise ValueError("success value must be non-negative")
        if not self.orders.enabled:
            raise ValueError("order control requires orders.enabled")


def generate_orders(
    cfg: OrderConfig,
    seed: int,
    episode_ticks: int,
) -> list[Order]:
    rng = random.Random(seed * 104729 + cfg.seed_offset)
    items = (Item.GEAR, Item.COMPONENT)
    orders: list[Order] = []
    for index in range(cfg.order_count):
        quantity = rng.randint(cfg.quantity_min, cfg.quantity_max)
        deadline = rng.randint(
            cfg.deadline_min, min(cfg.deadline_max, episode_ticks - 20)
        )
        order = Order(
            id=index + 1,
            item=items[rng.randrange(len(items))],
            quantity=quantity,
            deadline=deadline,
            value_per_unit=rng.randint(cfg.value_min, cfg.value_max),
        )
        orders.append(order)
    orders.sort(key=lambda order: (order.deadline, order.id))
    return orders


ORDER_FEATURES = (
    "active_orders_norm",
    "remaining_units_norm",
    "nearest_deadline_norm",
    "gear_remaining_norm",
    "component_remaining_norm",
    "fulfilled_value_norm",
    "failed_units_norm",
)


class OrderObservation:
    """Production view plus order summary."""

    def __init__(self, config: FactoryConfig) -> None:
        self.config = config

    def observe(
        self,
        production_observation: np.ndarray,
        orders: list[Order],
        info: dict[str, Any],
    ) -> np.ndarray:
        active = [order for order in orders if order.remaining > 0]
        remaining = sum(order.remaining for order in active)
        gear = sum(
            order.remaining for order in active if order.item is Item.GEAR
        )
        component = sum(
            order.remaining
            for order in active
            if order.item is Item.COMPONENT
        )
        nearest = (
            min(order.deadline for order in active) - int(info["tick"])
            if active
            else 0
        )
        values = (
            len(active) / max(1, len(orders)),
            remaining / max(1, sum(order.quantity for order in orders)),
            max(0, nearest) / max(1, self.config.ticks_per_episode),
            gear / max(1, sum(order.quantity for order in orders)),
            component / max(1, sum(order.quantity for order in orders)),
            float(info["fulfilled_value"]) / 1000.0,
            float(info["failed_units"]) / max(
                1, sum(order.quantity for order in orders)
            ),
        )
        return np.concatenate(
            [production_observation, np.asarray(values, dtype=np.float32)]
        )


class OrderControlEnv:
    """Choose gear/component production against seeded orders."""

    n_actions = 2
    ACTION_NAMES = ("gear", "component")

    def __init__(
        self,
        config: FactoryConfig,
        mix: ProductionMixConfig | None = None,
        orders: OrderControlConfig | None = None,
    ) -> None:
        self.config = config
        self.mix = mix or ProductionMixConfig(
            episode_ticks=config.ticks_per_episode
        )
        self.order_config = orders or OrderControlConfig(
            episode_ticks=config.ticks_per_episode
        )
        if self.order_config.episode_ticks != config.ticks_per_episode:
            raise ValueError(
                "order episode_ticks must equal config.ticks_per_episode"
            )
        self.base = ProductionMixEnv(config, self.mix)
        self.observation = OrderObservation(config)
        self.orders: list[Order] = []
        self.reset(0)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        production_observation, _ = self.base.reset(seed)
        self.orders = generate_orders(
            self.order_config.orders,
            seed,
            self.config.ticks_per_episode,
        )
        self.fulfilled_value = 0
        self.failed_units = 0
        self.penalty = 0.0
        self.wasted = 0
        self.recipe_switches = 0
        self.last_action = "gear"
        info = self._info()
        return (
            self.observation.observe(
                production_observation, self.orders, info
            ),
            info,
        )

    def _apply_deliveries(
        self,
        before: dict[Item, int],
        after: dict[Item, int],
    ) -> float:
        reward = 0.0
        for item in (Item.GEAR, Item.COMPONENT):
            new_units = int(after.get(item, 0) - before.get(item, 0))
            if new_units <= 0:
                continue
            candidates = [
                order
                for order in self.orders
                if order.item is item
                and order.remaining > 0
                and order.deadline >= self.base.world.state.tick
            ]
            candidates.sort(key=lambda order: (order.deadline, order.id))
            for order in candidates:
                take = min(new_units, order.remaining)
                if take <= 0:
                    continue
                order.fulfilled += take
                self.fulfilled_value += take * order.value_per_unit
                reward += take * order.value_per_unit
                new_units -= take
                if new_units <= 0:
                    break
            self.wasted += max(0, new_units)
        return reward

    def _expire_orders(self) -> float:
        penalty = 0.0
        tick = self.base.world.state.tick
        for order in self.orders:
            if order.remaining <= 0 or order.deadline > tick:
                continue
            lost = order.remaining
            order.failed += lost
            self.failed_units += lost
            amount = (
                lost
                * order.value_per_unit
                * self.order_config.orders.failed_penalty_fraction
            )
            self.penalty += amount
            penalty += amount
        return penalty

    def action_mask(self) -> np.ndarray:
        return np.asarray([True, True], dtype=bool)

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        previous_recipe = self.base.world.state.production_recipe
        if previous_recipe != action:
            self.recipe_switches += 1
        before = dict(self.base.world.state.delivered)
        production_observation, _, terminated, truncated, _ = self.base.step(
            action
        )
        after = dict(self.base.world.state.delivered)
        reward = self._apply_deliveries(before, after)
        penalty = self._expire_orders()
        reward -= penalty
        self.last_action = self.ACTION_NAMES[action]
        info = self._info()
        done = terminated or truncated
        return (
            self.observation.observe(
                production_observation, self.orders, info
            ),
            reward,
            done,
            truncated,
            info,
        )

    def _info(self) -> dict[str, Any]:
        state = self.base.world.state
        return {
            "tick": state.tick,
            "score": state.score,
            "fulfilled_value": self.fulfilled_value,
            "failed_units": self.failed_units,
            "penalty": self.penalty,
            "wasted": self.wasted,
            "recipe_switches": self.recipe_switches,
            "production_recipe": state.production_recipe,
            "success": self.fulfilled_value >= self.order_config.success_value,
            "last_action": self.last_action,
            "orders": [
                {
                    "id": order.id,
                    "item": order.item.name,
                    "quantity": order.quantity,
                    "deadline": order.deadline,
                    "value": order.value_per_unit,
                    "fulfilled": order.fulfilled,
                    "failed": order.failed,
                }
                for order in self.orders
            ],
        }
