# Experiment 0048 — Compact layout-aware Q

- **Status:** complete (H2, H4, H5 pass; H1 and H3 fail on the success gate)
- **Date:** 2026-11-22
- **Type:** learned-baseline experiment
- **Task:** `factory.power.crew-layouts.v1` (0046)
- **Mechanic:** none; new Q state representation
- **Code:** `src/fabline/harness/layout_q.py`
- **CLI:** `python -m fabline crew-layout-q`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**The compact Q nearly closes the mean gap, but misses the success gate.** On
fresh seeds 8000–8009, compact Q averages **422.0** against old tabular Q
**233.3** (**+188.7 [136, 253]**) and oracle **442.0** (95.5% of oracle). The
mean quality gate passes, but success is **0.50**, below the pre-registered
0.60. One Q seed matches the oracle exactly (442.0, 0.60 success); the other two
score 424/0.50 and 400/0.40. The compact relative-geometry state is a large
representation win, but not yet a reliable H4 closure.

## Environment

- 32×16, two gear lines, random x offsets, one generator capacity 24.
- Crew A at the first depot; B on a random empty cell at least eight Manhattan
  cells from A.
- Targets: loop, small bridge, large bridge.
- Warning 40; failures 90 (loop), 110 (small), 130 (large).
- One-shot pair assignment; same-wire positive pairs masked.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 6000–6009. Compact Q 442.0/0.60; old Q 217.0/0.00.
- Formal evaluation: seeds 8000–8009 (10 contiguous, all valid by reset-only
  check; one episode each).
- Compact Q: three policies, 2000 layouts each, starting at
  80000 + 1000 × Q seed.
- Old tabular Q: three policies, 500 layouts each, same disjoint ranges.
- Evaluation is zero-shot; train/eval seeds are disjoint.

## Results

| policy | mean score | 95% CI | min | max | success |
|---|---:|---:|---:|---:|---:|
| noop | 114.0 | [111.0, 117.0] | 110 | 120 | 0.00 |
| single_edf | 120.0 | [120.0, 120.0] | 120 | 120 | 0.00 |
| random | 199.0 | [119.0, 282.6] | 110 | 520 | 0.10 |
| parallel_nearest | 382.0 | [280.0, 480.0] | 120 | 520 | 0.60 |
| parallel_greedy | 421.0 | [364.0, 481.0] | 310 | 520 | 0.50 |
| old tabular Q | 233.3 | [191.7, 274.5] | 110 | 520 | 0.07 |
| **compact Q** | **422.0** | [389.0, 461.0] | 310 | 520 | **0.50** |
| **oracle** | **442.0** | [385.0, 500.6] | 310 | 520 | **0.60** |

Compact Q per policy:

| Q seed | mean score | success |
|---|---:|---:|
| 0 | 442.0 | 0.60 |
| 1 | 424.0 | 0.50 |
| 2 | 400.0 | 0.40 |

Per-seed mean scores:

| seed | old Q | compact Q | oracle |
|---:|---:|---:|---:|
| 8000 | 340.0 | 520.0 | 520 |
| 8001 | 246.7 | 520.0 | 520 |
| 8002 | 193.3 | 340.0 | 340 |
| 8003 | 316.7 | 450.0 | 520 |
| 8004 | 193.3 | 460.0 | 520 |
| 8005 | 193.3 | 340.0 | 340 |
| 8006 | 176.7 | 310.0 | 310 |
| 8007 | 380.0 | 450.0 | 520 |
| 8008 | 183.3 | 310.0 | 310 |
| 8009 | 110.0 | 520.0 | 520 |

Oracle pairs: 8000:11, 8001:11, 8002:12, 8003:11, 8004:14, 8005:3, 8006:12,
8007:11, 8008:12, 8009:11.

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 compact Q quality | mean ≥ 0.85 × oracle; success ≥ 0.60 | **fail**, mean pass (95.5%), success fail (0.50) |
| H2 representation gain | compact Q ≥ old Q + 100 | **pass**, +188.7 [136, 253] |
| H3 success | compact Q success ≥ 0.60 | **fail**, 0.50 |
| H4 scripted ceiling | report nearest/greedy/oracle | **pass** |
| H5 budget | 2000 × 3 compact; 500 × 3 old | **pass** |

## Interpretation

- **The compact state is the active ingredient.** It lifts old Q from 233 to
  422 without changing the task or action space. Relative geometry and
  reachability are the right abstraction.
- **One Q seed matches oracle exactly.** Policy 0 scores 442.0/0.60; policies 1
  and 2 score 424/0.50 and 400/0.40. The state is sufficient on this seed block,
  but the Q seed still matters.
- **The mean gate passes; success does not.** Compact Q is 20 points below
  oracle on average [2.9, 39.5] and loses 70 points on seeds 8003 and 8007.
- **The per-seed majority is 0.60.** Across the three policies, six of ten
  seeds have a mean score at or above 400, matching oracle success; the pooled
  per-run success is 0.50. The pre-registered per-run gate is the one reported
  as failed.
- **Not a full H4 closure.** The representation is promising, but a single Q
  policy is not reliable across seeds.

## Caveats

- Three Q policies; Q-seed variance is material.
- The compact key aliases layouts with the same closer/reachability pattern;
  some 70-point losses are aliasing, not training budget.
- Reachability is binary; it loses margin and late-repair score.
- The recall extension would need separate A-deadline and B-recall limits.
- No post-hoc tuning on evaluation seeds.
- Not part of frozen `factory-v0.1`.

## Next

1. **Compact-state ensemble or averaging.** The three policies bracket oracle;
   averaging their Q values or voting across them could remove Q-seed variance.
2. **Add margin features.** Replace binary reachability with coarse slack bins
   to address the 70-point aliasing losses.
3. **Test the compact state on 0047** after fixing the A-deadline/B-recall
   limit split.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Code: `src/fabline/harness/layout_q.py`
- CLI: `python -m fabline crew-layout-q`
- Raw results: `results/crew-layout-q/` (ignored)
- Task card: `docs/tasks/crew-layouts.md`
- Prior: [`../0046-crew-layouts/summary.md`](../0046-crew-layouts/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
