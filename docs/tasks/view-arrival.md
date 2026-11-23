# Task card — multiview view arrival

- **Task family:** generic view-arrival suite
- **Version:** 0.1.0
- **Status:** `multiview.v1` and `ViewArrivalTask` contract implemented; not in
  `factory-v0.1`
- **World:** any supervised FABLINE task with named views
- **Owner:** FABLINE
- **Date:** 2026-11-23

## Phenomenon

A model trained on base views receives a new view after deployment. The suite
tests whether a bounded update can add the new view, preserve old-view behavior,
match full fine-tuning, and stay within a declared update-cost budget.

## Contract

- **Observation:** `multiview.v1` — named views plus a boolean `view_mask`.
- **Roles:** base views, new view, retention views.
- **Label:** task-specific binary or scalar label.
- **Splits:** grouped by episode/layout/scenario; no frame-level random split.
- **Availability:** masks represent view arrival, dropout, and failure.
- **Flatten:** fixed-width vector with inactive views zeroed.
- **Task protocol:** `ViewArrivalSpec` plus `load() -> ViewArrivalData`.

## Acceptance criteria

- Exact insertion: max |Δ| ≤ 1e-5 on old-view outputs at insertion.
- New-view gain: ≥ 0.02 AP over the base on the declared task.
- Old-view retention: within 0.01 AP of the base.
- Update cost: ≤ 0.5× full retrain at matched final AP.

## Metrics

- task metric and gain;
- old-view retention;
- exact-insertion max |Δ|;
- parameter/state counts;
- update seconds and peak memory;
- inference latency at batch 1 and 256.

## Negative controls

- redundant view — should not clear the gain gate;
- aggregate vs per-entity view;
- noisy selection vs true selection;
- full fine-tune allowed to forget old-view performance.

## Known pitfalls

- The contract is not a model; flatten is a tabular baseline path.
- Availability masks must be trained, not only applied at test time.
- Episode-grouped splits are mandatory.
- Update methods are consumer-side; the public package does not prescribe a
  model architecture or a specific adaptation method.
- Not part of frozen `factory-v0.1`.

## Changelog

- 2026-11-23 — contract and task-family card created.
- 2026-11-23 — public surface limited to the contract; update methods are
  consumer-side.
