# Slice 05 — trust gate

## Responsibility
Decide, per CI run, whether its recorded test outcomes may be used as evidence at all. Runs
upstream of every split and every observer, because one poisoned run can manufacture dozens
of fake "flaky" tests that every later phase would inherit.

## Reads
The raw `maven.log` for a run, nested inside that run's archive inside the project archive.
When a log contains multiple `Tests run:` summaries (a multi-module build), all of them —
summed, not just the last one.

## Emits
Per run: one verdict from `{TRUSTED, BUILD_FAILED, LOG_TRUNCATED, MASS_FAILURE, UNKNOWN}` and
a reason string that must match what was actually found in the log — a verdict can be right
while its stated reason is fabricated, and that is treated as a bug, not a passing test.

Per project: a deterministic-test exclusion set — tests failing in >=80% of that project's
runs, which are excluded from the mass-failure fraction (they are consistently broken, not
random infrastructure noise) and returned alongside the run verdicts so later phases reuse
this decision instead of re-parsing the archives.

## Refuses
When a run matches none of `BUILD_FAILED`, `LOG_TRUNCATED`, or `MASS_FAILURE`, but the log
also does not parse as a clean, complete test-summary, the gate emits `UNKNOWN` rather than
forcing a `TRUSTED`/rejected call it cannot support.

## Constraint
Verdicts are checked in a fixed precedence: `BUILD_FAILED` before `LOG_TRUNCATED` before
`MASS_FAILURE` before `TRUSTED`/`UNKNOWN`. A run that never compiled must never be reported
as `MASS_FAILURE`, even though every test in it technically "failed" — the two causes
require different fixes, and the reason is what a future engineer reads.

## Connects to
Upstream: none — this reads raw archives directly, independent of phase 04's CSV pipeline.
Downstream: phase 06's splits and every observer (07 tabular, 08 sequence, 09 retrieval)
must be built only on runs this gate marks `TRUSTED`, using the deterministic-exclusion set
this gate produces rather than recomputing it.
