# Mechanic RFC 0026 — Assembler recipe choice

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-24
- **Related:** ADR 0037, experiment 0070

## Summary

Add an opt-in assembler recipe choice: fast/expensive (2 ingots, 12 ticks) or
slow/cheap (1 ingot, 20 ticks). Both produce gears. The agent chooses the recipe
at each decision interval; the trade-off depends on the ingot queue. The frozen
world keeps the original recipe and hash.

## Motivation

P3 lists dynamic recipes / byproducts / queues as a gap. A recipe-cost switch
is the smallest version: no new item, no depot change, and no frozen-benchmark
change. It tests queue-aware scheduling and long-horizon credit assignment.

A pilot on seeds 36,000–36,004 with a seeded initial ingot buffer:

| policy | mean score |
|---|---:|
| fast | 278 |
| slow | 230 |
| alternate | 248 |
| random | 284 |
| one-step lookahead | 278 |
| **buffer-aware** | **320** |

The myopic lookahead matches fast; the queue-aware policy wins. That is the
intended decision.

## Rules

- 16×8 gear scenario, 500 ticks, decision interval 10.
- Recipe fast: 2 ingots, 12 ticks.
- Recipe slow: 1 ingot, 20 ticks.
- Initial assembler ingot buffer: seeded 0–6.
- Action: set the recipe for the next interval.
- Reward: factory production score; success ≥ 300.

## Observation and action impact

The recipe observation is 22 features: the 18 vector features, a two-way recipe
one-hot, and normalized assembler input/output totals. The action space is two.

## Data impact

- New task `factory.production.recipe-choice.v1`.
- `RecipeConfig` is separate from `FactoryConfig`; `factory-v0.1` config hash is
  unchanged.
- `WorldState.recipe_index` is canonical only when nonzero; default state hashes
  are unchanged.
- The world uses the original recipe unless an explicit `RecipeConfig` is passed.

## Tests

- Default state hash unchanged with and without a recipe config.
- Recipe action switches the recipe and counts switches.
- Recipe config validation.
- Frozen benchmark regression.

## Alternatives

- **New alloy item / depot score.** Larger change; deferred.
- **Byproduct queues.** Larger change; deferred until the recipe switch is
  tested.
- **Fixed recipe schedule.** Rejected; no agent decision.

## Decision

Accepted. See ADR 0037 and experiment 0070. If buffer-aware does not beat fast
by 10 on fresh seeds, retire the recipe axis.
