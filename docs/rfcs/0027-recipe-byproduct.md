# Mechanic RFC 0027 — Byproduct queue on recipe choice

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-24
- **Related:** ADR 0039, RFC 0026, experiment 0072

## Summary

Slow recipe crafts produce a byproduct that accumulates on the assembler. At
capacity the assembler cannot start another craft until the byproduct is purged.
A third action purges the queue. Fast crafts produce no byproduct. This adds a
queue-management decision on top of the fast/cheap trade-off.

## Motivation

0070 established recipe choice; 0071 showed power is a robustness constraint,
not a new decision. The next P3 gap is a new output/queue structure. A byproduct
is the smallest version: no new `Item`, no depot/logistics change, and default
state hashes remain unchanged.

Pilot on seeds 40,000–40,004 with capacity 2:

| policy | mean score |
|---|---:|
| fast | 278 |
| buffer-aware (no purge) | 278 |
| slow | 20 |
| slow + purge | 200 |
| purge-aware | **304** |

The purge action adds +26 over fast and +26 over buffer-aware without purge.

## Rules

- Recipe fast: 2 ingots, 12 ticks, no byproduct.
- Recipe slow: 1 ingot, 20 ticks, 1 byproduct.
- Byproduct capacity: 2; at capacity, slow crafts block.
- Action 2 purges the byproduct queue.
- Reward: production score; success ≥ 300.

## Observation and action impact

With byproduct enabled, the observation appends `byproduct_norm`; the action
space is three (fast, slow, purge). Default recipe tasks keep two actions and
the 22-feature observation.

## Data impact

- New task condition `factory.production.recipe-choice.v1` with byproduct.
- Default `RecipeConfig` and `factory-v0.1` state/config hashes unchanged.
- No new `Item`.

## Tests

- Byproduct accumulates on slow crafts.
- Capacity blocks slow crafts.
- Purge resets the queue.
- Observation and action count.
- Default hash regression.

## Decision

Accepted. See ADR 0039 and experiment 0072. If purge-aware does not beat fast
and buffer-aware by 10, retire the byproduct axis.
