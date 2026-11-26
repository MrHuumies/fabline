# Task card — assembly-edge production control

- **Task ID:** `factory.assembly.control.v1` (draft)
- **Version:** 0.1.0-draft
- **Status:** mechanic implemented; task wrapper and benchmark pending
- **World:** `factory-0.1.0` + opt-in production tree
- **Owner:** FABLINE
- **Date:** 2026-11-26
- **RFC:** [`0031-assembly-edge.md`](../rfcs/0031-assembly-edge.md)

## Phenomenon

A factory can make gears directly from ingots, make components from ingots, or
assemble gears from ingots plus components. The assembly route requires a
shared intermediate and a multi-step plan. The task tests whether a policy can
choose per-assembler recipes, hold the right intermediate buffer, and meet
demand without myopic switching.

## Contract (draft)

- **Observation:** production graph, assembler recipe state, component/gear
  buffers, and order queue/status.
- **Action:** per-assembler recipe: gear (0), component (1), assembly (2);
  optional build/route actions in a later slice.
- **Orders:** seeded gear/component orders with deadlines and values.
- **Reward:** fulfilled order value minus late/unfilled penalties and waste.
- **Episode:** 300–500 ticks; decision interval 10.
- **Success:** fixed at pre-registration.
- **Layout:** an assembly cell with separate ingot and component feeds; the
  linear starter line is not sufficient.

## Baselines

| Baseline | Rule |
|---|---|
| always_gear | always recipe 0 |
| always_component | always recipe 1 |
| always_assembly | always recipe 2 (needs component feed) |
| buffer_aware | choose by component/ingot buffers |
| EDF/value | order-aware recipe choice |
| random | uniform legal recipe |
| tabular Q | recipe/buffer/order buckets |
| CEM/OR | finite-horizon plan |
| GNN/MPNN | production-graph policy/value |

## Gates (draft)

| Gate | Threshold |
|---|---|
| H1 assembly effect | oracle ≥ best fixed/scripted + 10 |
| H2 learned baseline | best learned ≥ random + 10 |
| H3 success | best learned success ≥ 0.60 |
| H4 default hash | v0.1/v0.2/v0.3 unchanged |
| H5 cost | report parameters/training/inference |

## Known pitfalls

- **Routing.** Component must reach the assembly assembler; the linear starter
  line sends component to the depot.
- **Recipe state is per entity.** A global `production_recipe` is not enough.
- **Component conservation.** Component should only disappear at assembly,
  depot delivery, or removal.
- **Small action space.** One assembler with three recipes is a sequential
  decision, not a hard control benchmark; multiple assemblers/routing are a
  later slice.
- **Economics are not fixed.** At the current costs (2 ingots/12 ticks direct
  vs 2 ingots/24 ticks through component plus assembly), assembly is dominated.
  The task must add a higher-value output, output quantity, lower cost, or
  demand premium; otherwise always-gear is optimal.
- **Do not tune order distributions after the formal block.**

## Changelog

- 2026-11-26 — draft card created; mechanic slice implemented.
