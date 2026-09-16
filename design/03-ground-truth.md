# Slice 03 — ground-truth source

## Responsibility
Report a test's flaky/not-flaky label together with its provenance — the labeling
procedure and the rerun count behind it — not the bare label alone.

## Reads
The raw rerun results for a test: the sequence of pass/fail outcomes across however many
reruns were performed on identical code.

## Emits
For each test: the label (flaky/not-flaky) and the rerun count it was derived from. A label
with no recorded rerun count is a number with no error bar, so the count always ships with
the label, never separately.

## Refuses
Refuses to emit a usable "not flaky" label when the rerun count is missing or below the
trustworthy threshold. A test rerun only once (or not at all) that happened to pass is not
evidence of stability — it is an untested case, and must not be treated as a solid negative.

## Constraint
Must never let a label be used downstream without its rerun count attached, and must never
treat a low-rerun-count "not flaky" the same as a high-rerun-count one.

## Connects to
Upstream: none yet — this is the first data-adjacent slice. Downstream: phase 04 builds the
feature matrix from these labels, and the rerun-count/trust distinction this slice makes
carries forward into phase 05's trust gate.
