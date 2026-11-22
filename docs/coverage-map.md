# Coverage map — model families, benchmarks, and mechanics

- **Status:** living design document
- **Date:** 2026-11-21
- **Purpose:** choose world mechanics and benchmarks because they expose a
  specific model weakness, not because they add content or serve one consumer.
- **Related:** [`testbed.md`](testbed.md), [`research-axes.md`](research-axes.md),
  [`coverage-review-0.1.2.md`](coverage-review-0.1.2.md),
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
| partial throughput | regression | masked vector window | 60% dropout; history recovers ~70% |
| reliability contract | risk selection | aggregate power | mean/CVaR trade replicated |
| wired cascade | regression | wire/entity graph | graph cut is learnable |
| wire repair | control | ranked wire slots | budgeted prioritization |
| preventive wire | control | degraded wire | warning makes repair actionable |
| preventive machine | control | diagnostics | delayed-credit Q is unstable |
| maintenance threshold | bandit | context | representation fix; deterministic |

### Current baselines

- mean / persistence;
- linear / ridge;
- GBDT;
- MLP;
- `graph_mp` message-passing features;
- scripted, random, tabular Q, behavior cloning.

**Representative families added in P0/P1:** CNN, end-to-end GNN/MPNN,
Transformer, GRU/RNN, calibration, CVaR/risk selection, and bandits. Still
missing: world model, deep RL, offline RL beyond behavior cloning, multi-agent
RL, and generative models.

### Current benchmark families

| Family | Coverage | Read |
|---|---|---|
| Supervised tabular | strong | throughput, bottleneck, faults, power |
| Spatial | partial | masked-grid, grid next-state; small fixed layouts |
| Relational | partial | graph_mp and end-to-end MPNN on debug tasks; no frozen graph benchmark |
| Temporal / sequence | partial | next-state and control-dynamics; short horizons |
| Event detection | partial | fault onset; aggregate views |
| Control / RL | partial | small discrete tasks; no deep RL |
| Offline / imitation | partial | scripted demos + BC; no offline RL or shift |
| Planning / world models | absent | no planning or rollout benchmark |
| Causal / counterfactual | partial | bottleneck labels; no intervention benchmark |
| Self-supervised | strong | next-state, masked-grid, control-dynamics |
| Robustness / OOD | partial | scenario splits; stochastic power |
| Uncertainty / calibration | partial | calibration metrics for stochastic power; maintenance forecasts uncalibrated |
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
| GNN / MPNN | permutation invariance, message passing | `graph_mp` features and an end-to-end MPNN (debug) | multi-hop constraints, global resources, planning | wired planning, multi-agent |
| Transformer | long-range attention, set/sequence flexibility | masked-window sequence task | locality, sample efficiency, long rollouts | sequence/relational tasks |
| RNN / GRU / LSTM / SSM | temporal memory | masked-window GRU | partial observability, delays, event timing | longer event sequences |
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
| Transformer | ○ | ○ | ◐ | ◐ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
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
   observation masks on existing tasks. Wrappers are implemented. A masked
   feature-window task now shows the intended effect: a single masked frame
   loses R²; a 4-frame window recovers about 70% for linear/GBDT. See
   [experiment 0024](experiments/0024-masked-window/summary.md).
3. **Calibration and risk:** calibration metrics are implemented for stochastic
   power (Brier, NLL, ECE). Risk-sensitive control is implemented as a
   reliability-contract task and replicated on fresh seeds (+17.05 CVaR
   [13.25, 21.15] for a 4.59 mean premium). See
   [0022](experiments/0022-calibration-stochastic-power/summary.md) and
   [0031](experiments/0031-contract-confirm/summary.md).

### P1 — wired power and preventive maintenance (complete)

P1 added an opt-in wire-edge graph with branches and loops, bridge/loop faults,
cascade-size prediction (0032), budgeted repair (0033), timed repair (0034),
preventive wire maintenance (0035), preventive machine maintenance (0037), and
maintenance-threshold selection (0038). The risk-score noise (0036) and
contextual-threshold (0039) pilots were negative and are not promoted.

The remaining P1 question is **spatial scheduling with one crew and travel
time**. It is preregistered as experiment 0040 (RFC 0010, ADR 0020). If it does
not produce a meaningful travel-aware gain, stop P1 and move to P2.

The alternative remains:

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
- **Partial-observability wrappers:** done. Pure-delay pilot saturated (0023);
  masked feature-window task passes its gates (0024).
- **Representative baselines:** complete for P0. Sequence baselines are a
  bounded negative (0025); grid CNN nearly solves the clear grid but is less
  fog-robust than flattened MLP (0026); end-to-end MPNN transfers on the
  compositional split but trails `graph_mp` by 0.09 (0027). Flattened views
  collapse on the held-out combination while relational views stay positive.
- **Risk-sensitive control:** complete for P0. The first two
  reliability-contract experiments (0028, 0029) had a sampling defect: block
  expansion overlapped adjacent blocks, so train/test were not disjoint. The
  fixed design (0030) aligned the distributions and measured +13.55 [10.50,
  16.95]. The fresh-seed confirmation (0031) passed all gates with +17.05
  [13.25, 21.15] for a 4.59 mean premium. The task is offline selection with a
  fixed operating policy; it is a P0 benchmark candidate, not part of frozen
  `factory-v0.1`.
- **P0 coverage is complete.** Calibration, partial observability,
  representative architecture baselines, and risk-sensitive control are all
  implemented and documented.
- **P1 wired power:** phase 1A and 1B complete. Cascade-size `graph_mp` R²
  0.431 vs vector 0.264 (0032). Budgeted wire repair: outage-ranked policy 260
  vs noop 79; tabular Q 212 with zero wasted repairs (0033). With 60-tick
  repairs, Q matches outage-ranked repair 223.2 and succeeds on every seed, but
  the repair-order gate fails (+2.4 vs +10); repair time matters, order is not
  robust (0034). Preventive maintenance makes a warning actionable: early repair
  260 vs reactive 185.6 vs noop 113.6; Q learns prevention on every seed (0035).
  Noisy warnings, multi-wire scheduling, and machine-wear prevention are
  follow-ups. A risk-score noise pilot found only a small prediction effect and
  is not promoted (0036). Preventive machine maintenance (0037) is a split
  result: threshold maintenance 250 vs noop 200, but Q collapses to
  always-maintain on three of five seeds and H2 fails. A threshold meta-action
  (0038) fixes the representation: UCB/epsilon select 0.7/0.8 and score 250,
  +72 over per-step Q. A contextual-threshold pilot found only +5 over the best
  fixed arm and is not promoted (0039). See the
  [0.1.2 coverage review](coverage-review-0.1.2.md) for the full read and the
  recommended next slice (per-entity crew scheduling with travel).

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

- Does per-entity crew scheduling with travel produce a travel-aware gain, or is
  impact-only already sufficient?
- Can multi-agent work on the current 16×8 layout, or does it need a larger
  world?
- Which efficiency metrics belong in the public benchmark?
- Should maintenance/repair forecasts get calibration metrics, or is power
  calibration enough?
- Is a world-model/planning benchmark feasible on the current action space?

## Maintenance

Update this map when a task is added, retired, or found saturated. The map
should stay short enough to read in one sitting and specific enough to choose
the next mechanic without another strategy debate.
