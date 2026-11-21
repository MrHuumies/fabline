# Project intent

This document is the anchor. If a proposed feature, experiment, or refactor
does not serve this document, it is probably scope drift. Changes to this file
require explicit approval from the human owner.

## One sentence

Build a deterministic, inspectable factory world that generates reproducible
multi-view data and a method-agnostic benchmark harness for testing learning
methods, representations, and theories.

## The problem

Research on modularity, composition, continual learning, world models, and
efficiency needs worlds where the data-generating process is known, the tasks
are controlled, and the same episode can be viewed through different observation
and action interfaces. Public datasets are static snapshots; they cannot test
view arrival, retention under distribution shift, or counterfactual structure.

## Goals

1. **A small, legible factory world.** Enough mechanics to support many tasks,
   small enough to understand and simulate quickly.
2. **A canonical state with derived observations.** One simulation state; many
   observation adapters and task projections.
3. **Reproducible data.** Seeded, deterministic, replayable; materialized
   observations on demand.
4. **A method-agnostic harness.** Frozen task suites, baselines, metrics, compute
   accounting, and standard reports.
5. **Ground truth for diagnosis.** Latents, causal structure, events, and
   counterfactuals available for probing and analysis.
6. **Extensibility.** A new mechanic, observation, or task should be addable
   without rewriting the core.
7. **A playable and watchable shell.** The world should be fun enough to sustain
   the project and useful for demonstrations and human data.

## Non-goals

- Proving a single mechanism. The testbed is method-agnostic.
- A commercial game or a photorealistic simulation.
- An AGI project, a general-intelligence claim, or a leaderboard chase.
- A universal framework for every ML method.
- Multiplayer, fluids, trains, or full circuit networks before the core works.
- A content treadmill before the first benchmark suite exists.
- Large-scale scaling; the interesting behavior is in the interface and the
  loop, not the parameter count.

## Success criteria

By the end of M2:

- three task families run end-to-end on the same world: supervised,
  self-supervised, and control;
- at least three observation adapters exist: grid, vector, and graph;
- a new task can be added in under a day without touching the world core;
- a benchmark CLI runs multiple methods on multiple tasks with fixed seeds and
  produces a standard report;
- any episode replays exactly from seed plus action log;
- headless generation meets the performance policy: 10k factory ticks/s is the
  reference target, 1k ticks/s is the supported-machine floor, and no change may
  regress the same machine by more than 20%; hardware and measured rates are
  recorded with every result;
- every task has a documented baseline, split, and task card.

By the end of M4:

- a playable viewer exists and uses the same core;
- human demonstrations can be recorded and replayed;
- the benchmark core is frozen and versioned independently of the game shell.

## Design principles

1. **Canonical state, derived views.** The simulation does not know about ML.
   Observations, rewards, labels, and splits are adapters.
2. **Headless first.** The core runs without a renderer. Rendering is read-only.
3. **Determinism is a feature.** Fixed timestep, seeded RNG, stable IDs, ordered
   updates, state hashing, exact replay.
4. **Small world, deep tasks.** Add task structure and observability variants
   before adding content volume.
5. **Data-driven content.** Mechanics, recipes, maps, and tasks live in data
   files where practical.
6. **Measure before claiming.** Baselines, seeds, confidence intervals, compute
   budgets, and pre-registered gates.
7. **Negative results count.** A method that fails is a boundary, not a failed
   project.
8. **Version everything.** World, observation, task, dataset, benchmark, and
   baseline versions are part of every result.
9. **Fun is a means.** The game shell sustains the project; it must not leak
   into the benchmark core.
10. **One mechanism per milestone.** Do not mix unrelated changes in one pass.

## Drift alarms

These are signs of scope drift. They are not automatically wrong, but they
require a conversation and an ADR.

- "Let's add fluids/trains/pathfinding before the core loop works."
- "Let's make it 3D because it will look better."
- "We need a bigger world" before the current one is measured.
- "The benchmark score is the goal."
- "We'll add tests and docs after the prototype."
- "Let's tune the world until the method wins."
- "Let's support every ML method before we have one working task."
- "One method would work if we just changed the world."
- "The game needs progression before the data pipeline is reproducible."
- "One more mechanic will make the benchmark interesting."

## Relationship to prior work

- `devec`: the four locks (composition, credit, drift, retention). Use them to
  judge whether a task gives a modular method room.
- `circlenn`: a small inspectable world, deterministic runs, renderer
  separation, ADRs, pre-registration, and honest negative results. Reuse the
  practices, not the ring.

## Change protocol

Changes to this file need owner approval. Other behavior or scope changes need
an ADR, a test, and a docs update. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
