"""Trust gate (design/05-infra-gate.md).

Reads a run's maven.log (and its surefire reports) and returns a verdict plus
a reason. Runs upstream of every split and every observer -- a poisoned run
must never contribute evidence.
"""

import re
import tarfile
from collections import Counter

MASS_FAILURE_THRESHOLD = 0.30
DETERMINISTIC_THRESHOLD = 0.80

# each test class prints its own "Tests run: N ... Time elapsed: Xs" line, then
# every module prints one final "Results :" block ending in "Tests run: N ..."
# that is already the per-module total, with any failing/erroring tests listed
# in between as "methodName(ClassName): message". Only the block totals should
# be summed across modules, or a multi-module build's total gets counted twice.
RESULTS_BLOCK_RE = re.compile(
    r"Results\s*:(?P<body>.*?)Tests run:\s*(?P<total>\d+),\s*Failures:\s*(?P<failures>\d+),"
    r"\s*Errors:\s*(?P<errors>\d+),\s*Skipped:\s*(?P<skipped>\d+)",
    re.DOTALL,
)
FAILED_TEST_IN_BLOCK_RE = re.compile(r"(\w+)\(([\w.$]+)\):")


def _results_blocks(log_text):
    return [m.groupdict() for m in RESULTS_BLOCK_RE.finditer(log_text)]


def _failing_tests_in_blocks(blocks):
    failing_tests = set()
    for block in blocks:
        for method, cls in FAILED_TEST_IN_BLOCK_RE.findall(block["body"]):
            failing_tests.add(f"{cls}#{method}")
    return failing_tests


def parse_run_log(log_text, deterministic_tests=frozenset()):
    """Returns a dict: verdict, reason, total, failed (after excluding
    deterministic_tests from both), and failing_tests (set of "Class#method").
    This is the one function that assigns a verdict -- see design/05,
    Constraint: fixed precedence, never reordered."""
    has_success = "BUILD SUCCESS" in log_text
    has_failure_marker = "BUILD FAILURE" in log_text
    summaries = _results_blocks(log_text)
    has_test_summary = len(summaries) > 0

    if not has_test_summary and has_failure_marker:
        return {
            "verdict": "BUILD_FAILED",
            "reason": "no Tests run: summary found, and the log ends in BUILD FAILURE",
            "total": 0,
            "failed": 0,
            "failing_tests": set(),
        }

    if not has_success and not has_failure_marker:
        return {
            "verdict": "LOG_TRUNCATED",
            "reason": "neither BUILD SUCCESS nor BUILD FAILURE appears in the log",
            "total": 0,
            "failed": 0,
            "failing_tests": set(),
        }

    if not has_test_summary:
        return {
            "verdict": "UNKNOWN",
            "reason": "a terminal build marker is present but no Tests run: summary exists",
            "total": 0,
            "failed": 0,
            "failing_tests": set(),
        }

    # sum every module's Results block, not just the last one (multi-module build)
    total = sum(int(m["total"]) for m in summaries)
    failing_tests = _failing_tests_in_blocks(summaries)
    scored_failing_tests = failing_tests - deterministic_tests
    # a deterministic test that failed here is removed from the denominator too,
    # since its outcome is excluded from the fraction entirely, not just the count
    total_scored = total - len(deterministic_tests & failing_tests)
    failed = len(scored_failing_tests)

    if total_scored and failed / total_scored >= MASS_FAILURE_THRESHOLD:
        return {
            "verdict": "MASS_FAILURE",
            "reason": f"{failed}/{total_scored} tests failed ({failed/total_scored:.0%}), "
            f">= {MASS_FAILURE_THRESHOLD:.0%} threshold, after excluding deterministic tests",
            "total": total_scored,
            "failed": failed,
            "failing_tests": scored_failing_tests,
        }

    return {
        "verdict": "TRUSTED",
        "reason": f"{failed}/{total_scored} tests failed, below the "
        f"{MASS_FAILURE_THRESHOLD:.0%} mass-failure threshold",
        "total": total_scored,
        "failed": failed,
        "failing_tests": scored_failing_tests,
    }


def read_run_archive(run_tar_path):
    """Extract maven.log text from one run .tgz. Returns None if absent."""
    with tarfile.open(run_tar_path) as tf:
        for member in tf.getmembers():
            if member.name.endswith("maven.log"):
                f = tf.extractfile(member)
                if f is not None:
                    return f.read().decode("utf-8", errors="replace")
    return None


def _iter_run_logs(project_tgz_path):
    """Yields each run's maven.log text from a project archive."""
    with tarfile.open(project_tgz_path) as outer:
        run_members = [m for m in outer.getmembers() if m.name.endswith(".tgz")]
        for member in run_members:
            f = outer.extractfile(member)
            if f is None:
                continue
            with tarfile.open(fileobj=f) as inner:
                log_member = next(
                    (m for m in inner.getmembers() if m.name.endswith("maven.log")), None
                )
                if log_member is None:
                    continue
                yield inner.extractfile(log_member).read().decode("utf-8", errors="replace")


def find_deterministic_tests(project_tgz_path):
    """First pass over every run in a project archive: which tests fail in
    >= DETERMINISTIC_THRESHOLD of runs. Returned set is excluded from the
    mass-failure fraction on the second pass (design/05, Emits)."""
    fail_counts = Counter()
    run_count = 0
    for text in _iter_run_logs(project_tgz_path):
        run_count += 1
        for t in _failing_tests_in_blocks(_results_blocks(text)):
            fail_counts[t] += 1
    if run_count == 0:
        return set()
    return {t for t, n in fail_counts.items() if n / run_count >= DETERMINISTIC_THRESHOLD}


def scan_project(project_tgz_path):
    """Second pass: verdict every run in a project archive. Returns the
    report written to artifacts/results/infra.json."""
    deterministic_tests = find_deterministic_tests(project_tgz_path)
    verdict_counts = Counter()
    all_failing = set()
    trusted_failing = set()

    for text in _iter_run_logs(project_tgz_path):
        result = parse_run_log(text, deterministic_tests=deterministic_tests)
        verdict_counts[result["verdict"]] += 1
        all_failing |= result["failing_tests"]
        if result["verdict"] == "TRUSTED":
            trusted_failing |= result["failing_tests"]

    return {
        "verdict_counts": dict(verdict_counts),
        "distinct_failing_tests_all_runs": len(all_failing),
        "distinct_failing_tests_trusted_runs": len(trusted_failing),
        "deterministic_tests": sorted(deterministic_tests),
    }
