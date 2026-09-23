import dataclasses

import pytest

from ci_triage.contracts import Evidence, independent_sources


def _evidence(**overrides):
    defaults = dict(
        observer="tabular",
        source="phase04_csv",
        case_id="pkg.Test#method",
        probability=0.7,
        calibrated=True,
        n_observations=10,
        cost_usd=0.0,
        latency_ms=5.0,
    )
    defaults.update(overrides)
    return Evidence(**defaults)


def test_calibrated_flag_is_required_not_defaulted():
    # design/10, Refuses: a probability with no explicit calibration state
    # must be impossible to construct, not silently assumed either way
    kwargs = dict(
        observer="tabular",
        source="phase04_csv",
        case_id="pkg.Test#method",
        probability=0.7,
        n_observations=10,
        cost_usd=0.0,
        latency_ms=5.0,
    )
    with pytest.raises(TypeError):
        Evidence(**kwargs)  # missing `calibrated`


def test_no_default_calibration_value_exists_on_the_class():
    field = next(f for f in dataclasses.fields(Evidence) if f.name == "calibrated")
    assert field.default is dataclasses.MISSING
    assert field.default_factory is dataclasses.MISSING


def test_probability_out_of_range_is_rejected():
    with pytest.raises(ValueError):
        _evidence(probability=1.5)
    with pytest.raises(ValueError):
        _evidence(probability=-0.1)


def test_negative_observation_count_is_rejected():
    with pytest.raises(ValueError):
        _evidence(n_observations=-1)


def test_no_evidence_and_evidence_pointing_everywhere_are_distinguishable():
    # both can carry the same probability (0.5) but must not be the same state
    no_evidence = _evidence(probability=0.5, n_observations=0)
    conflicting_evidence = _evidence(probability=0.5, n_observations=50)
    assert no_evidence.n_observations != conflicting_evidence.n_observations


def test_independent_sources_counts_distinct_sources_not_records():
    # two records from the same source are one observation, not two
    # (decisions/10-independence.md, rule 1)
    records = [
        _evidence(observer="sequence", source="phase05_raw_archives"),
        _evidence(observer="retrieval", source="phase05_raw_archives"),
        _evidence(observer="tabular", source="phase04_csv"),
    ]
    assert independent_sources(records) == {"phase05_raw_archives", "phase04_csv"}
    assert len(independent_sources(records)) == 2  # not 3, despite 3 records
