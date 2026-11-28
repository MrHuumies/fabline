# Experiment 0097 — Layout-shift pilot

- **Status:** exploratory pilot (mixed; diagnostic/challenge candidate; no
  benchmark freeze)
- **Date:** 2026-11-28
- **Type:** 0.8.0 spatial grammar, first slice
- **Task:** layout-shift throughput (draft; no benchmark)
- **Code:** `src/fabline/harness/layout_shift.py`,
  `src/fabline/obs/layout.py`, `src/fabline/tasks/throughput.py` (scenario hook)
- **CLI:** `python -m fabline layout-shift --observation layout-summary --normalize-target`
- **Benchmark:** none; `factory-v0.6` unchanged; `factory-v0.7` not frozen

## Result in one paragraph

**The layout-shift pilot is mixed.** Training on base layouts (16×8, 20×12,
24×16 twin) gives a strong raw-score fit (linear R² 0.983), but the shift R² is
−1.29 on the 32×24 spread layout, 0.13 on the 24×20 random layout, and −303 on
the 24×20 obstacle layout. A per-line normalized target makes the random shift
generalize (linear R² 0.60) but still fails the large shift (−0.99) and the
obstacle shift (−18.8); the base skill drops to 0.67 and the MLP is negative.
No tabular model is robust across layouts. The pilot is a diagnostic/challenge
candidate, not a standard benchmark; `factory-v0.7` is not frozen.

## Setup

Base layouts: 16×8 gear, 20×12 gear, 24×16 twin (12 train / 4 val / 4 test
layout seeds each). Shift layouts: 32×24 three-line spread, 24×20 randomized
twin, 24×20 obstacle-heavy; 8 layout seeds each. Throughput task: 200 warmup,
100-tick horizon, 500-tick episodes, 10-tick samples. Observations: vector and
fixed-width layout-summary (vector + width/height/line count/density).

## Results

### Raw target, layout-summary, broad base

| Shift | Linear test R² | Linear shift R² | MLP test R² | MLP shift R² |
|---|---:|---:|---:|---:|
| large 32×24 | 0.983 | −1.285 | 0.747 | −5.548 |
| random 24×20 | 0.983 | 0.134 | 0.747 | −1.234 |
| obstacles 24×20 | 0.983 | −302.957 | 0.747 | −22.609 |

### Per-line normalized target, layout-summary, broad base

| Shift | Linear test R² | Linear shift R² | MLP test R² | MLP shift R² |
|---|---:|---:|---:|---:|
| large 32×24 | 0.670 | −0.991 | −0.236 | −4.624 |
| random 24×20 | 0.670 | 0.595 | −0.236 | −0.294 |
| obstacles 24×20 | 0.670 | −18.808 | −0.236 | −0.826 |

The raw-score vector-only pilot was scale-confounded (base 0.864; large/random
−122); it is not used.

## Gates (pilot)

| Gate | Result |
|---|---|
| H1 base skill (best R² ≥0.20) | pass, 0.983 raw / 0.670 normalized |
| H2 OOD gap (≥0.10) | pass, but for the wrong reason on raw score |
| H3 no seed leakage | pass |
| H4 metrics complete | pass |

The raw-score H2 gap is dominated by label scale; the normalized gap is
structural but the obstacle/large shifts have no robust model.

## Interpretation

- **Layout shift is real.** The random 24×20 layout generalizes under a
  per-line target; the large three-line and obstacle-heavy layouts do not.
- **Scale is a confound.** A raw score target rewards extrapolating the
  layout scale; without scale variation in training, a model cannot learn it.
  The normalized target and layout-summary view reduce, but do not remove, the
  confound.
- **Tabular models are not enough.** Linear is strong in-distribution but
  collapses on the obstacle shift; the MLP is negative even in-distribution.
  The planned CNN/MPNN/Transformer baselines are the right next test.
- **The obstacle shift is severe.** It may be a challenge condition, not a
  standard benchmark; do not freeze until a model family is robust or the task
  is deliberately labeled challenge.
- **No benchmark freeze.** `factory-v0.7` is not created; `factory-v0.6`
  remains current.

## Next

1. Add a fixed-size padded grid observation (valid mask + layout descriptors)
   and run CNN/MPNN/Transformer baselines on the same layout split.
2. If a model family separates in-distribution and OOD, write a formal
   layout-shift pre-registration with fixed base/shift specs, target
   normalization, and seeds.
3. If no model is robust, keep the task as a challenge or cut the obstacle
   shift; do not tune 0097 after this pilot.

## Artifacts

- RFC 0033 / ADR 0044
- Raw pilot: `/tmp/opencode/layout-shift-pilot4/` (not checked in)
