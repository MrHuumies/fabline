# Mechanic RFC 0015 — Private crew views and communication

- **Status:** accepted; promoted on the distributed layout (0052)
- **Author:** FABLINE
- **Date:** 2026-11-23
- **Related:** ADR 0026, RFC 0012, ADR 0022, RFC 0013, ADR 0023

## Summary

Add an opt-in visibility layer to the twin-line crew task. Each crew sees only
wires within a radius of its current position. The dispatcher can use the union
of current crew views, or a delayed shared report; wires outside the view are
unknown. The survivor can recover an orphan only if it has seen it or received a
report. This tests the multi-agent information gap that the fixed 16×8 layout
could not expose.

## Motivation

The 16×8 partial-view pilot (0043) was binary: radius ≤10 hid the bridges and
≥14 was effectively omniscient. The twin-line 32×16 layout has nonlocal
distances and a random crew-B base, so visibility should have a graded middle.
The compact-Q work is near its ceiling; the next useful question is
coordination under local information, not another Q state.

## Rules

- Base task: twin-line recall/replanning (`factory.power.crew-replan-layouts.v1`)
  or twin-line assignment (`factory.power.crew-layouts.v1`).
- Each crew has a visibility radius `r` around its current position.
- A wire is visible to a crew if its nearest endpoint is within `r` Manhattan
  cells.
- The shared report channel stores the last observation of a wire seen by
  either crew. With report age `d`, the dispatcher may use a report if
  `tick - last_seen <= d`; otherwise the wire is unknown.
- The action mask only permits a crew to target a wire it currently sees or has
  a report for.
- Conditions:
  - `global`: full state (radius ∞).
  - `local`: union of current views, no memory (`d = 0`).
  - `delayed`: local views plus reports up to age `d`.
- Private per-crew policies and explicit message budgets are follow-ups; the
  first slice uses the centralized pair action with per-crew visibility.

## What it tests

- Is there a graded partial-view regime on the twin-line layout?
- What is the cost of local information versus global?
- Does a delayed report recover part of the gap?
- Can the survivor recover an orphan it did not currently see?
- Do scripted nearest/greedy/recall-aware policies degrade gracefully?
- Is a learned policy needed, or are the scripted effects already useful?

## Observation impact

Per-role features are masked for wires unknown to a crew. `info` exposes
`visible_a`, `visible_b`, `known`, and `report_age`. Hidden role state,
distance, and deadline are zero; known stale reports keep their last values.
The action mask is filtered by per-crew knowledge.

## Data impact

- New debug task `factory.power.crew-visibility.v1`.
- Frozen `factory-v0.1` is unchanged.

## Determinism

- Visibility depends only on seeded crew positions and wire endpoints.
- Reports are deterministic at decision ticks.
- Crews remain control state, not factory hash state.

## Tests

- Visibility distance and per-crew masks.
- Hidden features are zero; known stale reports persist.
- Report age expiry.
- Local action masks exclude unknown targets.
- Global behavior is unchanged.
- Frozen benchmark regression.

## Alternatives

- **Private per-crew policies.** Deferred; the centralized pair action isolates
  the information effect first.
- **Message budget.** Deferred; start with report age.
- **Line-of-sight/occlusion.** Deferred; Manhattan radius is the first slice.
- **Repeated failure.** A fallback if visibility is binary again.

## Decision

The twin-line pilot was negative (0051), but the distributed `spread_gear`
layout (48×24, result 16, report age 60) gives a useful local block: global
oracle 778, local 680, delayed60 734. See ADR 0026 and experiment 0052. Promoted
as `factory.power.crew-visibility.v1`.
