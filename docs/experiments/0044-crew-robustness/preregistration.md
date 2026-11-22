# Experiment 0044 — Seed robustness of two-crew coordination

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-22
- **Type:** evaluation robustness; no new mechanic
- **Mechanic:** two crews, parallel travel + repair (RFC 0011, ADR 0021)
- **Task:** `factory.power.crew-coordination.v1` (unchanged from 0042)
- **Code:** `src/fabline/env/multi_crew.py`,
  `src/fabline/harness/multi_crew.py`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Was the 0042 formal result (two crews 260 vs single-crew 60 on five seeds)
representative, or an easy-seed artifact?

The 0042 pilot (seeds 0–9) had nearest/greedy failures on four seeds, while the
five formal seeds all let every parallel policy choose the same pair and score
260. This experiment measures the score distribution over a larger contiguous
seed block and tests whether tabular Q generalizes across layouts rather than
being trained per evaluation seed.

## Environment

Identical to 0042; no mechanic or config changes.

- Gear line, wired power, one generator, capacity 12.
- Crew A at the depot; crew B at the opposite corner.
- Targets: loop, small bridge, large bridge.
- Warnings at 40; failures at 90 (loop), 110 (small), 130 (large).
- One-shot assignment: one target per crew; same-wire positive pairs masked.
- Travel = 2 × Manhattan; service 40 ticks; jobs run concurrently.
- Reward: production score from the assignment to episode end.
- Success ≥ 150.

## Data and seeds

- **Evaluation:** seeds 3000–3039 (40 contiguous seeds). A reset-only validity
  check confirmed all 40 produce a loop and two bridges before any policy was
  scored.
- **No seed selection after scoring.** All 40 seeds are reported.
- **Q training:** five independent policies, each trained on 500 layouts:
  - 40000–40499, 41000–41499, 42000–42499, 43000–43499, 44000–44499.
- Q evaluation is zero-shot on all 40 evaluation seeds. Training and evaluation
  seeds are disjoint.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only, earliest positive deadline |
| random | uniform legal pair, seeded per evaluation seed |
| parallel_nearest | each crew takes its nearest positive target |
| parallel_greedy | maximize summed outage per service time, no duplicates |
| oracle | best pair by simulation on the evaluation seed |
| tabular Q | role/position state, five independently trained policies |

## Gates

| Gate | Threshold |
|---|---|
| H1 coordination gain | parallel_nearest mean ≥ single_edf mean + 10 |
| H2 oracle gain | oracle mean ≥ single_edf mean + 10 |
| H3 seed sensitivity | diagnostic: report nearest/greedy success; the 0042 easy-seed caveat is confirmed if either success < 0.95 |
| H4 Q quality | pooled Q mean ≥ 0.85 × oracle mean; success ≥ 0.60 |
| H5 protocol | all 40 seeds, no exclusions, fixed config, disjoint Q training |

## Predictions

- Single-crew EDF scores about 60 on every seed.
- Parallel nearest/greedy average 180–230 with success 0.60–0.90; at least four
  seeds score below 150.
- Oracle scores 260 on most seeds; a few layouts may cap below 260 if both
  bridges cannot be saved even with the best pair.
- Pooled Q averages 200–260 with success 0.70–1.00. If it falls below the gate,
  report the generalization gap rather than training on evaluation seeds.
- The 0042 five-seed mean of 260 is above the 40-seed mean.

## Decision rules

- If H1 or H2 fails, retire the two-crew task and revisit the mechanic.
- If H3 is refuted (nearest/greedy success ≥ 0.95), the task is stable but easy;
  keep it as a positive coordination control, not a headline benchmark.
- If H4 fails, report Q's layout generalization gap; do not tune Q or the state
  on the evaluation seeds.
- No post-hoc seed selection, deadline changes, or gate changes.
- Keep `factory-v0.1` frozen.

## Analysis plan

- Report mean score, 95% bootstrap CI, min, max, success, prevented, aborted,
  and travel for every policy.
- Report per-seed scores for every scripted policy and the mean Q score.
- Report paired differences (nearest − single_edf, oracle − nearest) with
  bootstrap CIs.
- Report per-Q-policy means and the number of seeds below 150.
- Report oracle pairs and any seeds where the best pair is not
  (small for A, large for B).
- Keep the mechanic, deadlines, and one-shot assignment fixed.

## Artifacts

- Mechanic: RFC 0011, ADR 0021
- Env: `src/fabline/env/multi_crew.py`
- Harness: `src/fabline/harness/multi_crew.py`
- CLI: `python -m fabline crew-robustness`
- Task card: `docs/tasks/multi-crew.md`
- Raw results: `results/crew-robustness/` (ignored)
- Summary: `docs/experiments/0044-crew-robustness/summary.md`
- Prior experiment: [`../0042-multi-crew/summary.md`](../0042-multi-crew/summary.md)
