## Review
1. slice fit   — `ci_triage/contracts.py` defines only the shared record and a helper to
   count independent sources; it does not implement fusion (phase 11's job) or touch any
   observer's internals, matching `design/10-architecture-independence.md`'s Reads clause.
2. correctness — `calibrated` has no default value, so `Evidence(...)` without it raises
   `TypeError` at construction, not a silent `None`/`False` default that could be mistaken
   for a real answer.
3. ML validity — `n_observations` is a separate field from `probability`, specifically so a
   0.5 from "nothing observed yet" and a 0.5 from "50 conflicting observations" cannot
   collapse into the same signal downstream.
4. necessity   — `Evidence` is a frozen dataclass with 8 fields; no registry, no plugin
   system, no base class hierarchy, per TASK.md's explicit "ponytail: a dataclass" instruction.

## Proposed
Weight fusion by how many observers agree (e.g. "3 of 3 observers say flaky" counts for more
than "1 of 3"), since more agreement intuitively feels like stronger evidence.

## Rejected / narrowed to
Rejected by the builder, working from the concrete overlap computation in
`decisions/10-independence.md`: observers 2 and 3 read from the same underlying source
(phase 05's TRUSTED-run gate over the same 3 archives), so "3 of 3 agree" here is really "2
independent sources agree" -- counting observers instead of counting independent sources
would let a correlated pair systematically outvote the one genuinely independent observer,
inflating confidence on the basis of the same mistake counted twice.

## Because
The whole point of computing the overlap in this phase was to make that miscount impossible
to make by accident later, in phase 11, once there are five fusion strategies to compare and
it would be easy to reach for "count how many agree" without re-deriving why that undercounts
correlation.

## Ponytail pass
`independent_sources()` is a one-line set comprehension. No separate `Source` enum or
registry was introduced -- `source` is a plain string field on `Evidence`, matching what each
observer's own design doc already calls its input (`"phase04_csv"`, `"phase05_raw_archives"`).
