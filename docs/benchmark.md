# Benchmark protocol

This document defines how methods are compared on FABLINE. The benchmark is a
contract: frozen tasks, frozen splits, fixed budgets, standard reports.

**Current release:** `factory-v0.2` — see
[`benchmarks/factory-v0.2/card.md`](../benchmarks/factory-v0.2/card.md). It is a
research benchmark (159 core episodes, 2,948 samples, plus planning,
calibration, and causal blocks), not a public leaderboard. `factory-v0.1`
remains frozen for provenance.

Run the current benchmark with:

```bash
.venv/bin/python -m fabline benchmark-v02 --out results/factory-v0.2
```

## Goals

- Compare methods fairly on the same world and tasks.
- Separate task performance from sample, compute, memory, and update cost.
- Make negative results and scope conditions visible.
- Keep results reproducible months later.

## Task suite

A benchmark release is a set of tasks with pinned versions:

```text
benchmark: factory-v0.2
tasks:
  - factory.throughput.predict.v1
  - factory.bottleneck.classify.v1
  - factory.build.control.v1
  - factory.planning.triage.v1
  - factory.fault.calibration.v1
  - factory.causal.remove.v1
splits: train / val / test / shift, plus decision-block seeds
seeds: fixed per task; see benchmark.toml
budgets: per task
```

Each task has a card. A task is not part of a benchmark until it has:

- a precise label or reward definition;
- a deterministic generator or episode source;
- disjoint splits;
- at least one trivial baseline and one strong baseline;
- a metric and a compute budget;
- known pitfalls.

## Splits

- **Random by episode** — never random by frame.
- **Grouped** — by layout seed, generator family, or scenario, so near-duplicates
  do not cross splits.
- **Compositional** — train on mechanic combinations AB and BC; test on AC and
  ABC.
- **Distribution shift** — unseen layouts, recipes, ore densities, noise levels,
  delays, or entity mixes.
- **Temporal** — later episodes or later world versions as test.
- **Private holdout** — a small set not used during development, if the benchmark
  is public.

Splits are generated from a manifest and validated for disjointness.

## Baselines

Every task declares its applicable baselines:

| Baseline | Use |
|---|---|
| Random / uniform | Floor for control and classification |
| Scripted expert | Strong reference and demonstration source |
| Mean / persistence | Floor for regression and next-state |
| Linear / logistic | Cheap learned baseline |
| GBDT | Strong tabular baseline |
| MLP | Standard neural baseline |
| GNN / transformer | Structured and sequence baselines |
| PPO / SAC | Control baselines |
| Behavior cloning | Imitation baseline |
| Classical search / planner | Planning baseline |

A method is not comparable unless it is run at a declared compute and data
budget. If a baseline is not applicable, say why in the task card.

## Metrics

Task metrics:

- regression: MAE, RMSE, R²;
- classification: accuracy, balanced accuracy, AP, AUROC, calibration;
- control: return, success rate, throughput, optimality gap;
- next-state: MSE, cosine, downstream probe;
- planning: success rate, plan length, optimality gap;
- causal: intervention error, counterfactual accuracy.

Cross-cutting metrics:

- **sample efficiency** — steps or episodes to a threshold;
- **compute efficiency** — wall-clock, FLOPs where available, GPU-hours;
- **update cost** — time and memory to adapt to a new task/view;
- **inference cost** — latency at batch 1 and 256, throughput;
- **retention** — old-task performance after adaptation;
- **transfer** — forward/backward transfer;
- **robustness** — performance under shift, noise, delay, dropout;
- **calibration** — reliability of predicted uncertainty.

## Protocol

1. Pre-register the question, hypothesis, conditions, seeds, budgets, metrics,
   and kill criteria.
2. Run at least 5 seeds; 10 preferred. Report mean and 95% confidence interval.
3. Use paired comparisons where possible (same seeds, same data, same budget).
4. Fix the compute budget, not just the epoch count. Report both.
5. Do not tune on the test split. Use validation for selection.
6. Report negative results in the first paragraph.
7. Record the exact versions, git commit, hardware, and config hash.
8. Keep raw JSONL/Parquet; commit summaries and configs.

## Reports

Every benchmark run produces:

- `report.md` — human-readable tables and caveats;
- `results.jsonl` — one record per run;
- `config.json` — resolved config and versions;
- `env.json` — hardware, OS, Python, library versions;
- `manifest.json` — dataset and split hashes.

A report without a config hash and version pins is not a result.

## Benchmark lifecycle

- **Draft** — tasks may change; results are exploratory.
- **Frozen** — tasks, splits, seeds, and baselines are pinned; results are
  comparable.
- **Retired** — kept for provenance; no new results.

Frozen benchmarks are immutable tags. Changes require a new version. Do not
silently edit a task and compare new results to old ones.

## Leaderboard

A local leaderboard is enough at first. If a public leaderboard is added:

- require a reproducible config and a compute declaration;
- separate tracks by budget and modality;
- allow negative and null results;
- publish the evaluation script;
- keep a private holdout.

## Anti-patterns

- comparing methods at different compute or data budgets;
- reporting a single seed;
- tuning on test;
- changing the world between methods;
- conflating a data artifact with a method result;
- hiding missing views or label leakage;
- claiming a general result from one task;
- treating the leaderboard as the project goal.
