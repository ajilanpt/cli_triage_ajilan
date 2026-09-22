from ci_triage.infra import parse_run_log

TRUSTED_LOG = """
Running com.example.FooTest
Tests run: 100, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 1 sec

Results :

Tests run: 100, Failures: 0, Errors: 0, Skipped: 0

[INFO] BUILD SUCCESS
"""

MASS_FAILURE_LOG = """
Running com.example.FooTest
Tests run: 10, Failures: 4, Errors: 0, Skipped: 0, Time elapsed: 1 sec

Results :

Failed tests:   testA(com.example.FooTest): boom
  testB(com.example.FooTest): boom
  testC(com.example.FooTest): boom
  testD(com.example.FooTest): boom

Tests run: 10, Failures: 4, Errors: 0, Skipped: 0

[INFO] BUILD SUCCESS
"""

BUILD_FAILED_LOG = """
[INFO] Compiling 12 source files
[ERROR] COMPILATION ERROR :
[ERROR] cannot find symbol
[INFO] BUILD FAILURE
"""

LOG_TRUNCATED_LOG = """
Running com.example.FooTest
Tests run: 100, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 1 sec
"""

UNKNOWN_LOG = """
[INFO] Nothing much happened
[INFO] BUILD SUCCESS
"""

MULTI_MODULE_LOG = """
Results :

Tests run: 50, Failures: 0, Errors: 0, Skipped: 0

[INFO] Building module-two

Results :

Tests run: 30, Failures: 0, Errors: 0, Skipped: 0

[INFO] BUILD SUCCESS
"""


def test_trusted_verdict_and_reason_match_the_real_counts():
    result = parse_run_log(TRUSTED_LOG)
    assert result["verdict"] == "TRUSTED"
    assert "0/100" in result["reason"]


def test_mass_failure_verdict_and_reason_match_the_real_counts():
    result = parse_run_log(MASS_FAILURE_LOG)
    assert result["verdict"] == "MASS_FAILURE"
    assert "4/10" in result["reason"]
    assert result["failed"] == 4
    assert result["total"] == 10


def test_build_failed_is_not_reported_as_mass_failure():
    # every "test" in a run that never compiled would look 100% failed if
    # miscategorised -- the reason must say build_failed, not mass failure
    result = parse_run_log(BUILD_FAILED_LOG)
    assert result["verdict"] == "BUILD_FAILED"
    assert "mass" not in result["reason"].lower()


def test_log_truncated_when_no_terminal_marker_present():
    result = parse_run_log(LOG_TRUNCATED_LOG)
    assert result["verdict"] == "LOG_TRUNCATED"


def test_unknown_when_success_but_no_test_summary():
    result = parse_run_log(UNKNOWN_LOG)
    assert result["verdict"] == "UNKNOWN"


def test_reason_changes_when_the_underlying_numbers_change():
    # catches a fabricated reason: two different inputs must not produce the
    # same "explanation" for two different verdicts
    trusted = parse_run_log(TRUSTED_LOG)
    mass_failure = parse_run_log(MASS_FAILURE_LOG)
    assert trusted["reason"] != mass_failure["reason"]
    assert trusted["verdict"] != mass_failure["verdict"]


def test_multi_module_results_blocks_are_summed_not_just_the_last_one():
    result = parse_run_log(MULTI_MODULE_LOG)
    assert result["total"] == 80  # 50 + 30, not just the last module's 30


def test_deterministic_tests_are_excluded_from_the_mass_failure_fraction():
    # same log as MASS_FAILURE_LOG, but all 4 failing tests are declared
    # deterministic -- they must not count toward the fraction at all
    deterministic = {
        "com.example.FooTest#testA",
        "com.example.FooTest#testB",
        "com.example.FooTest#testC",
        "com.example.FooTest#testD",
    }
    result = parse_run_log(MASS_FAILURE_LOG, deterministic_tests=deterministic)
    assert result["verdict"] == "TRUSTED"
    assert result["failed"] == 0
    assert result["total"] == 6  # 10 - the 4 excluded deterministic tests


# real format seen in square-okhttp, not kevinsawicki-http-request: no
# parentheses, "Class.method:line", an inherited method as "Run>Declaring",
# and a "->" call-chain continuation on the SAME failing-test entry.
MODERN_FORMAT_LOG = """
Running com.example.BarTest
Tests run: 5, Failures: 1, Errors: 2, Skipped: 0, Time elapsed: 1 sec

Results :

Failed tests:
  BarTest.explode:42 boom

Tests in error:
  BarTest>BaseTest.chained:100->BaseTest.helper:200 NoSuchMethod
  at some.pkg.Helper.run(Helper.java:12)
  BarTest.other:55 NoSuchMethod

Tests run: 5, Failures: 1, Errors: 2, Skipped: 0

[INFO] BUILD SUCCESS
"""

# the format this codebase's regex has no rule for at all
UNRECOGNIZED_FORMAT_LOG = """
Running com.example.BazTest
Tests run: 3, Failures: 2, Errors: 0, Skipped: 0, Time elapsed: 1 sec

Results :

  !! testX and testY blew up, see log above !!

Tests run: 3, Failures: 2, Errors: 0, Skipped: 0

[INFO] BUILD SUCCESS
"""

# the exact shape that broke the old kevinsawicki-only regex on square-okhttp:
# one broken @Before failing several @Test methods, all logged under the
# setUp method's own name -- one distinct name, three failed executions.
REPEATED_NAME_LOG = """
Running com.example.PoolTest
Tests run: 3, Failures: 0, Errors: 3, Skipped: 0, Time elapsed: 1 sec

Results :

Tests in error:
  PoolTest.setUp:10 boom
  PoolTest.setUp:10 boom
  PoolTest.setUp:10 boom

Tests run: 3, Failures: 0, Errors: 3, Skipped: 0

[INFO] BUILD SUCCESS
"""


def test_modern_class_dot_method_format_is_parsed():
    result = parse_run_log(MODERN_FORMAT_LOG)
    assert result["verdict"] == "MASS_FAILURE"
    assert result["failed"] == 3
    assert result["failing_tests"] == {"BarTest#explode", "BarTest#chained", "BarTest#other"}


def test_call_chain_continuation_is_not_double_counted():
    # BaseTest.helper:200 is where BarTest#chained's failure happened to
    # occur, not a second failing test -- must not appear in failing_tests
    result = parse_run_log(MODERN_FORMAT_LOG)
    assert "BaseTest#helper" not in result["failing_tests"]


def test_stack_trace_file_line_is_not_mistaken_for_a_failing_test():
    # "Helper.java:12" fits the same Class.method:line shape as a real entry
    result = parse_run_log(MODERN_FORMAT_LOG)
    assert not any("Helper" in name for name in result["failing_tests"])


def test_unrecognized_failing_test_format_is_unknown_not_silently_zero():
    # the old bug: a name regex that matches nothing still returns a verdict,
    # with a fabricated "0 failed" reason instead of admitting it can't parse
    result = parse_run_log(UNRECOGNIZED_FORMAT_LOG)
    assert result["verdict"] == "UNKNOWN"
    assert result["failed"] == 0
    assert "not recognized" in result["reason"]


def test_repeated_name_counts_each_failed_execution_in_the_fraction():
    result = parse_run_log(REPEATED_NAME_LOG)
    assert result["failed"] == 3  # three failed executions ...
    assert result["failing_tests"] == {"PoolTest#setUp"}  # ... one distinct name
    assert result["verdict"] == "MASS_FAILURE"  # 3/3 = 100%, not 1/3
