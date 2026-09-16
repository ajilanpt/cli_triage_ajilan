## Review
No code this phase — nothing to run against the four passes.

## Proposed
Exclude every "not flaky" test whose rerun count is below the 100-rerun trust bar entirely,
rather than keeping it with a trust weight.

## Rejected / narrowed to
Rejected. Low-rerun-count "not flaky" tests stay in the dataset, flagged with a low trust
score, not deleted.

## Because
At the priced rerun bar ($500,000 for 100 reruns/test on a 500-test suite, in
`decisions/03-label-procedure.md`), almost no real project's data would meet the 100-rerun
threshold. Excluding everything below it would throw away most of the negative class, not
just the untrustworthy part of it. Keeping the low-trust cases with a flag lets evaluation
weight or filter by trust later, without discarding data the system will need.

## Ponytail pass
Not applicable — no code this phase.
