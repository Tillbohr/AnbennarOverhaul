"""Static checks on the revised spells, one class per school: data in tools/data/spells.py and the hand-written
effects, events, modifiers and loc behind them (docs/superpowers/specs/2026-11-01-spell-revision-design.md).

    python -I -m unittest discover -s tools/tests -p "test_spell_schools.py"
"""

import importlib.util
import re
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
MOD = TOOLS.parent


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


def load_spells():
    spec = importlib.util.spec_from_file_location("aov_spells_data", TOOLS / "data" / "spells.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SPELLS


SPELLS = load_spells()
BY = {s["key"]: s for s in SPELLS}


def keys_in_slot_order(school):
    return [s["key"] for s in sorted((s for s in SPELLS if s["school"] == school), key=lambda s: s["slot"])]


def effects():
    return read("common/scripted_effects/aov_magic_effects.txt")


def modifiers():
    return read("common/modifiers/aov_magic_modifiers.txt")


def tuning():
    return read("common/script_values/aov_spell_tuning.txt")


class AbjurationTests(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(keys_in_slot_order("abjuration"),
                         ["combat_ward", "ward", "purify", "mass_ward", "mage_armor", "field_of_forbiddance"])

    def test_numbers(self):
        self.assertIn("prowess = 6", BY["combat_ward"]["modifier"])
        self.assertIn("health = 0.25", BY["combat_ward"]["modifier"])
        self.assertIn("garrison_size = 0.5", BY["mass_ward"]["modifier"])
        self.assertIn("defender_advantage = 6", BY["mass_ward"]["modifier"])
        self.assertIn("maa_toughness_mult = 0.25", BY["mage_armor"]["modifier"])
        self.assertIn("levy_toughness = ", BY["mage_armor"]["modifier"])
        self.assertIn("enemy_hostile_scheme_success_chance_add = -30", BY["field_of_forbiddance"]["modifier"])
        # The dispel runs on each enemy, not on the caster
        self.assertEqual(BY["field_of_forbiddance"]["effect"].strip(), "aov_field_of_forbiddance = yes")
        b = block(effects(), "aov_field_of_forbiddance")
        self.assertIn("every_war_enemy = {", b)
        self.assertIn("aov_spell_dispel_war_spells = yes", b.split("every_war_enemy = {", 1)[1])

    def test_ward_strengthened(self):
        self.assertIn("enemy_hostile_scheme_success_chance_add = -30", block(modifiers(), "aov_spell_ward_target"))

    def test_purify(self):
        self.assertEqual((BY["purify"]["type"], BY["purify"]["level"]), ("self", 1))
        self.assertEqual(BY["purify"]["effect"].strip(), "aov_purify = yes")
        b = block(effects(), "aov_purify")
        for s in ("remove_trait = wounded_1", "remove_trait = wounded_2", "remove_trait = wounded_3",
                  "aov_spell_remove_curses = yes", "add_stress = -20"):
            self.assertIn(s, b)
        for disease in ("ill", "consumption", "typhus", "smallpox", "bubonic_plague", "measles", "dysentery"):
            self.assertIn(f"recover_from_disease_effect = {{ DISEASE = {disease} }}", b)
        self.assertNotIn("aov_remove_pain = {", effects())

    def test_removed(self):
        self.assertNotIn("protected_journey", BY)


if __name__ == "__main__":
    unittest.main()
