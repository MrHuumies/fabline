"""Wire-repair control on the opt-in wired power topology."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.generator import SCENARIOS
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import Entity, PowerWire
from fabline.worlds.factory.wire import entity_connected, reachable_cells
from fabline.worlds.factory.world import FactoryWorld

WIRE_REPAIR_TASK_ID = "factory.power.wire-repair.v1"
WIRE_REPAIR_TASK_VERSION = "0.1.0"

WIRE_REPAIR_FEATURES = (
    "tick_norm",
    "score_norm",
    "budget_norm",
    "failed_norm",
    "max_outage_norm",
    "total_outage_norm",
    *(
        f"slot_{slot}_{name}"
        for slot in range(1, 4)
        for name in ("outage_norm", "is_bridge", "age_norm", "exists")
    ),
)


@dataclass(frozen=True)
class WireRepairConfig:
    episode_ticks: int = 500
    decision_interval: int = 10
    repair_budget: int = 2
    repair_cost: float = 1.0
    restoration_reward: float = 10.0
    wasted_penalty: float = 20.0
    success_score: int = 150
    fault_ticks: tuple[int, ...] = (50, 150, 250)
    max_slots: int = 3
    power: PowerConfig = field(
        default_factory=lambda: PowerConfig(
            enabled=True,
            topology="wired",
            generator_count=1,
            generator_capacity=12,
            generator_radius=8,
            wire_redundancy=2,
        )
    )

    def __post_init__(self) -> None:
        if self.episode_ticks <= 0 or self.decision_interval <= 0:
            raise ValueError("episode_ticks and decision_interval must be positive")
        if self.repair_budget < 0:
            raise ValueError("repair_budget must be non-negative")
        if self.repair_cost < 0:
            raise ValueError("repair_cost must be non-negative")
        if self.restoration_reward < 0:
            raise ValueError("restoration_reward must be non-negative")
        if self.wasted_penalty < 0:
            raise ValueError("wasted_penalty must be non-negative")
        if self.success_score < 0:
            raise ValueError("success_score must be non-negative")
        if not self.power.enabled or self.power.topology != "wired":
            raise ValueError("wire repair requires wired power")
        if self.max_slots <= 0:
            raise ValueError("max_slots must be positive")
        if len(self.fault_ticks) > self.max_slots:
            raise ValueError("fault_ticks cannot exceed max_slots")
        if any(tick <= 0 for tick in self.fault_ticks):
            raise ValueError("fault ticks must be positive")
        if list(self.fault_ticks) != sorted(set(self.fault_ticks)):
            raise ValueError("fault ticks must be strictly increasing")


class WireRepairEnv:
    """Choose a failed wire to repair under a limited budget."""

    n_actions = 4
    ACTION_NAMES = ("noop", "slot_1", "slot_2", "slot_3")

    def __init__(
        self,
        config: FactoryConfig,
        repair: WireRepairConfig | None = None,
    ) -> None:
        self.config = config
        self.repair = repair or WireRepairConfig()
        if not self.config.starter_line:
            raise ValueError("wire repair requires a starter line")
        if self.repair.episode_ticks != self.config.ticks_per_episode:
            raise ValueError(
                "repair.episode_ticks must equal config.ticks_per_episode"
            )
        self.world = FactoryWorld(config, power=self.repair.power)
        self.reset(0)

    def reset(self, seed: int = 0) -> tuple[np.ndarray, dict[str, Any]]:
        self.world.reset(seed, SCENARIOS["gear"])
        self.total_reward = 0.0
        self.repairs = 0
        self.wasted_repairs = 0
        self.steps = 0
        self.last_action = "noop"
        self.last_reward = 0.0
        self._impact_cache: dict[int, int] | None = None
        self.fault_schedule = self._choose_faults()
        self._fault_index = 0
        return self._observation(), self._info()

    def _consumers(self) -> list[Entity]:
        return [
            entity
            for entity in sorted(
                self.world.state.entities.values(), key=lambda item: item.id
            )
            if self.repair.power.demand(entity.type) > 0
        ]

    def _connected_ids(self) -> set[int]:
        wires = self.world.state.power_wires
        reachable = reachable_cells(
            self.world.state.power_sources[0], wires
        )
        return {
            entity.id
            for entity in self._consumers()
            if entity_connected(entity, reachable, wires)
        }

    def _outage(self, wire: PowerWire) -> int:
        """Connectivity impact of flipping this wire's failed flag."""

        before = self._connected_ids()
        was_failed = wire.failed
        wire.failed = not was_failed
        after = self._connected_ids()
        wire.failed = was_failed
        return len(before.symmetric_difference(after))

    def _outages(self) -> dict[int, int]:
        if self._impact_cache is None:
            self._impact_cache = {
                wire.id: self._outage(wire)
                for wire in self.world.state.power_wires
            }
        return self._impact_cache

    def _choose_faults(self) -> list[tuple[int, int]]:
        outages = self._outages()
        positive = sorted(
            (wire_id for wire_id, size in outages.items() if size > 0),
            key=lambda wire_id: (outages[wire_id], wire_id),
        )
        loops = sorted(
            wire_id for wire_id, size in outages.items() if size == 0
        )
        chosen: list[int] = []
        if loops:
            chosen.append(loops[0])
        if positive:
            chosen.append(positive[0])
        if len(positive) > 1:
            chosen.append(positive[-1])
        chosen = list(dict.fromkeys(chosen))
        ticks = self.repair.fault_ticks[: len(chosen)]
        return list(zip(ticks, chosen, strict=True))

    def _failed(self) -> list[tuple[PowerWire, int]]:
        outages = self._outages()
        failed = [
            wire for wire in self.world.state.power_wires if wire.failed
        ]
        failed.sort(key=lambda wire: (-outages[wire.id], wire.id))
        return [(wire, outages[wire.id]) for wire in failed]

    def _slots(self) -> list[tuple[PowerWire, int]]:
        return self._failed()[: self.repair.max_slots]

    def action_mask(self) -> np.ndarray:
        mask = np.zeros(self.n_actions, dtype=bool)
        mask[0] = True
        if self.repairs < self.repair.repair_budget:
            for index in range(len(self._slots())):
                mask[index + 1] = True
        return mask

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if action < 0 or action >= self.n_actions:
            raise ValueError(f"action {action} is outside the action space")
        slots = self._slots()
        legal = bool(self.action_mask()[action])
        reward = 0.0
        restored = 0
        if action > 0 and legal:
            wire, outage = slots[action - 1]
            if self.repairs >= self.repair.repair_budget:
                legal = False
            else:
                self.world.repair_wire(wire.id)
                self._impact_cache = None
                self.repairs += 1
                restored = outage
                if outage == 0:
                    self.wasted_repairs += 1
                reward = (
                    outage * self.repair.restoration_reward
                    - self.repair.repair_cost
                )
                if outage == 0:
                    reward -= self.repair.wasted_penalty
        for _ in range(self.repair.decision_interval):
            next_tick = self.world.state.tick + 1
            while (
                self._fault_index < len(self.fault_schedule)
                and self.fault_schedule[self._fault_index][0] == next_tick
            ):
                _, wire_id = self.fault_schedule[self._fault_index]
                self.world.fail_wire(wire_id)
                self._impact_cache = None
                self._fault_index += 1
            self.world.tick()
        self.total_reward += reward
        self.steps += 1
        self.last_action = self.ACTION_NAMES[action]
        self.last_reward = reward
        info = self._info()
        info["illegal"] = not legal
        info["restored"] = restored
        return self._observation(), reward, self.world.done, False, info

    def _observation(self) -> np.ndarray:
        slots = self._slots()
        consumers = max(1, len(self._consumers()))
        state = self.world.state
        budget = max(1, self.repair.repair_budget)
        outages = [outage for _, outage in slots]
        values: list[float] = [
            state.tick / self.repair.episode_ticks,
            state.score / 500.0,
            (self.repair.repair_budget - self.repairs) / budget,
            min(1.0, len(slots) / self.repair.max_slots),
            (max(outages) / consumers) if outages else 0.0,
            (sum(outages) / consumers) if outages else 0.0,
        ]
        for slot in range(self.repair.max_slots):
            if slot < len(slots):
                wire, outage = slots[slot]
                age = max(0, state.tick - self._failed_tick(wire))
                values.extend(
                    [
                        outage / consumers,
                        1.0 if outage > 0 else 0.0,
                        min(1.0, age / self.repair.episode_ticks),
                        1.0,
                    ]
                )
            else:
                values.extend([0.0, 0.0, 0.0, 0.0])
        return np.asarray(values, dtype=np.float32)

    def _failed_tick(self, wire: PowerWire) -> int:
        for event in reversed(self.world.state.events):
            if (
                event.kind == "power_wire_fault"
                and event.data.get("wire_id") == wire.id
            ):
                return event.tick
        return self.world.state.tick

    def _info(self) -> dict[str, Any]:
        slots = self._slots()
        outages = [outage for _, outage in slots]
        return {
            "score": self.world.state.score,
            "tick": self.world.state.tick,
            "budget_remaining": max(
                0, self.repair.repair_budget - self.repairs
            ),
            "failed_count": sum(
                1 for wire in self.world.state.power_wires if wire.failed
            ),
            "slot_ids": [wire.id for wire, _ in slots],
            "slot_outages": outages,
            "repairs": self.repairs,
            "wasted_repairs": self.wasted_repairs,
            "total_reward": self.total_reward,
            "last_action": self.last_action,
            "last_reward": self.last_reward,
            "fault_schedule": list(self.fault_schedule),
            "success": self.world.state.score >= self.repair.success_score,
        }
