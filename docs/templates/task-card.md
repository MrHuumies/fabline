# Task card — <task id>

- **Version:** 0.1.0
- **Status:** draft | frozen | retired
- **Owner:** <name>
- **Date:** YYYY-MM-DD
- **World:** factory-0.1.0
- **Benchmark:** factory-v0.1 (if frozen)

## Phenomenon

What question does this task isolate? Why does it need this world?

## Contract

- **Observation adapter(s):** grid-0.1.0, vector-0.1.0
- **Action adapter:** grid-build-0.1.0 or none (offline)
- **Label / reward:** exact definition, units, horizon
- **Termination:** exact conditions
- **Decision interval:** ticks per action
- **Episode length:** ticks
- **Info / ground truth:** what is available for analysis

## Data source

- Generator or replay set:
- Seeds:
- Number of episodes:
- Split definitions:
- Leakage audit:

## Splits

| Split | Definition | Episodes | Purpose |
|---|---|---:|---|
| train |  |  |  |
| val |  |  |  |
| test |  |  |  |
| compositional |  |  |  |
| shift |  |  |  |

## Metrics

- Primary:
- Secondary:
- Cost metrics:
- Retention / transfer metrics (if applicable):

## Baselines

| Baseline | Budget | Expected range | Notes |
|---|---|---|---|
|  |  |  |  |

## Compute budget

- Per run:
- Seeds:
- Hardware:
- Time limit:

## Known pitfalls

- label leakage:
- confounds:
- saturation:
- ambiguous cases:
- missing views:
- near-duplicates across splits:

## Negative controls

What should a valid method *not* beat? What result would indicate the task is
broken?

## Results

Link pre-registration, raw results, and summary. Report negative results in the
first paragraph.

## Changelog

- YYYY-MM-DD — created.
