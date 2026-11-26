# Experiment 0089 — Production-mix pilot

- **Status:** complete (mixed; see [summary](summary.md))
- **Date:** 2026-11-26
- **Type:** 0.4.0 Phase 1 mechanic pilot
- **Task:** `factory.production.mix.v1` (draft, not in a frozen benchmark)
- **Code:** planned `ProductionConfig` + production wrapper
- **CLI:** planned `python -m fabline production-mix`
- **Benchmark:** none; `factory-v0.2` unchanged

## Question

Does the opt-in production mix (gear vs component) create a non-trivial recipe
decision before adding orders?

## Hypothesis

A single assembler cannot make both deliverables at once. If component and gear
have different value/throughput, the best schedule is not always-gear or
always-component; there is a recipe-switch decision with an oracle gap.

## Mechanic

- Opt-in `ProductionConfig`.
- Assembler recipe 0: gear from ingots (current).
- Assembler recipe 1: component from ingots.
- Component has an opt-in depot score; default scoring is unchanged.
- A task wrapper chooses the recipe at decision boundaries; the frozen grid
  action contract is unchanged.
- Default state hash must remain unchanged when the config is absent.

## Design

- 5 evaluation seeds: 70,000–70,004.
- Episode 300 ticks; decision interval 10.
- Conditions:
  - always gear;
  - always component;
  - fixed alternation periods 10/20/40 ticks;
  - random recipe;
  - tabular Q over production state;
  - oracle over the fixed schedule family.
- Report deliveries, score, switches, and success.

## Gates

| Gate | Threshold |
|---|---|
| H1 mechanic | config runs; default hash unchanged |
| H2 decision | best fixed/oracle ≥ always-gear + 10 |
| H3 oracle gap | oracle ≥ best fixed + 10 |
| H4 frozen benchmark | `factory-v0.2` unchanged |

If H2/H3 fail, the production mix is too easy; proceed to the order stream or
Phase 1b assembly edge rather than tuning the recipe.

## Predictions

- Always-gear and always-component are close if scores are balanced.
- Alternation and Q may find a small gain.
- If the gap is under 10, the mix alone is not a task; orders are the real
  decision.

## Kill criteria

- Default hash changes: reject the mechanic.
- No oracle gap over the best fixed schedule: report a negative pilot.
- No post-hoc score/recipe tuning.

## Transparency note

The pilot is the first slice of RFC 0030. It does not include orders, deadlines,
or the component→gear assembly edge.
