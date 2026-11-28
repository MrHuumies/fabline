# Experiment 0095 — Sequential crew repair, 5-target redesign

- **Status:** complete (positive validity; challenge; see [summary](summary.md))
- **Date:** 2026-11-28
- **Type:** 0.7.0 Phase 1 redesign (second condition)
- **Task:** `factory.power.crew-sequential.v1` (Phase 1; `factory-v0.6` candidate)
- **Code:** `src/fabline/env/sequential_crew.py`,
  `src/fabline/harness/sequential_crew.py`
- **CLI:** `python -m fabline sequential-crew`
- **Benchmark:** none; `factory-v0.5` unchanged; `factory-v0.6` candidate
- **ADR:** [`0043`](../../decisions/0043-sequential-crew-scope.md)

## Context

The 0093 formal block (3 targets, 500 ticks) failed H1: assigned 93.2 vs single
88.4, only +4.8. The 0094 formal block (4 targets, 500 ticks) also failed H1:
assigned 58.8 vs single 52.0, +6.8. In both cases the single crew was stronger
on fresh seeds than in the pilot.

A 5-target/400-tick pilot was too hard (all scripted scores 0, success 0.13).
A 5-target/500-tick pilot was more promising:

| Policy | Score | Success | Repairs |
|---|---:|---:|---:|
| single_crew | 0.0 | 0.17 | 2.67 |
| greedy | 28.3 | 0.67 | 4.67 |
| assigned | 31.7 | 0.67 | 4.67 |

That pilot gives H1 +31.7 and H2 0.67, so 5 targets with 500 ticks is the next
registered condition. The learned baselines may still fail; if H1/H2 pass and
H3/H4 fail, the task is released as a **challenge task**.

## Environment

- 32×32 gear scenario with wired power, 500 ticks, 10-tick decisions;
- two crews, **five** failed target wires, six actions per crew
  (N/E/S/W, wait, repair);
- shared 20-feature observation for Phase 1; local views and `report` are
  Phase 2;
- 6 repair ticks;
- success is mission completion (all five targets repaired within 500 ticks);
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

- Formal: **seeds 110,150–110,154**, five episodes per seed (offsets 0–4).
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

- H1 or H2 fails: the sequential redesign is not valid; retire the line rather
  than tuning this block.
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

- H1 or H2 fails: retire the sequential line or run a genuinely new mechanic
  under a new RFC; do not tune 0095.
- Learned baselines fail H3/H4: publish as a challenge task; a larger Q/BC
  budget is a new pre-registration.
- No post-hoc changes to targets, ticks, seeds, gates, or reward.

## Result

The formal block passed H1 (+21.6) and H2 (1.00); H3/H4 failed. The task is
frozen as a challenge in `factory-v0.6`. See [summary](summary.md).

## Artifacts

- Task card: [`../../tasks/crew-sequential.md`](../../tasks/crew-sequential.md)
- ADR: [`../../decisions/0043-sequential-crew-scope.md`](../../decisions/0043-sequential-crew-scope.md)
- Raw results: `results/sequential-crew-5target/` (ignored)
