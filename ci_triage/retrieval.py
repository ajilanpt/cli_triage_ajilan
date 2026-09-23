"""Observer 3 -- retrieval (design/09-retrieval-observer.md).

No training: embed a failure's exception/stack-trace text, look up the most
similar past failures in a two-class index, vote. Reuses phase 05's gate
(ci_triage/infra.py) for both the TRUSTED filter and the flaky/not-flaky
split (decisions/09-index-contents.md).
"""

import re

from ci_triage.infra import DETERMINISTIC_THRESHOLD, parse_run_log
from ci_triage.sequences import _deterministic_from_logs, read_all_run_logs

# per-method failure detail block in the per-class test output (richer than
# the terse one-line entries in the final "Results :" summary): a header
# line, then the exception message and indented stack trace, until the next
# header or the Results block.
FAILURE_HEADER_RE = re.compile(
    r"^(?P<method>\w+)\((?P<cls>[\w.$]+)\)\s+Time elapsed:[^\n]*<<<\s*(?:FAILURE|ERROR)!\s*$",
    re.MULTILINE,
)

TOP_K = 5
MAX_DOCS_PER_TEST = 5


def _failure_details(log_text):
    """Yields (test_name, detail_text) for each per-method failure in this
    log's per-class output section. test_name uses the short class name
    (last dotted component) -- this per-method header is fully qualified
    (e.g. "com.squareup.okhttp...HttpOverSpdy3Test"), but the Results-block
    summary this project's deterministic-test set is built from only ever
    uses the short name (e.g. "HttpOverSpdy3Test"); without normalizing,
    the two never match and every deterministic test's failures were
    silently mislabeled "flaky"."""
    matches = list(FAILURE_HEADER_RE.finditer(log_text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(log_text)
        detail = log_text[start:end].strip()
        results_idx = detail.find("\nResults")
        if results_idx != -1:
            detail = detail[:results_idx].strip()
        if detail:
            short_cls = m.group("cls").rsplit(".", 1)[-1]
            yield f"{short_cls}#{m.group('method')}", detail


def build_project_documents(project_name, logs, max_docs_per_test=MAX_DOCS_PER_TEST):
    """One document per (test, TRUSTED-or-MASS_FAILURE run, failure detail),
    labeled per decisions/09-index-contents.md, capped at max_docs_per_test
    occurrences per test -- a deterministic test can fail with a near-
    identical message in thousands of runs, and embedding every copy adds
    no diversity, only cost. `doc_id` lets a query exclude the document
    sourced from its own occurrence."""
    deterministic_tests = _deterministic_from_logs(logs, threshold=DETERMINISTIC_THRESHOLD)
    documents = []
    per_test_count = {}

    for run_idx, text in enumerate(logs):
        verdict_result = parse_run_log(text, deterministic_tests=deterministic_tests)
        verdict = verdict_result["verdict"]
        if verdict not in ("TRUSTED", "MASS_FAILURE"):
            continue

        for test_name, detail in _failure_details(text):
            if per_test_count.get(test_name, 0) >= max_docs_per_test:
                continue

            if verdict == "MASS_FAILURE":
                label = "not-flaky"  # infra-caused, per decisions/09
            elif test_name in deterministic_tests:
                label = "not-flaky"  # permanently broken, not intermittent
            else:
                label = "flaky"

            documents.append(
                {
                    "doc_id": f"{project_name}:{run_idx}:{test_name}",
                    "project": project_name,
                    "run_idx": run_idx,
                    "test": test_name,
                    "label": label,
                    "text": detail,
                }
            )
            per_test_count[test_name] = per_test_count.get(test_name, 0) + 1

    return documents


def build_corpus(project_paths):
    """project_paths: {project_name: tgz_path}. Returns {project_name: [documents]}."""
    corpus = {}
    for name, path in project_paths.items():
        logs = read_all_run_logs(path)
        corpus[name] = build_project_documents(name, logs)
    return corpus


_MODEL = None


def _embedder():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def embed(texts):
    return _embedder().encode(texts, show_progress_bar=False, convert_to_numpy=True)


def vote(labels, positive_label="flaky"):
    """Majority vote over a list of neighbour labels."""
    return 1 if labels.count(positive_label) > len(labels) / 2 else 0


def has_both_classes(documents, min_per_class):
    counts = {}
    for d in documents:
        counts[d["label"]] = counts.get(d["label"], 0) + 1
    return counts.get("flaky", 0) >= min_per_class and counts.get("not-flaky", 0) >= min_per_class


def evaluate_index(index_documents, index_vectors, query_documents, query_vectors, k=TOP_K, exclude_self=False):
    """Query each (document, vector) in query_documents/query_vectors against
    index_documents/index_vectors, top-k, majority vote. If exclude_self,
    a query never retrieves a document with the same doc_id (design/09,
    Constraint) -- used for within-project leave-one-out."""
    from sklearn.neighbors import NearestNeighbors

    n_neighbors = k + 1 if exclude_self else k
    n_neighbors = min(n_neighbors, len(index_documents))
    nn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine").fit(index_vectors)
    _, neighbor_idx = nn.kneighbors(query_vectors)

    correct = 0
    scored = 0
    distinct_test_counts = []
    for i, q_doc in enumerate(query_documents):
        candidates = [j for j in neighbor_idx[i] if not (exclude_self and index_documents[j]["doc_id"] == q_doc["doc_id"])]
        candidates = candidates[:k]
        if not candidates:
            continue
        neighbor_labels = [index_documents[j]["label"] for j in candidates]
        neighbor_tests = {index_documents[j]["test"] for j in candidates}
        predicted = vote(neighbor_labels)
        true = 1 if q_doc["label"] == "flaky" else 0
        correct += int(predicted == true)
        scored += 1
        distinct_test_counts.append(len(neighbor_tests))

    if scored == 0:
        return None
    return {
        "precision_at_k": correct / scored,
        "n_scored": scored,
        "k": k,
        "mean_distinct_tests_among_neighbors": sum(distinct_test_counts) / len(distinct_test_counts),
    }


def majority_baseline(documents):
    positive = sum(1 for d in documents if d["label"] == "flaky")
    return max(positive, len(documents) - positive) / len(documents)
