## Review
1. slice fit   — `parse_run_log` is the one function that assigns a verdict, matching the
   precedence order from `design/05-infra-gate.md`; `scan_project` returns the
   deterministic-exclusion set alongside verdicts so later phases reuse it.
2. correctness — first draft double-counted totals: it summed every `Tests run:` line,
   including both each test class's per-class line (with `Time elapsed`) and the module's
   final `Results :` total, which already included the per-class numbers. Caught by running
   it against a real clean run (163 actual tests) and getting 326. Fixed to only sum
   `Results :` blocks.
3. ML validity — the mass-failure and deterministic thresholds (30%, 80%) are recorded as
   guesses, not measured, in `decisions/05-infra-gate.md`; nothing was reported as more
   certain than it is.
4. necessity   — `read_run_archive`/`_iter_run_logs` were originally duplicated between
   `find_deterministic_tests` and `scan_project`; consolidated into one shared generator.

## Proposed
Use Maven's own exit status (`BUILD SUCCESS` / `BUILD FAILURE`) directly as the trust
signal — simplest possible implementation, and it's the field Maven itself uses to mean
"something went wrong."

## Rejected / narrowed to
Rejected. `BUILD_FAILED` is detected by the absence of any `Results :`/`Tests run:` summary
(the build never got far enough to run tests), not by the `BUILD SUCCESS`/`BUILD FAILURE`
string.

## Because
Real data from this project's own archives (run `kevinsawicki-http-request-8663`) showed 11
failures + 4 errors out of 163 tests, and the log still ended in `[INFO] BUILD SUCCESS`.
This dataset's collection harness does not fail the overall build on test failures — it
needs the build to keep completing across thousands of reruns. Using the Maven exit status
directly would have silently classified genuinely poisoned runs as fine, and vice versa.

## Ponytail pass
`ci_triage/infra.py` is regex-based parsing plus two small loop functions over `tarfile`;
nothing here duplicates a library. Kept as plain functions, no class, per the phase's own
instruction that this "is a function that reads a run and returns a verdict plus a reason,
not a framework."
