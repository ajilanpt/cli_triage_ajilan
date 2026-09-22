# Experiment — split comparison

## Prediction (written before running anything; not edited afterward)

**What a random row-wise split measures:** how well the model fits the general pattern of
flaky-vs-not across rows drawn from all 25 projects pooled together, with no guarantee that
a given project's rows are kept together — a project seen in training can also appear in
test.

**What the project-held-out split measures:** how well the model performs on a project it
has never seen any row from during training — the actual shape of deployment, per
`decisions/06-split-choice.md`.

**Which will score higher, and by how much:** the project-held-out split will score
**higher**, by **more than 10%**.

**What would tell me this reasoning was wrong:** if the random split scores higher instead —
that would mean the model is doing better when it can see rows from the same project in both
train and test than when it has to generalize to an unseen project, which would suggest it is
picking up on something project-specific (memorizing per-project patterns) rather than a
general flaky-test signal.

---

## Result

Gradient-boosted trees, same 15 numeric features, same 5 folds each, scored with ROC AUC
(`artifacts/results/baseline.json`):

| Split | Mean AUC | Std |
|---|---|---|
| Random row-wise | **0.907** | 0.008 |
| Project held-out (grouped) | **0.587** | 0.245 |

Majority-class baseline accuracy: 96.8% (positive rate 3.16%).

**The prediction's direction was wrong.** I predicted the project-held-out split would score
higher, by more than 10%. The random split scored higher instead, by about 32 points of AUC
— and one grouped fold scored 0.121, *worse than a coin flip*.

**But the falsification criterion I wrote down beforehand was right.** I wrote: "if the
random split scores higher instead — that would mean the model is doing better when it can
see rows from the same project in both train and test... picking up on something
project-specific rather than a general flaky-test signal." That is exactly what happened.

**What actually explains it, from real data:** per-project positive rate is wildly uneven —
0% for `commons-exec` and `jimfs`, 62% for `alluxio`, versus an overall rate of 3.16%.
`assertj-core` alone contributes 6,261 rows with exactly 1 positive. ROC AUC is rank-based
and has no imbalance-dependent baseline (0.5 always means chance), so imbalance alone
doesn't explain the *mean* gap between splits. What does: under the random split, a model
sees some rows of a high-positive-rate project like `alluxio` in training and other rows of
the *same* project in test, and can partly succeed by learning "this looks like an alluxio
row" rather than a real flakiness signal — a leak that only exists when a project appears on
both sides. Holding a project out entirely removes that leak, which is why the grouped split
is both lower on average and far less stable fold-to-fold (a fold that holds out an unusual
project, like the tiny high-rate `alluxio`, is a very different test than one holding out
`assertj-core`).

## What this means for the system
The 0.907 random-split number is not a measurement of this model's ability to catch flaky
tests in a new project — it is inflated by project-identity leakage and would badly
overstate real-world performance if reported as "the" number. The 0.587 grouped number is
the honest one for the deployment this system targets (per `decisions/06-split-choice.md`):
weak, unstable across projects, and the real starting point for phase 07.
