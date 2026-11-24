# Experiment 0081 — Compact relative-geometry Q for decentralized triage

- **Status:** preregistered (implementation and formal run pending)
- **Date:** 2026-11-24
- **Type:** P3 decentralized multi-agent follow-up
- **Task:** `factory.multiagent.decentralized.v1` (debug/P3, not in
  `factory-v0.2`)
- **Code:** planned additions to `src/fabline/env/crew_decentralized.py` and
  `src/fabline/harness/crew_decentralized.py`
- **CLI:** planned `python -m fabline crew-decentralized-compact`
- **Benchmark:** none; `factory-v0.2` is immutable

## Question

Does a compact relative-geometry Q state, combined with a small Q ensemble,
close the decentralized success gate without centralized training?

## Hypothesis

The current private-Q state aliases two decision-relevant quantities:

- absolute tick and distance buckets, rather than time remaining in the current
  phase;
- outage/status, without the **service time** and **deadline slack** that make
  a role feasible or infeasible.

A compact state that encodes service and slack should learn a better local
policy. A three-policy ensemble should reduce Q-seed variance. Together they
should reach **success ≥ 0.60** and **mean ≥ best local scripted + 10**.

## Environment

Same task as 0077:

- 48×24 spread layout, three gear lines, wired power, capacity 48;
- private Manhattan radius 16 per crew;
- warnings 40; failures 90/110/130; recall 100; success ≥ 600;
- per-crew action 0..3; joint action `a*4 + b`;
- no shared reports, no centralized execution, no communication.

## Conditions

All conditions are evaluated on the same five fresh seeds.

| Condition | State / policy |
|---|---|
| `local_nearest` | nearest known target per crew |
| `local_greedy` | outage per own service time |
| `local_aware` | earliest deadline / outage |
| `private_q_1000` | the 0077 private-Q state, 1,000 training episodes |
| `compact_q` | the compact state below, 1,000 training episodes |
| `compact_ensemble` | mean action value across the three compact-Q seeds |
| `global_oracle` | exhaustive pair with the full view |

`private_q_1000` is the controlled representation baseline. The 0077 500-episode
result (582, success 0.47) is historical context, not a paired condition.

## Compact state

The state is per crew and uses only information available in that crew's private
view. The key is:

```text
phase                 0 initial, 1 replan
crew_b_available      0/1
orphaned_role         -1 / 0 / 1 / 2
phase_tick            min(3, phase_tick // 25)

for each role in ROLES:
  status              0 ok, 1 degraded, 2 failed, 3 unknown
  outage_bucket       min(2, outage // 4)
  service_bucket      0 unknown, else min(3, own_service // 30)
  slack_bucket        3 if unknown/not degraded/no deadline
                      0 if deadline - tick - service < 0
                      1 if < 20
                      2 if < 40
                      3 otherwise
```

`phase_tick` is the tick within the current phase: `tick` in the initial phase,
and `max(0, tick - 100)` in the replan phase. `own_service` is
`distance * travel_ticks_per_cell + repair_ticks`; it is 0 for an unknown role.
The slack bucket is a single ordered value, not a set of separate margin
features, so it does not repeat the 0049 margin-bin fragmentation.

## Training

- Q seeds: `0, 1, 2`.
- Training episodes: 1,000 per seed, equal for `private_q_1000` and `compact_q`.
- Training seed start: `60,000 + q_seed * 1,000`.
- Alpha 0.2, gamma 0.95, linear epsilon 1.0 → 0.05.
- Ensemble: mean Q value over the three compact policies for each legal action;
  ties choose the lowest action.
- Evaluation seeds: `56,000–56,004` (fresh, five seeds).
- No reward shaping, no communication, no centralized execution.

## Metrics

- mean score with 95% bootstrap CI;
- success rate;
- per-seed and per-Q-seed scores;
- local/global gap and ensemble gain.

## Gates

| Gate | Threshold |
|---|---|
| H1 task validity | global oracle ≥ best local scripted + 10 |
| H2 compact skill | compact Q mean ≥ best local scripted + 10 |
| H3 compact reliability | compact Q success ≥ 0.60 |
| H4 ensemble | ensemble success ≥ 0.60 and mean ≥ best single compact Q |
| H5 frozen benchmark | `factory-v0.2` unchanged |

The task's original local-success gate (best local scripted ≥ 0.60) is reported
as a caveat; it is not a gate on the learned policy. H3/H4 are the learned-policy
gates.

## Predictions

- `local_greedy` 440–500, success 0.35–0.45.
- `private_q_1000` 540–620, success 0.45–0.55.
- `compact_q` 600–680, success 0.55–0.65.
- `compact_ensemble` 620–700, success 0.60–0.72.
- `global_oracle` 730–760, success 1.00.

The prediction is directional: the compact state should beat the old state at
equal training budget; the ensemble should reduce seed variance.

## Kill criteria

- Compact Q success under 0.50, or mean under best local scripted + 10: report a
  negative representation result.
- Ensemble not better than the best single compact Q on success: report a
  negative ensemble result.
- No post-hoc state, bucket, seed, radius, or training-budget tuning after the
  formal block.
- If H3/H4 fail, the next pre-registration is centralized training with
  decentralized execution, not another compact-state variant.

## Analysis plan

- Report all conditions with mean/CI/success.
- Report per-Q-seed compact and ensemble results to expose seed variance.
- Report the paired difference against `private_q_1000` and `local_greedy`.
- Report the local/global gap and the fraction of the oracle gap closed.
- Do not tune the world, layout, or reward.

## Transparency note

No compact-Q pilot has been run yet. A one-seed smoke on seed 55,000 is allowed
after implementation for wiring checks only; it is not a formal result. Formal
seeds 56,000–56,004 are fresh and disjoint from the 0077 seeds 54,000–54,004.
