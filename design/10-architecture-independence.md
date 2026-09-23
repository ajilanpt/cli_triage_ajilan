# Slice 10 — integration contract

## Responsibility
Define the one evidence record every observer writes to, and enforce the rules that make
combining multiple observers' agreement meaningful evidence rather than one observation
counted twice.

## Reads
Nothing from the observers' own internals — only their published evidence records. This
slice never reads `ci_triage/tabular.py`, `sequences.py`, or `retrieval.py`'s internals
directly; it defines the shape they must write into (`ci_triage/contracts.py`).

## Emits
`ci_triage/contracts.py`'s `Evidence` record: what was observed (the test/case identity),
the probability, an explicit `calibrated: bool` flag, what the observer read (its declared
source, for the overlap check below), and cost in money and milliseconds — measured by the
observer that produced it, not a constant documented elsewhere.

## Refuses
An `Evidence` record with a probability but no explicit calibration flag is invalid — there
is no default. Downstream (fusion, phase 11) must never be able to treat an uncalibrated
score as if it were a measured probability by omission.

## Constraint
No observer may read another observer's output. Each writes independently to the common
`Evidence` record; none reads a sibling's record before writing its own. This is checked by
convention in this phase (no shared mutable state between observer calls) and becomes load-
bearing once phase 11's fusion logic exists to violate it.

## Connects to
Upstream: observers 07 (tabular), 08 (sequence), 09 (retrieval) — each must be rewritten (or
wrapped) to emit `Evidence` records; their `Reads` sources are the input to the overlap
computation this phase performs (`decisions/10-independence.md`).
Downstream: phase 11's fusion/arbiter, which reads only `Evidence` records, never an
observer's raw internals.
