# Task card — two-crew repair coordination

- **Task ID:** `factory.power.crew-coordination.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run complete; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power
- **Owner:** FABLINE
- **Date:** 2026-11-22

## Phenomenon

Two repair crews with different starting positions must be assigned in parallel
to a loop, a small bridge, and a large bridge. One crew cannot save both
bridges before their deadlines; two crews can, but only if the targets are
matched to the crews.

## Contract

- **Observation:** tick, score, crew positions, and per-wire outage, state,
  deadline, and distance to each crew.
- **Actions:** 16 pairs (noop/loop/small/large for each crew); same-wire
  positive assignments are masked.
- **Crews:** A at the depot, B at the opposite corner.
- **Warnings:** tick 40; failures at 90/110/130.
- **Travel:** 2 × Manhattan; service 40 ticks; jobs run concurrently.
- **Assignment:** one-shot; each crew one job.
- **Reward:** production score gained from the assignment to episode end.
- **Outcome:** final score; success ≥ 150.

## Metrics

- mean score;
- prevented and restored outage;
- aborted jobs;
- travel ticks;
- success rate.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| parallel_nearest | nearest target per crew |
| parallel_greedy | outage per service time |
| oracle | best pair by simulation |
| random | uniform legal pair |
| tabular Q | role/position state |

## Gates

| Gate | Threshold |
|---|---|
| H1 coordination gain | best two-crew scripted ≥ single_edf + 10 |
| H2 oracle gain | oracle ≥ single_edf + 10 |
| H3 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 |
| H4 assignment quality | report duplicates/aborts/pairs |
| H5 budget | 500 training episodes |

## Results (0042)

Seeds 1000, 1001, 1002, 1004, 1005; one episode each.

| policy | score | prevented | success |
|---|---:|---:|---:|
| noop | 46.0 | 0.0 | 0.00 |
| single_edf | 60.0 | 1.0 | 0.00 |
| random | 94.0 | 1.2 | 0.20 |
| parallel_nearest | **260.0** | 2.0 | **1.00** |
| parallel_greedy | **260.0** | 2.0 | **1.00** |
| tabular Q | **260.0** | 2.0 | **1.00** |
| oracle | **260.0** | 2.0 | **1.00** |

All gates pass; the coordination gain is +200. The formal seeds are easy for
every parallel policy; the pilot had nearest/greedy failures on some seeds. See
[`experiments/0042-multi-crew`](../experiments/0042-multi-crew/summary.md).

## Known pitfalls

- **Centralized assignment only.** No per-crew partial views or communication.
- **One-shot.** Not repeated dispatch or crew failure.
- **Fixed bases.** Base positions are a scope choice.
- **Pilot Q is borderline.** Seed 0 failed in the pilot; formal seeds decide.
- If coordination does not add 10 points, retire the slice and move to larger
  layouts or full worker agents.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-22 — card created; two-crew mechanic and gates preregistered.
- 2026-11-22 — formal run: two crews 260 vs single 60; Q 260; all gates pass.
