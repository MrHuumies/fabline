# Coverage review — FABLINE 0.4.0

- **Status:** complete; post-release review
- **Date:** 2026-11-26
- **Scope:** experiments 0089–0092, `factory-v0.3`, and the `v0.4.0` surface
- **Related:** [coverage map](coverage-map.md), frozen
  [`factory-v0.3` card](../benchmarks/factory-v0.3/card.md), and the public
  [`v0.4.0` release](https://github.com/MrHuumies/fabline/releases/tag/v0.4.0)

## Verdict

0.4.0 delivered **two positive order tasks, one mixed mechanic pilot, and one
negative baseline track**:

- **order control** is positive: the order stream turns recipe choice into a
  real deadline-aware decision, and tabular Q beats random by 53.8 points;
- **order planning** is positive: CEM matches the exhaustive oracle on a
  five-block plan, with EDF 28.6 points behind;
- **production mix alone** is mixed: component beats gear as a fixed item, but
  switching adds only 3.2 points over the best fixed policy;
- **deep/offline RL** is negative at 10k PPO steps: BC is +6.6 over random and
  PPO is 74.3 below it.

`factory-v0.3` is frozen at 12 headline tasks: the v0.2 core plus order control
and order planning. The common lesson is that **orders, not recipes alone,
supply the decision**. The next step should be a new scope decision, not
another order-control variant or a deep-RL tune.

## Experiment map

| # | Slice | Result | Read |
|---|---|---|---|
| 0089 | Production-mix pilot | component 186 vs gear 150; Q 189.2 (+3.2 over best fixed) | mixed; precondition only |
| 0090 | Order control | value 289.8/1.00; Q 280.2/1.00; random 226.4/0.88 | positive; frozen |
| 0091 | Order planning | CEM = oracle 292.4/1.00; EDF 263.8/1.00 | positive; frozen |
| 0092 | BC/PPO on order control | BC 249.8/0.80 (+6.6); PPO 169.0/0.44 (−74.3) | negative; baseline only |
| — | `factory-v0.3` | 12 tasks; 159 core episodes | frozen |
| — | `benchmark-v03` | compact expected summary; cheap + full CI | shipped |

The 0092 numbers come from its own fresh evaluation block (seeds
77,000–77,004), so its scripted references differ from 0090's seed block
(72,000–72,004): value 272.5, EDF 270.6, and Q 259.5 on 77k. Do not compare
scripted values across the two blocks.

## What 0.4.0 established

### Demand-driven production

- The production-mix mechanic is real and opt-in. The default world hash is
  unchanged.
- Item choice matters at the fixed-policy level: component scores 186 versus
  gear 150. But switching alone adds only 3.2 points over always-component, so
  the mix is a **precondition**, not a standalone scheduling task.
- Deadlines and values make the switch decision pay. With the order stream,
  always-gear falls to 119.6, while value/EDF reach roughly 289 and tabular Q
  reaches 280.2 on the 0090 block.
- The order state is task-layer state, not a new world physics. The envelope,
  recipe, and event log remain the source of truth.

### Order control

- Order control is a valid positive task: H1–H4 pass on fresh seeds.
- **The task is scripted-easy.** EDF (289.0) and value (289.8) both reach
  success 1.00; Q also succeeds 1.00. The learned headroom is the +53.8 over
  random, not a gap to the scripted references.
- Success is saturated at the 160 threshold. **Fulfilled order value is the
  headline**; success is reported as a caveat.
- Tabular Q is reliable at 100 training episodes. It is 9.6 below the value
  policy but well above random.

### Order planning

- The five-block recipe plan is a real finite-horizon decision: oracle 292.4
  versus best scripted EDF 263.8, a +28.6 gap.
- CEM matches the oracle on every formal seed. The plan space is only five
  bits (32 plans), so this is an **exact small-space result**, not evidence that
  CEM solves general planning.
- EDF is a strong scripted baseline (263.8/1.00); the planning task still
  separates it from the oracle, but the headroom is modest.
- This is true-simulator planning. The learned transition-model line from
  0.3.0 (0083/0085/0086) remains closed and is not revived by this result.

### Deep/offline RL

- BC imitates the value expert but reaches only 249.8/0.80, +6.6 over random
  243.2/1.00. It misses the +10 gate.
- PPO reaches 169.0/0.44 at 10k steps, 74.3 below random.
- Training cost is small (about 1.2k parameters; 1.05 s BC, 5.34 s PPO), so the
  negative is a scope/budget result, not a compute artifact.
- The deep/offline RL line is **closed at this budget**. A larger budget is a
  new pre-registration, not a tune of 0092.

### Benchmark and tooling

- `factory-v0.3` is frozen at 12 tasks: the 10 v0.2 tasks plus order control
  and order planning. It reuses the v0.2 core (159 episodes, 20 test and 20
  shift) and is not a new world.
- The compact expected summary is checked in; the cheap `benchmark-v03` check
  passes with zero mismatches, and the scheduled full check matches.
- Production mix and BC/PPO are diagnostics/baselines, not headline tasks.
- The freeze check caught one real defect: the first expected summary included
  machine-dependent planning latency. Timing was removed; the expected summary
  now contains deterministic metrics only. This is a reusable rule for future
  benchmarks.
- `v0.4.0` is published; private and public CI are green on `main` and the
  release tag.

## Negative and saturated results

- **Production mix standalone (0089):** H3 fails. The best schedule gains 3.2
  over best fixed, below the +10 gate, and no policy reaches the 200 success
  threshold. Keep it as a mechanic diagnostic.
- **Order-control success (0090):** saturated at 1.00 for EDF, value, and Q.
  Value is the headline; success is not a discriminating metric.
- **Deep/offline RL (0092):** BC +6.6 and PPO −74.3 versus random. Negative at
  10k steps; do not tune.
- **Demand calibration/causal variants:** not run in 0.4.0. Deferred, not a
  negative result.
- **Generative recipe/layout:** still infeasible on current content (7 unique
  line sequences, diversity 0.080). Not revisited.

## Remaining gaps

1. **Order uncertainty.** Orders are known at reset; there are no arrivals,
   cancellations, or demand shocks. One order/value/deadline regime is tested.
2. **Assembly edge (Phase 1b).** `INGOT + COMPONENT -> GEAR` is not
   implemented. The current mix is recipe-only, so build/route coupling is
   absent.
3. **Planning scale.** Five bits and 32 plans make the oracle small. A larger
   horizon or action space is a new task, not a seed sweep.
4. **Deep RL scope.** The 10k-step negative does not rule out a larger-budget
   method, but that is a new pre-registration.
5. **Demand calibration/causal.** No new view or intervention task was added;
   the prior calibration lesson still applies: skill first, then ECE.
6. **Multi-item breadth.** The order stream covers gear and component demand,
   not a broader item mix or shared-capacity allocation across several lines.

## Recommended next slice

**Make a 0.5.0 scope decision before adding another 0.4.0 variant.**

The leading candidate is **Phase 1b, the assembly edge**: ingot plus component
to gear. It changes the production constraint structure rather than adding
another order-table knob, and it directly addresses the 0089 finding that the
recipe-only mix has no scheduling gap. It requires a new RFC/ADR, a mechanic
card, and a pre-registration.

The alternative is **demand arrival/uncertainty**: reveal orders over time and
test forecast or calibration against realized demand. This is only worth doing
if the new observation carries skill; prior calibration lines were closed when
the views were redundant.

Do not expand `factory-v0.3`; it is frozen. Do not add a third order task
before one of these mechanics changes the decision.

## What not to do next

- tune PPO/BC after the 0092 formal block;
- run another order-control seed, threshold, or reward sweep;
- add another fixed-item policy or tabular-Q variant;
- treat the 32-plan CEM result as general planning evidence;
- add a demand-calibration view without a skill gate;
- add tasks or seeds to frozen `factory-v0.3`;
- reuse the 0092 comparison-block numbers as 0090 references.

## Release state

- Public `v0.4.0` is published; `factory-v0.3` is tagged and immutable.
- `factory-v0.1` and `factory-v0.2` remain frozen; their hashes are unchanged.
- Private and public CI are green on `main` and `v0.4.0`.
- The next experiment is a new pre-registration; `factory-v0.3` is not
  modified.

## Map maintenance

Update the [coverage map](coverage-map.md) and the private roadmap when the
next mechanic passes or fails. Do not add a new benchmark version until the
gate result is known.
