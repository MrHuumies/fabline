# Experiment 0037 — Preventive machine maintenance

- **Status:** complete (H1/H3 pass; H2 fails; see [`summary.md`](summary.md))
- **Date:** 2026-11-22
- **Type:** P1 phase 1C normal-fault preventive experiment
- **Mechanic:** machine-wear maintenance (RFC 0009, ADR 0019)
- **Task:** `factory.fault.preventive.v1` (debug/P1, not in `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does maintaining a worn machine before the fault threshold beat waiting for the
fault and auto-repair?

The normal fault mechanic already exposes wear. This experiment adds a
10-tick maintenance action that resets wear; waiting leads to a fault and a
60-tick auto-repair. The agent must choose when to spend the planned downtime.

## Environment

- Gear line, faults enabled.
- Wear threshold 20; wear per craft 1.
- Fault auto-repair 60 ticks; preventive maintenance 10 ticks.
- Actions: noop, or maintain the most worn non-faulted machine.
- Reward: production score delta.
- Outcome: final score; success ≥ 240.
- Episode 500 ticks; decision interval 10.

## Baselines

| Baseline | Rule |
|---|---|
| noop | never maintain |
| maintain_0.5 | maintain at 50% of the wear threshold |
| maintain_0.7 | maintain at 70% |
| maintain_0.9 | maintain at 90% |
| always | maintain whenever any wear exists |
| random | uniform legal action |
| tabular Q | wear-bucket state; 500 training layouts from 7000+ |

## Data and seeds

- Evaluation: seeds 400–404, 5 episodes each = 25 episodes.
- Q training: 500 layouts from 7000 + 1000 × Q seed.
- No dataset artifact; the generated gear line is deterministic.

## Gates

| Gate | Threshold |
|---|---|
| H1 prevention gain | best threshold ≥ noop + 30 |
| H2 Q quality | Q ≥ 0.95 × best threshold; Q success ≥ 0.80 |
| H3 timing | maintain_0.5 ≤ best threshold − 5 |
| H4 seed consistency | report per-seed scores; no gate |
| H5 budget | report maintenance and fault counts |

## Predictions

- Noop scores about 200 with 3 faults.
- maintain_0.7 and maintain_0.9 score 250 with no faults; 0.9 uses fewer
  maintenance actions.
- maintain_0.5 scores about 240; the extra maintenance is too early.
- Always-maintain scores about 130; random about 187.
- Q learns the wear threshold and scores about 243–250.

## Kill criteria

- Best threshold does not beat noop by 30.
- Early maintenance is not worse than the best threshold.
- Q is below 0.85 × best or succeeds below 0.6.
- The result is dominated by one seed.
- The task requires post-hoc changes to wear, repair, maintenance, or gates.

## Analysis plan

- Report score, bootstrap CI, maintenance count, fault count, and success.
- Report Q per-seed scores.
- Keep the wear/repair/maintenance timings fixed after the formal run.
- Keep `factory-v0.1` frozen.

## Artifacts

- Env: `src/fabline/env/preventive_fault.py`
- Harness: `src/fabline/harness/preventive_fault.py`
- CLI: `python -m fabline preventive-fault`
- Task card: `docs/tasks/fault-preventive.md`
- Raw results: `results/preventive_fault/` (ignored)
- Summary: `docs/experiments/0037-preventive-fault/summary.md`
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
