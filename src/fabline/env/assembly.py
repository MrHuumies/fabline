"""Assembly-edge production control on a fixed two-feed assembly cell."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.worlds.factory.assembly import generate_assembly_state
from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.production import ProductionConfig
from fabline.worlds.factory.state import Entity, EntityType, Item
from fabline.worlds.factory.world import FactoryWorld

ASSEMBLY_CONTROL_TASK_ID = "factory.assembly.control.v1"
ASSEMBLY_CONTROL_TASK_VERSION = "0.1.0"

ASSEMBLY_FEATURES = (
    "tick_norm",
    "score_norm",
    "recipe_gear",
    "recipe_assembly",
    "assembly_input_ingot_norm",
    "assembly_input_component_norm",
    "assembly_output_norm",
    "component_input_norm",
    "component_output_norm",
    "component_craft_norm",
    "assembly_craft_norm",
    "delivered_gear_norm",
)


@dataclass(frozen=True)
class AssemblyControlConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    success_score: int = 100
    initial_component_max: int = 0
    initial_ingot_max: int = 0
    production: ProductionConfig = field(
        default_factory=lambda: ProductionConfig(
            enabled=True,
            assembly_enabled=True,
            component_ticks=24,
            assembly_ticks=16,
            assembly_output=2,
        )
    )

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode ticks and decision interval must be positive")
        if self.success_score < 0:
            raise ValueError("success_score must be non-negative")
        if self.initial_component_max < 0 or self.initial_ingot_max < 0:
            raise ValueError("initial buffers must be non-negative")
        if not self.production.enabled or not self.production.assembly_enabled:
            raise ValueError("assembly control requires the assembly production tree")


class AssemblyControlEnv:
    """Choose direct-gear or assembly recipe for the assembly assembler."""

    n_actions = 2
    ACTION_NAMES = ("gear", "assembly")

    def __init__(
        self,
        config: FactoryConfig,
        assembly: AssemblyControlConfig | None = None,
    ) -> None:
        self.config = config
        self.assembly = assembly or AssemblyControlConfig()
        if self.assembly.episode_ticks != self.config.ticks_per_episode:
            raise ValueError("assembly episode ticks must match config")
        self.world = FactoryWorld(
            config, production=self.assembly.production
        )
        self.reset(0)

    def _assembler(self, x: int) -> Entity:
        return next(
            entity
            for entity in self.world.state.entities.values()
            if entity.type is EntityType.ASSEMBLER and entity.x == x
        )

    def _component_assembler(self) -> Entity:
        return self._assembler(5)

    def _assembly_assembler(self) -> Entity:
        return self._assembler(7)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.set_state(generate_assembly_state(self.config, seed))
        rng = random.Random(seed * 104_729 + 23)
        component = self._component_assembler()
        assembly = self._assembly_assembler()
        component.recipe = 1
        assembly.recipe = 0
        assembly.input_buffer[Item.INGOT] = rng.randint(
            0, self.assembly.initial_ingot_max
        )
        assembly.input_buffer[Item.COMPONENT] = rng.randint(
            0, self.assembly.initial_component_max
        )
        self.total_reward = 0.0
        self.steps = 0
        self.switches = 0
        self.last_action = 0
        self.last_reward = 0.0
        return self._observation(), self._info()

    def action_mask(self) -> np.ndarray:
        return np.asarray([True, True], dtype=bool)

    def step(
        self, action: int
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        assembly = self._assembly_assembler()
        recipe = 0 if action == 0 else 2
        if assembly.recipe != recipe:
            self.switches += 1
        assembly.recipe = recipe
        before = self.world.state.score
        self.world.run_ticks(self.assembly.decision_interval)
        reward = float(self.world.state.score - before)
        self.total_reward += reward
        self.steps += 1
        self.last_action = action
        self.last_reward = reward
        return (
            self._observation(),
            reward,
            self.world.done,
            False,
            self._info(),
        )

    def _observation(self) -> np.ndarray:
        state = self.world.state
        assembly = self._assembly_assembler()
        component = self._component_assembler()
        cap = max(1, self.config.assembler_input_capacity)
        out_cap = max(1, self.config.assembler_output_capacity)
        values = (
            state.tick / self.assembly.episode_ticks,
            state.score / 500.0,
            1.0 if assembly.recipe == 0 else 0.0,
            1.0 if assembly.recipe == 2 else 0.0,
            assembly.input_buffer.get(Item.INGOT, 0) / cap,
            assembly.input_buffer.get(Item.COMPONENT, 0) / cap,
            assembly.output_buffer.get(Item.GEAR, 0) / out_cap,
            component.input_buffer.get(Item.INGOT, 0) / cap,
            component.output_buffer.get(Item.COMPONENT, 0) / out_cap,
            component.craft_progress / max(1, self.assembly.production.component_ticks),
            assembly.craft_progress / max(1, self.assembly.production.assembly_ticks),
            state.delivered.get(Item.GEAR, 0) / 100.0,
        )
        return np.asarray(values, dtype=np.float32)

    def _info(self) -> dict[str, Any]:
        state = self.world.state
        assembly = self._assembly_assembler()
        component = self._component_assembler()
        return {
            "tick": state.tick,
            "score": state.score,
            "delivered_gear": state.delivered.get(Item.GEAR, 0),
            "delivered_component": state.delivered.get(Item.COMPONENT, 0),
            "recipe": assembly.recipe,
            "assembly_component": assembly.input_buffer.get(Item.COMPONENT, 0),
            "assembly_ingot": assembly.input_buffer.get(Item.INGOT, 0),
            "component_output": component.output_buffer.get(Item.COMPONENT, 0),
            "switches": self.switches,
            "steps": self.steps,
            "total_reward": self.total_reward,
            "last_action": self.last_action,
            "last_reward": self.last_reward,
            "success": state.score >= self.assembly.success_score,
        }
