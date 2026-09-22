import pandas as pd
import pytest

from ci_triage.tabular import (
    _assert_no_project_leak,
    fit_and_score_fold,
    feature_matrix,
    run_per_project_pivot,
)


def _toy_df():
    rows = []
    for project, n, positives in [("proj-a", 20, 8), ("proj-b", 20, 10), ("proj-c", 20, 6)]:
        for i in range(n):
            rows.append(
                {
                    "project": project,
                    "testClassName": "T",
                    "testMethodName": f"m{i}",
                    "label": 1 if i < positives else 0,
                    "rerun_count": 5,
                    "feat1": i,
                    "feat2": i * 2 % 7,
                }
            )
    return pd.DataFrame(rows)


def test_fit_raises_when_a_project_appears_on_both_sides_of_the_fold():
    # the invariant this phase must never silently violate: a held-out
    # project's rows must never also be in the training rows
    df = _toy_df()
    X, y = feature_matrix(df)
    proj_a_idx = df.index[df["project"] == "proj-a"].tolist()
    proj_b_idx = df.index[df["project"] == "proj-b"].tolist()

    # deliberately leaky: proj-a rows appear in both train and test
    train_idx = proj_a_idx + proj_b_idx
    test_idx = proj_a_idx[:3]

    with pytest.raises(ValueError, match="leak"):
        fit_and_score_fold(df, X, y, train_idx, test_idx, calibrate=False)


def test_assert_no_project_leak_passes_when_folds_are_clean():
    df = _toy_df()
    train_idx = df.index[df["project"] != "proj-a"].tolist()
    test_idx = df.index[df["project"] == "proj-a"].tolist()
    _assert_no_project_leak(df, train_idx, test_idx)  # must not raise


def test_pivot_skips_projects_below_the_positive_threshold_instead_of_dropping_silently():
    df = _toy_df()
    # proj-c has only 6 positives; raise the threshold above that on purpose
    result = run_per_project_pivot(df, min_positives=7, n_splits=2)
    assert "proj-c" in result["projects_skipped"]
    assert "proj-c" not in result["per_project"]
    assert result["projects_skipped"]["proj-c"]["positives"] == 6


def test_pivot_scores_every_project_that_meets_the_threshold():
    df = _toy_df()
    result = run_per_project_pivot(df, min_positives=5, n_splits=2)
    assert set(result["per_project"]) == {"proj-a", "proj-b", "proj-c"}
    for project_result in result["per_project"].values():
        assert project_result["auc"] is not None
