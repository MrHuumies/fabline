# Mechanic RFC 0022 — Multiview observation and view-arrival contract

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-23
- **Related:** ADR 0033, docs/interface.md, experiment suite `view-arrival`

## Summary

Implement the public `multiview.v1` observation contract and the task-facing
shape of a view-arrival experiment. This is a contract-first slice: named views,
a boolean view mask, a fixed-width flatten path, a named-view registry, and a
generic `ViewArrivalTask` data contract. Training and update methods are
consumer-side.

## Motivation

The interface describes a named view dictionary but the public source has no
adapter or view-mask plumbing. Consumers cannot test view insertion, masking, or
retention against a stable contract.

## Contract

### Multiview observation

- `MultiviewFrame`: `views: dict[str, np.ndarray]` plus
  `view_mask: dict[str, bool]`.
- `MultiviewObservation`: a versioned adapter over a mapping of named
  observation adapters.
- `observe(state, view_mask=None)` returns a frame; a dynamic mask may only
  narrow/activate declared views.
- `flatten(frame)` returns a fixed-width float32 vector. Inactive views are
  zeroed so the width is stable across masks.
- `ObservationSpec` name `multiview`, version `1.0.0`; shape and prefixed
  feature names are the sum of view widths when all view shapes are known.
- `register_view(name, factory)` and `build_registered_view(...)` provide the
  named-view registry.
- `build_observation("multiview", ..., views=..., view_mask=...)` is the built-in
  construction path.

### View-arrival task

- `ViewArrivalSpec`: task id/version, base views, new view, retention views,
  label.
- `ViewArrivalData`: named views, view mask, labels, splits, episode ids.
- Splits are episode-grouped; a row-level random split is rejected.
- `ViewArrivalTask` is a protocol with `spec` and `load()`.
- `validate_view_selection` checks that declared views exist.

## What this does not do

- No training method or cost benchmark in the public package.
- No dataset or public result table.
- No frozen `factory-v0.1` changes.
- No private consumer naming, private experiment numbers, or private results.

## Tests

- Named view dictionary and mask.
- Dynamic mask and unknown-view rejection.
- Fixed-width flatten with zeroed inactive views.
- Registry construction.
- Task spec role validation and episode-grouped splits.
- Frozen benchmark regression.

## Decision

Accepted. See ADR 0033. Any training/update method is consumer-side and is not
part of the public package.
