# Task card — preventive wire maintenance

- **Task ID:** `factory.power.wire-maintenance.v1`
- **Version:** 0.1.0
- **Status:** P1 debug task; formal run complete; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power
- **Owner:** FABLINE
- **Date:** 2026-11-22

## Phenomenon

A wire becomes degraded and is scheduled to fail. The agent sees the warning and
can start a repair before the failure. Preventive repair avoids the outage; a
late repair aborts when the wire fails mid-job. This makes a failure prediction
actionable instead of only ranking failures after they happen.

## Contract

- **Observation:** 8 features — tick, score, outage, degraded, failed,
  time-to-failure, budget, repaired.
- **Actions:** noop; repair the watched wire.
- **Warning:** tick 60.
- **Failure:** tick 220.
- **Repair time:** 140 ticks; atomic.
- **Budget:** 1.
- **Reward:** preventive `outage*15 - 1`; reactive
  `outage*10*remaining/episode - 1`; aborted 0.
- **Outcome:** production score; success ≥ 150.
- **Episode:** 500 ticks; decision interval 10.

## Metrics

- mean production score (bootstrap CI);
- control reward;
- prevention and abort counts;
- success rate.

## Baselines

| Baseline | Rule |
|---|---|
| noop | never repair |
| preventive | repair at the warning |
| reactive | repair after failure |
| late | repair 40 ticks after the warning |
| random | uniform legal action |
| tabular Q | 200 layouts from seed 6000 + 500 × Q seed |

## Results (0035)

Seeds 300–304, 5 episodes each.

| policy | mean score | prevented | aborted | success |
|---|---:|---:|---:|---:|
| noop | 113.6 | 0.0 | 0.0 | 0.00 |
| late | 113.6 | 0.0 | 1.0 | 0.00 |
| reactive | 185.6 | 0.0 | 0.0 | 1.00 |
| random | 231.2 | 0.8 | 0.2 | 0.80 |
| preventive | **260.0** | 1.0 | 0.0 | **1.00** |
| tabular Q | **260.0** | 1.0 | 0.0 | **1.00** |

All five gates pass. Prevention is worth +74.4 over reactive repair and +146.4
over noop. See
[`experiments/0035-wire-maintenance`](../experiments/0035-wire-maintenance/summary.md).

## Known pitfalls

- **Perfect warning.** No noise, false positives, or false negatives yet.
- **One watched wire.** Multi-wire preventive scheduling is a follow-up.
- **Late jobs abort.** The budget is spent and the wire remains failed.
- **Ranked/one-wire action.** This is not end-to-end graph control.
- **Layouts without a single-wire bridge are skipped.**
- **One generator; no crew travel.**
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-22 — card created; warning/degraded mechanic and formal result added.
