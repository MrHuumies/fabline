# Pilot 0043 — Partial per-crew visibility

- **Status:** pilot negative; not promoted
- **Date:** 2026-11-22
- **Type:** exploratory P2 pilot; follow-up to
  [`0042`](../0042-multi-crew/summary.md)
- **Mechanic:** two-crew coordination (RFC 0011, ADR 0021)
- **Code:** exploratory patch only; not committed
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does a per-crew visibility radius create a useful partial-view coordination
task?

The two-crew task (0042) is centralized and omniscient. The next P2 question is
whether hiding wires from each crew makes assignment harder in a graded way.

## Setup

- Same two-crew task: loop, small bridge, large bridge; warnings 40; failures
  90/110/130.
- Each crew can only target wires within a Manhattan radius of its position.
- Hidden wire features are masked in the joint observation.
- Sweep radius 4, 6, 8, 10, 12, 14, 16, 20, 999.
- Compare parallel greedy and the visibility-aware oracle over seeds 0–9.

## Results

| radius | greedy mean | oracle mean |
|---:|---:|---:|
| 4 | 61 | 63 |
| 6 | 61 | 66 |
| 8 | 61 | 68 |
| 10 | 81 | 88 |
| 12 | 203 | 204 |
| 14 | 224 | 224 |
| 16 | 185 | 242 |
| 20 | 185 | 260 |
| 999 | 185 | 260 |

## Why it is not promoted

- **Visibility is effectively binary.** At radius ≤10, the bridges are hidden
  from both crews and the task collapses (oracle ~60–88). At radius ≥14, the
  crews see enough to behave like the omniscient task.
- **No graded partial-view regime.** The interesting middle (12–14) gives greedy
  and oracle the same score; the 16–20 range mostly reflects the assignment
  gap already present at radius 999.
- **The layout is too small.** The two bases are either close enough to see the
  bridges or not; there is no spatial ambiguity to resolve.
- **Masking features does not create a new coordination problem** at this
  scale; it removes options.

The exploratory patch was reverted. Do not add a partial-view task on this
layout.

## Next

- **Crew failure/replanning** on the two-crew task: one crew is unavailable and
  the other must cover or replan.
- **Larger/random layouts** so visibility has a graded spatial structure.
- Or return to P2 scope selection: full worker agents vs larger layouts.

## Artifacts

- Exploratory patch: not committed.
- Coverage map: [`../../coverage-map.md`](../../coverage-map.md)
