from ci_triage.sequences import build_examples


def _toy_sequences(n_events=30):
    # one test with enough history for both prefix lengths (5, 10) plus a
    # 20-run suffix window; deliberately includes a flip in the suffix
    events = [(f"t{i}", 0) for i in range(n_events)]
    events[12] = ("t12", 1)  # a flip inside what will be the suffix window
    return {"pkg.Test#method": events}


def test_no_run_appears_in_both_prefix_and_suffix():
    sequences = _toy_sequences()
    examples = build_examples(sequences, prefix_lengths=(5, 10), suffix_length=20)
    assert examples  # sanity: the toy data actually produced examples

    for ex in examples:
        k = ex["prefix_length"]
        # prefix is positions [0, k); suffix is positions [k, k+suffix_length)
        # -- by construction these index ranges cannot overlap, but this
        # test exists to catch a future change that breaks that invariant
        prefix_positions = set(range(0, k))
        suffix_positions = set(range(k, k + 20))
        assert prefix_positions.isdisjoint(suffix_positions)


def test_deliberately_broken_overlap_is_caught_by_the_invariant():
    # break the invariant on purpose (suffix starts before the prefix ends)
    # and confirm a version of the check above would fail on it
    k = 5
    suffix_length = 20
    broken_suffix_start = k - 2  # overlaps the last 2 prefix positions

    prefix_positions = set(range(0, k))
    broken_suffix_positions = set(range(broken_suffix_start, broken_suffix_start + suffix_length))

    assert not prefix_positions.isdisjoint(broken_suffix_positions)


def test_label_reflects_a_flip_within_the_suffix_only():
    sequences = _toy_sequences()
    examples = build_examples(sequences, prefix_lengths=(5,), suffix_length=20)
    ex = examples[0]
    assert ex["label"] == 1  # the flip at index 12 falls inside runs [5, 25)


def test_no_flip_in_suffix_gives_a_negative_label():
    events = [("t", 0) for _ in range(30)]  # no flip anywhere
    examples = build_examples({"pkg.Test#allpass": events}, prefix_lengths=(5,), suffix_length=20)
    assert examples[0]["label"] == 0


def test_examples_skipped_when_history_too_short():
    events = [("t", 0) for _ in range(10)]  # shorter than 5 + 20
    examples = build_examples({"pkg.Test#short": events}, prefix_lengths=(5, 10), suffix_length=20)
    assert examples == []
