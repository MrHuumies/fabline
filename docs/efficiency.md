# FABLINE efficiency table

Generated with `fabline efficiency`; Python 3.12.3, NumPy 2.5.5, processor x86_64.

Dataset: 18 episodes, 297 samples. Repeats: 3. Descriptive only; timings are machine-dependent.

Reproduce with:

```bash
.venv/bin/python -m fabline efficiency --out results/efficiency --repeats 3
```

The fixed dataset is generated in memory (no committed dataset): 16×8 gear
lines, 200-tick episodes, 10-tick sampling. Fit/predict timings are medians of
three runs; artifact bytes are pickle size; peak memory is `tracemalloc` during
one fit. The table is descriptive, not a leaderboard or a converged training
budget.

## World and observations

| path | rate |
|---|---:|
| world ticks | 45167/s |
| vector observation | 46373/s |
| grid observation | 8476/s |
| entities observation | 30884/s |

## Models

| task | model | rows | features | fit (s) | predict (µs/row) | artifact (KB) | peak (MB) |
|---|---|---:|---:|---:|---:|---:|---:|
| throughput-vector | mean | 198 | 18 | 0.0000 | 0.14 | 0.1 | 0.00 |
| throughput-vector | linear | 198 | 18 | 0.0002 | 0.80 | 0.4 | 0.08 |
| throughput-vector | gbdt | 198 | 18 | 0.3651 | 186.12 | 185.4 | 0.68 |
| throughput-vector | mlp | 198 | 18 | 0.4609 | 11.94 | 34.3 | 0.25 |
| bottleneck | majority | 198 | 18 | 0.0001 | 0.15 | 0.2 | 0.00 |
| bottleneck | gbdt | 198 | 18 | 1.1903 | 629.15 | 602.0 | 1.34 |
| bottleneck | mlp | 198 | 18 | 0.4783 | 17.65 | 37.6 | 0.24 |
| masked-grid | copy | 198 | 768 | 0.0000 | 0.28 | 0.1 | 0.04 |
| masked-grid | linear | 198 | 768 | 0.0149 | 7.35 | 865.3 | 5.16 |
| masked-grid | mlp | 198 | 768 | 0.3159 | 17.00 | 923.5 | 3.03 |

## Caveats

- Descriptive, not a leaderboard; timings are machine-dependent.
- Small fixed dataset; fit time is not a converged training budget.
- Artifact bytes are a pickle-size proxy, not deployment memory.
- No GPU and no Torch baselines in this slice.
