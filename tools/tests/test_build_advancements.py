"""Tests for tools/data/advancements.py and tools/build_advancements.py.

    python -I -m unittest discover -s tools/tests -p "test_build_advancements.py"
"""

import copy
import importlib.util
import re
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
MOD = TOOLS.parent
sys.path.insert(0, str(TOOLS))


def load_data():
    spec = importlib.util.spec_from_file_location("aov_advancements_data", TOOLS / "data" / "advancements.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ADVANCEMENTS


ADVS = load_data()

import build_advancements as ba  # noqa: E402
from build_inventions import GeneratorError  # noqa: E402


class DataTests(unittest.TestCase):
    def test_one_advancement_per_school(self):
        self.assertEqual(sorted(a["school"] for a in ADVS), sorted(ba.SCHOOLS))
        self.assertEqual({a["school"]: a["key"] for a in ADVS}, ba.ADV_OF_SCHOOL)

    def test_three_levels_each(self):
        for a in ADVS:
            self.assertEqual(len(a["levels"]), 3, a["key"])
            self.assertTrue(all(lv["name"] and lv["desc"] for lv in a["levels"]), a["key"])

    def test_costs_and_durations_rise(self):
        for seq in (ba.GOLD, ba.MANA, ba.YEARS):
            self.assertEqual(list(seq), sorted(set(seq)))
        self.assertEqual((ba.GOLD, ba.MANA, ba.YEARS), ((100, 200, 400), (50, 75, 100), (2, 3, 4)))

    def test_possession_and_prisoner_requirements(self):
        req = {a["key"]: a["requires"] for a in ADVS}
        self.assertIn("aov_adv_can_craft_enchanted_artifact", req["enchanted_artifact"][1])
        for n in (2, 3):
            self.assertIn("aov_adv_owns_enchanted_artifact", req["enchanted_artifact"][n])
        self.assertIn("aov_adv_owns_phylactery", req["lichdom"][3])
        self.assertIn("aov_adv_has_sacrifice", req["lichdom"][3])
        self.assertIn("aov_adv_can_become_lich", req["lichdom"][3])


class ValidateTests(unittest.TestCase):
    def broken(self, change):
        advs = copy.deepcopy(ADVS)
        change(advs[0])
        with self.assertRaises(GeneratorError):
            ba.validate(advs)

    def test_real_data_valid(self):
        ba.validate(ADVS)

    def test_rejects_unknown_school(self):
        self.broken(lambda a: a.update(school="pyromancy"))

    def test_rejects_two_levels(self):
        self.broken(lambda a: a.update(levels=a["levels"][:2]))

    def test_rejects_double_quote(self):
        self.broken(lambda a: a["levels"][0].update(desc='a "quoted" word'))

    def test_rejects_bad_requires_level(self):
        self.broken(lambda a: a.update(requires={4: ["aov_adv_x"]}))

    def test_rejects_duplicate(self):
        advs = copy.deepcopy(ADVS)
        advs.append(copy.deepcopy(advs[0]))
        with self.assertRaises(GeneratorError):
            ba.validate(advs)


if __name__ == "__main__":
    unittest.main()
