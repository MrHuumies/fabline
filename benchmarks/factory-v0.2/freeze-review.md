# `factory-v0.2` freeze review

- **Status:** frozen as `factory-v0.2`
- **Version:** 0.2.0
- **Date:** 2026-11-24
- **Scope:** 0.3.0 benchmark
- **Related:** [spec](spec.md), [card](card.md), RFC 0029, ADR 0041
- **Expected summary:** [`expected/summary.json`](expected/summary.json)
- **Predecessor:** `factory-v0.1` remains immutable

## Decision

`factory-v0.2` is an extended benchmark built from **10 headline tasks**:

1. **Core block:** seven v0.1 task families on 159 shared episodes, with 20 test
   and 20 shift episodes.
2. **Planning block:** three-bridge triage planning with true-simulator CEM,
   random shooting, scripted policies, and a negative ridge value model.
3. **Calibration block:** fault-onset calibration on the hard context + sensor
   views, including the skilled top-4 entity view.
4. **Causal block:** same-type counterfactual entity removal with target vs
   type-only features.

Fault prediction, stochastic power, next-state, decentralized multi-agent, and
generative layout/recipe are **not frozen**. They are diagnostics or deferred
pilots; they remain runnable and documented.

## Evidence

| Candidate | Gate | Result | Decision |
|---|---|---|---|
| core v0.1 family | 20 test + 20 shift episodes; baseline ordering stable | 159 episodes, 2,948 samples | freeze |
| planning-triage (0076) | CEM true ≥ random + 10; success ≥ 0.60 | CEM true 454 = oracle; random 188; success 1.00 | freeze task; learned value model negative |
| fault calibration (0078) | top-4 balanced ≥ 0.70; ECE ≤ 0.05 | GBDT balanced 0.950 ± 0.011; ECE 0.008 | freeze |
| causal removal (0079) | target GBDT R² ≥ 0.30; target ≥ type-only + 0.20 | target 0.910; type-only −0.300 | freeze |
| decentralized (0077) | local success ≥ 0.60 | local greedy 0.40; private Q 0.47 | defer |
| fault prediction | not saturated | GBDT 1.000, Brier ≈ 0 | diagnostic only |
| stochastic power | not near majority | balanced 0.50–0.56 | diagnostic only |
| generative pilot | validity/diversity gate | not run | defer |
| next-state | not saturated | copy/linear saturated | diagnostic only |

The table cites the task pilots. On the frozen benchmark seeds, the ordering is
the same: planning CEM true 462 = oracle, random 108, CEM learned 232; top-4
calibration GBDT balanced 0.923, ECE 0.0118; causal target GBDT R² 0.987,
type-only −0.074. The learned planner beats random on these seeds but is far
below the true planner; the H3 model-quality gate still fails. The compact
expected summary is the source of truth for the benchmark numbers.

## Scope cuts

- **No layout split.** The draft 20-episode layout split is deferred. The
  shared-suite API supports four splits, and adding a fifth split is a separate
  interface change that was not justified by a stable layout task.
- **No decentralized task.** The local/global gap is real (+288), and private Q
  improves on local greedy (+122), but the local-success gate is open. Freezing
  it would freeze a task whose local baselines are unreliable.
- **No fault prediction or power headline.** Both are useful diagnostics, but
  they fail the "not saturated / not near majority" freeze criterion.
- **No generative task.** The optional pilot did not run and is not
  release-blocking.

## Why the frozen set is 10 tasks

The v0.1 core supplies regression, classification, self-supervised, and control
coverage. The three new tasks add the missing decision and inference surfaces:
planning, calibration, and intervention. Together they form a runnable
10-task benchmark without inflating episode count or freezing known-saturated
tasks.

The 159-episode core is a 3.5× increase over v0.1's 46 episodes. The test and
shift splits are each 20 episodes, up from 6.

## Reproduction and checks

```bash
.venv/bin/python -m fabline benchmark-v02 --out results/factory-v0.2
.venv/bin/python -m fabline benchmark-v02 --out results/factory-v0.2 \
  --check-expected benchmarks/factory-v0.2/expected/summary.json
```

The expected summary is compact (headline metrics only). The comparison uses
`rtol=0.03` and `atol=0.02`. The full check includes planning; CI can use
`--skip-planning --skip-diagnostics` for a cheap check, and the scheduled
workflow runs the full check.

## Freeze gates

- [x] `factory-v0.1` hash and assets unchanged.
- [x] 159 core episodes; 20 test and 20 shift.
- [x] planning, calibration, and causal blocks complete.
- [x] compact expected summary checked in.
- [x] full expected-summary comparison implemented.
- [x] benchmark card, spec, and task cards complete.
- [x] public export scrub remains clean.

## Follow-ups

1. Build the stdlib wizard and viewer QoL.
2. Run the 0.3.0 release audit.
3. Revisit decentralized Q only with a compact state or centralized training.
4. Revisit a transition-model planning baseline as a new pre-registration.

## Changelog

- 2026-11-24 — draft freeze review; core + fault/power + decision blocks.
- 2026-11-24 — frozen at 10 headline tasks; fault/power and next-state are
  diagnostics; layout split and decentralized/generative deferred.
