# Task card — sequential crew repair control

- **Task ID:** `factory.power.crew-sequential.v1`
- **Version:** 0.1.0
- **Status:** frozen as a **challenge** task in `factory-v0.6`
- **World:** `factory-0.1.0` + wired power (task-layer crews)
- **Owner:** FABLINE
- **Date:** 2026-11-28
- **RFC:** [`0032-uncertain-repair.md`](../rfcs/0032-uncertain-repair.md)
- **ADR:** [`0043-sequential-crew-scope.md`](../decisions/0043-sequential-crew-scope.md)
- **Benchmark:** [`factory-v0.6`](../../benchmarks/factory-v0.6/card.md)

## Phenomenon

Two repair crews move through a repair yard with failed wires at different
positions. Each crew chooses movement, wait, or repair and contributes to the
team's restored production. The task tests sequential per-crew control and
coordination, not a one-shot assignment.

## Contract (Phase 1)

- **Observation:** shared 20-feature task state for Phase 1 (clock, score,
  positions, target failure/distance/progress, repaired fraction, budget).
  Local per-crew views and reports are Phase 2.
- **Action (per crew):** move N/E/S/W, wait, repair. `report` is Phase 2.
- **Joint action:** `6^2 = 36` with legal masks.
- **Reward:** time-weighted restored production plus repair/progress bonuses.
- **Episode:** 500 ticks; decision interval 10; repair ticks 6.
- **Success:** mission completion — all five targets repaired within 500 ticks.
  Score is a continuous secondary metric.
- **Layout:** fixed 32×32 gear/wired-power layout.
- **State:** crew positions and repair progress are task-layer state, not part
  of the canonical factory hash; they are serialized for replay.

## Baselines

| Baseline | Rule |
|---|---|
| single_crew | crew 0 repairs; crew 1 waits |
| greedy | each crew pursues its nearest failed target |
| assigned | distinct nearest-pair assignment |
| queue_oracle | best queue assignment/order over the scripted movement policy |
| random | uniform legal joint action |
| independent_q | per-crew tabular Q, 500 training episodes |
| bc | behavior cloning of `assigned`, 50 episodes + 3 DAgger iterations |

`queue_oracle` is a queue-plan upper bound, not a full joint-action oracle.

## Gates

| Gate | Threshold |
|---|---|
| H1 coordination | best scripted ≥ single crew + 10 |
| H2 scripted success | best scripted mission completion ≥ 0.60 |
| H3 learned gap | best learned ≥ random + 10 |
| H4 learned success | best learned success ≥ 0.60 for a standard task |
| H5 cost | report parameters, training seconds, messages (0 in Phase 1) |

Oracle gap is a diagnostic, not a freeze gate.

## Challenge tier

A task may freeze as a **challenge task** if H1/H2 pass but the best learned
baseline misses H3/H4. Label it challenge in the task card and expected summary,
report the learned gap, and do not lower H4 or tune after the formal block. If
H1/H2 fail, the task is not valid and is not frozen.

## Phase 1 results

Seeds and conditions:

| Experiment | Condition | Single crew | Assigned | H1 | Outcome |
|---|---|---|---:|---:|---:|---|
| 0093 | 3 targets, 500 ticks | 88.4 / 0.84 | 93.2 / 1.00 | +4.8 | H1 fail; not frozen |
| 0094 | 4 targets, 500 ticks | 52.0 / 0.88 | 58.8 / 1.00 | +6.8 | H1 fail; not frozen |
| **0095** | **5 targets, 500 ticks** | **12.0 / 0.28** | **33.6 / 1.00** | **+21.6** | **H1/H2 pass; challenge** |

0095 details: H2 1.00, H3 +9.2 (BC 9.2 vs random 0) — fail by 0.8, H4 0.20 —
fail, H5 pass. Oracle gap +5.2. Q is 0.0/0.00; BC is 9.2/0.20. The task is valid
but too hard for the registered learned baselines, so it is frozen as a
challenge; H4 is not lowered.

The 5-target condition is the smallest tested condition where one crew is
clearly insufficient (3.48 of 5 targets) while two crews complete all five.
The 0093/0094 pilots were optimistic; the formal single crew was stronger on
fresh seeds.

## Known pitfalls

- **Action-space growth.** Two crews; factorize the policy for larger teams.
- **Task-layer state.** Crew positions/progress must be serialized for replay;
  they are not in the canonical factory hash.
- **One-shot leakage.** Do not let a single macro action run a job to
  completion; the policy must make sequential decisions.
- **Credit assignment.** Team reward; report per-crew contribution.
- **Challenge interpretation.** A learned failure is an open challenge, not a
  solved control task; do not tune the formal block.
- **Communication is Phase 2.** The current task has no `report` action or
  message budget.

## Changelog

- 2026-11-26 — design card created.
- 2026-11-28 — Phase 1 narrowed to deterministic two-crew control; stochastic
  faults deferred to 0.8.0.
- 2026-11-28 — 0093 (3 targets) and 0094 (4 targets) negative on H1.
- 2026-11-28 — 0095 (5 targets) valid; H3/H4 fail; frozen as a challenge in
  `factory-v0.6`.
