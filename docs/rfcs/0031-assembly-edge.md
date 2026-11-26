# RFC 0031 — Assembly edge and per-assembler recipe state

- **Status:** proposed
- **Author:** FABLINE
- **Date:** 2026-11-26
- **Related:** RFC 0030, ADR 0042, `factory-v0.4` coverage draft,
  [`roadmap-0.5.0-0.8.0.md`](../roadmap-0.5.0-0.8.0.md),
  [`coverage-analysis-2026-11-26.md`](../coverage-analysis-2026-11-26.md)

## Summary

Add an opt-in production tree:

```text
ORE -> INGOT                      (furnace)
INGOT -> GEAR                     (assembler recipe 0, existing)
INGOT -> COMPONENT                (assembler recipe 1)
INGOT + COMPONENT -> GEAR         (assembler recipe 2, assembly edge)
```

The mechanic adds per-assembler recipe state, component as a logistics item,
and the multi-input assembly craft. It is off by default; the v0.1/v0.2/v0.3
hashes and assets remain unchanged.

This is the leading 0.5.0/0.6.0 mechanic from the 0.4.0 review. It addresses
the 0089 finding that the recipe-only mix has no schedule gap because the
product mix is a global switch, not a production graph.

## Motivation

- The current production mix chooses gear or component globally; there is no
  shared intermediate or build/route coupling.
- A shared intermediate creates a real multi-step decision: produce component,
  hold it, switch the assembler, and assemble.
- It exposes compositional planning, DAG/graph representation, multi-input
  scheduling, myopic failure, causal recipe effects, and a richer generative
  recipe space.
- It is a small content change: one intermediate, three recipes, no new
  dependency.

## Design

### State

- `Entity.recipe: int = 0` (0 gear, 1 component, 2 assembly).
- The field is included in the state hash only when nonzero, so default
  hashes stay unchanged.
- `ProductionConfig` gains opt-in assembly fields:
  - `assembly_enabled`, `assembly_ticks`, `assembly_ingot_cost`,
    `assembly_component_cost`, `assembly_score`.
- `ProductionConfig.enabled` remains the production-tree gate; assembly
  requires it.

### Machines

- Recipe 0 uses the existing gear recipe.
- Recipe 1 consumes ingots and outputs component.
- Recipe 2 consumes ingots plus component and outputs gear.
- A machine only starts a craft when all inputs are present and the output
  buffer has space.

### Logistics

- Belts already carry any item.
- Depots accept component only when production is enabled (existing behavior).
- An assembler accepts component whenever the assembly tree is enabled, so the
  input buffer can hold component while the assembler runs direct gear.
- Component is conserved except at the depot/removal/assembly.

## Tasks

| Task | Kind | Purpose |
|---|---|---|
| `assembly-control` | control | choose per-assembler recipe online against orders |
| `assembly-planning` | planning | choose an initial recipe/line plan for known orders |
| `bom-forecast` | regression | predict component starvation/gear output |
| `recipe-intervention` | causal | counterfactual effect of a recipe switch/removal |

The first task wrapper is implemented on `feat/0.6.0-assembly-edge`:
`factory.assembly.control.v1`, `AssemblyControlEnv`, and
`harness/assembly_control.py`.

## Layout

The task uses a fixed **assembly cell** (`worlds/factory/assembly.py`) with two
independent feeds into one assembly assembler:

- component line: miner -> belt -> furnace -> belt -> component assembler ->
  belts -> assembly assembler from the north;
- ingot line: miner -> belt -> furnace -> belts -> assembly assembler from the
  south;
- assembly assembler -> belt -> depot.

The linear starter line is not used for assembly; it cannot route component
back to an assembler without a second feed or a splitter.

## Economics

The task sets:

- component: 1 ingot -> 1 component / 24 ticks;
- direct gear: 2 ingots -> 1 gear / 12 ticks;
- assembly: 1 ingot + 1 component -> **2 gears** / 16 ticks.

Component is deliberately slow so direct gear is a useful fallback and the
assembler must batch component before switching. Assembly outputs two gears so
it is worth doing. These are task-specific costs, not generic world defaults.

The formal pilot (5 seeds x 5 episodes) is positive:

| Policy | Score |
|---|---:|
| always gear | 260 |
| always assembly | 360 |
| buffer-aware | 420 |
| random | 429.2 |
| batch-aware | 440 |
| tabular Q (500 train episodes) | **460** |

The Q baseline beats random by 30.8 and succeeds 1.00; all control gates pass.

## Gates

- Mechanic: opt-in; default v0.1/v0.2/v0.3 hashes unchanged; component and
  assembly logistics tested.
- Control: oracle ≥ best scripted + 10; best learned ≥ random + 10; success ≥
  0.60.
- Planning: oracle ≥ best scripted + 10; CEM/OR within 10; success ≥ 0.60.
- Causal: target R² ≥ 0.30 and ≥ type-only + 0.20.

## Alternatives

- **Global recipe only:** rejected; 0089 showed no schedule gap.
- **Many recipes/items:** rejected; content treadmill.
- **Splitter/merger first:** deferred to 0.8.0; it solves routing but adds a
  larger spatial mechanic.

## Risks

- **Routing.** The component must reach the assembly assembler; the public task
  uses a fixed two-feed cell, not the linear starter line.
- **Action-contract churn.** Per-assembler recipe is task-layer state; do not
  change the frozen grid action contract.
- **Hash drift.** Default entity hashes must stay identical.
- **Content growth.** Keep the recipe set to three.

## Decision

Proposed. The first slice (state, recipes, logistics, tests) and the
`factory.assembly.control.v1` task wrapper are implemented on
`feat/0.6.0-assembly-edge`. The formal pilot is positive and no frozen
benchmark is changed. Planning/causal/forecast variants remain pending.
