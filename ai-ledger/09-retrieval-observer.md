## Review
1. slice fit   — `build_project_documents` reads only TRUSTED-or-MASS_FAILURE runs and
   labels via phase 05's own deterministic-test set, matching `design/09-retrieval-observer.md`.
2. correctness — the per-method failure header uses a fully-qualified class name
   (`com.squareup.okhttp...HttpOverSpdy3Test`), while phase 05's deterministic-test set (from
   the Results-block summary) uses the short class name (`HttpOverSpdy3Test`). Without
   normalizing, `test_name in deterministic_tests` silently never matched for square-okhttp,
   and every deterministic test's failures were mislabeled "flaky" (825,221 flaky / 165
   not-flaky, instead of the correct 165,278 / 660,108). Caught by checking one known
   deterministic test's label by hand against phase 05's own recorded list.
3. ML validity — the two "completed" cross-project folds (kevinsawicki, tootallnate held
   out) report precision@k exactly equal to the majority baseline (both 1.0), because those
   two projects contribute zero not-flaky documents -- the evaluation population has no
   class contrast to discriminate. Flagged as uninformative in `artifacts/results/retrieval.json`
   rather than reported as a win.
4. necessity   — `max_docs_per_test` caps embedding cost by capping near-duplicate
   occurrences of the same test's failure, not by reducing evaluation scope; the within-
   project evaluation still scored all 813 capped documents for square-okhttp.

## Proposed
Report the cross-project result as "1.0 precision on 2 of 3 held-out projects" -- technically
true, and the strongest-looking number in the phase.

## Rejected / narrowed to
Rejected by the builder. Recorded instead as "cross-project evaluation is not performable
with this data" (`artifacts/results/retrieval.json`, `not_performable_with_this_data: true`),
with the reason named: those two folds' query population is 100% one class, so matching the
majority baseline exactly is not evidence retrieval works across projects.

## Because
A number that exactly equals the majority baseline is not a result -- it is what any
uninformed guesser would also score. Reporting it as "1.0 precision" without that context
would be the same kind of self-deception the earlier phases (05's silent zero, 08's averaged
fold disagreement) were built to catch.

## Ponytail pass
`ci_triage/retrieval.py` is `sklearn.neighbors.NearestNeighbors` plus
`sentence_transformers.SentenceTransformer`, called directly -- no index class, per TASK.md's
explicit instruction ("If you are writing an index class, stop"). The only original logic is
building/labeling documents, the self-exclusion check, and the majority-vote/baseline
functions.
