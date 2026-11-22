# Experiment 0038 — Maintenance-threshold selection

- **Status:** complete (all gates pass; see [`summary.md`](summary.md))
- **Date:** 2026-11-22
- **Type:** P1 method/representation experiment; follow-up to
  [`0037`](../0037-preventive-fault/summary.md)
- **Task:** `factory.fault.preventive-threshold.v1` (debug/P1, not in
  `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does choosing the maintenance threshold once per episode stabilize the learned
policy where per-step tabular Q collapsed?

In 0037, the scripted threshold solved the task (250 vs noop 200), but per-step
Q scored 178 and collapsed to always-maintain on three of five seeds. The
fault-avoidance benefit is delayed relative to each noop/maintain decision. This
experiment makes the decision variable the actual policy knob: choose a wear
threshold, then a scripted policy applies it.

## Environment

- Same gear line, faults enabled, wear threshold 20.
- Fault auto-repair 60 ticks; maintenance 10 ticks.
- Arms: `0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0` of the wear threshold.
- Each episode is one action: choose an arm; the inner environment runs the full
  500-tick episode with that threshold.
- Reward: final production score.
- Success ≥ 240.

## Baselines

| Baseline | Rule |
|---|---|
| fixed arms | every threshold evaluated on the test seeds |
| UCB | untried-first, then UCB1; 50 training episodes |
| epsilon-greedy | sample average, epsilon 0.1; 50 training episodes |
| per-step Q | 0037 reference (178, H2 failed) |

## Data and seeds

- Training (learners): seeds 9000–9049.
- Evaluation: seeds 700–704.
- Pilot used training 8000–8049 and evaluation 600–604; those are not formal.

## Gates

| Gate | Threshold |
|---|---|
| H1 best fixed arm | best fixed score = 250 at 0.7/0.8/0.9 |
| H2 learner quality | UCB and epsilon-greedy score ≥ 245; success 1.00 |
| H3 selected arm | each learner selects an arm in {0.7, 0.8, 0.9} |
| H4 representation gain | best learner ≥ per-step Q + 50 |
| H5 sample efficiency | learners use ≤ 50 training episodes |

## Predictions

- Fixed arms: 0.4 → 230; 0.5/0.6 → 240; 0.7/0.8/0.9 → 250; 1.0 → 200.
- UCB selects 0.7; epsilon-greedy selects 0.8 or 0.9.
- Both learners score 250 and succeed on every evaluation seed.
- Per-step Q remains 178; the meta-action closes the 72-point gap.

## Kill criteria

- Best fixed arm is not 250.
- A learner scores below 245 or fails a seed.
- A learner selects 0.5 or lower.
- The representation gain is below 30.
- The task requires post-hoc changes to the arms, training budget, or gates.

## Analysis plan

- Report every fixed arm and both learners.
- Report the selected arm, score, success, maintenance, and fault counts.
- Report the 0037 per-step Q reference separately.
- Do not tune the arms or training budget after the formal run.
- Keep `factory-v0.1` frozen.

## Artifacts

- Env: `src/fabline/env/preventive_threshold.py`
- Harness: `src/fabline/harness/preventive_threshold.py`
- CLI: `python -m fabline preventive-threshold`
- Task card: `docs/tasks/fault-preventive-threshold.md`
- Raw results: `results/preventive_threshold/` (ignored)
- Summary: `docs/experiments/0038-preventive-threshold/summary.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
