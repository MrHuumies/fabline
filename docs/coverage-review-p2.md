# Coverage review — P2 multi-agent

- **Status:** complete; P2 checkpoint
- **Date:** 2026-11-23
- **Scope:** experiments 0042–0059; opt-in tasks on `main`, not the frozen
  `factory-v0.1` benchmark
- **Related:** [coverage map](coverage-map.md), [roadmap](roadmap.md), frozen
  [benchmark card](../benchmarks/factory-v0.1/card.md)

## Verdict

P2 has a broad multi-agent surface: two-crew assignment, crew recall and
sequential recovery, twin-line layouts, distributed visibility, private views,
report age, report budgets, and three-bridge triage. The strongest results are
the **two-crew coordination gain**, the **twin-line assignment gap**, the
**distributed local/global visibility gap**, and **triage with failure at 100**.

The line is now **saturated in several places**:

- compact Q is near its state-abstraction ceiling;
- report age, privacy, and bandwidth are characterized;
- one-report selection does not recover the K=1 loss;
- the spread layout does not widen triage;
- several tasks are positive but shallow, with greedy matching oracle.

Do not add another Q variant or another visibility sweep. The next mechanic
should add a new coordination axis, not tune the existing ones.

## Experiment map

| # | Slice | Result | Read |
|---|---|---|---|
| 0042 | Two-crew assignment | 260 vs 60; all parallel policies 260 | positive, shallow |
| 0043 | Partial views on 16×8 | pilot negative | radius binary |
| 0044 | 40-seed robustness | nearest 255.5, greedy 245, Q 225.5 | robust, seed-sensitive |
| 0045 | Crew recall/replan | recovery +154; nearest 254, oracle 260 | positive, shallow |
| 0046 | Twin-line assignment | oracle 441, greedy 419, nearest 361 | positive layout gap |
| 0047 | Recall + twin-line | recovery +240; oracle-greedy +9 | near-miss; not promoted |
| 0048 | Compact Q | 422 vs old 233, oracle 442; success 0.50 | representation win, gate miss |
| 0049 | Margin-aware Q | 340–384 | negative pilot |
| 0050 | Compact-Q ensemble | 430 vs oracle 448; success 0.50 | variance fixed, gate miss |
| 0051 | Visibility on twin-line | binary; reports add nothing | negative pilot |
| 0052 | Distributed visibility | local cost +98; delayed60 +54 | positive |
| 0053 | One-shot multi-orphan | greedy/aware/oracle 280–330 | negative pilot |
| 0054 | Sequential survivor | recovery +342; greedy=oracle 460 | positive, shallow |
| 0055 | Three-bridge triage | oracle 456, greedy 378 | positive, real gap |
| 0056 | Private vs shared | shared local +40, delayed +74 | positive |
| 0057 | Report budget | K=2 matches shared; K=1 −42 | positive bandwidth threshold |
| 0058 | K=1 report rules | no rule recovers the loss | negative pilot |
| 0059 | Spread triage | greedy=oracle 600 | negative pilot |

## What P2 established

### Coordination

- Two crews beat one crew decisively when deadlines make a single crew
  insufficient.
- The twin-line layout creates a real assignment gap; nearest/greedy are no
  longer at the oracle ceiling.
- Three-bridge triage with failure at 100 creates an oracle gap (+78 over
  greedy) and non-trivial sequences.

### Information and communication

- Distributed 48×24 layout makes local visibility graded at radius 16.
- Delayed shared reports recover part of the local/global gap.
- Private per-crew policies lose 40–74 points versus shared views.
- Two reports per crew match shared-local; one report costs 42 points.
- Scripted report selection at K=1 does not recover the loss; bandwidth is
  binding.

### Learned baselines

- The old tabular Q failed on twin-line layouts.
- Compact relative-geometry Q is a large representation win (233 → 422), but
  success remains 0.50; one seed aliases.
- Margin bins and a larger state were negative; ensemble fixed variance but not
  success.
- Q is not needed for the strongest results; scripted/oracle comparisons carry
  the P2 story.

## Negative and saturated results

- Partial views on the 16×8 and twin-line layouts are binary/stepwise.
- Recall plus twin-line loses the layout gap (+9 vs +10 gate).
- Compact Q and its ensemble miss the 0.60 success gate.
- Margin-aware Q fragments the table.
- One-shot double-orphan collapses to one bridge.
- Sequential survivor is positive but greedy matches oracle.
- One-report selection rules do not recover the K=1 bandwidth loss.
- Spread-layout triage does not widen the 0055 gap.

## Remaining gaps

1. **Third crew / replacement.** Handoff and parallel recovery are the largest
   untested multi-agent axis.
2. **Asymmetric triage.** Values, deadlines, and repair costs can make order
   matter; the current greedy rule is often optimal.
3. **Explicit report actions and age + budget.** The channel is characterized
   but not jointly controlled by the policy.
4. **Larger/random topology.** Three lines are still a controlled layout; a
   true random factory topology remains open.
5. **Planning/world models, deep RL, offline RL.** Still absent; outside P2.

## Recommended next slice

**Third crew / replacement on the triage task.** It is the largest orthogonal
multi-agent gap:

- three crews, three bridges, one crew fails/recalled;
- a replacement or third crew tests handoff and parallel recovery;
- compare two-crew + replacement, three-crew parallel, EDF, nearest, greedy,
  oracle;
- gates: third crew/handoff ≥ best two-crew + 10, oracle ≥ best scripted + 10,
  success, frozen benchmark unchanged.

If the third crew does not add a meaningful gain, the P2 multi-agent line is
near its practical ceiling; move to random topology or P3.

## Release state

- Public `v0.1.2` and its assets are unchanged.
- All P2 tasks are opt-in on `main`; frozen `factory-v0.1` hash remains
  `5f0d54f...`.
- Private and public CI green at the time of this review.

## Map maintenance

Update the [coverage map](coverage-map.md) and [roadmap](roadmap.md) when the
next slice is accepted or rejected. Do not add another Q or visibility variant
without a new named question.
