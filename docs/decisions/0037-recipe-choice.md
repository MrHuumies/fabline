# ADR 0037 — Assembler recipe choice

- **Status:** accepted
- **Date:** 2026-11-24
- **Related:** RFC 0026, experiment 0070

## Context

P3 lists dynamic recipes/byproducts/queues as a gap. Adding fields to
`FactoryConfig` would change the frozen benchmark's config hash, so the recipe
settings must live outside it.

## Decision

1. Add `RecipeConfig` with fast/slow tick and ingot costs; default disabled.
2. Add `WorldState.recipe_index`, canonical only when nonzero.
3. Add an optional `recipe` argument to `FactoryWorld`; default `None` preserves
   the original recipe and state hash.
4. Add `RecipeEnv` and the `fabline recipe-choice` CLI.
5. Use a seeded initial ingot buffer (0–6) to create per-episode trade-off
   variation.
6. Keep the task opt-in and the frozen benchmark unchanged.

## Alternatives considered

- **Add recipe fields to `FactoryConfig`.** Rejected: changes the frozen config
  hash.
- **New alloy item.** Rejected for the first slice; larger state and depot
  change.
- **Fixed recipe schedule.** Rejected: no decision.

## Consequences

- The task tests queue-aware recipe selection with no new item.
- The frozen config hash and default state hash are unchanged.
- The one-step lookahead is myopic; buffer-aware is the strong scripted
  baseline.
- If the formal gap is under 10, retire the recipe axis.

## Follow-ups

- [ ] Formal experiment 0070 on seeds 37,000–37,004.
- [ ] Update the coverage map and roadmap with the verdict.
- [ ] Consider byproducts only if the recipe switch is positive.
