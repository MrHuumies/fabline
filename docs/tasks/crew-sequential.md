# Task card — sequential crew repair control

- **Task ID:** `factory.power.crew-sequential.v1` (draft)
- **Version:** 0.1.0-wip
- **Status:** Phase 1 formal negative on H1; not frozen (0093)
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
| H2 scripted success | assigned/greedy mission completion ≥ 0.60 |
| H3 learned | best learned ≥ random + 10; report vs best scripted |
| H4 success | best learned success ≥ 0.60 for a standard task |
| H5 cost | report parameters, steps, messages (0 in Phase 1), wall-clock |

`queue_oracle` is a queue-plan upper bound, not a full joint-action oracle.

## Challenge tier

A task may freeze as a **challenge task** if H1/H2 pass but the best learned
baseline misses H3/H4. Label it challenge in the task card and expected summary,
report the learned gap, and do not lower H4 or tune after the formal block. If
H1/H2 fail, the task is not valid and is not frozen.

## Formal result (0093)

Seeds 100,010–100,014, five episodes: assigned **93.2/1.00** vs single
**88.4/0.84**, a **+4.8** score gain below the +10 H1 gate. H2 passed (1.00),
H3 passed only because random scored 0, H4 failed (BC 0.24, Q 0.16), and H5
passed. The pilot's +12 did not replicate. The challenge tier does not apply
because H1 failed; `factory-v0.6` is not frozen. Redesign with a new
pre-registration or retire the sequential variant under RFC 0032.

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
- 2026-11-28 — challenge-tier release allowed when task validity passes but the
  learned baseline misses the success gate; H4 is not lowered.
- 2026-11-28 — formal 0093 negative on H1 (+4.8 vs +10); no `factory-v0.6`
  freeze; redesign or retire.
