# Experiment 0077 — Decentralized private-view triage

- **Status:** preregistered (formal run pending)
- **Date:** 2026-11-24
- **Type:** P3 decentralized multi-agent experiment
- **Task:** `factory.multiagent.decentralized.v1` (debug/P3, not in
  `factory-v0.1`)
- **Code:** `src/fabline/env/crew_decentralized.py`,
  `src/fabline/harness/crew_decentralized.py`
- **CLI:** `python -m fabline crew-decentralized`
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Do per-crew local policies retain most of the global oracle score, and can an
independent per-crew Q policy add value over local scripted rules?

## Pilot

One seed (52,000), radius 16, success 600:

| policy | score |
|---|---:|
| local nearest | 600 |
| local greedy | 600 |
| local aware | 180 |
| private Q (30 train episodes) | 180 |
| global oracle | 740 |

The local/global cost is +140. Q was undertrained in the smoke; the formal run
uses 500 episodes per Q seed and three Q seeds.

## Environment

- 48×24 spread layout, three gear lines, capacity 48.
- Private Manhattan radius 16; no shared report memory.
- Warnings 40; failures 90/110/130; recall 100.
- Per-crew action 0..3; joint action `a*4+b`.
- Success ≥ 600.

## Data and seeds

- Pilot: 52,000 (smoke).
- Formal: 54,000–54,004 (5 fresh seeds).
- Q seeds: 0,1,2; 500 training episodes each.
- No dataset artifact.

## Gates

| Gate | Threshold |
|---|---|
| H1 local cost | global oracle ≥ best local scripted + 10 |
| H2 local success | best local scripted success ≥ 0.60 |
| H3 learned policy | private Q ≥ best local scripted + 10 |
| H4 frozen benchmark | unchanged |

## Predictions

- Global oracle 730–750; local nearest/greedy 590–610; local aware 180–350.
- H1/H2 pass; H3 fails (independent Q).
- If Q matches local scripted, report a learned multi-agent result; if not, the
  gap is the independent-Q state/credit assignment.

## Analysis plan

- Report all baselines with score/CI/success.
- Report local cost and Q gap.
- No post-hoc radius/layout changes.

## Kill criteria

- Local cost under 10: visibility is not binding.
- Local success under 0.60: task not reliable.
- No post-hoc Q or layout tuning.

## Transparency note

The one-seed smoke is not a confirmation. Formal seeds are fresh.
