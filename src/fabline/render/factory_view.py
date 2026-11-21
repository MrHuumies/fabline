# mypy: ignore-errors
"""A read-only pygame view of factory state."""

from __future__ import annotations

from typing import Any

import pygame

from fabline.worlds.factory.config import FactoryConfig
from fabline.worlds.factory.faults import FaultConfig
from fabline.worlds.factory.power import PowerConfig
from fabline.worlds.factory.state import (
    EntityType,
    Item,
    TileType,
    WorldState,
)

BACKGROUND = (18, 20, 26)
PANEL = (24, 27, 35)
GRID_LINE = (42, 46, 56)
TEXT = (232, 236, 244)
MUTED = (150, 158, 174)
ACCENT = (240, 196, 80)
GOOD = (100, 210, 140)
BAD = (230, 100, 90)

TILE_COLORS = {
    TileType.EMPTY: (31, 35, 43),
    TileType.ROCK: (82, 88, 100),
    TileType.ORE: (120, 82, 42),
    TileType.DEPOT: (40, 78, 140),
}
ENTITY_COLORS = {
    EntityType.MINER: (220, 188, 68),
    EntityType.BELT: (76, 158, 102),
    EntityType.FURNACE: (190, 98, 72),
    EntityType.ASSEMBLER: (148, 106, 206),
    EntityType.DEPOT: (70, 128, 220),
}
ITEM_COLORS = {
    Item.ORE: (230, 150, 70),
    Item.INGOT: (200, 210, 225),
    Item.GEAR: (90, 220, 210),
}


class FactoryView:
    """Draws a factory state and a telemetry panel. Never mutates the state."""

    def __init__(
        self,
        config: FactoryConfig,
        tile_size: int | None = None,
        panel_width: int = 310,
        faults: FaultConfig | None = None,
        power: PowerConfig | None = None,
    ) -> None:
        pygame.font.init()
        self.config = config
        self.faults = faults or FaultConfig()
        self.power = power or PowerConfig()
        self.tile = tile_size or max(16, min(48, 800 // max(config.width, config.height)))
        self.grid_width = config.width * self.tile
        self.grid_height = config.height * self.tile
        self.panel_width = panel_width
        self.width = self.grid_width + self.panel_width
        self.height = max(self.grid_height + 40, 480)
        self.surface = pygame.Surface((self.width, self.height))
        self.font = pygame.font.Font(None, 23)
        self.small = pygame.font.Font(None, 18)
        self.tiny = pygame.font.Font(None, 15)

    def render(
        self,
        state: WorldState,
        info: dict[str, Any] | None = None,
    ) -> pygame.Surface:
        info = info or {}
        self.surface.fill(BACKGROUND)
        self._draw_tiles(state)
        self._draw_power_sources(state)
        self._draw_path(state, info)
        self._draw_entities(state)
        self._draw_panel(state, info)
        return self.surface

    def _cell_rect(self, x: int, y: int) -> pygame.Rect:
        return pygame.Rect(
            x * self.tile,
            y * self.tile,
            self.tile,
            self.tile,
        )

    def _draw_tiles(self, state: WorldState) -> None:
        for y in range(state.height):
            for x in range(state.width):
                rect = self._cell_rect(x, y)
                tile = state.tile_at(x, y)
                pygame.draw.rect(self.surface, TILE_COLORS[tile], rect)
                pygame.draw.rect(self.surface, GRID_LINE, rect, 1)
                if tile is TileType.ORE:
                    for offset in (-4, 0, 4):
                        pygame.draw.circle(
                            self.surface,
                            (210, 140, 70),
                            (rect.centerx + offset, rect.centery + offset // 2),
                            max(2, self.tile // 12),
                        )
                elif tile is TileType.ROCK:
                    pygame.draw.polygon(
                        self.surface,
                        (105, 112, 126),
                        [
                            (rect.left + 5, rect.bottom - 5),
                            (rect.centerx, rect.top + 4),
                            (rect.right - 4, rect.bottom - 6),
                        ],
                    )

    def _draw_power_sources(self, state: WorldState) -> None:
        if not self.power.enabled:
            return
        for source in state.power_sources:
            rect = self._cell_rect(source.x, source.y)
            center = rect.center
            radius = max(4, self.tile // 3)
            pygame.draw.circle(self.surface, (38, 92, 132), center, radius, 2)
            pygame.draw.line(
                self.surface,
                ACCENT,
                (center[0] - 3, center[1] - radius + 2),
                (center[0] + 2, center[1]),
                2,
            )
            pygame.draw.line(
                self.surface,
                ACCENT,
                (center[0] + 2, center[1]),
                (center[0] - 1, center[1] + radius - 2),
                2,
            )
            label = self.tiny.render("PWR", True, ACCENT)
            self.surface.blit(
                label,
                (source.x * self.tile + 2, source.y * self.tile + 2),
            )

    def _draw_path(self, state: WorldState, info: dict[str, Any]) -> None:
        path = info.get("path")
        if not path:
            return
        index = int(info.get("path_index", 0))
        for position in path:
            x, y = position
            if state.in_bounds(x, y):
                pygame.draw.rect(
                    self.surface,
                    (70, 90, 115),
                    self._cell_rect(x, y),
                    1,
                )
        if index < len(path):
            x, y = path[index]
            pygame.draw.rect(
                self.surface,
                ACCENT,
                self._cell_rect(x, y),
                3,
            )
            label = self.tiny.render("NEXT", True, ACCENT)
            self.surface.blit(label, (x * self.tile + 2, y * self.tile + 2))

    def _draw_entities(self, state: WorldState) -> None:
        for entity in sorted(state.entities.values(), key=lambda item: item.id):
            rect = self._cell_rect(entity.x, entity.y).inflate(-5, -5)
            color = ENTITY_COLORS[entity.type]
            pygame.draw.rect(self.surface, color, rect, border_radius=3)
            pygame.draw.rect(self.surface, (12, 14, 18), rect, 1, border_radius=3)

            dx, dy = entity.direction.delta
            center = rect.center
            pygame.draw.line(
                self.surface,
                (17, 20, 24),
                center,
                (
                    center[0] + dx * (self.tile // 3),
                    center[1] + dy * (self.tile // 3),
                ),
                2,
            )
            if entity.type is EntityType.MINER:
                pygame.draw.circle(self.surface, (60, 50, 20), center, max(2, self.tile // 8))
            elif entity.type is EntityType.BELT:
                pygame.draw.circle(self.surface, (25, 70, 45), center, max(2, self.tile // 8))
            elif entity.type is EntityType.FURNACE:
                pygame.draw.rect(
                    self.surface,
                    (100, 42, 34),
                    pygame.Rect(
                        rect.centerx - self.tile // 8,
                        rect.centery - self.tile // 8,
                        self.tile // 4,
                        self.tile // 4,
                    ),
                )
            elif entity.type is EntityType.ASSEMBLER:
                pygame.draw.polygon(
                    self.surface,
                    (70, 45, 100),
                    [
                        (rect.centerx, rect.top + 5),
                        (rect.right - 5, rect.centery),
                        (rect.centerx, rect.bottom - 5),
                        (rect.left + 5, rect.centery),
                    ],
                )

            if entity.faulted:
                pygame.draw.rect(
                    self.surface,
                    BAD,
                    self._cell_rect(entity.x, entity.y),
                    3,
                    border_radius=3,
                )
                label = self.tiny.render("FAULT", True, BAD)
                self.surface.blit(
                    label,
                    (entity.x * self.tile + 2, entity.y * self.tile + 2),
                )
            elif (
                self.power.enabled
                and self.power.active_demand(entity) > 0
                and not entity.powered
            ):
                pygame.draw.rect(
                    self.surface,
                    ACCENT,
                    self._cell_rect(entity.x, entity.y),
                    3,
                    border_radius=3,
                )
                label = self.tiny.render("NO PWR", True, ACCENT)
                self.surface.blit(
                    label,
                    (entity.x * self.tile + 2, entity.y * self.tile + 2),
                )
            elif entity.wear and self.faults.enabled:
                ratio = min(1.0, entity.wear / max(1, self.faults.fault_threshold))
                wear_rect = pygame.Rect(
                    rect.left + 2,
                    rect.top + 2,
                    int((rect.width - 4) * ratio),
                    2,
                )
                pygame.draw.rect(self.surface, ACCENT, wear_rect)

            self._draw_buffers(entity, rect)
            if entity.craft_progress > 0:
                progress = min(
                    1.0,
                    entity.craft_progress / max(1, self._craft_ticks(entity)),
                )
                bar = pygame.Rect(
                    rect.left + 2,
                    rect.bottom - 4,
                    int((rect.width - 4) * progress),
                    2,
                )
                pygame.draw.rect(self.surface, ACCENT, bar)

    def _draw_buffers(self, entity, rect: pygame.Rect) -> None:
        items: list[tuple[Item, int]] = []
        items.extend((item, count) for item, count in entity.input_buffer.items() if count)
        items.extend((item, count) for item, count in entity.output_buffer.items() if count)
        total = sum(count for _, count in items)
        if total == 0:
            return
        dots = min(total, 4)
        for index in range(dots):
            item = items[min(index, len(items) - 1)][0]
            pygame.draw.circle(
                self.surface,
                ITEM_COLORS[item],
                (
                    rect.left + 5 + index * 5,
                    rect.bottom - 6,
                ),
                2,
            )

    def _craft_ticks(self, entity) -> int:
        if entity.type is EntityType.FURNACE:
            return self.config.furnace_ticks
        if entity.type is EntityType.ASSEMBLER:
            return self.config.assembler_ticks
        return 1

    def _draw_panel(self, state: WorldState, info: dict[str, Any]) -> None:
        panel = pygame.Rect(self.grid_width, 0, self.panel_width, self.height)
        pygame.draw.rect(self.surface, PANEL, panel)
        pygame.draw.line(
            self.surface,
            GRID_LINE,
            (self.grid_width, 0),
            (self.grid_width, self.height),
            2,
        )

        x = self.grid_width + 14
        y = 14

        def line(text: str, color=TEXT, small=False, gap=4) -> None:
            nonlocal y
            font = self.small if small else self.font
            rendered = font.render(text, True, color)
            self.surface.blit(rendered, (x, y))
            y += rendered.get_height() + gap

        line("FABLINE", ACCENT)
        line(f"tick {state.tick}   score {state.score}", TEXT)
        line(
            f"ingots {state.delivered[Item.INGOT]}   gears {state.delivered[Item.GEAR]}",
            MUTED,
            small=True,
        )
        counts = {kind: 0 for kind in EntityType}
        for entity in state.entities.values():
            counts[entity.type] += 1
        line(
            "entities  "
            f"miner {counts[EntityType.MINER]}  belt {counts[EntityType.BELT]}  "
            f"furnace {counts[EntityType.FURNACE]}  asm {counts[EntityType.ASSEMBLER]}",
            MUTED,
            small=True,
        )

        blocked = sorted(
            (entity for entity in state.entities.values() if entity.blocked_ticks),
            key=lambda entity: entity.blocked_ticks,
            reverse=True,
        )[:3]
        if blocked:
            summary = ", ".join(
                f"{entity.type.name.lower()} {entity.blocked_ticks}" for entity in blocked
            )
            line(f"blocked: {summary}", BAD, small=True)
        else:
            line("blocked: none", GOOD, small=True)

        faulted = [entity for entity in state.entities.values() if entity.faulted]
        if faulted:
            summary = ", ".join(
                f"{entity.type.name.lower()} {entity.id}" for entity in faulted
            )
            line(f"faulted: {summary}", BAD, small=True)
        elif self.faults.enabled:
            line("faulted: none", GOOD, small=True)

        if self.power.enabled:
            active = [
                entity
                for entity in state.entities.values()
                if self.power.active_demand(entity) > 0 and not entity.faulted
            ]
            powered = sum(1 for entity in active if entity.powered)
            capacity = sum(source.capacity for source in state.power_sources)
            demand = sum(self.power.active_demand(entity) for entity in active)
            line(
                f"power: {powered}/{len(active)}  cap {capacity}  load {demand}",
                GOOD if powered == len(active) else ACCENT,
                small=True,
            )
            if powered < len(active):
                line(f"browned out: {len(active) - powered}", BAD, small=True)

        if info.get("mode") == "control":
            line("", TEXT)
            line(f"path {info.get('path_index', 0)}/6", ACCENT, small=True)
            if info.get("last_action") is not None:
                line(f"action: {info['last_action']}", TEXT, small=True)
            if info.get("reward") is not None:
                line(f"reward: {float(info['reward']):+.2f}", MUTED, small=True)
            if info.get("success"):
                line("SUCCESS", GOOD, small=True)
        if info.get("paused"):
            line("PAUSED", ACCENT, small=True)
        if info.get("message"):
            line(str(info["message"]), GOOD, small=True)

        y += 6
        line("Events", MUTED, small=True)
        for event in state.events[-7:]:
            detail = ""
            if "item" in event.data:
                detail = f" {event.data['item']}"
            elif "type" in event.data:
                detail = f" {event.data['type']}"
            line(f"{event.tick:>4} {event.kind}{detail}", TEXT, small=True, gap=1)

        y = self.height - 76
        line("Space pause   N step   +/- speed", MUTED, small=True, gap=1)
        line("R reset   Esc quit", MUTED, small=True, gap=1)
        if info.get("mode") == "control":
            line("0 noop  1 miner  2 belt  3 furnace  4 asm  5 remove", MUTED, small=True, gap=1)
            line("S save demo", ACCENT, small=True, gap=1)


def render_frame(
    state: WorldState,
    config: FactoryConfig,
    info: dict[str, Any] | None = None,
    faults: FaultConfig | None = None,
) -> pygame.Surface:
    return FactoryView(config, faults=faults).render(state, info)
