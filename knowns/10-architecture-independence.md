# Phase 10

| Was | Now | Statement | Evidence |
|---|---|---|---|
| unknown | known | observers 2 (sequence) and 3 (retrieval) are not independent evidence sources -- both derive from phase 05's TRUSTED-run gate over the same 3 raw archives, just in different representations (pass/fail sequence vs. exception text); only observer 1 (tabular, a separate dataset) is genuinely independent of them | decisions/10-independence.md |
| unknown | known | the evidence record (`ci_triage/contracts.py`) makes an unstated calibration flag impossible to construct (`TypeError`, no default) rather than silently defaulting one way | tests/test_contracts.py |
| unknown | known | "no evidence" (n_observations=0) and "evidence pointing in every direction" (high n_observations, probability near 0.5) are now distinguishable fields on the same record, rather than both collapsing into an ambiguous ~0.5 | ci_triage/contracts.py |
| unknown | known | the run-level release decision must not average case-level probabilities across a build's failing tests -- doing so can dilute the one real defect hiding among many flaky-looking failures below detectability | docs/architecture.md |
| unknown | known-unknown | how fusion (phase 11) should actually weight a correlated pair (observers 2+3) against the one independent observer (1) is not yet decided -- this phase established that they must be treated differently, not what that treatment should be |
| unknown | known-unknown | whether cost_usd/latency_ms as reported by each observer are being measured consistently (same units, same what-counts-as-cost) across tabular/sequence/retrieval has not been checked -- the contract requires the fields to exist, not that they're comparable across observers yet |
