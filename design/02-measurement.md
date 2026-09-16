# Slice 02 — evaluation component

## Responsibility
Compare predictions to true labels and report how good they are. It does not care whether
the predictions came from a trained model, a constant function, or a hand-written
heuristic — it is a method on the *evaluation*, not on the model, so anything can be scored
on identical terms.

## Reads
Predictions (probabilities), true labels, and a threshold when the metric needs one
(precision and recall require a threshold; ROC AUC, Brier, and ECE do not).

## Emits
One report containing the whole ladder together, not one metric at a time: accuracy, ROC
AUC, precision/recall at a threshold, Brier score, expected calibration error (with its
binning scheme named), cost-weighted risk (from the phase 01 cost table), and
coverage/risk-coverage.

## Refuses
When a metric is undefined for the given input — e.g. ROC AUC or recall with zero positive
examples in the batch — it explicitly reports that metric as undefined rather than guessing
a number or silently omitting it.

## Constraint
Must never report expected calibration error without stating which binning scheme (equal-
width or equal-frequency) produced it. At a low positive rate, equal-width bins can report a
falsely reassuring number, and a caller has no way to know which scheme they are looking at
unless it is labeled.

## Connects to
Upstream: the cost table in `decisions/01-output-space.md` / `PROBLEM.md` feeds
cost-weighted risk. Downstream: every model built later in this project (tabular, sequence,
retrieval observers) is scored through this same component, on identical terms.
