# Task card — crew recall and replanning

- **Task ID:** `factory.power.crew-replan.v1`
- **Version:** 0.1.0
- **Status:** P2 debug task; formal run complete; not in `factory-v0.1`
- **World:** factory-0.1.0 with opt-in wired power
- **Owner:** FABLINE
- **Date:** 2026-11-22

## Phenomenon

Two repair crews are dispatched in parallel to a loop, a small bridge, and a
large bridge. Crew B is recalled at tick 100. If B is still working, its job
aborts and its bridge is left without a crew. After crew A finishes its first
job, A can recover B's abandoned bridge. The task tests whether the survivor's
second dispatch matters and whether a policy can choose the first assignment
that keeps the critical bridge covered.

## Contract

- **Observation:** tick, score, crew positions, per-wire outage/state/deadline,
  distances to each crew, phase, B availability, recall countdown, and the
  orphan role.
- **Actions:** 16 initial pairs (noop/loop/small/large for each crew), with
  same-wire positive pairs masked. At the second decision, the mask is noop plus
  the abandoned positive bridge; an orphaned loop grants no useful dispatch.
- **Crews:** A at the depot, B at the opposite corner.
- **Warnings:** tick 40; failures at 90/110/130.
- **Recall:** B leaves at 100; its unfinished job aborts.
- **Travel:** 2 × Manhattan; service 40 ticks; jobs run concurrently.
- **Reward:** final production score; success ≥ 150.
- **Second dispatch:** only after B is recalled and A's first job resolves.

## Metrics

- mean score and success rate;
- B jobs aborted at recall;
- prevented repairs and total aborts;
- travel ticks;
- second-dispatch choices.

## Baselines

| Baseline | Rule |
|---|---|
| noop | no assignment |
| single_edf | crew A only |
| parallel_nearest | nearest positive pair; nearest unresolved target at replan |
| parallel_greedy | outage per service time |
| recall_aware | A earliest bridge, B the other; recover the orphan |
| recall_aware_no_replan | same first assignment, no second dispatch |
| random | uniform legal action |
| oracle | best initial pair and replan by simulation |
| tabular Q | role/recall/orphan state, 1000 training layouts |

## Gates

| Gate | Threshold |
|---|---|
| H1 coordination gain | best two-crew scripted ≥ single_edf + 10 |
| H2 replan gain | recall_aware ≥ recall_aware_no_replan + 10 |
| H3 assignment non-inferiority | recall_aware ≥ parallel_nearest − 10 |
| H4 Q quality | Q ≥ 0.85 × oracle; success ≥ 0.60 |
| H5 budget | 1000 episodes per Q policy |

## Results (0045)

Seeds 5000–5009; one episode each; five Q policies trained on disjoint blocks.

| policy | mean score | success | B aborted |
|---|---:|---:|---:|
| single_edf | 60.0 | 0.00 | 0.0 |
| parallel_nearest | 254.0 | 1.00 | 0.9 |
| parallel_greedy | **259.0** | **1.00** | 0.8 |
| recall_aware | 254.0 | 1.00 | 0.8 |
| recall_aware_no_replan | 100.0 | 0.20 | 0.8 |
| tabular Q | 144.0 | 0.44 | 0.6 |
| oracle | **260.0** | **1.00** | 0.7 |

H1, H2, H3, and H5 pass; H4 fails (Q 55.4% of oracle, 0.44 success). The second
dispatch is worth +154 points over no-replan, but nearest is already within 6
points of oracle. See
[`experiments/0045-crew-replan`](../experiments/0045-crew-replan/summary.md).

## Known pitfalls

- **Known recall, not random failure.** The recall tick is observable from reset.
- **One recall, one second dispatch.** No repeated failures or multiple orphans.
- **Small fixed layout.** Nearest is a strong baseline; the task may be easy
  for scripted policies.
- **Q may fail.** Two-decision credit assignment is harder than the one-shot
  task; report the gap rather than tuning on evaluation seeds.
- **Zero-impact loop orphan.** A loop orphan does not grant a useful second
  dispatch.
- Not part of `factory-v0.1`.

## Changelog

- 2026-11-22 — card created; recall/replanning contract and gates preregistered.
- 2026-11-22 — formal run: replan +154; nearest 254, greedy 259, Q 144.0
  fails H4.
