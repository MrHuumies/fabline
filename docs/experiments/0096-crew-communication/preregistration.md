# Experiment 0096 — Local-view crew communication

- **Status:** complete (negative on H1; see [summary](summary.md))
- **Date:** 2026-11-28
- **Type:** 0.7.1 Phase 2 communication
- **Task:** `factory.power.crew-communication.v1` (Phase 2; debug candidate)
- **Code:** `src/fabline/env/crew_communication.py`,
  `src/fabline/harness/crew_communication.py`
- **CLI:** `python -m fabline crew-communication`
- **Benchmark:** none; `factory-v0.6` unchanged
- **Related:** RFC 0032, ADR 0043, experiment 0095

## Question

Does a budgeted, delayed `report` action improve mission success over a local
view with no communication, on the frozen five-target Phase 1 layout?

## Hypothesis

Local views hide most targets, so a crew that reports a discovered failure can
save the other crew search time. Reporting costs a decision step, so the gain
may appear in **success** before it appears in **score**. The scripted report
policy should beat local no-report on success; the full-information shared
policy is the upper bound. A learned baseline is a follow-up, not part of 0096.

## Environment

- Phase 1 five-target, 32×32 gear/wired-power layout, 500 ticks, 10-tick
  decisions, 6 repair ticks;
- two crews, local visibility radius 6;
- seven actions per crew: N/E/S/W, wait, repair, report;
- report budget 2 per crew; reports are delivered after 1 decision;
- report cost 0.5 per report action;
- success is mission completion (all five targets repaired within 500 ticks);
- crew/report state is task-layer and does not change the canonical hash.

## Conditions

| Policy | Info | Reports |
|---|---|---|
| shared | full Phase 1 state | never |
| local_no_report | local radius 6 | never |
| local_report | local radius 6 | reports discovered failures |
| random | local legal actions | random |

## Pilot (120,000–120,004, 3 episodes)

| Policy | Score | Success | Messages |
|---|---:|---:|---:|
| shared | 43.33 | 1.00 | 0.00 |
| local_no_report | 18.67 | 0.47 | 0.00 |
| local_report | 22.00 | 0.67 | 3.53 |
| random | 0.00 | 0.00 | 1.60 |

The report policy gains **+0.20 success** and +3.33 score over local no-report.
The score gain is below 10; the success gain is the registered primary effect.
Messages are reported; the report policy is not spam-free by construction.

## Design

- Formal: **seeds 120,010–120,014**, five episodes per seed.
- All base and episode seeds are validated.
- No learned baseline in 0096; this is a task-validity communication block.
  A learned local policy is a new pre-registration.
- No post-hoc radius, budget, delay, cost, seed, or gate tuning.
- Report per-seed scores/success, messages, delivered reports, and 95% CIs.

## Gates

| Gate | Threshold |
|---|---|
| H1 communication | report success ≥ local no-report + 0.10 (**primary**) |
| H2 shared validity | shared success ≥ 0.60 |
| H3 report over random | report score ≥ random + 10 |
| H4 report success | report success ≥ 0.60 for a standard task |
| H5 cost | report messages, delivered reports, and report cost |

Score gain over local no-report is reported as a secondary metric. The pilot
shows a small score gain; do not substitute it for H1 after the formal block.

## Decision rule

- H1/H2/H4 pass: communication is a **standard** task-validity result.
- H1/H2 pass and H4 fails: communication is a **challenge** candidate.
- H1 or H2 fails: communication is negative on this layout; do not freeze a
  benchmark or tune the block.

No `factory-v0.7` freeze is claimed by 0096; a learned baseline and a task card
are required first. `factory-v0.6` remains untouched.

## Analysis

- Per-seed and pooled means with 95% bootstrap CIs.
- Report success, score, messages, and delivered reports separately.
- Report the shared upper bound and the local no-report lower bound.
- Negative and challenge results go first in the summary.

## Kill criteria

- H1 fails: local reporting does not improve success; retire or test a different
  layout/report contract in a new pre-registration.
- H2 fails: the shared task is not valid on these seeds.
- No post-hoc tuning of radius/budget/delay/cost or gates.

## Result

The formal block failed H1: local report 17.2/0.72 vs local no-report
28.4/0.92. H2/H3/H4/H5 passed. No challenge and no benchmark freeze. See
[summary](summary.md).

## Artifacts

- RFC: [`../../rfcs/0032-uncertain-repair.md`](../../rfcs/0032-uncertain-repair.md)
- ADR: [`../../decisions/0043-sequential-crew-scope.md`](../../decisions/0043-sequential-crew-scope.md)
- Raw results: `results/crew-communication/` (ignored)
