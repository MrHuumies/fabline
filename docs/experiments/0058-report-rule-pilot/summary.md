# Pilot 0058 — One-report selection rules

- **Status:** pilot negative; not promoted
- **Date:** 2026-11-23
- **Type:** exploratory communication-budget pilot
- **Follow-up to:** [`0057`](../0057-crew-budget/summary.md)
- **Task:** `factory.power.crew-visibility.v1` (0052)
- **Code:** exploratory rule knob; not committed
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a better scripted report rule recover the K=1 bandwidth loss?

The 0057 budget experiment showed two reports per crew match shared-local, while
one report loses 42 points. The default K=1 rule reports the highest-outage
visible bridge. This pilot tests nearest, earliest-deadline, and
outage-per-service rules against it.

## Setup

- 48×24 spread layout, radius 16, seeds 15000–15002.
- K=1 report per crew per decision; reports are shared.
- Rules:
  - `outage`: highest outage, then nearest.
  - `nearest`: nearest visible positive.
  - `deadline`: earliest deadline.
  - `efficiency`: highest outage per service time.
- Shared-local reference with the same seeds.

## Results

| condition | nearest | greedy | aware | oracle |
|---|---:|---:|---:|---:|
| shared | 700 | 710 | 603 | **710** |
| K=1 outage | 650 | 650 | 553 | **650** |
| K=1 efficiency | 650 | 650 | 553 | **650** |
| K=1 nearest | 510 | 510 | 413 | **510** |
| K=1 deadline | 510 | 510 | 413 | **510** |

## Why it is not promoted

- **No rule recovers the K=1 loss.** The best rules tie at 650, still 60 below
  shared-local.
- **Nearest/deadline are worse.** They prioritize a nearby/urgent bridge and
  omit the highest-outage bridge; the global assignment then loses more.
- **Bandwidth is binding, not just selection.** With three positive bridges and
  two reports, the dispatcher can see the critical pair. With one report per
  crew, the union often misses the third bridge even under the best rule.
- **A learned report policy is untested.** A policy that chooses reports based
  on the assignment objective could differ, but there is no evidence here that
  scripted selection closes the gap.

The exploratory `report_rule` knob was reverted. The committed 0057 budget
result stands: two reports match shared; one costs 42.

## Next

1. **Age + budget combined** (one report with delay) to separate staleness from
   bandwidth.
2. **Learned report selection** with the assignment objective, if report
   selection is the target question.
3. **K=2** is the practical channel for this layout; move to spread-layout
   triage/third crew instead of more K=1 rules.

## Artifacts

- Budget: [`../0057-crew-budget/summary.md`](../0057-crew-budget/summary.md)
- Task card: [`../../tasks/crew-visibility.md`](../../tasks/crew-visibility.md)
- Exploratory rule knob: not committed.
