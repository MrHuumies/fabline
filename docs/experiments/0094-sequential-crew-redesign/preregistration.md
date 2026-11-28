# Experiment 0094 — Sequential crew repair redesign

- **Status:** complete (negative on H1; see [summary](summary.md))
- **Date:** 2026-11-28
- **Type:** 0.7.0 Phase 1 redesign
- **Task:** `factory.power.crew-sequential.v1` (Phase 1 redesign; `factory-v0.6`
  candidate)
- **Code:** `src/fabline/env/sequential_crew.py`,
  `src/fabline/harness/sequential_crew.py`
- **CLI:** `python -m fabline sequential-crew`
- **Benchmark:** none; `factory-v0.5` unchanged; `factory-v0.6` candidate
- **ADR:** [`0043`](../../decisions/0043-sequential-crew-scope.md)

## Question

Does a **4-target, 500-tick** two-crew repair task create a coordination gain
over a single crew, and can independent Q or behavior cloning learn the
per-crew policy at the registered budget?

## Hypothesis

The 0093 task was too easy for task validity: one crew repaired 2.84 of 3
targets and the formal H1 gain was only +4.8. Four targets with the same
500-tick budget should make one crew insufficient and two crews necessary.
The learned baselines may still fail; a valid task that they cannot solve is
released as a **challenge task**.

## Environment

- 32×32 gear scenario with wired power, 500 ticks, 10-tick decisions;
- two crews, **four** failed target wires, six actions per crew
  (N/E/S/W, wait, repair);
- shared 20-feature observation for Phase 1; local views and `report` are
  Phase 2;
- 6 repair ticks;
- success is mission completion (all four targets repaired within 500 ticks);
  score is a continuous secondary metric;
- crew state is task-layer and does not change the canonical factory hash.

## Pilot (before pre-registration)

Scripted-only pilot on seeds 110,100–110,102, two episodes:

| Condition | Single crew | Greedy | Assigned |
|---|---:|---:|---:|
| 5 targets, 400 ticks | 0.0 / 0.13 | 0.0 / 0.13 | 0.0 / 0.13 |
| 5 targets, 500 ticks | 0.0 / 0.17 | 28.3 / 0.67 | 31.7 / 0.67 |
| **4 targets, 500 ticks** | **5.0 / 0.17** | **55.0 / 1.00** | **56.7 / 1.00** |

The 5-target/400 condition was too hard (all scores 0). The 5-target/500
condition passes H2 but is close to the gate. The 4-target/500 condition gives a
large H1 gain and scripted success 1.00, so it is the registered redesign.
The pilot is scripted-only; the formal block adds Q, BC, random, and the queue
oracle.

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

- Formal: **seeds 110,120–110,124**, five episodes per seed (offsets 0–4).
- All base and episode seeds are validated before training.
- Q: alpha 0.2, gamma 0.95, epsilon decay to 0.05.
- BC: one HistGradientBoostingClassifier per crew, 200 iterations, 3 DAgger
  iterations.
- No post-hoc layout, target, seed, or budget tuning.
- Report per-seed scores, bootstrap CIs, repairs, steps, and model cost.

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

- H1 or H2 fails: retire the redesign or run a new pilot/pre-registration; do
  not tune the 0094 block.
- Learned baselines fail H3/H4: publish as a challenge task; a larger Q/BC
  budget is a new pre-registration.
- No post-hoc changes to targets, ticks, seeds, gates, or reward.

## Result

The formal block failed H1 (+6.8 vs +10). H2/H3/H5 passed; H4 failed. The
challenge tier did not apply because task validity failed. See
[summary](summary.md).

## Artifacts

- Task card: [`../../tasks/crew-sequential.md`](../../tasks/crew-sequential.md)
- ADR: [`../../decisions/0043-sequential-crew-scope.md`](../../decisions/0043-sequential-crew-scope.md)
- Raw results: `results/sequential-crew-redesign/` (ignored)
