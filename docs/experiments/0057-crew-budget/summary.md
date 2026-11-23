# Experiment 0057 — Crew report budget

- **Status:** complete (all gates pass)
- **Date:** 2026-11-23
- **Type:** P2 multi-agent communication experiment
- **Task:** `factory.power.crew-visibility.v1` (0052)
- **Mechanic:** per-crew report budget (RFC 0018, ADR 0029)
- **Code:** `src/fabline/env/crew_visibility.py`,
  `src/fabline/harness/crew_budget.py`
- **CLI:** `python -m fabline crew-budget`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**Two reports per crew are enough; one report costs 42 points.** On seeds
16000–16004, shared local and budget2 both reach **776.0** (oracle/greedy);
budget1 drops to **734.0** (**−42**); private best is **702.0** (**−32** from
budget1, −74 from shared). Shared/budget2 succeed on every seed; budget1
succeeds on 4/5; private greedy succeeds on 4/5 but nearest/aware are noisy.
All five gates pass.

## Conditions

| Condition | Reports per crew |
|---|---:|
| shared local | all visible positives |
| budget2 | 2 |
| budget1 | 1 |
| private | none |

Each crew reports its top visible positive bridges by outage and distance.
Reports are shared; either crew may be assigned to a reported target.

## Data and seeds

- Pilot: seeds 15000–15002. Shared/budget2 710; budget1 650; private reference
  574.
- Formal: seeds 16000–16004 (5 contiguous, all valid by reset-only check).
- No Q training.
- No dataset artifact.

## Results

| condition | policy | mean score | 95% CI | success |
|---|---|---:|---:|---:|
| shared | nearest | 770.0 | [758.0, 780.0] | 1.00 |
| shared | greedy | 776.0 | [768.0, 780.0] | 1.00 |
| shared | aware | 548.0 | [472.0, 659.0] | 0.20 |
| shared | **oracle** | **776.0** | [768.0, 780.0] | **1.00** |
| budget2 | nearest | 770.0 | [758.0, 780.0] | 1.00 |
| budget2 | greedy | 776.0 | [768.0, 780.0] | 1.00 |
| budget2 | aware | 548.0 | [472.0, 659.0] | 0.20 |
| budget2 | **oracle** | **776.0** | [768.0, 780.0] | **1.00** |
| budget1 | nearest | 734.0 | [650.0, 780.0] | 0.80 |
| budget1 | greedy | 734.0 | [650.0, 780.0] | 0.80 |
| budget1 | aware | 512.0 | [472.0, 552.0] | 0.00 |
| budget1 | **oracle** | **734.0** | [650.0, 780.0] | **0.80** |
| private | nearest | 624.0 | [384.0, 780.0] | 0.80 |
| private | greedy | **702.0** | [618.0, 780.0] | **0.80** |
| private | aware | 624.0 | [384.0, 780.0] | 0.80 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 one-report cost | shared ≥ budget1 + 10 | **pass**, +42 |
| H2 two-report recovery | budget2 ≥ budget1 + 10 | **pass**, +42 |
| H3 two-report parity | budget2 ≥ shared − 10 | **pass**, 0 |
| H4 private comparison | budget1 ≥ private best + 10 | **pass**, +32 |
| H5 frozen benchmark | unchanged | **pass** |

## Interpretation

- **Two reports per crew are sufficient.** Budget2 is exactly shared-local on
  every scripted/oracle condition.
- **One report is the bandwidth threshold.** It loses 42 points and success
  drops from 1.00 to 0.80.
- **Private costs another 32.** Private best 702 trails budget1 734; nearest and
  aware collapse to 624.
- **The top-outage report rule is good enough at K=2.** With three roles, two
  reports cover the critical bridges; at K=1, the third target is often missing.
- **The communication channel is now characterized by age, privacy, and
  bandwidth.**

## Caveats

- Five formal seeds; CIs are wide.
- Reports are current (no age) and selected by a scripted top-outage rule; an
  explicit report policy could differ.
- K=2 is sufficient on this layout; a harder layout may need K=3.
- Success is 600; budget1 oracle 734 but 4/5 success because one seed is low.
- Not part of frozen `factory-v0.1`.

## Next

1. **Explicit report-action policy** rather than top-outage: does the crew
   choose what to report?
2. **Age + budget combined** (one report with delay) to test channel capacity
   and staleness together.
3. **Spread-layout triage/third crew** for repeated failure.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0018, ADR 0029
- Env: `src/fabline/env/crew_visibility.py`
- Harness: `src/fabline/harness/crew_budget.py`
- CLI: `python -m fabline crew-budget`
- Raw results: `results/crew-budget/` (ignored)
- Task card: `docs/tasks/crew-visibility.md`
- Prior: [`../0056-crew-private/summary.md`](../0056-crew-private/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
