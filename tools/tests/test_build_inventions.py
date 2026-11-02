"""Tests for tools/data/inventions.py and tools/build_inventions.py.

    python -I -m unittest discover -s tools/tests -p "test_build_inventions.py"
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
REMOVED = {"arcane_battery_capital_complex", "automated_translator", "market_mender", "plane_of_water_teleporter",
           "gene_food_cultivation", "vendorless_stall", "elemental_locomotives", "prefabricated_city_constructors",
           "t_wave_transceivers", "artificer_exo_arms", "commercial_sky_galleons", "magic_missile_deployer",
           "portable_turrets", "sparkdrive_rifles", "arcane_blaster", "balloonboost_packs", "coddorran_powered_exosuit",
           "gu_boats", "prototype_tanks", "artillery_autoloader", "bioartificed_ascension", "damestear_reactor_megacannon",
           "military_sky_galleons", "naval_mageshields", "personal_mageshields", "apparitional_communicator", "viewcatcher",
           "empire_engine", "think_thought_transmitters", "bureaucratizer", "crierless_crier_device", "negotiation_nexus",
           "runethought_network"}


class DataTests(unittest.TestCase):
    def test_forty_eight_unique_inventions(self):
        self.assertEqual(len(INVENTIONS), 48)
        self.assertEqual(len(set(KEYS)), 48)

    def test_category_tier_counts(self):
        counts = collections.Counter((i["category"], i["tier"]) for i in INVENTIONS)
        self.assertEqual(counts, {("economic", 1): 5, ("economic", 2): 4, ("economic", 3): 4,
                                  ("military", 1): 6, ("military", 2): 7, ("military", 3): 6,
                                  ("society", 1): 6, ("society", 2): 6, ("society", 3): 4})

    def test_removed_keys_are_gone(self):
        self.assertFalse(REMOVED & set(KEYS))

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

    def test_unlocks(self):
        self.assertEqual({i["key"]: i["unlock"] for i in INVENTIONS if i["unlock"]}, {
            "clockwork_waterwheels": "aov_clockwork_mill_01", "alchemical_distilleries": "aov_alchemical_distillery_01",
            "damestear_foundries": "aov_damestear_foundry_01", "clockwork_repeaters": "aov_clockwork_repeaters",
            "war_golems": "aov_war_golems", "gnomish_bombards": "aov_gnomish_bombards",
            "clockwork_plate_harness": "armored_artificers"})
        self.assertTrue(all("maa" not in i for i in INVENTIONS))

    def test_locks(self):
        self.assertEqual(sum(1 for i in INVENTIONS if i["faith"]), 8)
        self.assertEqual({i["key"] for i in INVENTIONS if i["gnome_only"]}, {"conversation_calibrator", "automaton_labourers"})

    def test_icon_matches_category_and_tier(self):
        code = {"economic": "Ec", "military": "Mi", "society": "So"}
        for i in INVENTIONS:
            with self.subTest(i["key"]):
                self.assertRegex(i["icon"], rf"^Artf_(Br|Ma|Te){code[i['category']]}{i['tier']}\.dds$")

    def test_spot_check_modifiers(self):
        by = {i["key"]: i["modifier"] for i in INVENTIONS}
        self.assertEqual(by["damestear_powder"], "gunpowder_damage_mult = 0.25")
        self.assertEqual(by["gnomish_spectacles"].split("\n"),
                         ["diplomacy = 1", "martial = 1", "stewardship = 1", "intrigue = 1", "learning = 1", "prowess = 1"])
        self.assertEqual(by["universal_grammarye"], "different_culture_opinion = 25\ndiplomacy = 2")
        self.assertEqual(by["clerk_automatons"], "domain_limit = 1\nvassal_limit = 20")

    def test_no_keys_tiger_rejects_in_character_modifiers(self):
        # travel_speed is a travel-plan modifier and cultural_acceptance_gain_mult a culture modifier
        for i in INVENTIONS:
            keys = set(re.findall(r"^\s*([a-z_]+)\s*=", i["modifier"], re.M))
            with self.subTest(i["key"]):
                self.assertFalse(keys & {"travel_speed", "cultural_acceptance_gain_mult"})

    def test_sorted_by_category_tier_key(self):
        order = {"economic": 0, "military": 1, "society": 2}
        self.assertEqual(INVENTIONS, sorted(INVENTIONS, key=lambda i: (order[i["category"]], i["tier"], i["key"])))


import build_inventions as bi  # noqa: E402
import build_hud_override  # noqa: E402  (brace_delta)


def balanced(text):
    depth = 0
    for line in text.split("\n"):
        depth += build_hud_override.brace_delta(line)
        if depth < 0:
            return False
    return depth == 0


def top_level_blocks(text):
    return re.findall(r"^([A-Za-z0-9_]+) = \{", text, re.M)


class ValidateTests(unittest.TestCase):
    def test_real_data_is_valid(self):
        bi.validate(INVENTIONS)

    def test_rejects_duplicate_key(self):
        with self.assertRaises(bi.GeneratorError):
            bi.validate(INVENTIONS + [dict(INVENTIONS[0])])

    def test_rejects_unknown_faith(self):
        bad = dict(INVENTIONS[0], faith="faith = faith:made_up")
        with self.assertRaises(bi.GeneratorError):
            bi.validate([bad])

    def test_rejects_bad_category(self):
        with self.assertRaises(bi.GeneratorError):
            bi.validate([dict(INVENTIONS[0], category="magic")])

    def test_rejects_unknown_unlock(self):
        with self.assertRaises(bi.GeneratorError):
            bi.validate([dict(INVENTIONS[0], unlock="aov_made_up")])

    def test_rejects_duplicate_unlock(self):
        a = dict(INVENTIONS[0], key="a", unlock="aov_war_golems")
        b = dict(INVENTIONS[0], key="b", unlock="aov_war_golems")
        with self.assertRaises(bi.GeneratorError):
            bi.validate([a, b])


class ScriptOutputTests(unittest.TestCase):
    def test_all_script_outputs_balanced_and_headed(self):
        for name in ("modifiers", "triggers", "values", "effects", "custom_loc"):
            with self.subTest(name):
                text = getattr(bi, name)(INVENTIONS)
                self.assertTrue(text.startswith("# Anbennar Overhaul: generated by tools/build_inventions.py"))
                self.assertTrue(balanced(text))

    def test_modifier_per_invention_with_category_icon(self):
        text = bi.modifiers(INVENTIONS)
        self.assertEqual(top_level_blocks(text), [f"aov_invention_{k}" for k in KEYS])
        self.assertIn("aov_invention_damestear_powder = {\n\ticon = martial_positive\n\tgunpowder_damage_mult = 0.25\n}", text)

    def test_triggers_per_invention(self):
        names = set(top_level_blocks(bi.triggers(INVENTIONS)))
        for k in KEYS:
            for suffix in ("visible", "unlocked", "available", "discovered", "active", "discoverable", "activatable", "offered", "unlock_ready"):
                self.assertIn(f"aov_invention_{k}_{suffix}", names)
        for c in bi.CATEGORIES:
            self.assertIn(f"aov_inventions_{c}_discoverable", names)
            self.assertIn(f"aov_inventions_{c}_unoffered_discoverable", names)
            for t in (1, 2, 3):
                self.assertIn(f"aov_inventions_t{t}_{c}_activatable", names)
        for n in ("aov_inventions_any_discovered", "aov_inventions_any_discoverable", "aov_inventions_any_activatable",
                  "aov_inventions_t1_activatable", "aov_inventions_t2_activatable", "aov_inventions_t3_activatable"):
            self.assertIn(n, names)

    def test_unlocked_uses_tier_era(self):
        text = bi.triggers(INVENTIONS)
        for i in INVENTIONS:
            block = re.search(rf"^aov_invention_{i['key']}_unlocked = \{{\n(.*?)\n\}}", text, re.M | re.S).group(1)
            self.assertIn(bi.ERAS[i["tier"]], block)

    def test_category_aggregate_only_lists_its_category(self):
        text = bi.triggers(INVENTIONS)
        for c in bi.CATEGORIES:
            block = re.search(rf"^aov_inventions_{c}_discoverable = \{{\n(.*?)\n\}}", text, re.M | re.S).group(1)
            listed = set(re.findall(r"aov_invention_([a-z0-9_]+)_discoverable", block))
            self.assertEqual(listed, {i["key"] for i in INVENTIONS if i["category"] == c})

    def test_values(self):
        text = bi.values(INVENTIONS)
        self.assertEqual(top_level_blocks(text)[:2], ["aov_invention_active_count", "aov_invention_newest_order"])
        for k in KEYS:
            self.assertIn(f"aov_invention_{k}_active = yes", text)
            self.assertIn(f"min = var:aov_inv_{k}_order", text)

    def test_effects_per_invention(self):
        names = set(top_level_blocks(bi.effects(INVENTIONS)))
        for k in KEYS:
            for suffix in ("discover", "activate", "deactivate"):
                self.assertIn(f"aov_invention_{k}_{suffix}", names)
        for c in bi.CATEGORIES:
            self.assertIn(f"aov_inventions_discover_random_{c}", names)
            self.assertIn(f"aov_inventions_roll_offers_{c}", names)
            self.assertIn(f"aov_inventions_ai_start_technomancers_{c}", names)
        for n in ("aov_inventions_discover_random", "aov_inventions_discover_research_target",
                  "aov_inventions_activate_last_discovered", "aov_inventions_suspend_all", "aov_inventions_resume_all",
                  "aov_inventions_deactivate_newest", "aov_inventions_inherit", "aov_inventions_ai_activate_best"):
            self.assertIn(n, names)

    def effect_block(self, name):
        text = bi.effects(INVENTIONS)
        return re.search(rf"^{name} = \{{\n(.*?)\n^\}}", text, re.M | re.S).group(1)

    def test_suspend_and_resume_cover_every_invention(self):
        suspend = self.effect_block("aov_inventions_suspend_all")
        resume = self.effect_block("aov_inventions_resume_all")
        for k in KEYS:
            self.assertIn(f"remove_character_modifier = aov_invention_{k}", suspend)
            self.assertIn(f"add_character_modifier = {{ modifier = aov_invention_{k} }}", resume)

    def test_activate_respects_dormancy(self):
        block = self.effect_block("aov_invention_damestear_powder_activate")
        self.assertIn("NOT = { has_variable = aov_artificery_dormant }", block)

    def test_deactivate_newest_is_a_single_chain(self):
        block = self.effect_block("aov_inventions_deactivate_newest")
        self.assertEqual(block.count("\tif = {"), 1)
        self.assertEqual(block.count("\telse_if = {"), 47)

    def test_random_draw_per_category_only_lists_its_category(self):
        for c in bi.CATEGORIES:
            block = self.effect_block(f"aov_inventions_discover_random_{c}")
            listed = set(re.findall(r"aov_invention_([a-z0-9_]+)_discover = yes", block))
            self.assertEqual(listed, {i["key"] for i in INVENTIONS if i["category"] == c})

    def test_roll_offers_fills_three_slots(self):
        block = self.effect_block("aov_inventions_roll_offers_military")
        for n in (1, 2, 3):
            self.assertIn(f"name = aov_tech_offer_military_{n}", block)
        self.assertIn("set_variable = aov_tech_offers_rolled_military", block)

    def test_custom_loc_and_loc(self):
        cl = bi.custom_loc(INVENTIONS)
        self.assertEqual(top_level_blocks(cl), ["AovLastDiscoveredName", "AovResearchTargetName"])
        lc = bi.loc(INVENTIONS)
        self.assertTrue(lc.startswith("l_english:\n"))
        for i in INVENTIONS:
            self.assertIn(f' aov_invention_{i["key"]}: "{i["name"]}"', lc)
            self.assertIn(f" aov_invention_{i['key']}_desc:", lc)
            self.assertIn(f" aov_invention_{i['key']}_tt:", lc)

    def test_deterministic(self):
        for name in ("modifiers", "triggers", "values", "effects", "custom_loc", "loc"):
            self.assertEqual(getattr(bi, name)(INVENTIONS), getattr(bi, name)(INVENTIONS))


class GuiOutputTests(unittest.TestCase):
    def test_unlock_ready_per_invention(self):
        text = bi.triggers(INVENTIONS)
        for k in KEYS:
            block = re.search(rf"^aov_invention_{k}_unlock_ready = \{{\n(.*?)\n\}}", text, re.M | re.S).group(1)
            self.assertEqual(block, f"\taov_invention_{k}_discovered = yes\n\taov_invention_{k}_visible = yes\n"
                                    "\tNOT = { has_variable = aov_artificery_dormant }")

    def test_unlocked_gates_on_lower_tier_discoveries(self):
        text = bi.triggers(INVENTIONS)
        for i in INVENTIONS:
            block = re.search(rf"^aov_invention_{i['key']}_unlocked = \{{\n(.*?)\n\}}", text, re.M | re.S).group(1)
            if i["tier"] == 1:
                self.assertNotIn("discovered_count", block)
            else:
                self.assertIn(f"aov_inventions_t{i['tier'] - 1}_discovered_count >= aov_invention_tier_gate_count", block)

    def test_discovered_counts_list_their_tier(self):
        text = bi.values(INVENTIONS)
        self.assertEqual(top_level_blocks(text), ["aov_invention_active_count", "aov_invention_newest_order",
                                                  "aov_inventions_t1_discovered_count", "aov_inventions_t2_discovered_count"])
        for t in (1, 2):
            block = re.search(rf"^aov_inventions_t{t}_discovered_count = \{{\n(.*?)\n\}}", text, re.M | re.S).group(1)
            self.assertEqual(set(re.findall(r"aov_invention_([a-z0-9_]+)_discovered = yes", block)),
                             {i["key"] for i in INVENTIONS if i["tier"] == t})

    def test_unlock_tooltip_and_loc(self):
        gui, lc = bi.gui(INVENTIONS), bi.loc(INVENTIONS)
        for i in INVENTIONS:
            k = i["key"]
            tt = gui.split(f"type aov_invention_{k}_tooltip = object_tooltip_pop_out {{")[1].split("\n\t}\n")[0]
            if i["unlock"]:
                name = f"building_{i['unlock']}" if i["unlock"] in bi.BUILDING_UNLOCKS else i["unlock"]
                self.assertIn(f'text = "aov_invention_{k}_unlock_tt"', tt)
                self.assertIn(f' aov_invention_{k}_unlock_tt: "#P Unlocks#! ${name}$ #weak (permanent once discovered)#!"', lc)
            else:
                self.assertNotIn("_unlock_tt", tt)

    def test_nine_sguis_per_invention(self):
        names = top_level_blocks(bi.sguis(INVENTIONS))
        self.assertEqual(len(names), 9 * 48)
        for k in KEYS:
            for s in ("visible", "unlocked", "undiscovered", "activate", "deactivate", "toggle", "offered", "research", "effects"):
                self.assertIn(f"aov_inv_{k}_{s}_sgui", names)

    def sgui_block(self, name):
        return re.search(rf"^{name} = \{{\n(.*?)\n\}}", bi.sguis(INVENTIONS), re.M | re.S).group(1)

    def test_deactivate_starts_cooldown(self):
        self.assertIn("aov_artificery_start_slot_cooldown = yes", self.sgui_block("aov_inv_damestear_powder_deactivate_sgui"))

    def test_toggle_activates_or_deactivates_with_cooldown(self):
        block = self.sgui_block("aov_inv_damestear_powder_toggle_sgui")
        self.assertIn("aov_invention_damestear_powder_discovered = yes", block)
        self.assertRegex(block, r"trigger_if = \{\s*limit = \{ NOT = \{ aov_invention_damestear_powder_active = yes \} \}"
                                r"\s*aov_invention_damestear_powder_available = yes\s*aov_artificery_has_free_slot = yes")
        self.assertRegex(block, r"aov_invention_damestear_powder_deactivate = yes\s*aov_artificery_start_slot_cooldown = yes")
        self.assertIn("else = { aov_invention_damestear_powder_activate = yes }", block)

    def test_gui_balanced_with_types(self):
        text = bi.gui(INVENTIONS)
        self.assertTrue(balanced(text))
        for t in ("aov_inventions_tier_1", "aov_inventions_tier_2", "aov_inventions_tier_3",
                  "aov_inventions_offers_economic", "aov_inventions_offers_military", "aov_inventions_offers_society"):
            self.assertIn(f"type {t} = vbox {{", text)
        for k in KEYS:
            self.assertIn(f"type aov_invention_{k}_tooltip = object_tooltip_pop_out {{", text)

    def tier_body(self, t):
        text = bi.gui(INVENTIONS)
        return text.split(f"type aov_inventions_tier_{t} = vbox {{")[1].split("\n\t}\n")[0]

    def test_tiers_have_society_economic_military_sections_of_their_boxes(self):
        for t in (1, 2, 3):
            body = self.tier_body(t)
            names = re.findall(r'name = "aov_inventions_t\d_([a-z]+)"', body)
            self.assertEqual(names, ["society", "economic", "military"])
            for c in bi.CATEGORIES:
                section = body.split(f'name = "aov_inventions_t{t}_{c}"')[1].split('name = "aov_inventions_t')[0]
                listed = re.findall(r'name = "aov_inv_box_([a-z0-9_]+)"', section)
                self.assertEqual(listed, [i["key"] for i in INVENTIONS if i["category"] == c and i["tier"] == t])

    def test_rows_hold_at_most_five_boxes(self):
        for t in (1, 2, 3):
            for row in self.tier_body(t).split("hbox = {")[1:]:
                self.assertLessEqual(row.count('name = "aov_inv_box_'), bi.PER_ROW)

    def box(self, k):
        text = bi.gui(INVENTIONS)
        return text.split(f'name = "aov_inv_box_{k}"')[1].split('name = "aov_inv_box_')[0]

    def test_box_click_toggles_and_hover_shows_invention_tooltip(self):
        for i in INVENTIONS:
            k = i["key"]
            b = self.box(k)
            self.assertIn(f"aov_inv_{k}_visible_sgui", b.split("\n")[1])
            self.assertIn(f"onclick = \"[GetScriptedGui('aov_inv_{k}_toggle_sgui').Execute( {bi.ROOT} )]\"", b)
            self.assertRegex(b, rf"tooltipwidget = \{{\s*aov_invention_{k}_tooltip = \{{\}}")
            # not the EU4 estate-privilege icon (the slice may run into the next type, e.g. the offers, so cut it)
            self.assertNotIn(i["icon"], b.split("type aov_inventions_")[0])

    def test_box_uses_eu4_invention_button_frames(self):
        # EU4 Anbennar's inventions menu: category strip, frame 1 locked/undiscovered, 2 discovered, 3 active
        for i in INVENTIONS:
            k, c = i["key"], i["category"]
            b = self.box(k)
            tex = f'texture = "gfx/interface/icons/aov_inventions/aov_invention_button_{c}.dds"'
            self.assertEqual(b.count(tex), 3, k)
            self.assertEqual(b.count("framesize = { 78 78 }"), 3, k)
            frames = {n: b.split(f"frame = {n}\n")[0].rsplit("visible = ", 1)[1] for n in (1, 2, 3)}
            self.assertIn(f"aov_inv_{k}_activate_sgui", frames[2])
            self.assertIn(f"aov_inv_{k}_deactivate_sgui", frames[3])
            self.assertIn(f"Not( Or( GetScriptedGui('aov_inv_{k}_activate_sgui')", frames[1])
            # EU4's society strip has a colour frame 1 (same as frame 2), so frame 1 is greyed in CK3
            self.assertIn('effectname = "GreyedOut"', frames[1].split("highlight_icon")[0] + b.split("frame = 1\n")[0].rsplit("highlight_icon", 1)[1])

    def test_tooltip_has_name_description_effects_and_status(self):
        text = bi.gui(INVENTIONS)
        for i in INVENTIONS:
            k = i["key"]
            tt = text.split(f"type aov_invention_{k}_tooltip = object_tooltip_pop_out {{")[1].split("\n\t}\n")[0]
            self.assertIn(f'text = "aov_invention_{k}"', tt)
            self.assertIn(f'text = "aov_invention_{k}_subtitle"', tt)
            self.assertIn(f'text = "aov_invention_{k}_desc"', tt)
            self.assertIn(f"[GetScriptedGui('aov_inv_{k}_effects_sgui').BuildTooltip( {bi.ROOT} )]", tt)
            for key in (f"AOV_INV_LOCKED_TIER_{i['tier']}_TT", "AOV_INV_UNDISCOVERED_TT", "AOV_INV_CLICK_ACTIVATE",
                        "AOV_INV_NO_FREE_SLOT", "AOV_INV_CLICK_DEACTIVATE"):
                self.assertIn(f'text = "{key}"', tt)

    def test_effects_sgui_adds_the_invention_modifier(self):
        for k in KEYS:
            block = self.sgui_block(f"aov_inv_{k}_effects_sgui")
            self.assertIn(f"add_character_modifier = {{ modifier = aov_invention_{k} }}", block)
            self.assertNotIn("is_shown", block)

    def test_offers_only_list_their_category_and_use_the_tooltip(self):
        text = bi.gui(INVENTIONS)
        for c in bi.CATEGORIES:
            body = text.split(f"type aov_inventions_offers_{c} = vbox {{")[1].split("type aov_inventions_offers_")[0]
            listed = set(re.findall(r'name = "aov_inv_offer_([a-z0-9_]+)"', body))
            self.assertEqual(listed, {i["key"] for i in INVENTIONS if i["category"] == c})
            for k in listed:
                self.assertIn(f"aov_invention_{k}_tooltip = {{}}", body)
                self.assertIn(f"GetScriptedGui('aov_inv_{k}_research_sgui').Execute", body)

    def test_subtitle_loc(self):
        lc = bi.loc(INVENTIONS)
        self.assertIn(' aov_invention_damestear_powder_subtitle: "$AOV_CATEGORY_MILITARY$, $AOV_TIER_1$"', lc)

    def test_render_all_paths(self):
        files = bi.render_all(INVENTIONS)
        self.assertEqual(set(files), {
            "common/modifiers/aov_invention_modifiers.txt",
            "common/scripted_triggers/aov_invention_triggers.txt",
            "common/script_values/aov_invention_values.txt",
            "common/scripted_effects/aov_invention_effects.txt",
            "common/scripted_guis/aov_invention_sgui.txt",
            "common/customizable_localization/aov_invention_custom_loc.txt",
            "gui/aov_inventions_generated.gui",
            "localization/english/aov_inventions_l_english.yml",
        })

    def test_write_all_bom_lf(self):
        with tempfile.TemporaryDirectory() as tmp:
            bi.write_all({"a/b.txt": "x = {\n}\n"}, Path(tmp))
            raw = (Path(tmp) / "a" / "b.txt").read_bytes()
            self.assertEqual(raw, b"\xef\xbb\xbfx = {\n}\n")

    def test_committed_icons_exist(self):
        bi.check_icons(INVENTIONS, bi.SUBMOD)

    def test_missing_icon_stops_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bi.GeneratorError):
                bi.check_icons(INVENTIONS, Path(tmp))
if __name__ == "__main__":
    unittest.main()
