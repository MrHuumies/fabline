# Experiment 0076 — Triage planning

- **Status:** complete (planning positive; learned score model negative)
- **Date:** 2026-11-24
- **Type:** P3 planning/world-model experiment
- **Task:** `factory.planning.triage.v1` (debug/P3, not in `factory-v0.1`)
- **Code:** `src/fabline/harness/planning_triage.py`
- **CLI:** `python -m fabline planning-triage`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**True planning works; the learned score model does not.** On fresh seeds
49,000–49,004, CEM with the simulator reaches **454.0**, exactly the exhaustive
oracle. Scripted greedy is 398.0, scripted aware 292.0, random 188.0, and random
shooting 422.0. CEM with a ridge score model scores **166.0**, worse than
random; model MSE is 11,009. H1 and H4 pass; H2 and H3 fail. The task is a valid
planning benchmark with a real oracle gap, but a value model is not a world
model: the world-model gap remains open.

## Results

| policy | mean score | success |
|---|---:|---:|
| random | 188.0 | 0.20 |
| scripted aware | 292.0 | 0.40 |
| scripted greedy | 398.0 | 0.80 |
| random shooting true | 422.0 | 0.80 |
| **CEM true** | **454.0** | **1.00** |
| **oracle** | **454.0** | **1.00** |
| CEM learned (ridge) | 166.0 | 0.20 |

Per-seed CEM true: `460, 390, 500, 440, 480`.
Per-seed CEM learned: `270, 60, 140, 300, 60`.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 planning over random | CEM true ≥ random + 10 | **pass**, +266 |
| H2 learned planning | CEM learned ≥ random + 10 | **fail**, −22 |
| H3 model quality | CEM learned within 10 of CEM true | **fail**, −288 |
| H4 success | CEM true success ≥ 0.60 | **pass**, 1.00 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Planning is diagnostic.** The oracle gap over scripted aware is +162, and
  over greedy +56. CEM with the true simulator reaches the oracle.
- **The score model is not a world model.** A ridge value model trained on all
  256 sequences × 8 seed layouts still fails; an exploratory GBDT score model
  was also poor. Predicting final score from initial state plus a sequence does
  not capture the dynamics needed for planning.
- **The planning task is a benchmark candidate.** It has a stable oracle,
  scripted baselines, and a clear true-simulator planner. The learned model is a
  negative baseline, not a reason to exclude the task.
- **World models need transition prediction, not a value shortcut.** The next
  world-model experiment should learn `(state, action) -> next state` and plan
  by rollout, or use a model-based RL baseline.

## Caveats

- Exhaustive oracle is 256 sequences; the action space is small.
- Scripted aware is unstable across seeds (210–410).
- The value model is a shortcut; the negative is about that shortcut, not all
  learned world models.
- Not part of frozen `factory-v0.1`.

## Next

1. **Transition-model planning:** train a one-step `(state, action) -> next
   state` model on triage transitions; compare rollout error and CEM.
2. **Decentralized multi-agent** remains the next 0.3.0 flagship.
3. **Included in `factory-v0.2`** with the learned value model as a negative
   baseline; see the [benchmark card](../../../benchmarks/factory-v0.2/card.md).

## Artifacts

- Task card: [`../../tasks/planning-triage.md`](../../tasks/planning-triage.md)
- Code: `src/fabline/harness/planning_triage.py`
- Raw results: `results/planning-triage/` (ignored)
