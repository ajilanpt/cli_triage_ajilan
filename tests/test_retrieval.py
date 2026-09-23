import numpy as np

from ci_triage.retrieval import evaluate_index, has_both_classes, majority_baseline, vote


def _doc(doc_id, label, test="pkg.T#m"):
    return {"doc_id": doc_id, "project": "p", "run_idx": 0, "test": test, "label": label}


def test_vote_is_majority_of_neighbor_labels():
    assert vote(["flaky", "flaky", "not-flaky"]) == 1
    assert vote(["not-flaky", "not-flaky", "flaky"]) == 0


def test_query_cannot_retrieve_a_document_with_its_own_doc_id():
    # a query's own document sits in the index with an identical vector --
    # exclude_self must ensure it never contributes to that query's vote
    index_docs = [
        _doc("q1", "flaky"),  # the query's own document, deliberately closest
        _doc("d2", "not-flaky"),
        _doc("d3", "not-flaky"),
        _doc("d4", "not-flaky"),
    ]
    index_vectors = np.array(
        [
            [1.0, 0.0],  # identical to the query vector below
            [0.0, 1.0],
            [0.0, 0.9],
            [0.0, 1.1],
        ]
    )
    query_docs = [_doc("q1", "flaky")]
    query_vectors = np.array([[1.0, 0.0]])

    result = evaluate_index(
        index_docs, index_vectors, query_docs, query_vectors, k=3, exclude_self=True
    )
    # without self-exclusion this would trivially match itself as the top hit
    # (a "flaky" query, majority-voted "not-flaky" by its real neighbours) --
    # predicted 0 vs true 1 makes the leak visible as a wrong answer, not a
    # silently perfect one
    assert result["precision_at_k"] == 0.0


def test_index_with_only_one_class_is_refused_not_silently_scored():
    one_class_index = [_doc(f"d{i}", "flaky") for i in range(10)]
    assert has_both_classes(one_class_index, min_per_class=1) is False

    two_class_index = one_class_index + [_doc("n1", "not-flaky")]
    assert has_both_classes(two_class_index, min_per_class=1) is True


def test_majority_baseline_matches_the_larger_class_fraction():
    docs = [_doc(f"d{i}", "flaky") for i in range(3)] + [
        _doc(f"n{i}", "not-flaky") for i in range(7)
    ]
    assert majority_baseline(docs) == 0.7


def test_distinct_test_count_can_be_less_than_k():
    # five neighbours that are all the same test are one opinion, not five
    index_docs = [_doc(f"d{i}", "flaky", test="pkg.T#same") for i in range(5)]
    index_vectors = np.array([[0.0, 1.0]] * 5)
    query_docs = [_doc("q1", "flaky", test="pkg.T#other")]
    query_vectors = np.array([[0.0, 1.0]])

    result = evaluate_index(index_docs, index_vectors, query_docs, query_vectors, k=5)
    assert result["mean_distinct_tests_among_neighbors"] == 1.0
