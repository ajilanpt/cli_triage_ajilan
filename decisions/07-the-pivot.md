# Decision — the pivot

## The four honest responses to a weak grouped-split result (AUC 0.587, one fold at 0.121)
1. **Accept it and ship a weak component.** Simplest, but per `PROBLEM.md`'s cost table, a
   real defect misreported as flaky costs $5000 — a near-chance signal (0.587, worse than a
   coin flip on some projects) is closer to noise dressed as evidence than a component that
   should influence a 02:47 release decision. Rejected on that basis, not on the metric alone.
2. **Get better features.** Nothing rules this out eventually, but nothing in the failure
   mode points at a specific missing feature either — the grouped fold's instability tracks
   project identity (positive rate 0% to 62%), not an obvious feature gap.
3. **Get more data.** More projects would help the *estimate's* stability, but does not
   change the underlying question being asked, and isn't available on this lab's timeline.
4. **Change the question.** Chosen.

## The argument, from PROBLEM.md, not the metric
`PROBLEM.md` frames the actor as "the on-call release engineer" on a specific build, not an
abstract cross-project classifier. `decisions/06-split-choice.md` already established that
production sees projects the model was never trained on **once, cold** — but that framing
assumed a single model trained once and never touched again. A more accurate reading of how
CI triage tooling is actually adopted: a team installs it on *their* project, and it
accumulates that project's own build history over time. The zero-shot cross-project question
("perform well on a project you've never seen a single row from") is not what most of this
system's operating life looks like — it's only the cold-start case. The steady-state
question is **per-project**: given a project's own accumulating history, how well does a
model trained on that project's own data perform on more of that same project's data.

## The pivot
Train and evaluate a separate model **per project**, using ordinary (non-grouped) k-fold
cross-validation *within* that project's own rows — the leak phase 06 was guarding against
(project identity leaking between train/test) is no longer a leak once the deployment
question itself is "does this project's own model work on more of this project's own data."

## Cost
This changes the claim, not just the number. The system is no longer "one model that works
on any unseen project cold" — it's "a model that needs a project's own history to become
useful," with an explicit cold-start gap for a brand-new project with no accumulated data
yet (the original 0.587 zero-shot number is the honest answer to *that* narrower question,
and stays on record rather than being discarded). Also: several projects have too few
positives to fit or evaluate a per-project model at all (`commons-exec`, `jimfs`: 0 positives;
`assertj-core`, `handlebars.java`, `ninja`: 1 positive) — the pivot does not help those
projects, and that gap is named rather than hidden.
