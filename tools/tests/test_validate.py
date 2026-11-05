"""Tests for tools/validate.py.

    python -I -m unittest discover -s tools/tests -p test_validate.py
"""

import io
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import validate  # noqa: E402

REPORT = "warning: Dûr-Vazhatun → 漢 \U0001f600 not in cp1252"


class RedirectedOutputTests(unittest.TestCase):
    def run_main(self, tiger_output: str, code: int = 0, args=("--all",)) -> tuple:
        """(exit code, bytes written) of main() with stdout redirected the way Windows Python sets it up."""
        raw = io.BytesIO()
        stdout = io.TextIOWrapper(raw, encoding="cp1252", newline="")
        done = subprocess.CompletedProcess([], code, stdout=tiger_output)
        with mock.patch.object(validate, "TIGER", Path(sys.executable)), \
                mock.patch.object(validate.subprocess, "run", return_value=done), \
                mock.patch.object(sys, "argv", ["validate.py", *args]), \
                mock.patch.object(sys, "stdout", stdout), \
                self.assertRaises(SystemExit) as stop:
            validate.main()
        stdout.flush()
        return stop.exception.code, raw.getvalue()

    def test_report_outside_the_console_code_page_is_written_whole(self):
        code, written = self.run_main(REPORT)
        self.assertEqual(code, 0)
        self.assertEqual(written.decode("utf-8").strip(), REPORT)

    def test_new_reports_mode_too(self):
        _, written = self.run_main(REPORT, args=())
        self.assertEqual(written.decode("utf-8").strip(), REPORT)

    def test_tiger_exit_code_is_kept(self):
        code, _ = self.run_main(REPORT, code=3)
        self.assertEqual(code, 3)

    def test_no_reports(self):
        _, written = self.run_main("  \n", args=())
        self.assertEqual(written.decode("utf-8").strip(), "ck3-tiger: no new reports")


if __name__ == "__main__":
    unittest.main()
