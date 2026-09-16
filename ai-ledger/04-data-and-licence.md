## Review
1. slice fit   — matches the ingestion slice: leak guard lives inside `load_dataset`, the
   only function that returns features, and dropped-row counts are reported in `report`
   rather than swallowed.
2. correctness — the first draft leaked `IsFlaky` itself into the feature matrix (forgot to
   exclude the label column the join brings in), caught by actually running `load_dataset`
   and inspecting the real output columns, not by inspection alone. Also missed
   `FirstFailingRunID`, `FirstPassingRunID`, `UniqueFailingExceptionTypes` — rerun-procedure
   artifacts in the same category as `NumFailingRuns`/`NumPassingRuns`. Both fixed.
3. ML validity — nothing further this pass; the join-key mismatch (project-name formats
   differ between the two CSVs) was caught before any modelling, not after.
4. necessity   — nothing to delete; every excluded-column list maps to a specific, named
   reason (leak, label-derived, unavailable history).

## Proposed
Keep the smaller `hIndexModificationsPerCoveredLine_window5`/`_window10` columns as
features, since the values are already computed and sitting in the CSV — no extra
infrastructure needed right now.

## Rejected / narrowed to
Rejected. All eight `hIndexModificationsPerCoveredLine_window*` columns are excluded, not
just the largest ones.

## Because
This project has no git-history-mining infrastructure at all, at any window size. The
values being present in this static CSV is an artifact of one offline computation the
original researchers did; it says nothing about whether this system can recompute the
feature for a brand-new red build tomorrow. A feature that only works on historical data
frozen at collection time is not a feature this system can actually use in deployment.

## Ponytail pass
`ci_triage/data.py` is a load + join + column-exclusion function; pandas does the CSV
reading and merge, nothing was hand-rolled that pandas already provides. Under 60 lines.
