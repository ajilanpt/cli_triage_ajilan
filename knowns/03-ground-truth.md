# Phase 03

| Was | Now | Statement | Evidence |
|---|---|---|---|
| unknown | known | a rerun that flips proves a test is flaky; a rerun that never flips only proves it did not flip in that many reruns, not that the test is stable | decisions/03-label-procedure.md |
| unknown | known | the negative class ("not flaky") is one-sided contamination — it can hide untested-but-flaky cases, with no equivalent failure mode on the positive side | experiments/03-rerun-bias.md |
| unknown | known | trusting a "not flaky" label at 100 reruns, on a 500-test suite at 2 min/run and $5/CI-minute, costs $500,000 — nobody pays this, so the negative class stays permanently contaminated | decisions/03-label-procedure.md |
| unknown | known-unknown | the actual rerun count (N) used to produce the real dataset's labels is not yet known — it must be checked when the data is loaded in phase 04 | — |
| unknown | known-unknown | how much of the negative class is actually mislabeled (truly flaky but never caught) has not been measured, only argued for | experiments/03-rerun-bias.md |
