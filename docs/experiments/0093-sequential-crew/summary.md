# Experiment 0093 — Sequential crew repair

- **Status:** complete (negative on task validity; H1 fails)
- **Date:** 2026-11-28
- **Type:** 0.7.0 Phase 1
- **Task:** `factory.power.crew-sequential.v1` (Phase 1)
- **Code:** `src/fabline/env/sequential_crew.py`,
  `src/fabline/harness/sequential_crew.py`
- **CLI:** `python -m fabline sequential-crew`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.6` is **not** frozen; `factory-v0.5`
  unchanged

## Result in one paragraph

**The Phase 1 task is not valid at the registered coordination gate.** On fresh
seeds 100,010–100,014, the assigned policy scores **93.2** with success 1.00
versus single crew **88.4** and 0.84: a **+4.8** score gain, below the +10 H1
gate, with overlapping confidence intervals. H2 passes (1.00), H3 passes only
because random scores 0 (BC 23.2, Q 17.6), and H4 fails (BC 0.24, Q 0.16). The
pilot's +12 coordination gain did not replicate. Because H1 failed, the
challenge tier does not apply and `factory-v0.6` is not frozen. The task needs a
redesign or retirement, not a tune.

## Formal results

Seeds 100,010–100,014; five episodes per seed:

| Policy | Score | 95% CI | Success | Repairs | Steps |
|---|---:|---:|---:|---:|---:|
| single_crew | 88.4 | [68.4, 104.4] | 0.84 | 2.84 | 50 |
| greedy | 91.2 | [74.2, 105.8] | 0.88 | 2.88 | 50 |
| assigned | **93.2** | [75.0, 108.6] | **1.00** | 3.00 | 50 |
| queue_oracle | 97.2 | [81.8, 110.4] | 1.00 | 3.00 | 50 |
| random | 0.0 | [0.0, 0.0] | 0.00 | 0.04 | 50 |
| independent_q | 17.6 | [4.4, 30.8] | 0.16 | 1.28 | 50 |
| bc | 23.2 | [6.4, 41.6] | 0.24 | 1.28 | 50 |

Cost: Q 528 table entries / 66.5 s training; BC 2 models × 200 iterations /
127.1 s training; messages 0 (Phase 1).

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 coordination | best scripted ≥ single + 10 | **fail**, +4.8 |
| H2 scripted success | best scripted mission completion ≥ 0.60 | **pass**, 1.00 |
| H3 learned gap | best learned ≥ random + 10 | **pass**, +23.2 (BC) |
| H4 learned success | best learned success ≥ 0.60 | **fail**, 0.24 (BC) |
| H5 cost | report parameters, seconds, messages | **pass** |

Oracle gap (queue oracle − best scripted): **+4.0**, diagnostic only.
Challenge tier: **no** — the challenge rule requires H1 and H2 to pass.

## Pilot vs formal

| Quantity | Pilot (100,005–100,009) | Formal (100,010–100,014) |
|---|---:|---:|
| single_crew score | 70.7 | 88.4 |
| assigned score | 82.7 | 93.2 |
| H1 gain | +12.0 | **+4.8** |
| assigned success | 1.00 | 1.00 |
| learned best | 0.0 (Q/BC) | 23.2 (BC) |

The pilot's coordination gain was optimistic. The formal single crew is strong
enough (2.84 of 3 targets repaired) that the second crew adds little score.

## Interpretation

- **The second crew adds only +4.8 score and +0.16 success.** The score CIs
  overlap; the registered +10 score gate fails.
- **The layout/budget does not create enough parallel pressure.** One crew
  already repairs 2.84 of 3 targets on the 32×32 gear line.
- **The learned baselines are weak but H3 is misleading.** Q 17.6 and BC 23.2
  beat random 0, so H3 passes; both are far below the scripted policies.
- **The oracle gap is only +4.0.** The scripted queue policies are close to the
  queue-plan upper bound, so the remaining score headroom is small.
- **Task validity comes before challenge status.** A task that fails H1 is not
  rescued by labeling it a challenge; it needs a different layout or a harder
  single-crew condition.
- **RFC 0032's kill criterion applies:** if sequential crews add no coordination
  gain over the existing one-shot tasks, retire the sequential variant.

## Why not a challenge task

The challenge tier is for valid tasks whose learned baselines miss the success
gate (H1/H2 pass, H3/H4 fail). Here H1 fails, so the task itself is not
validated. Releasing it as a challenge would hide a task-design failure behind
a label. `factory-v0.6` is not frozen and `v0.7.0` is not cut from this result.

## Next

1. **Redesign with a new pre-registration** if the line is kept:
   - a spread yard with graded visibility;
   - more targets or a tighter time budget;
   - a single-crew handicap (e.g., forced start position or repair delay).
   Do not reuse the 0093 seeds, layout, or gates.
2. **Or retire the sequential variant** under RFC 0032's kill criterion and move
   to 0.8.0 spatial grammar.
3. Do not tune the 0093 layout, seed block, budget, or success threshold after
   the formal block. A larger Q/BC budget is a new pre-registration.

## Caveats

- Phase 1 only: shared observation, six actions, no `report`/communication.
- Fixed 32×32 gear/wired-power layout; no layout split.
- Five seeds, five episodes; Q 500 training episodes, BC 50 episodes.
- Success is mission completion; score is a continuous secondary metric.

## Artifacts

- Task card: [`../../tasks/crew-sequential.md`](../../tasks/crew-sequential.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- ADR: [`../../decisions/0043-sequential-crew-scope.md`](../../decisions/0043-sequential-crew-scope.md)
- Raw results: `results/sequential-crew/` (ignored)
