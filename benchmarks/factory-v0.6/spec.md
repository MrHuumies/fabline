# factory-v0.6 benchmark specification

- **Status:** frozen; **challenge tier**
- **Version:** 0.6.0
- **Package release:** 0.7.0
- **Date:** 2026-11-28
- **World:** `factory-0.1.0` + wired power (task-layer crews)
- **Plan:** `sequential-v0.6`
- **Runner:** `python -m fabline sequential-crew`
- **Expected summary:** [`expected/summary.json`](expected/summary.json)
- **Predecessor:** `factory-v0.5` remains immutable

## Purpose

`factory-v0.6` tests true sequential per-crew control rather than one-shot crew
assignment. Two crews move through a repair yard, choose targets, and repair
failed wires; the task is valid only if the second crew materially improves the
outcome. It is frozen as a challenge because the current learned baselines do
not solve it.

## Contract

- **Layout:** 32×32 gear scenario with wired power; fixed layout per seed.
- **Crews:** two, each with position and repair progress in task-layer state.
- **Targets:** five failed wires selected by outage impact.
- **Actions:** six per crew — north, east, south, west, wait, repair.
- **Joint action:** 36 combinations; illegal actions are masked.
- **Observation:** shared 20-feature Phase 1 state (clock, score, positions,
  target failure/distance/progress, repaired fraction, budget).
- **Dynamics:** 500 ticks, 10-tick decisions, 6 repair ticks; the episode runs
  to the tick limit so production is comparable.
- **Success:** mission completion — all five targets repaired within 500 ticks.
- **Reward:** production delta plus repair/progress bonuses.
- **Determinism:** seeded layout and target selection; same seed plus actions
  yields the same replay state. The canonical factory hash is unchanged.
- **Task-layer state:** crew positions, targets, and repair progress are not in
  the canonical factory hash; they are serialized for replay.

## Baselines

| Baseline | Rule |
|---|---|
| single_crew | crew 0 repairs; crew 1 waits |
| greedy | each crew pursues its nearest failed target |
| assigned | distinct nearest-pair assignment |
| queue_oracle | best queue assignment/order over the scripted movement policy |
| random | uniform legal joint action |
| independent_q | per-crew tabular Q, 500 training episodes |
| bc | behavior cloning of `assigned`, 50 episodes + 3 DAgger iterations |

`queue_oracle` is a queue-plan upper bound, not a full joint-action oracle.

## Gates

| Gate | Threshold |
|---|---|
| H1 coordination | best scripted ≥ single crew + 10 |
| H2 scripted success | best scripted mission completion ≥ 0.60 |
| H3 learned gap | best learned ≥ random + 10 |
| H4 learned success | best learned success ≥ 0.60 for a standard task |
| H5 cost | report parameters, training seconds, and messages (0 in Phase 1) |

A valid task may freeze as a **challenge task** if H1/H2 pass but H3/H4 fail.
The challenge label is part of the expected summary. H4 is not lowered. If H1
or H2 fails, the task is not frozen.

## Seeds and budgets

- Formal seeds: 110,150–110,154; five episodes per seed (offsets 0–4).
- Q: 500 training episodes; BC: 50 episodes, 3 DAgger iterations, 200 boosting
  iterations.
- All base and episode seeds are validated before training; an invalid layout
  fails with the seed number.
- The expected-summary check uses a 3% relative / 0.02 absolute tolerance.

## Scope cuts

- Local per-crew views, `report`, and communication are Phase 2.
- Stochastic faults and POMDP maintenance are deferred to 0.8.0.
- No layout split or larger-crew scaling in 0.6.0.
- No deep MARL baseline; Q/BC are the registered learned baselines.
- No demand/order stream in this task.

## Version history

- 2026-11-28 — 0.6.0 challenge freeze; five-target design after 0093/0094
  failed H1.
