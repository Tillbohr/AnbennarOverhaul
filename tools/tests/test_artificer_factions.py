"""Static checks on the artificer factions (titles, influence, elections, Factions tab).

    python -I -m unittest discover -s tools/tests -v
"""

import re
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent
FACTIONS = ("brillites", "mechanists", "technomancers")
LEVELS = ("hostile", "displeased", "favored", "exalted")


def read(rel):
    return (MOD / rel).read_text(encoding="utf-8-sig")


def block(text, name):
    m = re.search(rf"^{re.escape(name)} = \{{\n(.*?)\n^\}}", text, re.M | re.S)
    assert m, name
    return m.group(1)


class TitleTests(unittest.TestCase):
    def test_three_landless_duchies(self):
        text = read("common/landed_titles/aov_artificer_faction_titles.txt")
        for f in FACTIONS:
            b = block(text, f"d_{f}")
            for line in ("landless = yes", "definite_form = yes", "ruler_uses_title_name = no",
                         "no_automatic_claims = yes", "can_use_nomadic_naming = no", "capital = c_nimscodd"):
                self.assertIn(line, b)
            self.assertNotIn("always_follows_primary_heir", b)

    def test_coats_of_arms_use_cogs(self):
        text = read("common/coat_of_arms/coat_of_arms/aov_artificer_factions.txt")
        self.assertIn("ce_anb_cog", block(text, "d_brillites"))
        self.assertIn("ce_anb_crystal_magic", block(text, "d_brillites"))
        self.assertIn("pattern_checkers_01", block(text, "d_mechanists"))
        self.assertEqual(block(text, "d_mechanists").count("ce_anb_cog.dds"), 2)
        self.assertIn("ce_anb_cog_02", block(text, "d_technomancers"))

    def test_revoke_override_keeps_anbennar_and_excludes_faction_titles(self):
        ours = block(read("common/scripted_triggers/zz_aov_interaction_triggers.txt"), "title_revocation_standard_can_pick_title_trigger")
        base = (MOD.parent / "anbennar-ck3-dev-master/common/scripted_triggers/00_interaction_triggers.txt").read_text(encoding="utf-8-sig")
        for line in block(base, "title_revocation_standard_can_pick_title_trigger").splitlines():
            self.assertIn(line, ours)
        self.assertIn("aov_is_artificer_faction_title = no", ours)

    def test_faction_title_trigger(self):
        b = block(read("common/scripted_triggers/aov_artificer_faction_triggers.txt"), "aov_is_artificer_faction_title")
        for f in FACTIONS:
            self.assertIn(f"this = title:d_{f}", b)


class InfluenceTests(unittest.TestCase):
    def test_twelve_modifiers(self):
        text = read("common/modifiers/aov_artificer_faction_modifiers.txt")
        for f in FACTIONS:
            for lv in LEVELS:
                block(text, f"aov_{f}_{lv}")
        self.assertIn("domain_tax_mult = 0.1", block(text, "aov_mechanists_exalted"))
        self.assertIn("domain_tax_mult = -0.1", block(text, "aov_mechanists_hostile"))
        self.assertIn("learning = 2", block(text, "aov_brillites_exalted"))
        self.assertIn("advantage = -5", block(text, "aov_technomancers_hostile"))

    def test_level_thresholds(self):
        b = block(read("common/script_values/aov_artificer_faction_values.txt"), "aov_influence_level_brillites")
        for n in ("15", "30", "60", "85"):
            self.assertIn(f">= {n}", b)

    def test_costs_and_quarters(self):
        text = read("common/script_values/aov_artificer_faction_values.txt")
        cost = block(text, "aov_research_cost_mechanists")
        for v in ("100", "75", "50", "38", "25"):
            self.assertIn(f"value = {v}", cost)
        q = block(text, "aov_research_quarters_technomancers")
        for v in ("75", "60", "45"):
            self.assertIn(f"value = {v}", q)

    def test_change_influence_clamps(self):
        b = block(read("common/scripted_effects/aov_artificer_faction_effects.txt"), "aov_faction_change_influence")
        self.assertIn("min = 0", b)
        self.assertIn("max = 100", b)
        self.assertIn("aov_faction_refresh_modifiers = yes", b)


if __name__ == "__main__":
    unittest.main()
