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


class EnchantmentTests(unittest.TestCase):
    def interactions(self):
        return read("common/character_interactions/aov_magic_interactions.txt")

    def test_keys(self):
        self.assertEqual(keys_in_slot_order("enchantment"),
                         ["enchanting_envoy", "heartstring", "enchant_trinket", "thoughtweave", "enchanting_embassy",
                          "dominate_to_surrender"])

    def test_numbers(self):
        self.assertEqual(BY["dominate_to_surrender"]["name"], "Dominate")
        self.assertIn("diplomacy = 4", BY["enchanting_envoy"]["modifier"])
        self.assertIn("general_opinion = 5", BY["enchanting_envoy"]["modifier"])
        self.assertIn("vassal_opinion = 25", BY["enchanting_embassy"]["modifier"])
        self.assertIn("general_opinion = 10", BY["enchanting_embassy"]["modifier"])
        self.assertIn("years = 3", BY["heartstring"]["effect"])
        self.assertIn("opinion = 50", block(read("common/opinion_modifiers/aov_magic_opinion_modifiers.txt"), "aov_charmed_opinion"))

    def test_hand_written_hostile_interactions(self):
        self.assertEqual(BY["thoughtweave"]["interaction"], "aov_thoughtweave_interaction")
        self.assertEqual(BY["dominate_to_surrender"]["interaction"], "aov_dominate_interaction")
        for k in ("thoughtweave", "dominate_to_surrender"):
            self.assertTrue(BY[k]["hostile"], k)

    def test_enchantment_interactions_respect_forbiddance(self):
        for name, k in (("aov_thoughtweave_interaction", "thoughtweave"), ("aov_dominate_interaction", "dominate_to_surrender")):
            b = block(self.interactions(), name)
            self.assertIn("scope:recipient = { aov_spell_target_allowed = yes }", b)
            self.assertIn(f"scope:actor = {{ aov_spell_{k}_castable = yes }}", b)
            self.assertIn(f"scope:actor = {{ aov_spell_{k}_cast = yes }}", b)
            self.assertIn("aov_spell_ai_hostile_target = yes", b)
            self.assertIn("send_options_exclusive = yes", b)

    def test_thoughtweave(self):
        b = block(self.interactions(), "aov_thoughtweave_interaction")
        for flag in ("aov_tw_friend", "aov_tw_lover", "aov_tw_rival", "aov_tw_hook"):
            self.assertIn(f"flag = {flag}", b)
        self.assertEqual(BY["thoughtweave"]["effect"].strip(), "aov_thoughtweave_apply = yes")
        a = block(effects(), "aov_thoughtweave_apply")
        for s in ("set_relation_friend", "type = manipulation_hook", "trigger_event = aov_magic.43",
                  "can_set_relation_lover_trigger", "can_set_relation_rival_trigger"):
            self.assertIn(s, a)
        e = block(read("events/aov_magic_events.txt"), "aov_magic.43")
        for s in ("set_relation_lover", "set_relation_rival", "scope:aov_tw_candidate_1", "scope:aov_tw_candidate_3",
                  "ai_chance"):
            self.assertIn(s, e)

    def test_dominate(self):
        b = block(self.interactions(), "aov_dominate_interaction")
        for flag in ("aov_dom_hook", "aov_dom_surrender", "aov_dom_free"):
            self.assertIn(f"flag = {flag}", b)
        self.assertIn("aov_dominate_surrender_possible = yes", b.split("flag = aov_dom_surrender")[0].rsplit("send_option", 1)[1])
        self.assertIn("any_prisoner", b.split("flag = aov_dom_free")[0].rsplit("send_option", 1)[1])
        self.assertEqual(BY["dominate_to_surrender"]["effect"].strip(), "aov_dominate_apply = yes")
        a = block(effects(), "aov_dominate_apply")
        for s in ("dominate_success_effect = yes", "end_war = attacker", "end_war = defender", "trigger_event = aov_magic.44"):
            self.assertIn(s, a)
        e = block(read("events/aov_magic_events.txt"), "aov_magic.44")
        self.assertIn("release_from_prison = yes", e)
        self.assertIn("scope:aov_dom_prisoner_3", e)

    def test_dominate_surrender_target_trigger(self):
        t = block(read("common/scripted_triggers/aov_magic_triggers.txt"), "aov_dominate_surrender_possible")
        for s in ("any_character_war", "primary_attacker = scope:recipient", "primary_defender = scope:actor",
                  "primary_attacker = scope:actor", "primary_defender = scope:recipient"):
            self.assertIn(s, t)

    def test_anbennar_compel_and_dominate_hidden(self):
        over = read("common/character_interactions/zz_aov_spell_overrides.txt")
        for name in ("start_compel_interaction", "start_dominate_interaction"):
            b = block(over, name)
            self.assertIn("is_shown = { always = no }", b)
            self.assertNotIn("start_scheme", b)

    def test_enchant_trinket(self):
        self.assertEqual(BY["enchant_trinket"]["effect"].strip(), "aov_enchant_trinket = yes")
        b = block(effects(), "aov_enchant_trinket")
        self.assertIn("create_artifact", b)
        self.assertIn("type = miscellaneous", b)
        self.assertIn("decaying = yes", b)
        for skill in ("diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess"):
            self.assertIn(f"modifier = aov_spell_trinket_{skill}", b)
            block(read("common/modifiers/aov_magic_modifiers.txt"), f"aov_spell_trinket_{skill}")
        loc = read("localization/english/aov_magic_l_english.yml")
        for k in ("aov_spell_trinket_name", "aov_spell_trinket_desc", "aov_magic.43.t", "aov_magic.44.t",
                  "aov_thoughtweave_interaction", "aov_dominate_interaction", "aov_tw_lover_option", "aov_dom_free_option"):
            self.assertIn(f" {k}:", loc)

    def test_removed(self):
        self.assertNotIn("command_animals", BY)


class EvocationTests(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(keys_in_slot_order("evocation"),
                         ["fireball", "shock_and_awe", "flaming_munitions", "winters_grip", "earthquake", "meteor_swarm"])

    def test_types_and_numbers(self):
        for k in ("fireball", "winters_grip", "earthquake"):
            self.assertEqual(BY[k]["type"], "targeted", k)
            self.assertTrue(BY[k]["hostile"], k)
        m = BY["meteor_swarm"]
        self.assertEqual((m["type"], m["level"], m["slot"]), ("war", 3, 6))
        for s in ("maa_damage_mult = 0.3", "advantage = 10", "health = -0.5"):
            self.assertIn(s, m["modifier"])
        self.assertEqual(m["effect"].strip(), "aov_meteor_swarm = yes")
        self.assertEqual(BY["shock_and_awe"]["name"], "Thunderclap")
        self.assertIn("advantage = 6", BY["shock_and_awe"]["modifier"])
        self.assertIn("maa_damage_mult = 0.1", BY["shock_and_awe"]["modifier"])
        self.assertIn("siege_phase_time = -0.4", BY["flaming_munitions"]["modifier"])

    def test_evocation_target_trigger(self):
        self.assertEqual(BY["fireball"]["target_trigger"], "aov_spell_target_war_foe")
        self.assertEqual(BY["winters_grip"]["target_trigger"], "aov_spell_target_war_capital")
        self.assertEqual(BY["earthquake"]["target_trigger"], "aov_spell_target_war_capital")
        triggers = read("common/scripted_triggers/aov_magic_triggers.txt")
        foe = block(triggers, "aov_spell_target_war_foe")
        for s in ("is_at_war_with = scope:recipient", "is_knight = yes", "is_commanding_army = yes"):
            self.assertIn(s, foe)
        cap = block(triggers, "aov_spell_target_war_capital")
        self.assertIn("is_at_war_with = scope:recipient", cap)
        self.assertIn("exists = capital_province", cap)

    def test_fireball(self):
        self.assertEqual(BY["fireball"]["effect"].strip(), "aov_fireball = yes")
        b = block(effects(), "aov_fireball")
        self.assertEqual(b.count("increase_wounds_effect = { REASON = fight }"), 2)
        self.assertIn("chance = aov_fireball_severe_chance", b)
        self.assertIn("value = 20", block(tuning(), "aov_fireball_severe_chance"))

    def test_winters_grip(self):
        self.assertEqual(BY["winters_grip"]["curse"], "aov_spell_winters_grip_target")
        m = block(modifiers(), "aov_spell_winters_grip_target")
        for s in ("movement_speed = -0.4", "maa_damage_mult = -0.15", "supply_limit_mult = -0.2"):
            self.assertIn(s, m)
        b = block(effects(), "aov_winters_grip")
        self.assertIn("value = aov_spell_winters_grip_years", b)
        self.assertIn("modifier = aov_spell_winters_grip_target", b)

    def test_earthquake(self):
        b = block(effects(), "aov_earthquake")
        for s in ("change_development_level = -2", "change_county_control = -40",
                  "add_county_modifier = { modifier = aov_earthquake_damage years = 3 }",
                  "chance = aov_earthquake_extra_chance", "change_development_level = -1"):
            self.assertIn(s, b)
        self.assertIn("value = 25", block(tuning(), "aov_earthquake_extra_chance"))
        m = block(modifiers(), "aov_earthquake_damage")
        self.assertIn("fort_level = -1", m)
        self.assertIn("garrison_size = -0.5", m)

    def test_meteor_swarm(self):
        b = block(effects(), "aov_meteor_swarm")
        for s in ("is_attacker = scope:aov_meteor_caster", "primary_defender", "primary_attacker",
                  "ordered_held_county = {", "order_by = development_level", "max = 3",
                  "change_development_level = -1", "change_county_control = -30",
                  "add_county_modifier = { modifier = aov_meteor_scorched years = 5 }"):
            self.assertIn(s, b)
        m = block(modifiers(), "aov_meteor_scorched")
        self.assertIn("levy_size = -0.5", m)
        self.assertIn("tax_mult = -0.5", m)

    def test_removed(self):
        for k in ("tearfall", "elemental_fury"):
            self.assertNotIn(k, BY)



class IllusionTests(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(keys_in_slot_order("illusion"),
                         ["invisibility", "fear_and_loathing", "phantasmal_rumour", "shadows_in_the_night",
                          "implant_scandal", "grand_deception"])

    def test_numbers(self):
        self.assertIn("intrigue = 4", BY["invisibility"]["modifier"])
        self.assertIn("owned_scheme_secrecy_add = 25", BY["invisibility"]["modifier"])
        self.assertIn("dread_baseline_add = 40", BY["fear_and_loathing"]["modifier"])
        self.assertIn("owned_hostile_scheme_success_chance_add = 25", BY["shadows_in_the_night"]["modifier"])
        self.assertIn("owned_scheme_secrecy_add = 40", BY["shadows_in_the_night"]["modifier"])
        for k in ("phantasmal_rumour", "implant_scandal", "grand_deception"):
            self.assertEqual(BY[k]["type"], "targeted", k)
            self.assertTrue(BY[k]["hostile"], k)

    def test_phantasmal_rumour(self):
        self.assertEqual(BY["phantasmal_rumour"]["curse"], "aov_spell_phantasmal_rumour_target")
        b = block(effects(), "aov_phantasmal_rumour")
        self.assertIn("add_prestige = -150", b)
        self.assertIn("modifier = aov_spell_phantasmal_rumour_target", b)
        self.assertIn("years = 3", b)
        self.assertIn("vassal_opinion = -20", block(modifiers(), "aov_spell_phantasmal_rumour_target"))

    def test_implant_scandal(self):
        b = block(effects(), "aov_implant_scandal")
        for secret in ("secret_deviant", "secret_witch", "secret_non_believer"):
            self.assertIn(f"{secret}_is_valid_trigger = {{ OWNER = scope:recipient }}", b)
            self.assertIn(f"any_secret = {{ secret_type = {secret} }}", b)
            self.assertIn(f"add_secret = {{ type = {secret} }}", b)
        self.assertIn("reveal_to = scope:aov_deceiver", b)

    def test_illusion_target_trigger(self):
        self.assertEqual(BY["grand_deception"]["target_trigger"], "aov_spell_target_has_county")
        self.assertIn("any_held_county", block(read("common/scripted_triggers/aov_magic_triggers.txt"),
                                               "aov_spell_target_has_county"))
        b = block(effects(), "aov_grand_deception")
        self.assertIn("any_neighboring_county", b)
        self.assertIn("capital_county", b)
        self.assertIn("add_pressed_claim = scope:aov_deception_county", b)

    def test_removed(self):
        for k in ("bread_and_circuses", "assimilation_program", "lead_the_crowds"):
            self.assertNotIn(k, BY)
        self.assertNotIn("aov_assimilation_program = {", effects())



class NecromancyTests(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(keys_in_slot_order("necromancy"),
                         ["ray_of_sickness", "contagion", "steal_vitality", "plague_cloud", "raise_dead", "finger_of_death"])

    def test_numbers(self):
        for k in ("ray_of_sickness", "contagion", "steal_vitality", "plague_cloud", "finger_of_death"):
            self.assertEqual(BY[k]["type"], "targeted", k)
            self.assertTrue(BY[k]["hostile"], k)
        self.assertEqual(BY["raise_dead"]["type"], "war")
        self.assertEqual(BY["steal_vitality"]["name"], "Life Drain")
        self.assertIn("health = 2", BY["steal_vitality"]["modifier"])
        self.assertIn("health = -2", block(modifiers(), "aov_spell_steal_vitality_victim"))
        self.assertIn("health = -1", block(modifiers(), "aov_spell_ray_of_sickness_victim"))
        self.assertEqual(BY["ray_of_sickness"]["curse"], "aov_spell_ray_of_sickness_victim")
        self.assertEqual(BY["steal_vitality"]["curse"], "aov_spell_steal_vitality_victim")

    def test_curses_last_the_casters_duration(self):
        for k, eff in (("ray_of_sickness", "aov_ray_of_sickness"), ("steal_vitality", "aov_life_drain")):
            self.assertEqual(BY[k]["effect"].strip(), f"{eff} = yes")
            b = block(effects(), eff)
            self.assertIn(f"value = aov_spell_{k}_years", b)

    def test_contagion(self):
        b = block(effects(), "aov_contagion")
        for d in ("consumption", "typhus", "smallpox"):
            self.assertIn(f"can_contract_disease_trigger = {{ DISEASE = {d} }}", b)
            self.assertIn(f"contract_disease_effect = {{ DISEASE = {d} TREATMENT_EVENT = no }}", b)
        self.assertIn("add_trait = ill", b)

    def test_plague_cloud_target_trigger(self):
        self.assertEqual(BY["plague_cloud"]["target_trigger"], "aov_spell_target_has_capital")
        self.assertIn("exists = capital_province", block(read("common/scripted_triggers/aov_magic_triggers.txt"),
                                                         "aov_spell_target_has_capital"))
        b = block(effects(), "aov_plague_cloud")
        self.assertIn("capital_province = {", b)
        for d in ("smallpox", "bubonic_plague", "typhus", "consumption", "measles", "dysentery"):
            self.assertIn(f"type = {d}", b)
        self.assertIn("add = aov_plague_cloud_major_chance", b)
        self.assertIn("intensity = major", b)
        self.assertIn("intensity = minor", b)
        self.assertNotIn("apocalyptic", b)
        self.assertIn("value = 20", block(tuning(), "aov_plague_cloud_major_chance"))

    def test_raise_dead(self):
        b = block(effects(), "aov_raise_dead")
        self.assertIn("aov_spawn_spell_army = { SPELL = raise_dead TYPE = aov_lich_skeletons STACKS = 2 }", b)
        self.assertIn("aov_spawn_spell_army = { SPELL = raise_dead TYPE = aov_lich_skeleton_archers STACKS = 1 }", b)
        self.assertIn("aov_spawn_spell_army = { SPELL = raise_dead TYPE = aov_lich_skeletons STACKS = 4 }", b)
        self.assertIn("aov_spawn_spell_army = { SPELL = raise_dead TYPE = aov_lich_skeleton_archers STACKS = 2 }", b)
        self.assertIn("has_trait = lich", b)
        self.assertIn("aov_spell_army_fizzle = { SPELL = raise_dead }", b)
        self.assertIn(" aov_raise_dead_army_name:", read("localization/english/aov_magic_l_english.yml"))

    def test_finger_of_death(self):
        b = block(effects(), "aov_finger_of_death")
        for v, n in (("aov_finger_death_chance", 15), ("aov_finger_injury_chance", 45), ("aov_finger_disease_chance", 40)):
            self.assertIn(f"add = {v}", b)
            self.assertIn(f"value = {n}", block(tuning(), v))
        self.assertIn("death = { death_reason = death_mysterious }", b)
        for t in ("maimed", "one_eyed", "one_legged", "disfigured"):
            self.assertIn(f"has_trait = {t}", b)
        self.assertIn("increase_wounds_effect", b)
        self.assertIn("contract_disease_effect", b)
        self.assertIn("add_dread = 20", b)

    def test_dark_magic_on_every_necromancy_spell(self):
        spell_effects = read("common/scripted_effects/aov_spell_effects.txt")
        for s in SPELLS:
            if s["school"] == "necromancy":
                self.assertIn("aov_dark_magic_roll = yes", block(spell_effects, f"aov_spell_{s['key']}_cast"), s["key"])

    def test_removed(self):
        for k in ("false_life", "speak_with_dead", "remove_pain", "chronophage"):
            self.assertNotIn(k, BY)
        self.assertNotIn("aov_speak_with_dead = {", effects())



SKILLS = ("diplomacy", "martial", "stewardship", "intrigue", "learning")
TROOPS = ("heavy_infantry", "skirmishers", "pikemen", "archers", "light_cavalry", "heavy_cavalry")
FORMS = ("bear", "wolf", "hawk")
TIERED = ("beauty", "intellect", "physique")
DEFECTS = ("clubfooted", "hunchbacked", "lisping", "stuttering", "dwarf", "giant", "spindly", "scaly", "wheezing",
           "bleeder", "infertile", "depressed_genetic", "lunatic_genetic", "possessed_genetic")


class TransmutationTests(unittest.TestCase):
    def events(self):
        return read("events/aov_magic_events.txt")

    def test_keys(self):
        self.assertEqual(keys_in_slot_order("transmutation"),
                         ["enhance_ability", "longstrider", "mass_enlarge", "living_steel", "shapechange", "perfect_form"])

    def test_numbers(self):
        ls = BY["longstrider"]
        self.assertEqual((ls["level"], ls["slot"]), (1, 2))
        self.assertIn("movement_speed = 0.3", ls["modifier"])
        self.assertIn("character_travel_speed_mult = 0.4", ls["modifier"])
        self.assertIn("maa_toughness_mult = 0.2", BY["mass_enlarge"]["modifier"])
        self.assertIn("maa_damage_mult = 0.2", BY["mass_enlarge"]["modifier"])
        self.assertEqual(BY["living_steel"]["type"], "war")
        for k, ev in (("enhance_ability", "aov_magic.40"), ("living_steel", "aov_magic.41"), ("shapechange", "aov_magic.42")):
            self.assertEqual(BY[k]["effect"].strip(), f"trigger_event = {ev}", k)
            self.assertTrue(BY[k]["scales_duration"], k)

    def choice_event(self, event, modifiers, spell):
        e = block(self.events(), event)
        self.assertEqual(e.count("option = {"), len(modifiers), event)
        self.assertEqual(e.count("ai_chance"), len(modifiers), event)
        self.assertIn(f"value = aov_spell_{spell}_years", e)
        for m in modifiers:
            self.assertIn(f"modifier = {m} years = scope:aov_choice_years", e)
            block(modifiers_text(), m)

    def test_enhance_ability(self):
        mods = [f"aov_spell_enhance_{s}" for s in SKILLS]
        self.choice_event("aov_magic.40", mods, "enhance_ability")
        for s in SKILLS:
            self.assertIn(f"{s} = 4", block(modifiers_text(), f"aov_spell_enhance_{s}"))

    def test_living_steel(self):
        mods = [f"aov_spell_living_steel_{t}" for t in TROOPS]
        self.choice_event("aov_magic.41", mods, "living_steel")
        for t in TROOPS:
            m = block(modifiers_text(), f"aov_spell_living_steel_{t}")
            self.assertIn(f"{t}_damage_mult = 0.3", m)
            self.assertIn(f"{t}_toughness_mult = 0.3", m)

    def test_shapechange(self):
        mods = [f"aov_spell_shape_{f}" for f in FORMS]
        self.choice_event("aov_magic.42", mods, "shapechange")
        for f in FORMS:
            self.assertIn("dread_baseline_add = 20", block(modifiers_text(), f"aov_spell_shape_{f}"))
        self.assertIn("prowess = 10", block(modifiers_text(), "aov_spell_shape_bear"))
        self.assertIn("martial = 3", block(modifiers_text(), "aov_spell_shape_wolf"))
        self.assertIn("intrigue = 3", block(modifiers_text(), "aov_spell_shape_hawk"))

    def test_perfect_form_pool_guards(self):
        pf = BY["perfect_form"]
        self.assertEqual(pf["requires"], "aov_perfect_form_possible")
        self.assertEqual(pf["effect"].strip(), "aov_perfect_form = yes")
        b = block(effects(), "aov_perfect_form")
        possible = block(read("common/scripted_triggers/aov_magic_triggers.txt"), "aov_perfect_form_possible")
        for g in TIERED:
            # none -> good 1, only without the bad trait of that group
            self.assertIn(f"add_trait = {g}_good_1", b)
            self.assertIn(f"remove_trait = {g}_good_1", b)
            self.assertIn(f"add_trait = {g}_good_2", b)
            self.assertIn(f"add_trait = {g}_good_3", b)
            self.assertNotIn(f"add_trait = {g}_good_4", b)
            for n in (1, 2, 3):
                self.assertIn(f"remove_trait = {g}_bad_{n}", b)
            self.assertIn(f"{g}_bad_1", possible)
        for d in DEFECTS:
            self.assertIn(f"remove_trait = {d}", b)
            self.assertIn(f"has_trait = {d}", possible)
        self.assertIn("add_trait = fecund", b)
        self.assertIn("NOT = { has_trait = fecund }", possible)
        self.assertNotIn("albino", b)
        self.assertNotIn("magical_affinity", b)
        self.assertIn("add_stress = 50", b)
        self.assertIn("chance = aov_perfect_form_health_risk", b)
        self.assertIn("value = 10", block(tuning(), "aov_perfect_form_health_risk"))

    def test_perfect_form_branch_guards(self):
        """Each pool entry is limited so it never gives a trait already held, never upgrades past good 3 and never
        offers a good trait while the bad trait of that group is held."""
        b = block(effects(), "aov_perfect_form")
        for g in TIERED:
            entry = b.split(f"add_trait = {g}_good_1")[0].rsplit("1 = {", 1)[1]
            for n in (1, 2, 3):
                self.assertIn(f"has_trait = {g}_good_{n}", entry)
                self.assertIn(f"has_trait = {g}_bad_{n}", entry)
            up2 = b.split(f"add_trait = {g}_good_2")[0].rsplit("1 = {", 1)[1]
            self.assertIn(f"has_trait = {g}_good_1", up2)
            up3 = b.split(f"add_trait = {g}_good_3")[0].rsplit("1 = {", 1)[1]
            self.assertIn(f"has_trait = {g}_good_2", up3)

    def test_removed(self):
        for k in ("plant_growth", "transmute_to_gold", "reshape_terrain", "rite_of_conception"):
            self.assertNotIn(k, BY)
        self.assertNotIn("aov_transmute_to_gold = {", effects())
        self.assertNotIn("aov_magic_on_birth", read("common/on_action/aov_magic_on_actions.txt"))


def modifiers_text():
    return read("common/modifiers/aov_magic_modifiers.txt")



class ReviewFixTests(unittest.TestCase):
    """Findings of the final review of the spell revision."""

    def test_forbiddance_dispels_living_steel(self):
        dispel = block(read("common/scripted_effects/aov_spell_effects.txt"), "aov_spell_dispel_war_spells")
        for t in TROOPS:
            self.assertIn(f"remove_character_modifier = aov_spell_living_steel_{t}", dispel)
        self.assertIn("remove_character_modifier = aov_spell_mass_enlarge", dispel)

    def test_bound_champion_can_be_a_knight(self):
        tpl = block(read("common/scripted_character_templates/aov_magic_templates.txt"), "aov_bound_champion_template")
        self.assertIn("gender_female_chance = root_soldier_female_chance", tpl)

    def test_enchanted_trinket_decays_in_about_ten_years(self):
        b = block(effects(), "aov_enchant_trinket")
        self.assertIn("add_durability = aov_enchant_trinket_durability_cut", b)
        self.assertIn("value = -50", block(tuning(), "aov_enchant_trinket_durability_cut"))

    def test_dominate_offers_the_casters_people_first(self):
        b = block(effects(), "aov_dominate_apply")
        for n in (0, 1, 2):
            self.assertIn(f"position = {n}", b)
        self.assertEqual(b.count("order_by = aov_dominate_prisoner_priority"), 3)
        self.assertEqual(b.count("check_range_bounds = no"), 3)
        v = block(tuning(), "aov_dominate_prisoner_priority")
        for s in ("value = prowess", "is_close_family_of = scope:aov_dominator", "is_spouse_of = scope:aov_dominator",
                  "is_courtier_of = scope:aov_dominator", "liege = scope:aov_dominator",
                  "is_allied_to = scope:aov_dominator", "add = 100"):
            self.assertIn(s, v)

    def test_war_spell_hits_are_open(self):
        for eff in ("aov_fireball", "aov_winters_grip", "aov_earthquake"):
            self.assertIn("aov_spell_struck_notice = yes", block(effects(), eff), eff)
        n = block(effects(), "aov_spell_struck_notice")
        self.assertIn("save_scope_as = aov_spell_caster", n)
        self.assertIn("trigger_event = aov_magic.51", n)
        e = block(read("events/aov_magic_events.txt"), "aov_magic.51")
        self.assertIn("right_portrait = scope:aov_spell_caster", e)
        loc = read("localization/english/aov_magic_l_english.yml")
        for k in ("aov_magic.51.t", "aov_magic.51.desc", "aov_magic.51.a"):
            self.assertIn(f" {k}:", loc)


if __name__ == "__main__":
    unittest.main()
