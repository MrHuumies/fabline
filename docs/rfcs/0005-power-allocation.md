# Mechanic RFC 0005 — Power allocation control

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-21
- **Related:** RFC 0004, ADR 0015

## Summary

Add a three-action power-allocation control environment. Under a generator
budget too small to run the furnace and assembler together, the agent chooses a
priority each decision interval: default id order, favor furnace, or favor
assembler. It must build ingot buffers and alternate priorities to produce
gears.

## Motivation

Phase 1 made the grid observational. The power mechanic's control half is
missing: when supply is tight, which load gets power? A fixed priority is not
enough because the gear line needs both the furnace and the assembler at
different times.

The existing line-building control task must stay unchanged. Power allocation
is a separate environment with its own observation, action, and success
contract.

## Rules

- `WorldState.power_priority` is canonical state:
  - `0` — default allocation by entity id;
  - `1` — furnaces first, then the rest by id;
  - `2` — assemblers first, then the rest by id.
- The priority is included in the state hash only when nonzero.
- `PowerAllocationEnv`:
  - fixed gear line, no faults;
  - generator count 1; capacity 5; radius 8;
  - episode 500 ticks; decision interval 10;
  - actions `default`, `favor_furnace`, `favor_assembler`;
  - reward = score delta over the interval;
  - success = final score ≥ 100.
- At capacity 5 the furnace and assembler cannot run together. The policy must
  alternate: run the furnace to build ingots, then the assembler to convert
  them to gears.
- The environment is online; it does not write a dataset or replay.

## Observation

`power_control.v1`, 18 features:

```text
power features (12)
assembler_input_norm, furnace_output_norm,
assembler_craft_norm, furnace_craft_norm,
miner_output_norm, score_norm
```

The first 12 are the phase-1 `power` view. The rest expose the line buffers and
craft state needed to time the switch.

## Baselines

- `default` — action 0 always.
- `favor_furnace` — action 1 always.
- `favor_assembler` — action 2 always.
- `alternate` — favor assembler while it is crafting or has ≥ 2 ingots, else
  favor furnace. A scripted oracle-style baseline.
- `random` — uniform over actions.
- `tabular_q` — Q-learning over assembler input, craft flags, furnace output,
  miner output, and tick bucket.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| power grid | priority changes allocation order | must not change phase-1 benchmark |
| crafting | furnace and assembler compete | buffers and timing matter |
| belts | unpowered belts stall the line | priority affects logistics indirectly |
| faults | disabled in this env | fault interaction is future work |
| macro control | separate environment | no change to the construction task |
| frozen benchmark | power disabled by default | hash regression must hold |

## Determinism

- Priorities are discrete and applied before the power tick.
- Allocation order is fixed by priority and entity id.
- No RNG in the environment; training RNG is explicit.

## Tests

- Priority changes allocation order and the state hash.
- Env reset, step, reward, mask, termination, and success.
- Observation shape and range.
- Scripted alternation beats every fixed policy.
- Tabular Q learns a successful policy.
- Runner and report.
- Power-free golden hash and frozen benchmark regression.

## Alternatives

- **Per-entity allocation.** Rejected: the action space is too large and the
  observation would need a much larger entity view.
- **Load shedding (disable types).** Rejected: fixed shedding policies are
  degenerate on this line; priority switching is the actual scheduling problem.
- **Two independent lines.** Deferred: a larger layout change; the single line
  already produces a clear furnace-vs-assembler trade-off.
- **Generator dispatch or fuel.** Deferred: phase 2 is about allocation, not
  generation.
- **Add power to the macro control task.** Rejected: changes its contract.

## Open questions

- Should the action choose per-entity priorities rather than type order?
- Should the budget vary over the episode?
- Should faults interact with allocation control?
- Should the agent choose both priority and build/remove?
