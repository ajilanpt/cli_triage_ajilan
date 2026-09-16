# Claim — rerun bias in the label

The negative class ("not flaky") in this dataset is contaminated with under-tested cases,
and the contamination direction is one-sided: it can only ever hide flaky tests inside the
"not flaky" label, never the reverse.

## Why
A "flaky" label comes from direct evidence — the test flipped, which is undeniable. A "not
flaky" label comes from absence of evidence — it did not flip in however many reruns were
budgeted, which at any realistic rerun count (see `decisions/03-label-procedure.md`, priced
at $500,000 for 100 reruns/test on a 500-test suite) can miss a genuinely intermittent test.

So the "not flaky" class is really two mixed-together populations: tests that are truly
stable, and tests that are flaky but were not caught. There is no equivalent failure mode on
the "flaky" side — a flip cannot be a false positive of the labeling procedure itself.

## What it would take to measure
Rerunning a sample of "not flaky" tests far beyond the original budget (e.g. 100x instead of
whatever N was used) and checking how many flip. The gap between the original miss rate and
this deeper rerun would estimate how contaminated the negative class actually is. Not
attempted here — this is a claim to carry forward, not a measured number.

## What it forces downstream
A model that appears to make "false positive" errors on the not-flaky class may, in some
fraction of cases, actually be right and the label wrong. Evaluation cannot treat every
negative as equally trustworthy ground truth (see phase 05's trust gate).
