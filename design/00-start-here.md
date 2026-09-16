# Slice 00 — system boundary

## Responsibility
Estimate the likely real state of a red build (real defect / flaky / infra) and surface
that estimate to the on-call release engineer.

## Reads
The red build report: which test failed, and whatever evidence is available about that
test/build (no schema decided yet — that is a later phase).

## Emits
A probability distribution over {real defect, flaky, infra}, addressed to the on-call
engineer. Nothing else — no action, no instruction.

## Refuses
When the evidence is too thin to give a confident estimate (e.g. a new test with no
history), it does not guess. It defers to the engineer instead of emitting a probability
it cannot support.

## Rejected/narrowed AI proposal
Proposed: the system auto-reruns the failing test on low confidence instead of always
deferring to the engineer. Narrowed, not rejected: accepted only for rerun, because
rerunning is reversible and has no effect outside the CI run. Release and stop remain
strictly human actions, never automated.

## Constraint
The system never takes an action on the release or the branch. It has no authority to
release, stop, merge, or delete anything — those remain the engineer's actions, always.
The one exception is rerunning the test it just evaluated: that action is reversible and
has no effect outside the CI run, so the system may trigger it automatically. Everything
that touches the release itself is still shown to the engineer, never done by the system.

## Connects to
Nothing upstream yet (this is the boundary slice). Downstream: slice 01 defines the exact
output contract (the four outputs) that consumes this estimate.
