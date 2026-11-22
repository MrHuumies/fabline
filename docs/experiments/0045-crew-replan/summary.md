# Experiment 0045 — Crew recall and replanning

- **Status:** complete (H1, H2, H3, H5 pass; H4 fails)
- **Date:** 2026-11-22
- **Type:** P2 multi-agent failure/replanning experiment
- **Mechanic:** known crew recall plus a targeted second dispatch (RFC 0012,
  ADR 0022)
- **Task:** `factory.power.crew-replan.v1` (debug/P2, not in `factory-v0.1`)
- **Code:** `src/fabline/env/crew_replan.py`,
  `src/fabline/harness/crew_replan.py`
- **CLI:** `python -m fabline crew-replan`
- **Pre-registration:** [`preregistration.md`](preregistration.md)
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Result in one paragraph

**A known crew recall creates a real recovery step, but the scripted task is
easy.** Single-crew EDF scores **60.0**; the same first assignment without the
second dispatch scores **100.0**; adding the survivor's recovery dispatch raises
recall-aware to **254.0**, nearest to **254.0**, greedy to **259.0**, and the
oracle to **260.0**. The replan gain is **+154 points**, and every two-crew
policy succeeds on every seed. The assignment itself is not hard: nearest is
already at the oracle minus 6, and recall-aware is not better than nearest.
Full tabular Q scores **144.0** (55.4% of oracle, 44% success) and **fails the
0.85 quality gate**; two-decision credit assignment is the remaining weakness.

## Environment

- Gear line, wired power, one generator, capacity 12.
- Crew A at the depot; crew B at the opposite corner.
- Targets: loop, small bridge, large bridge.
- Warnings at 40; failures at 90 (loop), 110 (small), 130 (large).
- B recall at 100; B's unfinished job aborts.
- Initial assignment: one target per crew; same-wire positive pairs masked.
- Second dispatch: after B leaves and A's first job resolves, A may recover the
  abandoned positive bridge or noop. A loop orphan grants no useful dispatch.
- Travel = 2 × Manhattan; service 40 ticks; jobs run concurrently.
- Reward: final production score; success ≥ 150.

## Data and seeds

- Formal evaluation: seeds 5000–5009 (10 contiguous, all valid by reset-only
  check; one episode each).
- Q training: five policies, 1000 layouts each, on 45000–45999, 46000–46999,
  47000–47999, 48000–48999, and 49000–49999.
- Q evaluation is zero-shot on the formal seeds; train/eval seeds are disjoint.
- Pilot: seeds 0–9.

## Results

| policy | mean score | 95% CI | min | max | success | B aborted | replans |
|---|---:|---:|---:|---:|---:|---:|---:|
| noop | 51.0 | [45.0, 56.0] | 40 | 60 | 0.00 | 0.00 | 0 |
| single_edf | 60.0 | [60.0, 60.0] | 60 | 60 | 0.00 | 0.00 | 0 |
| random | 95.0 | [54.0, 139.0] | 40 | 260 | 0.20 | 0.60 | 3 |
| **parallel_nearest** | **254.0** | [251.0, 257.0] | 250 | 260 | **1.00** | 0.90 | 9 |
| **parallel_greedy** | **259.0** | [257.0, 260.0] | 250 | 260 | **1.00** | 0.80 | 8 |
| **recall_aware** | **254.0** | [251.0, 257.0] | 250 | 260 | **1.00** | 0.80 | 8 |
| recall_aware_no_replan | 100.0 | [60.0, 160.0] | 60 | 260 | 0.20 | 0.80 | 0 |
| tabular Q | 144.0 | [116.4, 168.3] | 40 | 260 | 0.44 | 0.58 | 26 |
| **oracle** | **260.0** | [260.0, 260.0] | 260 | 260 | **1.00** | 0.70 | 7 |

Oracle actions (initial, replan):

| seed | initial | replan | score |
|---:|---:|---:|---:|
| 5000 | 14 | 8 | 260 |
| 5001 | 14 | 8 | 260 |
| 5002 | 11 | 0 | 260 |
| 5003 | 14 | 8 | 260 |
| 5004 | 11 | 12 | 260 |
| 5005 | 14 | 8 | 260 |
| 5006 | 11 | 12 | 260 |
| 5007 | 14 | 0 | 260 |
| 5008 | 14 | 8 | 260 |
| 5009 | 11 | 0 | 260 |

Actions 11 and 14 are `small A / large B` and `large A / small B`; the oracle
chooses the order per layout. A replan of 0 means B completed its job or the
orphan was the zero-impact loop.

Q per training seed:

| Q seed | mean score | success |
|---|---:|---:|
| 0 | 117.0 | 0.30 |
| 1 | 114.0 | 0.30 |
| 2 | 196.0 | 0.70 |
| 3 | 156.0 | 0.50 |
| 4 | 137.0 | 0.40 |

## Gates

| Gate | Threshold | Result |
|---|---|---|
| H1 coordination gain | best two-crew scripted ≥ single_edf + 10 | **pass**, +199 |
| H2 replan gain | recall_aware ≥ no_replan + 10 | **pass**, +154 |
| H3 assignment non-inferiority | recall_aware ≥ nearest − 10 | **pass**, 0 |
| H4 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 | **fail**, 55.4%; 0.44 |
| H5 budget | 1000 episodes per Q policy, 5 policies | **pass** |

## Interpretation

- **The recall creates a real second decision.** Without it, the same first
  assignment loses the abandoned bridge and scores 100; with it, the survivor
  recovers and scores 254.
- **The scripted task is easy.** Nearest and greedy are within 1–6 points of the
  oracle; recall-aware is not better than nearest. The orphan mask makes the
  recovery target obvious, so the hard part is the first assignment, and nearest
  is already good on this small layout.
- **The second dispatch is not a free extra job.** A loop orphan exposes no
  useful dispatch; only an abandoned positive bridge can be recovered.
- **Q fails on the second decision.** Five policies average 144 with high
  variance; seeds 5001, 5002, 5004, 5005, and 5009 average below 150. The full two-step
  tabular state is the bottleneck, not the mechanic.
- **This is a positive but shallow multi-agent slice.** It proves crew-loss
  recovery, not communication, partial views, or repeated failure.

## Caveats

- Known recall tick, not random failure; the agent sees the recall schedule.
- One recall, one orphan, and one second dispatch; no repeated failures.
- Small fixed 16×8 layout; nearest is near-ceiling.
- Q fails the pre-registered quality gate; no tuning on evaluation seeds.
- The second dispatch is restricted to the abandoned positive bridge.
- Not part of frozen `factory-v0.1`.

## Next

1. **Factored Q for replanning.** Keep the scripted first assignment and learn
   the recovery decision, or use a deadline/orphan-aware state. This mirrors the
   0040 → 0041 representation fix and directly targets H4.
2. **Larger/random layouts.** Make nearest fail more often and give the second
   dispatch a real target choice.
3. **Repeated failure or multiple orphans.** The next multi-agent step after
   the one-recall slice.
4. Keep `factory-v0.1` frozen.

## Artifacts

- Mechanic: RFC 0012, ADR 0022
- Env: `src/fabline/env/crew_replan.py`
- Harness: `src/fabline/harness/crew_replan.py`
- CLI: `python -m fabline crew-replan`
- Raw results: `results/crew-replan/` (ignored)
- Task card: `docs/tasks/crew-replan.md`
- Prior: [`../0044-crew-robustness/summary.md`](../0044-crew-robustness/summary.md)
- Coverage review: [`../../coverage-review-0.1.2.md`](../../coverage-review-0.1.2.md)
