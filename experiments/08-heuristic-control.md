# Experiment — heuristic control

## The circularity (found before writing any code)
`IsFlaky = 1` means, and only means: within the test's observed reruns, it both passed and
failed at least once (`experiments/03-rerun-bias.md`). Feeding a sequence model the test's
full observed rerun sequence and asking it to predict `IsFlaky` computed from that same
sequence is not forecasting anything — it is handing the model the label's own definition
and asking it to restate it. A model set up this way would score near 1.0 AUC and prove
nothing.

## The reformulation
**Prefix predicts suffix.** Each test's ordered, TRUSTED-only rerun sequence is split at a
prefix length *k*: the prefix (runs 1..k) is the input; the label is whether the **suffix**
(runs k+1..end) flips (both pass and fail occur within it) — mirroring how `IsFlaky` itself
is defined, applied to a later, non-overlapping window. No run ID appears in both halves of
the same example (`tests/test_sequences.py`'s required invariant).

Since all reruns are of one fixed commit per project (`Project_Info.csv`, one SHA per
project), this is not a "will the code still be broken next release" question — it is a
rerun-budget question: **given what the first k reruns showed, should I keep trusting this
test if I stop rerunning it after k, or does it look like it's still going to misbehave?**
That is actionable — it tells an engineer whether it's safe to stop paying for more reruns.

## The control
**Count of failures observed in the prefix.** No training, no parameters — just the raw
count, used directly as a ranking score against the suffix-flip label to get an AUC.

## Pre-registered decision (written before any model exists; not edited afterward)
**Keep the sequence model if:** its mean AUC across the leave-one-project-out folds beats
the control's mean AUC by **at least 0.05**.

**Throw it away if:** the margin is smaller than 0.05, or the two are within roughly a fold's
worth of noise of each other — per TASK.md, if they are close, this must be checked with an
actual distinguishability test (paired comparison across folds), not by eyeballing the two
means.

---

## Result

Leave-one-project-out, GRU vs. the count-of-past-failures control, same test examples per
fold (`artifacts/results/sequence.json`):

| Held out | Model raw AUC | Model calibrated AUC | Control AUC | Model − control (95% bootstrap CI) |
|---|---|---|---|---|
| tootallnate-java-websocket | 0.466 | 0.466 | 0.517 | -0.044 [-0.305, 0.177] |
| square-okhttp | 0.750 | 0.750 | 0.268 | **+0.483** [0.355, 0.600] |
| kevinsawicki-http-request | — | — | — | skipped: zero positive examples in test fold, AUC undefined |

**Raw and calibrated AUC are identical on both scored folds.** This is expected, not a bug:
Platt scaling (a logistic regression fit on the raw score) is a strictly monotonic
transform, and AUC depends only on rank order — a monotonic remap cannot change it. Contrast
with phase 07, where calibration *did* change AUC, because `CalibratedClassifierCV`'s
internal cross-validation retrained the base model on less data; nothing about the base
model is retrained here.

**The decision, against the pre-registered 0.05 margin:** the two results disagree sharply.
On square-okhttp the model clearly beats the control (a 0.48 AUC margin with a 95% CI nowhere
near zero — real, not noise). On tootallnate the model is *worse* than the control on
average, though the CI (-0.305 to 0.177) comfortably includes zero, so on only 46 test
examples this fold cannot actually distinguish "model worse than control" from "noise."

**Decision: throw the sequence model away.** The pre-registered rule asked for the model to
reliably beat the control; instead it beat the control on one project and, at best, tied it
on another, with the direction of the tie unresolved by the available data. A component that
only sometimes clears a free heuristic — and cannot be told apart from that heuristic when it
doesn't — does not earn a place in the system on the evidence collected here.

## Secondary finding: output collapse
The model's calibrated output collapsed to only 4 distinct probability values on tootallnate
(46 test examples) and 7 on square-okhttp (258 test examples) — very low resolution, most
likely from the small GRU (hidden size 8) trained on few examples (76-288 per fold) learning
only a handful of coarse input patterns rather than a smooth function of the prefix. This is
exactly the ambiguity `design/08-sequence-observer.md`'s Emits clause was written to catch:
a calibrated AUC alone cannot distinguish "no discrimination" from "collapsed output," and
reporting the distinct-value count alongside it is what makes that distinction visible here.
