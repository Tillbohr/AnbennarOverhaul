"""The hand-written tribal script: forming titles, raising vassals, and (Task 9) duels."""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import pdx_script  # noqa: E402

SUBMOD = Path(__file__).resolve().parents[2]
TIERS = {"duchy": "tier_county", "kingdom": "tier_duchy", "empire": "tier_kingdom"}


def read(rel: str) -> str:
    return (SUBMOD / rel).read_text(encoding="utf-8-sig")


def blocks(text: str) -> dict:
    return pdx_script.parse_blocks(pdx_script.strip_comments(text))


def section(body: str, name: str) -> str:
    """The block `name = { ... }` one tab into a top-level block."""
    return re.search(rf"(?m)^\t{name} = \{{\n(.*?)^\t\}}", body, re.S).group(1)


class FormDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decisions = blocks(read("common/decisions/aov_tribes_decisions.txt"))

    def decision(self, tier):
        return self.decisions[f"aov_form_tribal_{tier}_decision"]

    def test_form_decisions_tier_gates(self):
        for tier, below in TIERS.items():
            self.assertIn(f"highest_held_title_tier = {below}", section(self.decision(tier), "is_shown"), tier)

    def test_form_decisions_use_values(self):
        for tier in TIERS:
            body = self.decision(tier)
            self.assertIn(f"sub_realm_size >= aov_form_{tier}_counties", section(body, "is_valid"), tier)
            self.assertIn(f"prestige = aov_form_{tier}_prestige", section(body, "cost"), tier)

    def test_form_decisions_gate_on_government(self):
        for tier in TIERS:
            self.assertIn("government_has_flag = government_is_dwarovar_tribe",
                          section(self.decision(tier), "is_shown"), tier)

    def test_form_decisions_independent_or_not(self):
        # a vassal count may form a duchy; the tier gate and the county count are the only limits
        for tier in TIERS:
            self.assertNotIn("is_independent_ruler", self.decision(tier), tier)

    def test_form_decisions_need_a_free_title(self):
        for tier in TIERS:
            valid = section(self.decision(tier), "is_valid")
            self.assertRegex(valid, rf"custom_description = \{{\s*text = aov_tribe_no_free_title\s*"
                                    rf"aov_tribe_has_free_title_trigger = \{{ TIER = {tier} \}}", tier)

    def test_form_effect_transfers_the_saved_title(self):
        for tier in TIERS:
            effect = section(self.decision(tier), "effect")
            self.assertIn(f"aov_tribe_take_free_title_effect = {{ TIER = {tier} }}", effect, tier)
            self.assertIn("type = created", effect, tier)
            self.assertRegex(effect, r"scope:aov_new_title = \{\s*change_title_holder = \{\s*holder = root", tier)
            self.assertIn("resolve_title_and_vassal_change = scope:change", effect, tier)

    def test_ai_does_not_rush(self):
        for tier in TIERS:
            body = self.decision(tier)
            self.assertRegex(body, r"(?m)^\tai_check_interval = 60$", tier)
            self.assertRegex(section(body, "ai_will_do"), r"factor = 0", tier)


class RaiseVassalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = blocks(read("common/character_interactions/aov_tribes_interactions.txt"))[
            "aov_raise_tribal_vassal_interaction"]

    def test_raise_tier_rules(self):
        shown = section(self.body, "is_shown")
        self.assertIn("scope:recipient = {", shown)
        self.assertIn("liege = scope:actor", shown)
        self.assertEqual(shown.count("government_has_flag = government_is_dwarovar_tribe"), 2)
        self.assertRegex(shown, r"scope:actor = \{ highest_held_title_tier = tier_kingdom \}\s*"
                                r"scope:recipient = \{ highest_held_title_tier <= tier_county \}")
        self.assertRegex(shown, r"scope:actor = \{ highest_held_title_tier = tier_empire \}\s*"
                                r"scope:recipient = \{ highest_held_title_tier <= tier_duchy \}")

    def test_grants_one_tier_below_the_actor(self):
        accept = section(self.body, "on_accept")
        self.assertRegex(accept, r"highest_held_title_tier = tier_kingdom \}\s*\}\s*scope:recipient = \{\s*"
                                 r"aov_tribe_take_free_title_effect = \{ TIER = duchy \}")
        self.assertRegex(accept, r"scope:recipient = \{\s*aov_tribe_take_free_title_effect = \{ TIER = kingdom \}")
        self.assertRegex(accept, r"change_title_holder = \{\s*holder = scope:recipient")

    def test_duke_cannot_raise(self):
        shown = section(self.body, "is_shown")
        self.assertRegex(shown, r"scope:actor = \{[^}]*highest_held_title_tier >= tier_kingdom", re.S)

    def test_cost_and_auto_accept(self):
        self.assertRegex(self.body, r"(?m)^\tauto_accept = yes$")
        self.assertIn("prestige = aov_raise_prestige", section(self.body, "cost"))

    def test_needs_a_free_title(self):
        valid = section(self.body, "is_valid_showing_failures_only")
        self.assertIn("text = aov_tribe_no_free_title", valid)
        self.assertIn("aov_tribe_has_free_title_trigger = { TIER = duchy }", valid)
        self.assertIn("aov_tribe_has_free_title_trigger = { TIER = kingdom }", valid)


class LocTests(unittest.TestCase):
    def test_loc_complete(self):
        loc = read("localization/english/aov_tribes_decisions_l_english.yml")
        keys = ["aov_raise_tribal_vassal_interaction", "aov_raise_tribal_vassal_interaction_desc",
                "aov_tribe_no_free_title"]
        for tier in TIERS:
            base = f"aov_form_tribal_{tier}_decision"
            keys += [base, f"{base}_desc", f"{base}_tooltip", f"{base}_confirm"]
        self.assertEqual([k for k in keys if not re.search(rf'(?m)^ {k}:\d* ?"', loc)], [])


if __name__ == "__main__":
    unittest.main()
