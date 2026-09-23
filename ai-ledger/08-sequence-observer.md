## Review
1. slice fit   — `project_test_sequences`/`build_examples` read only TRUSTED-run outcomes
   from phase 05's own parsing (`ci_triage/infra.py`), reusing that machinery rather than
   building a second, parallel per-run parser.
2. correctness — an early implementation called `_iter_run_logs` (phase 05's per-run
   generator, which reopens the archive per member) twice per project and stalled
   indefinitely on the 497MB square-okhttp archive, reproducing the exact hang measured in
   phase 05. Fixed by reading each archive once into memory (`read_all_run_logs`) and
   reusing that in-memory list for every subsequent pass.
3. ML validity — raw and calibrated AUC are reported and, correctly, come out identical on
   both scored folds -- Platt scaling is a monotonic transform of a fixed model's raw score
   and cannot change AUC. Reporting both is what makes this fact checkable instead of assumed.
4. necessity   — the control (`control_score`, a raw failure count) is computed alongside
   every example at data-build time, not as a separate pass over the same data.

## Proposed
Report only the mean AUC margin across the two scored folds (mean of +0.483 and -0.044 =
+0.22) as "the sequence model beats the control by 0.22 on average," and keep the model on
that basis.

## Rejected / narrowed to
Rejected by the builder. A single averaged margin hides that the two folds disagree about
the *direction* of the result, not just its size -- one fold shows a real, bootstrap-
confirmed win for the model, the other shows the model losing to the control on average
(though not distinguishably from noise on only 46 examples). The pre-registered rule
(`experiments/08-heuristic-control.md`) was written specifically so a result like this could
not be quietly averaged into a "yes."

## Because
Averaging the two per-fold margins produces a positive number regardless of whether the
underlying folds actually agree, and a positive average is exactly the kind of result that
gets used to justify keeping a model that was supposed to prove itself against a free
alternative. The whole point of writing the decision rule down first was to prevent that.

## Ponytail pass
`SequenceGRU` is a single `nn.GRU` layer plus a linear head, batch size 1 in a plain Python
loop -- no batching/padding machinery, no custom trainer class, no config beyond the two
constructor arguments actually varied (`hidden_size`, `seed`). Calibration reuses
`sklearn.linear_model.LogisticRegression` directly rather than reimplementing Platt scaling.
