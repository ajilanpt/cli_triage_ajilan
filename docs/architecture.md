# Architecture

Assembled from `design/00-*.md` through `design/10-*.md` — see those files for each slice's
full contract. This document adds the one thing no single slice states on its own: how the
levels relate, and why agreement between observers is not automatically evidence.

## The two levels

**Case-level: "is this specific test flaky?"** Answered by observers 1–3 (`design/07`, `08`,
`09`), one test at a time. Consumed by whatever assembles the run-level picture — never
shown directly to the release engineer as a release recommendation.

**Run-level: "should we stop this release?"** Answered by fusion/the arbiter (phase 11),
which looks at *all* the case-level evidence for a build — potentially dozens or hundreds of
failing tests — and decides the four-way output from `design/01-decision-and-cost.md`
(stop the release / isolate as flaky / rerun / abstain).

**What goes wrong if you conflate them:** a build with 197 failing tests, most of them
genuinely flaky, and one that is a real defect. If the run-level decision is built by
averaging the 197 case-level probabilities, the one real defect's signal gets diluted into
the crowd and the release ships. The run-level layer must never collapse case-level evidence
before an engineer (or the arbiter) can see the worst individual case — averaging is not a
safe default aggregation here (phase 11's own material names this exact trap: "mean fusion
diluting a real observation").

## Independence

`decisions/10-independence.md` computes the actual overlap between what each observer reads:
observers 2 (sequence) and 3 (retrieval) both derive from phase 05's TRUSTED-run gate over
the same 3 raw archives — different representations of the same underlying observations, not
two independent looks. Observer 1 (tabular) is genuinely independent, from a separate
dataset (FlakeFlagger's CSV) computed by a different process.

The five rules this forces (full reasoning and the failure each prevents:
`decisions/10-independence.md`):
1. Agreement counts as independent evidence only across genuinely different sources.
2. Every observer states `calibrated: bool` explicitly — no default (`ci_triage/contracts.py`).
3. "No evidence" (`n_observations=0`) and "evidence pointing in every direction"
   (`n_observations` large, `probability` near 0.5) must never collapse into the same signal.
4. No observer reads another observer's output — each writes independently to the shared
   `Evidence` record.
5. Cost and latency are measured and reported by the component that incurred them.

## Slices so far

| Phase | Slice | Design |
|---|---|---|
| 00 | system boundary | `design/00-start-here.md` |
| 01 | external contract (4 outputs) | `design/01-decision-and-cost.md` |
| 02 | evaluation component | `design/02-measurement.md` |
| 03 | ground-truth source | `design/03-ground-truth.md` |
| 04 | ingestion / leak guard | `design/04-data-and-licence.md` |
| 05 | trust gate | `design/05-infra-gate.md` |
| 06 | experiment harness | `design/06-splits-and-baseline.md` |
| 07 | observer 1 (tabular) | `design/07-tabular-and-the-pivot.md` |
| 08 | observer 2 (sequence) | `design/08-sequence-observer.md` |
| 09 | observer 3 (retrieval) | `design/09-retrieval-observer.md` |
| 10 | integration contract | `design/10-architecture-independence.md` (this phase) |
