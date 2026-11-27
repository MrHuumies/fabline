# Task card — assembly-edge production control

- **Task ID:** `factory.assembly.control.v1`
- **Version:** 0.1.0
- **Status:** frozen in `factory-v0.5`
- **World:** `factory-0.1.0` + opt-in production tree
- **Owner:** FABLINE
- **Date:** 2026-11-26
- **RFC:** [`0031-assembly-edge.md`](../rfcs/0031-assembly-edge.md)
- **Code:** `src/fabline/env/assembly.py`,
  `src/fabline/harness/assembly_control.py`
- **CLI:** `python -m fabline assembly-control`

## Phenomenon

A factory can make gears directly from ingots, make components from ingots, or
assemble gears from ingots plus components. The assembly route requires a
shared intermediate and a multi-step plan. The task tests whether a policy can
choose per-assembler recipes, hold the right intermediate buffer, and meet
demand without myopic switching.

## Contract

- **Observation:** 12 features — tick, score, assembly recipe one-hot, assembly
  ingot/component/gear buffers, component-assembler input/output/progress,
  assembly craft progress, delivered gear.
- **Action:** 0 direct gear, 1 assembly. The component assembler is fixed to
  component production; the assembly assembler switches between direct gear and
  the assembly recipe.
- **Layout:** fixed two-feed assembly cell. The component line and the ingot
  line are independent; both feed the assembly assembler. Output goes to the
  depot.
- **Economics:** component 1 ingot / 24 ticks; direct gear 2 ingots / 12 ticks;
  assembly 1 ingot + 1 component / 16 ticks and **2 gears** per craft.
- **Episode:** 500 ticks; decision interval 10.
- **Success:** final score ≥ 100.

## Baselines

| Baseline | Rule |
|---|---|
| always_gear | always recipe 0 |
| always_assembly | always recipe 1 |
| buffer_aware | assembly if component ≥ 1 and ingot ≥ 1 |
| batch_aware | buffer component to 3 on direct gear, then assemble |
| random | uniform recipe |
| tabular Q | ingot/component/component-output/recipe buckets |

## Results (formal pilot, 5 seeds × 5 episodes)

| Policy | Mean score | Success | Switches |
|---|---:|---:|---:|
| always_gear | 260.0 | 1.00 | 0.0 |
| always_assembly | 360.0 | 1.00 | 1.0 |
| buffer_aware | 420.0 | 1.00 | 22.0 |
| random | 429.2 | 1.00 | 25.0 |
| batch_aware | 440.0 | 1.00 | 4.0 |
| **tabular Q** | **460.0** | **1.00** | 28.0 |

Q trains on 500 disjoint episodes. H1 scripted gap (+180), H2 learned gap
(+30.8 over random), and H3 success all pass. The task is scripted-easy but the
learned baseline is positive.

## Gates

| Gate | Threshold |
|---|---|
| H1 assembly effect | best scripted ≥ always_gear + 10 |
| H2 learned baseline | Q ≥ random + 10 |
| H3 success | Q success ≥ 0.60 |

Frozen v0.1–v0.4 hashes are enforced by the test suite and CI, not by the task
runner. Q trains for 500 episodes; wall-clock cost is not a gate.

## Known pitfalls

- **Routing is task content.** The fixed assembly cell has two feeds; the
  linear starter line cannot route component back to an assembler.
- **Recipe state is per entity.** A global `production_recipe` is not enough.
- **Component conservation.** Component should only disappear at assembly,
  depot delivery, or removal.
- **Small action space.** One binary recipe decision is a control floor, not a
  hard RL benchmark; multiple assemblers/routing are a later slice.
- **Economics are tuned for this task.** Component is deliberately slow
  (24 ticks) so direct gear is a useful fallback; assembly outputs two gears.
  Do not reuse these costs as generic world defaults.
- **Random is strong.** Switching is cheap; the batch/Q policies win by
  holding component, not by a wide margin.

## Changelog

- 2026-11-26 — draft card created; mechanic slice implemented.
- 2026-11-26 — task wrapper, assembly cell, Q baseline, and formal pilot added;
  Q 460, batch 440, random 429, always gear 260; all gates pass.
- 2026-11-27 — frozen in `factory-v0.5`; full suite reproduces Q 460.
