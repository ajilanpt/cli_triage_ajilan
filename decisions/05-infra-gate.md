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

## Mass-failure threshold: 30%
Chosen because a normal bad day (a handful of real regressions) shouldn't fail a third of an
entire suite at once; that scale of failure looks like the environment, not the code. This
is a guess, not a measured number. Choosing it better would need historical data on what a
real bad build actually looks like for these projects.

## Cross-run deterministic threshold: 80%
A test failing in most runs is consistently broken, not randomly noisy — excluding it from
the mass-failure fraction stops a permanently-broken test from making every run look
contaminated. The known limitation: a fraction gate like this cannot prove a cluster of
failures shared one root cause, only that they correlate with a run-level trust signal.
