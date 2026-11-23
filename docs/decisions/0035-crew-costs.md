# ADR 0035 — Asymmetric repair-cost triage

- **Status:** accepted
- **Date:** 2026-11-23
- **Related:** RFC 0024, RFC 0017, ADR 0028, experiment 0066

## Context

Three-bridge triage (0055) creates an oracle gap, but greedy and deadline-aware
policies are close. Value-weighted triage was a negative pilot. Repair cost is a
direct time-budget asymmetry and is already exposed through service times in
`info`.

## Decision

1. Add `role_repair_ticks: tuple[int, int, int] | None` to `MultiCrewConfig`.
   The tuple is ordered `loop`, `small`, `large`; `None` preserves 40 ticks.
2. Add an optional role argument to `_service_ticks` and pass the role from
   `_job` and `_info`.
3. Append six normalized service-time features to the crew-replan observation
   only when `role_repair_ticks` is set.
4. Add the `fabline crew-costs` CLI with repair costs `(20, 40, 100)` and the
   existing 0055 triage settings.
5. Keep the task opt-in and the frozen benchmark unchanged.

## Alternatives considered

- **Value-weighted triage.** Rejected after a negative pilot: value-greedy 256
  vs greedy 378.
- **Reuse 0055 without a new CLI.** Rejected; the new task needs a named preset
  and a task card.
- **Change the default repair time.** Rejected; existing tasks must not move.

## Consequences

- The task adds a cost/deadline trade-off without changing the action space.
- Default crew tasks keep 40-tick repairs and the 25-feature observation.
- A learned policy can see the six service features; scripted policies use
  `info`.
- If the formal oracle gap is under 10, the cost axis is retired.

## Follow-ups

- [ ] Formal experiment 0066 on seeds 25000–25004.
- [ ] Update the coverage map and roadmap after the result.
- [ ] Keep `factory-v0.1` frozen.
