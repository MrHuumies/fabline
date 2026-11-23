# Task card — three-bridge survivor triage

- **Task ID:** `factory.power.crew-triage.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run complete; all gates pass; not in
  `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power and twin-line layout
- **Owner:** FABLINE
- **Date:** 2026-11-23

## Phenomenon

Three positive bridges are active on a 32×16 twin-line map. Two crews are
assigned initially; job failure and recall at tick 100 abort any active jobs.
Crew A survives with two recovery jobs. Some initial jobs finish before 100, so
the first assignment matters; A then chooses which two of the remaining bridges
to restore and in what order. One bridge is left unresolved.

## Contract

- **Observation:** three-role crew observation (the legacy `loop` role is the
  medium bridge and has positive outage).
- **Actions:** initial 16 pair actions; survivor decisions choose noop or any
  unresolved positive bridge.
- **Failure/recall:** 100; active jobs abort.
- **Replan budget:** two survivor jobs; each starts from A's current position.
- **Travel:** 2 × Manhattan; service 40 ticks.
- **Reward:** final production score; success ≥ 300.

## Metrics

- mean score and success;
- initial jobs completed vs aborted;
- survivor choices and order;
- oracle gap and nearest/greedy/aware spread.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| nearest | nearest pair; nearest unresolved target |
| greedy | outage per service time |
| recall-aware | earliest bridge for A, other for B |
| no-replan | initial pair only |
| oracle | best initial pair and two-action survivor sequence |

## Gates

| Gate | Threshold |
|---|---|
| H1 oracle gap | oracle ≥ best scripted + 10 |
| H2 coordination gain | best scripted ≥ single/noop + 10 |
| H3 nearest sensitivity | nearest mean < oracle |
| H4 oracle success | oracle success ≥ 0.60 |
| H5 frozen benchmark | unchanged |

## Results (0055)

Seeds 12000–12004; failure/recall 100; two survivor jobs.

| policy | mean score | success |
|---|---:|---:|
| noop | 90.0 | 0.00 |
| single_edf | 90.0 | 0.00 |
| nearest | 284.0 | 0.80 |
| greedy | **378.0** | **0.80** |
| recall-aware | 326.0 | 0.80 |
| no-replan | 92.0 | 0.00 |
| oracle | **456.0** | **1.00** |

All gates pass: oracle +78 over greedy, nearest 284, oracle success 1.00. Oracle
sequences vary across seeds. See
[`experiments/0055-crew-triage`](../experiments/0055-crew-triage/summary.md).

## Known pitfalls

- The internal `loop` role is the medium positive bridge.
- One survivor, two jobs, three bridges; one remains unresolved.
- Some seeds may have no feasible full recovery.
- If greedy/nearest matches oracle, report the shallow ceiling.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-23 — card created; three-bridge triage contract and gates defined.
- 2026-11-23 — formal run: oracle 456, greedy 378, nearest 284; all gates
  pass.
