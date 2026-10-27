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
        # A committed character who lost their affinity still ticks, so the commitment is abandoned
        self.assertRegex(pulse, r"OR = \{\s*aov_is_mage = yes\s*aov_adv_is_committed = yes\s*\}")
        self.assertIn("aov_adv_quarterly = yes", pulse)

    def test_losing_all_land_abandons(self):
        """A mage who loses their last title stops getting quarterly_playable_pulse, so on_title_lost checks."""
        oa = read(ON_ACTIONS)
        self.assertIn("aov_adv_on_title_lost", block(oa, "on_title_lost"))
        lost = block(oa, "aov_adv_on_title_lost")
        self.assertIn("aov_adv_is_committed = yes", lost)
        self.assertIn("id = aov_advancement.60", lost)
        ev = block(read(EVENTS), "aov_advancement.60")
        self.assertIn("hidden = yes", ev)
        self.assertLess(ev.index("aov_adv_eligible = no"), ev.index("aov_adv_abandon = yes"))

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
                  "AOV_ADV_START", "AOV_ADV_ABANDON", "AOV_ADV_ABANDON_TT",
                  "AOV_ADV_PROGRESS", "AOV_ADV_COMPLETE", "AOV_ADV_LEVEL_DONE", "AOV_ADV_LEVEL_NEXT", "AOV_ADV_LEVEL_LOCKED",
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

    def test_hosts_are_free(self):
        """Summoned hosts cost nothing to recruit, to upgrade (adding regiments uses buy_cost) or to maintain."""
        maa = read(MAA)
        for h in HOSTS:
            body = block(maa, f"aov_host_{h}")
            for line in ("buy_cost = { gold = 0 }", "low_maintenance_cost = { gold = 0 }",
                         "high_maintenance_cost = { gold = 0 }", "provision_cost = 0"):
                self.assertIn(line, body, h)

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
            self.assertLess(eff.index("aov_adv_owns_orb = yes"), eff.index(f"add_artifact_modifier = aov_orb_{n}"))

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


KINDS = {"weapon": "sword", "armor": "armor_plate", "crown": "helmet", "regalia": "regalia_simple", "trinket": "miscellaneous"}


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

    def test_regalia_needs_no_missing_features(self):
        """Anbennar comments out every regalia_clothes feature, which the 'regalia' type requires (error.log: create_artifact
        'Failed to pick feature for group regalia_clothes'); 'regalia_simple' has the same slot and no required features."""
        body = block(read(LEVEL_EFFECTS), "aov_adv_enchanted_create_regalia")
        self.assertIn("type = regalia_simple", body)

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

    def test_recruits_can_lead_armies(self):
        # The game's soldier gender chance: a gender the recruiter's faith and culture allow as knights and commanders.
        temps = read(TEMPLATES)
        for n in (1, 2, 3):
            self.assertRegex(block(temps, f"aov_battlemage_template_{n}"),
                             r"gender_female_chance = root_soldier_female_chance\b")

    def test_recruit_shows_the_commander(self):
        r = block(read(LEVEL_EFFECTS), "aov_recruit_battlemage")
        self.assertLess(r.index("add_courtier = scope:aov_battlemage"), r.index("trigger_event = aov_advancement.70"))
        ev = block(read(EVENTS), "aov_advancement.70")
        self.assertRegex(ev, r"right_portrait = \{\s*character = scope:aov_battlemage")
        loc = read(CONTENT_LOC)
        desc = re.search(r'aov_advancement\.70\.desc: "(.*)"', loc).group(1)
        self.assertIn("[aov_battlemage.GetFullName]", desc)

    def test_decision_description_explains_the_tiers(self):
        desc = re.search(r'aov_recruit_battlemage_decision_desc: "(.*)"', read(CONTENT_LOC)).group(1)
        for words in ("Battlemage Academy", "Battlemage College", "Grand Battlemage Academy", "Magical Affinity",
                      "Evocation", "advantage"):
            self.assertIn(words, desc)

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


LICH_EVENTS = "events/aov_lichdom_events.txt"
LICH_LOC = "localization/english/aov_lichdom_l_english.yml"
# (working level, step) -> the step's event, after EU4's magic_project_lichdom ids
LICH_STEPS = {(1, 1): 2, (1, 2): 3, (1, 3): 4, (2, 1): 5, (2, 2): 6, (2, 3): 7, (3, 1): 8, (3, 2): 9, (3, 3): 20}


def event_ids(text):
    return re.findall(r"^aov_lichdom\.(\d+) = \{", text, re.M)


class LichdomTests(unittest.TestCase):
    def test_level_3_conditions(self):
        cond = read(CONDITIONS)
        lich = block(cond, "aov_adv_can_become_lich")
        for t in ("lich", "incapable", "vampire", "immortal", "lycanthrope"):
            self.assertIn(f"has_trait = {t}", lich)
        # The lich dies by their own potion: no prisoner is sacrificed
        self.assertNotRegex(cond, r"(?m)^aov_adv_has_sacrifice = \{")
        eff = read(LEVEL_EFFECTS)
        self.assertNotIn("prisoner", eff[eff.index("# Necromancy: Lichdom"):eff.index("# Transmutation: Homunculus")])

    def test_phylactery_guarded(self):
        own = block(read(CONDITIONS), "aov_adv_owns_phylactery")
        self.assertLess(own.index("exists = var:aov_adv_phylactery"), own.index("var:aov_adv_phylactery = {"))
        self.assertIn("artifact_owner = { this = root }", own)

    def test_level_1_crafts_the_chosen_phylactery(self):
        eff = level_effect("lichdom", 1)
        self.assertEqual(eff.count("create_artifact = {"), 2)
        self.assertEqual(eff.count("decaying = no"), 2)
        self.assertIn("var:aov_lichdom_vessel = flag:box", eff)
        self.assertIn("visuals = small_box", eff)
        self.assertIn("visuals = necklace", eff)
        self.assertIn("set_variable = { name = aov_adv_phylactery value = scope:aov_phylactery }", eff)
        ev = block(read(LICH_EVENTS), "aov_lichdom.2")
        for vessel in ("amulet", "box"):
            self.assertIn(f"set_variable = {{ name = aov_lichdom_vessel value = flag:{vessel} }}", ev)

    def test_level_2_brews_the_potion(self):
        eff = level_effect("lichdom", 2)
        self.assertLess(eff.index("aov_adv_owns_phylactery = no"), eff.index("modifier = aov_lichdom_potion"))
        self.assertIn("aov_dark_magic_roll = yes", eff)
        block(read(MODIFIERS), "aov_lichdom_potion")

    def test_ritual_ends_in_the_drink(self):
        eff = level_effect("lichdom", 3)
        self.assertIn(FAILED, eff)
        self.assertIn("trigger_event = aov_lichdom.10", eff)
        drink = block(read(LICH_EVENTS), "aov_lichdom.10")
        self.assertIn("aov_adv_lich_ascend = yes", drink)
        self.assertIn("trigger_event = aov_lichdom.11", drink)

    def test_ascension_outs_an_evil_mage_whatever_the_faith(self):
        asc = block(read(LEVEL_EFFECTS), "aov_adv_lich_ascend")
        self.assertIn("add_trait = lich", asc)
        self.assertIn("gain_forbidden_magic_trait_effect = yes", asc)
        self.assertNotIn("witchcraft", asc)
        self.assertNotIn("random", asc)
        self.assertIn("remove_character_modifier = aov_lichdom_potion", asc)
        self.assertNotIn("death", asc)

    def test_three_steps_per_level(self):
        nxt = block(read(LEVEL_EFFECTS), "aov_adv_lichdom_next_step")
        self.assertEqual(sorted(int(n) for n in re.findall(r"trigger_event = aov_lichdom\.(\d+)", nxt)),
                         sorted(LICH_STEPS.values()))
        ids = event_ids(read(LICH_EVENTS))
        for n in list(LICH_STEPS.values()) + [10, 11]:
            self.assertIn(str(n), ids)
        start = block(read(LEVEL_EFFECTS), "aov_adv_lichdom_on_start")
        self.assertLess(start.index("set_variable = { name = aov_lichdom_step value = 0 }"),
                        start.index("aov_adv_lichdom_next_step = yes"))
        pulse = block(read(ON_ACTIONS), "aov_adv_quarterly_pulse")
        self.assertLess(pulse.index("aov_adv_quarterly = yes"), pulse.index("aov_adv_lichdom_steps = yes"))
        steps = block(read(LEVEL_EFFECTS), "aov_adv_lichdom_steps")
        for line in ("aov_adv_working_on = { KEY = lichdom }", "var:aov_lichdom_step < 3",
                     "var:aov_adv_progress >= aov_lichdom_next_step_at"):
            self.assertIn(line, steps)
        self.assertIn("divide = 3", block(read(TUNING), "aov_lichdom_next_step_at"))

    def test_faster_choices_leave_a_quarter_per_step(self):
        hasten = block(read(LEVEL_EFFECTS), "aov_adv_lichdom_hasten")
        self.assertIn("clamp_variable = { name = aov_adv_progress max = aov_lichdom_progress_cap }", hasten)
        self.assertIn("aov_adv_working_on = { KEY = lichdom }", hasten)
        cap = block(read(TUNING), "aov_lichdom_progress_cap")
        for line in ("value = 4", "subtract = var:aov_lichdom_step", "multiply = -3", "add = aov_adv_months_needed"):
            self.assertIn(line, cap)
        for speed in ("fast", "faster"):
            self.assertRegex(read(TUNING), rf"(?m)^aov_lichdom_months_{speed} = \d+")
            self.assertIn(f"aov_lichdom_hasten_{speed}_tt", loc_keys(LICH_LOC))

    def test_every_step_can_back_out(self):
        ev = read(LICH_EVENTS)
        for n in (2, 3, 4, 5, 6, 7, 8, 9):
            self.assertIn("aov_adv_lichdom_back_out = yes", block(ev, f"aov_lichdom.{n}"), n)
        self.assertIn("aov_adv_abandon = yes", block(ev, "aov_lichdom.20"))
        back = block(read(LEVEL_EFFECTS), "aov_adv_lichdom_back_out")
        self.assertLess(back.index("add_prestige = aov_lichdom_back_out_prestige"), back.index("aov_adv_abandon = yes"))

    def test_each_step_keeps_an_ungated_choice(self):
        """Mana and school-level choices are gated; every step keeps a choice anyone can take."""
        ev = read(LICH_EVENTS)
        for n in LICH_STEPS.values():
            options = block(ev, f"aov_lichdom.{n}").split("\toption = {")[1:]
            self.assertTrue(any("trigger = " not in o for o in options), n)
            for o in options:
                if "aov_mana_spend" in o:
                    self.assertIn("aov_mana >= aov_lichdom_mana", o, n)

    def test_heir_choice_is_optional(self):
        ev = block(read(LICH_EVENTS), "aov_lichdom.7")
        self.assertIn("primary_heir = { save_scope_as = aov_lichdom_heir }", ev)
        heir = next(o for o in ev.split("\toption = {")[1:] if "scope:aov_lichdom_heir = {" in o)
        self.assertIn("trigger = { exists = scope:aov_lichdom_heir }", heir)

    def test_step_loc(self):
        keys = loc_keys(LICH_LOC)
        used = set(re.findall(r"(?m)^\t+(?:title|desc|name|custom_tooltip) = (aov_lichdom[\w.]+)", read(LICH_EVENTS)))
        used |= set(re.findall(r"custom_tooltip = (aov_lichdom[\w.$]+)", read(LEVEL_EFFECTS)))
        used = {u.replace("_$SPEED$", "_fast") for u in used}
        self.assertEqual(sorted(used - keys), [])

    def test_lost_phylactery_starts_over(self):
        check = block(read(LEVEL_EFFECTS), "aov_adv_lichdom_check")
        self.assertIn("aov_adv_owns_phylactery = no", check)
        self.assertIn("aov_adv_lichdom_level >= 1", check)
        self.assertIn("set_variable = { name = aov_adv_lichdom_lvl value = 0 }", check)
        self.assertIn("remove_character_modifier = aov_lichdom_potion", check)
        self.assertIn("aov_adv_abandon = yes", check)
        self.assertIn("NOT = { has_trait = lich }", check)
        self.assertIn("aov_adv_lichdom_check = yes", block(read(ON_ACTIONS), "aov_adv_quarterly_pulse"))


LICH_GENES = "common/genes/aov_lich_genes.txt"
LICH_PORTRAIT = "gfx/portraits/portrait_modifiers/aov_lich.txt"
LICH_ACCESSORIES = "gfx/portraits/accessories/aov_lich.txt"
LICH_ASSET = "gfx/models/portraits/aov_lich/aov_lich.asset"
GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
VANILLA_PATTERNS = "gfx/portraits/accessory_variations/textures/patterns/"
LICH_CLOTHES_ASSET = "gfx/models/portraits/aov_lich/clothes/aov_lich_clothes.asset"
LICH_EYES_ASSET = "gfx/models/portraits/aov_lich/eyes/aov_lich_eyes.asset"
LICH_EYE_COLOURS = ("blue", "gold", "green", "grey", "pink", "purple", "red", "teal", "white")
LICH_VARIATIONS = "gfx/portraits/accessory_variations/aov_lich.txt"


class LichPortraitTests(unittest.TestCase):
    """A Lich is Godherja's skeleton in Godherja's lich clothes (imported once, names prefixed aov_)."""

    def test_modifier_follows_the_lich_trait(self):
        mod = read(LICH_PORTRAIT)
        self.assertRegex(mod, r"exists = this\s*has_trait = lich")
        for gene, template in (("aov_lich_flesh", "aov_lich_flesh_hidden"), ("aov_lich_head", "aov_lich_skull"),
                               ("aov_lich_body", "aov_lich_bones"), ("aov_lich_eyes", "aov_lich_gem_eyes"),
                               ("eye_accessory", "no_eyes"), ("teeth_accessory", "no_teeth")):
            self.assertRegex(mod, rf"gene = {gene}\s*template = {template}")
        self.assertNotIn("gene = legwear", mod)

    def test_lich_clothes(self):
        mod = read(LICH_PORTRAIT)
        outfit = block(mod, "aov_lich_outfit")
        self.assertRegex(outfit, r"usage = game\s*priority = 100")

        def item(text, name):
            return re.search(rf"^\t{name} = \{{\n(.*?)\n^\t\}}", text, re.M | re.S).group(1)

        for k in range(1, 7):
            robed, armoured = item(outfit, f"aov_lich_outfit_{k}"), item(outfit, f"aov_lich_outfit_{k}_armoured")
            # Vanilla's clothes and cloaks are extra genes added by modifiers: only mode = add hides them
            for gene, template in (("clothes", "no_clothes"), ("cloaks", "no_cloak")):
                self.assertRegex(robed, rf"mode = add\s*gene = {gene}\s*template = {template}")
                self.assertNotIn(f"gene = {gene}", armoured)
            # Robe and hood of one look go together
            self.assertRegex(robed, rf"gene = aov_lich_clothes\s*template = aov_lich_robes_{k}\b")
            for body in (robed, armoured):
                self.assertRegex(body, rf"gene = aov_lich_hood\s*template = aov_lich_hood_{k}\b")
                self.assertIn("has_trait = lich", body)
                # Below 100, or the first valid look would always win
                self.assertIn("add = 10 ", body)
            self.assertIn("portrait_wear_armor_trigger = no", robed)
            self.assertIn("portrait_wear_armor_trigger = yes", armoured)
        self.assertNotIn("mode = replace\n\t\t\t\tgene = clothes", mod)
        self.assertRegex(block(mod, "aov_lich_mask"), r"gene = aov_lich_mask\s*template = aov_lich_mask")
        crowns = block(mod, "aov_lich_crown")
        for template, tier in (("aov_lich_king_crown", "highest_held_title_tier = tier_kingdom"),
                               ("aov_archlich_crown", "highest_held_title_tier >= tier_empire")):
            crown = item(crowns, template)
            self.assertRegex(crown, r"mode = add\s*gene = headgear\s*template = no_headgear")
            self.assertIn(tier, crown)
        for group in ("aov_lich_mask", "aov_lich_crown"):
            self.assertRegex(block(mod, group), r"usage = game\s*priority = 100")
            self.assertIn("has_trait = lich", block(mod, group))

    def test_lich_eyes_random_and_in_barbershop(self):
        mod = read(LICH_PORTRAIT)
        group = block(mod, "aov_lich_eyes")

        def item(name):
            return re.search(rf"^\t{name} = \{{\n(.*?)\n^\t\}}", group, re.M | re.S).group(1)

        # usage both: picked at random in game, chosen in the barbershop
        self.assertRegex(group, r"usage = both\s*interface_position = \d+\s*priority = 100")
        self.assertNotIn("gene = aov_lich_eyes", block(mod, "aov_lich"))
        loc = read("localization/english/aov_lichdom_l_english.yml")
        self.assertIn(" PORTRAIT_MODIFIER_aov_lich_eyes:", loc)
        for colour in LICH_EYE_COLOURS:
            body = item(f"aov_lich_eyes_{colour}")
            self.assertRegex(body, rf"gene = aov_lich_eyes\s*template = aov_lich_glowing_eyes_{colour}\b")
            self.assertIn("is_valid_custom = { has_trait = lich }", body)
            self.assertIn("add = 10", body)
            self.assertIn(f" PORTRAIT_MODIFIER_aov_lich_eyes_aov_lich_eyes_{colour}:", loc)
        # Gems and empty sockets are barbershop choices only
        for name in ("gems", "empty"):
            body = item(f"aov_lich_eyes_{name}")
            self.assertIn("add = 0", body)
            self.assertIn(f" PORTRAIT_MODIFIER_aov_lich_eyes_aov_lich_eyes_{name}:", loc)

    def test_lich_eyes_glow_under_anbennars_shader(self):
        """Anbennar's portrait_eye glows from the properties texture's red channel (EMISSIVE_PROPERTIES_RED)."""
        eyes = read(LICH_EYES_ASSET)
        self.assertEqual(eyes.count('shader = "portrait_eye"'), 2 * 2 * len(LICH_EYE_COLOURS))
        for level in (1, 2):
            self.assertIn(f'texture_specular = "aov_lich_eyes_glowing_{level}_properties.dds"', eyes)
        shader = MOD.parent / "anbennar-ck3-dev-master/gfx/FX/jomini/portrait.shader"
        if shader.is_file():
            text = shader.read_text(encoding="utf-8", errors="replace")
            effect = text[text.index("Effect portrait_eye\n"):]
            self.assertIn("EMISSIVE_PROPERTIES_RED", effect[:effect.index("}")])

    def test_lich_looks_match(self):
        """Each look's robe and hood use that look's single-row palette."""
        variations, clothes = read(LICH_VARIATIONS), read(LICH_CLOTHES_ASSET)
        for k in range(1, 7):
            palette = f"color_palette_lich_look_{k}.dds"
            for garment in ("robes", "hood"):
                var = re.search(rf'name = "aov_lich_{garment}_look_{k}"(.*?)\n\}}', variations, re.S).group(1)
                self.assertIn(palette, var)
                self.assertEqual(var.count("pattern = {"), 1)
            for entity in re.findall(rf'name = "(\w+_look_{k}_entity)"', clothes):
                body = clothes[clothes.index(f'name = "{entity}"'):]
                body = body[:body.index("\n}")]
                self.assertRegex(body, rf'variation = "aov_lich_(robes|hood)_look_{k}"')

    def test_new_genes_default_to_nothing(self):
        genes = read(LICH_GENES)
        for gene in ("aov_lich_flesh", "aov_lich_head", "aov_lich_body", "aov_lich_eyes", "aov_lich_clothes",
                     "aov_lich_hood", "aov_lich_mask", "aov_lich_crown"):
            body = genes[genes.index(f"\t{gene} = {{"):]
            first = re.search(r"index = 0\s*(?:visible = no\s*)?male = \{(.*?)\}", body, re.S).group(1)
            self.assertIn(first.strip(), ("", "1 = empty"), gene)
        self.assertIn('attribute = "bs_no_portrait"', genes)
        self.assertIn("female = male", genes[genes.index("aov_lich_flesh_hidden"):])

    def test_accessories_entities_and_files_exist(self):
        genes, acc = read(LICH_GENES), read(LICH_ACCESSORIES)
        skeleton, clothes, eyes = read(LICH_ASSET), read(LICH_CLOTHES_ASSET), read(LICH_EYES_ASSET)
        asset = skeleton + clothes + eyes
        for name in set(re.findall(r"= (aov_(?:male|female)_\w+)", genes)):
            self.assertRegex(acc, rf"(?m)^{name} = \{{", name)
        for entity in set(re.findall(r"entity = (aov_\w+_entity)", acc)):
            self.assertIn(f'name = "{entity}"', asset, entity)
        # Meshes and textures are found next to their .asset
        for text, folder in ((skeleton, "gfx/models/portraits/aov_lich"), (clothes, "gfx/models/portraits/aov_lich/clothes"),
                             (eyes, "gfx/models/portraits/aov_lich/eyes")):
            for f in set(re.findall(r'"(\w+\.(?:mesh|dds))"', text)):
                self.assertTrue((MOD / folder / f).exists(), f)
        variations = read(LICH_VARIATIONS)
        for v in set(re.findall(r'variation = "(\w+)"', asset)):
            self.assertIn(f'name = "{v}"', variations, v)
        for path in set(re.findall(r'"(gfx/[^"]+\.dds)"', asset + variations)):
            # The robes' fabrics are vanilla's
            root = GAME if path.startswith(VANILLA_PATTERNS) else MOD
            self.assertTrue((root / path).exists(), path)
        self.assertNotIn("1MOD", asset + variations)


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


class MaaIconTests(unittest.TestCase):
    def test_every_regiment_names_a_vanilla_icon(self):
        """Without icon = the game looks for gfx/interface/icons/regimenttypes/<key>.dds (tiger: missing-file)."""
        maa = read(MAA)
        expected = {"aov_host_angels": "heavy_infantry", "aov_host_eldritch": "heavy_cavalry",
                    "aov_host_devils": "bowmen", "aov_battlemages": "bowmen", "aov_battlemages_3": "bowmen"}
        for key, icon in expected.items():
            self.assertIn(f"\ticon = {icon}\n", block(maa, key) + "\n", key)
            # With both, the engine ignores icon (error.log: "Found both 'illustration' and 'icon' properties")
            self.assertNotIn("illustration", block(maa, key), key)


FAILED = "save_scope_value_as = { name = aov_adv_own_event value = yes }"


class FailedLevelTests(unittest.TestCase):
    """A paid level that cannot take effect says so and skips the success event (scope:aov_adv_own_event)."""

    def test_ritual_blocked_by_trait_fails_loudly(self):
        eff = level_effect("lichdom", 3)
        self.assertIn("trigger_event = aov_advancement.43", eff)
        block(read(EVENTS), "aov_advancement.43")

    def test_lost_artifact_fails_the_level(self):
        for key, owns in (("enchanted_artifact", "aov_adv_owns_enchanted_artifact"), ("orb_of_omniscience", "aov_adv_owns_orb")):
            for n in (2, 3):
                eff = level_effect(key, n)
                self.assertLess(eff.index(f"{owns} = yes"), eff.index("else = {"))
                self.assertIn(f"aov_adv_artifact_level_failed = {{ KEY = {key} LEVEL = {n - 1} }}", eff)
        failed = block(read(LEVEL_EFFECTS), "aov_adv_artifact_level_failed")
        self.assertIn(FAILED, failed)
        self.assertIn("set_variable = { name = aov_adv_$KEY$_lvl value = $LEVEL$ }", failed)
        self.assertIn("trigger_event = aov_advancement.44", failed)

    def test_lost_artifact_ends_the_commitment(self):
        check = block(read(LEVEL_EFFECTS), "aov_adv_artifact_check")
        for key, owns in (("enchanted_artifact", "aov_adv_owns_enchanted_artifact"), ("orb_of_omniscience", "aov_adv_owns_orb")):
            self.assertIn(f"aov_adv_working_on = {{ KEY = {key} }}", check)
            self.assertIn(f"{owns} = no", check)
        self.assertIn("aov_adv_abandon = yes", check)
        self.assertIn("aov_adv_artifact_check = yes", block(read(ON_ACTIONS), "aov_adv_quarterly_pulse"))
        ev = block(read(EVENTS), "aov_advancement.44")
        for key in ("enchanted_artifact", "orb_of_omniscience"):
            self.assertIn(f"scope:aov_adv = flag:{key}", ev)

    def test_owns_orb_guarded(self):
        own = block(read(CONDITIONS), "aov_adv_owns_orb")
        self.assertLess(own.index("exists = var:aov_adv_orb"), own.index("var:aov_adv_orb = {"))


class LocLineTests(unittest.TestCase):
    def test_every_value_is_on_one_line(self):
        """A real newline inside a loc value splits it and the game drops the rest; line breaks are written \\n."""
        for rel in (CONTENT_LOC, "localization/english/aov_advancements_l_english.yml", "localization/english/aov_magic_l_english.yml",
                    LICH_LOC):
            for n, line in enumerate(read(rel).split("\n")[1:], start=2):
                if line.strip() and not line.lstrip().startswith("#"):
                    self.assertRegex(line, r'^ [A-Za-z0-9_.\-]+:\d? ?".*"\s*(#.*)?$', f"{rel}:{n}")


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
