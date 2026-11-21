# Research axes

This document lists the questions the testbed is designed to support. It is a
menu, not a commitment: not every axis needs a task in every milestone. The
point is to make the world's coverage explicit and to prevent "general testbed"
from meaning "everything and nothing."

## Axis 1 — Observation structure and modality

**Question:** How do representation and generalization change when the same
world is observed through different channels?

**Factory instantiations:**

- grid vs. entity list vs. graph vs. pixels;
- full state vs. partial observability (fog, sensor range);
- clean vs. noisy vs. delayed observations;
- single view vs. multi-view (production, power, logistics, maintenance);
- symbolic text vs. tensors.

**Example tasks:**

- predict throughput from grid vs. graph;
- classify bottlenecks from local vs. global views;
- fuse redundant views under noise;
- add a new view later and measure retention and gain.

**Methods/baselines:** MLP, GNN, CNN, transformer, late fusion, early fusion,
multi-view arrival, view-dropout training.

**Metrics:** task metric, sample efficiency, robustness to noise/delay,
view marginal value, calibration.

## Axis 2 — Task family

**Question:** Can the same world support prediction, control, planning, and
generation without duplicating data?

**Factory instantiations:**

- **supervised:** throughput, bottleneck, failure, next-state;
- **self-supervised:** masked state, next-state, contrastive views;
- **control:** build/remove/schedule to maximize output;
- **imitation:** clone scripted or human build orders;
- **planning:** find a build order for a target output;
- **generation:** produce valid layouts or recipes;
- **causal:** estimate the effect of an intervention.

**Methods/baselines:** mean predictor, GBDT, MLP, transformer, PPO/SAC, behavior
cloning, classical search, world models, generative models.

**Metrics:** task-specific; retention; transfer; success rate; optimality gap;
validity; intervention error.

## Axis 3 — Composition and transfer

**Question:** What happens when a method must combine mechanics, or acquire a new
one without losing an old one?

**Factory instantiations:**

- new recipe or machine type arrives;
- new layout constraint or resource;
- new view or sensor channel;
- new task over existing mechanics;
- compositional split: train on AB and BC, test on AC or ABC.

**Example tasks:**

- continual recipe learning with old-output retention;
- modular expansion: add a machine type without breaking the existing line;
- view arrival: add a telemetry channel to a working predictor;
- cross-layout transfer: same task, unseen map distribution.

**Methods/baselines:** joint retrain, fine-tune, adapters/LoRA, progressive
networks, replay, EWC, modular components, from-scratch.

**Metrics:** old-task retention, new-task acquisition, forward/backward transfer,
interference, sample/compute cost, capacity before degradation.

**Task-design checklist (from `devec`):**

1. **Composition lock** — the target depends on interactions, not additive cues.
2. **Credit lock** — each part alone has weak marginal signal.
3. **Drift lock** — something arrives or shifts over time.
4. **Retention lock** — old behavior must not regress.

If a task lacks the locks, a modular method has no room; say so.

## Axis 4 — Temporal structure and memory

**Question:** How do horizon, recurrence, and partial observability affect
learning and credit assignment?

**Factory instantiations:**

- short-horizon prediction vs. long-horizon production planning;
- reactive control vs. scheduling with delayed effects;
- observation history vs. memory;
- delayed rewards and delayed observations.

**Example tasks:**

- predict output 10 vs. 100 vs. 1000 ticks ahead;
- build a line whose payoff arrives after a long delay;
- recover from a fault using only past observations;
- schedule maintenance with delayed failures.

**Methods/baselines:** feed-forward, history windows, RNN/GRU, transformer,
world models, model-based planning.

**Metrics:** task metric by horizon; memory ablation; sample efficiency;
credit-assignment diagnostics.

## Axis 5 — Efficiency and cost

**Question:** Which method gives the best result per unit of sample, compute,
memory, update cost, or inference latency?

**Factory instantiations:**

- small vs. large observation encoders;
- cached vs. recomputed features;
- batch vs. streaming updates;
- frozen vs. adapted modules;
- CPU vs. GPU regimes.

**Example tasks:**

- compare sample efficiency on a fixed task;
- compare update cost after a new view or recipe arrives;
- compare inference latency at batch 1 and 256;
- compare cache size vs. accuracy trade-offs.

**Methods/baselines:** any method, with a shared cost fingerprint:
parameter count, state size, training time, update time, inference latency,
throughput, memory, cache size, forward FLOPs where available.

**Metrics:** task metric at fixed budget; cost ratio; Pareto frontier; cache
per row; energy where measurable.

## Axis 6 — Causality and intervention

**Question:** Does a model learn the causal structure or only a correlate?

**Factory instantiations:**

- known recipes and flow graph;
- interventions: remove a machine, rotate a belt, change a recipe, add a
  buffer, inject a fault;
- counterfactual branches from a saved state;
- confounds: layout style, ore density, initial conditions.

**Example tasks:**

- predict the effect of removing a machine;
- identify the causal bottleneck;
- estimate treatment effects under layout confounds;
- plan an intervention to reach a target output.

**Methods/baselines:** correlation baselines, GBDT, causal graphs, intervention
predictors, world models, planning.

**Metrics:** intervention error, counterfactual accuracy, causal discovery
quality, robustness to confounds.

## Axis 7 — Multi-agent and interaction (later)

**Question:** What changes when several agents share the factory?

**Factory instantiations:**

- workers or vehicles with local views;
- shared resources and congestion;
- cooperative build tasks;
- competitive or mixed-motive layouts.

**Example tasks:**

- coordinate two builders without collisions;
- allocate scarce power;
- share observations under communication limits.

**Methods/baselines:** independent PPO, centralized training, communication
protocols, auction/assignment baselines.

**Metrics:** team return, coordination cost, communication volume, robustness to
agent failure.

Do not start this axis before the single-agent core works.

## Cross-cutting — Robustness and distribution shift

Every axis can be stressed with:

- unseen layouts, recipes, or mechanic combinations;
- sensor noise, delay, dropout, and failure;
- source/device/render-style confounds;
- temporal drift;
- adversarial or edge-case inputs.

Report the shift explicitly. A result without a shift condition is incomplete.

## Cross-cutting — Interpretability and visualization

The world has known structure, so it supports:

- probes for latent variables and causal edges;
- attention or attribution over entities and flows;
- counterfactual replay;
- human inspection of failures.

Visualization is an instrument. It should reveal dynamics, not hide them.

## Coverage matrix

A task is worth adding when it covers an axis that no current task covers, or
when it provides a negative control for an existing claim.

| Task family | Obs. structure | Composition | Temporal | Efficiency | Causal | Multi-agent |
|---|---|---|---|---|---|---|
| throughput prediction | grid/graph/vector | low | short | medium | low | no |
| bottleneck classification | grid/graph | medium | short | low | medium | no |
| next-state prediction | any | low | short | medium | low | no |
| build control | grid/graph | medium | long | high | medium | later |
| fault recovery | partial | high | long | medium | high | no |
| power allocation | partial | high | medium | medium | high | no |
| fault + power | partial | high | long | medium | high | no |
| build-order planning | graph | high | long | high | high | later |
| recipe continual | vector/graph | high | medium | high | low | no |
| intervention effect | graph | high | medium | low | high | no |
| layout generation | grid/graph | medium | none | low | low | no |
| multi-agent build | local views | high | long | high | medium | yes |

The matrix is a design tool. Update it when a task is added or retired.
