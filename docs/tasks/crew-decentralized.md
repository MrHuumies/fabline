# Task card — decentralized private-view triage

- **Task ID:** `factory.multiagent.decentralized.v1`
- **Version:** 0.1.0
- **Status:** P3 multi-agent task; formal local/global positive; Q mean positive;
  success gate fails; compact-Q follow-up negative; deferred from
  `factory-v0.2`
- **World:** factory-0.1.0, 48×24 spread layout, wired power
- **Owner:** FABLINE
- **Date:** 2026-11-24

## Phenomenon

Two crews each see only their Manhattan radius-16 neighborhood and choose
their own repair target. They cannot see the other crew's assignment directly.
The task tests decentralized local policies against a global oracle and a
learned per-crew policy.

## Contract

- **Observation:** private per-crew role data from `PrivateVisibilityEnv`:
  known/unknown, degraded/failed, outage, deadline, own distance, service.
- **Actions:** each crew chooses noop/loop/small/large; joint action is
  `a * 4 + b`.
- **Layout:** 48×24 spread, three gear lines, one generator capacity 48.
- **Crews:** A at depot; B at a random base at least eight cells away.
- **Warnings/failures:** 40; 90/110/130; recall 100.
- **Reward:** final production score; success ≥ 600.

## Baselines

| Baseline | Rule |
|---|---|
| local_nearest | nearest known target per crew |
| local_greedy | outage per own service time |
| local_aware | earliest deadline / outage |
| private_q | independent tabular Q per crew |
| global_oracle | exhaustive pair with the full view |

## Metrics

- mean score, CI, success;
- local cost = global oracle − best local scripted;
- learned-policy gap;
- per-seed scores.

## Gates

| Gate | Threshold |
|---|---|
| H1 local cost | global oracle ≥ best local scripted + 10 |
| H2 local success | best local scripted success ≥ 0.60 |
| H3 learned policy | private Q ≥ best local scripted + 10 |
| H4 frozen benchmark | unchanged |

H3 is an empirical gate; a failure is a learned-policy result, not a reason to
hide the task.

## Known pitfalls

- The private view is radius-16, not a true occlusion model.
- Independent Q shares the reward but not state; it is not centralized training.
- The task uses one layout family and one radius.
- Not part of `factory-v0.1`.

## Results (0077)

Seeds 54,000–54,004; Q seeds 0–2, 500 training episodes.

| policy | mean score | success |
|---|---:|---:|
| local nearest | 260 | 0.20 |
| local aware | 260 | 0.20 |
| local greedy | 460 | 0.40 |
| **private Q** | **582** | **0.47** |
| **global oracle** | **748** | **1.00** |

H1 +288 pass; H2 local success 0.40 fail; H3 Q +122 pass. See
[`experiments/0077-decentralized`](../experiments/0077-decentralized/summary.md).

## Follow-up (0081)

The 0077 state aliases phase-relative time, service time, and deadline slack.
Experiment 0081 preregisters a compact relative-geometry Q with equal training
budget and a three-policy ensemble.

- **State:** phase, crew-B availability, orphaned role, phase-relative time; per
  role status, outage, own service, and ordered deadline slack.
- **Conditions:** old private Q at 1,000 episodes, compact Q at 1,000 episodes,
  compact ensemble, local scripted, oracle.
- **Seeds:** formal 56,000–56,004; Q seeds 0–2; train start 60,000.
- **Gates:** compact Q success ≥ 0.60 and mean ≥ best local scripted + 10;
  ensemble success ≥ 0.60 and mean ≥ best single compact Q.

See
[`experiments/0081-decentralized-compact-q/preregistration.md`](../experiments/0081-decentralized-compact-q/preregistration.md).

### Results (0081)

Formal seeds 56,000–56,004; 1,000 training episodes per Q seed:

| policy | mean score | success |
|---|---:|---:|
| local greedy | 532 | 0.20 |
| private Q (old state) | 616 | 0.40 |
| compact Q | 616 | 0.40 |
| compact ensemble | 616 | 0.40 |
| global oracle | 764 | 1.00 |

H1/H2 pass; H3/H4 fail. The compact state and ensemble did not change the
learned policy. The next slice is centralized training with decentralized
execution, not another compact-state variant. See
[`experiments/0081-decentralized-compact-q/summary.md`](../experiments/0081-decentralized-compact-q/summary.md).

## Changelog

- 2026-11-24 — task card created; decentralized actions and baselines defined.
- 2026-11-24 — formal run: global 748, local greedy 460, private Q 582;
  success 0.47 misses 0.60.
- 2026-11-24 — follow-up 0081 preregistered: compact relative-geometry Q and
  ensemble.
- 2026-11-25 — 0081 formal negative: compact Q and ensemble 616/0.40, equal to
  the old state; CTDE is next.
