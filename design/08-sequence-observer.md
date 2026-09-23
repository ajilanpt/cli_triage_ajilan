# Slice 08 — observer 2 (sequence)

## Responsibility
Given the first *k* observed reruns of a test (the prefix), predict whether that test will
flip (show both pass and fail) again within a later, non-overlapping window of reruns (the
suffix) — a rerun-budget question ("should I keep trusting this test if I stop watching it
after *k* reruns"), not a code-change question, since all reruns are of one fixed commit.

## Reads
Per-test, per-run pass/fail outcomes parsed from the JUnit XML surefire reports inside each
run's archive (`TEST-<class>.xml`, `<testcase>` with no `<failure>`/`<error>` child = pass),
restricted to runs phase 05's gate marked `TRUSTED` for that project. Only the 3 projects
with raw archives (kevinsawicki-http-request, tootallnate-java-websocket, square-okhttp) can
supply this — the phase-04 CSV has no per-run sequence, only aggregate counts.

## Emits
Per (test, prefix-length) example: a probability that the suffix flips. Reported per fold:
raw AUC, calibrated AUC, and the count of distinct calibrated probability values — a
calibrated AUC of exactly 0.5 means either "no discrimination" or "everything collapsed to
one probability," and those are different failures that look identical without the count.

## Refuses
Emits nothing for a (test, prefix-length) pair when fewer than one full prefix-plus-suffix
window of TRUSTED runs exists for that test — there is no run left to compute a suffix label
from, so no example is produced rather than one built from a truncated or single-sided
window.

## Constraint
No run ID may appear in both the prefix and the suffix of the same example — this is the
fix for the circularity found in `experiments/08-heuristic-control.md` (feeding a model the
same runs `IsFlaky` was computed from just returns the label's own definition), and it
becomes the phase's required invariant test.

## Connects to
Upstream: phase 05 (`ci_triage/infra.py`, the TRUSTED-run gate), the raw run archives
directly (not phase 04's CSV).
Downstream: phase 10's integration contract and phase 11's fusion/arbiter, alongside the
tabular (07) and retrieval (09) observers — but only for the 3 projects this observer has
sequence data for; elsewhere it has nothing to contribute.
