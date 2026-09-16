## Review
1. slice fit   — `metrics.py` originally exposed seven separate functions with no combined
   report, but the slice's `Emits` promises the whole ladder together; added `evaluate()`
   to bundle them.
2. correctness — `precision_recall_at_threshold` silently returned `0.0` for precision when
   there were zero predicted positives (via sklearn's `zero_division=0`), the same failure
   the `Refuses` section was written to prevent on the recall side; fixed to return `None`.
3. ML validity — nothing this pass; the binary-vs-3-way label space question was raised and
   left open rather than patched (recorded as a known-unknown, not fixed silently).
4. necessity   — the seven single-purpose functions looked like one-line sklearn wrappers in
   isolation, but adding `evaluate()` gives them a real purpose: it composes them into the
   one report the slice promised, so they stayed.

## Proposed
Use equal-width bins for expected calibration error, since it is the standard default and
most examples online use it.

## Rejected / narrowed to
Rejected. `ci_triage/metrics.py` computes and reports both equal-width and equal-frequency
ECE, always labeled by scheme, never just one.

## Because
At this project's ~3% positive rate, equal-width bins dump almost every prediction into the
0-10% bucket. That one bin's average becomes nearly the entire ECE score, so it hides
whatever miscalibration is actually inside that crowded range. Equal-frequency bins split
that same range into equal-sized groups and can actually tell a well-calibrated cluster
apart from a badly-calibrated one. Measured on this project's data: equal-width ECE was
0.0168, equal-frequency was 0.0318 — the standard default was the flattering number, not the
honest one.

## Ponytail pass
`accuracy`, `roc_auc`, `brier` stayed as thin wrappers around sklearn — writing them by hand
would be reimplementing what sklearn already does correctly. Only `expected_calibration_error`,
`cost_weighted_risk`, and `coverage_risk` are hand-written, because sklearn has no equivalent
for any of them. `metrics.py` is under 100 lines with `evaluate()` included.
