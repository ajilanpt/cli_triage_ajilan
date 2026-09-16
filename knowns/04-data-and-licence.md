# Phase 04

| Was | Now | Statement | Evidence |
|---|---|---|---|
| unknown | known | FlakeFlagger (CC-BY-4.0) is usable; IDoFT has no licence and is not, absent one being added | decisions/04-dataset-choice.md |
| unknown | known | the real join key is `testClassName#testMethodName`, not `project`+`test_name` — the two CSVs format project names differently and that join produces zero matches | ci_triage/data.py, artifacts/results/eda.json |
| unknown | known | the join produces 26,134 rows across 25 projects, 825 positives (3.16%), matching the reference target within a legitimate version delta | artifacts/results/eda.json |
| unknown | known | `IsFlaky` (test_results.csv) is the trustworthy label; `flaky` (test_features.csv) comes from external tools (IDFlakies/DeFlaker) with untracked rerun budgets and disagrees with IsFlaky on 904 tests | decisions/04-dataset-choice.md |
| unknown | known | `flaky_source` leaks the `flaky` column perfectly (100% correspondence); `IsFlaky` itself, the rerun counts, and three rerun-procedure artifact columns are excluded from the feature matrix for the same reason | ci_triage/data.py, tests/test_data.py |
| unknown | known-unknown | the 8 `hIndexModificationsPerCoveredLine_window*` columns are excluded because this project has no git-history-mining infrastructure; whether they would help if that infrastructure existed is untested | — |
