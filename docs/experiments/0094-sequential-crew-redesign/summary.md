# Experiment 0094 — Sequential crew repair redesign (4 targets)

- **Status:** complete (negative on task validity; H1 fails)
- **Date:** 2026-11-28
- **Type:** 0.7.0 Phase 1 redesign
- **Task:** `factory.power.crew-sequential.v1` (4-target condition)
- **Code:** `src/fabline/env/sequential_crew.py`,
  `src/fabline/harness/sequential_crew.py`
- **CLI:** `python -m fabline sequential-crew`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.5` unchanged; `factory-v0.6` not frozen from
  this condition

## Result in one paragraph

**The 4-target redesign is not valid at the registered coordination gate.** On
fresh seeds 110,120–110,124, assigned scores **58.8** with success 1.00 versus
single crew **52.0** and 0.88: a **+6.8** gain, below the +10 H1 gate. H2 passes
(1.00), H3 passes only because random scores 0 (BC 14.4, Q 0.0), and H4 fails
(BC 0.12, Q 0.00). The pilot's +51.7 gain did not replicate: the single crew
repaired 3.76 of 4 targets on the formal seeds. The challenge tier does not
apply because task validity failed, so `factory-v0.6` is not frozen from this
condition.

## Formal results

Seeds 110,120–110,124; five episodes per seed:

| Policy | Score | 95% CI | Success | Repairs | Steps |
|---|---:|---:|---:|---:|---:|
| single_crew | 52.0 | [38.8, 65.2] | 0.88 | 3.76 | 50 |
| greedy | 58.8 | [49.2, 70.6] | 1.00 | 4.00 | 50 |
| assigned | **58.8** | [49.2, 70.6] | **1.00** | 4.00 | 50 |
| queue_oracle | 61.2 | [51.2, 72.2] | 1.00 | 4.00 | 50 |
| random | 0.0 | [0.0, 0.0] | 0.00 | 0.04 | 50 |
| independent_q | 0.0 | [0.0, 0.0] | 0.00 | 0.24 | 50 |
| bc | 14.4 | [0.0, 28.8] | 0.12 | 1.12 | 50 |

Cost: Q table and BC training are reported in the raw JSON; messages 0
(Phase 1).

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 coordination | best scripted ≥ single + 10 | **fail**, +6.8 |
| H2 scripted success | best scripted mission completion ≥ 0.60 | **pass**, 1.00 |
| H3 learned gap | best learned ≥ random + 10 | **pass**, +14.4 (BC) |
| H4 learned success | best learned success ≥ 0.60 | **fail**, 0.12 (BC) |
| H5 cost | report parameters, seconds, messages | **pass** |

Oracle gap (queue oracle − best scripted): **+2.4**, diagnostic only.
Challenge tier: **no** — H1 failed.

## Pilot vs formal

| Quantity | Pilot (110,100–110,102) | Formal (110,120–110,124) |
|---|---:|---:|
| single_crew score | 5.0 | 52.0 |
| assigned score | 56.7 | 58.8 |
| H1 gain | +51.7 | **+6.8** |
| assigned success | 1.00 | 1.00 |

The pilot's single crew was unusually weak; the formal single crew repairs 3.76
of 4 targets, so the second crew adds only +6.8.

## Interpretation

- **The 4-target layout still does not create enough parallel pressure.** One
  crew repairs 3.76 of 4 targets and succeeds on 0.88 of episodes; two crews
  add +6.8 score and +0.12 success.
- **The pilot gain was optimistic.** The same pattern as 0093: the single crew
  is stronger on fresh seeds.
- **The learned baselines are weak.** Q 0.0 and BC 14.4 are far below the
  scripted policies; H3 passes only because random is 0.
- **The oracle gap is +2.4.** The scripted policies are close to the queue-plan
  upper bound.
- **Task validity comes first.** The challenge tier does not apply when H1
  fails.

## Next

The 5-target/500 pilot is the remaining candidate (0095). If it also fails H1,
retire the sequential variant under RFC 0032's kill criterion. Do not tune the
0094 layout, seeds, budget, or gates.

## Caveats

- Phase 1 only: shared observation, six actions, no communication.
- Fixed 32×32 gear/wired-power layout; no layout split.
- Five seeds, five episodes; Q 500 training episodes, BC 50 episodes.
- Success is mission completion; score is continuous.

## Artifacts

- Task card: [`../../tasks/crew-sequential.md`](../../tasks/crew-sequential.md)
- Pre-registration: [`preregistration.md`](preregistration.md)
- ADR: [`../../decisions/0043-sequential-crew-scope.md`](../../decisions/0043-sequential-crew-scope.md)
- Raw results: `results/sequential-crew-redesign/` (ignored)
