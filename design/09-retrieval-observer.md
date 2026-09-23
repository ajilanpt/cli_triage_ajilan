# Slice 09 — observer 3 (retrieval)

## Responsibility
Given a new failure's exception/stack-trace text, retrieve the k most similar past failures
from a stateful index and vote whether this failure looks like genuine intermittent test
flakiness or non-flaky noise (a deterministically-broken test, or infra-caused failure) —
no training, no learned weights.

## Reads
Failure/exception text extracted from phase 05's TRUSTED runs in the 3 raw-archive projects
(kevinsawicki-http-request, tootallnate-java-websocket, square-okhttp), split into two real
classes per `decisions/09-index-contents.md`:
- **flaky** — failure text from a non-deterministic (intermittently failing) test.
- **not-flaky** — failure text from either a deterministic test (phase 05's >=80%-of-runs
  failures) or a run phase 05 marked `MASS_FAILURE`.
Both classes are real exception/stack-trace text, chosen specifically because both could
plausibly resemble a real query (per `PROBLEM.md`, a query only ever happens after a build
already went red — a "the test passed" document could never resemble a real query and would
sit unused, silently reproducing the failures-only trap).

## Emits
Per query: the majority-vote label over its top-k neighbours, the **distinct test count**
among those k (five hits on the same test are one opinion, not five), and precision@k.
Reported separately for within-project and (only where the data supports it) cross-project
evaluation, alongside the majority-class baseline for the same population.

## Refuses
Scores an evaluation only when the index being queried contains real text from both classes
with at least k documents each. When it does not (e.g. a held-out project's training index
lacks one class entirely), that evaluation is recorded as skipped, with the reason, rather
than a number being invented or a reference result reused (TASK.md, step 5).

## Constraint
A query must never be able to retrieve a document sourced from its own run/occurrence. This
is the required invariant test — an index that can retrieve its own query trivially wins on
paper and means nothing.

## Connects to
Upstream: phase 05 (`ci_triage/infra.py`) directly — the TRUSTED gate, the deterministic-test
set, and the raw failure text all come from there, not the phase-04 CSV.
Downstream: phase 10's integration contract and phase 11's fusion/arbiter, alongside the
tabular (07) and sequence (08) observers — scoped, like phase 08, to only the 3 projects with
raw archives.
