"""Tests for the hand-written Elven Haven script: game-start conversion, the Raise an Elven Haven decision, its picker
event, values and localization (spec docs/superpowers/specs/2026-10-25-rie-elves-design.md Section 4).

    python -I -m unittest discover -s tools/tests -p test_elven_haven_decision.py -v
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_portraits as bp  # noqa: E402
from data import rie_elves as data  # noqa: E402

SUBMOD = bp.SUBMOD
ON_ACTIONS = "common/on_action/aov_elven_haven_on_actions.txt"
DECISIONS = "common/decisions/aov_elven_haven_decisions.txt"
EVENTS = "events/aov_elven_haven_events.txt"
VALUES = "common/script_values/aov_elven_haven_conversion_values.txt"
TRIGGERS = "common/scripted_triggers/aov_elven_haven_triggers.txt"
EFFECTS = "common/scripted_effects/aov_elven_haven_decision_effects.txt"
LOC = "localization/english/aov_elven_haven_decisions_l_english.yml"


def read(rel: str) -> str:
    return (SUBMOD / rel).read_bytes().decode("utf-8-sig")


def blocks(text: str) -> dict:
    return {names[0]: text[start:end] for names, start, end in bp.blocks(text, 1, strict=False)}


class FileFormatTests(unittest.TestCase):
    def test_files_have_bom_and_lf(self):
        for rel in (ON_ACTIONS, DECISIONS, EVENTS, VALUES, TRIGGERS, EFFECTS, LOC):
            raw = (SUBMOD / rel).read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"), rel)
            self.assertNotIn(b"\r\n", raw, rel)


class GameStartTests(unittest.TestCase):
    def test_on_game_start_is_appended(self):
        found = blocks(read(ON_ACTIONS))
        self.assertRegex(found["on_game_start"], r"on_actions = \{ aov_elven_haven_game_start \}")
        self.assertNotIn("effect", found["on_game_start"])

    def test_game_start_converts_eligible_baronies(self):
        body = blocks(read(ON_ACTIONS))["aov_elven_haven_game_start"]
        self.assertIn("aov_can_become_elven_haven_trigger = yes", body)
        self.assertIn("aov_convert_to_elven_haven_effect = yes", body)

    def test_game_start_needs_an_elven_county_culture(self):
        # An elf ruling a human county (Eborthíl, Tefori culture) converts it by decision, not at game start.
        body = blocks(read(ON_ACTIONS))["aov_elven_haven_game_start"]
        self.assertRegex(body, r"culture = \{ has_elvish_heritage = yes \}")

    def test_eligible_means_elf_held_castle_or_tribe(self):
        body = blocks(read(TRIGGERS))["aov_can_become_elven_haven_trigger"]
        self.assertIn("has_holding_type = castle_holding", body)
        self.assertIn("has_holding_type = tribal_holding", body)
        self.assertIn("is_elvish_culture = yes", body)
        self.assertNotIn("city_holding", body)


class DecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision = blocks(read(DECISIONS))["aov_raise_elven_haven_decision"]

    def test_decision_needs_an_elf(self):
        self.assertIn("is_elvish_culture = yes", self.decision)

    def test_decision_has_a_five_year_cooldown(self):
        self.assertIn("cooldown = { years = 5 }", self.decision)

    def test_decision_opens_the_picker(self):
        self.assertIn("trigger_event = aov_elven_haven.1", self.decision)

    def test_option_charges_gold_and_prestige(self):
        effect = blocks(read(EFFECTS))["aov_raise_elven_haven_effect"]
        self.assertIn("remove_short_term_gold = scope:aov_haven_cost", effect)
        self.assertIn("add_prestige = -100", effect)
        self.assertIn("aov_convert_to_elven_haven_effect = yes", effect)

    def test_picker_offers_three_choices(self):
        event = blocks(read(EVENTS))["aov_elven_haven.1"]
        for n in (1, 2, 3):
            self.assertIn(f"save_scope_as = aov_haven_choice_{n}", event)
            self.assertIn(f"CHOICE = aov_haven_choice_{n}", event)


class ValueTests(unittest.TestCase):
    def test_target_level_agrees_with_level_map(self):
        body = blocks(read(VALUES))["aov_elven_haven_target_level"]
        for key, level in data.LEVEL_MAP.items():
            if level > 1:
                self.assertRegex(body, rf"has_building_or_higher = {key} \}}\s*value = {level}\b", key)

    def test_cost_is_100_per_level(self):
        body = blocks(read(VALUES))["aov_elven_haven_conversion_cost"]
        self.assertIn("value = aov_elven_haven_target_level", body)
        self.assertIn("multiply = 100", body)


class LocTests(unittest.TestCase):
    def test_every_named_key_has_loc(self):
        loc = read(LOC)
        script = bp.code(read(DECISIONS) + read(EVENTS) + read(TRIGGERS))
        keys = set(re.findall(r"\b(?:name|title|desc|text|custom_tooltip)\s*=\s*((?:aov_elven_haven\.|aov_raise_)[\w.]+)",
                              script))
        keys |= {"aov_raise_elven_haven_decision", "aov_raise_elven_haven_decision_desc",
                 "aov_raise_elven_haven_decision_tooltip", "aov_raise_elven_haven_decision_confirm"}
        self.assertGreater(len(keys), 8)
        for key in sorted(keys):
            self.assertRegex(loc, rf"(?m)^ {re.escape(key)}:", key)
        self.assertIsNone(re.search(data.FORBIDDEN_LORE, loc))
        self.assertNotIn("[elven_holding|E]", loc)  # no such game concept


if __name__ == "__main__":
    unittest.main()
