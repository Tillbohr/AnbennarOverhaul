"""Tests for tools/data/spells.py and tools/build_spells.py.

    python -I -m unittest discover -s tools/tests -v
"""

import collections
import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
MOD = TOOLS.parent
sys.path.insert(0, str(TOOLS))


def load_data():
    spec = importlib.util.spec_from_file_location("aov_spells_data", TOOLS / "data" / "spells.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SPELLS


SPELLS = load_data()

import build_spells as bs  # noqa: E402
import build_hud_override  # noqa: E402  (brace_delta)


def balanced(text):
    depth = 0
    for line in text.split("\n"):
        depth += build_hud_override.brace_delta(line)
        if depth < 0:
            return False
    return depth == 0


def top_level_blocks(text):
    return re.findall(r"^([A-Za-z0-9_.]+) = \{", text, re.M)


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


class DataTests(unittest.TestCase):
    def test_forty_nine_spells_in_eight_schools(self):
        self.assertEqual(len(SPELLS), 49)
        counts = collections.Counter(s["school"] for s in SPELLS)
        self.assertEqual(set(counts), set(bs.SCHOOLS))
        self.assertEqual(counts["transmutation"], 7)
        self.assertTrue(all(counts[c] == 6 for c in bs.SCHOOLS if c != "transmutation"))

    def test_slots_match_levels(self):
        level_of_slot = {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3}
        for s in SPELLS:
            if s["slot"]:
                self.assertEqual(level_of_slot[s["slot"]], s["level"], s["key"])
        for c in bs.SCHOOLS:
            slots = [s["slot"] for s in SPELLS if s["school"] == c and s["slot"]]
            self.assertEqual(sorted(slots), [1, 2, 3, 4, 5, 6], c)

    def test_existing_anbennar_spells(self):
        by = {s["key"]: s for s in SPELLS}
        self.assertEqual(by["thoughtweave"]["interaction"], "start_compel_interaction")
        self.assertEqual(by["dominate_to_surrender"]["interaction"], "start_dominate_interaction")
        self.assertEqual(by["enhance_ability"]["interaction"], "anb_enhance_ability_interaction")
        self.assertEqual((by["enhance_ability"]["school"], by["enhance_ability"]["level"]), ("transmutation", 1))

    def test_types(self):
        targeted = {s["key"] for s in SPELLS if s["type"] == "targeted"}
        self.assertEqual(targeted, {"ward", "heartstring", "thoughtweave", "dominate_to_surrender", "scry",
                                    "steal_vitality", "contagion", "enhance_ability"})
        for s in SPELLS:
            if s["type"] in ("self", "realm", "war"):
                self.assertTrue(s["modifier"].strip() or s["effect"].strip(), s["key"])


class ValidateTests(unittest.TestCase):
    def test_real_data_valid(self):
        bs.validate(SPELLS)

    def test_rejects_unknown_school(self):
        with self.assertRaises(bs.GeneratorError):
            bs.validate([dict(SPELLS[0], school="evokation")])

    def test_rejects_duplicate(self):
        with self.assertRaises(bs.GeneratorError):
            bs.validate(SPELLS + [dict(SPELLS[0])])


class ArtTests(unittest.TestCase):
    def test_downscale_averages(self):
        px = bytes([255, 0, 0, 255] * 4)  # 2x2 BGRA
        self.assertEqual(bs.downscale(px, 2, 2, 1), bytes([255, 0, 0, 255]))

    def test_copy_art_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bs.GeneratorError):
                bs.copy_art(Path(tmp, "nope"), Path(tmp, "mod"))


if __name__ == "__main__":
    unittest.main()
