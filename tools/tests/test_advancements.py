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
