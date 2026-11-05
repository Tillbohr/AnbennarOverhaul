"""Tests for tools/run_tests.py.

    python -I -m unittest discover -s tools/tests -p test_run_tests.py
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import run_tests as rt  # noqa: E402

PASSING = """import unittest
class T(unittest.TestCase):
    def test_a(self):
        print("noise from a passing test")
    def test_b(self):
        self.skipTest("no data")
"""
FAILING = """import unittest
class T(unittest.TestCase):
    def test_c(self):
        self.assertEqual(1, 2, "the reason this failed")
"""


class ParseTests(unittest.TestCase):
    def test_passing_module(self):
        o = rt.parse("m", 1.0, 0, "....\n----\nRan 4 tests in 0.1s\n\nOK (skipped=1)")
        self.assertEqual((o.tests, o.failures, o.errors, o.skipped, o.passed), (4, 0, 0, 1, True))

    def test_failing_module(self):
        o = rt.parse("m", 1.0, 1, "F\n----\nRan 9 tests in 0.1s\n\nFAILED (failures=2, errors=3, skipped=1)")
        self.assertEqual((o.tests, o.failures, o.errors, o.skipped, o.passed), (9, 2, 3, 1, False))

    def test_crash_before_the_summary_fails(self):
        self.assertFalse(rt.parse("m", 1.0, 0, "").passed)
        self.assertFalse(rt.parse("m", 1.0, 3221225477, "Ran 1 test in 0.1s\n\nOK").passed)

    def test_module_without_tests_passes(self):
        o = rt.parse("m", 1.0, rt.NO_TESTS_RAN, "----\nRan 0 tests in 0.0s\n\nNO TESTS RAN")
        self.assertEqual((o.tests, o.passed), (0, True))


class MainTests(unittest.TestCase):
    def run_main(self, folder: Path, *args) -> tuple:
        out = io.StringIO()
        with mock.patch.object(rt, "TESTS", folder), contextlib.redirect_stdout(out):
            code = rt.main(list(args))
        return code, out.getvalue()

    def test_passing_run_is_quiet_and_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "test_one.py").write_text(PASSING)
            code, out = self.run_main(Path(tmp))
        self.assertEqual(code, 0)
        self.assertIn("Ran 2 tests from 1 modules", out)
        self.assertIn("skipped=1", out)
        self.assertNotIn("noise", out)

    def test_failure_is_printed_in_full(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "test_one.py").write_text(PASSING)
            (Path(tmp) / "test_two.py").write_text(FAILING)
            code, out = self.run_main(Path(tmp), "-j", "2")
        self.assertEqual(code, 1)
        self.assertIn("the reason this failed", out)
        self.assertIn("Ran 3 tests from 2 modules", out)
        self.assertIn("FAILED in test_two", out)

    def test_names_select_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "test_one.py").write_text(PASSING)
            (Path(tmp) / "test_two.py").write_text(FAILING)
            code, out = self.run_main(Path(tmp), "one")
        self.assertEqual(code, 0)
        self.assertIn("from 1 modules", out)

    def test_no_match_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()):
            code, _ = self.run_main(Path(tmp), "nothing")
        self.assertEqual(code, 2)


class TraceCacheTests(unittest.TestCase):
    def test_only_modules_sharing_the_trace_fill_the_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            plain, user = Path(tmp) / "test_plain.py", Path(tmp) / "test_user.py"
            plain.write_text("import unittest\n")
            user.write_text("import shared_trace\n")
            with mock.patch.object(rt.subprocess, "run") as run:
                rt.fill_trace_cache([plain])
                run.assert_not_called()
                rt.fill_trace_cache([plain, user])
                run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
