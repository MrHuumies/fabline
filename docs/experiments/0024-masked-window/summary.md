# Experiment 0024 — Masked feature-window throughput

- **Status:** complete
- **Date:** 2026-11-21
- **Type:** P0 partial-observability experiment
- **World:** factory-0.1.0; layout context + line buffers
- **Code:** `experiments/partial_observability/window_data.py`,
  `window_run.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.1` unchanged

## Result in one paragraph

**A short history recovers most of the state lost to masked features.** The full
current frame gives linear R² 0.752, GBDT 1.000, and MLP 0.613. With 60% of
features masked, the single-frame R² falls to 0.164 / 0.593 / −0.194. A window
of four masked frames recovers to 0.578 / 0.883 / 0.002. All three gates pass:
partial damage is real, history recovery is real, and no model reaches the full
frame with the window. GBDT and linear recover about 70% of their lost R²; the
MLP recovers only 24% and overfits the 104-feature window.

## Data

- 100 episodes; fixed gear line; 150-tick warmup; 300-tick episodes.
- 10-tick sampling; 50-tick future-score horizon.
- 800 samples; train / val / test = 560 / 160 / 80.
- Frame: 7 layout-context features + 6 line-buffer features (13).
- Dropout: 60% per frame, independent of tick; binary mask included.
- Views: `current` (13), `single` masked + mask (26), `window` last 4 masked
  frames + masks (104).
- Formal data seed 1; the pilot used seed 0.

## Results

Test R² with 95% bootstrap CIs:

| method | current | single masked | window |
|---|---:|---:|---:|
| mean | 0.000 | 0.000 | 0.000 |
| linear | 0.752 [0.639, 0.806] | 0.164 [−0.015, 0.292] | 0.578 [0.406, 0.697] |
| GBDT | 1.000 [1.000, 1.000] | 0.593 [0.364, 0.722] | 0.883 [0.801, 0.941] |
| MLP | 0.613 [0.530, 0.665] | −0.194 [−0.698, 0.096] | 0.002 [−0.512, 0.358] |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 partial damage | single ≥ 0.10 below current for 2+ baselines | **pass**, all three |
| H2 history recovery | window ≥ 0.10 above single for 2+ baselines | **pass**, all three |
| H3 no free lunch | no baseline reaches current with window | **pass** |
| H4 model split | report which models recover | linear/GBDT recover; MLP barely |
| H5 data scale | report counts and CIs | 800 samples; 80 test |

## Interpretation

- **Masked features create a real partial-observability gap.** Single-frame R²
  drops by 0.41–0.81 depending on the model.
- **History is informative.** Linear recovers 70% of its lost R², GBDT 71%, and
  MLP 24%.
- **GBDT is the strongest tabular recovery model.** It reaches 0.883 with a
  window, still below its 1.000 full-frame ceiling.
- **The MLP overfits the 104-feature window.** 560 training rows are not enough
  for a dense model on this representation. This is a sample-efficiency result,
  not a task failure.
- **The mask does not leak phase.** Masks are seeded independently of tick; the
  pilot’s tick-seeded mask was discarded after it revealed phase.

## Caveats

- Labels have only two values (20 and 30), so GBDT on the full frame is at
  ceiling.
- One deterministic fit per baseline (`random_state=0`); CIs are row-bootstrap,
  not seed-to-seed.
- 80 test samples; CIs are wide.
- The fixed gear line is periodic; the task tests missing features, not
  non-periodic dynamics.
- The window is a concatenation, not a sequence model; an RNN/Transformer is the
  natural next baseline.

## Next

- Add RNN/Transformer/CNN baselines on the window/grid views.
- Try fogged grid with a moving visibility window.
- Keep `factory-v0.1` frozen.

## Artifacts

- Task card: `docs/tasks/partial-throughput.md`
- Dataset card: `docs/datasets/partial-window-debug-v0.1.md`
- Raw results: `results/partial_observability/window/` (ignored)
- Run: `PYTHONPATH=. .venv/bin/python -m experiments.partial_observability.window_run --data /tmp/window.npz --out results/partial_observability/window --episodes 100 --data-seed 1`
