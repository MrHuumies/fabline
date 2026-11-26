# The factory world

This document specifies the first world: a small, deterministic factory. It is
the content behind the testbed contracts in [`interface.md`](interface.md).

## Fantasy and scope

You are an engineer expanding a working factory. Ore arrives from patches,
belts move it, furnaces smelt it, assemblers turn ingots into gears, and a depot
scores the output. The factory must keep producing while you add, remove, or
reroute machines.

The research version is a controlled grid world. It is not a full automation
game. The MVP deliberately excludes fluids, trains, full power networks, and
combat.

## MVP defaults

These are starting values, not sacred constants. They live in a typed config.

| Parameter | Default | Notes |
|---|---:|---|
| Grid | 32 × 32 | Configurable; procedural layouts |
| Tick rate | 20 ticks/s | Rendering throttle; headless runs faster |
| Episode length | 2000 ticks | 100 decision intervals at 20 ticks |
| Decision interval | 10 ticks | For control tasks |
| Entity budget | 64 | Research mode; no resource cost |
| Belt capacity | 1 item/tile | Simple, legible backpressure |
| Miner rate | 1 ore / 4 ticks | While on an ore tile |
| Furnace recipe | 1 ore → 1 ingot / 8 ticks | Input buffer 4, output 2 |
| Assembler recipe | 2 ingots → 1 gear / 12 ticks | Input buffer 6, output 2 |
| Depot score | 2 / ingot, 10 / gear | Configurable per task |

## Tiles

- `empty` — buildable.
- `rock` — impassable, not buildable.
- `ore` — resource patch; a miner can be placed on it.
- `depot` — fixed sink; delivers score.

## Entities

| Entity | Footprint | Inputs | Outputs | Behavior |
|---|---|---|---|---|
| `miner` | 1 tile on ore | none | ore | Produces ore on a fixed cadence into a 1-item output buffer |
| `belt` | 1 tile | any item | same item | Moves one item one tile per tick in its direction |
| `furnace` | 1 tile | ore | ingot | Crafts on a timer; buffers inputs and outputs |
| `assembler` | 1 tile | ingots | gear | Crafts on a timer; buffers inputs and outputs |
| `depot` | fixed tile | ingot, gear | score | Consumes delivered items and increments score |

Later entities (deferred): power pole, chest, splitter, underground belt, train,
fluid pipe, repair bot. Generators are pre-placed infrastructure in the current
power mechanic, not entities.

## Items

- `ore` — raw.
- `ingot` — smelted.
- `gear` — assembled; the main score item.

Items are discrete. A belt tile holds at most one item. A machine buffer holds a
small count. There is no fluid or continuous flow in the MVP.

## Tick model

The update order is fixed and deterministic:

1. **Tick start.** Increment `tick`. Clear per-tick intents.
2. **Machines.** Each machine consumes inputs and advances its craft timer.
   Completed crafts place outputs in the output buffer. Miners produce ore on
   their cadence.
3. **Logistics.** Collect push intents from miners, machines, and belts. Resolve
   conflicts deterministically (see below). Apply moves simultaneously.
4. **Delivery and metrics.** Depots consume delivered items, update score and
   production counters. Emit events. Update rolling metrics.
5. **Termination check.** End the episode on the tick limit or a task-specific
   condition.

No system may mutate the grid outside its phase. No observation adapter may
advance time.

### Push model

Every producer attempts to push one item into the tile it faces:

- a miner faces its output direction;
- a machine faces its output direction;
- a belt faces its direction and pushes the item it holds.

A receiver accepts if:

- it is a belt with no item;
- it is a machine with a valid input and buffer space;
- it is a depot that accepts the item.

If multiple producers target the same tile in the same tick, the producer with
the lowest stable entity ID wins; the others keep their item and record a
`blocked` event. This is deterministic and easy to test.

Belt moves are computed from the pre-tick state and applied simultaneously. An
item moves at most one tile per tick. A belt cannot push into a tile that was
occupied at the start of the tick, even if that tile is vacated in the same
tick. This avoids chain-shift ambiguity.

### Crafting

A machine starts a craft only when:

- it has the required inputs;
- its output buffer has space;
- it is idle.

Inputs are consumed at craft start. The craft completes after `craft_ticks`.
The output is placed in the output buffer at completion. A machine with a full
output buffer does not start a new craft.

## Build and remove

Control tasks use a typed action:

```text
build(entity_type, x, y, direction)
remove(x, y)
rotate(x, y)
noop()
```

Rules:

- build only on `empty` or `ore` tiles, subject to entity rules;
- a miner requires an `ore` tile;
- a belt, furnace, or assembler requires `empty`;
- remove only player-built entities, not the depot or rock;
- rotate only entities with a direction;
- no two entities on one tile;
- research mode has no resource cost, only an entity budget;
- game mode may add costs later; it must not change benchmark behavior.

Illegal actions are rejected with a typed error and do not change state.

## Procedural generation

A seed determines:

- rock obstacles;
- ore patches (clusters, not isolated tiles);
- depot position;
- optional starter line for control tasks;
- task-specific constraints (e.g., minimum ore count, reachable depot).

The generator must be deterministic and reject layouts that violate the task's
feasibility constraints. It returns the seed, the layout, and a generation
version.

## Ground truth

The world records, per tick or per event:

- production and delivery counts by item;
- per-entity utilization, blocked ticks, and buffer levels;
- item flow edges (source → destination);
- machine craft state;
- power: generator capacity, demand, powered state, and brownout events;
- fault wear and repair events (opt-in);
- a causal bottleneck label for benchmark tasks (counterfactual removal effect).

Events are semantic and typed:

```text
build, remove, rotate
item_spawned, item_moved, item_blocked
craft_started, craft_completed
item_delivered
fault_started, fault_repaired   (opt-in)
power_brownout, power_restored  (opt-in)
```

The event log is ground truth for probes, analysis, and replay validation. It is
not part of the agent-visible observation unless a task explicitly derives a view
from it.

## Observation views

The same state can be viewed as:

- **grid** — tile and entity channels;
- **entities/graph** — typed entity records plus flow edges;
- **vector** — aggregate production, inventory, and utilization;
- **power** — aggregate grid capacity, load, powered ratio, and brownouts;
- **power_grid** — spatial supply coverage, demand, and powered state;
- **pixels** — optional RGB render for vision tasks;
- **text** — optional templated description for language tasks;
- **multi-view** — a named set of the above with a mask.

Exact shapes and versions are in [`interface.md`](interface.md).

## Task hooks

The MVP supports these task shapes:

- **supervised** — predict throughput, bottleneck, or next state from a state;
- **self-supervised** — predict or reconstruct masked state;
- **control** — build/remove/rotate to maximize delivered gears;
- **imitation** — clone a scripted builder;
- **planning** — find a build order for a target output;
- **causal** — estimate the effect of an intervention.

Task definitions live outside the world. The world only provides state,
transitions, and ground truth.

## Faults (opt-in)

Faults are disabled by default so `factory-v0.1` behavior and hashes stay
unchanged. A separate `FaultConfig` enables:

- wear gained on each completed furnace/assembler craft;
- a fault at `fault_threshold` wear;
- a repair downtime of `repair_ticks`, after which the machine auto-repairs;
- optional miner wear;
- `sensors` and `diagnostics` observation views.

Sensor dynamics (`0.2.0`):

- each entity carries `temperature`, `vibration`, and `acoustic` in `[0, 100]`;
- temperature is a slow first-order follower of wear, crafting, and fault state;
- vibration decays and receives an impulse when a craft starts or a miner
  produces ore;
- acoustic decays and receives an impulse when an item is blocked or a fault
  starts;
- the channels are updated once per tick before machine work, and only when
  faults are enabled;
- the sensor fields are included in the entity hash only when nonzero, so
  fault-free hashes stay identical to `factory-v0.1`.

Fault rules:

- a faulted machine keeps its buffers but does not start or advance crafts;
- repair progress increments each tick; at completion, wear resets and the
  machine resumes the next tick;
- belts and depots do not fault in this pass;
- fault events are `fault_started` and `fault_repaired`;
- auto-repair is the baseline; a faulted entity can also be repaired explicitly
  with the `repair(x, y)` grid action, which clears fault, progress, and wear;
- the two-action fault-recovery environment spends a repair action for a small
  reward penalty.

Fault-free entity hashes are identical to `factory-v0.1`. Fault replays include
the fault config and must restore it before reset.

## Power (opt-in)

Power is disabled by default so `factory-v0.1` behavior and hashes stay
unchanged. A separate `PowerConfig` enables:

- pre-placed generators stored as canonical infrastructure state, not entities;
- Manhattan-radius distribution with deterministic generator-id and consumer-id
  allocation;
- per-entity powered and brownout state;
- `power` and `power_grid` observation views.

Demand is activity-gated:

- miner: 2 continuously;
- belt: 1 while carrying an item;
- furnace: 3 while crafting;
- assembler: 4 while crafting;
- depot: 0.

Stochastic variation (opt-in):

- `load_jitter`, `capacity_jitter`, and `variation_period` generate a seeded
  piecewise-constant schedule at reset;
- factors are integer percentages stored in canonical state;
- active demand and generator capacity are scaled by the current factors;
- future factors are not exposed in observations, so prediction is genuinely
  uncertain;
- jitter 0 keeps the deterministic power behavior and hashes.

Rules:

- idle machines draw 0 and are ready to start; demand appears on the next power
  tick, so starting a craft can trigger a brownout;
- faulted machines demand 0 and are offline; a fault can free capacity for
  others;
- unpowered miners do not produce, unpowered machines do not advance crafts,
  and unpowered belts do not move items;
- `brownout_ticks` increments while an active entity is unpowered;
- transitions emit `power_brownout` and `power_restored`;
- generators are included in the state hash only when the list is non-empty;
  powered/brownout fields are included only when nonzero, so power-free hashes
  stay identical to `factory-v0.1`.

Allocation control (`factory.power.allocate.v1`) sets a priority each decision
interval: default entity-id order, furnace-first, or assembler-first. Under a
tight budget the agent must alternate between building ingots and assembling
gears.

Buildable generators, wires, fuel, and batteries are deferred.

## Production tree (opt-in)

Production is disabled by default; the frozen single-gear recipe is unchanged.
A separate `ProductionConfig` enables a small multi-item tree:

```text
ORE -> INGOT
INGOT -> GEAR              (assembler recipe 0, existing)
INGOT -> COMPONENT         (assembler recipe 1)
INGOT + COMPONENT -> GEAR  (assembler recipe 2, assembly edge)
```

Rules:

- `Entity.recipe` is per assembler (0 gear, 1 component, 2 assembly); it is
  included in the state hash only when nonzero, so default hashes stay
  identical;
- component is a logistics item carried by belts and accepted by depots when
  production is enabled;
- an assembler accepts component whenever the assembly tree is enabled, so the
  input buffer can hold component while the assembler runs direct gear;
- assembly consumes one ingot and one component and outputs **two gears** in the
  public assembly task (task-specific economics: component 24 ticks, assembly
  16 ticks);
- the linear starter line sends component toward the depot, so the assembly
  control task uses a fixed two-feed assembly cell
  (`worlds/factory/assembly.py`).

See RFC 0031 and the assembly-edge task card.

## Deferred mechanics

Do not add these before the MVP is measured:

- stochastic faults and sensor noise;
- multi-tick repair, repair budgets, and entity choice;
- fluids and pipes;
- trains and long-distance logistics;
- splitters and underground belts;
- circuits and programmable logic;
- combat, enemies, and destruction;
- multi-agent workers;
- 3D rendering.

Each is a legitimate future mechanic. Each needs an RFC, tests, observation
changes, and a data-impact note.

## Invariants

- Items are conserved except at miners (sources) and depots (sinks).
- A belt tile holds at most one item.
- No two entities occupy one tile.
- No two power sources occupy one tile, and no source overlaps an entity.
- A machine never crafts without inputs or with a full output buffer.
- Entity IDs are stable and unique.
- The depot and rock are never removed.
- Every action either succeeds or returns a typed error; no partial mutation.
- All randomness comes from the supplied seeded generator.
- The same seed and action log produce the same state hash.
- The renderer never advances or mutates the world.

## Why this world

- **Factored state** — entities, tiles, inventories, and flows are explicit.
- **Graph structure** — production is a directed graph, not a flat vector.
- **Causal transparency** — recipes and flows are known; interventions are
  meaningful.
- **Procedural content** — layouts and seeds give held-out distributions.
- **Cheap simulation** — tick-based, no physics, high throughput.
- **Measurable outcomes** — throughput, uptime, cost, and bottlenecks are
  objective.
- **Visual satisfaction** — belts and flows are legible and fun to watch.
- **Task breadth** — one world supports prediction, control, planning, and
  causal tasks.
