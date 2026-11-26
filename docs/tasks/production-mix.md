# Task card — production mix

- **Task ID:** `factory.production.mix.v1`
- **Version:** 0.1.0
- **Status:** draft; Phase 1 mechanic pilot; not in any frozen benchmark
- **World:** factory-0.1.0 + opt-in `ProductionConfig`
- **Owner:** FABLINE
- **Date:** 2026-11-26

## Phenomenon

The assembler can make gears from ingots or components from ingots. The agent
chooses the recipe at decision boundaries. The task tests whether a product-mix
decision is non-trivial before adding orders and deadlines.

## Contract

- **Observation:** production view: tick, score, delivered gear/component,
  inventory, active recipe, assembler state, blocked ticks.
- **Action:** recipe 0 = gear, recipe 1 = component; wrapper action at decision
  boundaries. The frozen grid action contract is unchanged.
- **Default:** gears from ingots; component is opt-in.
- **Score:** opt-in component depot score; default scoring unchanged.
- **Episode:** 300 ticks; decision interval 10.
- **Success threshold:** fixed at preregistration.

## Baselines

| Baseline | Rule |
|---|---|
| always_gear | recipe 0 throughout |
| always_component | recipe 1 throughout |
| alternation | switch every fixed interval |
| random | uniform recipe choice |
| tabular Q | production state buckets |
| behavior cloning | scripted/oracle recipe sequences |

## Metrics

- mean score with 95% bootstrap CI;
- gear/component deliveries;
- recipe switches and setup time;
- success rate.

## Gates (pilot)

| Gate | Threshold |
|---|---|
| H1 mechanic | production config runs; default hash unchanged |
| H2 decision | best scripted/oracle ≥ always-gear + 10 |
| H3 not saturated | oracle gap over best fixed ≥ 10 |
| H4 frozen benchmark | `factory-v0.2` unchanged |

If H2/H3 fail, the production mix is too easy; proceed to the order stream or
Phase 1b assembly edge rather than tuning the recipe.

## Known pitfalls

- A single assembler cannot make both items at once; switching has setup cost.
- Component has no value unless `ProductionConfig` enables it.
- The wrapper action is not part of `grid_build.v1`.
- Default states, hashes, and observations must not change.

## Results (0089)

Seeds 70,000–70,004; 5 episodes per seed:

| policy | mean score | switches | success |
|---|---:|---:|---:|
| always gear | 150.0 | 0.0 | 0.00 |
| always component | 186.0 | 1.0 | 0.00 |
| tabular Q | 189.2 | 23.8 | 0.00 |

H2 passes (+36 over always-gear), but H3 fails: the best schedule gains only
+3.2 over best fixed. The mix alone is a fixed-item choice, not a scheduling
task; the order stream is the next layer. See
[`experiments/0089-production-mix`](../experiments/0089-production-mix/summary.md).

## Changelog

- 2026-11-26 — draft card created; Phase 1 pilot pending.
- 2026-11-26 — pilot mixed: component 186 vs gear 150; no schedule gap.
