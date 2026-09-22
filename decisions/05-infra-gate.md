# Decision — trust gate

## What a run looked like, before automating anything
Inspected `kevinsawicki-http-request` run archives directly: each project `.tgz` contains
per-run `.tgz` archives, and `maven.log` lives inside each one. A clean run (5825) showed two
per-class summaries (`Tests run: 161 ...`, `Tests run: 2 ...`) each with a `Time elapsed`, and
one final `Results :` block per module — the block total, not a third module — with no
`Time elapsed`. A failing run (8663) showed the same shape, with `Failed tests:` /
`Tests in error:` sections listing individual `method(Class): message` lines between the
`Results :` header and the final tally.

**Real finding that changed the design:** this dataset's build harness does not fail the
overall build on test failures — run 8663 had 11 failures + 4 errors out of 163 tests and
still logged `[INFO] BUILD SUCCESS`. `BUILD SUCCESS`/`BUILD FAILURE` text alone cannot detect
a broken build; the actual signal is whether any `Results :` / `Tests run:` summary exists
at all (if the code never compiled, no test ever got a chance to produce one).

**Second real finding, from square-okhttp specifically:** the failing-test name format inside
a `Results :` block is not stable across projects. kevinsawicki-http-request uses
`method(Class): message`; square-okhttp uses `Class.method:line message`, with
`RunClass>DeclaringClass.method:line` for an inherited test method, and a `->` call-chain
continuation on the same line for where inside that test the failure occurred. A name regex
built and tested only against kevinsawicki silently matched zero names on square-okhttp,
which would have reported every run `TRUSTED` with a fabricated "0 failed" reason — for the
one project fetched specifically because it has real contamination. Fixed by widening the
regex to both formats and adding a runtime cross-check: each block's own `Failures + Errors`
count must equal how many names were parsed from it, or the run is `UNKNOWN`, not scored on
an unverified parse. See `ai-ledger/05-infra-gate.md`.

## Verdicts
`TRUSTED`, `BUILD_FAILED`, `LOG_TRUNCATED`, `MASS_FAILURE`, `UNKNOWN`.

## Precedence
`BUILD_FAILED` -> `LOG_TRUNCATED` -> `MASS_FAILURE` -> `TRUSTED` / `UNKNOWN`.

A run that never compiled reports every test as "failed" and would also match
`MASS_FAILURE` by fraction alone. `BUILD_FAILED` must win: mass failure means the tests
actually ran and legitimately failed; build failure means they never got a fair chance to
run. Conflating them would send a future engineer chasing flaky tests when the real problem
is a broken build.

## Rules, from what was actually observed
- `BUILD_FAILED`: no `Results :`/`Tests run:` summary anywhere, and the log ends in
  `BUILD FAILURE`.
- `LOG_TRUNCATED`: neither `BUILD SUCCESS` nor `BUILD FAILURE` appears anywhere.
- `MASS_FAILURE`: a summary exists; failure fraction (after excluding that project's
  deterministic tests) is >= 30%.
- `TRUSTED`: a summary and a terminal marker exist; failure fraction is below 30%.
- `UNKNOWN`: a terminal marker exists but no summary does — a log that claims success with
  no evidence any test ran is suspicious on its own, not evidence of a clean run.

## Mass-failure threshold: 10% (revised from an initial 30% guess)
30% was the first guess, reasoned only in the abstract ("a normal bad day shouldn't fail a
third of a suite"). Once square-okhttp's real archive was scanned, the actual post-exclusion
failure fraction across all 7,872 non-truncated runs topped out at 10.07% (mean 0.28%, p95
0.55%) — 30% was never close to being tested by this data at all. Inspecting that single
worst run (`2540`) by hand showed a genuine infrastructure symptom: a DNS resolution failure
inside a shared `setUp()`, cascading into a dozen unrelated test methods. That is exactly the
kind of run this gate exists to catch, and 30% would have let it through as `TRUSTED`.
Lowered to 10% so this run is caught, with the top three non-deterministic runs (10.07%,
8.98%, 8.98%) as the only runs anywhere near the line. Still a threshold chosen from one
project's distribution, not derived from a principled cost model — see
`knowns/05-infra-gate.md` for what remains open about whether it generalizes.

## Cross-run deterministic threshold: 80%
A test failing in most runs is consistently broken, not randomly noisy — excluding it from
the mass-failure fraction stops a permanently-broken test from making every run look
contaminated. The known limitation: a fraction gate like this cannot prove a cluster of
failures shared one root cause, only that they correlate with a run-level trust signal.
