# Experiment 0084 — Maintenance-risk calibration

- **Status:** complete (mixed: diagnostics view calibrated; full maintenance view fails ECE)
- **Date:** 2026-11-25
- **Type:** P3 calibration follow-up
- **Task:** `factory.fault.maintenance_calibration.v1` (debug/P3, not in
  `factory-v0.2`)
- **Code:** `src/fabline/harness/maintenance_calibration.py`
- **CLI:** `python -m fabline maintenance-calibration`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**Calibration is mixed, and the registered full-view GBDT gate fails.** On 60
fresh episodes, the diagnostics-only view is skilled and calibrated (GBDT
balanced **0.9969**, ECE **0.0054**), but the full preventive-maintenance view
with maintenance count/remaining features is miscalibrated for GBDT (balanced
0.8925, ECE **0.0929**). The registered H2 gate uses the full view and fails;
the MLP full view is calibrated (ECE 0.0272). H1 and H3 pass; H2 fails. The
pilot's GBDT ECE of 0.014 did not replicate on the larger formal block, so this
is not promoted as a clean calibration task. Do not tune the view or refit
post-hoc.

## Formal results

60 episodes, seeds 61,000–61,059; 2,400 samples; positive rate 0.575;
train/val/test 1,680/480/240.

| view | model | balanced | Brier | NLL | ECE |
|---|---|---:|---:|---:|---:|
| diagnostics | GBDT | **0.9969** | 0.0032 | 0.0085 | **0.0054** |
| diagnostics | MLP | 0.8941 | 0.0754 | 0.2415 | 0.0478 |
| diagnostics + maintenance | GBDT | 0.8925 | 0.0909 | 0.6101 | **0.0929** |
| diagnostics + maintenance | MLP | 0.8977 | 0.0481 | 0.1563 | 0.0272 |

Majority baseline: accuracy 0.325, balanced 0.500.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 skill | GBDT balanced ≥ 0.75 | **pass**, 0.8925 |
| H2 calibration | GBDT ECE ≤ 0.05 | **fail**, 0.0929 |
| H3 view relevance | GBDT balanced ≥ majority + 0.20 | **pass**, +0.3925 |
| H4 base caveat | report positive/majority | pass, reported |
| H5 frozen benchmark | `factory-v0.2` unchanged | **pass** |

The **diagnostics-only** view passes the calibration gate (ECE 0.0054), but it
was not the registered primary view. It is a diagnostic comparison, not a
post-hoc promotion.

## Interpretation

- **Maintenance state features hurt GBDT calibration.** The full view adds
  maintenance count and remaining time; GBDT becomes overconfident even though
  its discrimination remains high. The MLP is better calibrated on the full
  view.
- **The base diagnostics view is calibrated.** It is also near the skill
  ceiling (balanced 0.997), so this is a ceiling-adjacent result, not a broad
  calibration stress test.
- **The pilot did not replicate.** The 40-episode pilot's GBDT ECE 0.014 was
  optimistic; the formal 60-episode block is the result.
- **Do not refit or drop the maintenance features to rescue H2.** That would be
  post-hoc view selection.

## Caveats

- 60 episodes; test split 240 samples and 6 episodes.
- One behavior policy (5% random maintenance) and one horizon (10 ticks).
- No sensor noise; calibration reflects state aliasing and future-activity
  uncertainty.
- The diagnostics-only view is near ceiling.
- Not part of `factory-v0.2`.

## Next

1. Report maintenance calibration as **mixed**: diagnostics calibrated, full
   maintenance view miscalibrated for GBDT.
2. Do not add another maintenance-calibration view or horizon.
3. Keep `factory-v0.2` and `v0.3.0` unchanged.

## Artifacts

- Task card: [`../../tasks/maintenance-calibration.md`](../../tasks/maintenance-calibration.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Code: `src/fabline/harness/maintenance_calibration.py`
- Raw results: `results/maintenance-calibration/` (ignored)
