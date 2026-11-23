# Experiment 0060 — Replacement crew handoff

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-23
- **Type:** P2 third-crew/handoff experiment
- **Mechanic:** replacement crew at the recalled slot (RFC 0019, ADR 0030)
- **Task:** `factory.power.crew-replacement.v1` (debug/P2, not in
  `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a replacement crew arriving at the recalled slot add a meaningful handoff
gain over the no-replacement sequential triage?

## Environment

- 32×16 twin-line, three positive bridges.
- Initial A/B pair; failure/recall at 100.
- B's unfinished job aborts; C arrives at B's base.
- Post-failure A/C pair; duplicate positive targets masked.
- Reward: final production score; success ≥ 300.

## Data and seeds

- Pilot: seeds 19000–19002. No-replacement oracle 476.7, best scripted aware
  430; replacement oracle 490, greedy 490, nearest 480, aware 466.7.
- Formal: seeds 20000–20004 (5 contiguous, all valid by reset-only check).
- No Q training.
- No dataset artifact.

## Baselines

| Condition | Policies |
|---|---|
| no-replacement | nearest, greedy, aware, no-replan, oracle |
| replacement | nearest, greedy, aware, oracle |

## Gates

| Gate | Threshold |
|---|---|
| H1 replacement oracle | replacement oracle ≥ no-replacement oracle + 10 |
| H2 handoff gain | replacement best scripted ≥ no-replacement best + 10 |
| H3 coordination | replacement best ≥ no-replacement single/noop + 10 |
| H4 oracle gap | report replacement oracle vs best scripted |
| H5 frozen benchmark | unchanged |

## Predictions

- Replacement best 470–500; no-replacement best 410–440.
- Handoff gain 40–60; oracle gain 10–20.
- Greedy may match the replacement oracle; the task is a handoff demonstration,
  not a hard assignment benchmark.
- Success 1.00 for replacement, 1.00 for no-replacement best.

## Kill criteria

- Replacement does not beat no-replacement by 10 on H1 or H2.
- The task requires post-hoc changes to replacement timing, base, or gates.

## Analysis plan

- Report all conditions with score, CI, success, and per-seed scores.
- Report oracle actions.
- Keep the layout, failure/recall, C base, and one-pair budget fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0019, ADR 0030
- Env: `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_replacement.py`
- CLI: `python -m fabline crew-replacement`
- Task card: `docs/tasks/crew-replacement.md`
- Raw results: `results/crew-replacement/` (ignored)
- Summary: `docs/experiments/0060-crew-replacement/summary.md`
- Prior: [`../0055-crew-triage/summary.md`](../0055-crew-triage/summary.md)
