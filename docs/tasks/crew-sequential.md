# Task card — sequential crew repair control

- **Task ID:** `factory.power.crew-sequential.v1` (draft)
- **Version:** 0.1.0-wip
- **Status:** Phase 1 WIP; not release-ready (ADR 0043)
- **World:** `factory-0.1.0` + wired power (task-layer crews)
- **Owner:** FABLINE
- **Date:** 2026-11-26
- **RFC:** [`0032-uncertain-repair.md`](../rfcs/0032-uncertain-repair.md)

## Phenomenon

Two or three repair crews move through a repair yard with failed/degraded
components at different positions. Each crew sees only its local
neighborhood, chooses movement/repair/report actions, and contributes to the
team's restored production. The task tests sequential per-agent control,
coordination, and communication, not a one-shot assignment.

## Contract (Phase 1 WIP)

- **Observation:** shared task observation for Phase 1 (positions, target
  failure/distance, repair progress, clock, budget); local per-crew views and
  received reports are Phase 2.
- **Action (per crew):** move N/E/S/W, wait, repair. `report` is Phase 2.
- **Joint action:** tuple of per-crew actions; `6^2 = 36` with legal masks.
- **Reward:** time-weighted restored connectivity/production minus repair and
  abort costs.
- **Episode:** 500 ticks; decision interval 10; repair ticks 6.
- **Success:** fixed by the pre-registration after threshold calibration.
- **Layout:** fixed gear/wired-power layout for Phase 1; a spread yard with
  graded visibility is Phase 2.

## WIP audit (2026-11-28)

The WIP branch is based on an older `main` and passes ruff/mypy, but it is not
release-ready:

- no tests, CLI, Makefile target, pre-registration, or task-card update;
- no centralized oracle (`queue_search` is only a scripted queue search);
- gates omit the oracle gap, cost, and message volume;
- evaluation does not retry invalid layouts;
- mission completion does not terminate the episode;
- `success_score=150` is uncalibrated: a 1-seed smoke run repaired all three
  targets but scored 60, so scripted success was 0;
- the Phase 1 contract (6 actions, shared observation) was implicit.

See [ADR 0043](../decisions/0043-sequential-crew-scope.md) for the scope
decision and required follow-ups.

## Baselines

| Baseline | Rule |
|---|---|
| centralized oracle | full view, exhaustive/CP-SAT for small instances |
| greedy/nearest/EDF | scripted assignment + movement |
| independent Q | per-crew local state |
| MAPPO/QMIX/MADDPG/COMA | centralized training, decentralized execution |
| communication policies | CommNet/TarMAC/DIAL |

## Gates (draft)

| Gate | Threshold |
|---|---|
| H1 coordination | best multi-crew ≥ single crew + 10 |
| H2 oracle gap | oracle ≥ best scripted + 10 |
| H3 learned | best learned ≥ best scripted + 10 |
| H4 success | best learned success ≥ 0.60 |
| H5 cost | report parameters, steps, messages, wall-clock |

A learned failure is a challenge-tier result, not a reason to lower H4.

## Known pitfalls

- **Action-space growth.** Start with two crews; factorize the policy.
- **Task-layer state.** Crew positions/progress must be serialized for replay;
  they are not in the canonical factory hash.
- **Binary visibility.** Use a spread layout with graded distance/occlusion.
- **One-shot leakage.** Do not let a single macro action run a job to
  completion; the policy must make sequential decisions.
- **Credit assignment.** Team reward; report per-crew contribution.

## Changelog

- 2026-11-26 — design card created.
- 2026-11-28 — WIP audit; Phase 1 narrowed to deterministic 2-crew control,
  shared observation, and six actions; stochastic faults deferred to 0.8.0.
