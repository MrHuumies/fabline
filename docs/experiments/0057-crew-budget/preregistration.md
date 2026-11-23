# Experiment 0057 — Crew report budget

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-23
- **Type:** P2 multi-agent communication experiment
- **Task:** `factory.power.crew-visibility.v1` (0052)
- **Mechanic:** per-crew report budget (RFC 0018, ADR 0029)
- **Code:** `src/fabline/env/crew_visibility.py`,
  `src/fabline/harness/crew_budget.py`
- **CLI:** `python -m fabline crew-budget`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

How many reports per crew are needed to match shared-local visibility, and how
much does one report lose?

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

- Pilot: seeds 15000–15002. Shared/budget2 710; budget1 650; private 0056
  reference 574.
- Formal: seeds 16000–16004 (5 contiguous, all valid by reset-only check).
- No Q training.
- No dataset artifact.

## Gates

| Gate | Threshold |
|---|---|
| H1 one-report cost | shared local ≥ budget1 + 10 |
| H2 two-report recovery | budget2 ≥ budget1 + 10 |
| H3 two-report parity | budget2 ≥ shared local − 10 |
| H4 private comparison | budget1 ≥ private best + 10 |
| H5 frozen benchmark | unchanged |

## Predictions

- Shared local and budget2 690–720.
- Budget1 620–670.
- Private best 500–590.
- Two reports are enough; one report is the bandwidth threshold.
- If budget1 matches shared, the channel is not bandwidth-bound; report the
  negative.

## Analysis plan

- Report score, CI, success, and per-seed scores for each condition.
- Report report-set coverage and any hidden-target assignments.
- Keep layout, radius, top-K rule, and success threshold fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0018, ADR 0029
- Env: `src/fabline/env/crew_visibility.py`
- Harness: `src/fabline/harness/crew_budget.py`
- CLI: `python -m fabline crew-budget`
- Task card: `docs/tasks/crew-visibility.md`
- Raw results: `results/crew-budget/` (ignored)
- Summary: `docs/experiments/0057-crew-budget/summary.md`
- Prior: [`../0056-crew-private/summary.md`](../0056-crew-private/summary.md)
