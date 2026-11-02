"""Static checks on the hand-written research files.

    python -I -m unittest discover -s tools/tests -v
"""

import re
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def block(text, name):
    m = re.search(rf"^{name} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


BUILDINGS = {
    "aov_clockwork_mill_01": ("clockwork_waterwheels", 150, "icon_building_watermills.dds",
                              ["tax_mult = 0.15", "development_growth_factor = 0.1"]),
    "aov_alchemical_distillery_01": ("alchemical_distilleries", 250, "icon_building_breweries.dds",
                                     ["tax_mult = 0.2", "county_opinion_add = 5"]),
    "aov_damestear_foundry_01": ("damestear_foundries", 400, "icon_building_wind_furnaces.dds",
                                 ["tax_mult = 0.25", "development_growth_factor = 0.15", "levy_size = 0.15"]),
}


class ResearchTests(unittest.TestCase):
    def test_invention_buildings(self):
        text = read("common/buildings/aov_invention_buildings.txt")
        self.assertEqual(re.findall(r"^([a-z0-9_]+) = \{", text, re.M), list(BUILDINGS))
        for b, (inv, cost, icon, mods) in BUILDINGS.items():
            body = block(text, b)
            gate = f"scope:holder = {{ aov_invention_{inv}_unlock_ready = yes }}"
            self.assertIn(gate, body.split("can_construct_potential = {")[1].split("\n\t}")[0])
            self.assertIn(gate, body.split("is_enabled = {")[1].split("\n\t}")[0])
            self.assertIn("show_disabled = yes", body)
            self.assertIn(f"cost_gold = {cost}", body)
            self.assertIn(f'type_icon = "{icon}"', body)
            county = body.split("county_modifier = {")[1].split("}")[0]
            for m in mods:
                self.assertIn(m, county)

    def test_invention_building_loc(self):
        text = read("localization/english/aov_artificery_l_english.yml")
        for b in BUILDINGS:
            for key in (f"building_type_{b}", f"building_type_{b}_desc", f"building_{b}", f"building_{b}_desc", f"{b}_effect_desc"):
                self.assertIn(f" {key}:", text)

    def test_complete_research_refunds_when_nothing_discovered(self):
        b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_complete_research")
        self.assertIn("remove_variable = aov_last_discovered", b)
        self.assertRegex(b, r"else = \{\s*add_gold = var:aov_research_paid\s*trigger_event = aov_artificery\.2")

    def test_sponsor_durations(self):
        text = read("common/scripted_effects/aov_artificery_research_effects.txt")
        # Durations are per faction and influence: common/script_values/aov_artificer_faction_values.txt
        for f in ("brillites", "mechanists", "technomancers"):
            self.assertIn(f"aov_artificery_start_research_common = {{ SPONSOR = {f} }}", text)
        self.assertIn("value = aov_research_quarters_$SPONSOR$", text)

    def test_technomancer_category_sgui_rolls_only_once(self):
        text = read("common/scripted_guis/aov_artificery_research_sgui.txt")
        for c in ("economic", "military", "society"):
            b = block(text, f"aov_research_technomancers_{c}_sgui")
            self.assertIn(f"NOT = {{ has_variable = aov_tech_offers_rolled_{c} }}", b)
            self.assertIn(f"aov_inventions_roll_offers_{c} = yes", b)

    def test_cooldowns_cover_six_slots(self):
        b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_start_slot_cooldown")
        for n in range(1, 7):
            self.assertIn(f"set_variable = {{ name = aov_slot_cd_{n} years = 1 }}", b)

    def test_inherit_copies_six_cooldowns(self):
        text = read("common/scripted_effects/aov_artificery_research_effects.txt")
        for n in range(1, 7):
            self.assertIn(f"scope:aov_predecessor = {{ has_variable = aov_slot_cd_{n} }}", text)

    def test_slots_and_tier_gate_values(self):
        text = read("common/script_values/aov_artificery_values.txt")
        slots = block(text, "aov_invention_slots_max")
        self.assertRegex(slots, r"^\tvalue = 4\n")
        self.assertIn("value = 5", slots)
        self.assertIn("value = 6", slots)
        self.assertIn("has_variable = aov_slot_cd_6", block(text, "aov_invention_slots_cooling"))
        self.assertRegex(text, r"(?m)^aov_invention_tier_gate_count = 6$")

    def test_tier_lock_loc_shows_progress(self):
        text = read("localization/english/aov_artificery_l_english.yml")
        for t, prev in ((2, 1), (3, 2)):
            line = next(l for l in text.splitlines() if l.startswith(f" AOV_INV_LOCKED_TIER_{t}_TT:"))
            self.assertIn("ScriptValue('aov_invention_tier_gate_count')", line)
            self.assertIn(f"ScriptValue('aov_inventions_t{prev}_discovered_count')", line)

    def test_tier_banner_requires_discovery_gate(self):
        text = read("common/scripted_guis/aov_artificery_research_sgui.txt")
        for t, prev in ((2, 1), (3, 2)):
            b = block(text, f"aov_inventions_tier_{t}_unlocked_sgui")
            self.assertIn(f"aov_inventions_t{prev}_discovered_count >= aov_invention_tier_gate_count", b)

    def test_tier_banner_loc_shows_both_requirements(self):
        text = read("localization/english/aov_artificery_l_english.yml")
        for t, prev in ((2, 1), (3, 2)):
            line = next(l for l in text.splitlines() if l.startswith(f" AOV_INVENTIONS_TIER_LOCKED_{t}:"))
            self.assertIn("ScriptValue('aov_invention_tier_gate_count')", line)
            self.assertIn(f"ScriptValue('aov_inventions_t{prev}_discovered_count')", line)

    def test_slots_tooltip_says_four_five_six(self):
        text = read("localization/english/aov_artificery_l_english.yml")
        line = next(l for l in text.splitlines() if l.startswith(" AOV_INVENTIONS_SLOTS_TT:"))
        self.assertIn("4 slots in the Early Medieval era, 5 in the High Medieval era and 6 in the Late Medieval era", line)
        self.assertNotIn("3 slots", line)

    def test_on_actions_hook_quarterly_and_death(self):
        text = read("common/on_action/aov_inventions_on_actions.txt")
        self.assertIn("quarterly_playable_pulse = {\n\ton_actions = { aov_artificery_quarterly }", text)
        self.assertIn("on_death = {\n\ton_actions = { aov_artificery_on_death }", text)

    def test_invention_maa_file_and_gates(self):
        text = read("common/men_at_arms_types/aov_invention_maa_types.txt")
        self.assertEqual(re.findall(r"^([a-z_]+) = \{", text, re.M),
                         ["aov_clockwork_repeaters", "aov_war_golems", "aov_gnomish_bombards"])
        for maa, inv in (("aov_clockwork_repeaters", "clockwork_repeaters"), ("aov_war_golems", "war_golems"),
                         ("aov_gnomish_bombards", "gnomish_bombards")):
            b = block(text, maa)
            self.assertIn(f"aov_invention_{inv}_unlock_ready = yes", b)
            self.assertIn("has_enabled_artificer_academy_trigger = yes", b)
        for maa, (dmg, tough) in {"aov_clockwork_repeaters": (55, 23), "aov_war_golems": (45, 31)}.items():
            b = block(text, maa)
            self.assertIn(f"\tdamage = {dmg}\n", b)
            self.assertIn(f"\ttoughness = {tough}\n", b)
        bomb = block(text, "aov_gnomish_bombards")
        for line in ("type = siege_weapon", "siege_tier = 4", "siege_value = 0.75", "toughness = 12", "stack = 10"):
            self.assertIn(line, bomb)

    def test_armored_artificers_reenabled(self):
        text = read("common/men_at_arms_types/zz_aov_gnome_maa_overrides.txt")
        b = block(text, "armored_artificers")
        for line in ("type = gunpowder", "damage = 19", "toughness = 15", "stack = 75",
                     "aov_invention_clockwork_plate_harness_unlock_ready = yes",
                     "has_enabled_artificer_academy_trigger = yes"):
            self.assertIn(line, b)
        self.assertNotIn("always = no", b)
        self.assertIn("can_recruit = { always = no }", block(text, "artificers"))

    def test_maa_loc(self):
        text = read("localization/english/aov_artificery_l_english.yml")
        self.assertNotIn("aov_prototype_tanks", text)
        self.assertNotIn("megacannon", text)
        for k in ("aov_clockwork_repeaters", "aov_gnomish_bombards", "aov_war_golems"):
            self.assertIn(f" {k}:", text)
            self.assertIn(f" {k}_flavor:", text)
        self.assertIn(" armored_artificers_flavor:",
                      read("localization/english/replace/aov_artificery_replace_l_english.yml"))
