## Review
1. slice fit   — `run_tabular_observer` reads only phase 06's saved split (`load_splits`,
   never a fresh one) and always emits a probability (no abstain path), per
   `design/07-tabular-and-the-pivot.md`.
2. correctness — `_assert_no_project_leak` is checked inside `fit_and_score_fold` itself,
   not just at the split-generation step, so a bug in how a caller slices train/test indices
   is caught at the point the model is actually fit, not only when the split file is built.
3. ML validity — calibration is measured on the same folds/metrics before and after, and the
   AUC drop from calibration is reported and explained rather than only reporting the ECE
   improvement calibration was expected to produce.
4. necessity   — `feature_matrix` is one shared helper used by both the grouped observer and
   the per-project pivot; no duplicated feature-selection logic between them.

## Proposed
Ship the grouped cross-project model (0.587 AUC) as-is, since it is still meaningfully above
0.5 on average and a weak signal is better than no signal for the on-call engineer.

## Rejected / narrowed to
Rejected by the builder. Per `PROBLEM.md`'s cost table, a real defect misreported as flaky
costs $5000 -- a signal this close to chance (one grouped fold scored 0.121, worse than a
coin flip) is not a safe input to a 02:47 release decision just because its *average* is
above 0.5. The builder chose to change the question instead (per-project models) rather than
ship the weak zero-shot number or tune it further. See `decisions/07-the-pivot.md`.

## Because
"Average AUC is above 0.5" hides the fold that scored 0.121 -- reporting only the mean would
let a genuinely dangerous failure mode (confidently wrong on a specific kind of unseen
project) pass as a mediocre-but-acceptable overall number.

## Ponytail pass
`run_per_project_pivot` reuses `feature_matrix` and `sklearn`'s `StratifiedKFold` directly;
the only original logic is the per-project loop, the skip-and-name-it threshold, and the
summary aggregation. No new class, no configuration object beyond the two threshold
constants at the top of the module.
