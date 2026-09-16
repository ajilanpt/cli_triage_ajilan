# Decision — metric ladder

## The constant predictor
A function that always says "not flaky," scored on a 100-row toy array with 3 positives:

```
constant predictor accuracy: 0.97
constant predictor recall  : 0.0
```

97% accuracy, catches nothing. Accuracy alone would call this a good system.

## The ladder

| Measurement | Question it answers |
|---|---|
| accuracy | almost nothing here — the constant predictor scores 0.97 on it |
| ROC AUC | does the model rank flaky builds above not-flaky ones |
| precision @ threshold | of what we flagged as flaky, how much really was |
| recall @ threshold | of what really was flaky, how much did we catch |
| Brier score | squared error on the probability itself, one number for calibration and ranking together |
| expected calibration error (ECE) | when it says 80%, is it right about 80% of the time — binning scheme must be named |
| cost-weighted risk | the actual objective from phase 01, in dollars, not an abstract score |
| coverage / risk–coverage | what happens to error rate as the system is allowed to abstain more |

## The binning trap

```
ECE equal_width    : 0.0168
ECE equal_frequency: 0.0318
```

Equal-width bins (0-10%, 10-20%, ...) are misleading here. At a ~3% positive rate, nearly
every prediction lands in the 0-10% bucket, so that one bin's average becomes almost the
entire ECE score and hides whatever miscalibration is inside it. Equal-frequency bins carve
that same crowded range into several equal-sized groups, so they can actually distinguish a
well-calibrated cluster of predictions from a badly-calibrated one within it. The lower
equal-width number (0.0168) is the flattering one, not the honest one.

## Decision
`ci_triage/metrics.py` always reports ECE for both binning schemes, labeled, rather than
picking one as the default — this is now enforced as a constraint in
`design/02-measurement.md`.
