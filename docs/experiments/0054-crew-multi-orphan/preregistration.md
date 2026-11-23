# Experiment 0054 — Sequential survivor dispatch

- **Status:** complete; see [`summary.md`](summary.md)
- **Date:** 2026-11-23
- **Type:** P2 repeated-failure experiment
- **Mechanic:** double job failure plus sequential survivor recovery (RFC 0016,
  ADR 0027)
- **Task:** `factory.power.crew-multi-orphan.v1` (debug/P2, not in
  `factory-v0.1`)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Does sequential survivor dispatch turn the one-shot double-orphan collapse into
a useful recovery task?

The one-shot pilot (0053) was negative: A could recover one orphan and greedy
matched oracle. Here both jobs abort at 80, two orphans remain, and A gets a
decision after each recovery (two survivor jobs).

## Environment

- 32×16 twin-line layout, random crew-B base.
- Warnings 40; failures 90/110/130.
- Recall and job failure both at 80; both initial jobs abort.
- A has two survivor jobs; each starts from its current position.
- Action mask: noop or any remaining positive orphan.
- Reward: final production score; success ≥ 400.

## Data and seeds

- Pilot: seeds 0–4. Greedy/aware/oracle 470–500; nearest 420–500; no-replan
  100–120.
- Formal: seeds 11000–11004 (5 contiguous, all valid by reset-only check).
- No Q training; scripted and oracle sequence baselines.
- No dataset artifact.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only, no survivor loop |
| nearest | nearest pair; nearest remaining orphan |
| greedy | outage per service time; highest-outage orphan |
| recall-aware | earliest bridge for A, other for B; highest-outage orphan |
| no-replan | initial pair only |
| oracle | best initial pair and two-action survivor sequence by simulation |

## Gates

| Gate | Threshold |
|---|---|
| H1 recovery gain | best sequential scripted ≥ no-replan + 10 |
| H2 coordination gain | best sequential scripted ≥ single/noop + 10 |
| H3 nearest sensitivity | nearest mean < best sequential mean |
| H4 oracle gap | report oracle vs best scripted; expected shallow |
| H5 frozen benchmark | unchanged |

## Predictions

- Greedy/aware reach 470–500 with success 1.0.
- Nearest is 420–500; no-replan 100–120.
- Oracle matches greedy/aware; the task is a recovery demonstration, not a hard
  triage benchmark.
- The speedup/score gain comes from the second survivor job, not assignment
  subtlety.

## Kill criteria

- Sequential recovery does not beat no-replan by 10.
- The task requires post-hoc changes to failure/recall timing or gates.

## Analysis plan

- Report all baselines with score, CI, success, orphan recoveries, and survivor
  order.
- Report oracle sequences and per-seed scores.
- Keep the layout, failure tick, recall, and two-job budget fixed.
- Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0016, ADR 0027
- Env: `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_multi_orphan.py`
- CLI: `python -m fabline crew-multi-orphan`
- Task card: `docs/tasks/crew-multi-orphan.md`
- Raw results: `results/crew-multi-orphan/` (ignored)
- Summary: `docs/experiments/0054-crew-multi-orphan/summary.md`
- Prior: [`../0053-multi-orphan-pilot/summary.md`](../0053-multi-orphan-pilot/summary.md)
