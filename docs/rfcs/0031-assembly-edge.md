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
- An assembler accepts component only when the assembly tree is enabled and its
  recipe is 2.
- Component is conserved except at the depot/removal.

## Tasks

| Task | Kind | Purpose |
|---|---|---|
| `assembly-control` | control | choose per-assembler recipe online against orders |
| `assembly-planning` | planning | choose an initial recipe/line plan for known orders |
| `bom-forecast` | regression | predict component starvation/gear output |
| `recipe-intervention` | causal | counterfactual effect of a recipe switch/removal |

The first task wrapper is not implemented in this RFC. The mechanic and unit
tests are the first slice.

## Layout problem

The starter line is linear: miner -> belt -> furnace -> belt -> assembler ->
belt -> depot. Component produced by the assembler flows toward the depot, so
the same assembler cannot consume it without a second feed or a routing change.

The first task wrapper needs one of:

- a custom assembly-cell layout with two input belts (ingot and component) into
  the assembly assembler;
- a second assembler/furnace branch that feeds component into the assembly
  assembler;
- a splitter/merger (a later 0.8.0 mechanic).

Do not force the linear starter line to do assembly without one of these.

## Economics problem

The current recipe costs do not make assembly attractive: direct gear is
2 ingots / 12 ticks, while component (1 ingot / 8 ticks) plus assembly
(1 ingot + 1 component / 16 ticks) is 2 ingots / 24 ticks. Assembly is
dominated unless the task adds one of:

- a higher-value assembly output (a new item or a quality flag);
- an output quantity greater than one (for example 2 gears per assembly);
- a lower ingot cost for the assembly recipe;
- a demand/contract that values assembly output differently.

This must be fixed in the task pre-registration. Do not freeze an assembly task
where always-gear is optimal. The mechanic slice deliberately leaves the
economics open.

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

- **Routing.** The component must reach the assembly assembler; a linear line
  cannot do it without a second feed.
- **Action-contract churn.** Per-assembler recipe is task-layer state; do not
  change the frozen grid action contract.
- **Hash drift.** Default entity hashes must stay identical.
- **Content growth.** Keep the recipe set to three.

## Decision

Proposed. The first slice (state, recipes, logistics, tests) is implemented on
`feat/0.6.0-assembly-edge`; the task wrapper and benchmark are pending.
