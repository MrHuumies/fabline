# Pilot 0051 — Crew visibility and communication

- **Status:** pilot negative; not promoted
- **Date:** 2026-11-23
- **Type:** exploratory multi-agent information pilot
- **Mechanic:** per-crew Manhattan visibility plus shared report age (RFC 0015,
  ADR 0026)
- **Task:** twin-line recall/replanning base (`0047`); not in `factory-v0.1`
- **Code:** exploratory wrapper; not committed
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does the twin-line layout produce a graded partial-view regime, and does a
delayed shared report recover part of the global/local gap?

The 16×8 pilot (0043) was binary; the twin-line layout was the retry. The pilot
also tested whether the survivor can recover an orphan it did not currently see.

## Setup

- 32×16 twin-line recall task, random crew-B base, 5 seeds 0–4.
- Per-crew Manhattan visibility radius; a crew can target a wire only if it
  currently sees it or has a shared report within the age limit.
- Conditions: radius 8, 12, 16, 20, global (∞); delayed reports at radius 12
  with ages 30 and 60.
- Baselines: nearest, greedy, recall-aware, and oracle under the same
  information mask.
- Success threshold 400.

## Results

| condition | nearest | greedy | recall-aware | oracle |
|---|---:|---:|---:|---:|
| local r=8 | 154 / 0.0 | 154 / 0.0 | 154 / 0.0 | 154 / 0.0 |
| local r=12 | 234 / 0.2 | 234 / 0.2 | 154 / 0.0 | 276 / 0.4 |
| local r=16 | 234 / 0.2 | 234 / 0.2 | 154 / 0.0 | 276 / 0.4 |
| local r=20 | 306 / 0.4 | 474 / 0.8 | 362 / 0.4 | 516 / 1.0 |
| delayed r=12 age 30 | 234 / 0.2 | 234 / 0.2 | 154 / 0.0 | 276 / 0.4 |
| delayed r=12 age 60 | 234 / 0.2 | 234 / 0.2 | 154 / 0.0 | 276 / 0.4 |
| global | 306 / 0.4 | 474 / 0.8 | 362 / 0.4 | 516 / 1.0 |

Each cell is mean score / success rate over seeds 0–4.

## Why it is not promoted

- **Still effectively binary.** Radius 8 hides the bridges; 12–16 is a flat
  plateau; 20 is already the global result. There is no smooth middle.
- **The delayed report adds nothing.** At radius 12, ages 30 and 60 are
  identical to the current-view condition. The crews do not move before the
  decision, so there is no useful report to carry.
- **The twin-line wires remain clustered.** Two compact lines still put the
  targets near the same band; a random far base does not create distributed
  information.
- **The middle band is not a coordination task.** At r=12/16 the oracle gains
  over nearest, but the scripted policies are flat and the band collapses to
  global at 20.

## What it tells us

Visibility alone is not enough on this layout. To make partial views and
communication meaningful, the **information must be distributed**: wires and
consumers across the map, branches on different sides, or line-of-sight
occlusion with obstacles. A second requirement is **movement or multiple
decision points**; a single pre-assignment does not generate reports worth
sending.

## Next

1. **Distributed layout:** multiple lines/branches spread across the map, not
   two compact rows. Then re-run the radius sweep before adding communication.
2. **Repeated failure/multiple orphans:** a mechanic that does not depend on
   visibility and directly tests replanning robustness.
3. **Occlusion/line-of-sight:** walls or blocked corridors, if the layout can be
   made spatial.

Do not promote visibility/communication on the current twin-line layout.

## Artifacts

- Mechanic: RFC 0015, ADR 0026
- Task card: [`../../tasks/crew-visibility.md`](../../tasks/crew-visibility.md)
- Base task: [`../0047-crew-replan-layouts/summary.md`](../0047-crew-replan-layouts/summary.md)
- Exploratory wrapper: not committed.
