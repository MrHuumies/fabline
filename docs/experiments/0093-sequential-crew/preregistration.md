# Experiment 0093 — Sequential crew repair

- **Status:** complete (negative on H1; see [summary](summary.md))
- **Date:** 2026-11-28
- **Type:** 0.7.0 Phase 1
- **Task:** `factory.power.crew-sequential.v1` (draft; `factory-v0.6` candidate)
- **Code:** `src/fabline/env/sequential_crew.py`,
  `src/fabline/harness/sequential_crew.py`
- **CLI:** `python -m fabline sequential-crew`
- **Benchmark:** none; `factory-v0.5` unchanged
- **ADR:** [`0043`](../../decisions/0043-sequential-crew-scope.md)

## Question

Does deterministic two-crew sequential repair produce a coordination gain over
a single crew, and can independent Q or behavior cloning learn the per-crew
policy at the registered budget?

## Hypothesis

The task is valid if the scripted multi-crew policies beat a single crew and
complete all targets. The learned baselines may fail: the action space is
factorized, the reward is delayed, and the observation is shared in Phase 1. A
valid task that the learned baselines cannot solve is released as a **challenge
task**, not hidden or tuned until it passes.

## Environment

- 32×32 gear scenario with wired power and the default 500-tick episode;
- two crews, three failed target wires, six actions per crew
  (N/E/S/W, wait, repair);
- shared 20-feature observation for Phase 1; local views and `report` are
  Phase 2;
- 10-tick decisions, 6 repair ticks;
- success is **mission completion** (all targets repaired within 500 ticks);
  score is a continuous secondary metric;
- crew state is task-layer and does not change the canonical factory hash.

## Conditions

| Policy | Rule |
|---|---|
| single_crew | crew 0 repairs; crew 1 waits |
| greedy | each crew pursues its nearest failed target |
| assigned | distinct nearest-pair assignment |
| queue_oracle | best queue assignment/order over the scripted movement policy |
| random | uniform legal joint action |
| independent_q | per-crew tabular Q, 500 training episodes |
| bc | behavior cloning of the assigned policy, 50 episodes + 3 DAgger iterations |

## Design

- Pilot: seeds 100,005–100,009, 3 episodes, Q 100, BC 10.
- Formal: **seeds 100,010–100,014**, 5 episodes per seed (offsets 0–4).
- All base/episode seeds are validated before training; invalid layouts fail
  loudly with the seed.
- Q: alpha 0.2, gamma 0.95, epsilon decay to 0.05.
- BC: one HistGradientBoostingClassifier per crew, 200 iterations, 3 DAgger
  iterations.
- No sleep, no global RNG; the task is deterministic given seed + actions.
- Report per-seed scores, bootstrap CIs, repairs, steps, and model cost.

## Pilot (100,005–100,009, 3 episodes)

| Policy | Score | Success |
|---|---:|---:|
| single_crew | 70.67 | 0.87 |
| greedy | 82.67 | 1.00 |
| assigned | 82.67 | 1.00 |
| queue_oracle | 86.67 | 1.00 |
| random | 0.00 | 0.00 |
| independent_q | 0.00 | 0.00 |
| bc | 0.00 | 0.00 |

H1 coordination +12.0 and H2 scripted success 1.00 pass. H3/H4 fail; the pilot
is a challenge-tier candidate. The oracle gap is +4.0; it is diagnostic, not a
freeze gate.

## Gates

| Gate | Threshold |
|---|---|
| H1 coordination | best scripted ≥ single crew + 10 |
| H2 scripted success | best scripted mission completion ≥ 0.60 |
| H3 learned gap | best learned ≥ random + 10 |
| H4 learned success | best learned success ≥ 0.60 for a standard task |
| H5 cost | report parameters, training seconds, and messages (0 in Phase 1) |

Oracle gap (queue oracle − best scripted) is reported as a diagnostic.

## Freeze rule

- H1 or H2 fails: the task is not valid; do not freeze `factory-v0.6`.
- H1/H2 pass and H3/H4 pass: freeze as a standard challenge-tier-capable task.
- H1/H2 pass and H3/H4 fail: freeze as a **challenge task**; label it in the
  card and expected summary, report the learned gap, and do not lower H4 or
  tune after the formal block.

## Analysis

- Report per-seed and pooled means with 95% bootstrap CIs.
- Report the learned-vs-random and learned-vs-scripted gaps.
- Report success (mission completion) and score separately.
- Report training/inference cost and model size.
- Negative and challenge results go in the first paragraph of the summary.

## Kill criteria

- H1 or H2 fails: retire the sequential variant or redesign it in a new
  pre-registration.
- Learned baselines fail H3/H4: publish as a challenge task; do not add a larger
  Q/BC budget or tune hyperparameters in this experiment.
- A larger budget or a new observation contract is a new pre-registration.

## Result

The formal block failed H1 (+4.8 vs +10). H2/H3/H5 passed; H4 failed. The
challenge tier did not apply because task validity failed. `factory-v0.6` was
not frozen. See [summary](summary.md).

## Artifacts

- Task card: [`../../tasks/crew-sequential.md`](../../tasks/crew-sequential.md)
- ADR: [`../../decisions/0043-sequential-crew-scope.md`](../../decisions/0043-sequential-crew-scope.md)
- Raw results: `results/sequential-crew/` (ignored)
