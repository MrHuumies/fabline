# RFC 0032 — Sequential crew control and uncertain repair

- **Status:** accepted for 0.7.0 Phase 1 (deterministic sequential crews); 0095 valid as a challenge; `factory-v0.6` frozen; stochastic faults deferred to 0.8.0 (ADR 0043).
- **Author:** FABLINE
- **Date:** 2026-11-26
- **Related:** RFC 0011, RFC 0012, RFC 0015, RFC 0017,
  [`roadmap-0.5.0-0.8.0.md`](../roadmap-0.5.0-0.8.0.md),
  [`coverage-analysis-2026-11-26.md`](../coverage-analysis-2026-11-26.md)

## Summary

0.7.0 replaces the one-shot crew macro-action with **true sequential
per-crew control**, and adds stochastic faults/sensor noise so belief state and
calibration matter. The integrated theme is **uncertain repair**:

- crews move one cell per decision, choose targets, repair, and communicate;
- local views are radius/occlusion-limited;
- faults are stochastic/noisy and some wear is hidden;
- the task rewires the multi-agent and POMDP coverage gaps rather than adding
  another centralized assignment sweep.

This is one flagship (sequential crews) with one closer on the same surface
(stochastic faults). ADR 0043 narrows 0.7.0 to Phase 1: deterministic sequential
crews with a shared observation and no communication. The stochastic
fault/POMDP closer moves to 0.8.0.

## Why

The current crew tasks are macro-action assignments:

- a `step` often runs a job to completion and returns the final score;
- the action is a pair/one-shot assignment, not a per-agent policy;
- there is no movement, no per-crew communication action, and no repeated
  failure;
- partial per-crew visibility was binary on the 16x8 and twin-line layouts.

As a result, the benchmark has no frozen multi-agent task with a learned
per-agent policy, and POMDP control is absent. The public coverage suite still
has no multi-agent or belief-state task.

## Sequential crew mechanic

### Layout

Use a fixed or seeded repair yard with:

- 2–3 crews with distinct start cells;
- 3–5 repair targets (wires or components) at different positions;
- one or two production depots whose score depends on repaired connectivity;
- optional travel obstacles/rocks;
- a local visibility radius per crew.

The first slice can reuse the wired-power world and crew positions; the task
state (crew positions, repair progress, messages) is task-layer state, not
canonical factory state. It must be serialized for replay.

### Actions

Per crew, one action per decision:

```text
move_north, move_east, move_south, move_west, wait, repair, report
```

- `repair` is legal only when the crew is adjacent to or on a repair target;
- repair progress increments per tick while the crew stays on the target;
- `report` shares the crew's current target/status with the team, subject to a
  message budget and optional delay/noise;
- a joint action is the tuple of per-crew actions; illegal actions are masked.

The first slice can use a macro `move_to(target)` instead of four directions if
the grid path is trivial, but the sequential state must still expose position,
travel time, and repair progress. Do not fall back to a one-shot assignment.

### Observation

Per crew:

- own position and current action/progress;
- local radius view of targets, faults, and crew positions;
- received reports with age/source;
- task clock, budget, and team score.

Global observation is available only to the centralized oracle/baseline, not to
the decentralized policy.

### Reward and termination

- time-weighted restored connectivity/production;
- repair cost and aborted-job penalty;
- optional deadline/recall penalty;
- episode ends at the tick limit or mission completion;
- success threshold fixed at pre-registration.

## Stochastic fault/POMDP closer

Add an opt-in `FaultConfig` extension:

- stochastic onset hazard depends on wear, load, and maintenance;
- sensor noise/drift and false positives/negatives;
- hidden wear/fault state;
- correlated failures via shared power/load;
- optional inspect action.

Tasks:

| Task | Kind | Purpose |
|---|---|---|
| `fault-detection-noise` | detection/calibration | detect onset under noisy sensors |
| `pomdp-maintenance` | control | inspect/repair/continue with hidden wear |
| `root-cause` | prediction/causal | identify the source of a production drop |

The task layer exposes noisy sensor views; the simulator keeps the true latent
state in `info` for labels and evaluation.

## Tasks and baselines

### `crew-sequential`

- Baselines: centralized oracle, greedy/nearest/EDF, independent Q, MAPPO,
  QMIX/VDN, MADDPG, COMA, OR/CP-SAT assignment reference.
- Gates: coordination gain ≥10 over single crew; oracle gap ≥10; best learned
  success ≥0.60, or challenge tier; cost/message volume reported.

### `crew-communication`

- Baselines: no communication, shared local, delayed reports, CommNet/TarMAC/
  DIAL.
- Gates: communication gain ≥10 over no communication; message budget;
  robustness to delay/noise.

### `pomdp-maintenance`

- Baselines: threshold/reactive, HMM, Kalman/particle filter, survival model,
  belief-state RL, POMDP solver.
- Gates: detection skill over base rate; ECE ≤0.05 if calibration is claimed;
  control gain over threshold.

## Implementation phases

1. **Deterministic sequential crew** on a fixed layout, no communication.
   Tests: movement, action masks, repair progress, determinism, replay.
2. **Local views + report action** with budget/delay; communication baseline.
3. **Stochastic faults/noise** and `pomdp-maintenance`; calibration metrics.
4. **Multi-crew scaling** (3 crews, repeated failure) and challenge tier.

Each phase is a separate pre-registration; do not mix phases in one formal run.

## Risks

- **Action-space growth.** `7^N` for N crews; use legal-action masks and a
  factorized policy. Start with 2 crews.
- **Credit assignment.** Team reward with per-crew actions; report per-agent
  contribution diagnostics.
- **Task-layer state.** Crew positions/progress are not in the factory hash;
  replay must serialize the task state explicitly.
- **Communication semantics.** Define budget, delay, noise, and observation
  masking before the pilot.
- **Layout dependence.** Binary visibility on small layouts was a dead end; use
  a spread layout with graded distance/occlusion.
- **Scope.** The combined sequential + stochastic theme may be too large; split
  if a phase misses its gate.

## Kill criteria

- If sequential crews do not add a coordination/communication gain over the
  existing one-shot tasks, retire the sequential variant.
- If stochastic faults do not change decisions or calibration, retire them as a
  diagnostic.
- If the 2-crew action space cannot be learned above random, publish as a
  challenge task; do not tune indefinitely.

## Decision

Accepted for 0.7.0 Phase 1: deterministic sequential crews, two crews and five
target wires, six actions (no `report`), shared observation, and no
communication. ADR 0043 records the WIP audit and the required tests, CLI,
oracle, and threshold calibration. Stochastic faults/POMDP are deferred to
0.8.0. The 0093 (3 targets) and 0094 (4 targets) blocks failed H1; the 0095
5-target block passed H1 (+21.6) and H2 (1.00) but failed H3/H4. The task is
frozen as a challenge; H4 is not lowered. A larger learned budget or Phase 2
communication is a new pre-registration.
