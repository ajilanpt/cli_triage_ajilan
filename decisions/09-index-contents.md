# Decision — index contents

## What is indexed
Real exception/stack-trace text extracted from phase 05's TRUSTED runs, from the 3 projects
with raw archives, split into two classes:

- **flaky** — the failure text of a test that fails intermittently (not deterministic per
  phase 05's >=80%-of-runs threshold). One document per (test, TRUSTED run in which it
  failed).
- **not-flaky** — the failure text of either (a) a deterministic test (phase 05: fails in
  >=80% of runs — e.g. the JDK/SSL `NoSuchMethodError` mismatch found in square-okhttp), or
  (b) any run phase 05 marked `MASS_FAILURE` (e.g. the DNS `UnknownHostException` in run
  `2540`) — real infra-caused failure text, not a flaky test at all.

## What is deliberately not indexed
- Text from tests that never failed. Per `PROBLEM.md`, a query only ever happens after a
  build has already gone red — a document built from a passing test could never resemble a
  real query, so it would sit in the index unused. Including it would not make the index
  wrong, just silently useless on that side, reproducing the "only failures" trap by a
  different route.
- Labels, test names alone, or any synthetic/placeholder text as a substitute for real
  failure text — the corpus must be real text an engineer would actually paste in.

## The failures-only thought experiment
If the index contained only failures (no non-flaky/infra class), every neighbour of any
query would itself be a failure by construction — the vote could never do anything but agree
"yes, this looks like a failure," regardless of what the query said. The system would be
correct on paper and uninformative in practice; it could not distinguish a genuinely flaky
test from a one-off DNS hiccup, which is the entire point of this observer.

## Scope
Only the 3 projects with raw archives can supply real failure text at all — the phase-04 CSV
has no text, only numeric features. Cross-project evaluation is therefore attempted only
where enough of these 3 projects, held one out, still leave both classes represented in the
remaining training index; see `artifacts/results/retrieval.json` for which evaluations were
actually performable.
