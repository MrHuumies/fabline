# Experiment 0044 — Seed robustness of two-crew coordination

- **Status:** complete (H1, H2, H4, H5 pass; H3 diagnostic confirms mild
  seed sensitivity)
- **Date:** 2026-11-22
- **Type:** evaluation robustness; no new mechanic
- **Mechanic:** two crews, parallel travel + repair (RFC 0011, ADR 0021)
- **Task:** `factory.power.crew-coordination.v1` (unchanged from 0042)
- **Code:** `src/fabline/env/multi_crew.py`,
  `src/fabline/harness/multi_crew.py`
- **CLI:** `python -m fabline crew-robustness`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The two-crew coordination gain is robust over 40 seeds, but the five-seed 0042
block was mildly optimistic.** Parallel nearest averages **255.5** (97.5%
success) and parallel greedy **245.0** (92.5%) against single-crew EDF **60.0**;
the oracle is **260.0** on every seed. The nearest-minus-single gain is
**+195.5 [186.5, 200.0]**, and the oracle-minus-nearest gap is only
**+4.5 [0.0, 13.5]**. Pooled tabular Q reaches **225.5** (86.7% of oracle,
83.5% success), passing the 0.85 quality gate but trailing the scripted
heuristic by 30 points. The 0042 five-seed sample was not an artifact; it was a
slightly easy block. The task is a valid positive coordination benchmark, but
nearest is near-ceiling; the learned baseline is the part with headroom.

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

- Evaluation: seeds 3000–3039 (40 contiguous, one episode each). A reset-only
  validity check confirmed all 40 before any policy was scored.
- Q training: five independent policies, 500 layouts each, on 40000–40499,
  41000–41499, 42000–42499, 43000–43499, and 44000–44499.
- Q evaluation is zero-shot on all 40 evaluation seeds; training and evaluation
  seeds are disjoint.
- No post-hoc seed selection.

## Results

| policy | mean score | 95% CI | min | max | success | prevented | travel | below 150 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| noop | 47.0 | [45.0, 49.3] | 40 | 60 | 0.00 | 0.00 | 0.0 | 40 |
| single_edf | 60.0 | [60.0, 60.0] | 60 | 60 | 0.00 | 1.00 | 7.0 | 40 |
| random | 72.5 | [55.5, 94.9] | 40 | 260 | 0.10 | 1.10 | 28.1 | 36 |
| **parallel_nearest** | **255.5** | [246.5, 260.0] | 80 | 260 | **0.975** | 1.98 | 35.8 | 1 |
| **parallel_greedy** | **245.0** | [229.3, 260.0] | 50 | 260 | **0.925** | 1.93 | 32.8 | 3 |
| tabular Q (pooled) | 225.5 | [215.0, 235.2] | 40 | 260 | 0.835 | 1.74 | 31.9 | 6 |
| **oracle** | **260.0** | [260.0, 260.0] | 260 | 260 | **1.000** | 2.00 | 36.5 | 0 |

Paired differences:

| comparison | mean | 95% CI |
|---|---:|---:|
| parallel_nearest − single_edf | +195.5 | [186.5, 200.0] |
| oracle − parallel_nearest | +4.5 | [0.0, 13.5] |

Q per training seed:

| Q seed | mean score | success | seeds below 150 |
|---|---:|---:|---:|
| 0 | 228.8 | 0.85 | 6 |
| 1 | 228.8 | 0.85 | 6 |
| 2 | 239.0 | 0.90 | 4 |
| 3 | 203.3 | 0.72 | 11 |
| 4 | 227.8 | 0.85 | 6 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 coordination gain | parallel_nearest mean ≥ single_edf + 10 | **pass**, +195.5 |
| H2 oracle gain | oracle mean ≥ single_edf + 10 | **pass**, +200.0 |
| H3 seed sensitivity | diagnostic: the easy-seed caveat is confirmed if nearest or greedy success < 0.95 | **confirmed**, greedy 0.925; nearest 0.975 |
| H4 Q quality | pooled Q ≥ 0.85 × oracle; success ≥ 0.60 | **pass**, 86.7%; 0.835 |
| H5 protocol | all 40 seeds, no exclusions, disjoint Q training | **pass** |

## Interpretation

- **Parallelism is the gain, and it survives a larger sample.** Single-crew EDF
  is identical on all 40 seeds; nearest and greedy are 195–200 points ahead on
  average.
- **The 0042 five-seed block was easy, not unrepresentative.** Nearest drops
  from 260 to 255.5 and greedy from 260 to 245 over 40 seeds. The pilot's four
  failures in ten seeds overstated the failure rate; here nearest fails one seed
  and greedy fails three.
- **The oracle pair is still always action 11** (small for crew A, large for
  crew B) on all 40 seeds. The task is about recognizing that assignment, not
  about discovering a different pair.
- **Nearest is near-ceiling.** Its 4.5-point oracle gap and 97.5% success leave
  little room for a coordination benchmark. The failures are informative:
  nearest scores 80 on seed 3003, and greedy scores 50 on 3003, 3024, and 3039.
- **Q is the non-saturated baseline.** Pooled Q is 30 points below nearest,
  with 33 of 200 policy-seed runs below 150. It passes the pre-registered gate
  narrowly; the gap is layout generalization, not a training-seed accident
  (means 203–239 across five policies).
- **The task remains centralized and one-shot.** It does not test partial
  views, communication, failure, or replanning.

## Caveats

- 40 layouts from one 16×8 gear scenario; larger or random layouts may differ.
- One episode per layout; the layouts are deterministic.
- Q uses a fixed role/position state and 500 training layouts; the result is a
  tabular baseline, not a tuned MARL method.
- Success ≥ 150 is a chosen threshold; the score distribution is also reported.
- Centralized assignment; no per-crew observations or communication limits.
- Not part of frozen `factory-v0.1`.

## Next

1. **Crew failure/replanning** on the two-crew task: one crew becomes
   unavailable and the survivor must cover or replan. This is the clearest
   missing multi-agent question now that the centralized gain is robust.
2. **Larger/random layouts** to make nearest fail more often and to give
   partial views a graded spatial structure. The 0043 pilot was negative on the
   current small layout.
3. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0011, ADR 0021
- Env: `src/fabline/env/multi_crew.py`
- Harness: `src/fabline/harness/multi_crew.py`
- CLI: `python -m fabline crew-robustness`
- Raw results: `results/crew-robustness/` (ignored)
- Task card: `docs/tasks/multi-crew.md`
- Prior experiment: [`../0042-multi-crew/summary.md`](../0042-multi-crew/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
