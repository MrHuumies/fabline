# Experiment 0046 — Twin-line crew layouts

- **Status:** complete (H1, H2, H3, H5 pass; H4 fails)
- **Date:** 2026-11-22
- **Type:** P2 larger/random-layout experiment
- **Mechanic:** two-crew assignment on twin-line randomized layouts (RFC 0013,
  ADR 0023)
- **Task:** `factory.power.crew-layouts.v1` (debug/P2, not in `factory-v0.1`)
- **Code:** `src/fabline/env/multi_crew.py`,
  `src/fabline/worlds/factory/generator.py`
- **CLI:** `python -m fabline crew-layouts`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The twin-line layout breaks the 16×8 ceiling.** On seeds 6000–6009, nearest
averages **361.0** and greedy **419.0**, while the oracle averages **441.0** and
single-crew EDF **139.0**. The oracle-best scripted gap is **+22 points**, and
nearest succeeds on only **5/10** seeds at the 400 threshold (oracle 7/10).
Oracle pairs vary (11, 3, 14, 1, 12), so the layout is no longer a single fixed
assignment. Full tabular Q scores **217.0** with **0.00** success and fails the
0.85 quality gate; the larger layout is a real spatial assignment test, but the
learned baseline is not solved.

## Environment

- 32×16 map, two gear lines at independent rows and random x offsets.
- One generator, capacity 24, wired topology; both lines share it.
- Crew A at the first depot; crew B on a random empty cell at least eight
  Manhattan cells from A.
- Targets: zero-outage loop, smallest positive bridge, largest positive bridge.
- Warning 40; failures at 90 (loop), 110 (small), 130 (large).
- One-shot pair assignment; same-wire positive pairs masked.
- Travel = 2 × Manhattan; service 40 ticks.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 0–19.
- Formal evaluation: seeds 6000–6009 (10 contiguous, all valid by reset-only
  check; one episode each).
- Q training: 500 layouts per evaluation seed, starting at
  `55000 + 1000 × evaluation_seed`.
- Train and evaluation layouts are disjoint.
- No dataset artifact.

## Results

| policy | mean score | 95% CI | success | prevented | aborted | travel |
|---|---:|---:|---:|---:|---:|---:|
| noop | 113.0 | [108.0, 117.0] | 0.00 | 0.00 | 0.00 | 0.0 |
| single_edf | 139.0 | [118.0, 180.0] | 0.00 | 0.80 | 0.20 | 16.8 |
| random | 153.0 | [112.0, 211.5] | 0.00 | 0.40 | 0.80 | 42.4 |
| **parallel_nearest** | **361.0** | [259.0, 462.0] | 0.50 | 1.40 | 0.60 | 54.0 |
| **parallel_greedy** | **419.0** | [327.8, 499.0] | 0.60 | 1.50 | 0.50 | 50.4 |
| tabular Q | 217.0 | [154.0, 284.0] | 0.00 | 0.60 | 0.80 | 42.6 |
| **oracle** | **441.0** | [344.4, 520.0] | 0.70 | 1.60 | 0.10 | 32.6 |

Per-seed scores:

| seed | nearest | greedy | Q | oracle | oracle pair |
|---:|---:|---:|---:|---:|---:|
| 6000 | 520 | 300 | 100 | 520 | 11 |
| 6001 | 520 | 520 | 340 | 520 | 11 |
| 6002 | 310 | 310 | 310 | 310 | 3 |
| 6003 | 120 | 520 | 120 | 520 | 14 |
| 6004 | 120 | 120 | 120 | 120 | 1 |
| 6005 | 520 | 520 | 110 | 520 | 11 |
| 6006 | 340 | 340 | 120 | 340 | 12 |
| 6007 | 120 | 520 | 340 | 520 | 14 |
| 6008 | 520 | 520 | 310 | 520 | 11 |
| 6009 | 520 | 520 | 300 | 520 | 11 |

Pairs 11 and 14 are small A / large B and large A / small B; pairs 3, 1, and 12
are loop/noop, noop/loop, and large/noop. The oracle pair is no longer fixed.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 layout gap | oracle ≥ best scripted + 10 | **pass**, +22 |
| H2 coordination gain | best scripted ≥ single_edf + 10 | **pass**, +280 |
| H3 nearest sensitivity | diagnostic: nearest success < oracle success | **confirmed**, 0.50 vs 0.70 |
| H4 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 | **fail**, 49.2%; 0.00 |
| H5 budget | 500 training episodes per evaluation seed | **pass** |

## Interpretation

- **The layout creates a real assignment problem.** Nearest and greedy are no
  longer at the ceiling; the oracle gains 22 points over the best scripted
  policy, and the oracle pair varies.
- **The task is not always fully solvable.** The oracle scores 310–520; seed
  6004 caps at 120 because the random base/wire geometry leaves no feasible
  pair. That is a layout property, not a bug; score is the outcome.
- **Greedy is the strongest scripted baseline.** It is 22 points below oracle
  and succeeds on 6/10 seeds; nearest fails more often, especially when both
  crews are closer to the wrong bridges.
- **Q fails badly.** The larger layout and sparse reward make the tabular state
  insufficient: 217 mean, 0/10 success, 49.2% of oracle. This is a
  representation boundary, not a reason to tune on evaluation seeds.
- **The layout variant is a positive P2 slice.** It makes spatial assignment
  matter without changing the action or observation contract.

## Caveats

- 10 formal seeds; CIs are wide.
- Twin lines are east-facing and share one generator; orientation and multiple
  generators are future work.
- Random crew B can be far from every bridge; the oracle may accept a loss.
- Success 400 is on the two-line score scale and is not comparable to the
  16×8 task.
- Q fails the quality gate; no post-hoc tuning.
- Not part of frozen `factory-v0.1`.

## Next

1. **Test the recall/replan task on twin-line layouts.** The 0045 recovery
   dispatch is a natural next step now that assignment is non-trivial.
2. **Factored or layout-aware Q.** The full tabular state fails; a compact
   distance/orphan feature state may close the gap.
3. **Random orientation or multiple generators.** The next layout axis.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0013, ADR 0023
- Env: `src/fabline/env/multi_crew.py`
- Generator: `src/fabline/worlds/factory/generator.py`
- Harness: `src/fabline/harness/multi_crew.py`
- CLI: `python -m fabline crew-layouts`
- Raw results: `results/crew-layouts/` (ignored)
- Task card: `docs/tasks/crew-layouts.md`
- Prior: [`../0044-crew-robustness/summary.md`](../0044-crew-robustness/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
