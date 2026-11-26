# Task card — sequential crew repair control

- **Task ID:** `factory.power.crew-sequential.v1` (draft)
- **Version:** 0.1.0-draft
- **Status:** design; not implemented
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

## Contract (draft)

- **Observation (per crew):** own position, local radius view of targets and
  crews, own repair progress, received reports with age, clock/budget/team
  score.
- **Action (per crew):** move N/E/S/W, wait, repair, report.
- **Joint action:** tuple of per-crew actions; `7^N` with legal masks.
- **Reward:** time-weighted restored connectivity/production minus repair and
  abort costs.
- **Episode:** 300–500 ticks; decision interval 1–5 ticks.
- **Success:** fixed at pre-registration.
- **Layout:** spread yard with graded visibility; not the 16x8 binary layout.

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
