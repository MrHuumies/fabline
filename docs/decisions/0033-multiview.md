# ADR 0033 — Multiview observation and view-arrival contract

- **Status:** accepted
- **Date:** 2026-11-23
- **Related:** RFC 0022, docs/interface.md, `view-arrival` suite

## Context

The observation interface defines `multiview.v1` but the public implementation
does not expose it. A consumer needs a stable named-view/mask contract before a
consumer-side training method is meaningful.

## Decision

1. Add `src/fabline/obs/multiview.py` with `MultiviewFrame`,
   `MultiviewObservation`, a named-view registry, and mask-aware flattening.
2. Add `build_observation("multiview", ..., views, view_mask)`.
3. Add `src/fabline/tasks/view_arrival.py` with `ViewArrivalSpec`,
   `ViewArrivalData`, `ViewArrivalTask`, and view-selection validation.
4. Require episode-grouped splits in `ViewArrivalData`.
5. Keep training and update methods consumer-side; the public package does not
   prescribe a model architecture.
6. Keep the public tree free of private consumer names and results.

## Alternatives considered

- **Task-specific view-arrival projections.** Rejected; a general task contract
  avoids one-off projections.
- **A training method first.** Rejected; the interface must settle before model
  code.
- **Masked views absent from flatten.** Rejected; fixed-width zeros keep tabular
  baselines stable across masks.

## Consequences

- Consumers can build and test named view dictionaries now.
- A consumer can add models without changing the observation contract.
- The flatten path is intentionally simple and not a model architecture.
- No world, task label, split, or frozen benchmark behavior changes.

## Follow-ups

- [ ] Consumer-side view-arrival experiments are not part of the public package.
- [ ] Keep private consumer names and results out of the public tree.
