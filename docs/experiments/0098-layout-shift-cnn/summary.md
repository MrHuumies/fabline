# Experiment 0098 — Layout-shift CNN follow-up

- **Status:** positive model-family pilot; layout-shift candidate; no freeze
- **Date:** 2026-11-28
- **Type:** 0.8.0 spatial grammar, first slice follow-up
- **Task:** layout-shift throughput (draft; no benchmark)
- **Code:** `src/fabline/harness/layout_shift.py`,
  `src/fabline/obs/layout.py`, `src/fabline/tasks/throughput.py`
- **CLI:** `python -m fabline layout-shift --observation padded-grid --normalize-target`
- **Benchmark:** none; `factory-v0.6` unchanged; `factory-v0.7` not frozen

## Result in one paragraph

**The padded-grid CNN is the first model that generalizes across layouts.** On
the 0097 layout split, the CNN reaches **0.905** test R² on base layouts and
**0.785 / 0.792 / 0.857** on the large, random, and obstacle shifts — gaps of
**0.119 / 0.113 / 0.047**. The tabular layout-summary models from 0097 had base
0.67 and collapsed on large/obstacle shifts (−0.99 / −18.8). The task is a
valid benchmark candidate, but this is a pilot: the formal block needs fresh
layout seeds, and MPNN/Transformer baselines are still missing. `factory-v0.7`
is not frozen.

## Setup

Same layout split as 0097: base 16×8, 20×12, 24×16 twin; shifts 32×24 spread,
24×20 random twin, 24×20 obstacle-heavy; 12/4/4 base train/val/test layout
seeds; 8 shift seeds. Target: future score per production line. Observation:
padded 24×32×14 grid (6 grid channels + valid mask + 7 layout descriptors).
CNN: 50 epochs, hidden 32, 14,401 parameters, 30.5 s training.

## Results

| Shift | CNN test R² | CNN shift R² | Gap |
|---|---:|---:|---:|
| large 32×24 | 0.905 | 0.785 | 0.119 |
| random 24×20 | 0.905 | 0.792 | 0.113 |
| obstacles 24×20 | 0.905 | 0.857 | 0.047 |

Gates: H1 base skill pass, H2 OOD gap pass, H3 no seed leakage pass, H4 metrics
complete pass.

## Comparison to 0097

| Model | Base test R² | Large shift | Random shift | Obstacle shift |
|---|---:|---:|---:|---:|
| linear (layout-summary) | 0.670 | −0.991 | 0.595 | −18.808 |
| MLP (layout-summary) | −0.236 | −4.624 | −0.294 | −0.826 |
| **CNN (padded grid)** | **0.905** | **0.785** | **0.792** | **0.857** |

The CNN is robust where the tabular models are not. The obstacle gap is small
(0.047); the large/random gaps are ~0.11, which is the useful OOD signal.

## Interpretation

- **The layout representation matters.** A fixed padded grid with a valid mask
  and layout descriptors gives the CNN enough structure to generalize.
- **The task is a valid spatial candidate.** The model ordering is meaningful
  (CNN > linear > MLP on shift), and the OOD gap is material but not trivial.
- **Pilot only.** The layout seeds are the same as 0097; a formal block needs
  fresh layout seeds. MPNN/Transformer are still missing.
- **No benchmark freeze.** `factory-v0.7` is not created; the formal
  pre-registration and fresh-seed block are next.

## Next

1. Write a formal layout-shift pre-registration with fresh layout seeds,
   fixed base/shift specs, the per-line target, and CNN + tabular baselines.
2. Add MPNN/Transformer baselines (or record them as a documented scope cut).
3. Run the formal block; freeze `factory-v0.7` only if the OOD gap and model
   ordering replicate.
4. Do not tune 0098 after this pilot.

## Artifacts

- RFC 0033 / ADR 0044
- Raw pilot: `results/layout-shift-cnn/` (ignored)
