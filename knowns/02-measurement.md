# Phase 02

| Was | Now | Statement | Evidence |
|---|---|---|---|
| unknown | known | accuracy is close to meaningless on this problem — a constant "not flaky" predictor scores 0.97 accuracy while catching 0% of flaky cases | tests/test_metrics.py::test_constant_predictor_high_accuracy_zero_recall |
| unknown | known | the ECE binning scheme changes the answer at this project's positive rate — equal-width bins scored 0.0168, equal-frequency scored 0.0318, on the same array | decisions/02-metric-ladder.md |
| unknown | known | equal-width ECE is the flattering number here, not the honest one, because it dumps nearly all predictions into one bucket at a ~3% positive rate | decisions/02-metric-ladder.md |
| unknown | known-unknown | `metrics.py` assumes a single binary probability (flaky vs not); how that reconciles with the 3-way real-defect/flaky/infra output space from phase 01 is not yet resolved | — |
