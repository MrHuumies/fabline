# Mechanic RFC 0024 — Asymmetric repair-cost triage

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-23
- **Related:** ADR 0035, RFC 0017, ADR 0028, experiment 0066

## Summary

Add role-specific repair durations to the three-bridge survivor triage task. The
loop, small, and large bridges take 20, 40, and 100 ticks to repair respectively.
Travel time is unchanged. The action space, deadlines, recall, and two-survivor
budget stay the same. The task tests whether repair cost asymmetry makes the
triage order matter beyond the existing outage-per-service greedy rule.

## Motivation

The 0055 triage task has a real oracle gap, but greedy and deadline-aware
policies are close (378 vs 326 on the formal block). The 0059 spread-layout
pilot found that layout alone does not widen the gap. The next axis is
asymmetric values, deadlines, or repair costs. A value-weighted pilot was
negative: naive value-greedy scored 256 against greedy 378. Repair cost is the
cleaner axis because it changes the time budget directly.

A pilot on 0055 seeds 12000–12004 with repair costs 20/40/100 gives greedy 336,
aware 334, nearest 258, and oracle 388. The pilot is evidence that the cost axis
creates a gap; the formal run uses fresh seeds.

## Rules

- 32×16 twin-line layout, three positive bridges.
- Roles: `loop` = medium bridge, `small` = smallest outage, `large` = largest.
- Warnings 40; failures 90/110/130.
- Repair durations: loop 20, small 40, large 100; travel 2 × Manhattan.
- Job failure and B recall at 100; active jobs abort.
- Initial action: 16 A/B pairs; A gets two survivor jobs.
- Reward: final production score; success ≥ 300.

## Observation and action impact

The default observation is unchanged. When `role_repair_ticks` is set, the
crew-replan observation appends six normalized service-time features
(`role_service_a_norm`, `role_service_b_norm` for each role), so a learned
policy can see the cost asymmetry. The action space is unchanged.

## Data impact

- New task `factory.power.crew-triage-costs.v1`.
- Frozen `factory-v0.1` is unchanged.
- Default `role_repair_ticks=None` preserves all existing crew tasks.

## Tests

- `role_repair_ticks` length and non-negative validation.
- Role-specific service times in `info`.
- Default service time remains 40 ticks.
- Observation shape with and without cost features.
- Frozen benchmark regression.

## Alternatives

- **Value-weighted triage.** Negative pilot: naive value-greedy is worse than
  greedy; values alone do not capture the deadline interaction.
- **Spread-layout triage.** Negative pilot 0059; greedy matches oracle.
- **Random topology.** Deferred; a larger mechanic.

## Decision

Accepted. See ADR 0035 and experiment 0066. If the oracle gap is under 10
points on fresh seeds, retire the cost axis and move to random topology or P3.
