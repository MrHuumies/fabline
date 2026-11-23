# ADR 0039 — Byproduct queue on recipe choice

- **Status:** accepted
- **Date:** 2026-11-24
- **Related:** RFC 0027, RFC 0026, experiment 0072

## Context

The recipe task has a queue decision but no output/queue structure. Adding a new
`Item` would touch logistics and depot scoring. A per-assembler byproduct counter
is the smallest way to add a blocking queue.

## Decision

1. Add `byproduct_enabled`, `byproduct_per_slow`, and `byproduct_capacity` to
   `RecipeConfig`; default disabled.
2. Add `Entity.byproduct`, canonical only when nonzero.
3. Slow crafts add byproduct; at capacity, `_advance_machine` blocks the craft.
4. Add action 2 (purge) to `RecipeEnv` when byproduct is enabled.
5. Append `byproduct_norm` to the observation and add `byproduct`/`purges` to
   `info`.
6. Keep default recipe tasks at two actions and unchanged state hashes.

## Alternatives considered

- **New slag item.** Rejected: logistics and depot changes are unnecessary.
- **Score penalty per byproduct.** Rejected: blocking is the decision, not a
  scalar cost.
- **Automatic purge.** Rejected: removes the action.

## Consequences

- The task tests recipe choice plus queue purge.
- The fast recipe remains the no-queue baseline.
- The byproduct counter is an opt-in state field; default hashes are unchanged.
- If purge-aware does not beat fast and buffer-aware by 10, retire the axis.

## Follow-ups

- [ ] Formal 0072 on seeds 41,000–41,004.
- [ ] Update the coverage map and roadmap.
- [ ] Keep `factory-v0.1` frozen.
