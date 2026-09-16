# Slice 01 — external contract

## Responsibility
Translate the probability distribution over {real defect, flaky, infra} into one of four
caller-facing outputs, each tied to a distinct engineer action.

## Reads
The probability distribution over {real defect, flaky, infra} emitted by slice 00. Derives
a confidence/entropy measure from that same distribution — a flat distribution is
low-confidence, a peaked one is high-confidence. Nothing else; no new input is required
from slice 00.

## Emits
One of four outputs, each addressed to the on-call engineer and each carrying the action it
implies:

| Output | Engineer action |
|---|---|
| real defect | stop the release |
| flaky | isolate the test, release continues |
| infra | rerun the test |
| abstain | no recommendation; engineer manually investigates and decides |

## Refuses
Emits ABSTAIN when the distribution's entropy is too high to support a confident single
cause — i.e. the evidence does not favor any one of the three causes enough to act on.

## Constraint
Must never round a high-entropy (flat) distribution into a confident-looking single cause.
When the distribution is genuinely uncertain, it must abstain rather than manufacture a
headline verdict.

## Connects to
Upstream: slice 00, which supplies the probability distribution this slice reads.
Downstream: open for now — no later slice has been designed yet to consume this contract.
