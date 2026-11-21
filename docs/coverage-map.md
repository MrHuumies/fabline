# Coverage map — model families, benchmarks, and mechanics

- **Status:** living design document
- **Date:** 2026-11-21
- **Purpose:** choose world mechanics and benchmarks because they expose a
  specific model weakness, not because they add content or serve one consumer.
- **Related:** [`testbed.md`](testbed.md), [`research-axes.md`](research-axes.md),
  [`benchmarks/factory-v0.1/card.md`](../benchmarks/factory-v0.1/card.md)

## How to use this map

A task is **diagnostic** when it separates model families or exposes a boundary:
a family that should win does win, or a family that should fail fails for the
predicted reason. A task that every reasonable model solves is a control, not a
headline benchmark.

Rules for adding a mechanic or task:

1. Name the model weakness it should expose.
2. Name the benchmark family and the baseline families.
3. Fix the observation, action, label, split, metric, and version first.
4. Add a task card and, for research claims, a pre-registration.
5. Keep new mechanics opt-in so `factory-v0.1` stays frozen.
6. Report negative and saturated results first.
7. Do not add content volume without a diagnostic question.

This document is a map, not a commitment to implement every row.

## Current FABLINE surface

### Tasks

| Task | Kind | Observation | Status |
|---|---|---|---|
| throughput-vector | regression | vector | strong linear signal |
| throughput-grid | regression | grid | learned baselines fail to generalize |
| throughput-entities | regression | graph/entities | `graph_mp` helps; flattened baselines fail |
| next-state | self-supervised | vector | saturated by copy/linear |
| masked-grid | self-supervised | grid | useful spatial task |
| bottleneck | classification | graph/vector | counterfactual labels |
| expand-control | control | control view | small discrete construction puzzle |
| control-dynamics | self-supervised | control view | action-conditioned dynamics |
| fault prediction | classification | vector/diagnostics | easy for GBDT |
| fault onset | detection | sensors/entity views | small acoustic signal |
| fault recovery | control | diagnostics | two-action repair task |
| power brownout | classification | vector/power | easy for GBDT |
| power allocation | control | power/line | three-action priority task |
| fault + power | control | fault-power | four-action repair + priority task |

### Current baselines

- mean / persistence;
- linear / ridge;
- GBDT;
- MLP;
- `graph_mp` message-passing features;
- scripted, random, tabular Q, behavior cloning.

**Missing representative families:** end-to-end CNN, GNN/MPNN, Transformer,
RNN/SSM, world model, deep RL, offline RL, multi-agent RL, generative models.

### Current benchmark families

| Family | Coverage | Read |
|---|---|---|
| Supervised tabular | strong | throughput, bottleneck, faults, power |
| Spatial | partial | masked-grid, grid next-state; small fixed layouts |
| Relational | partial | graph view exists; no end-to-end GNN baseline |
| Temporal / sequence | partial | next-state and control-dynamics; short horizons |
| Event detection | partial | fault onset; aggregate views |
| Control / RL | partial | small discrete tasks; no deep RL |
| Offline / imitation | partial | scripted demos + BC; no offline RL or shift |
| Planning / world models | absent | no planning or rollout benchmark |
| Causal / counterfactual | partial | bottleneck labels; no intervention benchmark |
| Self-supervised | strong | next-state, masked-grid, control-dynamics |
| Robustness / OOD | partial | scenario splits; stochastic power |
| Uncertainty / calibration | partial | stochastic power; no calibration metrics |
| Efficiency | partial | cost experiments; not in the public benchmark |
| Multi-agent | absent | no shared-agent tasks |
| Generative | absent | no layout/recipe generation task |

## Model-family map

| Family | Inductive bias | Current diagnostics | Where it should fail | Candidate mechanic |
|---|---|---|---|---|
| Linear / ridge | additive, local linearity | next-state, throughput | nonlinear interactions, bottlenecks, faults | dynamic recipes, faults |
| MLP | dense feature interactions | throughput, fault/power classification | relational structure, variable entities, long horizons | graph/sequence tasks |
| GBDT | axis-aligned thresholds | throughput, bottleneck, faults, power | smooth dynamics, extrapolation, spatial structure | layout shift, continuous control |
| CNN | local spatial weight sharing | masked-grid | long-range dependencies, topology, variable layouts | larger maps, wired power |
| GNN / MPNN | permutation invariance, message passing | `graph_mp` features only | multi-hop constraints, global resources, planning | wired power, multi-agent |
| Transformer | long-range attention, set/sequence flexibility | not benchmarked | locality, sample efficiency, long rollouts | sequence/relational tasks |
| RNN / GRU / LSTM / SSM | temporal memory | not benchmarked | partial observability, delays, event timing | fog/delay/dropout |
| World model | action-conditioned rollout | not benchmarked | compounding error, stochasticity, constraints | planning benchmark |
| Model-free RL | sequential credit assignment | small tabular/scripted tasks | sparse rewards, partial observability, multi-objective | deadlines, multi-agent |
| Offline RL / BC | offline policy learning | scripted demos + BC | distribution shift, extrapolation, recovery | offline shift tasks |
| Multi-agent RL | coordination/communication | none | shared resources, partial views, agent failure | multi-agent workers |
| Causal models | interventions and counterfactuals | bottleneck labels | delayed effects, confounding, multiple mechanisms | intervention tasks |
| Generative models | distribution matching | none | validity, diversity, constraint satisfaction | layout/recipe generation |

## Model × benchmark matrix

`●` a diagnostic task exists (the family baseline may be missing), `◐` partial
or related coverage, `○` absent, `×` saturated.

| Model family | Tabular | Spatial | Relational | Temporal | Control | Planning | Causal | Robustness | Uncertainty | Multi-agent | Generative |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Linear | ● | ○ | ○ | ◐ | ◐ | ○ | ○ | ◐ | ○ | ○ | ○ |
| MLP | ● | ● | ◐ | ◐ | ● | ○ | ○ | ◐ | ◐ | ○ | ○ |
| GBDT | ● | ◐ | ○ | ◐ | ◐ | ○ | ○ | ◐ | ◐ | ○ | ○ |
| CNN | ○ | ● | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| GNN / MPNN | ○ | ◐ | ◐ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| Transformer | ○ | ◐ | ◐ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| RNN / SSM | ○ | ○ | ○ | ◐ | ◐ | ○ | ○ | ○ | ○ | ○ | ○ |
| World model | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| Model-free RL | ○ | ○ | ○ | ○ | ◐ | ○ | ○ | ○ | ○ | ○ | ○ |
| Offline RL / BC | ○ | ○ | ○ | ○ | ◐ | ○ | ○ | ○ | ○ | ○ | ○ |
| Multi-agent RL | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| Causal model | ○ | ○ | ◐ | ○ | ○ | ○ | ◐ | ○ | ○ | ○ | ○ |
| Generative | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |

The matrix says the largest gaps are **planning/world models, multi-agent,
partial observability, end-to-end relational/temporal models, calibration, and
public efficiency benchmarks**. More tabular throughput tasks would add little.

## Candidate mechanics

Scores are qualitative: **diagnostic value**, **reuse of existing code**, and
**cost**. Priority is P0 (do first), P1 (next), P2 (larger), P3 (optional).

| Mechanic | Weaknesses exposed | Benchmark types | Reuse | Cost | Priority |
|---|---|---|---|---|---|
| Partial observability: fog, delay, dropout | memory, belief state, rollout under uncertainty | POMDP control, state estimation, delayed prediction | high | low | **P0** |
| End-to-end relational/temporal baselines (no world change) | GNN, Transformer, RNN/SSM, world model | graph/sequence next-state, forecasting | high | low | **P0** |
| Calibration on stochastic power | calibration, risk sensitivity, robustness | calibration, risk-sensitive control | high | low | **P0** |
| Larger/random layouts | CNN receptive field, systematic generalization | layout shift, scale transfer | high | low | **P1** |
| Wired power topology and cascades | graph constraints, long-range dependence, failure propagation | cascade prediction, topology repair, constrained allocation | medium | medium | **P1** |
| Stochastic faults and sensor noise | calibration, robust control, anomaly detection | fault detection, risk-sensitive repair | high | low | **P1** |
| Multi-agent workers/vehicles | coordination, communication, credit assignment, partial views | cooperative control, communication limits, agent failure | low | high | **P2** |
| Routing / trains / long-distance logistics | long-horizon planning, nonlocal dependencies | routing, build-order, throughput under delay | low | medium | **P2** |
| Dynamic recipes / byproducts / queues | compositional generalization, constraint satisfaction | multi-input crafting, scheduling, transfer | medium | medium | **P2** |
| Deadlines / contracts / markets | credit assignment, multi-objective trade-offs | scheduling, auction/market control | low | medium | **P3** |
| Adversarial disruptions / sabotage | robustness, recovery, anomaly detection | attack/repair, anomaly detection | medium | medium | **P3** |
| Weather/environment effects | distribution shift, sensor/power robustness | shifted prediction and control | medium | medium | **P3** |
| Generative layout/recipe tasks | distribution matching, validity, diversity | layout/recipe generation | low | medium | **P3** |

## Prioritized roadmap

### P0 — no world changes

1. **Add representative baselines:** end-to-end GNN/MPNN, Transformer,
   CNN, and RNN/SSM on the existing graph, grid, and sequence tasks. This tests
   whether current tasks discriminate architectures before adding mechanics.
2. **Partial observability wrappers:** fog, delayed sensors, dropout, and
   observation masks on existing tasks. This exposes memory and belief-state
   weaknesses cheaply.
3. **Calibration and risk:** calibration metrics are implemented for stochastic
   power (Brier, NLL, ECE); risk-sensitive control variants are still future
   work. See [experiment 0022](experiments/0022-calibration-stochastic-power/summary.md).

### P1 — one small extension

Choose **one**:

- **Wired power topology:** turn the radius grid into a graph with wires,
  cascading failures, and topology repair. This exposes GNN/planning weaknesses
  and reuses the power mechanic.
- **Larger/random layouts:** add scale and layout-shift splits. This exposes
  CNN/MLP generalization weaknesses and reuses the generator.

### P2 — one new mechanic

Choose **one**:

- **Multi-agent workers/vehicles:** shared resources, partial views,
  communication limits, and agent failure. This is the biggest orthogonal
  addition.
- **Routing/trains/long-distance logistics:** long-horizon planning and
  nonlocal dependencies.

### P3 — optional

Dynamic recipes, deadlines/markets, adversarial disruptions, weather,
generative layout/recipe tasks.

### P0 progress

- **Calibration metrics:** done for stochastic power (experiment 0022).
- **Representative baselines:** next.
- **Partial observability:** next.
- **Risk-sensitive control:** not started.

## What not to add yet

- more entity types without a diagnostic task;
- bigger maps without scale/shift benchmarks;
- photorealistic rendering;
- general vision or language benchmarks;
- a public leaderboard;
- mechanics that only make the game more fun;
- content that duplicates an existing saturated task.

## Decision rules

- **One weakness, one task.** If a mechanic does not name the model weakness it
  exposes, it is content, not a testbed addition.
- **Frozen benchmark stays frozen.** New mechanics are opt-in until a new
  benchmark version is deliberate.
- **Saturated tasks are controls.** Keep them, but do not headline them.
- **Prefer tasks where families fail differently.** A task where all models fail
  for the same reason is a boundary, not a discriminator.
- **Public surface stays legible.** New mechanics should be explainable in one
  card and runnable in one command.
- **Negative results count.** A failed mechanism is a boundary; report it first.

## Open questions

- Does the existing graph view support an end-to-end GNN without a new layout
  generator?
- Should partial observability be an observation wrapper or a world mechanic?
- Can multi-agent work on the current 16×8 layout, or does it need a larger
  world?
- Which efficiency metrics belong in the public benchmark?
- Is calibration a metric on existing tasks or a separate benchmark family?

## Maintenance

Update this map when a task is added, retired, or found saturated. The map
should stay short enough to read in one sitting and specific enough to choose
the next mechanic without another strategy debate.
