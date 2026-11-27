# ADR 0043 — 0.7.0 scope: deterministic sequential crews

- **Status:** accepted
- **Date:** 2026-11-28
- **Related:** RFC 0032, RFC 0030, ADR 0042,
  [`roadmap-0.5.0-0.8.0.md`](../roadmap-0.5.0-0.8.0.md),
  [`crew-sequential.md`](../tasks/crew-sequential.md),
  [`factory-v0.5`](../../benchmarks/factory-v0.5/card.md)
- **Approved by:** owner

## Context

0.6.0 shipped the assembly edge and froze `factory-v0.5`. The next roadmap item
is 0.7.0, *uncertain repair*. RFC 0032 proposes two connected mechanics:

1. true sequential per-crew control (movement, repair, local views, reports);
2. stochastic faults and POMDP maintenance (hidden wear, sensor noise,
   inspect/repair/continue).

The combined theme is too large for one release. The public WIP branch
`feat/0.7.0-sequential-crew` already contains a 2-crew deterministic environment
(425 lines) and harness (677 lines), but it is a partial Phase 1 slice, not a
release candidate.

### WIP audit (2026-11-28)

The WIP branch is based on `3fd2c0c`, behind current `main`. It passes ruff and
mypy, and a 1-seed smoke run completes, but the audit found:

- **No tests, CLI, Makefile target, pre-registration, or task-card update.**
- **No oracle baseline.** `queue_search` is a scripted queue search, not the
  centralized oracle the task card requires.
- **Incomplete gates.** The WIP checks coordination, scripted success, and a BC
  gap, but not the oracle gap, cost, or message volume.
- **Invalid-layout handling is uneven.** Training retries layouts with too few
  outage wires; evaluation does not.
- **Mission completion does not terminate the episode.** `terminated` is always
  false and the episode runs to the tick limit.
- **The success threshold is not calibrated.** In a 1-seed smoke run, the
  scripted policies repaired all three targets but scored 60 against
  `success_score=150`, so scripted success is 0 before any learned baseline is
  considered.
- **The Phase 1 contract is implicit.** The WIP has 6 actions (no `report`) and
  a shared observation, while the task card still describes 7 actions and
  per-crew local views.

## Decision

1. Accept RFC 0032 for 0.7.0, narrowed to **deterministic sequential crews**.
2. Defer stochastic faults and POMDP maintenance to **0.8.0**. Do not mix them
   into 0.7.0.
3. Fix the Phase 1 contract:
   - two crews and three target wires on a fixed gear/wired-power layout;
   - six actions: north, east, south, west, wait, repair;
   - shared observation for Phase 1; local views, `report`, and communication
     are Phase 2;
   - crew positions and repair progress are task-layer state, not canonical
     factory state;
   - 500 ticks, decision interval 10, repair ticks 6;
   - the default world hash and frozen v0.1–v0.5 assets are unchanged.
4. The formal pre-registration must fix the success threshold and layout from a
   pilot, before the formal five-seed block. Do not tune either after seeing the
   formal result.
5. Add a centralized oracle and the task-card gates H1–H5, including the oracle
   gap and cost/message reporting.
6. Add tests for movement, action masks, repair progress, determinism, replay
   round-trip, invalid-layout handling, and hash invariance.
7. Add a `sequential-crew` CLI command and a Makefile target.
8. Do not freeze `factory-v0.6` until the Phase 1 formal block passes. A learned
   failure is a challenge-tier result, not a reason to lower the gate.

## Alternatives considered

- **Ship the combined uncertain-repair theme.** Rejected: the WIP is not
  release-ready, and the stochastic fault/POMDP surface is a second mechanic.
- **Keep the 7-action contract with `report` in Phase 1.** Rejected: there are
  no communication semantics, message budget, or communication baseline yet;
  add them in Phase 2.
- **Use a macro `move_to(target)` action.** Rejected: it hides sequential
  control and reintroduces one-shot leakage.
- **Keep `success_score=150`.** Rejected until calibrated: the smoke run scored
  60 with all targets repaired.
- **Treat `queue_search` as the oracle.** Rejected: it searches a small scripted
  queue space, not the centralized oracle in the task card.
- **Move directly to 0.8.0.** Rejected: the sequential multi-agent gap is the
  larger missing coverage and should be tested first.

## Consequences

- 0.7.0 becomes a smaller, testable sequential-control release.
- The multi-agent gap is addressed first; stochastic faults and belief-state
  calibration remain open for 0.8.0.
- The WIP branch must be rebased and completed before any formal run.
- `factory-v0.1`–`factory-v0.5` remain immutable; no default hash changes.

## Follow-ups

- [ ] Rebase `feat/0.7.0-sequential-crew` onto current `main`.
- [ ] Add tests, CLI, and Makefile target.
- [ ] Add a centralized oracle and fix the gate set.
- [ ] Calibrate the success threshold/layout and write the pre-registration.
- [ ] Update the `crew-sequential` task card and RFC 0032 status.
- [ ] Run the formal five-seed block; freeze `factory-v0.6` only if the gates
      pass.
