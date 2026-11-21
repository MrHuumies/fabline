# The testbed

This document defines what FABLINE is trying to be, who it serves, and how we
judge it. It sits above the world, data, and benchmark specs.

## What a testbed is

A testbed is not a dataset and not a game. It is a **controlled environment plus
a protocol**:

- a world with known mechanics and known ground truth;
- observation and action interfaces that can be varied independently;
- tasks that isolate phenomena;
- a data format that preserves reproducibility;
- an evaluation harness that compares methods fairly.

The world is the content. The testbed is the contract around it.

## The product

The durable artifacts are:

1. **The environment API** — reset, step, state, observations, actions, masks.
2. **The task suite** — frozen tasks, splits, metrics, and baselines.
3. **The data format** — replay, materialized observations, annotations, cards.
4. **The harness** — training, evaluation, cost accounting, reports.
5. **The world** — mechanics and content that make the tasks meaningful.

Code, art, and progression can change. The contracts should change rarely and
with versioning.

## Who it serves

- **Future you**, running a new theory six months from now without rebuilding
  the world.
- **Collaborators**, who need to add a method or task without reading the whole
  simulation.
- **Methods**, which should plug into a task without special cases in the core.
- **Humans**, who want to watch, play, debug, and generate demonstrations.

## The five contracts

### 1. World contract

The world exposes a canonical, factored state and a deterministic transition
function. It does not know about observations, rewards, or ML.

### 2. Observation contract

Observations are pure functions of state. Multiple adapters can exist for the
same state: grid, vector, graph, pixels, text, multi-view. Each has a version,
a spec, and a cost.

### 3. Action contract

Actions are typed and parameterized. Legality is explicit via masks. The same
world can support discrete, parameterized, macro, and continuous action
adapters.

### 4. Task contract

A task is a projection: observation adapter(s) + action adapter + label/reward +
termination + split + metrics + baselines. The same episode can serve multiple
tasks.

### 5. Evaluation contract

Every result pins the world, observation, task, dataset, benchmark, and baseline
versions. Seeds, compute budgets, and confidence intervals are reported. The
benchmark is frozen and immutable per release.

## What makes a good testbed

| Property | What it means | How we check it |
|---|---|---|
| Coverage | Supports several research axes | Task matrix in `research-axes.md` |
| Control | Can isolate the phenomenon | Ablations and negative controls |
| Reproducibility | Same seed and actions give the same result | State hash and replay tests |
| Extensibility | New task or adapter without core changes | Add-a-task exercise |
| Cost | Fast enough to iterate | Ticks/sec and data throughput |
| Legibility | A human can understand why | Replay viewer and event log |
| Ground truth | Latents and causes are known | Probes and counterfactuals |
| Fun | The world sustains the project | Playtests and human data |

## How we judge the testbed

The testbed succeeds when:

- a new task can be added in under a day;
- five methods can be run on five tasks with one command;
- every episode replays exactly;
- every task has a baseline and a card;
- at least three observation adapters and three task families work end-to-end;
- a method that fails produces a useful boundary, not a dead end.

The testbed fails when:

- only one method can use it;
- the world's quirks dominate every result;
- tasks are saturated or ambiguous;
- adding a task requires editing the simulation;
- results cannot be reproduced;
- the game shell and the benchmark core are entangled.

## Small world, deep tasks

Do not simulate everything. A factory with a few resources, machines, and
procedural layouts can support dozens of tasks. Depth comes from:

- observation variants (full, partial, noisy, delayed, multi-view);
- action variants (discrete, macro, continuous);
- task variants (supervised, self-supervised, control, planning, causal);
- split variants (random, compositional, distribution shift, temporal);
- ground-truth annotations (latents, causes, counterfactuals).

Content volume is not the goal. Controlled complexity is.

## Relation to the game shell

The game shell is a client of the testbed:

- it uses the same core and the same data;
- it adds progression, art, UI, and human play;
- it never changes benchmark behavior;
- it can be versioned and released separately.

The benchmark core is frozen and minimal. The shell is allowed to be fun.
