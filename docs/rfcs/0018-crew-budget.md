# Mechanic RFC 0018 — Crew report budget

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-23
- **Related:** ADR 0029, RFC 0015, ADR 0026, experiment 0057

## Summary

Add a per-crew report budget to the distributed visibility task. Each crew may
report at most `K` visible positive bridges per decision; reports are shared,
and the dispatcher may assign either crew to any reported target. `K=3` is
effectively the full local union, `K=1` is a single report per crew, and `K=0`
is private/no communication.

## Motivation

The 0052/0056 tasks test shared union and delayed memory, but not bandwidth.
A one-report budget is the smallest channel that forces each crew to choose what
to communicate. The pilot shows two reports match shared-local and one report
loses 60 points, so the bandwidth threshold is a real variable.

## Rules

- Base: distributed visibility task (`factory.power.crew-visibility.v1`).
- Each crew reports its top `K` visible positive bridges, ranked by outage and
  distance.
- Reports are shared: either crew may be assigned to any reported target.
- No report age in the budget condition; reports are current.
- `K=3` is the shared-local upper bound; `K=1` is the budget condition;
  private uses no reports.
- Action mask allows noop or a reported role for either crew.

## Observation and action impact

`info["roles"]` contains only reported targets; hidden roles are zeroed.
`info["reports"]` lists each crew's reported roles. The pair action space is
unchanged. Defaults and existing tasks are unchanged.

## Data impact

- New debug condition `factory.power.crew-visibility.v1` with report budget.
- Frozen `factory-v0.1` is unchanged.

## Determinism

- Report selection depends on seeded visibility and wire state.
- Crews remain control state, not factory hash state.

## Tests

- Report sets and union masking.
- K=3 matches shared local.
- K=1 reports only one target per crew.
- Hidden targets are masked.
- Default behavior unchanged.

## Alternatives

- **Message age only.** Already 0052/0056.
- **Explicit report-action policy.** Deferred; scripted top-K first.
- **Per-crew private policies.** Already 0056; budget is shared.

## Decision

Accepted. See ADR 0029 and experiment 0057. Test whether two reports per crew
match shared-local and one report is measurably worse.
