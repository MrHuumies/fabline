# Experiment 0095 — Sequential crew repair, 5-target redesign

- **Status:** complete (positive task validity; **challenge tier**; frozen as
  `factory-v0.6` and released in v0.7.0)
- **Date:** 2026-11-28
- **Type:** 0.7.0 Phase 1 redesign
- **Task:** `factory.power.crew-sequential.v1` (5-target condition)
- **Code:** `src/fabline/env/sequential_crew.py`,
  `src/fabline/harness/sequential_crew.py`
- **CLI:** `python -m fabline sequential-crew`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** [`factory-v0.6`](../../../benchmarks/factory-v0.6/card.md)
  (challenge; `factory-v0.5` unchanged)

## Result in one paragraph

**The 5-target task is valid and freezes as a challenge.** On fresh seeds
110,150–110,154, assigned scores **33.6** with success 1.00 versus single crew
**12.0** and 0.28: a **+21.6** coordination gain, well above the +10 H1 gate.
H2 passes (1.00), H5 passes, but the learned baselines fail: Q scores 0.0 and BC
scores 9.2 with success 0.20. H3 misses by 0.8 (+9.2 vs +10) and H4 is far below
0.60. Because H1/H2 pass and H3/H4 fail, the task is frozen as a **challenge
task**; H4 is not lowered. Oracle gap is +5.2.

## Formal results

Seeds 110,150–110,154; five episodes per seed:

| Policy | Score | 95% CI | Success | Repairs | Steps |
|---|---:|---:|---:|---:|---:|
| single_crew | 12.0 | [3.2, 29.6] | 0.28 | 3.48 | 50 |
| greedy | 32.4 | [20.6, 46.8] | 1.00 | 5.00 | 50 |
| assigned | **33.6** | [20.6, 49.4] | **1.00** | 5.00 | 50 |
| queue_oracle | 38.8 | [24.0, 55.2] | 1.00 | 5.00 | 50 |
| random | 0.0 | [0.0, 0.0] | 0.00 | 0.00 | 50 |
| independent_q | 0.0 | [0.0, 0.0] | 0.00 | 0.84 | 50 |
| bc | 9.2 | [1.6, 24.2] | 0.20 | 2.48 | 50 |

Cost: Q table entries and BC model metadata are in the raw JSON; no message
cost (Phase 1).

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 coordination | best scripted ≥ single + 10 | **pass**, +21.6 |
| H2 scripted success | best scripted mission completion ≥ 0.60 | **pass**, 1.00 |
| H3 learned gap | best learned ≥ random + 10 | **fail**, +9.2 (BC) |
| H4 learned success | best learned success ≥ 0.60 | **fail**, 0.20 (BC) |
| H5 cost | report parameters, seconds, messages | **pass** |

Oracle gap (queue oracle − best scripted): **+5.2**, diagnostic.
Challenge tier: **yes**.

## Pilot vs formal

| Quantity | Pilot (110,100–110,102) | Formal (110,150–110,154) |
|---|---:|---:|
| single_crew score | 0.0 | 12.0 |
| assigned score | 31.7 | 33.6 |
| H1 gain | +31.7 | **+21.6** |
| scripted success | 0.67 | 1.00 |

The formal single crew was stronger than the pilot, but the coordination gain
remains large and H2 improves to 1.00.

## Interpretation

- **Five targets with 500 ticks creates real parallel pressure.** One crew
  repairs 3.48 of 5 targets and scores 12.0; two crews repair all five and score
  33.6.
- **The task is valid.** H1 +21.6 and H2 1.00 on fresh seeds.
- **The learned baselines do not solve it.** Q is 0 and BC is 9.2/0.20; H3
  misses by 0.8 and H4 is far below the gate.
- **This is a challenge, not a failed task.** The scripted/oracle references
  are useful; the learned failure is reported in the card and expected summary.
- **No H4 lowering.** A larger Q/BC budget or a communication action is a new
  pre-registration.
- **Earlier conditions were negative:** 0093 (3 targets) H1 +4.8; 0094
  (4 targets) H1 +6.8. They are not frozen.

## Next

- `factory-v0.6` is frozen as a challenge benchmark for the 0.7.0 release.
- Phase 2 (local views, `report`, communication) and stochastic faults/POMDP
  remain future work; do not add them to this freeze.
- Do not tune the 0095 block or the learned baselines.

## Caveats

- Phase 1: shared observation, six actions, no communication.
- Fixed 32×32 gear/wired-power layout; no layout split.
- Five seeds, five episodes; Q 500 training episodes, BC 50 episodes.
- Success is mission completion; score is continuous.
- `queue_oracle` is a queue-plan upper bound, not a full joint-action oracle.

## Artifacts

- Task card: [`../../tasks/crew-sequential.md`](../../tasks/crew-sequential.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- Benchmark: [`../../benchmarks/factory-v0.6/card.md`](../../../benchmarks/factory-v0.6/card.md)
- ADR: [`../../decisions/0043-sequential-crew-scope.md`](../../decisions/0043-sequential-crew-scope.md)
- Raw results: `results/sequential-crew-5target/` (ignored)
