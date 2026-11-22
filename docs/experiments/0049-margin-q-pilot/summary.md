# Pilot 0049 — Margin-aware compact Q

- **Status:** pilot negative; not promoted
- **Date:** 2026-11-22
- **Type:** exploratory learned-baseline pilot
- **Follow-up to:** [`0048`](../0048-crew-layout-q/summary.md)
- **Task:** `factory.power.crew-layouts.v1` (0046)
- **Code:** exploratory patch only; not committed
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Do coarse arrival-slack bins fix the compact Q's state aliasing?

Compact Q uses binary reachability (`can`/`cannot` finish). The 0048 losses on
seeds 8003 and 8007 suggested that two layouts with the same closer/reachability
pattern can still have different optimal pairs. A margin-aware state splits each
crew-target reachability into:

- late (`slack < 0`)
- tight (`0 <= slack < 10`)
- comfortable (`slack >= 10`)

That gives `3 × 3 × 3⁴ = 729` initial states instead of 144.

## Setup

- Twin-line 32×16 layout, random crew-B base, 10 evaluation seeds 6000–6009.
- Three Q seeds, 1000 and 2000 training layouts per policy.
- Same action space, reward, and epsilon schedule as compact Q.

## Results

| episodes | Q seed | mean score | success |
|---:|---:|---:|---:|
| 1000 | 0 | 340.0 | 0.30 |
| 1000 | 1 | 340.0 | 0.30 |
| 1000 | 2 | 362.0 | 0.40 |
| 2000 | 0 | 383.0 | 0.40 |
| 2000 | 1 | 384.0 | 0.40 |
| 2000 | 2 | 362.0 | 0.30 |

For comparison, compact Q with 2000 layouts scored 441.0/0.60 on the same
6000–6009 pilot block, and 422.0/0.50 on the fresh 8000–8009 block (0048).

## Why it is not promoted

- **State fragmentation dominates.** 729 states with 2000 episodes is only a
  few visits per state; the binary 144-state table gets many more updates.
- **Binary reachability was already sufficient.** The margin split did not
  recover the seeds where compact Q lost; it lost additional seeds.
- **The aliasing is not mainly arrival margin.** The 70-point losses likely come
  from which bridge is score-critical and from pair interactions, not from
  one-tick timing differences.
- **No evidence of a gain.** All six margin policies are below the weakest
  compact-Q policy on the same block.

The exploratory class was reverted. Do not add margin bins to the compact state.

## Next

Try a **compact-state ensemble** across Q seeds: one 0048 policy already matches
oracle exactly, and the others are within 18–42 points. Averaging Q values or
voting across policies targets Q-seed variance without enlarging the state.

## Artifacts

- Compact Q: [`../0048-crew-layout-q/summary.md`](../0048-crew-layout-q/summary.md)
- Task card: [`../../tasks/crew-layouts.md`](../../tasks/crew-layouts.md)
- Exploratory patch: not committed.
