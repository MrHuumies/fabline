# Task card — multiview view arrival

- **Task family:** generic view-arrival suite
- **Version:** 0.1.0
- **Status:** contract implemented; training runner pending; not in
  `factory-v0.1`
- **World:** any supervised FABLINE task with named views
- **Owner:** FABLINE
- **Date:** 2026-11-23

## Phenomenon

A model trained on base views receives a new view after deployment. The suite
tests whether a bounded update can add the new view, preserve old-view behavior,
and stay within a declared update-cost budget.

## Contract

- **Observation:** `multiview.v1` — named views plus a boolean `view_mask`.
- **Roles:** base views, new view, retention views.
- **Label:** task-specific binary or scalar label.
- **Splits:** grouped by episode/layout/scenario; no frame-level random split.
- **Availability:** masks represent view arrival, dropout, and failure.
- **Flatten:** fixed-width vector with inactive views zeroed.

## Acceptance criteria

- Exact insertion: max |Δ| < 1e-5 on old-view outputs at insertion.
- New-view gain: ≥ 0.02 AP over the base on the declared task.
- Cached update: within 0.01 AP of full fine-tuning.
- Old-view retention: within 0.01 AP of the base.
- Update cost: ≤ 0.5× full retrain at matched final AP.
- Cache per row within the declared deployment budget.

## Baselines

| Baseline | Rule |
|---|---|
| base | old views only |
| residual | frozen base + zero-gated new-view residual |
| cached adapter | frozen base logits + cached adapter |
| cached LoRA | frozen base + cached low-rank adapter |
| full | full fine-tune on all views |

## Negative controls

- redundant view — should not clear the gain gate;
- aggregate vs per-entity view;
- noisy selection vs true selection;
- full fine-tune allowed to forget old-view performance.

## Metrics

- task metric and gain;
- old-view retention;
- exact-insertion max |Δ|;
- parameter/state counts;
- update seconds and peak memory;
- cache MB and cache MB/row;
- inference latency at batch 1 and 256.

## Known pitfalls

- The contract is not a model; flatten is a tabular baseline path.
- Availability masks must be trained, not only applied at test time.
- Episode-grouped splits are mandatory.
- No private or consumer-specific results belong in the public card.
- Not part of frozen `factory-v0.1`.

## Changelog

- 2026-11-23 — contract and task-family card created.
