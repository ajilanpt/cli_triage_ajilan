import numpy as np

from ci_triage import metrics


def test_constant_predictor_high_accuracy_zero_recall():
    # typed by hand, ~3% positive rate
    y_true = [0] * 97 + [1] * 3
    y_pred_label = [0] * 100  # constant "not flaky"
    y_prob = [0.0] * 100

    acc = metrics.accuracy(y_true, y_pred_label)
    result = metrics.precision_recall_at_threshold(y_true, y_prob, threshold=0.5)

    assert acc >= 0.9
    assert result["recall"] == 0.0


def test_roc_auc_undefined_with_no_positives():
    y_true = [0, 0, 0, 0]
    y_prob = [0.1, 0.2, 0.3, 0.4]
    assert metrics.roc_auc(y_true, y_prob) is None


def test_recall_undefined_with_no_positives():
    y_true = [0, 0, 0, 0]
    result = metrics.precision_recall_at_threshold(y_true, [0.9, 0.1, 0.2, 0.8], threshold=0.5)
    assert result["recall"] is None


def test_precision_undefined_with_no_predicted_positives():
    y_true = [0, 1, 0, 1]
    y_prob = [0.1, 0.2, 0.3, 0.4]  # nothing crosses the threshold
    result = metrics.precision_recall_at_threshold(y_true, y_prob, threshold=0.5)
    assert result["precision"] is None


def test_evaluate_returns_whole_ladder_with_ece_labeled_by_binning():
    y_true = [0] * 97 + [1] * 3
    y_prob = [0.05] * 97 + [0.6] * 3

    report = metrics.evaluate(y_true, y_prob, threshold=0.5)

    for key in ("accuracy", "roc_auc", "precision", "recall", "brier", "ece", "coverage_risk"):
        assert key in report
    assert "equal_width" in report["ece"]
    assert "equal_frequency" in report["ece"]


def test_ece_binning_schemes_disagree_at_low_positive_rate():
    rng = np.random.default_rng(0)
    n = 1000
    y_true = (rng.random(n) < 0.03).astype(int)
    # a model that is always fairly confident it's "not flaky"
    y_prob = np.clip(rng.normal(0.05, 0.02, n), 0, 1)

    ece_width = metrics.expected_calibration_error(y_true, y_prob, binning="equal_width")
    ece_freq = metrics.expected_calibration_error(y_true, y_prob, binning="equal_frequency")

    assert ece_width != ece_freq


def test_cost_weighted_risk_matches_hand_computed_total():
    cost_table = {
        ("real_defect", "flaky"): 5000,
        ("real_defect", "real_defect"): 0,
        ("flaky", "real_defect"): 500,
        ("flaky", "flaky"): 0,
    }
    y_true_cause = ["real_defect", "flaky", "flaky"]
    y_pred_output = ["flaky", "real_defect", "flaky"]

    risk = metrics.cost_weighted_risk(y_true_cause, y_pred_output, cost_table)

    assert risk == (5000 + 500 + 0) / 3
