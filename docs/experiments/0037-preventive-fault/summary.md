# Experiment 0037 — Preventive machine maintenance

- **Status:** complete (H1/H3 pass; H2 fails; Q unstable)
- **Date:** 2026-11-22
- **Type:** P1 phase 1C normal-fault preventive experiment
- **Mechanic:** machine-wear maintenance (RFC 0009, ADR 0019)
- **Task:** `factory.fault.preventive.v1` (debug/P1, not in `factory-v0.1`)
- **Code:** `src/fabline/env/preventive_fault.py`,
  `src/fabline/harness/preventive_fault.py`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Scheduled maintenance before the wear threshold beats noop, but tabular Q is
unstable.** Maintaining at 70% or 90% of the wear threshold scores **250** with
zero faults, versus 200 for noop (3 faults) and 130 for always-maintain. Early
maintenance at 50% scores 240. The scripted prevention result is +50 over noop,
but Q scores **178** and succeeds on only 0.40 of episodes: two Q seeds find the
optimal 250 policy, while three collapse to always-maintain at 130. H1 and H3
pass; **H2 fails**. The task is deterministic, so the Q variance is an
exploration/credit-assignment failure, not task noise.

## Environment

- Gear line, faults enabled.
- Wear threshold 20; wear per craft 1.
- Fault auto-repair 60 ticks; preventive maintenance 10 ticks.
- Actions: noop, or maintain the most worn non-faulted machine.
- Reward: production score delta.
- Outcome: final score; success ≥ 240.
- Episode 500 ticks; decision interval 10.

## Data and seeds

- Evaluation: seeds 400–404, 5 episodes each = 25 episodes.
- Q training: 500 layouts from 7000 + 1000 × Q seed.
- The line is deterministic; seed variance in Q is from exploration and
  tie-breaking, not layout.

## Results

| policy | mean score | 95% CI | maintenance | faults | success |
|---|---:|---:|---:|---:|---:|
| noop | 200.0 | [200.0, 200.0] | 0.0 | 3.0 | 0.00 |
| always | 130.0 | [130.0, 130.0] | 37.0 | 0.0 | 0.00 |
| random | 179.6 | [175.6, 183.2] | 22.4 | 0.0 | 0.00 |
| maintain_0.5 | 240.0 | [240.0, 240.0] | 6.0 | 0.0 | 1.00 |
| maintain_0.7 | **250.0** | [250.0, 250.0] | 4.0 | 0.0 | **1.00** |
| maintain_0.9 | **250.0** | [250.0, 250.0] | 3.0 | 0.0 | **1.00** |
| tabular Q | 178.0 | [158.8, 202.0] | 23.8 | 0.0 | 0.40 |

Q per-seed scores: 250, 130, 250, 130, 130. The two good seeds use 4
maintenance actions; the three bad seeds use 37 (always-maintain).

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 prevention gain | best threshold ≥ noop + 30 | **pass**, +50 |
| H2 Q quality | Q ≥ 0.95 × best; success ≥ 0.80 | **fail**, 178 vs 237.5; 0.40 |
| H3 timing | maintain_0.5 ≤ best − 5 | **pass**, 240 vs 245 |
| H4 seed consistency | report | Q per-seed 250/130 split |
| H5 budget | report | maintenance/fault counts above |

## Interpretation

- **Preventive maintenance is worth it when timed.** 0.7/0.9 thresholds avoid
  all three faults and gain +50 over noop.
- **Early maintenance is too expensive.** The 0.5 threshold spends two extra
  maintenance windows and loses 10 score.
- **Always-maintain is a trap.** 37 maintenance windows drop the score to 130.
- **Q fails at the delayed trade.** The benefit of maintenance is a fault avoided
  much later; the immediate reward is lost production. Some seeds collapse to a
  degenerate always-maintain policy.
- **This is a learned-baseline failure, not a mechanic failure.** The scripted
  threshold solves the task; Q's exploration/credit assignment is the missing
  piece.

## Caveats

- Deterministic gear line; scores are identical across seeds for scripted
  policies.
- The agent maintains the most worn machine only; per-entity choice is not
  modeled.
- Maintenance is 10 ticks vs 60-tick auto-repair; the ratio is a scope choice.
- Faults auto-repair; explicit repair is not part of this task.
- Q is seed-sensitive; do not read the mean as a stable learned baseline.
- Not part of frozen `factory-v0.1`.

## Next

1. **Stabilize Q:** eligibility traces, optimistic initialization, or a
   semi-MDP action that spans the maintenance window.
2. **Per-entity maintenance scheduling:** multiple machines and one crew.
3. **Noisy wear sensors:** prediction quality for normal maintenance.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0009, ADR 0019
- Env: `src/fabline/env/preventive_fault.py`
- Harness: `src/fabline/harness/preventive_fault.py`
- CLI: `python -m fabline preventive-fault`
- Raw results: `results/preventive_fault/` (ignored)
- Task card: `docs/tasks/fault-preventive.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
