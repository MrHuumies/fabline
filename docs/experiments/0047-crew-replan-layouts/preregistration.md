# Experiment 0047 — Recall/replanning on twin-line layouts

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-22
- **Type:** P2 multi-agent combination experiment
- **Mechanic:** known crew recall on twin-line randomized layouts (RFC 0014,
  ADR 0024)
- **Task:** `factory.power.crew-replan-layouts.v1` (debug/P2, not in
  `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does the survivor's recovery dispatch still add value when the first assignment
is nonlocal and hard?

The 16×8 recall task (0045) is positive but nearest is within 6 points of
oracle. The twin-line layout (0046) makes assignment hard: oracle 441, greedy
419, nearest 361. This experiment combines the two.

## Environment

- 32×16, two gear lines, random x offsets, one generator capacity 24.
- Crew A at the first depot; B on a random empty cell at least eight Manhattan
  cells from A.
- Warnings 40; failures 90 (loop), 110 (small), 130 (large).
- B recall 100; unfinished B job aborts.
- Initial pair assignment; A's second dispatch is noop or the abandoned
  positive bridge.
- Travel = 2 × Manhattan; service 40 ticks.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 0–9. Means: noop 136, single 140, nearest 405, greedy 491,
  recall_aware 433, no_replan 260, oracle 512.
- Formal: seeds 7000–7009 (10 contiguous, all valid by reset-only check).
- Q training: three policies, 500 layouts each, on 65000–65499, 66000–66499,
  67000–67499.
- Q evaluation is zero-shot on the formal seeds; train/eval disjoint.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| parallel_nearest | nearest positive pair; nearest unresolved at replan |
| parallel_greedy | outage per service time |
| recall_aware | A earliest bridge, B the other; recover the orphan |
| recall_aware_no_replan | same first assignment, no second dispatch |
| random | uniform legal action |
| oracle | best initial pair and replan by simulation |
| tabular Q | role/recall/orphan state, 500 training layouts |

## Gates

| Gate | Threshold |
|---|---|
| H1 coordination gain | best two-crew scripted ≥ single_edf + 10 |
| H2 replan gain | recall_aware ≥ recall_aware_no_replan + 10 |
| H3 layout gap | oracle ≥ best two-crew scripted + 10 |
| H4 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 |
| H5 budget | 500 episodes per Q policy; 3 policies |

## Predictions

- Single-crew EDF scores about 140; noop 100–310.
- Nearest 380–420, greedy 470–510, recall-aware 410–450.
- No-replan 240–280; recovery adds 150+ points.
- Oracle 500–520; oracle-best scripted gap 10–30.
- Q scores below 0.85 × oracle; the two-decision larger state is harder than
  either component task.

## Kill criteria

- Recovery does not add 10 points over no-replan.
- The oracle does not beat the best scripted policy by 10.
- The best scripted two-crew policy does not beat single-crew by 10.
- The task requires post-hoc changes to layout, recall, thresholds, or gates.

## Analysis plan

- Report score, CI, success, B aborts, prevented repairs, travel, and
  second-dispatch counts for every policy.
- Report oracle pairs and per-seed scores.
- Report Q per-seed scores and the gap to oracle.
- Keep layout, recall, deadlines, and gates fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0014, ADR 0024
- Env: `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_replan.py`
- CLI: `python -m fabline crew-replan-layouts`
- Task card: `docs/tasks/crew-replan-layouts.md`
- Raw results: `results/crew-replan-layouts/` (ignored)
- Summary: `docs/experiments/0047-crew-replan-layouts/summary.md`
- Prior: [`../0046-crew-layouts/summary.md`](../0046-crew-layouts/summary.md)
