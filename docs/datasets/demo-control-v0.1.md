# Dataset card — demo-control-v0.1

- **Status:** M4 demonstration dataset
- **License:** CC-BY-4.0 (synthetic data); code Apache-2.0
- **Source:** scripted control policy
- **Demos:** 10
- **Transitions:** 300 (30 decisions per demo)
- **Success rate:** 1.00
- **Mean final score:** 140.0
- **World version:** `factory-0.1.0`
- **Task:** `factory.expand.control.v1`
- **Generation command:** `.venv/bin/python -m fabline demo --episodes 10 --out datasets/demo-control-v0.1`

## Purpose

A reproducible demonstration dataset for the line-building control task. It is
used to validate the demo writer, replay validation, and the behavior-cloning
pipeline. It is **not** a human-data claim.

Human demos use the same format and are collected with:

```bash
.venv/bin/python -m fabline play --out datasets/human-control-v0.1
```

## Contents

Each demo records:

- the 49-feature control observation before each action;
- the macro action (`0`–`5`);
- the reward for the decision interval;
- a state hash after each step;
- final score and success.

## Action distribution

The scripted policy builds the known optimal sequence:
`miner, belt, furnace, belt, assembler, belt`, then noops.

## Caveats

- Scripted demos solve the task; behavior cloning reaches 1.00 success in the
  M4 sanity check because the demos are clean and few.
- Human demos will be noisier and may require more data.
- The control task is a fixed six-tile puzzle, not general factory building.
- The dataset is small; report demo count and evaluation seeds with any claim.

## Behavior cloning

```bash
.venv/bin/python -m fabline human-bc \
  --dataset datasets/demo-control-v0.1 --out results/human-bc
```

M4 reference result: decision-tree clone, 10 demos, 300 transitions, success
rate 1.00 on 5 evaluation episodes.
