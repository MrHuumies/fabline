# Benchmark specification — factory-v0.3 (draft)

- **Status:** draft; **not frozen** (Phase 1 production mix implemented; pilot
  mixed)
- **Date:** 2026-11-26
- **Target release:** FABLINE 0.4.0
- **World:** `factory-0.1.0` + opt-in production/order configs (expected; version
  bump only if canonical defaults change)
- **Predecessor:** [`factory-v0.2`](../factory-v0.2/card.md) remains immutable
- **Related:** RFC 0030, ADR 0042

## Purpose

`factory-v0.2` has 10 headline tasks but one fixed production recipe and a
seven-sequence line grammar. `factory-v0.3` adds a demand-driven production
mechanic and a new control/planning surface without changing the default world.

The benchmark is **not frozen**. The task set, splits, seeds, and expected
summary are fixed only after the 0.4.0 pilots pass.

## Candidate tasks

### Kept from v0.2

- throughput-vector
- throughput-grid
- throughput-entities
- masked-grid
- bottleneck
- expand-control
- control-dynamics
- planning-triage
- fault-calibration
- causal-removal

### New tasks

| Task | Kind | Observation | Why it is here |
|---|---|---|---|
| order-planning | planning | production + order state | choose a recipe/line plan for known orders |
| order-control | control | production + order view | switch recipes/build to meet deadlines |
| demand-calibration | calibration | order/production history | late/unfilled risk and value |
| recipe-intervention | prediction | state + recipe intervention | causal effect of a recipe switch/removal |
| production-mix | control | production view | gear vs component mix (Phase 1 slice) |

A task enters only if its pilot passes; `factory-v0.3` may ship with a subset.

## Mechanic

### Production mix (Phase 1)

- Opt-in `ProductionConfig`:
  - assembler recipe `0`: gear from ingots (current);
  - assembler recipe `1`: component from ingots;
  - opt-in component depot score;
  - task wrapper chooses the recipe; the frozen grid action contract is
    unchanged.
- `Item.COMPONENT` is absent from default delivered keys; default hashes are
  unchanged.
- The full `INGOT + COMPONENT -> GEAR` assembly edge is Phase 1b, gated on the
  Phase 1 pilot.

### Order stream (Phase 2)

- Opt-in `OrderConfig` with item, quantity, deadline, and value.
- Deterministic seeded arrivals.
- Fulfillment on delivery; late/unfilled penalties.
- `orders` observation view; order events are in the state hash when enabled.

## Splits and episodes (candidate)

- Core: 20 test and 20 shift episodes, same compositional split as v0.2.
- Order tasks: 5 evaluation seeds × 20 episodes; train/val/test by order seed.
- Control: 5 seeds; success/score thresholds fixed at freeze.
- No layout split unless the production task needs it.

## Baselines

- Regression/classification: existing v0.2 families.
- Production mix: always-gear, always-component, fixed alternation, random,
  tabular Q, behavior cloning.
- Order planning: scripted EDF/value, random, CEM/true simulator, oracle.
- Order control: scripted EDF/value, random, tabular Q, BC, PPO/SAC optional.
- Calibration: majority, GBDT, MLP; Brier/NLL/ECE.
- Causal: type-only vs target/intervention features.

## Metrics

- regression/classification/calibration/control metrics as v0.2;
- production: delivered item mix, score, recipe switches, setup time;
- orders: fulfilled fraction, lateness, value, wasted production;
- planning: score, success, budget, latency;
- causal: intervention R²/MAE vs observational baseline;
- efficiency: fit/predict time, artifact size, inference cost.

## Freeze criteria (draft)

1. Production/order configs are opt-in and default hashes are unchanged.
2. Each included task has a card, preregistration, and five-seed pilot.
3. No included task is saturated or near majority without a stated caveat.
4. 20 test and 20 shift episodes are present.
5. Expected summary and CI check exist.
6. `factory-v0.2` assets are unchanged.
7. Release audit and public scrub pass.

## Not frozen

- deep/offline RL as a headline task (baseline track only);
- a generative model on the current seven line grammars;
- new decentralized or calibration variants;
- a new world, fluids, trains, or full circuit networks.

## Runner

Planned `fabline benchmark-v03` after the pilot harnesses settle. It will
aggregate the core, production/order tasks, calibration/causal blocks, and the
efficiency table.

## Changelog

- 2026-11-26 — draft spec created; not frozen.
