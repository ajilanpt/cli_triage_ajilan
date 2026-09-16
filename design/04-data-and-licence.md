# Slice 04 — ingestion layer

## Responsibility
Load the raw FlakeFlagger CSVs, join them into one row per test, and produce a feature
matrix with every leaking or history-dependent column already removed — dropping those
columns is part of producing the matrix, not a separate step.

## Reads
The raw FlakeFlagger CSVs: `test_features.csv`, `test_results.csv`, `Project_Info.csv`.

## Emits
A feature matrix, one row per test, with the label and its rerun-count/trust provenance
(from phase 03) carried alongside it, and every column that fails the leak or
history-availability check already excluded.

## Refuses
When a test ID appears in one CSV but not the other, the row is dropped from the join
rather than kept with missing values — but the dropped-row count is reported, never
silently swallowed.

## Constraint
The leak guard lives inside the one function that returns the feature matrix. There is no
code path that returns features without it — it cannot be a step a caller forgets to call.

## Connects to
Upstream: phase 03's ground-truth source — the label and its rerun-count/trust flag travel
into this matrix rather than being re-derived. Downstream: phase 05's trust gate and phase
06's splits both consume this function's output directly.
