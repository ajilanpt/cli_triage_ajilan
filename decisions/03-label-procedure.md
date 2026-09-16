# Decision — label procedure

## The mechanism
A test is labeled by rerunning it some number of times (N) on identical code:

- If it both passes and fails at least once across those N reruns → **flaky**.
- If it never flips across those N reruns → **not flaky**.

N (the rerun count) is not yet known — it depends on the actual dataset, inspected in phase
04. It is an explicit unknown to check for when the data is loaded, not an assumption.

## The asymmetry
- A test that flips **proves** it is flaky — that outcome cannot be explained away.
- A test that never flips only proves it did not flip in that specific number of reruns. If
  it is actually intermittent and flips 1 in 20 runs, a 3-rerun trial has a real chance of
  missing it. "Not flaky" here means "no flip caught yet," not "confirmed stable."

## Pricing the truth
To trust a "not flaky" label with reasonable confidence: **100 reruns** per test.

Across a project with **500 tests**, at **2 minutes** per run and **$5/CI-minute**:

```
100 reruns x 500 tests x 2 min x $5/min = $500,000
```

Nobody pays this. That is why the negative class stays permanently contaminated with
under-tested cases rather than confirmed-stable ones.

## What it forces
The negative class cannot be treated as uniformly trustworthy ground truth during
evaluation. A model flagging a well-tested (high-rerun-count) negative as flaky is a real
mistake; a model flagging a barely-tested (low-rerun-count) negative might be catching
something the label procedure never had the budget to catch. Evaluation must be able to
weight or filter by the label's rerun count, not treat every negative the same. This
constraint carries into phase 05's trust gate.
