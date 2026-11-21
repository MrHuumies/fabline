# Glossary

**Adapter** — A pure function that derives an observation, label, reward, or
split from canonical state or an episode. Adapters do not mutate the world.

**Benchmark** — A frozen set of tasks, splits, seeds, baselines, and metrics with
a version. Results are comparable only within a benchmark version.

**Canonical state** — The single source of truth for the world at a tick:
entities, tiles, inventories, events, metrics, and RNG state.

**Compositional split** — A split where test tasks require combinations of
mechanics or views not seen together in training.

**Decision interval** — The number of world ticks between agent actions in a
control task.

**Demonstration** — A recorded trajectory with actions and outcomes, from a
scripted, optimal, or human agent.

**Human demo** — A control-task demonstration recorded by the playable client:
observations, macro actions, rewards, state hashes, and a replay.

**Determinism** — Same seed, actions, config, and versions produce the same
state hash sequence.

**Entity** — A placed object in the factory: miner, belt, furnace, assembler,
depot. Entities have stable IDs.

**Fault** — A machine state in the opt-in fault mechanic: the entity stops
crafting for a repair window, then auto-repairs.

**FaultConfig** — Opt-in configuration for wear, threshold, downtime, and miner
wear. Disabled by default so `factory-v0.1` is unchanged.

**Wear** — The deterministic usage counter that triggers a fault at the
configured threshold.

**Sensor dynamics** — Canonical per-entity `temperature`, `vibration`, and
`acoustic` state in the opt-in fault mechanic. Temperature is a slow follower;
vibration and acoustic are decaying event impulses. The 0.2.0 views normalize
these to `[0, 1]`.

**Power grid** — The opt-in power mechanic. Pre-placed generators supply
capacity to entities within a Manhattan radius. Capacity is allocated by
generator id and then consumer id.

**Brownout** — An active entity whose power demand is not met. It stops work
and increments `brownout_ticks`; a new transition emits `power_brownout`.

**Activity-gated demand** — Power demand appears only while an entity is doing
work: belts while carrying, furnaces/assemblers while crafting, miners
continuously.

**Power priority** — The allocation order for a power tick: default entity-id
order, furnace-first, or assembler-first. Used by the power-allocation control
task.

**Fault + power interaction** — The control problem where faults remove demand
and repair re-enters it, so repair and reallocation compete under a tight power
budget.

**Load/capacity factor** — A seeded integer percentage applied to active power
demand or generator capacity. Schedules are generated at reset and stored in
canonical state; future factors are not observed.

**Episode** — One run of the world from reset to termination, with a seed and
version pins.

**Event** — A typed semantic record: build, item moved, craft completed, item
delivered, fault, etc.

**Ground truth** — Privileged information about the world: true latents, causal
structure, counterfactuals, sensor parameters. Not agent-visible by default.

**Harness** — The code that trains, evaluates, measures cost, and reports
results for a method.

**Materialized observation** — An array or table derived from a replay and
stored for training. A cache, not the source of truth.

**Mechanic** — A rule system in the world: mining, transport, crafting,
power, faults.

**Multi-view** — A set of named observation channels with a mask indicating
availability.

**Observation adapter** — A versioned, pure transformation from state to an
observation.

**Projection** — A task view over shared episodes: select a view, target,
split, and metrics without re-running the world.

**Replay** — Seed plus action log plus version pins. The smallest complete
record of an episode.

**Shared episode** — One passive rollout that records several views and targets;
offline tasks are projections over it.

**Split** — A named partition of episodes for training, validation, test, or a
shift condition.

**State hash** — A deterministic digest of the canonical state, used to validate
replays and detect unintended changes.

**Task** — A projection over episodes: observation(s), action, label/reward,
termination, split, metrics, and baselines.

**Task card** — A document describing a task's phenomenon, contract, splits,
metrics, baselines, and pitfalls.

**Tick** — One synchronous simulation step. The update order is fixed and
specified in [`world.md`](world.md).

**View** — A named observation channel, such as grid, vector, graph, pixels, or
text.

**World** — The simulation: mechanics, entities, generator, and transition
function. It does not know about ML.
