"""Tests for the religion text that replaces Anbennar's blank and placeholder keys (terminology, tenets, doctrines, patrons).

    python -I -m unittest discover -s tools/tests -p "test_religion_text*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdx_script import ANBENNAR_CK3 as ANBENNAR  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent.parent

TEXT_FILE = "localization/replace/english/aov_religion_text_replace_l_english.yml"

# Keys Anbennar's religion files reference but never define.
NEW_KEYS = {"halessi_high_god_name_alternate", "halessi_high_god_name_alternate_possessive",
            "raheni_high_god_name_alternate", "raheni_high_god_name_alternate_possessive"}


def _text(path):
    return path.read_bytes().decode("utf-8-sig") if path.is_file() else ""


def loc_values(text):
    return dict(re.findall(r'^\s*([\w.\-]+):\d*\s*"(.*)"\s*(?:#.*)?$', text, re.M))


class ReligionTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = {}
        for f in (ANBENNAR / "localization/english").rglob("*.yml"):
            cls.base.update(loc_values(_text(f)))
        cls.ours = loc_values(_text(SUBMOD / TEXT_FILE))

    def test_values_are_real_text(self):
        for key, value in self.ours.items():
            self.assertTrue(value.strip(), key)
            self.assertNotRegex(value, r"TODO|LOREM|\bidk\b|\(WIP\)", key)

    def test_only_blank_or_placeholder_keys_replaced(self):
        for key in set(self.ours) - NEW_KEYS:
            old = self.base.get(key)
            self.assertIsNotNone(old, key)
            self.assertTrue(old.strip() == "" or re.search(r"TODO|LOREM", old), f"{key}: {old!r}")

    def test_patron_descriptions_all_filled(self):
        blank = [k for k, v in self.base.items() if re.fullmatch(r"(anb_\w+_)?patron_\w+_modifier_desc", k) and not v.strip()]
        self.assertEqual([k for k in blank if k not in self.ours], [])


if __name__ == "__main__":
    unittest.main()
