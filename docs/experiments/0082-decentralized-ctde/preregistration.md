# Experiment 0082 — Centralized critic, decentralized actors for triage

- **Status:** complete (negative; see [summary](summary.md))
- **Date:** 2026-11-25
- **Type:** P3 decentralized multi-agent follow-up
- **Task:** `factory.multiagent.decentralized.v1` (debug/P3, not in
  `factory-v0.2`)
- **Code:** planned additions to `src/fabline/harness/crew_decentralized.py`
  and the CLI
- **Benchmark:** none; `factory-v0.2` unchanged

## Question

Does centralized training with decentralized execution close the decentralized
success gate after compact-state Q failed?

## Hypothesis

0081 showed that a better private state alone does not change the learned
policy: compact Q, old private Q, and the ensemble all scored 616/0.40. The
binding constraint is credit assignment under partial observability, not the
private-state features.

A centralized critic can use the full state during training to assign credit to
joint actions. A per-crew actor then executes on the private view only. If the
private view is sufficient to identify the actor's role, CTDE should improve
success and mean score over independent Q.

## Environment

Same task as 0077/0081:

- 48×24 spread layout, three gear lines, wired power, capacity 48;
- private Manhattan radius 16 per crew;
- warnings 40; failures 90/110/130; recall 100; success ≥ 600;
- per-crew action 0..3; joint action `a*4 + b`;
- no communication; execution is decentralized.

## Conditions

All conditions are evaluated on the same five seeds.

| Condition | Policy |
|---|---|
| `local_greedy` | outage per own service time |
| `private_q` | 0081 old-state independent Q, 1,000 episodes |
| `compact_q` | 0081 compact-state independent Q, 1,000 episodes |
| `ctde` | centralized critic + decentralized actors, 1,000 episodes |
| `global_oracle` | exhaustive pair with the full view |

`private_q` and `compact_q` are carried forward from 0081 for comparison.

## Centralized critic

The critic is a tabular Q over a compact full-state key and the 16 joint
actions:

```text
phase, crew_b_available, orphaned_role, phase_tick

for each role:
  status             0 ok, 1 degraded, 2 failed
  outage_bucket      min(2, outage // 4)
  service_a_bucket   min(3, service_a // 30)
  service_b_bucket   min(3, service_b // 30)
  slack_a_bucket     0 overdue, 1 <20, 2 <40, 3 otherwise
  slack_b_bucket     same
```

`phase_tick` is the tick within the current phase. The critic uses the full
`CrewReplanEnv` info during training only.

## Decentralized actors

Each actor is a tabular count policy over the 0081 compact private key (16
features) and its four actions. Counts decay by 0.999 per update so early
noop targets cannot dominate the policy after the critic improves.
Probabilities are Laplace-smoothed counts over legal actions. Execution chooses
the highest-count legal action; ties choose the lowest action.

Training step:

1. Actors choose joint exploratory actions (epsilon-greedy, epsilon 1.0 → 0.05).
2. Critic updates with TD(0) on the joint action, using the full next state.
3. After a 50-episode warmup, each actor updates toward the action with the
   highest marginal critic value, where the other crew's action is marginalized
   under its current actor policy.
4. No centralized critic is used at evaluation.

## Budget and seeds

- Formal evaluation seeds: `56,000–56,004` (same as 0081, paired).
- Q seeds: `0, 1, 2`.
- Training episodes: 1,000 per seed; train start `60,000`.
- Alpha 0.2, gamma 0.95.
- Actor update warmup: 50 episodes.
- No reward shaping.

## Metrics

- mean score with 95% bootstrap CI;
- success rate;
- per-seed and per-Q-seed scores;
- CTDE gain over local greedy, private Q, and compact Q;
- local/global gap.

## Gates

| Gate | Threshold |
|---|---|
| H1 task validity | global oracle ≥ local greedy + 10 |
| H2 CTDE skill | CTDE mean ≥ local greedy + 10 |
| H3 CTDE over independent Q | CTDE mean ≥ best of private/compact Q + 10 |
| H4 CTDE reliability | CTDE success ≥ 0.60 |
| H5 frozen benchmark | `factory-v0.2` unchanged |

H2–H4 are the CTDE gates. If they fail, the local-policy line is retired and the
task is reported as oracle/scripted-only.

## Predictions

- `local_greedy` 500–540, success 0.20.
- `private_q` / `compact_q` 600–630, success 0.40.
- `ctde` 640–720, success 0.55–0.70.
- `global_oracle` 750–770, success 1.00.

The prediction is directional: centralized credit assignment should add
+40–100 over independent Q if private execution is sufficient.

## Kill criteria

- CTDE success under 0.60, or mean under independent Q + 10: report a negative
  CTDE result.
- No post-hoc critic-state, actor-state, warmup, or seed tuning.
- If CTDE fails, retire the current local-policy line; do not add another
  representation or critic variant to this task.

## Analysis plan

- Report all conditions with mean/CI/success.
- Report per-Q-seed CTDE results.
- Report paired differences against local greedy and independent Q.
- Report the fraction of the oracle gap closed.

## Transparency note

A one-seed, 50-episode wiring smoke on seed 55,000 scored 170/0.00 and exposed
early count lock-in; counts now decay by 0.999 per update. That smoke is not a
formal result. Formal seeds 56,000–56,004 are fresh and shared with 0081 for a
paired comparison.
