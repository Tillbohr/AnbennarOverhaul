"""Tests for tools/data/spells.py and tools/build_spells.py.

    python -I -m unittest discover -s tools/tests -v
"""

import collections
import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
MOD = TOOLS.parent
sys.path.insert(0, str(TOOLS))


def load_data():
    spec = importlib.util.spec_from_file_location("aov_spells_data", TOOLS / "data" / "spells.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SPELLS


SPELLS = load_data()

import build_spells as bs  # noqa: E402
import build_hud_override  # noqa: E402  (brace_delta)


def balanced(text):
    depth = 0
    for line in text.split("\n"):
        depth += build_hud_override.brace_delta(line)
        if depth < 0:
            return False
    return depth == 0


def top_level_blocks(text):
    return re.findall(r"^([A-Za-z0-9_.]+) = \{", text, re.M)


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


class DataTests(unittest.TestCase):
    def test_forty_eight_spells_in_eight_schools(self):
        self.assertEqual(len(SPELLS), 48)
        counts = collections.Counter(s["school"] for s in SPELLS)
        self.assertEqual(set(counts), set(bs.SCHOOLS))
        self.assertTrue(all(counts[c] == 6 for c in bs.SCHOOLS))

    def test_slots_match_levels(self):
        level_of_slot = {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3}
        for s in SPELLS:
            if s["slot"]:
                self.assertEqual(level_of_slot[s["slot"]], s["level"], s["key"])
        for c in bs.SCHOOLS:
            slots = [s["slot"] for s in SPELLS if s["school"] == c and s["slot"]]
            self.assertEqual(sorted(slots), [1, 2, 3, 4, 5, 6], c)

    def test_existing_anbennar_spells(self):
        by = {s["key"]: s for s in SPELLS}
        self.assertEqual(by["thoughtweave"]["interaction"], "start_compel_interaction")
        self.assertEqual(by["dominate_to_surrender"]["interaction"], "start_dominate_interaction")
        self.assertNotIn("enhance_ability", by)  # removed from the game (zz_aov_spell_overrides.txt)

    def test_types(self):
        targeted = {s["key"] for s in SPELLS if s["type"] == "targeted"}
        self.assertEqual(targeted, {"ward", "heartstring", "thoughtweave", "dominate_to_surrender", "scry",
                                    "steal_vitality", "contagion"})
        for s in SPELLS:
            if s["type"] in ("self", "realm", "war"):
                self.assertTrue(s["modifier"].strip() or s["effect"].strip(), s["key"])


class ValidateTests(unittest.TestCase):
    def test_real_data_valid(self):
        bs.validate(SPELLS)

    def test_rejects_unknown_school(self):
        with self.assertRaises(bs.GeneratorError):
            bs.validate([dict(SPELLS[0], school="evokation")])

    def test_rejects_duplicate(self):
        with self.assertRaises(bs.GeneratorError):
            bs.validate(SPELLS + [dict(SPELLS[0])])


class ArtTests(unittest.TestCase):
    def test_tab_emblem_drops_ring_and_fills_icon(self):
        """The tab icon is only the hands-and-flame emblem from the middle of EU4's school wheel: the ring and
        the school icons around it are cleared, and the emblem is cropped and scaled to fill the icon."""
        w = h = 181
        c = w // 2
        px = bytearray(w * h * 4)
        for y in range(h):
            for x in range(w):
                d2 = (x - c) ** 2 + (y - c) ** 2
                if d2 <= 20 ** 2 or 55 ** 2 <= d2 <= 60 ** 2:  # emblem blob and ring
                    px[(y * w + x) * 4:(y * w + x) * 4 + 4] = bytes([0, 0, 255, 255])
        out = bs.tab_emblem(bytes(px), w, h, 95)
        self.assertEqual(len(out), 95 * 95 * 4)
        alpha = [[out[(y * 95 + x) * 4 + 3] for x in range(95)] for y in range(95)]
        self.assertEqual(alpha[0][0], 0)                       # corners clear: no ring
        self.assertEqual(alpha[47][47], 255)                   # emblem in the middle
        opaque = [x for x in range(95) if alpha[47][x] > 128]
        self.assertLessEqual(min(opaque), 6)                   # emblem spans the icon (small margin only)
        self.assertGreaterEqual(max(opaque), 88)

    def test_copy_art_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bs.GeneratorError):
                bs.copy_art(Path(tmp, "nope"), Path(tmp, "mod"))


class ValueTests(unittest.TestCase):
    def setUp(self):
        self.files = bs.render_all(SPELLS)
        self.v = self.files["common/script_values/aov_spell_values.txt"]

    def test_cost_value_has_floor(self):
        b = block(self.v, "aov_spell_meteor_swarm_cost")
        self.assertIn("subtract = aov_cost_cut_evocation", b)
        self.assertIn("subtract = aov_cost_cut_war", b)
        self.assertIn("min = 0.5", b)
        self.assertIn("multiply = 100", b)
        self.assertIn("floor = yes", b)
        self.assertNotIn("aov_cost_cut_war", block(self.v, "aov_spell_guidance_cost"))
        self.assertIn("subtract = aov_cost_cut_targeted", block(self.v, "aov_spell_scry_cost"))

    def test_years_value(self):
        b = block(self.v, "aov_spell_elemental_fury_years")
        self.assertIn("value = 5", b)
        self.assertIn("multiply = aov_years_mult_evocation", b)
        self.assertIn("floor = yes", b)

    def test_duration_multiplier_only_for_lasting_spells(self):
        for k in ("scry", "heartstring"):
            self.assertNotIn("aov_years_mult", block(self.v, f"aov_spell_{k}_years"), k)
        for k in ("enchanting_envoy", "summon_elementals"):
            self.assertIn("multiply = aov_years_mult_", block(self.v, f"aov_spell_{k}_years"), k)

    def test_cooldown_and_modifier_share_years_value(self):
        b = block(self.files["common/scripted_effects/aov_spell_effects.txt"], "aov_spell_guidance_cast")
        self.assertIn("set_variable = { name = aov_spell_guidance_cd years = aov_spell_guidance_years }", b)
        self.assertIn("add_character_modifier = { modifier = aov_spell_guidance years = aov_spell_guidance_years }", b)
        self.assertIn("aov_mana_spend = { AMOUNT = aov_spell_guidance_cost }", b)
        self.assertIn("aov_school_add_progress = { SCHOOL = divination AMOUNT = 25 }", b)
        self.assertIn("add_magic_lifestyle_xp = 25", b)

    def test_no_fixed_costs_left(self):
        for rel in ("common/scripted_triggers/aov_spell_triggers.txt", "common/scripted_effects/aov_spell_effects.txt",
                    "localization/english/aov_spells_l_english.yml", "gui/aov_magic_generated.gui"):
            self.assertNotRegex(self.files[rel], r"AOV_SPELL_(COST|REQ_MANA|FACTS)_\d", rel)
            self.assertNotRegex(self.files[rel], r"aov_mana >= \d", rel)

    def test_dynamic_loc(self):
        loc = self.files["localization/english/aov_spells_l_english.yml"]
        self.assertIn("ScriptValue('aov_spell_fireball_cost')", loc)
        self.assertIn("ScriptValue('aov_spell_fireball_years')", loc)

    def test_elementals_follow_spell_years(self):
        eff = (MOD / "common/scripted_effects/aov_magic_effects.txt").read_text(encoding="utf-8-sig")
        self.assertIn("trigger_event = { id = aov_magic.10 years = aov_spell_summon_elementals_years }", eff)
        self.assertNotIn("years = 3", block(eff, "aov_summon_elementals"))


class GeneratedTests(unittest.TestCase):
    def test_outputs_balanced_and_headed(self):
        for name in ("modifiers", "triggers", "effects", "sguis"):
            with self.subTest(name):
                text = getattr(bs, name)(SPELLS)
                self.assertTrue(text.startswith("# Anbennar Overhaul: generated by tools/build_spells.py"))
                self.assertTrue(balanced(text))

    def test_necromancy_rolls_dark_magic(self):
        t = bs.effects(SPELLS)
        self.assertIn("aov_dark_magic_roll = yes", block(t, "aov_spell_false_life_cast"))
        self.assertNotIn("aov_dark_magic_roll", block(t, "aov_spell_guidance_cast"))

    def test_castable_requires_mage(self):
        b = block(bs.triggers(SPELLS), "aov_spell_fireball_castable")
        for s in ("aov_is_mage = yes", "aov_spell_fireball_known = yes", "aov_spell_fireball_ready = yes", "aov_mana >= aov_spell_fireball_cost"):
            self.assertIn(s, b)
        self.assertIn("aov_school_level_at_least = { SCHOOL = evocation LEVEL = 0 }",
                      block(bs.triggers(SPELLS), "aov_spell_fireball_known"))

    def test_war_spells_need_war(self):
        self.assertIn("is_at_war = yes", block(bs.triggers(SPELLS), "aov_spell_meteor_swarm_castable"))
        self.assertNotIn("is_at_war", block(bs.triggers(SPELLS), "aov_spell_guidance_castable"))

    def test_sgui_only_for_window_spells(self):
        names = set(top_level_blocks(bs.sguis(SPELLS)))
        self.assertIn("aov_spell_guidance_sgui", names)
        self.assertNotIn("aov_spell_heartstring_sgui", names)
        for c in bs.SCHOOLS:
            self.assertIn(f"aov_study_{c}_sgui", names)

    def test_modifier_per_lasting_spell(self):
        names = set(top_level_blocks(bs.modifiers(SPELLS)))
        self.assertIn("aov_spell_combat_ward", names)
        self.assertIn("aov_spell_steal_vitality", names)
        self.assertNotIn("aov_spell_transmute_to_gold", names)  # one-off

    def test_loc_keys(self):
        lc = bs.loc(SPELLS)
        self.assertTrue(lc.startswith("l_english:\n"))
        for s in SPELLS:
            for suffix in ("", "_desc", "_flavour"):
                self.assertIn(f" aov_spell_{s['key']}{suffix}:", lc)
        for c in bs.SCHOOLS:
            for lvl in range(4):
                self.assertIn(f" AOV_SPELL_REQ_{c.upper()}_{lvl}:", lc)

    def test_ai_casts_window_spells_only(self):
        b = block(bs.effects(SPELLS), "aov_magic_ai_cast_random")
        for s in SPELLS:
            if s["type"] == "targeted":
                self.assertNotIn(f"aov_spell_{s['key']}_cast", b)
            else:
                self.assertIn(f"aov_spell_{s['key']}_castable = yes }}", b)
        self.assertIn("30 = {", b)  # war spells weigh more
        # AI does not risk Forbidden Magic Practitioner: Necromancy only where magic is not illegal or shunned
        for sp in SPELLS:
            if sp["school"] == "necromancy" and sp["type"] != "targeted":
                opt = b.split(f"aov_spell_{sp['key']}_castable = yes")[0].rsplit("trigger = {", 1)[1]
                self.assertIn("NOT = { aov_dark_magic_risky = yes }", opt, sp["key"])
        t = block(bs.triggers(SPELLS), "aov_magic_ai_any_castable")
        self.assertIn("aov_spell_guidance_castable = yes", t)
        self.assertNotIn("aov_spell_heartstring_castable", t)

    def test_generated_interactions(self):
        text = bs.interactions(SPELLS)
        self.assertTrue(balanced(text))
        names = set(top_level_blocks(text))
        self.assertEqual(names, {f"aov_spell_{k}_interaction" for k in ("ward", "heartstring", "scry", "steal_vitality", "contagion")})
        for name in names:
            b = block(text, name)
            k = name[len("aov_spell_"):-len("_interaction")]
            self.assertIn("category = interaction_category_spells", b)
            self.assertIn(f"scope:actor = {{ aov_spell_{k}_castable = yes }}", b)
            self.assertIn("scope:recipient = { aov_spell_target_allowed = yes }", b)
            self.assertIn(f"scope:actor = {{ aov_spell_{k}_cast = yes }}", b)

    def test_interaction_loc(self):
        lc = bs.loc(SPELLS)
        for k in ("ward", "heartstring", "scry", "steal_vitality", "contagion"):
            self.assertIn(f" aov_spell_{k}_interaction:", lc)
            self.assertIn(f" aov_spell_{k}_interaction_desc:", lc)

    def test_gui_school_pages_and_cards(self):
        text = bs.gui(SPELLS)
        self.assertTrue(balanced(text))
        for c in bs.SCHOOLS:
            self.assertIn(f"type aov_magic_school_{c} = vbox {{", text)
        self.assertEqual(len(re.findall(r'name = "aov_spell_card_[a-z_]+"', text)), 48)
        for s in SPELLS:
            k = s["key"]
            card = text.split(f'name = "aov_spell_card_{k}"')[1].split('name = "aov_spell_card_')[0].split("type aov_magic_school_")[0]
            if s["type"] == "targeted":
                self.assertNotIn("Execute", card, k)
                self.assertIn("AOV_SPELL_CAST_FROM_PORTRAIT", card, k)
            else:
                self.assertIn(f"GetScriptedGui('aov_spell_{k}_sgui').Execute( {bs.ROOT} )", card, k)
            self.assertIn(f'tooltip = "aov_spell_{k}_tt"', card, k)
            if s["slot"]:
                self.assertIn(f'texture = "gfx/interface/icons/aov_magic/spell_slot_{s["slot"]}.dds"', card, k)
                self.assertIn(f"frame = {bs.SCHOOLS.index(s['school']) + 1}", card, k)

    def test_gui_card_layout_matches_eu4_slot(self):
        """EU4 draws the 290x64 plate and the 64x76 level frame at the slot origin and the 60x60 icon at +2,+2,
        all unscaled; the Cast button sits right of the plate."""
        text = bs.gui(SPELLS)
        self.assertNotIn("Corneredstretched", text)
        for s in SPELLS:
            k = s["key"]
            card = text.split(f'name = "aov_spell_card_{k}"')[1].split('name = "aov_spell_card_')[0].split("type aov_magic_school_")[0]
            plate = card.split('texture = "gfx/interface/icons/aov_magic/spell_plate.dds"')[0].rsplit("icon = {", 1)[1]
            self.assertIn("position = { 0 0 }", plate, k)
            self.assertIn("size = { 290 64 }", plate, k)
            if s["slot"]:
                icon = card.split(f'spell_slot_{s["slot"]}.dds"')[0].rsplit("icon = {", 1)[1]
                self.assertIn("position = { 2 2 }", icon, k)
                self.assertIn("size = { 60 60 }", icon, k)
            frame = card.split('spell_frames.dds"')[0].rsplit("icon = {", 1)[1]
            self.assertIn("position = { 0 0 }", frame, k)
            self.assertIn("size = { 64 76 }", frame, k)
            action = card.split("button_standard = {" if s["type"] != "targeted" else "text_multi = {")[1]
            self.assertIn("parentanchor = right", action, k)
            self.assertIn("position = { -6 16 }", action, k)

    def test_gui_cards_fit(self):
        for w in re.findall(r"aov_spell_card_[a-z_]+\"\n\t*size = \{ (\d+) ", bs.gui(SPELLS)):
            self.assertLessEqual(int(w), 480)

    def test_gui_school_header_study_button(self):
        text = bs.gui(SPELLS)
        for c in bs.SCHOOLS:
            page = text.split(f"type aov_magic_school_{c} = vbox {{")[1].split("type aov_magic_school_")[0]
            self.assertIn(f"GetScriptedGui('aov_study_{c}_sgui').Execute( {bs.ROOT} )", page)
            self.assertIn(f'texture = "gfx/interface/icons/aov_magic/school_{c}.dds"', page)

    def test_render_all_paths(self):
        self.assertEqual(set(bs.render_all(SPELLS)), {
            "common/character_interactions/aov_spell_interactions.txt",
            "gui/aov_magic_generated.gui",
            "common/modifiers/aov_spell_modifiers.txt",
            "common/scripted_triggers/aov_spell_triggers.txt",
            "common/scripted_effects/aov_spell_effects.txt",
            "common/script_values/aov_spell_values.txt",
            "common/scripted_guis/aov_spell_sgui.txt",
            "localization/english/aov_spells_l_english.yml",
        })


if __name__ == "__main__":
    unittest.main()
