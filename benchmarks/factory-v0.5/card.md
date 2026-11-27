# Benchmark card — factory-v0.5

- **Status:** frozen
- **Version:** 0.5.0
- **Date:** 2026-11-27
- **World:** `factory-0.1.0` + opt-in production tree
- **Plan:** `assembly-v0.5`
- **Spec:** [`spec.md`](spec.md)
- **Expected summary:** [`expected/summary.json`](expected/summary.json)
- **Freeze review:** [`freeze-review.md`](freeze-review.md)
- **Predecessor:** `factory-v0.4` remains immutable
- **Runner:** `python -m fabline assembly-suite --out results/factory-v0.5`
- **Check:** `python -m fabline assembly-suite --out results/factory-v0.5 --check-expected benchmarks/factory-v0.5/expected/summary.json`

## What is frozen

`factory-v0.5` is the **assembly-edge release**. It keeps the frozen v0.4
coverage suite by reference and publishes four tasks on the opt-in production
tree:

| Task | Kind | Observation | Status |
|---|---|---|---|
| assembly-control | control | 12-feature cell state | pass |
| assembly-planning | planning | initial cell state | pass |
| assembly-bom | regression | 12-feature cell state | pass |
| assembly-intervention | causal effect | 12-feature cell state | pass |

The production tree is opt-in. It adds per-assembler recipes, component
logistics, and `INGOT + COMPONENT -> 2 GEAR`. Frozen v0.1–v0.4 assets and hashes
are unchanged.

## Suite result

Full suite, 2026-11-27:

| Task | Status | Key result |
|---|---|---|
| assembly-control | pass | tabular Q 460.0 vs random 429.2, gear 260.0 |
| assembly-planning | pass | CEM 428.0 vs oracle 430.0, frontload 410.0 |
| assembly-bom | pass | GBDT R² 0.503 vs linear 0.343 |
| assembly-intervention | pass | GBDT R² 0.944; gain +1.62 of +2.00 |

The assembly-control result confirms the earlier formal pilot. Planning is a
five-bit open-loop task with true-simulator CEM; BOM and intervention are
state-to-outcome regression tasks. Intervention is a paired counterfactual
effect task, not an online policy.

## Caveats

- Demand uncertainty is deferred; it is not part of this freeze.
- The cell is fixed at two assemblers on a 16×8 line. There is no layout split.
- Planning is five binary blocks; CEM is near-exhaustive and is not general
  planning evidence.
- BOM and intervention report tabular baselines only.
- Intervention labels are paired simulator potential outcomes. Estimation from
  logged data alone is a follow-up.
- The `--fast` path is a smoke check, not a valid freeze configuration.
- There is no generated demand stream in the assembly suite.

## Changelog

- 2026-11-27 — card created for the `factory-v0.5` freeze.
