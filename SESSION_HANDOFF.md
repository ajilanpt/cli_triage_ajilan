# Session handoff — 2026-09-16

Transient working note for the next Claude Code session, not a lab deliverable. Safe to
delete once phase 05 is properly redone and understood.

## Where we are
Phases 00–04 are complete and pass `uv run lab.py check NN`. Phase 05 (trust gate) was
drafted in the last session, but the builder didn't feel they properly understood the
`maven.log` / `infra.py` material — **redo phase 05 from the start, slower**, explaining
concepts before writing any code. Don't just re-present the existing draft as finished.

## What exists already on disk (treat as a first draft to walk back through, not a result)
- `design/05-infra-gate.md`, `decisions/05-infra-gate.md`, `ci_triage/infra.py`,
  `tests/test_infra.py` (8 tests, passing), `ai-ledger/05-infra-gate.md`.
- Still missing: `artifacts/results/infra.json` (needs real numbers from a project with
  actual contaminated runs) and `knowns/05-infra-gate.md`.

## What "maven.log" and "infra.py" are, for context
Each project's raw data is one `.tgz` archive containing thousands of per-run `.tgz`
archives — one per CI build attempt, from the rerun procedure decided in phase 03. Each run
archive contains a `maven.log`, the build's console output. `infra.py` reads that text to
decide whether a run's results can be trusted as evidence, independent of whether the tests
in it passed or failed — a run can lie (e.g. the code never compiled, so every test looks
"failed" even though nothing was wrong with the tests themselves).

This is a separate raw-log analysis. It is **not** yet wired into `ci_triage/data.py` or the
phase-04 joined dataframe — that would be a further step, mainly relevant once phases 08–09
need the actual pass/fail sequence per test rather than just final aggregate counts.

## Data state
`data/raw/` currently has:
- `test_features.csv`, `test_results.csv`, `Project_Info.csv` (phase 04).
- `kevinsawicki-http-request.tgz` (38MB) — fully downloaded. All 7,905 runs verdict
  `TRUSTED`, 15 distinct failing tests, 0 deterministic — matches `data/README.md`'s
  reference archive-scan numbers exactly.
- `tootallnate-java-websocket.tgz` (56MB) — fully downloaded. All 7,905 runs `TRUSTED`, 23
  distinct failing tests found (data/README.md's archive-scan says 43 — this gap is not yet
  root-caused, treat as open, don't silently assume either number is right).
- `square-okhttp.tgz` — **not downloaded**. This is the project `data/README.md` most
  recommends (real class balance, genuine contaminated runs), needed for a real
  before/after "trusted vs all runs" comparison, since the two archives above turned out to
  have zero untrusted runs at all. Zenodo was very slow/flaky for this ~520MB file (curl
  with `--retry` and `-C -` resume still only managed ~4MB/min effective throughput with
  frequent connection drops).

## The two-PC plan (already agreed with the builder — don't relitigate it)
Builder downloads `square-okhttp.tgz` on their office PC, then zips `data/raw/` (only that
folder — not `data/cache/`, `data/distill/`, or the deleted scratch `data/extract/`) and
copies it to this PC by hand later. `data/` stays gitignored on purpose, matching
`data/README.md`'s own instruction to record commands, not bytes — do not suggest
committing it or changing `.gitignore`.

## Working-style note
The builder wants the decision-dialogue method actually followed for phase 05 specifically —
concepts explained before code, one question at a time, waiting for real answers — not code
drafted quickly with explanation bolted on after. This session moved too fast once real data
and file-format parsing were involved. Slow down.
