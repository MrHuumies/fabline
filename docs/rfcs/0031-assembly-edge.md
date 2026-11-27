# RFC 0031 — Assembly edge and per-assembler recipe state

- **Status:** accepted; frozen in `factory-v0.5`
- **Author:** FABLINE
- **Date:** 2026-11-26
- **Related:** RFC 0030, ADR 0042, `factory-v0.4` coverage suite,
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
    `assembly_component_cost`, `assembly_output`, `component_score`.
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
| `assembly-control` | control | online recipe switching; Q 460 vs random 429.2 |
| `assembly-planning` | planning | five-block recipe plan; CEM 428 vs oracle 430 |
| `assembly-bom` | regression | future gear output under decision noise; GBDT R² 0.503 |
| `assembly-intervention` | causal | counterfactual switch effect; GBDT R² 0.944 |

All four task wrappers are implemented and frozen in `factory-v0.5`:
`AssemblyControlEnv` plus `harness/assembly_control.py`,
`harness/assembly_planning.py`, `harness/assembly_bom.py`, and
`harness/assembly_intervention.py`.

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

The remaining assembly pilots are also positive:

| Task | Result |
|---|---|
| planning | CEM 428.0 vs oracle 430.0; frontload 410.0; random 372.9 |
| BOM | GBDT R² 0.503; linear 0.343; MLP 0.465 |
| intervention | GBDT R² 0.944; +1.62 of +2.00 oracle switching gain |

The BOM task logs with a stochastic policy so the future is not a deterministic
function of the observation. The intervention task uses paired simulator
potential outcomes: force the opposite recipe and hold it versus continue the
behaviour policy.

## Gates

- Mechanic: opt-in; default v0.1–v0.4 hashes unchanged; component and assembly
  logistics tested.
- Control: best scripted ≥ always gear + 10; best learned ≥ random + 10;
  success ≥ 0.60.
- Planning: oracle ≥ best scripted + 10; CEM ≥ random + 10; CEM within 10 of
  oracle; success ≥ 0.60.
- BOM: GBDT R² ≥ 0.30; GBDT ≥ linear + 0.05; not saturated; MLP ≥ 0.20.
- Causal: GBDT R² ≥ 0.30; GBDT ≥ linear + 0.05; model gain at least half of
  oracle gain and ≥ 0.5; MLP ≥ 0.20.

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

Accepted and frozen in `factory-v0.5`. The mechanic (state, recipes, logistics,
tests) and all four task families are implemented. Every pilot is positive and
no frozen v0.1–v0.4 asset is changed. Demand uncertainty, layout splits, and
logged-data causal identification remain follow-ups for a later version.
