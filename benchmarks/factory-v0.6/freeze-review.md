# `factory-v0.6` freeze review

- **Status:** frozen as `factory-v0.6` (challenge tier)
- **Version:** 0.6.0
- **Package release:** 0.7.0
- **Date:** 2026-11-28
- **Scope:** 0.7.0 Phase 1 sequential crews
- **Related:** [card](card.md), [spec](spec.md), ADR 0043, RFC 0032,
  experiments 0093–0095
- **Predecessor:** `factory-v0.5` remains immutable

## Decision summary

`factory-v0.6` freezes **one challenge task**, `crew-sequential`, on the opt-in
wired-power layout. It is not a new world and does not change the default
factory hash.

The task is valid: on the formal 0095 block, two scripted crews beat one crew by
+21.6 score and +0.72 success, and complete all five targets. The learned
baselines do not solve it: Q scores 0 and BC scores 9.2 with success 0.20. The
task is therefore frozen as a **challenge**, not a standard learned-control
task. H4 is not lowered.

## Evidence

Formal block, 2026-11-28, seeds 110,150–110,154, five episodes each:

| Policy | Score | Success |
|---|---:|---:|
| single_crew | 12.0 | 0.28 |
| greedy | 32.4 | 1.00 |
| assigned | 33.6 | 1.00 |
| queue_oracle | 38.8 | 1.00 |
| random | 0.0 | 0.00 |
| independent_q | 0.0 | 0.00 |
| bc | 9.2 | 0.20 |

Gates:

| Gate | Result |
|---|---|
| H1 coordination | pass, +21.6 |
| H2 scripted success | pass, 1.00 |
| H3 learned gap | fail, +9.2 (BC) |
| H4 learned success | fail, 0.20 (BC) |
| H5 cost | pass |

Oracle gap: +5.2, diagnostic.

## Why 5 targets

The earlier conditions were not valid:

- 0093 (3 targets, 500 ticks): assigned 93.2 vs single 88.4, **+4.8** — H1 fail.
- 0094 (4 targets, 500 ticks): assigned 58.8 vs single 52.0, **+6.8** — H1 fail.
- 5 targets / 400 ticks: too hard; scripted success 0.13.
- **5 targets / 500 ticks: H1 +21.6, H2 1.00** — valid.

The 5-target condition is the smallest tested condition that makes one crew
insufficient while two crews remain viable. The 0093/0094 pilots were
optimistic; the formal single crew was stronger on fresh seeds in both cases.
The 5-target formal result is the frozen evidence.

## Challenge-tier decision

The learned baselines miss H3 by 0.8 and H4 by 0.40. The task is still useful:
the scripted/oracle gap is real, the action space is factorized, and the
observation contract is public. It is labeled challenge in the card, spec, and
expected summary. Do not tune Q/BC or lower H4; a larger budget is a new
pre-registration.

## Scope cuts

- Phase 1 only: shared observation, six actions, no `report`/communication.
- Stochastic faults and POMDP maintenance are 0.8.0.
- Fixed layout; no layout split or 3-crew scaling.
- No deep MARL baseline.

## Freeze gates

- [x] Default world hash and v0.1–v0.5 assets unchanged.
- [x] Task validity H1/H2 passes on fresh seeds.
- [x] Learned failure is reported honestly and labeled challenge.
- [x] Expected summary is checked in; no timing fields.
- [x] Runner and check command are documented.
- [x] Task card, ADR, and RFC agree on the 5-target challenge scope.
- [x] Public/private export matches the frozen tree.
- [x] Tag-triggered `factory-v0.6` check exists.

## Risks

- The learned baselines are far below the scripted policies; do not read the
  challenge as a solved control task.
- The queue oracle is a scripted-plan upper bound, not a full joint-action
  oracle.
- The fixed 32×32 layout and shared observation limit generality; Phase 2 is a
  new contract.
- A larger Q/BC budget or communication action is a new pre-registration.
