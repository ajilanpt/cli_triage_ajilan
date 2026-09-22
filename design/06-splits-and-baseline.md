# Slice 06 — experiment harness

## Responsibility
Assign every row in the phase-04 dataframe to a fold, once, and make that assignment the
one thing every later experiment loads instead of regenerates — so a score can only change
because a model or feature changed, never because the split quietly changed underneath it.

## Reads
The phase-04 joined dataframe (`ci_triage/data.py`) and its `project` column only, to form
groups. No feature or label column influences the split — group identity is the only input,
per `decisions/06-split-choice.md`: production sees projects the model has never trained on,
so the split must hold projects out whole.

## Emits
A saved fold assignment (`artifacts/splits.json` or equivalent): for each row, which fold it
belongs to under the grouped split, keyed by a hash/signature of the input dataframe so a
stale assignment is detectable. Downstream, mean and standard deviation of the chosen metric
across folds, for both the grouped split and a random row-wise split, reported side by side
in `artifacts/results/baseline.json` alongside the majority-class baseline.

## Refuses
If the current phase-04 dataframe's signature does not match the one recorded when the split
was generated, the harness refuses to run and reports the mismatch — it never silently
regenerates a fresh split or reuses a stale one against changed data. Regenerating the split
is a deliberate, explicit action the builder takes, not something that happens as a side
effect of running an experiment.

## Constraint
No project ever appears in more than one fold of the grouped split. This is invisible in any
aggregate metric and fatal to the deployment claim if violated — it becomes the phase's
required invariant test (`tests/test_splits.py`).

## Connects to
Upstream: phase 04's `ci_triage/data.py` (the joined dataframe, project column).
Downstream: every phase from 07 on (tabular, sequence, retrieval observers, fusion) trains
and evaluates against this same saved split, not a freshly drawn one.
