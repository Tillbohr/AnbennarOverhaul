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

    def test_change_variable_only_on_existing_variables(self):
        """change_variable on an unset variable is a runtime error that does nothing ('Variable not of the
        value scope type'), so school progress never grew. Every changed variable is created first."""
        effects = self.effects()
        for name in set(re.findall(r"change_variable = \{ name = (\S+)", effects)):
            self.assertIn(f"NOT = {{ has_variable = {name} }}", effects, name)
        b = block(effects, "aov_school_add_progress")
        create = b.index("set_variable = { name = aov_school_$SCHOOL$_progress value = 0 }")
        self.assertLess(create, b.index("change_variable = { name = aov_school_$SCHOOL$_progress"))

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
        # The army this event was scheduled for (a recast army is a different scope), guarded if already gone
        self.assertIn("exists = scope:aov_new_elementals", b)
        self.assertIn("scope:aov_new_elementals = { deplete_army_by_percentage = 1 }", b)  # 0-1 fraction

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


class ReviewFixTests(unittest.TestCase):
    def test_new_mage_starts_full(self):
        v = block(read("common/script_values/aov_magic_values.txt"), "aov_mana")
        self.assertIn("value = aov_mana_max", v)
        e = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_mana_change")
        self.assertIn("set_variable = { name = aov_mana value = aov_mana_max }", e)

    def test_elementals_refund_without_capital(self):
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_summon_elementals")
        self.assertIn("aov_mana_change = { AMOUNT = aov_spell_summon_elementals_cost }", b)
        self.assertIn("remove_variable = aov_spell_summon_elementals_cd", b)


class AiTests(unittest.TestCase):
    def test_ai_studies_and_casts(self):
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_magic_ai_quarterly")
        self.assertIn("is_ai = yes", b)
        for school in ("enchantment", "evocation", "transmutation", "illusion", "divination"):
            self.assertIn(f"aov_study_set = {{ SCHOOL = {school} }}", b)
        self.assertIn("aov_magic_ai_any_castable = yes", b)
        self.assertIn("aov_magic_ai_cast_random = yes", b)
        self.assertIn("aov_magic_ai_quarterly = yes", block(read("common/on_action/aov_magic_on_actions.txt"), "aov_magic_quarterly_pulse"))


class SpellOverrideTests(unittest.TestCase):
    OVERRIDES = (
        ("start_compel_interaction", "anb_spellcasting_infin_spells.txt", "thoughtweave"),
        ("start_dominate_interaction", "anb_spellcasting_infin_spells.txt", "dominate_to_surrender"),
        ("anb_enhance_ability_interaction", "anb_spellcasting_interactions_enchantment.txt", "enhance_ability"),
    )

    def over(self):
        return read("common/character_interactions/zz_aov_spell_overrides.txt")

    def test_overrides_keep_anbennar_bodies(self):
        for name, src, _ in self.OVERRIDES:
            base = (MOD.parent / "anbennar-ck3-dev-master/common/character_interactions" / src).read_text(encoding="utf-8-sig")
            ours = block(self.over(), name)
            for line in block(base, name).splitlines():
                if line.strip() and not line.strip().startswith("#"):
                    self.assertIn(line, ours, f"{name}: {line}")

    def test_overrides_need_mana_level_and_cast(self):
        for name, _, k in self.OVERRIDES:
            b = block(self.over(), name)
            self.assertIn(f"scope:actor = {{ aov_spell_{k}_castable = yes }}", b)
            self.assertIn(f"scope:actor = {{ aov_spell_{k}_cast = yes }}", b)

    def test_interactions_respect_forbiddance(self):
        for name, _, _ in self.OVERRIDES:
            self.assertIn("scope:recipient = { aov_spell_target_allowed = yes }", block(self.over(), name))
        t = block(read("common/scripted_triggers/aov_magic_triggers.txt"), "aov_spell_target_allowed")
        self.assertIn("has_character_modifier = aov_spell_field_of_forbiddance", t)


if __name__ == "__main__":
    unittest.main()
