# Decision — independence rules

## The overlap, computed
- Observer 1 (tabular, `design/07`) reads: the phase-04 FlakeFlagger CSV's numeric columns.
- Observer 2 (sequence, `design/08`) reads: per-test pass/fail sequences derived from phase
  05's TRUSTED-run gate over the 3 raw `maven.log` archives.
- Observer 3 (retrieval, `design/09`) reads: per-test failure/exception text, also derived
  from phase 05's TRUSTED-run gate over the same 3 raw archives.

Observers 2 and 3 share a root source: the same TRUSTED runs, from the same 3 projects,
gated by the same phase-05 logic. They compute different representations (a binary sequence
vs. exception text), but a mistake in phase 05's gate (or a poisoned run it missed) would
propagate into both identically. If a test's history was mislabeled upstream, both observers
inherit the same mistake — it is one observation, not two. Observer 1 is genuinely
independent: a separate dataset (FlakeFlagger), computed by a different process, sharing no
upstream failure mode with 05's gate.

## The rules, derived from the failure mode above
1. **Two observers' agreement counts as independent evidence only if they read from
   genuinely different underlying sources** — not just different representations of the same
   source. Prevents: false confidence from double-counting one observation as if it were two
   (observers 2 and 3 here).
2. **Every observer reports a calibrated probability, or is explicitly marked uncalibrated.**
   Prevents: downstream treating a raw, uncalibrated score as a measured probability (e.g.
   averaging an uncalibrated 0.9 with a calibrated 0.9 as if they meant the same thing).
3. **"No evidence" and "evidence pointing in every direction" must not be encoded
   identically.** Both can look like a probability near 0.5 from a single scalar; without a
   separate signal for "how much was actually observed," the two are indistinguishable.
   Prevents: an abstain-worthy total absence of signal being silently treated the same as a
   genuinely uncertain, well-evidenced case.
4. **No observer may read another observer's output.** Each writes independently to the
   common evidence record. Prevents: an artificial feedback loop where "three observers
   agree" is true only because one observer's output leaked into another's input, making
   unanimity trivial rather than earned.
5. **Cost and latency are measured and reported by the component that incurred them, not
   documented as constants elsewhere.** Prevents: a cost figure silently going stale as the
   system changes, with nothing to catch the drift.

## What this changes about the system decision
The run-level release recommendation cannot treat observer 2 and observer 3 agreeing as
strong corroborating evidence the way it could treat observer 1 agreeing with either of them.
Fusion (phase 11) must weight or gate on source independence, not just count how many
observers agree.
