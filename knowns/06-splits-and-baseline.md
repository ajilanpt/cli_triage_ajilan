# Phase 06

| Was | Now | Statement | Evidence |
|---|---|---|---|
| unknown | known | this system's deployment sees projects it has never trained on (training data is 25 unrelated open-source projects, not accumulating history from one) — the split must hold projects out whole, not shuffle rows randomly | decisions/06-split-choice.md |
| unknown | known | the same gradient-boosted model, same 15 features, scores 0.907 mean AUC on a random row-wise split versus 0.587 mean AUC (std 0.245, one fold at 0.121) on a project-held-out split | artifacts/results/baseline.json |
| unknown | known | the gap is project-identity leakage, not noise: per-project positive rate ranges from 0% (commons-exec, jimfs) to 62% (alluxio) against an overall 3.16%; the random split lets a model partly succeed on a project it saw in training without learning a real flakiness signal | experiments/06-split-comparison.md |
| unknown | known | the majority-class baseline is 96.8% accuracy at a 3.16% positive rate — the number from phase 02's cost table is no longer hypothetical | artifacts/results/baseline.json |
| unknown | known-unknown | the grouped split's instability (std 0.245, one fold worse than chance) means a single mean AUC across 5 folds may itself be an unstable summary for this dataset — whether more folds, a different grouping granularity, or simply more projects would stabilize it is untested |
| unknown | known-unknown | the prediction written before running (`experiments/06-split-comparison.md`) got the direction wrong despite correctly naming the actual mechanism (project leakage) as the falsification criterion — worth remembering that reasoning about the mechanism and reasoning about the sign of a result are separable skills, before trusting either alone on a later phase |
