# Task card — crew visibility and communication

- **Task ID:** `factory.power.crew-visibility.v1`
- **Version:** 0.1.0
- **Status:** pilot negative; not promoted; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power and twin-line layout
- **Owner:** FABLINE
- **Date:** 2026-11-23

## Phenomenon

Two crews work on a 32×16 twin-line map. Each crew sees only wires within a
Manhattan radius of its position. The dispatcher can use the union of current
views or a shared report up to a given age. A wire outside both views is
unknown; a crew cannot target it unless it has seen or been told about it. The
survivor after a recall can only recover an orphan it knows.

## Contract

- **Observation:** the twin-line crew observation plus per-role `visible_a`,
  `visible_b`, `known`, and report age. Hidden state/distance/deadline are zero;
  known stale reports keep their last values.
- **Actions:** same 16 pair actions; the mask excludes targets a crew neither
  sees nor has a report for.
- **Visibility:** Manhattan radius `r` from the crew position to the nearest
  wire endpoint.
- **Communication:** shared report memory with age limit `d`; `d=0` means
  current views only.
- **Conditions:** global (radius ∞), local (radius r, d=0), delayed (radius r,
  d>0).
- **Reward:** final production score; success threshold per base task.

## Metrics

- mean score and success;
- local/global gap;
- visible-target coverage;
- report age at assignment;
- orphan recovery when known vs unknown.

## Baselines

| Baseline | Rule |
|---|---|
| global oracle | full-state best pair |
| local oracle | best pair under the visibility mask |
| global nearest/greedy | full-state scripted |
| local nearest/greedy | visible/reported targets only |
| global/local recall-aware | earliest visible bridge |
| random | uniform legal pair |

Q is optional/diagnostic.

## Pilot gates

| Gate | Threshold |
|---|---|
| H1 graded visibility | score changes monotonically over the radius sweep; no binary cliff |
| H2 local cost | global oracle − local oracle ≥ 10 at a mid radius |
| H3 communication gain | delayed report ≥ local + 10 at the same radius |
| H4 orphan knowledge | recovery differs when the orphan is known vs unknown |
| H5 frozen benchmark | unchanged |

## Known pitfalls

- Manhattan radius ignores walls/occlusion.
- The shared report is a memory window, not a message schedule.
- Private per-crew policies and message budgets are follow-ups.
- If the radius is binary again, retire the mechanic.

## Changelog

- 2026-11-23 — card created; pilot contract and gates defined.
