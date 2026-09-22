# Slice 07 — observer 1 (tabular)

## Responsibility
Produce a probability that a given test failure is flaky, from the 23 numeric tabular
features alone, evaluated only on phase 06's saved grouped-by-project split.

## Reads
The phase-04 feature matrix's numeric columns (leak/label-derived/history columns already
excluded by `ci_triage/data.py`), and phase 06's saved fold assignment (`artifacts/splits.json`)
via `ci_triage.splits.load_splits` — never a freshly drawn split.

## Emits
Per row: a probability P(flaky) in [0, 1], calibrated. Per fold: AUC, ECE, Brier, and
cost-weighted risk (`ci_triage/metrics.py`), reported both before and after calibration.

## Refuses
Never. This observer always emits a probability, even on a row from a project it has never
seen and is unreliable on — it does not decide ABSTAIN itself. That decision belongs to the
fusion/arbiter layer (phase 11), which sees this observer's output alongside others and is
the only place `design/01-decision-and-cost.md`'s system-level ABSTAIN is emitted. A weak or
overconfident probability here is a quality problem for calibration to address, not a
refusal for this slice to make.

## Constraint
Must be fit and scored using only phase 06's saved grouped split — a project in a fold's
test set must never also appear in that fold's training rows. This is the same invariant
`tests/test_splits.py` checks at the split level; this phase's test checks it holds at the
point the model is actually fit, since a bug here (e.g. accidentally training on the full
dataframe instead of the fold's train indices) would silently reproduce phase 06's random-
split leak inside what looks like a grouped-split number.

## Connects to
Upstream: phase 04 (`ci_triage/data.py`, the feature matrix), phase 06 (`ci_triage/splits.py`,
the saved grouped split).
Downstream: phase 10's integration contract and phase 11's fusion/arbiter consume this
observer's calibrated probability alongside the sequence (08) and retrieval (09) observers.
