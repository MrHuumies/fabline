# Interface contracts

This document defines the contracts between the world, observations, actions,
tasks, data, and evaluation. It is the most important document in the repo. If a
change breaks one of these contracts, it needs an ADR and a version bump.

## Principles

1. **One canonical state.** The world emits a single factored state and an event
   log. Everything else is derived.
2. **Pure adapters.** Observation and task adapters do not mutate the world.
3. **Explicit versions.** World, observation, action, task, dataset, benchmark,
   and baseline versions are recorded with every result.
4. **Replay first.** A seed plus an action log is the smallest complete record.
   Materialized observations are a cache, not the source of truth.
5. **Ground truth is separate.** Agent-visible observations and privileged
   labels live in different fields.
6. **Missing data is explicit.** View masks, availability, noise, delay, and
   failure are part of the observation spec.

## Canonical state

The conceptual schema:

```text
WorldState
  tick: int
  seed: int
  grid: Tile[H, W]
  entities: Entity[]
  power_sources: PowerSource[]  # power-enabled only
  power_priority: int            # 0 default, 1 furnace, 2 assembler
  power_load_factors: int[]      # stochastic power only
  power_capacity_factors: int[]  # stochastic power only
  inventories: map[item, int]
  score: int
  events: Event[]            # current tick or ring buffer
  metrics: Metrics           # rolling production, utilization
  rng_state: ...             # serialized, for exact resume
  world_version: str
```

An entity:

```text
Entity
  id: int                    # stable, never reused
  type: enum                 # miner, belt, furnace, assembler, depot
  x: int
  y: int
  direction: enum            # N, E, S, W
  recipe: str | null
  input_buffer: map[item, int]
  output_buffer: map[item, int]
  craft_progress: int
  blocked_ticks: int
  built_tick: int
  wear: int                  # fault-enabled only
  faulted: bool              # fault-enabled only
  repair_progress: int       # fault-enabled only
  temperature: int           # [0, 100], fault-enabled only
  vibration: int             # [0, 100], fault-enabled only
  acoustic: int              # [0, 100], fault-enabled only
  powered: bool              # power-enabled only
  brownout_ticks: int        # power-enabled only
```

A power source:

```text
PowerSource
  id: int
  x: int
  y: int
  capacity: int              # per-tick capacity
```

Power sources are infrastructure, not entities; they are included in the hash
only when the list is non-empty.

The exact serialization (JSON, MessagePack, or a columnar layout) is an
implementation detail. The fields and semantics are the contract.

## Observation adapters

Each adapter has a spec:

```text
ObservationSpec
  name: str                  # e.g. "grid", "vector", "entities"
  version: str               # semver
  shape: tuple | null        # null for variable-size graph views
  dtype: str
  normalized: bool
  format: str                # "tensor" or "graph"
  rate: int                  # ticks between observations, 1 = every tick
  noise: NoiseSpec | null
  delay: int                 # ticks
  mask: bool                 # whether a mask is emitted
  cost: CostSpec             # encoder cost estimate
```

### `grid.v1`

A dense array `(H, W, C)` with channels:

- tile type (empty, rock, ore, depot);
- entity type (none, miner, belt, furnace, assembler);
- direction (one-hot or scalar);
- input buffer fill;
- output buffer fill;
- craft progress.

Normalization is documented per channel. Shapes are fixed for a given world
size.

### `entities.v1`

A variable-length list of entity records plus a directed edge list:

```text
entities: [{id, type, x, y, direction, recipe, input, output, progress, ...}]
edges: [{src, dst, kind}]   # flow, adjacency, or dependency
```

This view is intended for GNNs, transformers, and relational baselines. Padding
and batching are the harness's responsibility, not the world's.

The M2 implementation returns a `GraphObservation` with `entity_features`,
`entity_mask`, and `adjacency`. Tabular baselines consume a flattened vector via
`EntitiesObservation.flatten`; a GNN consumes the three arrays directly.

### `vector.v1`

A fixed-size aggregate vector:

- tick, score, entity counts by type;
- inventory by item;
- production and delivery rates over a window;
- per-entity-type utilization and blocked rates;
- optional task-specific aggregates.

The exact order and normalization are versioned.

### `sensors.v2` and `diagnostics.v2`

Fault-aware diagnostic views, available when `FaultConfig.enabled` is true:

- `sensors`: `(H, W, 5)` — wear, temperature, vibration, acoustic, faulted;
- `diagnostics`: 13 aggregate features — fault count, mean/max wear,
  temperature, vibration, acoustic, machine count, blocked ticks.

The sensor channels are canonical state with temporal dynamics: temperature is
a slow follower, vibration is a work-start transient, and acoustic is a
blockage/fault transient. All values are normalized to `[0, 1]` in the views.

Fault-free worlds emit zeros for these views and keep the frozen entity hash
format; the standard vector/grid/entity views do not include explicit fault
state.

### `entity_sensors_top4.v1`

A fault-aware per-entity view: the top four entities by acoustic level, sorted
by `(acoustic desc, entity id asc)`, each with 8 features:

```text
mask, acoustic, vibration, temperature, wear, faulted, crafting, type_norm
```

Shape `(4, 8)`, flattened to 32 features for tabular models. It exists to test
whether per-entity sensor state preserves onset signatures that aggregate
mean/max views dilute. Fault-free worlds emit zeros.

### `power.v1`

Power-aware aggregate view, available when `PowerConfig.enabled` is true:

- 12 features: tick, capacity, demand ratio, powered ratio, brownout ratio,
  mean brownout ticks, per-type powered ratios (miner/belt/furnace/assembler),
  headroom, source count.

Demand is activity-gated. Idle machines draw 0 and are considered powered.
With stochastic power, demand and capacity are scaled by the current integer
factors; future factors are not exposed.

### `fault_power.v1`

A control observation for fault + power interaction: the 12 `power.v1`
features, 6 line-buffer features, and 6 fault aggregates (faulted ratio, mean
and max wear, furnace/assembler faulted flags, mean repair progress). Shape
`(24,)`.

### `power_control.v1`

A control observation for power allocation: the 12 `power.v1` features plus
assembler input, furnace output, assembler/furnace craft progress, miner
output, and score. Shape `(18,)`.

### `power_grid.v1`

A `(H, W, 3)` spatial view: normalized generator coverage, normalized active
demand, and powered flag. Power-free worlds emit zeros.

### `pixels.v1`

An RGB frame rendered from the state. This is optional and generated offline.
The renderer must be deterministic for a given state and style version.

### `text.v1`

A templated textual description of the state. This is optional and intended for
language-model experiments. The template is versioned; it is not a free-form
narration.

### `multiview.v1`

A named dictionary of views plus a boolean mask:

```text
views: {grid: ..., vector: ..., text: ...}
view_mask: {grid: true, vector: true, text: false}
```

View dropout, arrival, and failure are represented by the mask. The base model
must be trained with masks if it is expected to handle missing views.

Implementation: `MultiviewObservation` returns a `MultiviewFrame` and supports
`observe(state, view_mask=...)`. `flatten` emits a fixed-width float32 vector;
inactive views are zeroed. The spec is `multiview`/`1.0.0`, with prefixed
feature names when every view shape is known. Named views can be registered with
`register_view`.

## Action adapters

### `grid_build.v2`

```text
Action
  op: enum          # build, remove, rotate, repair, noop
  entity: enum|null # miner, belt, furnace, assembler
  x: int|null
  y: int|null
  direction: enum|null
```

The action mask shape is `(5, 5, H, W, 4)` = (op, entity, y, x, direction).
`repair` is legal only on a faulted non-depot entity. Illegal actions return a
typed error and leave the state unchanged.

The frozen `factory-v0.1` benchmark is action-free; the version bump matters
only for action consumers.

### `macro.v1`

A fixed-length or variable-length sequence of `grid_build.v1` actions, applied
at a decision boundary. Intended for planning and imitation.

### `continuous.v1`

Reserved for later worlds. Not part of the factory MVP.

## Task adapters

```text
TaskSpec
  id: str                    # e.g. "factory.throughput.predict.v1"
  version: str
  world: str                 # world + version
  observation: ObservationSpec | list[ObservationSpec]
  action: ActionSpec | null  # null for offline supervised tasks
  label: LabelSpec | null
  reward: RewardSpec | null
  termination: TerminationSpec
  split: SplitSpec
  metrics: list[MetricSpec]
  baselines: list[BaselineSpec]
  card: path                 # task card
```

A task is a projection over episodes. The same episode can be used by several
tasks with different observation adapters, labels, and splits.

### `ViewArrivalTask`

A view-arrival task exposes:

```text
ViewArrivalSpec
  task_id: str
  task_version: str
  base_views: tuple[str, ...]
  new_view: str
  retention_views: tuple[str, ...]
  label: str

ViewArrivalData
  views: map[str, ndarray]
  view_mask: map[str, bool]
  labels: ndarray
  splits: ndarray
  episode_ids: ndarray
```

Splits are grouped by episode id; a row-level random split is rejected. The
task protocol is `spec` plus `load()`. Training and update methods are
consumer-side; the public package does not prescribe a model architecture or a
specific adaptation method.

## Episode schema

A logical episode:

```text
Episode
  id: str
  seed: int
  world_version: str
  task_version: str
  observation_version: str
  action_version: str
  split: str
  agent: str
  config_hash: str
  steps: Step[]
  events: Event[]
  metrics: map[str, float]
  cost: CostReport
```

A step:

```text
Step
  t: int
  views: map[str, Any]       # observation adapter outputs
  view_mask: map[str, bool]
  action: Any | null
  reward: float | null
  label: Any | null
  done: bool
  info: Info                 # privileged ground truth, not agent-visible
```

`info` may contain:

- true entity states and inventories;
- the causal bottleneck label;
- counterfactual outcomes;
- sensor noise parameters;
- event references.

Keeping `info` separate prevents label leakage and enables probes.

## Data products

1. **Replay** — seed + action log + version pins. Smallest complete record.
2. **Materialized observations** — arrays for training, Parquet/Zarr, generated
   from replays.
3. **Demonstrations** — scripted, optimal, or human trajectories with actions
   and outcomes.
4. **Annotations** — ground-truth latents, causal graphs, event labels,
   counterfactuals.

See [`dataset.md`](dataset.md) for formats and generation.

## Versioning

Use semver for each contract:

```text
world:      factory-0.1.0
observation: grid-0.1.0, vector-0.1.0, entities-0.1.0
action:      grid-build-0.1.0
task:        throughput-predict-0.1.0
dataset:     2026.11-factory-debug
benchmark:   factory-v0.1
```

Compatibility rules:

- **Patch** — bug fix, no schema change, replays remain valid.
- **Minor** — additive fields or new adapters; old consumers keep working.
- **Major** — schema or semantics change; old replays are not promised.

Every evaluation report pins all versions and the git commit. Benchmark tags are
immutable.

## Determinism and replay

- Fixed timestep and explicit update order.
- Seeded RNG; no global random calls.
- Stable entity IDs.
- Deterministic conflict resolution.
- State hash at every tick or at a configurable interval.
- Replay validation: same seed + action log + versions → same hash sequence.
- If a replay mismatches, fail loudly with the first divergent tick.

Floating-point caveats are documented per world. The factory MVP uses integer
arithmetic for items and ticks, which avoids most cross-platform drift.

## Non-goals

- A universal observation schema for every possible world.
- Serializing the entire state on every step for every dataset.
- Hiding missing data or label leakage behind defaults.
- Letting a task mutate the world outside the action contract.
