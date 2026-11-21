# Experiment 0025 — Sequence baselines on masked-window throughput

- **Status:** complete (H1 fails; bounded negative)
- **Date:** 2026-11-21
- **Type:** P0 architecture baseline experiment
- **Task:** `factory.throughput.partial.v1`
- **Code:** `experiments/architecture_baselines/sequence_run.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.1` unchanged

## Result in one paragraph

**Sequence structure helps a little, but not enough to clear the gate, and GBDT
remains far ahead.** On the same masked-window data as 0024, flattened MLP R² is
0.577, GRU 0.608, Transformer 0.655, temporal CNN 0.248, and GBDT 0.883. The
best sequence model beats the flat MLP by **+0.078**, below the pre-registered
+0.10 gate. H2 also fails because the temporal CNN is 0.33 below the flat MLP.
The result is a scale/task boundary: four frames and 800 samples do not give
sequence models enough room to beat a strong tabular model.

## Data

Same masked-window dataset as 0024, formal seed 1:

- 800 samples; 560 / 160 / 80 train / val / test;
- 60% feature dropout, masks independent of tick;
- four recent frames of 26 features (values + mask);
- label: future depot score over 50 ticks.

## Results

Five seeds for neural models; mean test R² with 95% bootstrap intervals.

| model | params | test R² |
|---|---:|---:|
| flat MLP | 6,785 | 0.577 [0.556, 0.601] |
| GRU | 5,793 | 0.608 [0.594, 0.621] |
| Transformer | 9,569 | **0.655** [0.588, 0.722] |
| temporal CNN | 1,729 | 0.248 [0.223, 0.274] |
| GBDT reference | — | **0.883** |

The target was standardized using train mean/std before neural training; the
first unscaled run predicted near zero and was discarded as an implementation
bug.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 sequence gain | best sequence ≥ flat MLP + 0.10 | **fail**, +0.078 |
| H2 no regression | every sequence ≥ flat MLP − 0.05 | **fail**, CNN −0.329 |
| H3 seed consistency | best sequence std ≤ 0.10 | **pass**, Transformer std ≈ 0.05 |
| H4 full-view context | report reference | full view: linear 0.752, GBDT 1.000, MLP 0.613 |
| H5 budget | report params/epochs/seeds | 50 epochs, 5 seeds, params shown |

## Interpretation

- **The gate was not met.** The Transformer is the best neural model, but its
  gain over the flat MLP is 0.078, not 0.10.
- **GBDT is the strongest model for this task.** A four-frame masked tabular
  window is still a threshold-friendly representation; 560 training rows and a
  two-value label favor GBDT.
- **The temporal CNN is not useful here.** Its local convolution over four
  frames adds parameters without matching the sequence models.
- **The task is small.** 80 test rows; a 0.078 difference is within the
  uncertainty of the task. Do not overread the ordering.
- **This is a boundary, not a verdict on sequence models.** A longer sequence,
  a harder label, or a larger dataset could change the result; that would be a
  new experiment.

## Caveats

- One task, one window length, one dropout level, one data seed.
- Five neural seeds; GBDT is a deterministic reference, not a seed sweep.
- Test set 80 rows; bootstrap intervals over seeds are narrow but the task is
  small.
- The flat MLP here uses the same training budget as the sequence models; it is
  not identical to the sklearn MLP in 0024.
- No grid/CNN or entity/GNN comparison yet.

## Next

1. **Grid CNN on fogged grid** — spatial locality and occlusion.
2. **GNN/MPNN on the entity graph** — relational structure and variable
   entities.
3. Or move to a larger sequence task only if the world gains a genuinely
   longer-horizon event structure.

## Artifacts

- Code: `experiments/architecture_baselines/sequence_run.py`
- Raw results: `results/architecture_baselines/sequence/` (ignored)
- Task card: `docs/tasks/partial-throughput.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
