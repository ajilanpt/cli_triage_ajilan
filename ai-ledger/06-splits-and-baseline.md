## Review
1. slice fit   — `generate_splits`/`load_splits` are the only way to get a fold assignment;
   no code path recomputes a split as a side effect of running an experiment, matching
   `design/06-splits-and-baseline.md`'s Refuses clause.
2. correctness — the invariant test (`test_no_project_appears_in_more_than_one_grouped_fold`)
   is built on a hand-constructed toy dataframe with uneven per-project row counts
   specifically so a naive (non-grouped) split would visibly violate it.
3. ML validity — the baseline compares the same model/features across both splits and
   reports mean and standard deviation across all 5 folds, not a single number, per the
   phase's own instruction.
4. necessity   — one shared `_signature`/`fold_indices` pair is used for both the grouped
   and random splits rather than two parallel implementations.

## Proposed
Use a plain random 80/20 train/test split (unstratified, ungrouped) as the first
implementation — simplest possible, and `sklearn.model_selection.train_test_split` is one
line.

## Rejected / narrowed to
Rejected. Per `decisions/06-split-choice.md`, production sees projects the model has never
trained on — a random split (whether one 80/20 split or k-fold) lets rows from the same
project land on both sides, which the real result confirms is not a hypothetical concern:
the random split scored 0.907 mean AUC versus 0.587 for the grouped split, on the identical
model and features. `GroupKFold` on project identity is the only split that matches the
deployment question that was asked first.

## Because
The gap between the two splits is not noise — `experiments/06-split-comparison.md` shows it
came from project identity leaking between train and test under the random split (positive
rate ranges from 0% to 62% across the 25 projects; a model can partly succeed on a project it
saw at all in training without learning a real flakiness signal). Reporting the random
split's number as "the" system performance would be reporting a measurement of
project-memorization, not of the thing this system needs to do in production.

## Ponytail pass
`ci_triage/splits.py` is two `sklearn` splitter calls plus a small save/load/signature
wrapper around them — no class, no configuration nothing else uses. `GroupKFold`/`KFold` do
the actual splitting; only the persistence and staleness-check are original code.
