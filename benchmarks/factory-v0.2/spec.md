# Benchmark specification — factory-v0.2

- **Status:** frozen
- **Version:** 0.2.0
- **Date:** 2026-11-24
- **Target release:** FABLINE 0.3.0
- **World:** `factory-0.1.0` (canonical state unchanged)
- **Plan:** `compositional-v0.2`
- **Predecessor:** [`factory-v0.1`](../factory-v0.1/card.md) remains immutable
- **Freeze review:** [`freeze-review.md`](freeze-review.md)
- **Card:** [`card.md`](card.md)
- **Expected summary:** [`expected/summary.json`](expected/summary.json)
- **Runner:** `.venv/bin/python -m fabline benchmark-v02 --out results/factory-v0.2`
- **Related:** RFC 0029, ADR 0041, P3 coverage review

## Purpose

`factory-v0.1` is stable but narrow: 46 episodes, 6 test episodes, and one
control task. `factory-v0.2` widens the benchmark without changing the world:

1. **More test power:** 20 test and 20 shift episodes, each with 2,948 samples.
2. **New decision surfaces:** planning, fault-onset calibration, and causal
   intervention, alongside the strong regression/classification/control core.
3. **Explicit diagnostics:** saturated fault prediction and near-majority
   stochastic power are run and reported, but are not frozen headline tasks.

The benchmark is a new version, not a patch to `factory-v0.1`. The world,
canonical state, tick semantics, and the v0.1 assets are unchanged.

## Frozen task matrix

| Task | Kind | Observation | Why it is here |
|---|---|---|---|
| throughput-vector | regression | vector | strong tabular signal |
| throughput-grid | regression | grid | spatial generalization boundary |
| throughput-entities | regression | entities/graph | relational baseline (`graph_mp`) |
| masked-grid | self-supervised | grid | partial-observability control |
| bottleneck | classification | graph/vector | counterfactual label |
| expand-control | control | control view | small discrete construction |
| control-dynamics | self-supervised | control view | action-conditioned dynamics |
| planning-triage | planning | state + budget | true-simulator vs learned-value gap |
| fault-calibration | calibration/detection | context + sensors | event timing and probability calibration |
| causal-removal | prediction | state + intervention | interventional vs observational gap |

`next-state` is a diagnostic, not a headline task: copy/linear saturates it. It
is still produced by the shared-suite runner for continuity.

### Diagnostics (reported, not frozen)

| Diagnostic | Why it is not frozen |
|---|---|
| fault prediction (50-tick) | saturated: GBDT accuracy 1.000, Brier ≈ 0 |
| power brownout (stochastic) | near majority: balanced 0.50–0.56 |
| next-state | copy/linear saturated |
| decentralized private-view triage | local success 0.40 and private Q success 0.47 miss the 0.60 gate |
| generative layout/recipe | optional pilot not run |

Diagnostics are useful context and a regression signal for the mechanic, but
they do not define the frozen benchmark score.

## Episodes and splits

Core shared episodes:

| Split | Episodes | Scenarios |
|---|---:|---|
| train | 99 | ingot, gear, extra_ingot (33 each) |
| val | 20 | ingot, gear (10 each) |
| test | 20 | extra_gear (held out) |
| shift | 20 | shift_gear (layout shift) |
| **total** | **159** | |

- Episode ticks: 300; warmup 100; sample interval 10; horizon 50;
  bottleneck horizon 30.
- Test, shift, and train are episode-grouped; there are no frame-level splits.
- The shared-suite API supports four splits. The draft layout split is deferred;
  it is not part of the frozen v0.2 plan.
- Control tasks use their own budget: 10 evaluation episodes, 300 training
  episodes, five seeds.

Decision blocks:

| Block | Seeds | Episodes per seed/block |
|---|---|---:|
| planning-triage | 62,000–62,004 | 1 evaluation episode per seed (5 total) |
| fault-calibration | 63,000 / 63,100 / 63,200 | 40 per block (3 blocks) |
| causal-removal | 64,000 / 64,100 / 64,200 | 40 per block (3 blocks) |

Diagnostics:

| Block | Seed start | Episodes |
|---|---:|---:|
| fault prediction | 60,000 | 40 |
| power brownout | 61,000 | 40 |

## Baselines

| Family | Tasks | Notes |
|---|---|---|
| mean / persistence | regression | persistence only where meaningful |
| linear / ridge | all tabular | strong reference |
| GBDT | regression, classification, calibration | strong tabular |
| MLP | all tabular/sequence | small fixed budget |
| CNN | grid tasks | spatial bias |
| `graph_mp` | entities/relational | message-passing features |
| copy | next-state / self-supervised | continuity control |
| scripted / random | control, planning | non-learned reference |
| tabular Q / BC | control | small discrete baselines |
| random shooting / CEM | planning | model-based planning |
| ridge value model | planning | negative learned-value baseline |

Deep RL and offline RL remain optional baseline tracks, not new mechanics.
Efficiency is reported as a cost table, not a task.

## Metrics

- Regression: R², MAE, RMSE; bootstrap CIs.
- Classification/detection: AP, accuracy, balanced accuracy, macro F1.
- Calibration: Brier, NLL, ECE.
- Self-supervised: MSE and cosine.
- Control: success, score/reward, steps, build penalty.
- Planning: mean score, success, plan sequence, planning latency, model MSE.
- Causal: R² and MAE for observational vs interventional views.

The compact expected summary stores test/shift point estimates for the core
tasks, planning mean scores and per-seed scores, and calibration/causal block
values. Planning latency is reported but not compared because it is
machine-dependent.

## Freeze criteria

A task enters `factory-v0.2` only if:

- it has a task card and a pre-registration;
- it is not saturated on its headline metric;
- its baseline ordering is stable across the stated seeds;
- its expected metric can be regenerated deterministically;
- it adds a decision or diagnostic not already covered.

The benchmark is frozen when:

1. All headline tasks have expected summaries.
2. `factory-v0.1` hash and assets are unchanged.
3. 20 test and 20 shift episodes are present.
4. A CI regression check compares a run against the expected summary.
5. The benchmark card, spec, and task cards are complete.
6. A release audit verifies the public snapshot and assets.

## Runner and checks

Full frozen run:

```bash
.venv/bin/python -m fabline benchmark-v02 --out results/factory-v0.2
```

Regenerate the compact expected summary:

```bash
.venv/bin/python -m fabline benchmark-v02 --out results/factory-v0.2 \
  --expected benchmarks/factory-v0.2/expected/summary.json
```

Check a run against the expected summary:

```bash
.venv/bin/python -m fabline benchmark-v02 --out results/factory-v0.2 \
  --check-expected benchmarks/factory-v0.2/expected/summary.json
```

The check uses `rtol=0.03` and `atol=0.02`; `--skip-planning` and
`--skip-diagnostics` produce a cheap regression run for CI. The scheduled CI
workflow runs the full check. The full run is compute-heavy (roughly 20–40
minutes on the development machine) because the planning block trains its value
model and runs CEM/oracle on five seeds; the cheap check skips it.

## What is not in v0.2

- a layout split (deferred; shared-suite API still has four splits);
- next-state as a headline task;
- fault prediction and stochastic power as frozen tasks;
- decentralized multi-agent as a frozen task;
- generative layout/recipe (optional pilot not run);
- deep RL/offline RL as new mechanics;
- any change to `factory-v0.1`.

## Changelog

- 2026-11-24 — draft spec created for 0.3.0.
- 2026-11-24 — frozen at 10 headline tasks, 159 core episodes, and a compact
  expected summary; fault/power and next-state are diagnostics.
