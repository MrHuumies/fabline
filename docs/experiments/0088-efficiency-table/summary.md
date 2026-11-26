# Experiment 0088 — Public efficiency table

- **Status:** complete
- **Date:** 2026-11-26
- **Type:** efficiency/release-quality report
- **Task:** `factory.efficiency.v1` (descriptive, not a benchmark task)
- **Code:** `src/fabline/harness/efficiency.py`
- **CLI:** `python -m fabline efficiency`
- **Table:** [`docs/efficiency.md`](../../efficiency.md)
- **Benchmark:** none; `factory-v0.2` unchanged

## Result in one paragraph

**The efficiency table is now reproducible and public.** On a fixed 18-episode,
297-sample dataset, world throughput is **45,167 ticks/s**, vector observations
**46,373/s**, grid observations **8,476/s**, and entity observations
**30,884/s**. Model fit medians range from 0.0000 s (mean/majority/copy) to
1.19 s (bottleneck GBDT); artifact sizes range from 0.1 KB to 923.5 KB. The
table is descriptive, not a leaderboard: timings are machine-dependent, the
dataset is small, and the fit budget is not a converged benchmark budget.

## Method

- Fixed in-memory shared dataset: 16×8 gear lines, 200-tick episodes, 10-tick
  sampling, 18 episodes / 297 samples.
- Tasks: throughput-vector regression, bottleneck classification, masked-grid
  self-supervised.
- Baselines: mean/majority/copy, linear, GBDT, MLP.
- Metrics: median fit time, predict µs/row, pickle artifact size, tracemalloc
  peak; world ticks/s and observation adapters/s.
- Repeats: 3.

## Headline table

See [`docs/efficiency.md`](../../efficiency.md) for the full table.

| Path | Rate |
|---|---:|
| world ticks | 45,167/s |
| vector observation | 46,373/s |
| grid observation | 8,476/s |
| entities observation | 30,884/s |

## Caveats

- Descriptive, not a leaderboard; timings are machine-dependent.
- Small fixed dataset; fit time is not a converged training budget.
- Artifact bytes are a pickle-size proxy, not deployment memory.
- No GPU or Torch baselines in this slice.
- Efficiency is not the testbed's success criterion.

## Next

1. Keep `factory-v0.2` and `v0.3.0` unchanged.
2. Remaining release-quality work is viewer QoL (replay browser/task-card
   viewer).
3. A deeper efficiency study (GPU, Torch, larger budgets) is a separate scope.
