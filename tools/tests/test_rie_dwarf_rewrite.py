"""Tests for tools/rie_dwarf_rewrite.py and tools/data/rie_dwarves.py.

    python -I -m unittest discover -s tools/tests -p test_rie_dwarf_rewrite.py -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rie_dwarf_rewrite as rw  # noqa: E402
from data import rie_dwarves as data  # noqa: E402


def enabled(inner):
    return "x_01 = {\n\tis_enabled = {\n" + inner + "\t}\n}\n"


class RewriteTests(unittest.TestCase):
    def test_is_dwarf_becomes_anbennar_trigger(self):
        out, _ = rw.rewrite_block(enabled("\t\tscope:holder = { is_dwarf = yes }\n"), set())
        self.assertIn("is_dwarvish_culture = yes", out)
        self.assertNotIn("is_dwarf ", out)

    def test_orc_branch_leaves_no_empty_or(self):
        out, _ = rw.rewrite_block(enabled(
            "\t\tOR = {\n\t\t\tscope:holder = { is_dwarf = yes }\n\t\t\tscope:holder = { is_orc = yes }\n\t\t}\n"), set())
        self.assertNotIn("is_orc", out)
        self.assertEqual(out.count("OR = {"), 1)
        self.assertIn("is_dwarvish_culture = yes", out)

    def test_only_orc_or_is_removed_whole(self):
        out, _ = rw.rewrite_block(enabled("\t\tOR = { is_orc = yes }\n\t\talways = yes\n"), set())
        self.assertNotIn("OR", out)
        self.assertIn("always = yes", out)

    def test_depths_become_hold_levels(self):
        out, _ = rw.rewrite_block(enabled("\t\thas_building_or_higher = dwarven_depths_04\n"), set())
        self.assertIn("has_building_or_higher = dwarven_hold_04", out)
        self.assertNotIn("depths", out)

    def test_dynasty_modifier_block_removed(self):
        out, notes = rw.rewrite_block(
            "x_01 = {\n\tprovince_dynasty_modifier = {\n\t\tcounty_holder_dynasty_perk = lotr_khazad_legacy_5\n"
            "\t\tmonthly_income = 0.1\n\t}\n\tcounty_modifier = {\n\t\tdevelopment_growth_factor = 0.02\n\t}\n}\n", set())
        self.assertNotIn("province_dynasty_modifier", out)
        self.assertNotIn("monthly_income", out)
        self.assertIn("development_growth_factor = 0.02", out)
        self.assertTrue(any("lotr_khazad_legacy_5" in n for n in notes))

    def test_dynasty_perk_tooltip_removed(self):
        out, _ = rw.rewrite_block(enabled(
            "\t\tscope:holder = { is_dwarf = yes }\n\t\tcustom_tooltip = {\n"
            "\t\t\ttext = dwarven_forge_dynasty_requirement\n"
            "\t\t\tcounty.holder.dynasty ?= { has_dynasty_perk = lotr_crafting_legacy_3 }\n\t\t}\n"), set())
        self.assertNotIn("custom_tooltip", out)
        self.assertNotIn("dynasty", out)
        self.assertIn("is_dwarvish_culture", out)

    def test_goat_innovation_condition_removed(self):
        out, _ = rw.rewrite_block(enabled(
            "\t\tscope:holder = {\n\t\t\tculture = { has_innovation = innovation_iron_hills_goat_domestication }\n\t\t}\n"
            "\t\talways = yes\n"), set())
        self.assertNotIn("innovation", out)
        self.assertNotIn("culture", out)
        self.assertNotIn("scope:holder", out)
        self.assertIn("always = yes", out)

    def test_unlock_full_delving_ungated(self):
        out, _ = rw.rewrite_block(
            "x_01 = {\n\tcounty_culture_modifier = {\n\t\tparameter = unlock_full_delving\n"
            "\t\tdevelopment_growth = 0.05\n\t}\n}\n", set())
        self.assertIn("county_modifier = {", out)
        self.assertNotIn("county_culture_modifier", out)
        self.assertNotIn("parameter", out)
        self.assertIn("development_growth = 0.05", out)

    def test_known_parameter_kept(self):
        src = "x_01 = {\n\tcounty_culture_modifier = {\n\t\tparameter = quarries_building_bonuses\n\t}\n}\n"
        out, _ = rw.rewrite_block(src, {"quarries_building_bonuses"})
        self.assertEqual(out, src)

    def test_unknown_parameter_block_removed(self):
        out, notes = rw.rewrite_block(
            "x_01 = {\n\tcounty_culture_modifier = {\n\t\tparameter = rie_only_thing\n\t\tmonthly_income = 1\n\t}\n"
            "\tdaily_cost = 1\n}\n", set())
        self.assertNotIn("rie_only_thing", out)
        self.assertNotIn("monthly_income", out)
        self.assertIn("daily_cost = 1", out)
        self.assertTrue(any("rie_only_thing" in n for n in notes))

    def test_crafting_effect_desc_removed(self):
        out, _ = rw.rewrite_block(
            "x_01 = {\n\teffect_desc = dwarven_forge_01_artifact_crafting_buff\n\teffect_desc = other_desc\n}\n", set())
        self.assertNotIn("crafting_buff", out)
        self.assertIn("effect_desc = other_desc", out)

    def test_terrain_triggers_renamed(self):
        out, _ = rw.rewrite_block(enabled(
            "\t\tlotr_dwarven_hill_buildings_requirement_terrain = yes\n"
            "\t\tlotr_dwarven_mountain_buildings_requirement_terrain = yes\n"
            "\t\tlotr_dwarven_underground_buildings_requirement_terrain = yes\n"
            "\t\tlotr_dwarven_is_surface_dwarf = yes\n\t\tlotr_dwarven_is_mountain_dwarf = yes\n"
            "\t\tlotr_subterranean_buildings = yes\n"), set())
        for new in ("aov_rie_hill_terrain_trigger = yes", "aov_rie_mountain_terrain_trigger = yes",
                    "aov_rie_hold_province_trigger = yes", "aov_rie_surface_dwarf_trigger = yes",
                    "aov_rie_dwarven_holder_trigger = yes", "is_dwarvish_culture = yes"):
            self.assertIn(new, out)
        self.assertNotIn("lotr_", out)

    def test_four_space_indentation_handled(self):
        tab = enabled("\t\tOR = {\n\t\t\tscope:holder = { is_dwarf = yes }\n\t\t\tscope:holder = { is_orc = yes }\n\t\t}\n")
        spaced = tab.replace("\t", "    ")
        out_tab, _ = rw.rewrite_block(tab, set())
        out_spaced, _ = rw.rewrite_block(spaced, set())
        self.assertEqual(out_tab.replace("\t", "    "), out_spaced)

    def test_crlf_input_gives_lf(self):
        out, _ = rw.rewrite_block(enabled("\t\tis_dwarf = yes\n").replace("\n", "\r\n"), set())
        self.assertNotIn("\r", out)

    def test_elven_alternative_removed_but_siblings_stay(self):
        out, _ = rw.rewrite_block(
            "x_01 = {\n\tcan_construct = {\n\t\tOR = {\n\t\t\thas_building_or_higher = dwarven_depths_01\n"
            "\t\t\thas_building_or_higher = elven_settlement_01\n\t\t}\n\t}\n}\n", set())
        self.assertNotIn("elven", out)
        self.assertIn("has_building_or_higher = dwarven_hold_01", out)

    def test_comments_are_left_alone(self):
        out, _ = rw.rewrite_block(enabled("\t\t# is_orc = yes and is_dwarf\n\t\talways = yes\n"), set())
        self.assertIn("# is_orc = yes and is_dwarf", out)

    def test_prune_empty_recursive(self):
        self.assertEqual(rw.prune_empty("a = {\n\tb = {\n\t\tc = { }\n\t}\n}\nkeep = yes\n"), "keep = yes\n")


class DataTests(unittest.TestCase):
    def test_data_ores_and_weights(self):
        self.assertEqual(len(data.ORES), 15)
        self.assertEqual(set(data.ORE_WEIGHTS), set(data.ORES))
        expected = {"iron": 40, "copper": 40, "tin": 40, "lead": 40, "quartz": 12, "onyx": 12, "peridot": 12,
                    "amethyst": 12, "silver": 8, "gold": 6, "sapphire": 4, "emerald": 4, "ruby": 4, "diamond": 3,
                    "mithril": 1}
        self.assertEqual(data.ORE_WEIGHTS, expected)

    def test_start_deposits_and_mines(self):
        self.assertEqual(data.START_DEPOSITS, {"b_hul_az_amekh": "ruby", "b_gulandhum": "gold",
                                               "b_anvilwright": "silver"})
        self.assertEqual(data.MINE_BUILDINGS[0], "mithril_mines_01")
        self.assertEqual(len(data.MINE_BUILDINGS), 15)
        self.assertEqual(len(data.HOLD_BUILDINGS), 35)
        self.assertEqual(len(data.SURFACE_BUILDINGS), 11)
        self.assertFalse(any(b.startswith(("oath_", "breweries")) for b in data.HOLD_BUILDINGS))


if __name__ == "__main__":
    unittest.main()
