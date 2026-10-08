"""Tests for tools/data/inventions.py and tools/build_inventions.py.

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
sys.path.insert(0, str(TOOLS))


def load_data():
    spec = importlib.util.spec_from_file_location("aov_inventions_data", TOOLS / "data" / "inventions.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.INVENTIONS


INVENTIONS = load_data()
KEYS = [i["key"] for i in INVENTIONS]


class DataTests(unittest.TestCase):
    def test_sixty_unique_inventions(self):
        self.assertEqual(len(INVENTIONS), 60)
        self.assertEqual(len(set(KEYS)), 60)

    def test_category_counts_match_research_doc(self):
        counts = collections.Counter(i["category"] for i in INVENTIONS)
        self.assertEqual(counts, {"economic": 16, "military": 26, "society": 18})

    def test_every_category_tier_pair_is_populated(self):
        pairs = {(i["category"], i["tier"]) for i in INVENTIONS}
        self.assertEqual(len(pairs), 9)

    def test_fields(self):
        for i in INVENTIONS:
            with self.subTest(i["key"]):
                self.assertRegex(i["key"], r"^[a-z0-9_]+$")
                self.assertIn(i["tier"], (1, 2, 3))
                self.assertRegex(i["icon"], r"^Artf_\w+\.dds$")
                self.assertTrue(i["modifier"].strip())
                self.assertTrue(i["name"] and i["desc"])
                self.assertNotIn('"', i["name"] + i["desc"])

    def test_maa_unlocks(self):
        maa = {i["key"]: i["maa"] for i in INVENTIONS if i["maa"]}
        self.assertEqual(maa, {
            "prototype_tanks": "aov_prototype_tanks",
            "war_golems": "aov_war_golems",
            "damestear_reactor_megacannon": "aov_damestear_megacannon",
        })

    def test_locks(self):
        self.assertEqual(sum(1 for i in INVENTIONS if i["faith"]), 8)
        self.assertEqual({i["key"] for i in INVENTIONS if i["gnome_only"]},
                         {"conversation_calibrator", "coddorran_powered_exosuit", "gu_boats", "prefabricated_city_constructors"})

    def test_sorted_by_category_tier_key(self):
        order = {"economic": 0, "military": 1, "society": 2}
        self.assertEqual(INVENTIONS, sorted(INVENTIONS, key=lambda i: (order[i["category"]], i["tier"], i["key"])))


if __name__ == "__main__":
    unittest.main()
