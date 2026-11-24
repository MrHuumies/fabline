# Experiment 0079 — Counterfactual entity removal

- **Status:** complete (positive; causal signal)
- **Date:** 2026-11-24
- **Type:** P3 causal-intervention experiment
- **Task:** `factory.causal.remove.v1` (debug/P3, not in `factory-v0.1`)
- **Code:** `src/fabline/harness/causal_intervention.py`
- **CLI:** `python -m fabline causal-remove`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Target-specific intervention features predict same-type removal effects;
type alone does not.** Across three 40-episode blocks, target GBDT R² is
**0.986, 0.753, 0.992** (mean **0.910**); type-only GBDT is **−0.234, −0.594,
−0.072** (mean **−0.300**). Target linear mean R² is 0.598; type-only linear is
near zero. H1/H2/H4 pass. The task is a small but clean counterfactual
prediction benchmark, not a causal graph recovery claim.

## Formal results

Mean over three blocks (58,000 / 58,100 / 58,200), 120 rows per block:

| view | method | R² | MAE |
|---|---|---:|---:|
| type_only | GBDT | −0.300 | ~20 |
| type_only | linear | ~−0.13 | ~20 |
| type_only | MLP | ~−0.29 | ~20 |
| **target** | **GBDT** | **0.910** | ~2 |
| target | linear | 0.598 | ~10 |
| target | MLP | 0.157 | ~14 |

Per-block target GBDT: `0.986, 0.753, 0.992`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 target skill | target GBDT R² ≥ 0.30 | **pass**, 0.910 |
| H2 causal signal | target ≥ type-only + 0.20 | **pass**, +1.21 |
| H3 linear/MLP | report | linear 0.598; MLP 0.157 |
| H4 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Same-type pairs remove the type shortcut.** The type-only model is at or
  below the mean baseline; target positions and buffers carry the signal.
- **GBDT is the strongest causal predictor.** It explains 91% of the signed
  removal difference on average.
- **Linear/MLP are weaker but positive.** The signal is not only a GBDT
  artifact.
- **The task is small.** 120 rows per block, three sample ticks, one horizon.
  CIs are wide; report it as a debug causal benchmark.
- **Intervention, not discovery.** The label is a counterfactual score
  difference; the task does not recover a causal graph.

## Caveats

- Three 40-episode blocks; 120 rows each.
- Same-type pairs only; one sample tick set and one horizon.
- The counterfactual is a 100-tick score difference, not a full trajectory.
- No faults or power in the causal task.
- Not part of frozen `factory-v0.1`.

## Next

1. Include the causal task in the `factory-v0.2` candidate set.
2. Add a multi-horizon or multi-intervention variant only if it adds a new
   decision; do not tune this one.
3. Move to the GUI/wizard and benchmark-freeze phase.

## Artifacts

- Task card: [`../../tasks/causal-removal.md`](../../tasks/causal-removal.md)
- Code: `src/fabline/harness/causal_intervention.py`
- Raw results: `results/causal-remove/` (ignored)
