"""Static checks on the hand-written magic advancement script (interlock, tick, level effects, content).

    python -I -m unittest discover -s tools/tests -p "test_advancements.py"
"""

import importlib.util
import re
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
MOD = TOOLS.parent
SCHOOLS = ("abjuration", "conjuration", "divination", "enchantment", "evocation", "illusion", "necromancy", "transmutation")


def load_data():
    spec = importlib.util.spec_from_file_location("aov_advancements_data", TOOLS / "data" / "advancements.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ADVANCEMENTS


ADVS = load_data()
ADV_KEYS = [a["key"] for a in ADVS]

LEVEL_EFFECTS = "common/scripted_effects/aov_advancement_level_effects.txt"
CONDITIONS = "common/scripted_triggers/aov_advancement_conditions.txt"
ON_ACTIONS = "common/on_action/aov_advancement_on_actions.txt"
EVENTS = "events/aov_advancement_events.txt"
CONTENT_LOC = "localization/english/aov_advancement_content_l_english.yml"
TUNING = "common/script_values/aov_advancement_tuning.txt"
MODIFIERS = "common/modifiers/aov_advancement_modifiers.txt"


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


def loc_keys(rel):
    return set(re.findall(r"^ ([A-Za-z0-9_.]+):", read(rel), re.M))


class InterlockTests(unittest.TestCase):
    def test_study_button_blocked_while_committed(self):
        sg = read("common/scripted_guis/aov_spell_sgui.txt")
        for c in SCHOOLS:
            body = block(sg, f"aov_study_{c}_sgui")
            self.assertIn("text = AOV_ADV_REQ_NOT_COMMITTED", body)
            self.assertIn("NOT = { aov_adv_is_committed = yes }", body)

    def test_ai_does_not_restudy_while_committed(self):
        ai = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_magic_ai_quarterly")
        self.assertRegex(ai, r"NOT = \{ has_variable = aov_studying \}\s*\n\s*NOT = \{ has_variable = aov_adv_committed \}")

    def test_quarterly_pulse_runs_the_tick_for_mages(self):
        oa = read(ON_ACTIONS)
        self.assertIn("aov_adv_quarterly_pulse", block(oa, "quarterly_playable_pulse"))
        pulse = block(oa, "aov_adv_quarterly_pulse")
        self.assertIn("aov_is_mage = yes", pulse)
        self.assertIn("aov_adv_quarterly = yes", pulse)

    def test_every_level_effect_defined_once(self):
        eff = read(LEVEL_EFFECTS)
        for key in ADV_KEYS:
            for n in (1, 2, 3):
                self.assertEqual(len(re.findall(rf"^aov_adv_{key}_{n}_effect = \{{", eff, re.M)), 1, f"{key} {n}")

    def test_every_requires_trigger_defined(self):
        cond = read(CONDITIONS)
        for a in ADVS:
            for names in a["requires"].values():
                for t in names:
                    self.assertRegex(cond, rf"(?m)^{t} = \{{", t)

    def test_completion_event_exists(self):
        ev = read(EVENTS)
        self.assertTrue(ev.startswith("namespace = aov_advancement"))
        body = block(ev, "aov_advancement.1")
        for key in ADV_KEYS:
            self.assertIn(f"scope:aov_adv = flag:{key}", body)

    def test_ui_loc(self):
        keys = loc_keys(CONTENT_LOC)
        for k in ("AOV_ADV_REQ_ELIGIBLE", "AOV_ADV_REQ_NOT_COMMITTED", "AOV_ADV_REQ_NOT_DONE",
                  "AOV_ADV_IN_PROGRESS_ELSEWHERE", "AOV_ADV_START", "AOV_ADV_ABANDON", "AOV_ADV_ABANDON_TT",
                  "AOV_ADV_PROGRESS", "AOV_ADV_COMPLETE", "AOV_ADV_ENDS_STUDY",
                  "AOV_MAGIC_TAB_ADVANCEMENTS", "AOV_MAGIC_TAB_SPELLS", "aov_advancement.1.t", "aov_advancement.1.a"):
            self.assertIn(k, keys)
        for key in ADV_KEYS:
            self.assertIn(f"aov_advancement.1.desc.{key}", keys)


def level_effect(key, n):
    return block(read(LEVEL_EFFECTS), f"aov_adv_{key}_{n}_effect")


class MagicalFortressTests(unittest.TestCase):
    def test_levels_refresh_wards(self):
        for n in (1, 2, 3):
            self.assertIn("aov_adv_wards_refresh = yes", level_effect("magical_fortress", n))

    def test_wards_refresh_yearly(self):
        oa = read(ON_ACTIONS)
        self.assertIn("aov_adv_wards_yearly", block(oa, "yearly_playable_pulse"))
        y = block(oa, "aov_adv_wards_yearly")
        self.assertIn("aov_adv_magical_fortress_level >= 1", y)
        self.assertIn("aov_adv_eligible = yes", y)
        self.assertIn("aov_adv_wards_refresh = yes", y)

    def test_level_1_capital_only(self):
        r = block(read(LEVEL_EFFECTS), "aov_adv_wards_refresh")
        first = re.search(r"limit = \{ aov_adv_magical_fortress_level = 1 \}(.*?)\n\t\}", r, re.S).group(1)
        self.assertIn("capital_county = {", first)
        self.assertNotIn("every_held_county", first)

    def test_wards_lapse(self):
        r = block(read(LEVEL_EFFECTS), "aov_adv_wards_refresh")
        adds = re.findall(r"add_county_modifier = \{[^}]*\}", r)
        self.assertTrue(adds)
        for a in adds:
            self.assertIn("days = aov_adv_ward_days", a)

    def test_ward_modifiers(self):
        mods = read(MODIFIERS)
        for m in ("aov_ward_1", "aov_ward_3"):
            body = block(mods, m)
            for key in ("development_growth_factor", "fort_level", "garrison_size", "hostile_raid_time"):
                self.assertIn(key, body, m)
        self.assertIn("defender_holding_advantage", block(mods, "aov_ward_capital"))
        self.assertIn("aov_adv_ward_days", read(TUNING))


MAA = "common/men_at_arms_types/aov_advancement_maa_types.txt"
HOSTS = {"angels": "heavy_infantry", "eldritch": "heavy_cavalry", "devils": "archers"}


class SummonExtraplanarsTests(unittest.TestCase):
    def test_level_1_chooses_host(self):
        self.assertIn("trigger_event = aov_advancement.10", level_effect("summon_extraplanars", 1))

    def test_host_choice_event_three_options(self):
        ev = block(read(EVENTS), "aov_advancement.10")
        self.assertEqual(ev.count("\toption = {"), 3)
        for h in HOSTS:
            self.assertIn(f"set_variable = {{ name = aov_adv_host value = flag:{h} }}", ev)

    def test_maa_need_level_and_host(self):
        maa = read(MAA)
        for h, base in HOSTS.items():
            body = block(maa, f"aov_host_{h}")
            self.assertIn(f"type = {base}", body)
            self.assertIn("aov_adv_summon_extraplanars_level >= 1", body)
            self.assertIn(f"var:aov_adv_host = flag:{h}", body)

    def test_level_modifiers_use_base_type(self):
        mods = read(MODIFIERS)
        for h, base in HOSTS.items():
            self.assertIn(f"{base}_damage_mult", block(mods, f"aov_host_{h}_2"))
            three = block(mods, f"aov_host_{h}_3")
            self.assertIn(f"{base}_toughness_mult", three)
            self.assertIn(f"{base}_max_size_add = 1", three)

    def test_levels_2_3_add_the_hosts_modifier(self):
        for n in (2, 3):
            eff = level_effect("summon_extraplanars", n)
            for h in HOSTS:
                self.assertIn(f"var:aov_adv_host = flag:{h}", eff)
                self.assertIn(f"add_character_modifier = {{ modifier = aov_host_{h}_{n} }}", eff)


class OrbOfOmniscienceTests(unittest.TestCase):
    def test_orb_created_non_decaying(self):
        eff = level_effect("orb_of_omniscience", 1)
        self.assertIn("create_artifact = {", eff)
        self.assertIn("type = scientific_apparatus", eff)
        self.assertIn("decaying = no", eff)
        self.assertIn("modifier = aov_orb_1", eff)
        self.assertIn("set_variable = { name = aov_adv_orb value = scope:aov_orb }", eff)

    def test_upgrades_guard_missing_orb(self):
        for n in (2, 3):
            eff = level_effect("orb_of_omniscience", n)
            self.assertLess(eff.index("exists = var:aov_adv_orb"), eff.index(f"add_artifact_modifier = aov_orb_{n}"))

    def test_orb_modifiers(self):
        mods = read(MODIFIERS)
        one = block(mods, "aov_orb_1")
        self.assertIn("learning = ", one)
        self.assertIn("monthly_lifestyle_xp_gain_mult = ", one)
        self.assertIn("enemy_scheme_secrecy_add = -", block(mods, "aov_orb_2"))
        block(mods, "aov_orb_3")

    def test_scry_reveals_more_with_the_orb(self):
        scry = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_scry_reveal")
        self.assertIn("aov_adv_orb_of_omniscience_level >= 2", scry)

    def test_foresight_and_fortune_last_longer(self):
        vals = read("common/script_values/aov_spell_values.txt")
        for k in ("foresight", "manipulated_fortune"):
            self.assertIn("multiply = aov_adv_orb_spell_years_mult", block(vals, f"aov_spell_{k}_years"))
        self.assertNotIn("aov_adv_orb_spell_years_mult", block(vals, "aov_spell_guidance_years"))
        self.assertIn("aov_adv_orb_of_omniscience_level >= 3", block(read(TUNING), "aov_adv_orb_spell_years_mult"))


KINDS = {"weapon": "sword", "armor": "armor_plate", "crown": "helmet", "regalia": "regalia", "trinket": "miscellaneous"}


class EnchantedArtifactTests(unittest.TestCase):
    def test_one_artifact_per_lifetime(self):
        cond = block(read(CONDITIONS), "aov_adv_can_craft_enchanted_artifact")
        self.assertIn("NOT = { has_variable = aov_adv_enchanted_crafted }", cond)
        store = block(read(LEVEL_EFFECTS), "aov_adv_enchanted_store")
        self.assertIn("set_variable = { name = aov_adv_enchanted_crafted value = yes }", store)
        self.assertIn("set_variable = { name = aov_adv_enchanted_artifact value = scope:newly_created_artifact }", store)

    def test_owns_guarded(self):
        cond = block(read(CONDITIONS), "aov_adv_owns_enchanted_artifact")
        self.assertLess(cond.index("exists = var:aov_adv_enchanted_artifact"),
                        cond.index("var:aov_adv_enchanted_artifact = {"))
        self.assertIn("artifact_owner = { this = root }", cond)

    def test_level_1_chooses_type(self):
        self.assertIn("trigger_event = aov_advancement.20", level_effect("enchanted_artifact", 1))
        ev = block(read(EVENTS), "aov_advancement.20")
        self.assertEqual(ev.count("\toption = {"), 5)
        for kind in KINDS:
            self.assertIn(f"aov_adv_enchanted_create_{kind} = yes", ev)

    def test_creation_per_kind(self):
        eff = read(LEVEL_EFFECTS)
        for kind, art_type in KINDS.items():
            body = block(eff, f"aov_adv_enchanted_create_{kind}")
            self.assertIn(f"type = {art_type}", body)
            self.assertIn("decaying = no", body)
            self.assertIn(f"modifier = aov_enchanted_{kind}_1", body)
            self.assertIn(f"aov_adv_enchanted_store = {{ KIND = {kind} }}", body)

    def test_five_kinds_three_levels(self):
        mods = read(MODIFIERS)
        for kind in KINDS:
            for n in (1, 2, 3):
                block(mods, f"aov_enchanted_{kind}_{n}")

    def test_levels_2_3_strengthen_the_same_artifact(self):
        for n in (2, 3):
            eff = level_effect("enchanted_artifact", n)
            self.assertIn("aov_adv_owns_enchanted_artifact = yes", eff)
            for kind in KINDS:
                self.assertIn(f"var:aov_adv_enchanted_type = flag:{kind}", eff)
                self.assertIn(f"add_artifact_modifier = aov_enchanted_{kind}_{n}", eff)

    def test_trinket_feeds_magic(self):
        life = read("common/script_values/aov_magic_lifestyle_values.txt")
        self.assertIn("add = aov_adv_trinket_mana_bonus", block(life, "aov_mana_max_bonus"))
        for c in SCHOOLS:
            self.assertIn("add = aov_adv_trinket_cost_cut", block(life, f"aov_cost_cut_{c}"))
        tuning = read(TUNING)
        for v in ("aov_adv_trinket_mana_bonus", "aov_adv_trinket_cost_cut"):
            body = block(tuning, v)
            self.assertIn("aov_adv_owns_enchanted_artifact = yes", body)
            self.assertIn("var:aov_adv_enchanted_type = flag:trinket", body)


ACADEMY = "common/buildings/aov_battlemage_academy.txt"
DECISIONS = "common/decisions/aov_battlemage_decisions.txt"
TEMPLATES = "common/scripted_character_templates/aov_advancement_templates.txt"


class BattlemageAcademyTests(unittest.TestCase):
    def test_holdings_list_academy(self):
        holdings = read("common/holdings/00_holdings.txt")
        for h in ("castle_holding", "city_holding"):
            self.assertIn("battlemage_academy_01", block(holdings, h))

    def test_building_tiers_need_level(self):
        b = read(ACADEMY)
        for n in (1, 2, 3):
            body = block(b, f"battlemage_academy_0{n}")
            self.assertIn(f"aov_adv_battlemage_academy_level >= {n}", body)
            self.assertIn("flag = battlemage_academy", body)
            if n < 3:
                self.assertIn(f"next_building = battlemage_academy_0{n + 1}", body)
        self.assertIn("battlemage_academy_none_in_domain_trigger = yes", block(b, "battlemage_academy_01"))

    def test_tier_trigger(self):
        t = block(read(CONDITIONS), "aov_battlemage_academy_tier_at_least")
        self.assertIn("has_building_or_higher = battlemage_academy_0$TIER$", t)

    def test_decision_cooldown_and_recruit(self):
        d = block(read(DECISIONS), "aov_recruit_battlemage_decision")
        self.assertIn("cooldown = { years = 5 }", d)
        self.assertIn("aov_battlemage_academy_tier_at_least = { TIER = 1 }", d)
        self.assertIn("aov_recruit_battlemage = yes", d)

    def test_recruits_scale_with_tier(self):
        r = block(read(LEVEL_EFFECTS), "aov_recruit_battlemage")
        temps = read(TEMPLATES)
        for n in (1, 2, 3):
            self.assertIn(f"template = aov_battlemage_template_{n}", r)
            block(temps, f"aov_battlemage_template_{n}")
        self.assertIn("add_trait = magical_affinity_1", r)
        self.assertIn("aov_school_evocation_progress", r)
        self.assertIn("add_courtier = scope:aov_battlemage", r)

    def test_tier_3_recruits_get_advantage(self):
        r = block(read(LEVEL_EFFECTS), "aov_recruit_battlemage")
        self.assertIn("modifier = aov_battlemage_trained", r)
        self.assertIn("advantage = ", block(read(MODIFIERS), "aov_battlemage_trained"))

    def test_battlemage_maa_need_tier(self):
        maa = read(MAA)
        two = block(maa, "aov_battlemages")
        self.assertIn("aov_battlemage_academy_tier_at_least = { TIER = 2 }", two)
        self.assertIn("NOT = { aov_battlemage_academy_tier_at_least = { TIER = 3 } }", two)
        self.assertIn("aov_battlemage_academy_tier_at_least = { TIER = 3 }", block(maa, "aov_battlemages_3"))


SKILLS = ("diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess")


class MirrorImageTests(unittest.TestCase):
    def test_skills_rise_one_per_level(self):
        mods = read(MODIFIERS)
        for n in (1, 2, 3):
            body = block(mods, f"aov_mirror_image_{n}")
            for s in SKILLS[:5]:
                self.assertIn(f"\t{s} = 1\n", body + "\n")
            self.assertRegex(body, r"\tprowess = [1-9]")
            eff = level_effect("mirror_image", n)
            self.assertIn(f"add_character_modifier = {{ modifier = aov_mirror_image_{n} }}", eff)
            self.assertNotIn("remove_character_modifier", eff)

    def test_level_extras(self):
        mods = read(MODIFIERS)
        self.assertIn("enemy_hostile_scheme_success_chance_add = -", block(mods, "aov_mirror_image_1"))
        three = block(mods, "aov_mirror_image_3")
        self.assertIn("general_opinion = ", three)
        self.assertIn("owned_personal_scheme_success_chance_add = ", three)

    def test_body_double_on_imprison(self):
        oa = read(ON_ACTIONS)
        self.assertIn("aov_adv_body_double", block(oa, "on_imprison"))
        bd = block(oa, "aov_adv_body_double")
        self.assertIn("aov_adv_mirror_image_level >= 2", bd)
        self.assertIn("chance = aov_adv_body_double_chance", bd)
        self.assertIn("id = aov_advancement.50", bd)
        ev = block(read(EVENTS), "aov_advancement.50")
        self.assertLess(ev.index("is_imprisoned = yes"), ev.index("release_from_prison = yes"))

    def test_illusion_cost_cut_reads_level(self):
        life = read("common/script_values/aov_magic_lifestyle_values.txt")
        self.assertIn("add = aov_adv_mirror_image_cost_cut", block(life, "aov_cost_cut_illusion"))
        self.assertIn("aov_adv_mirror_image_level >= 3", block(read(TUNING), "aov_adv_mirror_image_cost_cut"))


class LichdomTests(unittest.TestCase):
    def test_level_3_conditions(self):
        cond = read(CONDITIONS)
        lich = block(cond, "aov_adv_can_become_lich")
        for t in ("lich", "incapable", "vampire", "immortal", "lycanthrope"):
            self.assertIn(f"has_trait = {t}", lich)
        self.assertIn("any_prisoner = {", block(cond, "aov_adv_has_sacrifice"))

    def test_phylactery_guarded(self):
        own = block(read(CONDITIONS), "aov_adv_owns_phylactery")
        self.assertLess(own.index("exists = var:aov_adv_phylactery"), own.index("var:aov_adv_phylactery = {"))
        self.assertIn("artifact_owner = { this = root }", own)

    def test_crime_rolls_dark_magic(self):
        eff = level_effect("lichdom", 1)
        self.assertIn("aov_dark_magic_roll = yes", eff)
        self.assertIn("modifier = aov_lichdom_crime", eff)

    def test_level_2_crafts_phylactery(self):
        eff = level_effect("lichdom", 2)
        self.assertIn("create_artifact = {", eff)
        self.assertIn("decaying = no", eff)
        self.assertIn("set_variable = { name = aov_adv_phylactery value = scope:aov_phylactery }", eff)

    def test_ritual_grants_lich(self):
        eff = level_effect("lichdom", 3)
        self.assertIn("trigger_event = aov_advancement.40", eff)
        ritual = block(read(LEVEL_EFFECTS), "aov_adv_lich_ritual")
        self.assertIn("add_trait = lich", ritual)
        self.assertIn("death = {", ritual)
        ev = block(read(EVENTS), "aov_advancement.40")
        self.assertIn("ordered_prisoner = {", ev)
        self.assertIn("aov_adv_lich_ritual = { VICTIM = scope:aov_sacrifice_1 }", ev)

    def test_lost_phylactery_resets_to_level_1(self):
        check = block(read(LEVEL_EFFECTS), "aov_adv_lichdom_check")
        self.assertIn("aov_adv_owns_phylactery = no", check)
        self.assertIn("set_variable = { name = aov_adv_lichdom_lvl value = 1 }", check)
        self.assertIn("aov_adv_abandon = yes", check)
        self.assertIn("NOT = { has_trait = lich }", check)
        self.assertIn("aov_adv_lichdom_check = yes", block(read(ON_ACTIONS), "aov_adv_quarterly_pulse"))


class HomunculusTests(unittest.TestCase):
    def test_homunculus_trait_cannot_inherit_or_breed(self):
        trait = block(read("common/traits/aov_homunculus_traits.txt"), "aov_homunculus")
        for line in ("inheritance_blocker = all", "claim_inheritance_blocker = all", "can_have_children = no",
                     "shown_in_ruler_designer = no"):
            self.assertIn(line, trait)

    def test_level_1_creates_a_courtier(self):
        create = block(read(LEVEL_EFFECTS), "aov_adv_homunculus_create")
        self.assertIn("template = aov_homunculus_template", create)
        self.assertIn("add_trait = aov_homunculus", create)
        self.assertIn("modifier = aov_homunculus_maker_opinion", create)
        self.assertIn("add_courtier = scope:aov_homunculus", create)
        self.assertIn("set_variable = { name = aov_adv_homunculus value = scope:aov_homunculus }", create)
        self.assertIn("aov_adv_homunculus_create = yes", level_effect("homunculus", 1))
        block(read(TEMPLATES), "aov_homunculus_template")

    def test_level_2_recreates_if_dead(self):
        eff = level_effect("homunculus", 2)
        self.assertIn("is_alive = no", eff)
        self.assertLess(eff.index("aov_adv_homunculus_create = yes"), eff.index("trigger_event = aov_advancement.30"))
        ev = block(read(EVENTS), "aov_advancement.30")
        for s in SKILLS[:5]:
            self.assertIn(f"add_{s}_skill = aov_adv_homunculus_skill", ev)

    def test_labour_modifier(self):
        self.assertIn("add_character_modifier = { modifier = aov_homunculus_labour }", level_effect("homunculus", 3))
        labour = block(read(MODIFIERS), "aov_homunculus_labour")
        self.assertIn("build_speed = ", labour)
        self.assertIn("development_growth_factor = ", labour)


class AiTests(unittest.TestCase):
    def test_ai_pick_only_ai_uncommitted(self):
        oa = read(ON_ACTIONS)
        self.assertIn("aov_adv_ai_yearly", block(oa, "yearly_playable_pulse"))
        y = block(oa, "aov_adv_ai_yearly")
        for line in ("is_ai = yes", "aov_adv_eligible = yes", "NOT = { aov_adv_is_committed = yes }",
                     "chance = aov_adv_ai_chance", "aov_adv_ai_pick = yes"):
            self.assertIn(line, y)
        self.assertRegex(read(TUNING), r"(?m)^aov_adv_ai_chance = \d+")


class WindowTests(unittest.TestCase):
    def window(self):
        return read("gui/aov_window_magic.gui")

    def test_two_tabs_below_school_row(self):
        w = self.window()
        self.assertLess(w.index('name = "aov_magic_school_tabs"'), w.index("AOV_MAGIC_TAB_ADVANCEMENTS"))
        self.assertIn("GetVariableSystem.Clear( 'aov_magic_tab' )", w)
        self.assertIn("GetVariableSystem.Set( 'aov_magic_tab', 'spells' )", w)

    def test_each_school_has_both_pages(self):
        w = self.window()
        for c in SCHOOLS:
            self.assertIn(f"aov_advancement_{c} = {{", w)
            self.assertIn(f"aov_magic_school_{c} = {{", w)

    def test_pages_gated_by_tab(self):
        w = self.window()
        for c in SCHOOLS:
            adv = re.search(rf"aov_advancement_{c} = \{{\n\s*visible = \"(.*?)\"", w).group(1)
            spells = re.search(rf"aov_magic_school_{c} = \{{\n\s*visible = \"(.*?)\"", w).group(1)
            self.assertIn("Not( GetVariableSystem.Exists( 'aov_magic_tab' ) )", adv)
            self.assertIn("GetVariableSystem.HasValue( 'aov_magic_tab', 'spells' )", spells)

    def test_study_not_at_top_level(self):
        self.assertNotIn("AOV_MAGIC_STUDYING", self.window())

    def test_balanced(self):
        w = self.window()
        self.assertEqual(w.count("{"), w.count("}"))


if __name__ == "__main__":
    unittest.main()
