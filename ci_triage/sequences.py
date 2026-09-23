"""Observer 2 -- sequence (design/08-sequence-observer.md).

Prefix predicts suffix: given the first k TRUSTED reruns of a test, predict
whether it flips (both passes and fails) again within a later, non-
overlapping window. Reuses phase 05's gate (ci_triage/infra.py) directly --
no separate XML parsing subsystem.
"""

import io
import re
import tarfile
from collections import Counter

from ci_triage.infra import _failing_test_names_in_block, _results_blocks, parse_run_log

FINISHED_AT_RE = re.compile(r"Finished at:\s*([0-9T:.\-Z]+)")
DETERMINISTIC_THRESHOLD = 0.80
PREFIX_LENGTHS = (5, 10)
SUFFIX_LENGTH = 20


def _finished_at(log_text, fallback_order):
    m = FINISHED_AT_RE.search(log_text)
    return m.group(1) if m else f"~{fallback_order:08d}"  # stable fallback, sorts after real timestamps


def _raw_failing_names(text):
    names = set()
    for block in _results_blocks(text):
        names.update(_failing_test_names_in_block(block["body"]))
    return names


def read_all_run_logs(project_tgz_path):
    """One sequential pass over the project archive, all maven.log text held
    in memory -- reopening/reseeking the same big archive multiple times was
    measured to be extremely slow (phase 05); read once, reuse in memory."""
    logs = []
    with tarfile.open(project_tgz_path) as outer:
        run_members = [m for m in outer.getmembers() if m.name.endswith(".tgz")]
        for m in run_members:
            data = outer.extractfile(m).read()
            with tarfile.open(fileobj=io.BytesIO(data)) as inner:
                log_member = next(
                    (im for im in inner.getmembers() if im.name.endswith("maven.log")), None
                )
                if log_member is not None:
                    logs.append(inner.extractfile(log_member).read().decode("utf-8", errors="replace"))
    return logs


def _deterministic_from_logs(logs, threshold=DETERMINISTIC_THRESHOLD):
    fail_counts = Counter()
    for text in logs:
        fail_counts.update(_raw_failing_names(text))
    run_count = len(logs)
    if run_count == 0:
        return set()
    return {t for t, n in fail_counts.items() if n / run_count >= threshold}


def project_test_sequences(logs):
    """Returns {test_name: [(timestamp, failed: 0/1), ...]} in run order, for
    tests that ever showed variability in this project (deterministic or
    non-deterministic failing tests -- an always-passing test can never
    satisfy the flip label and carries no sequence information), using only
    TRUSTED runs (design/08, Reads). `logs` is a list of maven.log text,
    from `read_all_run_logs`."""
    deterministic_tests = _deterministic_from_logs(logs)

    target_tests = set(deterministic_tests)
    raw_events = []  # (timestamp, {failing test names in this TRUSTED run})

    for order, text in enumerate(logs):
        verdict_result = parse_run_log(text, deterministic_tests=deterministic_tests)
        if verdict_result["verdict"] != "TRUSTED":
            continue
        raw_result = parse_run_log(text, deterministic_tests=set())
        target_tests.update(raw_result["failing_tests"])
        raw_events.append((_finished_at(text, order), raw_result["failing_tests"]))

    raw_events.sort(key=lambda e: e[0])

    sequences = {t: [] for t in target_tests}
    for timestamp, failing in raw_events:
        for t in target_tests:
            sequences[t].append((timestamp, 1 if t in failing else 0))

    return sequences


def _to_tensor(prefix):
    import torch

    return torch.tensor(prefix, dtype=torch.float32).unsqueeze(-1)  # (seq_len, 1)


class SequenceGRU:
    """Thin wrapper around a 1-layer GRU + sigmoid head. batch_size=1 forward
    passes, looped -- the dataset here is small (hundreds of examples), so
    simplicity wins over batching (ponytail)."""

    def __init__(self, hidden_size=8, seed=42):
        import torch
        import torch.nn as nn

        torch.manual_seed(seed)

        class _Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.gru = nn.GRU(input_size=1, hidden_size=hidden_size, batch_first=True)
                self.out = nn.Linear(hidden_size, 1)

            def forward(self, x):
                _, h = self.gru(x)
                return self.out(h[-1]).squeeze(-1)

        self.net = _Net()

    def fit(self, examples, epochs=150, lr=0.01):
        import torch

        optimizer = torch.optim.Adam(self.net.parameters(), lr=lr)
        loss_fn = torch.nn.BCEWithLogitsLoss()
        self.net.train()
        for _ in range(epochs):
            optimizer.zero_grad()
            for ex in examples:
                x = _to_tensor(ex["prefix"]).unsqueeze(0)
                y = torch.tensor([float(ex["label"])])
                loss = loss_fn(self.net(x), y)
                loss.backward()
            optimizer.step()
        return self

    def predict_proba(self, examples):
        import torch

        self.net.eval()
        scores = []
        with torch.no_grad():
            for ex in examples:
                x = _to_tensor(ex["prefix"]).unsqueeze(0)
                scores.append(torch.sigmoid(self.net(x)).item())
        return scores


def build_examples(sequences, prefix_lengths=PREFIX_LENGTHS, suffix_length=SUFFIX_LENGTH):
    """One example per (test, prefix length) with enough TRUSTED history --
    prefix and suffix never share a run (design/08, Constraint)."""
    examples = []
    for test_name, events in sequences.items():
        outcomes = [failed for _, failed in events]
        for k in prefix_lengths:
            if len(outcomes) < k + suffix_length:
                continue
            prefix = outcomes[:k]
            suffix = outcomes[k : k + suffix_length]
            label = 1 if (0 in suffix and 1 in suffix) else 0
            examples.append(
                {
                    "test": test_name,
                    "prefix_length": k,
                    "prefix": prefix,
                    "control_score": sum(prefix),
                    "label": label,
                }
            )
    return examples
