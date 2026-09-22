import pandas as pd
import pytest

from ci_triage.splits import (
    fold_indices,
    generate_splits,
    load_splits,
)


def _toy_df():
    # 4 projects, uneven row counts, so a naive split could easily place a
    # project's rows on both sides if it weren't grouped
    rows = []
    for project, n, label_pattern in [
        ("proj-a", 5, [0, 0, 1, 0, 1]),
        ("proj-b", 3, [0, 1, 0]),
        ("proj-c", 6, [0, 0, 0, 1, 0, 1]),
        ("proj-d", 4, [1, 0, 0, 0]),
    ]:
        for i in range(n):
            rows.append({"project": project, "row": i, "label": label_pattern[i]})
    return pd.DataFrame(rows)


@pytest.fixture(autouse=True)
def _isolated_split_path(tmp_path, monkeypatch):
    # generate_splits/load_splits write to a real path on the module -- point
    # it at a scratch file so tests don't clobber the real artifacts/splits.json
    monkeypatch.setattr("ci_triage.splits.SPLIT_PATH", tmp_path / "splits.json")
    yield


def test_no_project_appears_in_more_than_one_grouped_fold():
    df = _toy_df()
    payload = generate_splits(df, n_folds=3)
    project_of_row = df["project"].tolist()

    project_to_folds = {}
    for row_idx, fold_id in enumerate(payload["grouped_fold"]):
        project = project_of_row[row_idx]
        project_to_folds.setdefault(project, set()).add(fold_id)

    for project, folds in project_to_folds.items():
        assert len(folds) == 1, f"{project} appears in folds {folds}, not just one"


def test_load_refuses_when_signature_does_not_match():
    df = _toy_df()
    generate_splits(df, n_folds=3)

    changed_df = df.copy()
    changed_df.loc[0, "label"] = 1 - changed_df.loc[0, "label"]  # flip one label
    with pytest.raises(ValueError, match="signature"):
        load_splits(changed_df)


def test_load_refuses_when_no_split_saved_yet():
    df = _toy_df()
    with pytest.raises(FileNotFoundError):
        load_splits(df)


def test_load_returns_the_same_assignment_that_was_generated():
    df = _toy_df()
    generated = generate_splits(df, n_folds=3)
    loaded = load_splits(df)
    assert loaded == generated


def test_fold_indices_partition_all_rows_with_no_overlap():
    df = _toy_df()
    payload = generate_splits(df, n_folds=3)
    seen = set()
    for fold_id in range(3):
        idx = fold_indices(payload, "grouped_fold", fold_id)
        assert seen.isdisjoint(idx)
        seen.update(idx)
    assert seen == set(range(len(df)))
