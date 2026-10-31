"""Tests for the trait text that replaces Anbennar's placeholders (Sun Reborn and Jaher's descendants).

    python -I -m unittest discover -s tools/tests -p "test_trait_text*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from test_religion_text import ANBENNAR, SUBMOD, _text, loc_values  # noqa: E402

TEXT_FILE = "localization/replace/english/aov_trait_text_replace_l_english.yml"
# Keys replaced although Anbennar's text is not a placeholder: the descendants' name, which repeats "Sun Reborn".
RENAMED = {"trait_sun_reborn_descendant": "Sun Reborn"}


class TraitTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = {}
        for f in (ANBENNAR / "localization/english").rglob("*.yml"):
            cls.base.update(loc_values(_text(f)))
        cls.ours = loc_values(_text(SUBMOD / TEXT_FILE))

    def test_values_are_real_text(self):
        for key, value in self.ours.items():
            self.assertTrue(value.strip(), key)
            self.assertNotRegex(value, r"TODO|GILLY", key)

    def test_only_placeholders_and_the_rename_replaced(self):
        for key in self.ours:
            old = self.base.get(key)
            self.assertIsNotNone(old, key)
            self.assertTrue(re.search(r"GILLY TODO", old) or RENAMED.get(key) == old, f"{key}: {old!r}")

    def test_no_sun_reborn_placeholder_left(self):
        left = [k for k, v in self.base.items() if "GILLY TODO" in v and ("sun_reborn" in k or "jaher" in k)]
        self.assertEqual([k for k in left if k not in self.ours], [])


if __name__ == "__main__":
    unittest.main()
