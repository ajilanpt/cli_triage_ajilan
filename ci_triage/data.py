"""Ingestion layer (design/04-data-and-licence.md).

Loads the raw FlakeFlagger CSVs, joins them, and returns a feature matrix with
the leak guard applied inside this one function -- there is no other way to
get features out of this module.

Data: FlakeFlagger (Zenodo record 4450723), CC-BY-4.0.
"""

from pathlib import Path

import pandas as pd

# Columns excluded from the feature matrix, and why. This list is read only
# inside load_dataset() -- there is no code path that returns features
# without applying it (design/04-data-and-licence.md, Constraint).
LEAK_COLUMNS = ["flaky", "flaky_source", "IsFlaky"]  # computed from / a restatement of the label
LABEL_DERIVED_COLUMNS = [
    "NumFailingRuns",
    "NumPassingRuns",
    "FirstFailingRunID",
    "FirstPassingRunID",
    "UniqueFailingExceptionTypes",
]  # only meaningful because the labeling reruns already happened
UNAVAILABLE_HISTORY_COLUMNS = [
    "hIndexModificationsPerCoveredLine_window5",
    "hIndexModificationsPerCoveredLine_window10",
    "hIndexModificationsPerCoveredLine_window25",
    "hIndexModificationsPerCoveredLine_window50",
    "hIndexModificationsPerCoveredLine_window75",
    "hIndexModificationsPerCoveredLine_window100",
    "hIndexModificationsPerCoveredLine_window500",
    "hIndexModificationsPerCoveredLine_window10000",
]  # needs full git history mining this project does not have (design/04, Refuses)

EXCLUDED_FROM_FEATURES = LEAK_COLUMNS + LABEL_DERIVED_COLUMNS + UNAVAILABLE_HISTORY_COLUMNS

ID_COLUMNS = ["project", "testClassName", "testMethodName"]
# duplicate/index columns the join brings in that carry no feature signal
REDUNDANT_COLUMNS = ["Unnamed: 0", "test_name", "Project"]
NON_FEATURE_COLUMNS = (
    ID_COLUMNS + EXCLUDED_FROM_FEATURES + REDUNDANT_COLUMNS + ["key", "label", "rerun_count"]
)


def load_dataset(raw_dir="data/raw"):
    """Returns (df, report). df has one row per joined test: id columns,
    feature columns (leak/history/label-derived columns already excluded),
    `label` (from IsFlaky), and `rerun_count` (NumFailingRuns + NumPassingRuns)
    carried as provenance, per phase 03, not as a feature."""
    raw_dir = Path(raw_dir)
    feat = pd.read_csv(raw_dir / "test_features.csv")
    res = pd.read_csv(raw_dir / "test_results.csv")

    feat = feat.copy()
    feat["key"] = feat["testClassName"] + "#" + feat["testMethodName"]
    res = res.rename(columns={"Test": "key"})

    joined = feat.merge(res, on="key", how="inner")

    report = {
        "features_rows": len(feat),
        "results_rows": len(res),
        "joined_rows": len(joined),
        "features_only": len(set(feat["key"]) - set(res["key"])),
        "results_only": len(set(res["key"]) - set(feat["key"])),
    }

    joined["label"] = joined["IsFlaky"].astype(int)
    joined["rerun_count"] = joined["NumFailingRuns"] + joined["NumPassingRuns"]

    feature_columns = [c for c in joined.columns if c not in NON_FEATURE_COLUMNS]
    df = joined[ID_COLUMNS + ["label", "rerun_count"] + feature_columns]

    return df, report

if __name__ == "__main__":
    df, report = load_dataset()
    print(report)