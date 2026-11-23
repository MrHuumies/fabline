# Pilot 0061 — Pair-aware replacement policy

- **Status:** pilot negative; not promoted
- **Date:** 2026-11-23
- **Type:** exploratory policy pilot
- **Follow-up to:** [`0060`](../0060-crew-replacement/summary.md)
- **Task:** `factory.power.crew-replacement.v1`
- **Code:** exploratory policy; not committed
- **Benchmark:** none; frozen `factory-v0.1` unchanged

## Question

Can a deadline/value pair heuristic close the replacement handoff gap?

Experiment 0060 has a replacement oracle 476 vs no-replacement 456 (+20), but
the best scripted replacement is 386 vs no-replacement 424 (−38). The current
replacement rules score crews independently. A pair-aware rule that values
preventive vs reactive recovery might capture the handoff.

## Setup

- 32×16 twin-line triage, failure/recall 100, replacement handoff.
- Seeds 19000–19002 (pilot).
- Replacement policies:
  - nearest: nearest A/C pair.
  - greedy: outage per service time.
  - aware: earliest deadlines.
  - deadline: outage if the crew finishes before the bridge deadline; half
    outage if reactive; jointly choose the A/C pair.
  - hybrid: recall-aware initial pair, then the pair rule.
- No oracle in this policy pilot; compare to 0060.

## Results

| policy | seed 19000 | 19001 | 19002 | mean |
|---|---:|---:|---:|---:|
| greedy | 480 | 470 | 520 | **490.0** |
| nearest | 470 | 450 | 520 | 480.0 |
| aware | 470 | 430 | 500 | 466.7 |
| deadline | 470 | 430 | 500 | 466.7 |
| greedy + aware initial | 480 | 460 | 500 | 480.0 |
| nearest + aware initial | 470 | 460 | 500 | 476.7 |
| aware + aware initial | 470 | 430 | 500 | 466.7 |
| deadline + aware initial | 470 | 430 | 500 | 466.7 |

## Why it is not promoted

- **Greedy remains the best replacement rule.** No pair heuristic beats it.
- **Deadline/value scoring ties aware.** It does not capture the oracle’s pair
  choices.
- **Hybrid initial rules do not help.** The recall-aware initial pair plus a
  pair rule is equal or worse than greedy.
- **The handoff gap is policy-limited, not scoring-limited.** A simple
  deadline/value model is insufficient; a learned or simulation-based policy
  would be needed.

The exploratory `ReplacementDeadline` policy was reverted. The 0060 mixed result
stands: oracle +20, best scripted −38, not promoted.

## Next

1. **Full third crew at the initial decision.** This changes the coordination
   structure rather than tuning the pair rule.
2. **Learned replacement policy** with compact state/one-step value.
3. If neither adds a scripted gain, P2 is at its practical ceiling.

## Artifacts

- Handoff: [`../0060-crew-replacement/summary.md`](../0060-crew-replacement/summary.md)
- Task card: [`../../tasks/crew-replacement.md`](../../tasks/crew-replacement.md)
- Exploratory policy: not committed.
