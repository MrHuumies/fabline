# Experiment 0045 — Crew recall and replanning

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-22
- **Type:** P2 multi-agent failure/replanning experiment
- **Mechanic:** known crew recall plus a second dispatch (RFC 0012, ADR 0022)
- **Task:** `factory.power.crew-replan.v1` (debug/P2, not in `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does losing a crew mid-assignment create a real replanning decision, and does
the survivor's second dispatch recover the abandoned bridge?

Crew A and crew B are dispatched in parallel to the loop, the small bridge, and
the large bridge. B is recalled at tick 100. If B is still working, its job
aborts and its bridge becomes the orphan. After A's first job resolves, A may
recover the orphan (or noop); a zero-impact loop orphan grants no useful second
dispatch.

## Environment

- Gear line, wired power, one generator, capacity 12.
- Crew A at the depot; crew B at the opposite corner.
- Targets: loop, small bridge, large bridge.
- Warnings at 40; failures at 90 (loop), 110 (small), 130 (large).
- B recall at 100; B's unfinished job aborts.
- Initial assignment: one target per crew; same-wire positive pairs masked.
- Travel = 2 × Manhattan; service 40 ticks; jobs run concurrently.
- Second dispatch: after B leaves and A's first job resolves, A may recover the
  orphan or noop. An orphaned loop exposes no useful second dispatch.
- Reward: final production score.
- Success ≥ 150.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only, earliest positive deadline |
| parallel_nearest | nearest positive pair; nearest unresolved target at replan |
| parallel_greedy | outage per service time; best unresolved at replan |
| recall_aware | A takes the earliest bridge; B takes the other; recover the orphan |
| recall_aware_no_replan | same first assignment, no second dispatch |
| random | uniform legal action at both decisions |
| oracle | best initial pair and best legal replan by simulation |
| tabular Q | role/recall/orphan state; 1000 training layouts per policy |

## Data and seeds

- Pilot: seeds 0–9; 10 valid.
- Formal: seeds 5000–5009 (10 contiguous, all valid by reset-only check).
- Q training: five policies, 1000 layouts each:
  - 45000–45999, 46000–46999, 47000–47999, 48000–48999, 49000–49999.
- Q evaluation is zero-shot on all formal seeds; train/eval seeds disjoint.
- No dataset artifact.

## Gates

| Gate | Threshold |
|---|---|
| H1 coordination gain | best two-crew scripted (nearest/greedy/recall_aware) mean ≥ single_edf mean + 10 |
| H2 replan gain | recall_aware mean ≥ recall_aware_no_replan mean + 10 |
| H3 assignment non-inferiority | recall_aware mean ≥ parallel_nearest mean − 10 |
| H4 Q quality | pooled Q mean ≥ 0.85 × oracle mean; success ≥ 0.60 |
| H5 budget | 1000 training episodes per Q policy; 5 policies; disjoint seeds |

## Predictions

- Single-crew EDF scores 60; noop 40–60.
- Nearest/greedy and recall-aware score 240–260; oracle 260 on every seed.
- Recall-aware without the second dispatch scores about 60–80; the second
  dispatch is worth more than 100 points.
- Nearest is a strong baseline on this small layout; recall-aware is within 10
  points, not necessarily better.
- Q scores 140–180 and may fail the 0.85 quality gate; the two-decision credit
  assignment is harder than the one-shot task.
- If Q fails, report it as a representation boundary; do not tune the state or
  gates on the evaluation seeds.

## Kill criteria

- H1 fails: the recall task loses the two-crew coordination gain.
- H2 fails: the second dispatch does not recover the orphan; retire the slice.
- H3 fails by more than 10: the recall-aware rule is dominated by nearest.
- The task requires post-hoc changes to recall timing, deadlines, or gates.

## Analysis plan

- Report score, CI, min, max, success, B aborts, prevented repairs, travel, and
  second-dispatch counts for every policy.
- Report oracle initial/replan actions per seed.
- Report Q per-seed scores and the gap to oracle.
- Keep the mechanic, recall tick, deadlines, and masks fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0012, ADR 0022
- Env: `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_replan.py`
- CLI: `python -m fabline crew-replan`
- Task card: `docs/tasks/crew-replan.md`
- Raw results: `results/crew-replan/` (ignored)
- Summary: `docs/experiments/0045-crew-replan/summary.md`
- Prior: [`../0044-crew-robustness/summary.md`](../0044-crew-robustness/summary.md)
