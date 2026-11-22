# Experiment 0038 — Maintenance-threshold selection

- **Status:** complete (all gates pass)
- **Date:** 2026-11-22
- **Type:** P1 method/representation experiment; follow-up to
  [`0037`](../0037-preventive-fault/summary.md)
- **Task:** `factory.fault.preventive-threshold.v1` (debug/P1, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/preventive_threshold.py`,
  `src/fabline/harness/preventive_threshold.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Choosing the maintenance threshold once per episode fixes the learned
baseline that per-step Q failed.** Fixed thresholds score 230 at 0.4, 240 at
0.5/0.6, **250 at 0.7/0.8/0.9**, and 200 at 1.0. UCB selects **0.7** and scores
**250**; epsilon-greedy selects **0.8** and scores **250**; both succeed on
every evaluation seed after 50 training episodes. Per-step tabular Q in 0037
scored **178** and collapsed to always-maintain, so the meta-action closes a
**72-point gap**. All five gates pass.

## Environment

- Gear line, faults enabled, wear threshold 20.
- Fault auto-repair 60 ticks; maintenance 10 ticks.
- Arms: `0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0` of the wear threshold.
- One action per episode; a scripted policy applies the chosen threshold.
- Reward: final production score; success ≥ 240.
- Episode 500 ticks.

## Data and seeds

- Training: seeds 9000–9049.
- Evaluation: seeds 700–704.
- Pilot: training 8000–8049, evaluation 600–604; not formal.

## Results

| threshold | mean score | maintenance | faults | success |
|---:|---:|---:|---:|---:|
| 0.4 | 230.0 | 7.0 | 0.0 | 0.00 |
| 0.5 | 240.0 | 6.0 | 0.0 | 1.00 |
| 0.6 | 240.0 | 6.0 | 0.0 | 1.00 |
| 0.7 | **250.0** | 4.0 | 0.0 | **1.00** |
| 0.8 | **250.0** | 4.0 | 0.0 | **1.00** |
| 0.9 | **250.0** | 3.0 | 0.0 | **1.00** |
| 1.0 | 200.0 | 4.0 | 2.0 | 0.00 |

| learner | selected threshold | mean score | success |
|---|---:|---:|---:|
| UCB | 0.7 | **250.0** | 1.00 |
| epsilon-greedy | 0.8 | **250.0** | 1.00 |
| per-step Q (0037) | — | 178.0 | 0.40 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 best fixed arm | best fixed = 250 at 0.7/0.8/0.9 | **pass** |
| H2 learner quality | both ≥ 245; success 1.00 | **pass** |
| H3 selected arm | in {0.7, 0.8, 0.9} | **pass** |
| H4 representation gain | best learner ≥ per-step Q + 50 | **pass**, +72 |
| H5 sample efficiency | ≤ 50 training episodes | **pass**, 50 |

## Interpretation

- **The decision variable mattered.** Per-step Q had to discover a delayed
  trade through noop/maintain actions; the threshold bandit chooses the policy
  knob directly.
- **The optimal plateau is broad.** 0.7, 0.8, and 0.9 all score 250; 0.9 uses
  fewer maintenance windows, but the production score ties.
- **Early maintenance is measurably worse.** 0.4 scores 230; 0.5/0.6 score 240.
- **Threshold 1.0 is not noop.** It can maintain at wear 20 before a fault; it
  still scores like noop (200) with two faults.
- **This is a representation fix, not a new mechanic.** The underlying machine
  maintenance is the 0037 environment.

## Caveats

- Deterministic arms; every seed has the same arm returns.
- One decision per episode; not sequential maintenance control.
- Seven discrete arms; a continuous threshold or contextual threshold is a
  follow-up.
- Most-worn target only; per-entity scheduling is not modeled.
- The bandit is easy; the result is about representation, not sample efficiency.
- Not part of frozen `factory-v0.1`.

## Next

1. **Contextual threshold selection:** vary wear rate or fault threshold per
   episode and condition the choice on observed context.
2. **Per-entity maintenance scheduling:** one crew, several worn machines.
3. **Semi-MDP/option Q:** keep per-step control but treat maintenance as an
   option with a delayed return.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Env: `src/fabline/env/preventive_threshold.py`
- Harness: `src/fabline/harness/preventive_threshold.py`
- CLI: `python -m fabline preventive-threshold`
- Raw results: `results/preventive_threshold/` (ignored)
- Task card: `docs/tasks/fault-preventive-threshold.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
