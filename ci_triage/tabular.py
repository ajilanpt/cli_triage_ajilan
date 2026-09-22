"""Observer 1 -- tabular (design/07-tabular-and-the-pivot.md).

A gradient-boosted tree over the numeric tabular features, fit and scored
only on phase 06's saved grouped-by-project split. Always emits a
probability -- this slice never abstains (design/07, Refuses).
"""

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold

from ci_triage.metrics import evaluate
from ci_triage.splits import fold_indices, load_splits

MIN_POSITIVES_FOR_PER_PROJECT = 5

NON_FEATURE_COLUMNS = ("project", "testClassName", "testMethodName", "label", "rerun_count")


def feature_matrix(df):
    feature_cols = [c for c in df.columns if c not in NON_FEATURE_COLUMNS]
    X = df[feature_cols].select_dtypes(include=[np.number]).fillna(0).to_numpy()
    y = df["label"].to_numpy()
    return X, y


def _assert_no_project_leak(df, train_idx, test_idx):
    """design/07, Constraint: a project in the test fold must never also
    appear in that fold's training rows. Guards against silently reproducing
    phase 06's random-split leak inside a model that is supposed to be
    scored on the grouped split."""
    train_projects = set(df["project"].iloc[train_idx])
    test_projects = set(df["project"].iloc[test_idx])
    overlap = train_projects & test_projects
    if overlap:
        raise ValueError(f"project leak between train and test fold: {sorted(overlap)}")


def fit_and_score_fold(df, X, y, train_idx, test_idx, calibrate):
    _assert_no_project_leak(df, train_idx, test_idx)

    base = GradientBoostingClassifier(random_state=42)
    if calibrate:
        model = CalibratedClassifierCV(base, method="sigmoid", cv=3)
    else:
        model = base
    model.fit(X[train_idx], y[train_idx])
    prob = model.predict_proba(X[test_idx])[:, 1]
    return evaluate(y[test_idx], prob)


def _mean_std(values):
    values = [v for v in values if v is not None]
    return {"mean": float(np.mean(values)), "std": float(np.std(values))}


def run_tabular_observer(df, n_folds=5):
    X, y = feature_matrix(df)
    payload = load_splits(df)

    before, after = [], []
    for fold_id in range(n_folds):
        test_idx = fold_indices(payload, "grouped_fold", fold_id)
        train_idx = [i for i in range(len(df)) if i not in set(test_idx)]
        before.append(fit_and_score_fold(df, X, y, train_idx, test_idx, calibrate=False))
        after.append(fit_and_score_fold(df, X, y, train_idx, test_idx, calibrate=True))

    def summarize(rows):
        # equal-frequency bins, not equal-width: predicted probabilities cluster
        # in a narrow low range at this ~3% positive rate, which leaves most
        # equal-width bins empty and the ECE estimate noisy
        return {
            "auc": _mean_std([r["roc_auc"] for r in rows]),
            "ece_equal_frequency": _mean_std([r["ece"]["equal_frequency"] for r in rows]),
            "brier": _mean_std([r["brier"] for r in rows]),
        }

    return {
        "n_folds": n_folds,
        "before_calibration": summarize(before),
        "after_calibration": summarize(after),
    }


def run_per_project_pivot(df, min_positives=MIN_POSITIVES_FOR_PER_PROJECT, n_splits=3):
    """decisions/07-the-pivot.md: a separate model per project, evaluated with
    ordinary k-fold *within* that project's own rows -- project identity no
    longer leaks between train/test here, because the deployment question
    being answered is "does this project's own model work on more of this
    project's own data," not "does one model generalize to an unseen project."
    Projects without enough positives to stratify a fold are skipped and
    named, not silently dropped."""
    per_project = {}
    skipped = {}

    for project, group in df.groupby("project"):
        n_pos = int(group["label"].sum())
        if n_pos < min_positives:
            skipped[project] = {"rows": len(group), "positives": n_pos}
            continue

        X, y = feature_matrix(group)
        splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        fold_aucs = []
        for train_idx, test_idx in splitter.split(X, y):
            model = GradientBoostingClassifier(random_state=42)
            model.fit(X[train_idx], y[train_idx])
            prob = model.predict_proba(X[test_idx])[:, 1]
            result = evaluate(y[test_idx], prob)
            if result["roc_auc"] is not None:
                fold_aucs.append(result["roc_auc"])

        per_project[project] = {
            "rows": len(group),
            "positives": n_pos,
            "auc": _mean_std(fold_aucs) if fold_aucs else None,
        }

    all_aucs = [p["auc"]["mean"] for p in per_project.values() if p["auc"] is not None]
    return {
        "n_splits": n_splits,
        "min_positives": min_positives,
        "projects_scored": len(per_project),
        "projects_skipped": skipped,
        "overall_auc": _mean_std(all_aucs) if all_aucs else None,
        "per_project": per_project,
    }
