# Pilot 0053 — Simultaneous multi-orphan failure

- **Status:** pilot negative; not promoted
- **Date:** 2026-11-23
- **Type:** exploratory repeated-failure pilot
- **Base task:** twin-line recall/replanning (`0047`)
- **Code:** exploratory patch only; not committed
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does aborting both crew jobs at the recall tick create a useful
multiple-orphan triage task?

The intended mechanic: crew B is recalled at tick 80 and crew A's active job
also fails at 80, leaving two orphaned bridges. A survives and can recover one.
The policy must choose the initial pair and then choose which orphan to save.

## Setup

- 32×16 twin-line layout, random crew-B base, seeds 0–4.
- Recall and job failure both at tick 80; warnings 40; failures 90/110/130.
- Both initial jobs are active at 80; both abort.
- A's second dispatch may recover one orphan or noop.
- Success threshold 200 (the score scale is lower because both jobs abort).
- Baselines: noop, single-crew EDF, nearest, greedy, recall-aware, no-replan,
  oracle.

## Results

| policy | mean score over seeds 0–4 | success |
|---|---:|---:|
| noop | 112.0 | 0.0 |
| single_edf | 112.0 | 0.0 |
| nearest | 152.0 | 0.2 |
| greedy | 306.0 | 1.0 |
| recall-aware | 306.0 | 1.0 |
| no-replan | 112.0 | 0.0 |
| oracle | 306.0 | 1.0 |

Per-seed greedy/aware/oracle: 320, 280, 310, 290, 330. Noop: 120, 100, 110,
110, 120. The oracle pair is `(3, 12)` on every seed: noop for crew A, large
for crew B; B's large job aborts, A recovers large. Nearest often chooses A
small and B large, leaving A to recover small or large; it fails more often.

## Why it is not promoted

- **It collapses to a single-bridge task.** Both jobs abort, so A can save only
  one bridge. The best initial assignment is to send both crews at the same
  high-value bridge: B's job aborts and A recovers it.
- **Greedy and recall-aware already match the oracle.** There is no
  assignment/replan gap to learn or test.
- **The initial assignment is mostly a target selector.** With one survivor and
  one dispatch, the second decision is a single-choice recovery, not triage
  across multiple orphans.
- **The score is low and the task is mostly reactive.** It does not test
  repeated failure or sequential recovery.

## What it tells us

A useful multiple-orphan task needs either:

1. **Sequential survivor dispatch:** A can recover one orphan, then make another
   decision after that job, with deadlines and travel order mattering.
2. **A third crew or replacement:** another agent arrives after a failure, so
   two orphans can be covered in parallel or by handoff.
3. **Asymmetric orphan value and timing:** if one orphan is cheap to reach and
   another is critical, the order itself is the decision.

The current one-shot second dispatch cannot represent those trade-offs.

## Next

Implement **sequential survivor dispatch** on the twin-line layout: both jobs
fail, A gets a decision after each completed recovery until the episode ends or
no orphan remains. Compare EDF, nearest, outage-first, no-replan, oracle order.
Do not promote the one-shot double-orphan version.

## Artifacts

- Base task: [`../0047-crew-replan-layouts/summary.md`](../0047-crew-replan-layouts/summary.md)
- Task card: [`../../tasks/crew-replan-layouts.md`](../../tasks/crew-replan-layouts.md)
- Exploratory patch: not committed.
