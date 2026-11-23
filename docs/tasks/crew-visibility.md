# Task card — crew visibility and communication

- **Task ID:** `factory.power.crew-visibility.v1`
- **Version:** 0.1.0
- **Status:** formal run complete; all pilot gates pass; not in `factory-v0.1`
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

## Results (0052)

Seeds 10000–10004; 48×24 spread layout; radius 16.

| condition | nearest | greedy | aware | oracle |
|---|---:|---:|---:|---:|
| global | 772 / 1.0 | 778 / 1.0 | 654 / 0.6 | 778 / 1.0 |
| local r16 | 650 / 0.6 | 656 / 0.6 | 666 / 0.6 | 680 / 0.6 |
| delayed30 | 650 / 0.6 | 656 / 0.6 | 666 / 0.6 | 680 / 0.6 |
| delayed60 | 728 / 0.8 | 734 / 0.8 | 666 / 0.6 | 734 / 0.8 |

Local cost is +98 for oracle; delayed60 recovers +54 of it. All five gates
pass. See
[`experiments/0052-crew-visibility`](../experiments/0052-crew-visibility/summary.md).

## Private per-crew policies (0056)

Seeds 14000–14004; radius 16; report age 60.

| condition | best scripted | oracle | success |
|---|---:|---:|---:|
| global | 762 | 762 | 1.00 |
| shared local | 606 | 614 | 0.60 |
| shared delayed60 | 640 | 648 | 0.60 |
| private | 574 | — | 0.40 |

Sharing views beats private best by +40 (local) and +74 (delayed60); the report
adds +34 over local. Private nearest/aware collapse to 296 with zero success.
All gates pass. See
[`experiments/0056-crew-private`](../experiments/0056-crew-private/summary.md).

## Known pitfalls

- Manhattan radius ignores walls/occlusion.
- The shared report is a memory window, not a message schedule.
- Private per-crew policies and message budgets are follow-ups.
- If the radius is binary again, retire the mechanic.

## Changelog

- 2026-11-23 — card created; pilot contract and gates defined.
- 2026-11-23 — formal run: local cost +98, delayed60 +54, all gates pass.
- 2026-11-23 — private views: shared local +40 and delayed60 +74 over private;
  private nearest/aware 296; all gates pass.
