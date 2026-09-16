from ci_triage.data import (
    EXCLUDED_FROM_FEATURES,
    ID_COLUMNS,
    load_dataset,
)


def test_no_leaking_or_history_column_reaches_the_feature_matrix():
    df, _ = load_dataset("data/raw")
    feature_columns = set(df.columns) - set(ID_COLUMNS) - {"label", "rerun_count"}

    for leaking in EXCLUDED_FROM_FEATURES:
        assert leaking not in feature_columns, f"{leaking} leaked into the feature matrix"


def test_join_matches_the_verified_shape():
    df, report = load_dataset("data/raw")

    # from data/README.md's verification targets: ~26.1k rows, ~3.16% positive
    assert 26000 < report["joined_rows"] < 26200
    assert 0.03 < df["label"].mean() < 0.033


def test_label_comes_from_isflaky_not_the_features_flaky_column():
    df, _ = load_dataset("data/raw")
    # the two label columns disagree (see decisions/04-dataset-choice.md);
    # IsFlaky has far more positives than test_features.csv's own `flaky` column
    assert df["label"].sum() > 800


def test_rerun_count_travels_with_the_label_but_is_not_a_feature():
    df, _ = load_dataset("data/raw")
    assert "rerun_count" in df.columns
    assert "rerun_count" not in (set(df.columns) - set(ID_COLUMNS) - {"label", "rerun_count"})
    assert (df["rerun_count"] > 0).all()
