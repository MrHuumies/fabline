# Mechanic RFC 0001 — Opt-in machine faults

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-21
- **Related:** ADR 0011

## Summary

Machines accumulate wear as they craft. At a threshold they fault, stop
producing for a repair window, then auto-repair. The mechanic is opt-in and adds
diagnostic sensor channels: wear, temperature, vibration, acoustic, and fault
state.

## Motivation

The testbed needs new world complexity
that creates causal labels, new information channels, and control/retention
pressure. Faults fit the sensor/view-arrival line: thermal, vibration, and
acoustic channels can arrive as new views later.

## Rules

- `FaultConfig`:
  - `enabled` — default false;
  - `wear_per_craft` — wear added when a furnace/assembler completes a craft;
  - `miner_wear_per_ore` — optional miner wear;
  - `fault_threshold` — wear at which the machine faults;
  - `repair_ticks` — downtime before auto-repair.
- A faulted machine:
  - does not start or advance crafts;
  - keeps its buffers;
  - increments `repair_progress` each tick;
  - auto-repairs at `repair_ticks`, resets wear, and resumes the next tick.
- Wear is checked on craft completion (and on miner production if enabled).
- Fault events: `fault_started`, `fault_repaired`.
- Belts and depots do not fault in this pass.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| mining | optional miner wear | starvation if enabled |
| transport | belts keep moving; buffers can back up | faulted machine blocks its output |
| crafting | wear on completion; fault stops crafting | throughput loss, line starvation |
| depot scoring | fault windows reduce deliveries | score/label shifts |
| diagnostics | wear/temperature/vibration/acoustic derived | no new state for sensors |

## Observation impact

New views:

- `sensors`: H×W×5, channels wear, temperature, vibration, acoustic, faulted;
- `diagnostics`: 13 aggregate features including fault count, mean/max wear,
  temperature, vibration, acoustic, machine count, blocked ticks.

The default vector/grid/entity views are unchanged. Fault-free hashes are
unchanged.

## Action impact

No new action in this pass. Auto-repair only. A repair action is a separate RFC
because it changes the action contract and the control task.

## Data impact

- Fault replay files include the fault config.
- Fault datasets/tasks are opt-in and separate from `factory-v0.1`.
- The fault-prediction task records diagnostics vs standard vector views.
- Fault-free datasets are unchanged.

## Determinism

- No RNG: wear and repair are deterministic counters.
- Entity fault fields enter the canonical state hash only when nonzero.
- Fault replay validation restores the fault config before reset.
- Fault-free state hashes must match `factory-v0.1`; a regression test covers
  the known line hash.

## Tests

- Fault starts, stops crafting, auto-repairs, and resumes.
- Fault-free world has no fault events and unchanged hash.
- Sensor and diagnostics shapes, ranges, faulted channel.
- Fault-prediction labels and dataset/replay round-trip.
- Fault benchmark report and frozen benchmark regression.

## Performance

Fault logic adds a few integer operations per entity per tick. The factory perf
target is unaffected; the fault benchmark runs 40 episodes in about 20 seconds
on the development machine.

## Alternatives

- Always-on faults: rejected, breaks the frozen benchmark.
- Repair action in the first pass: deferred.
- Separate fault world: rejected; opt-in config keeps the same world.

## Open questions

- Should repair be a player/agent action with a cost?
- Should belts jam independently?
- Should faults be hidden and only inferable from sensors?
- How do faults interact with power and multi-agent workers?
