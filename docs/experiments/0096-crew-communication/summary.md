# Experiment 0096 — Local-view crew communication

- **Status:** complete (negative on H1; no benchmark freeze)
- **Date:** 2026-11-28
- **Type:** 0.7.1 Phase 2 communication
- **Task:** `factory.power.crew-communication.v1` (debug candidate)
- **Code:** `src/fabline/env/crew_communication.py`,
  `src/fabline/harness/crew_communication.py`
- **CLI:** `python -m fabline crew-communication`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; `factory-v0.6` unchanged; no `factory-v0.7` freeze

## Result in one paragraph

**Local reporting does not improve this task; it makes it worse.** On fresh
seeds 120,010–120,014, local no-report scores **28.4** with success **0.92**,
while local report scores **17.2** with success **0.72**. The shared
full-information policy scores 28.4/1.00; random is 0. Reporting costs a
decision step and the local no-report policy already explores well enough. H1
fails on success (−0.20) and score (−11.2); H2/H3/H4/H5 pass. The pilot's +0.20
success gain did not replicate, and no challenge tier applies because the
communication gain failed. Phase 2 communication is closed on this layout.

## Formal results

Seeds 120,010–120,014; five episodes per seed:

| Policy | Score | 95% CI | Success | Messages | Delivered |
|---|---:|---:|---:|---:|---:|
| shared | 28.4 | [21.6, 35.2] | 1.00 | 0.00 | 0.00 |
| local_no_report | **28.4** | [21.6, 35.2] | **0.92** | 0.00 | 0.00 |
| local_report | 17.2 | [10.2, 24.0] | 0.72 | 3.36 | 6.60 |
| random | 0.0 | [0.0, 0.0] | 0.00 | 0.68 | 1.20 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 communication | report success ≥ no-report + 0.10 | **fail**, −0.20 |
| H2 shared validity | shared success ≥ 0.60 | **pass**, 1.00 |
| H3 report over random | report score ≥ random + 10 | **pass**, +17.2 |
| H4 report success | report success ≥ 0.60 | **pass**, 0.72 |
| H5 cost | messages/delivered/cost reported | **pass** |

Score gain over local no-report: **−11.2**, secondary.
Challenge tier: **no** — H1 failed.

## Pilot vs formal

| Quantity | Pilot (120,000–120,004) | Formal (120,010–120,014) |
|---|---:|---:|
| local_no_report score | 18.7 | 28.4 |
| local_no_report success | 0.47 | **0.92** |
| local_report score | 22.0 | 17.2 |
| local_report success | 0.67 | 0.72 |
| success gain | +0.20 | **−0.20** |

The pilot was optimistic about local no-report; on fresh seeds it succeeds on
0.92, leaving no room for a report gain.

## Interpretation

- **Local views plus exploration are strong on this 32×32, five-target layout.**
  The no-report policy already finds and repairs almost everything.
- **Reporting is a net cost.** It consumes a decision step, and the message
  budget/delay does not buy enough search time.
- **The shared policy is an upper bound, not a decodable target.** The local
  no-report policy matches its score and nearly matches its success.
- **The pilot did not replicate.** As in 0093/0094, the fresh-seed single/local
  baseline was stronger than the pilot suggested.
- **No challenge tier.** The challenge rule requires H1/H2 to pass; H1 failed.

## Next

- Do not tune the radius, report budget, delay, or cost after this formal block.
- Retire the communication line on this layout, or test a genuinely different
  layout/report contract in a new pre-registration.
- Keep `factory-v0.6` unchanged; no `factory-v0.7` freeze from 0096.
- A learned local policy is still a follow-up, but it would not rescue the
  negative communication result.

## Caveats

- Scripted policies only; no learned local baseline in 0096.
- Local radius 6, report budget 2, delay 1 decision, cost 0.5.
- Fixed 32×32 gear/wired-power layout; no layout split.
- Success is mission completion; score is continuous.

## Artifacts

- Pre-registration: [`preregistration.md`](preregistration.md)
- RFC: [`../../rfcs/0032-uncertain-repair.md`](../../rfcs/0032-uncertain-repair.md)
- ADR: [`../../decisions/0043-sequential-crew-scope.md`](../../decisions/0043-sequential-crew-scope.md)
- Raw results: `results/crew-communication/` (ignored)
