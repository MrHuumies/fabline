# Mechanic RFC 0016 — Sequential survivor dispatch

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-23
- **Related:** ADR 0027, RFC 0012, ADR 0022, RFC 0013, ADR 0023

## Summary

Extend the twin-line recall task with a simultaneous double job failure. Both
crews' initial jobs abort at tick 80, leaving two orphaned bridges. Crew A
survives and gets a recovery decision after each job, up to a configured number
of survivor jobs. The task tests triage order and sequential travel rather than
a single forced recovery.

## Motivation

The one-shot double-orphan pilot (0053) collapsed to a one-bridge task: A could
recover only one orphan, and greedy matched oracle. A useful repeated-failure
task needs the survivor to act more than once, so order and travel matter.

## Rules

- Base: twin-line recall/replanning (`factory.power.crew-replan-layouts.v1`).
- Warnings 40; failures 90/110/130; recall 100 by default.
- New `job_failure_tick`: both active initial jobs abort at this tick. The pilot
  sets it to 80, the same as recall.
- Both aborted roles become orphans. A may recover any remaining orphan.
- `replan_jobs` controls the number of survivor jobs (default 1; pilot 2).
- Each survivor job starts from A's current position; after it completes, A gets
  another decision if an orphan remains and the budget is not exhausted.
- The action mask allows noop plus every remaining positive orphan.
- Reward is the final production score; intermediate survivor decisions have
  zero immediate reward and the final decision carries the terminal score.

## Observation and action impact

The observation and pair action space are unchanged. `info` exposes
`orphaned_roles`; the replan mask can contain multiple positive orphans. Default
`replan_jobs=1` and `job_failure_tick=0` preserve the 0045/0047 behavior.

## Data impact

- New task `factory.power.crew-multi-orphan.v1`.
- Frozen `factory-v0.1` is unchanged.

## Determinism

- Failure tick, recall, orphan set, crew positions, and job durations are
  deterministic.
- Crews remain control state, not factory hash state.

## Tests

- Two orphans after the failure tick.
- Sequential decisions and A position updates.
- Mask exposes remaining orphans and removes repaired ones.
- Default single-replan behavior is unchanged.
- Frozen benchmark regression.

## Alternatives

- **One-shot double orphan.** Negative pilot (0053); collapses to one bridge.
- **Third crew/replacement.** Deferred; larger action contract.
- **Repair-attempt failure.** Deferred; different failure model.
- **Multiple recalls.** Only one survivor remains after a recall; sequential
  survivor work is the useful form.

## Decision

Accepted. See ADR 0027 and experiment 0054. The task is a recovery/triage
debug task; if greedy matches oracle, report it as shallow rather than claiming
an assignment benchmark.
