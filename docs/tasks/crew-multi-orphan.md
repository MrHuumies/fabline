# Task card — sequential survivor dispatch

- **Task ID:** `factory.power.crew-multi-orphan.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run complete; positive but shallow; not in
  `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power and twin-line layout
- **Owner:** FABLINE
- **Date:** 2026-11-23

## Phenomenon

Both crews' initial jobs abort at tick 80, leaving two orphaned bridges. Crew A
survives and can recover one orphan, then another if time and budget permit. The
task tests sequential recovery, travel order, and whether the first assignment
keeps a feasible recovery path.

## Contract

- **Observation:** twin-line crew observation plus `orphaned_roles` and phase.
- **Actions:** initial 16 pair actions; survivor decisions choose noop or a
  remaining positive orphan.
- **Failure:** both active initial jobs abort at 80.
- **Recall:** B is gone at 80; A is the only survivor.
- **Replan budget:** two survivor jobs (default; first decision after failure,
  second after the first recovery if an orphan remains).
- **Travel:** 2 × Manhattan; service 40 ticks; each survivor job starts from
  A's current position.
- **Reward:** final production score; success ≥ 400.

## Metrics

- mean score and success;
- number of orphans recovered;
- survivor travel and order;
- no-replan gap;
- nearest vs greedy/oracle.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only, no survivor loop |
| nearest | nearest pair; nearest remaining orphan at each replan |
| greedy | outage per service time; highest-outage orphan |
| recall-aware | earliest bridge for A, other for B; highest-outage orphan |
| no-replan | initial pair only |
| oracle | best initial pair and survivor sequence by simulation |

Q is optional; this is a scripted scheduling task.

## Gates

| Gate | Threshold |
|---|---|
| H1 recovery gain | best sequential scripted ≥ no-replan + 10 |
| H2 coordination gain | best sequential scripted ≥ single/noop + 10 |
| H3 nearest sensitivity | nearest mean < best sequential mean (diagnostic) |
| H4 oracle gap | report oracle vs best scripted; no hard gap |
| H5 frozen benchmark | unchanged |

## Results (0054)

Seeds 11000–11004; failure/recall 80; two survivor jobs.

| policy | mean score | success |
|---|---:|---:|
| noop | 118.0 | 0.00 |
| single_edf | 118.0 | 0.00 |
| nearest | 438.0 | 1.00 |
| greedy | **460.0** | **1.00** |
| recall-aware | **460.0** | **1.00** |
| no-replan | 118.0 | 0.00 |
| oracle | **460.0** | **1.00** |

H1/H2/H3/H5 pass; H4 is shallow (greedy matches oracle). Oracle sequence
`[11,12,8]` on every seed. See
[`experiments/0054-crew-multi-orphan`](../experiments/0054-crew-multi-orphan/summary.md).

## Known pitfalls

- Both jobs abort; the task is a recovery demonstration, not a normal
  assignment.
- Greedy/recall-aware may match oracle; report the shallow ceiling.
- Only one survivor and two jobs; no third crew.
- Twinline 32×16; not the spread layout.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-23 — card created; sequential survivor contract and gates defined.
- 2026-11-23 — formal run: recovery +342; nearest 438, greedy/aware/oracle 460;
  shallow, greedy matches oracle.
