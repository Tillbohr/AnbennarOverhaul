"""Static checks on Delve Deeper, the scripted dig that raises a dwarven hold one level.

    python -I -m unittest discover -s tools/tests -p test_hold_dig.py
"""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))  # python -I does not add the tools folder
from data import holds  # noqa: E402


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def top_block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


def trigger_block(name):
    return top_block(read("common/scripted_triggers/aov_hold_triggers.txt"), name)


def effect_block(name):
    return top_block(read("common/scripted_effects/aov_hold_effects.txt"), name)


def on_action_block(name):
    return top_block(read("common/on_action/aov_hold_on_actions.txt"), name)


def decision_block(name):
    return top_block(read("common/decisions/aov_hold_decisions.txt"), name)


def event_block(name):
    return top_block(read("events/aov_hold_delve_events.txt"), name)


class HoldDigTests(unittest.TestCase):
    def test_activity_is_gone(self):
        self.assertFalse((ROOT / "common/activities/activity_types/aov_hold_dig.txt").exists())
        for path in list((ROOT / "common").rglob("*.txt")) + list((ROOT / "events").rglob("*.txt")):
            self.assertNotIn("activity_hold_dig", path.read_text("utf-8-sig", errors="ignore"), path)

    def test_activity_art_and_loc_are_gone(self):
        self.assertFalse((ROOT / "localization/english/aov_hold_dig_l_english.yml").exists())
        for pattern in ("gfx/interface/icons/activities/activity_hold_dig*.dds",
                        "gfx/interface/icons/activity_option_categories/aov_dig_*.dds",
                        "gfx/interface/icons/activity_phases/aov_dig_*.dds",
                        "gfx/interface/illustrations/activity_header_backgrounds/activity_hold_dig.dds"):
            self.assertEqual(list(ROOT.glob(pattern)), [], pattern)

    def test_old_campaign_names_are_gone(self):
        for path in list((ROOT / "common").rglob("*.txt")) + list((ROOT / "events").rglob("*.txt")):
            text = path.read_text("utf-8-sig", errors="ignore")
            for gone in ("aov_dig_in_progress", "aov_hold_end_campaign_effect", "aov_hold_apply_campaign_effect",
                         "aov_dig_floor_progress", "aov_campaign_progress", "involved_activity",
                         "aov_hold_dig.101"):
                self.assertNotIn(gone, text, (path, gone))

    def test_running_trigger(self):
        self.assertIn("has_variable = aov_dig_target_level", trigger_block("aov_hold_dig_running"))

    def test_can_dig_needs_level_below_ten(self):
        self.assertIn("aov_can_start_dig_base = yes", trigger_block("aov_can_dig_at"))
        t = trigger_block("aov_can_start_dig_base")
        self.assertIn("aov_hold_is_working = yes", t)
        self.assertIn("aov_hold_level < 10", t)
        self.assertRegex(t, r"NOT = \{ aov_hold_dig_running = yes \}")
        self.assertIn("barony.holder = scope:digger", t)
        self.assertIn("is_dwarvish_culture = yes", t)

    def test_start_sets_target_progress_and_modifier(self):
        e = effect_block("aov_hold_start_dig_effect")
        self.assertIn("name = aov_dig_target_level", e)
        self.assertIn("set_variable = { name = aov_dig_progress value = 0 }", e)
        for level in range(2, 11):
            self.assertIn(f"modifier = aov_delving_{level:02d}", e)
        self.assertNotIn("gold", e)   # the caller pays

    def test_completion_levels_once_and_ends_dig(self):
        e = effect_block("aov_hold_check_dig_complete_effect")
        self.assertEqual(e.count("add_building = dwarven_hold_"), 9)   # targets 02..10, if/else_if chain
        for level in range(2, 11):
            self.assertIn(f"add_building = dwarven_hold_{level:02d}", e)
        self.assertEqual(e.count("\t\tif = {"), 1)   # one chain: a single level per completion
        self.assertIn("var:aov_dig_progress >= aov_dig_months", e)
        self.assertIn("aov_hold_end_dig_effect = yes", e)
        self.assertIn("save_scope_as = hold", e)
        self.assertIn("aov_hold_dig.100", e)

    def test_progress_floor(self):
        e = effect_block("aov_hold_add_dig_progress_effect")
        self.assertIn("add = $MONTHS$", e)
        self.assertIn("aov_dig_progress < 0", e)
        self.assertIn("aov_hold_check_dig_complete_effect = yes", e)

    def test_ruin_ends_dig(self):
        self.assertIn("aov_hold_end_dig_effect = yes", effect_block("aov_hold_ruin_effect"))
        end = effect_block("aov_hold_end_dig_effect")
        self.assertIn("remove_variable = aov_dig_progress", end)
        self.assertIn("remove_variable = aov_dig_target_level", end)
        for level in range(2, 11):
            self.assertIn(f"remove_province_modifier = aov_delving_{level:02d}", end)

    def test_quarterly_tick(self):
        oa = read("common/on_action/aov_hold_on_actions.txt")
        self.assertRegex(oa, r"quarterly_playable_pulse\s*=\s*\{\s*on_actions\s*=\s*\{[^}]*aov_hold_dig_quarterly")
        tick = on_action_block("aov_hold_dig_quarterly")
        for s in ("MONTHS = 3", "is_occupied", "is_dwarvish_culture", "aov_hold_dig_running = yes"):
            self.assertIn(s, tick)

    def test_events_use_the_hold(self):
        events = read("events/aov_hold_dig_events.txt")
        for n in range(1, 12):
            ev = top_block(events, f"aov_hold_dig.{n}")
            self.assertIn("exists = scope:hold", ev)
            self.assertIn("scope:hold = { aov_hold_dig_running = yes }", ev)
        self.assertIn("scope:hold.aov_hold_level", top_block(events, "aov_hold_dig.100"))
        self.assertNotIn("hold_province", events)

    def test_decision_gating_and_cost(self):
        d = decision_block("aov_delve_deeper_decision")
        self.assertIn("is_dwarvish_culture = yes", d)
        self.assertIn("aov_can_dig_at", d)
        self.assertIn("aov_dig_cost", d)

    def test_can_dig_excludes_occupied_holds(self):
        self.assertIn("is_occupied = no", trigger_block("aov_can_start_dig_base"))

    def test_decision_shows_both_failures_and_costs(self):
        d = decision_block("aov_delve_deeper_decision")
        valid = re.search(r"^\tis_valid = \{(.*?)\n\t\}", d, re.S | re.M).group(1)
        self.assertEqual(valid.count("custom_description"), 2)
        self.assertIn("text = aov_delve_deeper_no_hold", valid)
        self.assertIn("text = aov_delve_deeper_no_gold", valid)
        gold_part = valid.split("aov_delve_deeper_no_gold")[1]
        self.assertIn("scope:digger.gold >= aov_dig_cost", gold_part)
        self.assertNotIn("gold", valid.split("aov_delve_deeper_no_gold")[0].replace("no_gold", ""))
        loc = read("localization/english/aov_hold_delve_l_english.yml")
        for n in range(1, 10):
            self.assertIn(f"desc = aov_delve_deeper_cost_{n}\n", d)
            line = re.search(rf"^ aov_delve_deeper_cost_{n}:0 \"(.*)\"$", loc, re.M).group(1)
            self.assertIn("ScriptValue('aov_dig_cost')", line)
        self.assertIn(" aov_delve_deeper_no_gold:0 ", loc)

    def test_ruin_event_tells_of_a_lost_dig(self):
        e = effect_block("aov_hold_ruin_effect")
        self.assertRegex(e, r"limit = \{ aov_hold_dig_running = yes \}\s*save_scope_value_as = \{ name = aov_lost_dig")
        self.assertLess(e.index("aov_lost_dig"), e.index("aov_hold_end_dig_effect"))
        self.assertIn("scope:aov_lost_dig", read("events/aov_hold_ruin_events.txt"))
        self.assertIn(" aov_hold_ruin.1.desc.lost_dig:0 ", read("localization/english/aov_hold_ruin_l_english.yml"))

    def test_picker_excludes_running_digs(self):
        ev = event_block("aov_hold_delve.1")
        for h in holds.HOLDS:
            self.assertIn(f"title:{h['barony']}", ev)
        self.assertGreaterEqual(ev.count("aov_can_dig_at = yes"), 9)
        self.assertGreaterEqual(ev.count("aov_hold_start_dig_effect = yes"), 9)
        self.assertGreaterEqual(ev.count("remove_short_term_gold"), 9)

    def test_picker_ai_weights_positive_and_reserve(self):
        ev = event_block("aov_hold_delve.1")
        opts = [o for o in ev.split("	option = {")[1:] if "aov_hold_delve.1.hold_" in o]
        self.assertEqual(len(opts), 9)
        for o in opts:
            m = re.search(r"ai_chance = \{\s*base = (\d+)", o)
            self.assertTrue(m and int(m.group(1)) >= 1, o)   # positive floor: never all zero
            self.assertNotIn("subtract", o)
            self.assertIn("divide = title:", o)   # inverse-cost weight favours cheap holds
            self.assertRegex(o, r"trigger_if = \{\s*limit = \{ scope:digger = \{ is_ai = yes \} \}\s*scope:digger\.gold >= \{\s*value = aov_dig_cost\s*multiply = 2")
        self.assertRegex(ev, r"aov_hold_delve\.1\.cancel\s*ai_chance = \{ base = 0 \}")

    def test_progress_desc_per_hold(self):
        d = decision_block("aov_delve_deeper_decision")
        self.assertGreaterEqual(d.count("triggered_desc"), 9)
        self.assertIn("aov_hold_dig_running = yes", d)

    def test_ai_reserve_and_cheapest_hold(self):
        d = decision_block("aov_delve_deeper_decision")
        self.assertIn("ai_check_interval = 12", d)
        self.assertRegex(d, r"multiply = 2|2 \*|value = 2")


if __name__ == "__main__":
    unittest.main()
