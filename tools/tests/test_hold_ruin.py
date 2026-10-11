"""Static checks on hold ruin by conquest and restoration.

    python -I -m unittest discover -s tools/tests -p test_hold_ruin.py
"""

import re
import sys
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(MOD / "tools" / "data"))
import holds  # noqa: E402


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def top_block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


def on_action_block(name):
    return top_block(read("common/on_action/aov_hold_on_actions.txt"), name)


def event_block(name):
    return top_block(read("events/aov_hold_ruin_events.txt"), name)


class HoldRuinTests(unittest.TestCase):
    def test_ruin_requires_conquest_and_non_dwarf(self):
        block = on_action_block("aov_hold_on_title_gain")
        for flag in ("conquest", "conquest_claim", "conquest_holy_war", "conquest_populist"):
            self.assertIn(f"flag:{flag}", block)
        self.assertIn("is_dwarvish_culture = yes", block)
        self.assertRegex(block, r"NOT = \{\s*is_dwarvish_culture = yes")
        self.assertNotIn("flag:inheritance", block)
        self.assertIn("aov_hold_ruin_effect = yes", block)
        self.assertIn("on_title_gain = {\n\ton_actions = { aov_hold_on_title_gain aov_hold_restoration_handover }", read("common/on_action/aov_hold_on_actions.txt"))

    def test_ruin_effect(self):
        text = read("common/scripted_effects/aov_hold_effects.txt")
        b = top_block(text, "aov_hold_ruin_effect")
        for needle in ("aov_hold_ruined", "aov_dig_progress", "modifier = aov_ruined_hold",
                       "aov_hold_end_campaign_effect = yes", "aov_hold_ruin.1"):
            self.assertIn(needle, b)
        e = top_block(text, "aov_hold_end_campaign_effect")
        self.assertIn("remove_variable = aov_dig_in_progress", e)

    def test_restoration_follows_dwarven_holder(self):
        ev = event_block("aov_hold_ruin.3")
        self.assertIn("is_dwarvish_culture = yes", ev)
        self.assertIn("remove_county_modifier = aov_ruined_hold", ev)
        self.assertIn("remove_province_modifier = aov_restoring_hold", ev)
        self.assertIn("remove_variable = aov_hold_ruined", ev)

    def test_decision_costs(self):
        d = top_block(read("common/decisions/aov_hold_decisions.txt"), "aov_clear_ruins_decision")
        self.assertIn(f"gold = {holds.RESTORE['gold']}", d)
        self.assertIn(f"prestige = {holds.RESTORE['prestige']}", d)
        self.assertIn("is_dwarvish_culture = yes", d)
        self.assertIn("aov_hold_ruin.2", d)
        eff = read("common/scripted_effects/aov_hold_effects.txt")
        self.assertIn(f"years = {holds.RESTORE['years']}", top_block(eff, "aov_hold_begin_restoration_effect"))

    def test_one_option_per_hold(self):
        ev = event_block("aov_hold_ruin.2")
        options = re.findall(r"^\toption = \{\n(.*?)^\t\}", ev, re.M | re.S)
        self.assertEqual(len(options), len(holds.HOLDS))
        for hold, opt in zip(holds.HOLDS, options):
            self.assertIn(f"title:{hold['barony']}", opt)
            self.assertIn("aov_hold_ruined", opt.replace("aov_hold_is_ruined", "aov_hold_ruined"))
            self.assertIn("restoring_hold", opt)

    def test_loc_keys_exist(self):
        loc = read("localization/english/aov_hold_ruin_l_english.yml")
        for n in (1, 2, 3):
            self.assertIn(f"aov_hold_ruin.{n}.t:", loc)
        self.assertIn("aov_clear_ruins_decision:", loc)


if __name__ == "__main__":
    unittest.main()
