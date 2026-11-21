"""Wire-graph placement and connectivity for opt-in wired power.

Wires are orthogonal edges in a parallel infrastructure layer. They do not
occupy entity cells, so a wire can route past machines without blocking them.
Placement is a seeded randomized spanning tree over empty cells, followed by a
few loop edges so bridge faults and reroutes are both possible.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass

from .power import PowerConfig
from .state import Entity, PowerSource, PowerWire, TileType

Cell = tuple[int, int]


def _neighbors(x: int, y: int) -> tuple[Cell, ...]:
    return ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))


def _in_bounds(x: int, y: int, width: int, height: int) -> bool:
    return 0 <= x < width and 0 <= y < height


def _free_cell(
    cell: Cell,
    width: int,
    height: int,
    tiles: list[TileType],
    occupancy: dict[Cell, int],
    source_cells: set[Cell],
) -> bool:
    x, y = cell
    if not _in_bounds(x, y, width, height):
        return False
    if cell in occupancy or cell in source_cells:
        return False
    return tiles[y * width + x] is TileType.EMPTY


def _pick_terminal(
    cells: list[Cell],
    source: PowerSource,
    preferred_y: int,
) -> Cell:
    return min(
        cells,
        key=lambda cell: (
            abs(cell[0] - source.x) + abs(cell[1] - source.y),
            abs(cell[1] - preferred_y),
            cell[1],
            cell[0],
        ),
    )


def _candidate_band(
    width: int,
    height: int,
    tiles: list[TileType],
    occupancy: dict[Cell, int],
    source_cells: set[Cell],
    line_y: int,
    sources: list[PowerSource],
) -> set[Cell]:
    candidates: set[Cell] = set()
    for y in range(height):
        for x in range(width):
            cell = (x, y)
            if not _free_cell(cell, width, height, tiles, occupancy, source_cells):
                continue
            near_line = abs(y - line_y) <= 2
            near_source = any(
                abs(x - source.x) + abs(y - source.y) <= 2
                for source in sources
            )
            if near_line or near_source:
                candidates.add(cell)
    return candidates


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> bool:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return False
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1
        return True


def generate_wires(
    width: int,
    height: int,
    tiles: list[TileType],
    occupancy: dict[Cell, int],
    sources: list[PowerSource],
    entities: dict[int, Entity],
    power: PowerConfig,
    seed: int,
) -> list[PowerWire]:
    """Build a deterministic wire graph connecting the generator to consumers."""

    if power.topology != "wired":
        return []
    if len(sources) != 1:
        raise RuntimeError("wired topology currently requires one generator")
    source = sources[0]
    source_cells = {(source.x, source.y)}
    consumers = sorted(
        (
            entity
            for entity in entities.values()
            if power.demand(entity.type) > 0
        ),
        key=lambda entity: entity.id,
    )
    if not consumers:
        return []

    rng = random.Random(seed * 7919 + 31)

    def terminal_for(entity: Entity) -> Cell:
        options = [
            cell
            for cell in _neighbors(entity.x, entity.y)
            if _free_cell(
                cell, width, height, tiles, occupancy, source_cells
            )
        ]
        if not options:
            raise RuntimeError(
                f"no free cell adjacent to consumer {entity.id} for a wire"
            )
        return rng.choice(sorted(options))

    terminals = [terminal_for(entity) for entity in consumers]
    source_options = [
        cell
        for cell in _neighbors(source.x, source.y)
        if _free_cell(cell, width, height, tiles, occupancy, source_cells)
    ]
    if not source_options:
        raise RuntimeError("no free cell adjacent to the generator for a wire")
    source_terminal = rng.choice(sorted(source_options))
    terminals.append(source_terminal)

    # Use the full free grid. A narrow band makes the topology spatially
    # monotone, and a vector baseline with the fault position can solve the cut
    # without the graph.
    candidates = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if _free_cell(
            (x, y), width, height, tiles, occupancy, source_cells
        )
    }

    ordered = sorted(candidates)
    index = {cell: position for position, cell in enumerate(ordered)}
    if any(cell not in index for cell in terminals):
        raise RuntimeError("wire terminals are not on free cells")

    edges: list[tuple[Cell, Cell]] = []
    for x, y in ordered:
        for nx, ny in ((x + 1, y), (x, y + 1)):
            neighbor = (nx, ny)
            if neighbor in index:
                edges.append(((x, y), neighbor))
    rng.shuffle(edges)

    terminal_indices = {index[cell] for cell in terminals}
    union_find = _UnionFind(len(ordered))
    tree: list[tuple[Cell, Cell]] = []

    def terminals_connected() -> bool:
        roots = {union_find.find(item) for item in terminal_indices}
        return len(roots) == 1

    for left, right in edges:
        left_index = index[left]
        right_index = index[right]
        if not union_find.union(left_index, right_index):
            continue
        tree.append((left, right))
        if terminals_connected():
            break

    if not terminals_connected():
        raise RuntimeError("could not connect all wire terminals")

    # Kruskal can add edges in components that never join the terminals before
    # the stop condition. Keep only the component containing the generator.
    adjacency: dict[Cell, set[Cell]] = {}
    for left, right in tree:
        adjacency.setdefault(left, set()).add(right)
        adjacency.setdefault(right, set()).add(left)
    keep: set[Cell] = set()
    queue = deque([source_terminal])
    keep.add(source_terminal)
    while queue:
        cell = queue.popleft()
        for neighbor in adjacency.get(cell, ()):
            if neighbor not in keep:
                keep.add(neighbor)
                queue.append(neighbor)
    tree = [
        (left, right)
        for left, right in tree
        if left in keep and right in keep
    ]

    # Drop dead-end branches that do not lead to a terminal. What remains is
    # the minimal subtree connecting the generator and every consumer, so most
    # faults cut off at least one consumer.
    terminal_set = set(terminals)
    while True:
        degree: dict[Cell, int] = {}
        for left, right in tree:
            degree[left] = degree.get(left, 0) + 1
            degree[right] = degree.get(right, 0) + 1
        leaves = {
            cell
            for cell, count in degree.items()
            if count == 1 and cell not in terminal_set
        }
        if not leaves:
            break
        tree = [
            (left, right)
            for left, right in tree
            if left not in leaves and right not in leaves
        ]

    tree_cells = {cell for edge in tree for cell in edge}
    tree_set = {
        (min(left, right), max(left, right)) for left, right in tree
    }
    extras: list[tuple[Cell, Cell]] = []
    if power.wire_redundancy:
        spares = [
            edge
            for edge in edges
            if (min(edge[0], edge[1]), max(edge[0], edge[1])) not in tree_set
            and edge[0] in tree_cells
            and edge[1] in tree_cells
        ]
        rng.shuffle(spares)
        extras = spares[: power.wire_redundancy]

    wires: list[PowerWire] = []
    for left, right in [*tree, *extras]:
        first, second = sorted((left, right))
        wires.append(
            PowerWire(
                id=len(wires) + 1,
                ax=first[0],
                ay=first[1],
                bx=second[0],
                by=second[1],
            )
        )
    return wires


def wire_graph(
    wires: list[PowerWire],
    *,
    include_failed: bool = False,
) -> dict[Cell, set[Cell]]:
    graph: dict[Cell, set[Cell]] = {}
    for wire in wires:
        if wire.failed and not include_failed:
            continue
        left = (wire.ax, wire.ay)
        right = (wire.bx, wire.by)
        graph.setdefault(left, set()).add(right)
        graph.setdefault(right, set()).add(left)
    return graph


def reachable_cells(
    source: PowerSource,
    wires: list[PowerWire],
) -> set[Cell]:
    graph = wire_graph(wires)
    roots = [
        cell
        for cell in _neighbors(source.x, source.y)
        if cell in graph
    ]
    seen = set(roots)
    queue = deque(roots)
    while queue:
        cell = queue.popleft()
        for neighbor in graph.get(cell, ()):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def entity_terminal(
    entity: Entity,
    wires: list[PowerWire],
) -> Cell | None:
    """The single deterministic power inlet for a consumer.

    Adjacent redundant wires do not provide an alternate feed. This keeps the
    cascade label well defined: if the inlet cell is cut off, the consumer is
    disconnected even when another adjacent wire is still live.
    """

    cells = {
        cell
        for wire in wires
        for cell in ((wire.ax, wire.ay), (wire.bx, wire.by))
    }
    options = [
        cell for cell in _neighbors(entity.x, entity.y) if cell in cells
    ]
    return min(options) if options else None


def entity_connected(
    entity: Entity,
    reachable: set[Cell],
    wires: list[PowerWire],
) -> bool:
    terminal = entity_terminal(entity, wires)
    return terminal in reachable if terminal is not None else False


@dataclass(frozen=True)
class WireSummary:
    wire_count: int
    failed_wire_count: int
    component_count: int
    max_component_size: int
    node_count: int
    redundancy: int


def wire_summary(wires: list[PowerWire]) -> WireSummary:
    graph = wire_graph(wires, include_failed=False)
    nodes = set(graph)
    seen: set[Cell] = set()
    components: list[int] = []
    for node in sorted(nodes):
        if node in seen:
            continue
        size = 0
        queue = deque([node])
        seen.add(node)
        while queue:
            cell = queue.popleft()
            size += 1
            for neighbor in graph.get(cell, ()):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        components.append(size)
    edges = sum(len(neighbors) for neighbors in graph.values()) // 2
    redundancy = max(0, edges - len(nodes) + len(components))
    return WireSummary(
        wire_count=len(wires),
        failed_wire_count=sum(1 for wire in wires if wire.failed),
        component_count=len(components),
        max_component_size=max(components) if components else 0,
        node_count=len(nodes),
        redundancy=redundancy,
    )
