## Review
1. slice fit   — no code this phase; the decision (cost-weighted risk over accuracy) matches
   the external-contract slice, which exists to carry cost downstream, not just a label.
2. correctness — n/a, no code drafted this phase.
3. ML validity — n/a, no code drafted this phase.
4. necessity   — n/a, no code drafted this phase.

## Proposed
Use accuracy as the objective instead of cost-weighted risk. Simpler to explain, and
sklearn computes it for free.

## Rejected / narrowed to
Rejected. The objective is cost-weighted risk from the table in `PROBLEM.md`.

## Because
Accuracy treats every mistake the same, but the cost table shows they aren't equal — a real
defect that ships costs up to $5000, while a false alarm costs $500 or less. With real
defects likely rare compared to flaky/infra builds, a system that always guesses the
majority class could look highly accurate while catching zero real defects. Accuracy can't
see that; cost-weighted risk can.

## Ponytail pass
Not applicable — no code this phase.
