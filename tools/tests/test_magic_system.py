"""Static checks on the hand-written magic system (mana, study, levels, special spells, interactions, AI).

    python -I -m unittest discover -s tools/tests -v
"""

import re
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent
SCHOOLS = ("abjuration", "conjuration", "divination", "enchantment", "evocation", "illusion", "necromancy", "transmutation")


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


class ManaStudyTests(unittest.TestCase):
    def values(self):
        return read("common/script_values/aov_magic_values.txt")

    def effects(self):
        return read("common/scripted_effects/aov_magic_effects.txt")

    def test_mana_values(self):
        v = self.values()
        self.assertIn("value = 100", block(v, "aov_mana_max"))
        self.assertIn("multiply = 50", block(v, "aov_mana_max"))
        self.assertIn("value = 5", block(v, "aov_mana_refill_month"))
        self.assertIn("multiply = 5", block(v, "aov_study_gain_month"))

    def test_mana_change_clamps(self):
        b = block(self.effects(), "aov_mana_change")
        self.assertIn("min = 0", b)
        self.assertIn("max = aov_mana_max", b)

    def test_thresholds(self):
        v = self.values()
        for s in SCHOOLS:
            b = block(v, f"aov_school_{s}_level")
            for n in ("300", "800", "2000"):
                self.assertIn(f">= {n}", b)

    def test_quarterly_ticks_three_months(self):
        b = block(self.effects(), "aov_magic_quarterly")
        self.assertIn("multiply = 3", b)
        for s in SCHOOLS:
            self.assertIn(f"aov_is_studying = {{ SCHOOL = {s} }}", b)

    def test_pulse_only_for_mages(self):
        text = read("common/on_action/aov_magic_on_actions.txt")
        self.assertIn("quarterly_playable_pulse = {\n\ton_actions = { aov_magic_quarterly_pulse }", text)
        self.assertIn("aov_is_mage = yes", block(text, "aov_magic_quarterly_pulse"))

    def test_study_switch_keeps_progress(self):
        b = block(self.effects(), "aov_study_set")
        self.assertIn("set_variable = { name = aov_studying value = flag:$SCHOOL$ }", b)
        self.assertNotIn("progress", b)
        self.assertIn("< 3", block(self.effects(), "aov_magic_quarterly"))  # no study gain at level 3

    def test_level_up_event(self):
        b = block(self.effects(), "aov_school_add_progress")
        self.assertIn("trigger_event = aov_magic.1", b)
        ev = block(read("events/aov_magic_events.txt"), "aov_magic.1")
        for s in SCHOOLS:
            self.assertIn(f"scope:aov_school = flag:{s}", ev)

    def test_mastery_synced(self):
        b = block(self.effects(), "aov_magic_sync_mastery")
        self.assertIn("name = magic_mastery", b)
        self.assertIn("value = aov_magic_mastery_value", b)

    def test_mage_trigger_uses_anbennar_affinity(self):
        self.assertIn("has_magical_affinity = yes", block(read("common/scripted_triggers/aov_magic_triggers.txt"), "aov_is_mage"))


class SpecialSpellTests(unittest.TestCase):
    def test_elementals_spawn_bound_to_war(self):
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_summon_elementals")
        for s in ("spawn_army", "type = aov_conjured_elementals", "inheritable = no", "save_scope_as = aov_new_elementals",
                  "name = aov_elemental_army", "id = aov_magic.10", "war = scope:aov_elemental_war"):
            self.assertIn(s, b)

    def test_elementals_depletion_guarded(self):
        b = block(read("events/aov_magic_events.txt"), "aov_magic.10")
        self.assertIn("exists = var:aov_elemental_army", b)
        self.assertIn("deplete_army_by_percentage = 1", b)  # 0-1 fraction
        self.assertIn("remove_variable = aov_elemental_army", b)

    def test_elementals_never_recruitable(self):
        self.assertIn("always = no", block(read("common/men_at_arms_types/aov_magic_maa_types.txt"), "aov_conjured_elementals"))

    def test_rite_of_conception_on_birth(self):
        text = read("common/on_action/aov_magic_on_actions.txt")
        self.assertIn("on_birth_child = {\n\ton_actions = { aov_magic_on_birth }", text)
        b = block(text, "aov_magic_on_birth")
        self.assertIn("has_character_modifier = aov_spell_rite_of_conception", b)
        self.assertIn("add_trait = magical_affinity_1", b)
        self.assertIn("chance = 50", b)

    def test_eye_for_talent_brings_a_courtier(self):
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_eye_for_talent")
        self.assertIn("create_character", b)
        self.assertIn("add_courtier = scope:aov_talent", b)
        templates = read("common/scripted_character_templates/aov_magic_templates.txt")
        for skill in ("diplomacy", "martial", "stewardship", "intrigue", "learning"):
            self.assertIn(f"{skill} = {{ 14 18 }}", block(templates, f"aov_talent_{skill}_template"))

    def test_extraplanar_contact_event(self):
        b = block(read("events/aov_magic_events.txt"), "aov_magic.20")
        self.assertEqual(b.count("option = {"), 3)
        self.assertIn("aov_extraplanar_price = yes", b)


if __name__ == "__main__":
    unittest.main()
