# Mechanic RFC 0012 — Crew recall and replanning

- **Status:** accepted
- **Author:** FABLINE
- **Date:** 2026-11-22
- **Related:** ADR 0022, RFC 0011, ADR 0021, experiment 0045

## Summary

Add a two-decision repair task built on the two-crew assignment. Two crews are
dispatched in parallel to a loop, a small bridge, and a large bridge. Crew B has
a known recall tick. If B is still working when it is recalled, its job aborts.
Once B is gone and crew A's first job resolves, A gets a second dispatch to a
remaining target. The agent must assign B a job it can finish before recall and
replan with A when it cannot.

## Motivation

The centralized two-crew task (0042, 0044) is robust but shallow: nearest wins
97.5% of 40 seeds, and the oracle pair is always the same. Partial per-crew
visibility was binary on the current layout (0043). Crew loss is the next
orthogonal multi-agent question: does planning around an unavailable teammate
add a real decision?

## Rules

- Same layout, wires, warnings, and failure ticks as the two-crew task.
- Crew A starts at the depot; crew B starts at the opposite corner.
- Warnings at 40; failures at 90 (loop), 110 (small), 130 (large).
- Crew B is recalled at tick 100. The recall tick is known from reset.
- Initial assignment at 40: one target per crew, or noop/loop.
- Jobs run concurrently; travel = 2 × Manhattan, service = 40 ticks.
- If B is still working at recall, its job aborts and the wire is left degraded
  or failed. A completed B job counts normally.
- After B is recalled and A's first job resolves, A gets a second dispatch to
  B's abandoned target (or noop), starting from A's current position. An
  abandoned loop has zero outage and grants no useful dispatch.
- A's second job is a recovery attempt: it completes even if the target fails
  during travel, so a late repair still restores service.
- If B completed its job before recall, no orphan exists and A noops.
- Reward: final production score. The first decision has zero immediate reward;
  the second decision carries the terminal episode reward.
- Success threshold: 150, unchanged from 0042.

## Action space

- 16 actions at the initial decision (A choice × B choice), with same-wire
  positive pairs masked.
- The same 16-action vector is used at the second decision, but only noop and
  the abandoned positive bridge are legal. This keeps a fixed action shape
  across phases.

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| wire degradation | B may be recalled before a bridge fails | timing |
| crew travel | B can only finish jobs within its recall window | assignment |
| two-crew assignment | A must cover B's failed target | replanning |
| production | lost service until A repairs | reward |
| frozen benchmark | wired mode only | hash regression |

## Observation impact

New feature vector: the 0042 features plus phase, B availability, and remaining
recall ticks. The initial observation is otherwise the same.

## Data impact

- New task `factory.power.crew-replan.v1` (debug/P2).
- Metrics: score, prevented repairs, aborted B jobs, second-dispatch targets,
  travel, success.
- Frozen `factory-v0.1` is unchanged.

## Determinism

- Recall tick, targets, warnings, and failures are deterministic.
- Crew positions update after each completed job.
- Crews are control state, not factory hash state.
- Replays validate both decisions and both job timelines.

## Tests

- Initial pair mask and replan A-only mask.
- B job completion before recall vs abort at recall.
- A second dispatch from the post-job position.
- Observation shape and phase transitions.
- Oracle is at least as good as the best scripted policy.
- Frozen benchmark regression.

## Performance

Two crews, three targets, two decisions; constant work per action. The 1k
ticks/s floor holds.

## Alternatives

- **Random crew failure.** Rejected for the first slice; a known recall tick is
  deterministic and easier to attribute.
- **Mid-job redirection.** Deferred; it requires partial travel state.
- **Free second dispatch to any target.** Rejected; a loop orphan would grant a
  free extra job and break the single-crew comparison.
- **Full worker agents.** Deferred; much larger.
- **No second decision.** Rejected; it tests robust assignment, not replanning.

## Decision

Accepted. See ADR 0022; experiment 0045 tests whether the second dispatch
recovers the abandoned bridge, whether two crews still beat a single crew, and
whether recall-aware assignment is non-inferior to nearest.
