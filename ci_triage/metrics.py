"""Evaluation component (design/02-measurement.md).

Scores predictions against true labels. Knows nothing about how the predictions
were produced -- it works the same on a trained model, a constant function, or
a hand-written heuristic.
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


def accuracy(y_true, y_pred_label):
    return accuracy_score(y_true, y_pred_label)


def roc_auc(y_true, y_prob):
    if len(set(y_true)) < 2:
        return None  # undefined: needs both classes present
    return roc_auc_score(y_true, y_prob)


def precision_recall_at_threshold(y_true, y_prob, threshold):
    y_pred_label = [1 if p >= threshold else 0 for p in y_prob]
    precision = None if sum(y_pred_label) == 0 else precision_score(y_true, y_pred_label)
    recall = None if sum(y_true) == 0 else recall_score(y_true, y_pred_label)
    return {"precision": precision, "recall": recall}


def brier(y_true, y_prob):
    return brier_score_loss(y_true, y_prob)


def expected_calibration_error(y_true, y_prob, n_bins=10, binning="equal_width"):
    """ECE with a selectable binning scheme (design constraint: always report
    which scheme produced the number alongside it)."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)

    if binning == "equal_width":
        edges = np.linspace(0.0, 1.0, n_bins + 1)
    elif binning == "equal_frequency":
        edges = np.quantile(y_prob, np.linspace(0.0, 1.0, n_bins + 1))
        edges[0], edges[-1] = 0.0, 1.0
    else:
        raise ValueError(f"unknown binning scheme: {binning}")

    n = len(y_prob)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        in_bin = (y_prob >= lo) & (y_prob <= hi) if lo == edges[0] else (y_prob > lo) & (y_prob <= hi)
        if not in_bin.any():
            continue
        bin_confidence = y_prob[in_bin].mean()
        bin_accuracy = y_true[in_bin].mean()
        ece += (in_bin.sum() / n) * abs(bin_accuracy - bin_confidence)
    return ece


def cost_weighted_risk(y_true_cause, y_pred_output, cost_table):
    """cost_table: dict[(true_cause, output)] -> cost, from decisions/01.
    Returns mean cost per case; a correct call must be in the table as 0."""
    total = sum(cost_table[(t, p)] for t, p in zip(y_true_cause, y_pred_output))
    return total / len(y_true_cause)


def coverage_risk(y_true, y_prob, thresholds=None):
    """For each confidence threshold, the fraction of cases the system answers
    (coverage) and the error rate among those it answers (risk). Confidence is
    distance from a coin flip: |p - 0.5| * 2, so 0 = certain abstain, 1 = certain
    answer either way."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)
    confidence = np.abs(y_prob - 0.5) * 2
    if thresholds is None:
        thresholds = np.linspace(0.0, 0.9, 10)

    curve = []
    for t in thresholds:
        answered = confidence >= t
        coverage = answered.mean()
        if answered.sum() == 0:
            curve.append({"threshold": t, "coverage": coverage, "risk": None})
            continue
        pred_label = (y_prob[answered] >= 0.5).astype(float)
        risk = np.mean(pred_label != y_true[answered])
        curve.append({"threshold": t, "coverage": coverage, "risk": risk})
    return curve


def evaluate(y_true, y_prob, threshold=0.5, cost=None):
    """The whole ladder, in one report -- see design/02-measurement.md Emits.
    `cost`, if given, is {"y_true_cause", "y_pred_output", "cost_table"}; it is
    separate from y_true/y_prob because it can carry a different label space
    (the 3-way cause, not the binary flaky/not-flaky probability)."""
    pr = precision_recall_at_threshold(y_true, y_prob, threshold)
    report = {
        "accuracy": accuracy(y_true, [1 if p >= threshold else 0 for p in y_prob]),
        "roc_auc": roc_auc(y_true, y_prob),
        "precision": pr["precision"],
        "recall": pr["recall"],
        "brier": brier(y_true, y_prob),
        "ece": {
            "equal_width": expected_calibration_error(y_true, y_prob, binning="equal_width"),
            "equal_frequency": expected_calibration_error(y_true, y_prob, binning="equal_frequency"),
        },
        "coverage_risk": coverage_risk(y_true, y_prob),
    }
    if cost is not None:
        report["cost_weighted_risk"] = cost_weighted_risk(
            cost["y_true_cause"], cost["y_pred_output"], cost["cost_table"]
        )
    return report
