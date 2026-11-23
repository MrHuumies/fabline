# Mechanic RFC 0017 — Three-bridge survivor triage

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-23
- **Related:** ADR 0028, RFC 0016, ADR 0027, RFC 0013, ADR 0023

## Summary

Add a three-positive-bridge triage variant on the twin-line layout. Both crews
start assigned; some jobs complete, others abort at a tick-100 job failure.
Crew A survives with two recovery jobs. All unresolved positive bridges remain
eligible, so A must choose which two of three to restore and in what order. The
initial pair still matters because a job that finishes before 100 saves its
bridge.

## Motivation

The all-abort sequential task (0054) is shallow: the initial jobs never finish,
so the first assignment is irrelevant and greedy matches oracle. Moving the
failure to 100 lets some assignments complete, creating a real trade between
initial coverage and survivor triage.

## Rules

- Base: twin-line recall/replanning (`factory.power.crew-replan-layouts.v1`).
- Three positive bridges; the usual loop role is repurposed as the third
  positive bridge.
- Warnings 40; failures 90/110/130.
- Job failure and B recall at 100; active jobs abort.
- A gets two survivor jobs. Each starts from A's current position.
- The replan mask allows noop or any unresolved positive bridge, not only
  orphans.
- Reward is the final production score; success ≥ 300.

## Observation and action impact

Same three-role observation and 16-action vector. `role_outages["loop"]` is
positive in this task; the loop key is documented as the medium bridge. The
replan mask is all unresolved positives when `replan_mode="all_positive"`.
Defaults preserve 0045/0047/0054.

## Data impact

- New task `factory.power.crew-triage.v1`.
- Frozen `factory-v0.1` is unchanged.

## Determinism

- Bridge selection, failure/recall, crew positions, and job durations are
  deterministic.
- Crews remain control state, not factory hash state.

## Tests

- Three positive roles and a three-target mask.
- Some initial jobs complete, some abort.
- Two survivor decisions; repaired targets leave the mask.
- Defaults preserve existing tasks.
- Frozen benchmark regression.

## Alternatives

- **All-abort triage.** Negative/one-shot pilot (0053); initial assignment is
  irrelevant.
- **Third crew.** Deferred.
- **Spread-layout triage.** Possible follow-up; twin-line first.

## Decision

Accepted. See ADR 0028 and experiment 0055. The task is a real assignment/triage
test only if the oracle beats the best scripted policy by 10; otherwise report
the shallow ceiling.
