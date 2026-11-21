# Mechanic RFC — <name>

- **Status:** draft | accepted | rejected
- **Author:** <name>
- **Date:** YYYY-MM-DD
- **Related:** ADR NNNN

## Summary

One paragraph: what is the mechanic, and what new research does it enable?

## Motivation

Which research axis or task needs this? What can the current world not answer?
Link the task card or experiment.

## Rules

- Inputs:
- Outputs:
- State changes:
- Timing / phase:
- Failure modes:
- Edge cases:

## Interaction matrix

| Existing mechanic | Interaction | Risk |
|---|---|---|
| mining |  |  |
| transport |  |  |
| crafting |  |  |
|  |  |  |

## Observation impact

Does this add or change a view? Does it change the meaning of an existing field?
What is the version impact?

## Action impact

Does this add an action or change legality? Does it change the action mask?

## Data impact

- New labels or rewards:
- New ground truth:
- New failure cases:
- Dataset version impact:

## Determinism

How is the mechanic ordered? What conflicts can arise? How are they resolved?
What is the state hash impact?

## Tests

- Unit:
- Property:
- Golden:
- Integration:
- Perf:

## Performance

Expected cost per tick. Does it threaten the performance policy (10k reference
target, 1k supported floor, 20% same-machine regression gate)?

## Alternatives

What simpler mechanic could answer the same question?

## Open questions

- ...

## Decision

Record the outcome and link the ADR if accepted.
