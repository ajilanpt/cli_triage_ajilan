"""Integration contract (design/10-architecture-independence.md).

The one record every observer writes to. Ponytail: a dataclass, not a
framework, not a registry -- fusion (phase 11) reads only this shape, never
an observer's internals.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    """One observer's opinion about one case (a single test), never a whole
    run -- the case-level/run-level distinction from design/10 must not be
    collapsed here; aggregating many of these into a release decision is a
    later slice's job (phase 11), not this record's.

    n_observations distinguishes "no evidence" from "evidence pointing in
    every direction": a probability of 0.5 with n_observations=0 means the
    observer has nothing and this is a placeholder/prior, while 0.5 with
    n_observations=50 means it genuinely saw conflicting signal across 50
    real observations. A bare probability cannot tell those apart
    (design/10, Emits).
    """

    observer: str  # which component produced this, e.g. "tabular", "sequence", "retrieval"
    source: str  # the underlying data source read, e.g. "phase04_csv", "phase05_raw_archives"
    case_id: str  # the test this evidence is about, e.g. "ClassName#method"
    probability: float  # P(flaky), in [0, 1]
    calibrated: bool  # no default: an observer must state this explicitly
    n_observations: int  # how much evidence backs `probability`; 0 = no evidence at all
    cost_usd: float
    latency_ms: float

    def __post_init__(self):
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError(f"probability must be in [0, 1], got {self.probability}")
        if self.n_observations < 0:
            raise ValueError(f"n_observations must be >= 0, got {self.n_observations}")


def independent_sources(evidence_records):
    """Given a list of Evidence, returns the set of distinct `source` values
    represented -- the number of genuinely independent pieces of evidence
    is len(this set), not len(evidence_records) (decisions/10-independence.md,
    rule 1). Two records with the same source are one observation, not two,
    regardless of how many observers produced them."""
    return {e.source for e in evidence_records}
