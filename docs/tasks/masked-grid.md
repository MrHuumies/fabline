# Task card — masked grid prediction

- **Task ID:** `factory.masked_grid.predict.v1`
- **Version:** 0.1.0
- **Status:** benchmark candidate (`factory-v0.1`)
- **World:** factory-0.1.0
- **Owner:** FABLINE
- **Date:** 2026-11-21

## Phenomenon

Mask a fixed spatial patch of the grid observation and reconstruct it from the
visible context. This is a self-supervised inpainting task that tests spatial
representation and layout inference, not just temporal continuity.

## Contract

- **Observation:** `grid` (8×16×6).
- **Mask:** rows 3–5, columns 2–9, all six channels — a 3×8×6 patch (144
  values).
- **Input:** the grid with the masked patch zeroed, flattened to 768 values.
- **Target:** the masked patch values, flattened to 144 values.
- **Splits:** same scenario plan as throughput.
- **Metrics:** MSE, MAE, mean cosine with 95% bootstrap confidence intervals.
- **Baselines:** copy (zeros / current patch), linear, MLP.

## Results — `factory-v0.1`

Test:

| method | MSE | cosine |
|---|---:|---:|
| copy | 0.0603 | 0.8273 |
| linear | 0.0473 | 0.5954 |
| MLP | **0.0365** | **0.6438** |

Shift:

| method | MSE | cosine |
|---|---:|---:|
| copy | 0.0548 | 0.3387 |
| linear | 0.0659 | 0.5993 |
| MLP | **0.0254** | **0.7491** |

## Known pitfalls

- **Fixed patch:** the task tests one location. A random-patch variant is
  future work.
- **No spatial model:** linear and MLP baselines flatten the grid. A CNN or
  UNet is the natural next baseline.
- **Small data:** 110 test samples. CIs are wide.
- **The factory line is predictable:** the task is harder than vector
  masked-state but not a general inpainting benchmark.

## Negative controls

- Copy is a strong floor on the test split (cosine 0.827); a model that cannot
  beat it is not reconstructing the patch.
- The MLP beats copy on MSE and cosine; the linear model does not beat copy on
  cosine. That gap is the signal.

## Changelog

- 2026-11-21 — card created; M3 results added.
