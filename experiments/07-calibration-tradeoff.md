# Experiment — calibration tradeoff

## Prediction (written before calibrating anything; not edited afterward)

**ECE:** improves (gets lower / better) after calibration.

**AUC:** stays the same after calibration.

---

## Result

Gradient-boosted tree, grouped split, 5 folds, `CalibratedClassifierCV(method="sigmoid", cv=3)`
(`artifacts/results/tabular.json`):

| | AUC | ECE (equal-frequency) | Brier |
|---|---|---|---|
| Before calibration | 0.587 | 0.048 | 0.044 |
| After calibration | 0.519 | 0.044 | 0.036 |

**ECE prediction was right:** it improved (0.048 → 0.044), and Brier improved too (0.044 →
0.036).

**AUC prediction was wrong:** I predicted "stays the same." It dropped, from 0.587 toward
0.519 — nearly chance-level discrimination.

**Why AUC dropped, not just held steady:** `CalibratedClassifierCV(cv=3)` does not only
reshape an already-fitted model's output scores — it retrains the base classifier itself,
three separate times, each on only 2/3 of the fold's training rows, then combines the
rotating internal holdouts. The calibrated model's underlying ranking function therefore
learns from less independent data than the uncalibrated version (100% of the fold's training
rows). This is especially costly here because a grouped fold's training set is already small
and unevenly distributed across projects (e.g. `alluxio`: 187 rows total, 62% positive) —
splitting that further into internal thirds leaves very little signal for the base model to
rank on. The AUC drop is a side effect of calibration quietly shrinking the data an
already-fragile model gets to train on, not evidence that calibration itself damages
ranking in principle.

## What this means for the system
Calibration is not free here: it buys real improvement in probability quality (ECE, Brier)
at real cost to ranking ability (AUC), on top of an already weak grouped-split signal
(0.587, close to chance). A model this close to uninformative on unseen projects cannot
absorb further discrimination loss and still be useful — this result feeds directly into
`decisions/07-the-pivot.md`.
