# `factory-v0.5` freeze review

- **Status:** frozen as `factory-v0.5`
- **Version:** 0.5.0
- **Date:** 2026-11-27
- **Scope:** 0.6.0 assembly-edge release
- **Related:** [card](card.md), [spec](spec.md), RFC 0031,
  task cards for assembly control/planning/BOM/intervention,
  0.6.0 roadmap
- **Predecessor:** `factory-v0.4` remains immutable

## Decision summary

`factory-v0.5` freezes the **assembly edge**:

1. assembly-control
2. assembly-planning
3. assembly-bom
4. assembly-intervention

All four tasks pass their gates. The production tree is opt-in, and no frozen
v0.1–v0.4 asset is changed.

## Evidence

Full suite, 2026-11-27:

| Task | Status | Key result |
|---|---|---|
| assembly-control | pass | Q 460.0 vs random 429.2; batch 440; gear 260 |
| assembly-planning | pass | CEM 428.0 vs oracle 430.0; frontload 410; random 372.9 |
| assembly-bom | pass | GBDT R² 0.503, MLP 0.465, linear 0.343 |
| assembly-intervention | pass | GBDT R² 0.944, MLP 0.769; gain +1.62 of +2.00 |

Expected-summary check: **zero mismatches** on a fresh full run.

## What 0.6.0 established

- The production tree works: per-assembler recipes, component logistics, and
  `INGOT + COMPONENT -> 2 GEAR`.
- Online recipe control is learnable with a compact tabular Q policy.
- Finite-horizon planning is positive but shallow: five open-loop bits with a
  true-simulator CEM baseline.
- BOM output forecasting is non-saturated under decision noise (GBDT 0.503).
- A counterfactual recipe switch is learnable and decision-useful: the GBDT
  captures 81% of the oracle switching gain.
- The suite is deterministic and reproducible from a checked-in expected
  summary.

## Limitations

- Demand uncertainty is deferred; the assembly suite has no order stream.
- No layout split or private holdout.
- Planning is five binary blocks; the oracle is exhaustive at 32 plans.
- BOM and intervention use tabular sklearn baselines only.
- Intervention labels are paired simulator potential outcomes. A logged-data
  causal-identification task remains open.
- Regression CIs are row-level; the intervention decision CI is
  episode-clustered.
- The `--fast` path is a smoke check. It deliberately undertrains Q and CEM and
  is not a valid freeze configuration.
- The intervention decision gain is small in absolute score (+1.62). It is a
  sign of a sparse switch benefit, not a large policy improvement.

## Freeze gates

- [x] Four assembly tasks have cards, splits, and public harnesses.
- [x] Expected summary is checked in.
- [x] Full expected-summary check reports zero mismatches.
- [x] `factory-v0.1`–`factory-v0.4` assets and expected summaries are unchanged.
- [x] Freeze review and known limitations are documented.
- [x] CI workflow for the full check exists.

## Next steps

1. Keep `factory-v0.5` immutable.
2. Treat demand uncertainty, layout splits, and logged-data causal
   identification as a new benchmark version, not an edit.
3. Move to the 0.7.0 sequential-crew / uncertain-repair design and
   implementation.
