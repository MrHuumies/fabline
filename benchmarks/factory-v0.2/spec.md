# Benchmark specification — factory-v0.2 (draft)

- **Status:** draft; **not frozen**
- **Date:** 2026-11-24
- **Target release:** FABLINE 0.3.0
- **Related:** RFC 0029, ADR 0041,
  [`factory-v0.1`](../factory-v0.1/card.md)
- **Frozen predecessor:** `factory-v0.1` remains immutable

## Purpose

`factory-v0.1` is a stable but narrow core: 46 episodes, 6 test episodes, and
one control task. `factory-v0.2` widens the benchmark in three directions:

1. **More test power:** 20 test, 20 shift, and 20 layout episodes.
2. **More decision surfaces:** planning, decentralized multi-agent, and causal
   intervention, alongside the strong regression/classification/control core.
3. **More calibration:** fault onset and power brownout, not only power
   calibration.

The benchmark is frozen only after the candidate tasks pass their pilots. A
task that misses its gate is reported negative and excluded.

## Candidate task matrix

| Task | Kind | Observation | Why it is here |
|---|---|---|---|
| throughput-vector | regression | vector | strong tabular signal |
| throughput-grid | regression | grid | spatial generalization boundary |
| throughput-entities | regression | entities/graph | relational baseline (`graph_mp`) |
| masked-grid | self-supervised | grid | partial-observability control |
| bottleneck | classification | graph/vector | counterfactual label |
| fault onset | detection | sensors/entity views | event timing and calibration |
| power brownout | classification | vector/power | stochastic power and calibration |
| expand-control | control | control view | small discrete construction |
| control-dynamics | self-supervised | control view | action-conditioned dynamics |
| planning | planning | state + budget | world-model/rollout gap |
| decentralized multi-agent | control | local crew views | per-agent policy/communication gap |
| causal intervention | prediction | state + intervention | causal/intervention gap |

Candidate, not guaranteed:

- **Generative layout/recipe** is a stretch pilot and is not in the table.
- **Next-state** is retired from the headline because copy/linear saturates it;
  it may remain as a debug control, not a frozen task.

## Episodes and splits

Shared episodes:

| Split | Episodes | Scenarios |
|---|---:|---|
| train | 100 | ingot, gear, extra_ingot |
| val | 20 | ingot, gear |
| test | 20 | extra_gear |
| shift | 20 | shift_gear |
| layout | 20 | random_gear, spread_gear |
| **total** | **180** | |

- Episode ticks: 300; warmup 100; sample interval 10; horizon 50.
- Test, shift, and layout are episode-grouped; no frame-level splits.
- Control tasks use their own budgets; planning and multi-agent use 5 seeds ×
  20 evaluation episodes.
- The exact scenario counts are fixed at freeze, not before.

## Baselines

| Family | Tasks | Notes |
|---|---|---|
| mean / persistence | regression | persistence only where meaningful |
| linear / ridge | all tabular | strong reference |
| GBDT | regression, classification, calibration | strong tabular |
| MLP | all tabular/sequence | small fixed budget |
| CNN | grid tasks | spatial bias |
| `graph_mp` | entities/relational | message-passing features |
| copy | next-state-like/self-supervised | continuity control |
| scripted / random | control, planning, multi-agent | non-learned reference |
| tabular Q / BC | control | small discrete baselines |
| random shooting / CEM | planning | model-based planning |
| decentralized scripted / learned | multi-agent | local-view and communication |

Deep RL and offline RL are **optional baseline tracks**, not new mechanics.
Efficiency is reported as a separate cost table; it is not a task.

## Metrics

- Regression: R², MAE, RMSE; bootstrap CIs.
- Classification/detection: AP, accuracy, balanced accuracy, macro F1.
- Calibration: Brier, NLL, ECE, reliability curves.
- Self-supervised: MSE and cosine.
- Control: success, score/reward, steps, build penalty.
- Planning: plan success, budget used, rollout error, planning latency.
- Multi-agent: score, success, local/global gap, reports used.
- Causal: interventional prediction error vs observational baseline.
- Efficiency: update/inference seconds, memory, ticks/s.

## Freeze criteria

A task enters `factory-v0.2` only if:

- it has a task card, dataset card where applicable, and pre-registration;
- its pilot passes the task's named gate on at least 5 seeds;
- its baseline ordering is stable and not saturated;
- its expected metric can be regenerated deterministically;
- it adds a decision or diagnostic not already covered.

The benchmark is frozen only when:

1. All included tasks have expected summaries.
2. `factory-v0.1` hash and assets are unchanged.
3. 20 test, 20 shift, and 20 layout episodes are present.
4. CI has a regression check against the expected summary.
5. The benchmark card and spec are complete.
6. A release audit verifies the public snapshot and assets.

## Candidate TOML shape

This is a draft; values are fixed only at freeze.

```toml
[benchmark]
name = "factory-v0.2"
status = "draft"
world_version = "factory-0.1.0"  # or factory-0.2.0 if canonical state changes
target_release = "0.3.0"

[shared]
width = 16
height = 8
ticks_per_episode = 300
warmup_ticks = 100
sample_interval = 10
horizon = 50

[splits]
train = ["ingot", "gear", "extra_ingot"]
val = ["ingot", "gear"]
test = ["extra_gear"]
shift = ["shift_gear"]
layout = ["random_gear", "spread_gear"]

[episodes]
train = 100
val = 20
test = 20
shift = 20
layout = 20

[tasks]
regression = ["throughput-vector", "throughput-grid", "throughput-entities"]
self_supervised = ["masked-grid", "control-dynamics"]
classification = ["bottleneck", "fault-onset", "power-brownout"]
control = ["expand-control"]
planning = ["repair-or-build"]
multi_agent = ["decentralized-crews"]
causal = ["component-intervention"]

[control]
seeds = [0, 1, 2, 3, 4]
eval_episodes = 10

[planning]
seeds = [0, 1, 2, 3, 4]
eval_episodes = 20

[multi_agent]
seeds = [0, 1, 2, 3, 4]
eval_episodes = 20
```

## Open decisions

1. Planning task: repair sequence vs build sequence; model-based vs model-free.
2. Multi-agent task: action space and communication budget; local radius.
3. Whether canonical state changes enough to require `factory-0.2.0`.
4. Whether to include throughput-grid or replace it with layout-shift only.
5. Generative pilot: include only if validity/diversity gate passes.
6. Compute budget for 5-seed planning/multi-agent runs.

## What is not in v0.2

- next-state as a headline task (saturated);
- every P2/P3 debug task;
- generative layout unless the pilot passes;
- deep RL/offline RL as new mechanics (baselines only);
- any change to `factory-v0.1`.

## Freeze and release process

1. Pilot tasks in 0.3.0 phases.
2. Write cards and expected summaries for passing tasks.
3. Freeze `factory-v0.2` with a benchmark card and tag.
4. Run the 0.3.0 release audit.
5. Publish the public release; keep PyPI/Zenodo deferred.

## Changelog

- 2026-11-24 — draft spec created for 0.3.0; not frozen.
