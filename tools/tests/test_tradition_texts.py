"""Tests for the cultural tradition names and descriptions that replace Anbennar's placeholders ("<Unit> Test MAA",
"<Unit> Test MAA Desc", "TODO").

    python -I -m unittest discover -s tools/tests -p "test_tradition_texts*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdx_script import ANBENNAR_CK3 as ANBENNAR, parse_blocks, strip_comments  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent.parent

GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")  # vanilla traditions' text
TEXT_FILE = "localization/replace/english/aov_tradition_text_replace_l_english.yml"
TRADITION_DIR = "common/culture/traditions"

# Placeholders still waiting for text (e.g. new traditions after an Anbennar update, until their text is written).
AWAITING_TEXT = set()


def _text(path):
    return path.read_bytes().decode("utf-8-sig") if path.is_file() else ""


def loc_values(text):
    return dict(re.findall(r'^\s*([\w.\-]+):\d*\s*"(.*)"\s*(?:#.*)?$', text, re.M))


def traditions(root):
    """Every tradition defined under root's traditions folder, by key."""
    found = {}
    for f in sorted((root / TRADITION_DIR).glob("*.txt")):
        found.update(parse_blocks(strip_comments(_text(f))))
    return found


def hidden(body):
    return re.search(r"\bis_shown\s*=\s*\{\s*always\s*=\s*no\s*\}", body) is not None


def is_placeholder(value):
    return value is None or not value.strip() or re.search(r"Test MAA|TODO|\(WIP\)", value) is not None


class TraditionTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = {}
        for root in (GAME, ANBENNAR, SUBMOD):  # later wins; the overhaul's own traditions have their text there
            for f in (root / "localization/english").rglob("*.yml"):
                base.update(loc_values(_text(f)))
        defined = traditions(ANBENNAR)
        defined.update(traditions(SUBMOD))  # the overhaul's zz_ overrides win
        cls.shown = {k for k, body in defined.items() if not hidden(body)}
        cls.placeholders = {f"{k}{suffix}" for k in cls.shown for suffix in ("_name", "_desc")
                            if is_placeholder(base.get(f"{k}{suffix}"))}
        cls.ours = loc_values(_text(SUBMOD / TEXT_FILE))

    def test_every_placeholder_replaced_or_awaiting_text(self):
        self.assertEqual(self.placeholders - set(self.ours), AWAITING_TEXT)

    def test_only_placeholders_replaced(self):
        self.assertLessEqual(set(self.ours), self.placeholders)
        self.assertFalse(AWAITING_TEXT & set(self.ours))

    def test_texts_are_real(self):
        for key, value in self.ours.items():
            self.assertFalse(is_placeholder(value), key)
            self.assertGreaterEqual(len(value), 100 if key.endswith("_desc") else 5, key)
            self.assertNotRegex(value, r"§|£", key)  # EU4 colour and icon codes


if __name__ == "__main__":
    unittest.main()
