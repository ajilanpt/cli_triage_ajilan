"""Experiment harness (design/06-splits-and-baseline.md).

Splits are generated once and saved; every experiment loads the saved
assignment instead of regenerating it, so a score can only change because a
model or feature changed, never because the split quietly changed too.
"""

import hashlib
import json
from pathlib import Path

from sklearn.model_selection import GroupKFold, KFold

SPLIT_PATH = Path("artifacts/splits.json")
N_FOLDS = 5
RANDOM_STATE = 42


def _signature(df):
    """Short hash of what the split was generated against, so a stale saved
    split (generated from a dataframe that has since changed) is detected
    instead of silently reused (design/06, Refuses)."""
    key = f"{len(df)}|{sorted(df['project'].unique())}|{int(df['label'].sum())}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _folds_to_list(n_rows, splits):
    fold_of_row = [None] * n_rows
    for fold_id, (_, test_idx) in enumerate(splits):
        for i in test_idx:
            fold_of_row[i] = fold_id
    return fold_of_row


def generate_splits(df, n_folds=N_FOLDS, random_state=RANDOM_STATE):
    """Computes and saves grouped-by-project and random row-wise fold
    assignments for df. Overwrites any existing saved split -- an explicit,
    deliberate call the builder makes, not a side effect of running an
    experiment."""
    grouped = list(GroupKFold(n_splits=n_folds).split(df, groups=df["project"]))
    random_ = list(KFold(n_splits=n_folds, shuffle=True, random_state=random_state).split(df))

    payload = {
        "signature": _signature(df),
        "n_folds": n_folds,
        "random_state": random_state,
        "grouped_fold": _folds_to_list(len(df), grouped),
        "random_fold": _folds_to_list(len(df), random_),
    }
    SPLIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPLIT_PATH.write_text(json.dumps(payload))
    return payload


def load_splits(df):
    """Loads the saved split. Refuses (raises) if it doesn't exist, or if its
    signature no longer matches df -- call generate_splits(df) explicitly to
    (re)create it (design/06, Refuses)."""
    if not SPLIT_PATH.exists():
        raise FileNotFoundError(
            f"{SPLIT_PATH} does not exist -- call generate_splits(df) explicitly first"
        )
    payload = json.loads(SPLIT_PATH.read_text())
    if payload["signature"] != _signature(df):
        raise ValueError(
            f"{SPLIT_PATH}'s signature does not match the current dataframe -- "
            "the data changed since the split was generated; call generate_splits(df) "
            "again explicitly to regenerate it"
        )
    return payload


def fold_indices(payload, key, fold_id):
    """Row positions for one fold under payload[key] ('grouped_fold' or
    'random_fold')."""
    return [i for i, f in enumerate(payload[key]) if f == fold_id]
