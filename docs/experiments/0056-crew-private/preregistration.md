# Experiment 0056 — Private crew views versus shared reports

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-23
- **Type:** P2 multi-agent communication experiment
- **Task:** `factory.power.crew-visibility.v1` (0052)
- **Mechanic:** private per-crew policies versus shared local/delayed views
- **Code:** `src/fabline/harness/crew_private.py`
- **CLI:** `python -m fabline crew-private`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

How much of the distributed-layout visibility gap is recovered by sharing
views, and how much is lost when each crew acts privately?

The 0052 task gives the dispatcher the union of both crews' current views, or a
delayed shared report. A private policy gives each crew only its own radius and
no reports; the two choices are composed, and duplicate positive choices fall
back to B noop.

## Conditions

| Condition | What each crew sees | Communication |
|---|---|---|
| global | full state | centralized |
| shared local | own radius; dispatcher sees union | instantaneous |
| shared delayed60 | own radius; dispatcher sees union with 60-tick report memory | delayed |
| private | own radius only | none |

## Baselines

| Condition | Policies |
|---|---|
| global/shared | nearest, greedy, recall-aware, oracle |
| private | per-crew nearest, greedy, recall-aware; no oracle |

Private policies choose independently; if both choose the same positive wire,
B noops. The private action mask still requires each crew's target to be
visible to that crew.

## Data and seeds

- Pilot: seeds 13000–13002. Shared local 673; private greedy 570; private
  nearest/aware 440; global 720.
- Formal: seeds 14000–14004 (5 contiguous, all valid by reset-only check).
- No Q training.
- No dataset artifact.

## Gates

| Gate | Threshold |
|---|---|
| H1 shared-local gain | shared local ≥ private best + 10 |
| H2 shared-delayed gain | shared delayed60 ≥ private best + 10 |
| H3 private success | private success is reported; expected below shared |
| H4 global/local ordering | report global ≥ shared ≥ private |
| H5 frozen benchmark | unchanged |

## Predictions

- Shared local 650–690; private best 540–590; private nearest/aware 420–470.
- Shared success 0.6–0.8; private success 0.0–0.2.
- Sharing views recovers 80–200 points over private; the delayed report may or
  may not add over shared local on this block.
- The private collision rule is a floor, not an optimal decentralized policy.

## Analysis plan

- Report score, CI, success, and per-seed scores for every condition.
- Report private collision/fallback counts if available.
- Keep layout, radius, report age, and success threshold fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Harness: `src/fabline/harness/crew_private.py`
- CLI: `python -m fabline crew-private`
- Task card: `docs/tasks/crew-visibility.md`
- Raw results: `results/crew-private/` (ignored)
- Summary: `docs/experiments/0056-crew-private/summary.md`
- Prior: [`../0052-crew-visibility/summary.md`](../0052-crew-visibility/summary.md)
