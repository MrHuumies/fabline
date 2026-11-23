# ADR 0033 — Multiview observation and view-arrival contract

- **Status:** accepted
- **Date:** 2026-11-23
- **Related:** RFC 0022, docs/interface.md, `view-arrival` suite

## Context

The observation interface defines `multiview.v1` but the public implementation
does not expose it. A consumer needs a stable named-view/mask contract before a
training runner or update-cost benchmark is meaningful.

## Decision

1. Add `src/fabline/obs/multiview.py` with `MultiviewFrame`,
   `MultiviewObservation`, a named-view registry, and mask-aware flattening.
2. Add `build_observation("multiview", ..., views, view_mask)`.
3. Add `src/fabline/tasks/view_arrival.py` with `ViewArrivalSpec`,
   `ViewArrivalData`, `ViewArrivalTask`, and view-selection validation.
4. Require episode-grouped splits in `ViewArrivalData`.
5. Keep the training runner, cached models, and cost report as a follow-up.
6. Keep the public tree free of private consumer names and results.

## Alternatives considered

- **Task-specific view-arrival projections.** Rejected; a general task contract
  avoids one-off adapters.
- **A runner first.** Rejected; the interface must settle before model code.
- **Masked views absent from flatten.** Rejected; fixed-width zeros keep tabular
  baselines stable across masks.

## Consequences

- Consumers can build and test named view dictionaries now.
- The runner can add models without changing the observation contract.
- The flatten path is intentionally simple and not a model architecture.
- No world, task label, split, or frozen benchmark behavior changes.

## Follow-ups

- [ ] Training/update runner with base, residual, cached adapter, cached LoRA,
  and full fine-tune.
- [ ] Exact insertion, retention, update-cost, cache, and latency report.
- [ ] Public power/fault view-arrival evidence; no private results.
