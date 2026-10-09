"""Mod-wide checks for script mistakes the engine only reports at runtime.

    python -I -m unittest discover -s tools/tests -v
"""

import re
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent


class ChangeVariableTests(unittest.TestCase):
    def test_changed_variables_are_created_first(self):
        """change_variable on a variable that does not exist is a runtime error that does nothing ('Variable not
        of the value scope type'): school progress and election votes never grew because of it. Every changed
        variable is created in the same file (a has_variable guard or a set_variable)."""
        missing = []
        for root in ("common", "events"):
            for path in sorted((MOD / root).rglob("*.txt")):
                text = path.read_text(encoding="utf-8-sig")
                for name in sorted(set(re.findall(r"change_(?:global_)?variable = \{ name = (\S+)", text))):
                    created = (f"has_variable = {name}" in text or f"has_global_variable = {name}" in text
                               or re.search(rf"set_(?:global_)?variable = \{{ name = {re.escape(name)}\b", text))
                    if not created:
                        missing.append(f"{path.relative_to(MOD).as_posix()}: {name}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
