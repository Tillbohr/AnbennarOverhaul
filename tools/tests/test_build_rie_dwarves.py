"""Tests for tools/build_rie_dwarves.py (RiE dwarf buildings, mines, ore deposits).

    python -I -m unittest discover -s tools/tests -p test_build_rie_dwarves.py -v
"""

import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_portraits as bp  # noqa: E402
import build_rie_dwarves as rd  # noqa: E402
import rie_dwarf_rewrite as rw  # noqa: E402
from data import rie_dwarves as data  # noqa: E402

REAL = rd.Roots.default()
HAVE_REAL = REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir()
LEFTOVER = re.compile(r"\blotr_|\bis_dwarf\b|\bis_orc\b|dwarven_depths_|elven_settlement_")


def write_holdings(rie: Path) -> None:
    """RiE's two holdings files, as far as check_holding_lists reads them, agreeing with the data."""
    def group(title, keys):
        return "\t\t#" + title + "\n" + "".join(f"\t\t{key}\n" for key in keys) + "\n"
    mines = len(data.MINE_BUILDINGS)
    hold = ("dwarven_holding = {\n\tbuildings = {\n" + group("Crafting Resource Mines", data.HOLD_BUILDINGS[:mines])
            + group("Dwarven buildings", data.HOLD_BUILDINGS[mines:]) + group("orcish buildings", ["slave_farms_01"])
            + "\t}\n}\n")
    castle = ("castle_holding = {\n\tbuildings = {\n" + group("Dwarven buildings", data.SURFACE_BUILDINGS)
              + group("Crafting Resource Mines", data.MINE_BUILDINGS) + "\t}\n}\n")
    for rel, text in (("common/holdings/lotr_holdings.txt", hold), ("common/holdings/00_holdings.txt", castle)):
        (rie / rel).parent.mkdir(parents=True, exist_ok=True)
        (rie / rel).write_text(text, encoding="utf-8")


def fake_roots(tmp: Path, dwarf_text: str, anbennar_buildings: str = "") -> rd.Roots:
    rie, anbennar, game = tmp / "rie", tmp / "anbennar", tmp / "game"
    write_holdings(rie)
    for rel, text in ((data.RIE_BUILDING_FILES[0], dwarf_text), (data.RIE_BUILDING_FILES[1], "")):
        (rie / rel).parent.mkdir(parents=True, exist_ok=True)
        (rie / rel).write_text(text, encoding="utf-8")
    (anbennar / "common/buildings").mkdir(parents=True)
    (anbennar / "common/buildings/00_test.txt").write_text(anbennar_buildings, encoding="utf-8")
    (game / "game/common").mkdir(parents=True)
    return rd.Roots(rie=rie, anbennar=anbennar, game=game)


def top_keys(text: str) -> list:
    return [names[0] for names, _s, _e in bp.blocks(text, 1, strict=False)]


def block_of(text: str, key: str) -> str:
    for names, start, end in bp.blocks(text, 1, strict=False):
        if names[0] == key:
            return text[start:end]
    raise KeyError(key)


def sub_block(body: str, name: str) -> str:
    """The first depth-2 block called name inside a building block ('' when absent)."""
    for names, start, end in bp.blocks(body, 2, strict=False):
        if names[-1] == name:
            return body[start:end]
    return ""


class StopTests(unittest.TestCase):
    def test_unknown_trigger_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tis_enabled = {\n\t\tlotr_made_up = yes\n\t}\n}\n")
            with self.assertRaises(rd.GeneratorError) as caught:
                rd.build_all(roots)
            self.assertIn("lotr_made_up", str(caught.exception))
            self.assertIn("dwarven_test_01", str(caught.exception))

    def test_key_collision_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tcost_gold = 10\n}\n",
                               "dwarven_test_01 = {\n\tcost_gold = 20\n}\n")
            with self.assertRaises(rd.GeneratorError) as caught:
                rd.build_all(roots)
            self.assertIn("dwarven_test_01", str(caught.exception))


    def test_unrenamed_rie_trigger_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tis_enabled = {\n\t\trie_only_trigger = yes\n\t}\n}\n")
            (roots.rie / "common/scripted_triggers").mkdir(parents=True)
            (roots.rie / "common/scripted_triggers/x.txt").write_text("rie_only_trigger = {\n\talways = yes\n}\n")
            with self.assertRaisesRegex(rd.GeneratorError, "RiE scripted trigger rie_only_trigger has no rename"):
                rd.build_all(roots)

    def test_unknown_innovation_stops_build(self):
        # The goat innovation is rewritten away; any other RiE innovation Anbennar lacks must stop the build.
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tcan_construct_potential = {\n\t\tscope:holder = {"
                                          " culture = { has_innovation = innovation_rie_only } }\n\t}\n}\n")
            with self.assertRaisesRegex(rd.GeneratorError, "dwarven_test_01: innovation innovation_rie_only"):
                rd.render_buildings(rd.Build(roots, []))

    def test_goat_innovation_rewritten_in_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tcan_construct_potential = {\n\t\tscope:holder = {\n"
                                          "\t\t\tculture = {\n\t\t\t\thas_innovation = "
                                          "innovation_iron_hills_goat_domestication\n\t\t\t}\n\t\t}\n\t}\n}\n")
            build = rd.Build(roots, [])
            rd.render_buildings(build)
            out = build.files[rd.BUILDINGS_FILE].decode("utf-8-sig")
            self.assertIn("scope:holder = { is_dwarvish_culture = yes }", out)
            self.assertNotIn("innovation", out)

    def test_unknown_modifier_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tprovince_modifier = {\n\t\tmade_up_mult = 1\n\t}\n}\n")
            with self.assertRaisesRegex(rd.GeneratorError, "dwarven_test_01: modifier made_up_mult"):
                rd.build_all(roots)

    def test_rie_value_copied_with_its_variables(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tlevy = rie_value\n}\n")
            (roots.rie / "common/script_values").mkdir(parents=True)
            (roots.rie / "common/script_values/v.txt").write_text(
                "@unused = 5\n@a = 1\n@b = @[a + 1]\nrie_value = @[b]\nother = 2\n")
            build = rd.Build(roots, [])
            rd.render_buildings(build)
            rd.render_values(build)
            text = build.files[rd.VALUES_FILE].decode("utf-8-sig")
            self.assertIn("@a = 1\n@b = @[a + 1]\n", text)
            self.assertIn("\nrie_value = @[b]\n", text)
            self.assertNotIn("unused", text)
            self.assertNotIn("other", text)

    def test_unknown_value_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tlevy = nowhere_value\n}\n")
            with self.assertRaisesRegex(rd.GeneratorError, "script value nowhere_value"):
                rd.build_all(roots)


    def _loc_build(self, tmp: Path, name: str) -> rd.Build:
        roots = fake_roots(tmp, "dwarven_test_01 = {\n\tcost_gold = 10\n}\n")
        (roots.rie / "localization/english").mkdir(parents=True)
        (roots.rie / "localization/english/x_l_english.yml").write_text(
            f'﻿l_english:\n building_dwarven_test_01: "{name}"\n building_type_dwarven_test_01: "Test"\n',
            encoding="utf-8")
        build = rd.Build(roots, [])
        rd.render_buildings(build)
        return build

    def test_unmapped_concept_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(data, "LOC_OVERRIDES", {}):
            build = self._loc_build(Path(tmp), "A [made_up_concept|E] hall")
            with self.assertRaisesRegex(rd.GeneratorError, "building_dwarven_test_01: game concept made_up_concept"):
                rd.render_loc(build)

    def test_mapped_concept_becomes_words(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(data, "LOC_OVERRIDES", {}):
            build = self._loc_build(Path(tmp), "[dwarves|E] dig. Then [dwarves|E] drink with [middleearth|e].")
            rd.render_loc(build)
            text = build.files[rd.LOC_FILE].decode("utf-8-sig")
            self.assertIn('building_dwarven_test_01: "Dwarves dig. Then dwarves drink with Halann."', text)

    def test_unoverridden_lore_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(data, "LOC_OVERRIDES", {}):
            build = self._loc_build(Path(tmp), "Hall of the Iron Hills")
            with self.assertRaisesRegex(rd.GeneratorError, "Middle-earth lore.*building_dwarven_test_01"):
                rd.render_loc(build)

    def test_override_replaces_line_and_stale_override_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(data, "LOC_OVERRIDES", {"building_dwarven_test_01": "Hall of Halann"}):
                build = self._loc_build(Path(tmp), "Hall of the Iron Hills")
                rd.render_loc(build)
                self.assertIn('building_dwarven_test_01: "Hall of Halann"',
                              build.files[rd.LOC_FILE].decode("utf-8-sig"))
            with mock.patch.object(data, "LOC_OVERRIDES", {"building_gone_01": "x"}):
                with self.assertRaisesRegex(rd.GeneratorError, "building_gone_01"):
                    rd.render_loc(build)


class OtherRulesTests(unittest.TestCase):
    """The checks and the loc copy with a rules module other than the dwarf data (the elf generator's)."""

    class Rules:
        TOKEN_RENAMES = {"rie_elf_trigger": "aov_rie_elven_test_trigger"}
        LOC_OVERRIDES = {}
        CONCEPT_REPLACEMENTS = {"elves": "elves"}
        FORBIDDEN_LORE = r"Lorien"

    def test_trigger_renamed_by_given_rules_is_known(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "")
            code = "aov_rie_elven_test_trigger = yes"
            with self.assertRaisesRegex(rd.GeneratorError, "unknown trigger aov_rie_elven_test_trigger"):
                rd.check_trigger_names(roots, "x_01", code)
            rd.check_trigger_names(roots, "x_01", code, self.Rules)

    def test_copy_loc_uses_given_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "")
            (roots.rie / "localization/english").mkdir(parents=True)
            (roots.rie / "localization/english/x_l_english.yml").write_text(
                '﻿l_english:\n a_desc: "[elves|E] sing"\n b_desc: "In Lorien"\n', encoding="utf-8")
            build = rd.Build(roots, [])
            build.want_loc("a_desc")
            self.assertEqual(rd.copy_loc(build, self.Rules), {"a_desc": 'a_desc: "Elves sing"'})
            build.want_loc("b_desc")
            with self.assertRaisesRegex(rd.GeneratorError, "Middle-earth lore.*b_desc"):
                rd.copy_loc(build, self.Rules)


class DepositTests(unittest.TestCase):
    def _effects(self, tmp: str) -> str:
        build = rd.Build(fake_roots(Path(tmp), ""), [])
        rd.render_deposit_effects(build)
        return build.files[rd.DEPOSIT_EFFECTS_FILE].decode("utf-8-sig")

    def test_unknown_start_ore_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(data, "START_DEPOSITS", {"b_x": "adamant"}):
            with self.assertRaisesRegex(rd.GeneratorError, "adamant"):
                self._effects(tmp)

    def test_roll_weights(self):
        with tempfile.TemporaryDirectory() as tmp:
            roll = block_of(self._effects(tmp), "aov_expedition_roll_deposit_effect")
        weights = {ore: int(w) for w, ore in re.findall(
            r"(?m)^\t+(\d+) = \{\n\t+add_province_modifier = mining_(\w+)_province_modifier\n", roll)}
        self.assertEqual(weights, data.ORE_WEIGHTS)
        for ore in data.ORES:
            self.assertIn(f"set_variable = {{ name = aov_expedition_ore value = flag:{ore} }}", roll)

    def test_roll_and_setup_skip_provinces_with_a_deposit(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = self._effects(tmp)
        guard = "NOT = { aov_rie_has_deposit_trigger = yes }"
        self.assertIn(guard, block_of(text, "aov_expedition_roll_deposit_effect"))
        self.assertEqual(block_of(text, "aov_rie_deposit_setup_effect").count(guard), len(data.START_DEPOSITS))

    def test_start_deposits(self):
        with tempfile.TemporaryDirectory() as tmp:
            setup = block_of(self._effects(tmp), "aov_rie_deposit_setup_effect")
        for barony, ore in (("b_hul_az_amekh", "ruby"), ("b_gulandhum", "gold"), ("b_anvilwright", "silver")):
            self.assertRegex(setup, rf"title:{barony}\.title_province = \{{\n\t\tif = \{{\n(?:.*\n)*?\t+add_province_modifier = "
                                    rf"mining_{ore}_province_modifier", barony)

    def test_triggers_rendered(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = rd.Build(fake_roots(Path(tmp), ""), [])
            rd.render_triggers(build)
            text = build.files[rd.TRIGGERS_FILE].decode("utf-8-sig")
        self.assertEqual(top_keys(text), ["aov_rie_hold_province_trigger", "aov_rie_mountain_terrain_trigger",
                                          "aov_rie_hill_terrain_trigger", "aov_rie_dwarven_holder_trigger",
                                          "aov_rie_surface_dwarf_trigger", "aov_rie_vanilla_building_ground_trigger",
                                          "aov_rie_has_deposit_trigger"])
        self.assertIn("has_holding_type = dwarven_hold_holding", block_of(text, "aov_rie_hold_province_trigger"))
        for terrain in data.HILL_TERRAINS:
            self.assertIn(f"terrain = {terrain}\n", block_of(text, "aov_rie_hill_terrain_trigger"))
        self.assertNotIn("terrain = hills", block_of(text, "aov_rie_mountain_terrain_trigger"))
        self.assertIn("scope:holder = { is_dwarvish_culture = yes }", block_of(text, "aov_rie_dwarven_holder_trigger"))
        surface = block_of(text, "aov_rie_surface_dwarf_trigger")
        self.assertIn("text = aov_rie_surface_dwarf_tt", surface)
        self.assertIn("NOT = { has_holding_type = dwarven_hold_holding }", surface)
        ground = block_of(text, "aov_rie_vanilla_building_ground_trigger")
        self.assertIn("text = aov_rie_vanilla_building_ground_tt", ground)
        self.assertRegex(ground, r"NAND = \{\n\t+scope:holder \?= \{ is_dwarvish_culture = yes \}\n\t+OR = \{\n"
                                 r"\t+has_holding_type = dwarven_hold_holding\n\t+aov_rie_hill_terrain_trigger = yes\n")
        deposit = block_of(text, "aov_rie_has_deposit_trigger")
        for ore in data.ORES:
            self.assertIn(f"has_province_modifier = mining_{ore}_province_modifier", deposit)

    def test_surface_tooltip_has_loc(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(data, "LOC_OVERRIDES", {}):
            build = rd.Build(fake_roots(Path(tmp), ""), [])
            rd.render_loc(build)
        self.assertIn("\n aov_rie_surface_dwarf_tt:", build.files[rd.LOC_FILE].decode("utf-8-sig"))
        self.assertIn("\n aov_rie_vanilla_building_ground_tt:", build.files[rd.LOC_FILE].decode("utf-8-sig"))


TERRAIN_TRIGGERS = """building_requirement_tribal = {
	scope:holder ?= { government_has_flag = government_is_tribal }
}

building_quarries_requirement_terrain = {
	OR = {
		terrain = mountains
		#Anbennar
		terrain = cavern
	}
}

building_logging_camps_requirement_terrain = {
	terrain = forest
}
"""


class TerrainGateTests(unittest.TestCase):
    def _gates(self, tmp: Path, used_negated=True):
        roots = fake_roots(tmp, "")
        (roots.anbennar / "common/scripted_triggers").mkdir(parents=True)
        (roots.anbennar / "common/scripted_triggers/00_building_requirement_triggers.txt").write_text(
            TERRAIN_TRIGGERS, encoding="utf-8")
        (roots.game / "game/common/scripted_triggers").mkdir(parents=True)
        (roots.game / "game/common/scripted_triggers/00_other.txt").write_text(
            "building_hill_farms_requirement_terrain = { terrain = hills }\n", encoding="utf-8")
        build = rd.Build(roots, [])
        if used_negated:
            build.files[rd.BUILDINGS_FILE] = rd.txt_file(
                ["dwarven_forestry_01 = {\n\tcan_construct_potential = {\n"
                 "\t\tbuilding_logging_camps_requirement_terrain = no\n\t}\n}\n"])
        rd.render_terrain_gates(build)
        return build.files[rd.TERRAIN_GATES_FILE].decode("utf-8-sig"), build.notes

    def test_every_terrain_trigger_gets_the_ground_gate_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            text, _notes = self._gates(Path(tmp))
        self.assertEqual(top_keys(text), ["building_quarries_requirement_terrain",
                                          "building_hill_farms_requirement_terrain"])
        quarries = block_of(text, "building_quarries_requirement_terrain")
        self.assertTrue(quarries.startswith("building_quarries_requirement_terrain = {\n\t" + rd.GROUND_GATE), quarries)
        self.assertIn("\n\tOR = {\n\t\tterrain = mountains\n\t\t#Anbennar\n\t\tterrain = cavern\n\t}\n}", quarries)
        hills = block_of(text, "building_hill_farms_requirement_terrain")
        self.assertTrue(hills.startswith("building_hill_farms_requirement_terrain = {\n\t" + rd.GROUND_GATE), hills)
        self.assertIn(" terrain = hills }", hills)

    def test_level_icon_define_extends_the_effective_list(self):
        # the level circles read NGameIcons.BUILDING_LEVEL_ICONS: copying the IX and X pictures alone shows nothing
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "")
            icons = "".join(f'\t\t"gfx/interface/icons/building_types/building_level_0{n}.dds"\n' for n in range(1, 9))
            (roots.anbennar / "common/defines/graphics").mkdir(parents=True)
            (roots.anbennar / "common/defines/graphics/00_graphics.txt").write_text(
                f"NGameIcons = {{\n\tX = 1\n\tBUILDING_LEVEL_ICONS = {{\n{icons}\t}}\n}}\n", encoding="utf-8")
            build = rd.Build(roots, [])
            rd.render_level_icon_defines(build)
            text = build.files[rd.LEVEL_DEFINES_FILE].decode("utf-8-sig")
        self.assertTrue(rd.LEVEL_DEFINES_FILE.startswith("common/defines/graphics/zz_"))
        self.assertEqual(re.findall(r"building_level_(\d\d)\.dds", text), [f"{n:02d}" for n in range(1, 11)])
        self.assertRegex(text, r"(?m)^NGameIcons = \{\n\tBUILDING_LEVEL_ICONS = \{\n")
        self.assertNotIn("X = 1", text)

    def test_level_icon_define_needs_the_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(rd.GeneratorError, "BUILDING_LEVEL_ICONS"):
                rd.render_level_icon_defines(rd.Build(fake_roots(Path(tmp), ""), []))

    def test_trigger_used_negated_is_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            text, notes = self._gates(Path(tmp) / "a")
            self.assertNotIn("building_logging_camps_requirement_terrain", top_keys(text))
            self.assertTrue(any("building_logging_camps_requirement_terrain" in note for note in notes), notes)
            text, _notes = self._gates(Path(tmp) / "b", used_negated=False)
        self.assertIn("building_logging_camps_requirement_terrain", top_keys(text))


DEPTHS_5 = """dwarven_depths_05 = {
	can_construct_potential = {
		scope:holder = { is_dwarvish_culture = yes }
	}
	can_construct = {
		OR = {
			has_building_or_higher = dwarven_quarry_01
		}
		has_building_or_higher = dwarven_hold_04
		custom_tooltip = {
			text = has_mines_04_or_higher
			OR = {
				has_building_or_higher = iron_mines_04
				has_building_or_higher = tin_mines_04
			}
		}
	}
	levy = 5
}
"""


class DigRequirementTests(unittest.TestCase):
    def test_previous_level_dropped_and_single_or_unwrapped(self):
        body = rd.requirement_body(5, DEPTHS_5)
        self.assertEqual(body, "\thas_building_or_higher = dwarven_quarry_01\n\tcustom_tooltip = {\n"
                               "\t\ttext = has_mines_04_or_higher\n\t\tOR = {\n"
                               "\t\t\thas_building_or_higher = iron_mines_04\n"
                               "\t\t\thas_building_or_higher = tin_mines_04\n\t\t}\n\t}\n")

    def test_or_around_previous_level_means_all_required(self):
        """RiE's depths_04 puts every requirement in the orc alternative's OR next to the previous level; with the
        orc branch gone they are all required (spec Section 2 table)."""
        text = DEPTHS_5.replace("\t\tOR = {\n\t\t\thas_building_or_higher = dwarven_quarry_01\n\t\t}\n"
                                "\t\thas_building_or_higher = dwarven_hold_04\n",
                                "\t\tOR = {\n\t\t\thas_building_or_higher = dwarven_quarry_01\n"
                                "\t\t\thas_building_or_higher = dwarven_hold_04\n")
        text = text.replace("\t\t}\n\t}\n\tlevy", "\t\t}\n\t\t}\n\t}\n\tlevy")
        self.assertIn("\t\t\thas_building_or_higher = dwarven_hold_04\n\t\tcustom_tooltip", text)  # inside the OR
        notes = []
        self.assertEqual(rd.requirement_body(5, text, notes), rd.requirement_body(5, DEPTHS_5))
        self.assertEqual(len(notes), 1)
        self.assertIn("dwarven_depths_05", notes[0])

    def test_other_hold_level_stops_build(self):
        with self.assertRaisesRegex(rd.GeneratorError, "dwarven_hold_04"):
            rd.requirement_body(6, DEPTHS_5)

    def test_no_requirement_is_always_true(self):
        self.assertEqual(rd.requirement_body(5, "dwarven_depths_05 = {\n\tlevy = 5\n}\n"), "\talways = yes\n")

    def test_dispatch_on_level(self):
        text = rd.requirements_met_trigger()
        for n in range(2, 11):
            self.assertIn(f"\ttrigger_if = {{\n\t\tlimit = {{ aov_hold_level = {n - 1} }}\n"
                          f"\t\taov_hold_dig_requirements_{n}_trigger = yes\n\t}}\n", text)


class HoldingListTests(unittest.TestCase):
    def test_drift_from_rie_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "")
            rd.check_holding_lists(roots)
            with mock.patch.object(data, "SURFACE_BUILDINGS", data.SURFACE_BUILDINGS[:-1]):
                with self.assertRaisesRegex(rd.GeneratorError, "SURFACE_BUILDINGS"):
                    rd.check_holding_lists(roots)
            with mock.patch.object(data, "HOLD_BUILDINGS", data.HOLD_BUILDINGS[:-1]):
                with self.assertRaisesRegex(rd.GeneratorError, "HOLD_BUILDINGS"):
                    rd.check_holding_lists(roots)


class HelperTests(unittest.TestCase):
    def test_reindent_uses_tabs_by_depth(self):
        text = "a = {\n \tb = 1\n    c = {\n  d = 2   \n\t\t}\n}\n"
        self.assertEqual(rd.reindent(text), "a = {\n\tb = 1\n\tc = {\n\t\td = 2\n\t}\n}\n")
        self.assertEqual(rd.reindent("x = 1\n", 1), "\tx = 1\n")

    def test_removal_note_groups_levels(self):
        note = rd.removal_note("x", ["removed is_orc = yes", "removed is_orc = yes",
                                     "removed effect_desc dwarven_forge_01_artifact_crafting_buff",
                                     "removed effect_desc dwarven_forge_02_artifact_crafting_buff"])
        self.assertIn("removed is_orc = yes x2", note)
        self.assertIn("removed effect_desc dwarven_forge_NN_artifact_crafting_buff x2", note)

    def test_crafting_lifestyle_xp_dropped(self):
        out, notes = rw.rewrite_block("x_01 = {\n\tcharacter_modifier = {\n\t\tmonthly_crafting_lifestyle_xp_gain_mult"
                                      " = 0.01\n\t}\n\tcost_gold = 10\n}\n", set())
        self.assertNotIn("crafting", out)
        self.assertNotIn("character_modifier", out)
        self.assertEqual(notes, ["removed monthly_crafting_lifestyle_xp_gain_mult = 0.01"])


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class RealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notes = []
        cls.files = rd.build_all(REAL, cls.notes)
        cls.texts = {rel: c.decode("utf-8-sig") for rel, c in cls.files.items() if rel.endswith((".txt", ".yml"))}
        cls.ours = cls.texts[rd.BUILDINGS_FILE] + cls.texts[rd.MINES_FILE]
        cls.keys = top_keys(cls.ours)
        cls.rie = {}
        for rel in data.RIE_BUILDING_FILES:
            cls.rie.update(rd.rie_blocks(REAL, rel))

    def test_every_rie_building_copied_once(self):
        self.assertEqual(sorted(self.keys), sorted(self.rie))
        self.assertEqual(len(self.keys), len(set(self.keys)))
        self.assertEqual(len(self.keys), 380)

    def test_no_rie_identifiers_left(self):
        for rel, text in self.texts.items():
            if rel.endswith(".txt") and rel != rd.BACKGROUNDS_FILE:  # its pictures keep RiE's lotr_ file names
                self.assertIsNone(LEFTOVER.search(bp.code(text)), rel)

    def test_dwarf_gates_survive(self):
        gated = [key for key, body in self.rie.items() if re.search(r"\bis_dwarf\b", bp.code(sub_block(body, "is_enabled")))]
        self.assertGreater(len(gated), 100)
        for key in gated:
            self.assertIn("is_dwarvish_culture = yes", sub_block(block_of(self.ours, key), "is_enabled"), key)

    def test_mines_need_their_deposit(self):
        for ore in data.ORES:
            for n in range(1, 11):
                body = block_of(self.texts[rd.MINES_FILE], f"{ore}_mines_{n:02d}")
                self.assertIn(f"has_province_modifier = mining_{ore}_province_modifier",
                              sub_block(body, "can_construct_potential"))

    def test_ore_modifiers_verbatim(self):
        rie = dict(rd.rie_blocks(REAL, data.ORE_FILE))
        ours = self.texts[rd.ORE_MODIFIERS_FILE]
        self.assertEqual(top_keys(ours), [f"mining_{ore}_province_modifier" for ore in data.ORES])
        for ore in data.ORES:
            key = f"mining_{ore}_province_modifier"
            self.assertEqual(block_of(ours, key), rie[key])

    def test_rie_only_script_values_copied(self):
        values = self.texts[rd.VALUES_FILE]
        self.assertRegex(values, r"(?m)^elven_building_garrison_reinforcement_factor_tier_1\s*=")
        defined = set(top_keys(values)) | set(re.findall(r"(?m)^(\w+)\s*=", bp.code(values)))
        external = rd.external_script_values(REAL)
        used = set()
        for text in (self.ours, *rd.depths_level_effects(REAL).values()):
            code = bp.code(text)
            used |= set(re.findall(r"\b(?:cost_gold|levy|max_garrison|garrison_reinforcement_factor|construction_time)"
                                   r"\s*=\s*([A-Za-z_]\w*)", code))
        self.assertIn("elven_building_garrison_reinforcement_factor_tier_1", used)
        for name in used:
            self.assertTrue(name in defined or name in external, name)
        for var in set(re.findall(r"@\[([^\]]*)\]", values)):
            for name in re.findall(r"[A-Za-z_]\w*", var):
                self.assertRegex(values, rf"(?m)^@{name}\s*=", name)

    def test_loc_for_every_building_and_tooltip(self):
        loc = set(re.findall(r"(?m)^ ([\w.\-']+):\d*\s", self.texts[rd.LOC_FILE]))
        external = rd.external_loc_keys(REAL)
        has = lambda key: key in loc or key in external  # noqa: E731
        nexts = set(re.findall(r"\bnext_building\s*=\s*(\w+)", bp.code(self.ours)))
        for key in self.keys:
            self.assertTrue(has(f"building_{key}"), key)
            if key not in nexts:
                self.assertTrue(has(f"building_type_{key}"), key)
        for key in set(re.findall(r"\b(?:text|effect_desc|desc)\s*=\s*(\w+)", bp.code(self.ours))):
            self.assertTrue(has(key), key)
        for ore in data.ORES:
            self.assertTrue(has(f"mining_{ore}_province_modifier"), ore)

    def test_loc_has_no_middle_earth_lore_or_undefined_concepts(self):
        lines = self.texts[rd.LOC_FILE].split("\n")[3:]
        self.assertEqual([line for line in lines if re.search(data.FORBIDDEN_LORE, line)], [])
        concepts = {c for line in lines for c in rd.CONCEPT_REF.findall(line)}
        self.assertEqual(sorted(concepts - rd.external_concepts(REAL)), [])
        for key, text in data.LOC_OVERRIDES.items():
            self.assertIn(f' {key}: "{text}"\n', self.texts[rd.LOC_FILE])

    def test_type_icons_exist(self):
        icons = set(re.findall(r'\btype_icon\s*=\s*"([^"]+)"', self.ours))
        self.assertGreater(len(icons), 20)
        for icon in icons:
            rel = f"{rd.ICON_DIR}/{icon}"
            self.assertTrue(rel in self.files or bp._exists_outside(REAL, rel) is not None, icon)

    def test_holding_lists_match_rie(self):
        rd.check_holding_lists(REAL)
        hold = rd.rie_holding_groups(REAL, "common/holdings/lotr_holdings.txt", "dwarven_holding")
        castle = rd.rie_holding_groups(REAL, "common/holdings/00_holdings.txt", "castle_holding")
        self.assertEqual(sorted(data.HOLD_BUILDINGS[:15]), sorted(hold["crafting resource mines"]))
        self.assertEqual(data.HOLD_BUILDINGS[15:], hold["dwarven buildings"])
        self.assertEqual(data.SURFACE_BUILDINGS, castle["dwarven buildings"])
        self.assertEqual(sorted(data.MINE_BUILDINGS), sorted(castle["crafting resource mines"]))
        self.assertEqual(len(data.HOLD_BUILDINGS), 35)

    def test_start_baronies_exist(self):
        titles = "\n".join(text for _path, text in bp._texts(str(REAL.anbennar / "common/landed_titles"), "*.txt"))
        for barony in data.START_DEPOSITS:
            self.assertRegex(titles, rf"(?m)^\s*{barony}\s*=\s*\{{", barony)

    def test_vanilla_terrain_triggers_gated(self):
        gates = self.texts[rd.TERRAIN_GATES_FILE]
        keys = top_keys(gates)
        for key in ("building_hillside_grazing_requirement_terrain", "building_quarries_requirement_terrain",
                    "building_curtain_walls_requirement_terrain", "building_hill_forts_requirement_terrain",
                    "building_fungus_farms_requirement_terrain", "building_griffon_roosts_requirement_terrain"):
            self.assertIn(key, keys)
            self.assertEqual(block_of(gates, key).split("\n")[1].strip().split(" #")[0], rd.GROUND_GATE, key)
        self.assertNotIn("building_logging_camps_requirement_terrain", keys)  # dwarven_forestry uses it negated
        self.assertTrue(all(re.fullmatch(r"building_\w+_requirement_terrain", key) for key in keys), keys)
        self.assertEqual(len(keys), len(set(keys)))

    def test_every_renamed_trigger_defined(self):
        triggers = set(top_keys(self.texts[rd.TRIGGERS_FILE]))
        for name in data.TOKEN_RENAMES.values():
            if name.endswith("_trigger"):
                self.assertIn(name, triggers)

    def test_renamed_triggers_are_used_in_province_scope(self):
        """No terrain, hold or surface-dwarf trigger sits under a character-scope block (scope:holder, culture)."""
        pattern = re.compile(r"aov_rie_(?:hold_province|mountain_terrain|hill_terrain|surface_dwarf)_trigger\s*=\s*yes")
        stack, used = [], 0
        for line in self.ours.split("\n"):
            code = line.split("#")[0]
            if pattern.search(code):
                used += 1
                self.assertEqual([n for n in stack if n.startswith("scope:") or n in ("culture", "faith")], [], line)
            stack += re.findall(r"([\w:.]+)\s*\??=\s*\{", code)
            for _ in range(code.count("}")):
                if stack:
                    stack.pop()
        self.assertGreater(used, 200)

    def test_files_have_bom_and_lf(self):
        for rel, content in self.files.items():
            if rel.endswith((".txt", ".yml")):
                self.assertTrue(content.startswith(rd.BOM.encode("utf-8")), rel)
                self.assertNotIn(b"\r", content, rel)
                text = content.decode("utf-8-sig")
                self.assertIn("tools/build_rie_dwarves.py", text.split("\n", 3)[0 if rel.endswith(".txt") else 1])

    def test_depths_level_effects(self):
        effects = rd.depths_level_effects(REAL)
        self.assertEqual(sorted(effects), list(range(1, 11)))
        self.assertIn("fort_level = 20", effects[10])
        self.assertIn("building_slot_add = 9", effects[10])
        for n, text in effects.items():
            self.assertRegex(text, r"(?m)^\tprovince_modifier = \{$", n)
            self.assertRegex(text, r"(?m)^\tlevy = ", n)
            self.assertNotIn("parameter", bp.code(text), n)
            self.assertIsNone(LEFTOVER.search(bp.code(text)), n)
            self.assertNotRegex(text, r"\b(?:can_construct|is_enabled|asset|ai_value|next_building|cost_gold)\b", n)

    def test_dig_requirements_rendered_with_loc(self):
        triggers = self.texts[rd.TRIGGERS_FILE]
        keys = top_keys(triggers)
        self.assertEqual(keys[-10:], [f"aov_hold_dig_requirements_{n}_trigger" for n in range(2, 11)]
                         + ["aov_hold_dig_requirements_met_trigger"])
        loc = set(re.findall(r"(?m)^ ([\w.\-']+):\d*\s", self.texts[rd.LOC_FILE])) | rd.external_loc_keys(REAL)
        for n in range(2, 11):
            body = block_of(triggers, f"aov_hold_dig_requirements_{n}_trigger")
            self.assertIsNone(re.search(r"dwarven_hold_\d", body), n)
            for key in re.findall(r"\btext = (\w+)", body):
                self.assertIn(key, loc, key)
        self.assertIn("has_building_or_higher = dwarven_toolmaker_guild_06",
                      block_of(triggers, "aov_hold_dig_requirements_10_trigger"))
        four = block_of(triggers, "aov_hold_dig_requirements_4_trigger")  # quarry 3 and any mine 3 (spec table)
        self.assertRegex(four, r"\n\thas_building_or_higher = dwarven_quarry_03\n\tcustom_tooltip = \{\n"
                               r"\t\ttext = has_mines_03_or_higher\n")
        for n in range(4, 11):  # past level 3 a hold needs a mine
            self.assertRegex(block_of(triggers, f"aov_hold_dig_requirements_{n}_trigger"),
                             rf"\n\tcustom_tooltip = \{{\n\t\ttext = has_mines_{n - 1:02d}_or_higher\n", n)

    def test_removal_note_lists_only_rule_removals(self):
        note = next(n for n in self.notes if n.startswith("removed from RiE's buildings"))
        for item in re.findall(r"(?:^|; )([^;]+?) x\d+", note.split(": ", 1)[1]):
            self.assertRegex(item, r"^(removed (is_orc = yes|has_dynasty_perk = lotr_\w+|has_innovation = "
                                   r"innovation_iron_hills_goat_domestication|has_building_or_higher = elven_settlement_NN|"
                                   r"province_dynasty_modifier \(lotr_\w+\)|effect_desc \w+_artifact_crafting_buff|"
                                   r"monthly_crafting_lifestyle_xp_gain_mult = N|\w+ block gated on parameter \w+)"
                                   r"|ungated parameter unlock_full_delving"
                                   r"|replaced scope:holder = \{ culture = \{ has_innovation = "
                                   r"innovation_iron_hills_goat_domestication \} \} with scope:holder = \{ "
                                   r"is_dwarvish_culture = yes \})$")

    # --- surface buildings: dwarves only, never in a hold, hills, mountains or dwarven terrain (findings 1-3) ---

    def potential(self, key):
        return " ".join(bp.code(sub_block(block_of(self.ours, key), "can_construct_potential")).split())

    def test_goat_pastures_need_a_dwarven_holder(self):
        goats = [key for key in self.keys if key.startswith("goat_pastures_")]
        self.assertEqual(len(goats), 8)
        for key in goats:
            potential = self.potential(key)
            self.assertIn("scope:holder = { is_dwarvish_culture = yes }", potential, key)
            self.assertIn("aov_rie_hill_terrain_trigger = yes", potential, key)
            self.assertNotIn("innovation", block_of(self.ours, key), key)

    def test_surface_enabled_buildings_not_offered_in_holds(self):
        gated = []
        for key in self.keys:
            body = block_of(self.ours, key)
            uses = " ".join(bp.code(sub_block(body, name)) for name in (
                "is_enabled", "can_construct", "can_construct_showing_failures_only"))
            if "aov_rie_surface_dwarf_trigger" not in uses:
                continue
            gated.append(key)
            potential = self.potential(key)
            self.assertIn("aov_rie_hold_province_trigger = no", potential, key)
            self.assertRegex(potential, r"scope:holder = \{ is_dwarvish_culture = yes \}", key)
        self.assertGreater(len(gated), 50)
        for key in ("dwarven_tavern_01", "dwarven_tavern_06", "goat_pastures_01", "goat_pastures_08"):
            self.assertIn(key, gated)

    def test_surface_lines_on_hills_mountains_or_dwarven_terrain(self):
        lines = {key[:-3] for key in data.SURFACE_BUILDINGS}
        hold_lines = {key[:-3] for key in data.HOLD_BUILDINGS}
        own = {line for line in lines if any(rw.has_terrain_gate(bp.code(rw.rewrite_block(body, set())[0]))
                                             for key, body in self.rie.items() if key[:-3] == line)}
        # RiE gives these lines terrain gates of their own (forest, not hills, not mountains, hills): kept as RiE has them.
        self.assertEqual(own, {"dwarven_forestry", "dwarven_pit_mine", "dwarven_surface_farm", "dwarven_terrace_farm",
                               "goat_pastures"})
        gated = lines - own
        self.assertEqual(gated, {"dwarven_outpost", "dwarven_market", "dwarven_surface_forge",
                                 "dwarven_surface_workshop", "dwarven_mustering_grounds", "dwarven_tavern"})
        for key in self.keys:
            if key[:-3] not in gated:
                continue
            potential = self.potential(key)
            if key[:-3] in hold_lines and "aov_rie_hold_province_trigger = no" not in potential:
                self.assertIn("OR = { aov_rie_hold_province_trigger = yes aov_rie_hill_terrain_trigger = yes }",
                              potential, key)
            else:
                self.assertIn("aov_rie_hill_terrain_trigger = yes", potential, key)
        # Lines in both lists keep RiE's hold availability: terrace farms in holds, outposts never.
        self.assertIn("OR = { aov_rie_hold_province_trigger = yes aov_rie_hill_terrain_trigger = yes }",
                      self.potential("dwarven_terrace_farm_01"))
        self.assertIn("aov_rie_hold_province_trigger = no", self.potential("dwarven_outpost_01"))
        note = next(n for n in self.notes if n.startswith("surface buildings gated"))
        for line in sorted(gated):
            self.assertIn(line, note)


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class ExpeditionArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = rd.build_all(REAL)

    def test_backgrounds_defined_with_copied_pictures(self):
        text = self.files[rd.BACKGROUNDS_FILE].decode("utf-8-sig")
        environments = (REAL.game / "game/gfx/portraits/environments/portrait_environments.txt").read_text(
            encoding="utf-8-sig")
        self.assertEqual(set(top_keys(text)), set(data.BACKGROUNDS))
        for key, (picture, environment, ambience) in data.BACKGROUNDS.items():
            body = block_of(text, key)
            self.assertIn(f'reference = "{picture}"', body)
            self.assertIn(f'environment = "{environment}"', body)
            self.assertIn(f'ambience = "{ambience}"', body)
            self.assertTrue(picture in self.files or bp._exists_outside(REAL, picture) is not None, picture)
            self.assertRegex(environments, re.compile(rf"^{environment}\s*=\s*\{{", re.M))

    def test_activity_icons_copied(self):
        self.assertEqual(len(data.ACTIVITY_ICONS), 7)
        for source, target in data.ACTIVITY_ICONS.items():
            rel = f"gfx/interface/icons/{target}"
            self.assertEqual(self.files[rel], (REAL.rie / f"gfx/interface/icons/{source}").read_bytes())
        self.assertEqual(len(data.ACTIVITY_ILLUSTRATIONS), 3)
        for source, target in data.ACTIVITY_ILLUSTRATIONS.items():
            rel = f"gfx/interface/illustrations/{target}"
            self.assertEqual(self.files[rel], (REAL.rie / f"gfx/interface/illustrations/{source}").read_bytes())

    def test_ui_icons_copied(self):
        self.assertEqual(data.UI_ICONS["holding_types_tab/dwarven_holding.dds"],
                         "holding_types_tab/dwarven_hold_holding.dds")
        for level in ("09", "10"):
            self.assertIn(f"building_types/building_level_{level}.dds", data.UI_ICONS)
        for source, target in data.UI_ICONS.items():
            rel = f"gfx/interface/icons/{target}"
            self.assertEqual(self.files[rel], (REAL.rie / f"gfx/interface/icons/{source}").read_bytes())
        defines = self.files[rd.LEVEL_DEFINES_FILE].decode("utf-8-sig")
        self.assertEqual(re.findall(r"building_level_(\d\d)\.dds", defines), [f"{n:02d}" for n in range(1, 11)])

    def test_background_clash_stops_build(self):
        picture = next(iter(data.BACKGROUNDS.values()))[0]
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "")
            for root, content in ((roots.rie, b"rie"), (roots.anbennar, b"other")):
                (root / picture).parent.mkdir(parents=True, exist_ok=True)
                (root / picture).write_bytes(content)
            with self.assertRaisesRegex(rd.GeneratorError, "lotr_cave_interior"):
                rd.render_expedition_art(rd.Build(roots, []))


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class FreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = rd.build_all(REAL)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (rd.SUBMOD / rel).is_file() or (rd.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_rie_dwarves.py")

    def test_no_orphan_files(self):
        import build_rie_elves  # shares the building type icon folder
        produced = set(self.files) | set(build_rie_elves.build_all(REAL))
        orphans = []
        root = rd.SUBMOD / rd.ICON_DIR
        if root.is_dir():
            orphans += [p.relative_to(rd.SUBMOD).as_posix() for p in root.rglob("*") if p.is_file()]
        for folder, patterns in rd.OWNED_FOLDERS.items():
            root = rd.SUBMOD / folder
            if root.is_dir():
                orphans += [p.relative_to(rd.SUBMOD).as_posix() for pattern in patterns for p in root.glob(pattern)
                            if p.is_file()]
        self.assertEqual(sorted(o for o in orphans if o not in produced), [], "leftover files: delete them")


if __name__ == "__main__":
    unittest.main()
