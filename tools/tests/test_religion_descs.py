"""Tests for the religion and faith descriptions that replace Anbennar's placeholders ("TODO", "test", "idk", empty).

    python -I -m unittest discover -s tools/tests -p "test_religion_descs*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdx_script import ANBENNAR_CK3 as ANBENNAR, _balanced, parse_blocks, strip_comments  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent.parent

DESC_FILE = "localization/replace/english/aov_religion_desc_replace_l_english.yml"
RELIGION_DIR = "common/religion/religion_types"

# Placeholders still waiting for text (e.g. new faiths after an Anbennar update, until their text is written).
AWAITING_TEXT = set()


def _text(path):
    return path.read_bytes().decode("utf-8-sig") if path.is_file() else ""


def loc_values(text):
    return dict(re.findall(r'^\s*([\w.\-]+):\d*\s*"(.*)"\s*(?:#.*)?$', text, re.M))


def religions_and_faiths():
    """Every religion and faith Anbennar defines."""
    keys = set()
    for f in sorted((ANBENNAR / RELIGION_DIR).glob("*.txt")):
        for religion, body in parse_blocks(strip_comments(_text(f))).items():
            keys.add(religion)
            m = re.search(r"\bfaiths\s*=\s*\{", body)
            if m:
                keys |= set(parse_blocks(body[m.end():_balanced(body, m.end() - 1) - 1]))
    return keys


def is_placeholder(value):
    return value is None or len(value.strip()) < 40 or re.search(r"TODO|\bidk\b", value) is not None


class ReligionDescTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = {}
        for f in (ANBENNAR / "localization/english").rglob("*.yml"):
            base.update(loc_values(_text(f)))
        cls.keys = religions_and_faiths()
        cls.placeholders = {k for k in cls.keys if is_placeholder(base.get(f"{k}_desc"))}
        cls.ours = {k.removesuffix("_desc"): v for k, v in loc_values(_text(SUBMOD / DESC_FILE)).items()}

    def test_every_placeholder_replaced_or_awaiting_text(self):
        self.assertEqual(self.placeholders - set(self.ours), AWAITING_TEXT)

    def test_only_placeholders_replaced(self):
        self.assertLessEqual(set(self.ours), self.placeholders)
        self.assertFalse(AWAITING_TEXT & set(self.ours))

    def test_descriptions_are_real_text(self):
        for key, value in self.ours.items():
            self.assertFalse(is_placeholder(value), key)
            self.assertNotRegex(value, r"§|£", key)  # EU4 colour and icon codes


if __name__ == "__main__":
    unittest.main()
