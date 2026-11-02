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


class ConjurationTests(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(keys_in_slot_order("conjuration"),
                         ["summon_familiars", "summon_beasts", "bound_champion", "summon_elementals", "aid_construction",
                          "planar_gate"])

    def test_numbers(self):
        self.assertEqual(BY["aid_construction"]["name"], "Unseen Servants")
        self.assertIn("build_speed = -0.4", BY["aid_construction"]["modifier"])
        self.assertIn("build_gold_cost = -0.25", BY["aid_construction"]["modifier"])
        self.assertIn("intrigue = 3", BY["summon_familiars"]["modifier"])
        self.assertIn("learning = 3", BY["summon_familiars"]["modifier"])
        for k in ("summon_beasts", "summon_elementals", "planar_gate"):
            self.assertEqual(BY[k]["type"], "war", k)
            self.assertTrue(BY[k]["scales_duration"], k)
        self.assertTrue(BY["bound_champion"]["scales_duration"])

    def test_army_spells_use_the_helper(self):
        for eff, typ, stacks in (("aov_summon_beasts", "aov_conjured_beasts", 2),
                                 ("aov_summon_elementals", "aov_conjured_elementals", 6)):
            b = block(effects(), eff)
            spell_key = eff[len("aov_"):]
            self.assertIn(f"aov_spawn_spell_army = {{ SPELL = {spell_key} TYPE = {typ} STACKS = {stacks} }}", b)
            self.assertIn(f"aov_spell_army_fizzle = {{ SPELL = {spell_key} }}", b)
            self.assertIn("aov_spell_army_possible = yes", b)

    def test_planar_gate(self):
        b = block(effects(), "aov_planar_gate")
        for host in ("angels", "eldritch", "devils"):
            self.assertIn(f"var:aov_adv_host = flag:{host}", b)
            self.assertIn(f"TYPE = aov_host_{host} STACKS = 10", b)
        self.assertIn("TYPE = aov_conjured_elementals STACKS = 10", b)
        self.assertIn("aov_spell_army_fizzle = { SPELL = planar_gate }", b)
        self.assertIn("chance = aov_planar_gate_demon_chance", b)
        self.assertIn("trigger_event = aov_magic.20", b)
        self.assertIn("value = 10", block(tuning(), "aov_planar_gate_demon_chance"))
        loc = read("localization/english/aov_magic_l_english.yml")
        for k in ("summon_beasts", "planar_gate"):
            self.assertIn(f" aov_{k}_army_name:", loc)

    def test_beasts_never_recruitable(self):
        b = block(read("common/men_at_arms_types/aov_magic_maa_types.txt"), "aov_conjured_beasts")
        self.assertIn("type = light_cavalry", b)
        self.assertIn("always = no", b)
        self.assertIn(" aov_conjured_beasts:", read("localization/english/aov_magic_l_english.yml"))

    def test_champion_vanishes_on_their_own(self):
        b = block(effects(), "aov_bound_champion")
        for s in ("create_character", "template = aov_bound_champion_template", "add_courtier = scope:aov_champion",
                  "set_knight_status = force", "add_character_flag = aov_bound_outsider"):
            self.assertIn(s, b)
        champion = b.split("scope:aov_champion = {", 1)[1]
        self.assertIn("trigger_event = { id = aov_magic.11 years = scope:aov_champion_years }", champion)
        self.assertIn("death = { death_reason = death_vanished }", block(read("events/aov_magic_events.txt"), "aov_magic.11"))
        tpl = block(read("common/scripted_character_templates/aov_magic_templates.txt"), "aov_bound_champion_template")
        self.assertIn("prowess = { 23 27 }", tpl)
        self.assertIn("lifestyle_blademaster", tpl)

    def test_removed(self):
        for k in ("extraplanar_contact", "summon_animals", "conjure_supplies"):
            self.assertNotIn(k, BY)


class DivinationTests(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(keys_in_slot_order("divination"),
                         ["guidance", "detect_plots", "eye_for_talent", "scry", "augury", "foresight"])

    def test_numbers(self):
        self.assertIn("learning = 4", BY["guidance"]["modifier"])
        self.assertIn("monthly_lifestyle_xp_gain_mult = 0.15", BY["guidance"]["modifier"])
        f = BY["foresight"]["modifier"]
        for s in ("advantage = 12", "enemy_scheme_secrecy_add = -50", "owned_hostile_scheme_success_chance_add = 10"):
            self.assertIn(s, f)
        a = BY["augury"]
        self.assertIn("owned_hostile_scheme_success_chance_add = 10", a["modifier"])
        self.assertIn("monthly_prestige_gain_mult = 0.1", a["modifier"])
        self.assertEqual(a["years_mult"], "aov_adv_orb_spell_years_mult")
        self.assertEqual(a["effect"].strip(), "aov_augury = yes")
        self.assertEqual(BY["detect_plots"]["effect"].strip(), "aov_detect_plots = yes")

    def test_detect_plots_exposes_hostile_schemes_and_agents(self):
        b = block(effects(), "aov_detect_plots")
        for s in ("every_targeting_scheme = {", "is_hostile = yes", "every_scheme_agent_character = {",
                  "expose_scheme_agent = scope:aov_plot_agent", "expose_scheme = yes"):
            self.assertIn(s, b)

    def test_scry_reveals_everything(self):
        b = block(effects(), "aov_scry_reveal")
        self.assertIn("every_secret = {", b)
        self.assertIn("reveal_to = scope:aov_scryer", b)
        orb = b.split("aov_adv_orb_of_omniscience_level >= 2", 1)[1]
        self.assertIn("every_known_secret = {", orb)

    def test_augury_event(self):
        e = block(read("events/aov_magic_events.txt"), "aov_magic.45")
        for s in ("aov_augury_claimant", "aov_augury_faction", "aov_augury_dying", "aov_augury_plotter"):
            self.assertIn(f"exists = scope:{s}", e)
        b = block(effects(), "aov_augury")
        for s in ("every_claimant", "max_military_strength", "every_targeting_faction", "health < fine_health",
                  "every_targeting_scheme", "trigger_event = aov_magic.45"):
            self.assertIn(s, b)
        loc = read("localization/english/aov_magic_l_english.yml")
        for k in ("t", "desc.intro", "desc.claimant", "desc.faction", "desc.dying", "desc.plotter", "desc.none", "a"):
            self.assertIn(f" aov_magic.45.{k}:", loc)

    def test_removed(self):
        for k in ("deposit_divination", "manipulated_fortune"):
            self.assertNotIn(k, BY)
        self.assertNotIn("aov_deposit_divination = {", effects())


if __name__ == "__main__":
    unittest.main()
