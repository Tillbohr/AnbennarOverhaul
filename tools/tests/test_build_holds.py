import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_holds as bh  # noqa: E402
import build_portraits as bp  # noqa: E402
import build_rie_dwarves as rd  # noqa: E402
from data import holds  # noqa: E402
from data.holding_models import HOLD_DWARF_MESHES  # noqa: E402

LIVE = bh.ANBENNAR_CK3.is_dir()
REAL = bp.Roots.default()
HAVE_REAL = REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir()
SUBMOD = bh.SUBMOD
KEYS = [f"dwarven_hold_{n:02d}" for n in range(1, 11)]
OLD_BUILDINGS = re.compile(r"deep_mine|runeforge|hall_of_the_ancestors")


def parse_blocks(text):
    return {m.group(1): m.group(2) for m in re.finditer(r"^(\w+) = \{\n(.*?)^\}", text, re.M | re.S)}


def value(block, name):
    m = re.search(rf"\b{name} = (-?[\d.]+)", block)
    assert m, name
    return float(m.group(1))


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class HoldBuildingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = bh.render_buildings(REAL)
        cls.blocks = parse_blocks(cls.text)

    def test_levels_chain_and_are_not_buildable(self):
        for n in range(1, 11):
            block = self.blocks[f"dwarven_hold_{n:02d}"]
            self.assertIn("always = no", block)
            self.assertIn("is_dwarvish_culture = yes", block)
            self.assertIn("aov_hold_ruined", block)
            self.assertEqual(f"next_building = dwarven_hold_{n + 1:02d}" in block, n < 10)

    def test_level_effects_come_from_rie(self):
        effects = rd.depths_level_effects(REAL)
        for n in range(1, 11):
            self.assertIn(effects[n], self.blocks[f"dwarven_hold_{n:02d}"], n)

    def test_level_ten_matches_rie(self):
        province = re.search(r"\tprovince_modifier = \{\n(.*?)\n\t\}", self.blocks["dwarven_hold_10"], re.S).group(1)
        self.assertRegex(province, r"(?m)^\t\tfort_level = 20$")
        self.assertRegex(province, r"(?m)^\t\tbuilding_slot_add = 9\b")

    def test_levels_still_not_buildable(self):
        for n in range(1, 11):
            block = self.blocks[f"dwarven_hold_{n:02d}"]
            self.assertIn("\tcan_construct_potential = {\n\t\talways = no\n\t}\n", block, n)
            self.assertNotRegex(block, r"\bcan_construct = ", n)
            self.assertEqual(re.findall(r"\tis_enabled = \{\n.*?\n\t\}\n", block, re.S), [bh.IS_ENABLED.rstrip("\n") + "\n"],
                             n)
            self.assertIn("scope:holder = {\n\t\t\tis_dwarvish_culture = yes", bh.IS_ENABLED)
            self.assertIn("NOT = { has_variable = aov_hold_ruined }", bh.IS_ENABLED)

    def test_old_dwarven_buildings_gone(self):
        self.assertIsNone(OLD_BUILDINGS.search(self.text))
        self.assertIsNone(OLD_BUILDINGS.search(bh.render_loc()))
        self.assertIsNone(OLD_BUILDINGS.search((Path(bh.__file__).parent / "data/holds.py").read_text(encoding="utf-8")))
        self.assertIsNone(OLD_BUILDINGS.search(Path(bh.__file__).read_text(encoding="utf-8")))
        for name in ("DWARVEN_BUILDINGS", "LEVELS", "FLAT_VALUES", "_FLAT_TIERS", "_LEVEL_ROWS"):
            self.assertFalse(hasattr(holds, name), name)

    def test_flat_values_placed_like_castles(self):
        for n in range(1, 11):
            block = self.blocks[f"dwarven_hold_{n:02d}"]
            for name in ("levy", "max_garrison", "garrison_reinforcement_factor"):  # RiE's numbers or script values
                self.assertRegex(block, rf"(?m)^\t{name} = [\w.]+$", f"{n} {name}")
            province = re.search(r"\tprovince_modifier = \{\n(.*?)\n\t\}", block, re.S).group(1)
            self.assertIn("monthly_income = ", province, n)

    def test_ai_never_builds_levels(self):
        for n in range(1, 11):
            ai = re.search(r"\tai_value = \{\n(.*?)\n\t\}", self.blocks[f"dwarven_hold_{n:02d}"], re.S).group(1)
            self.assertEqual(value(ai, "base"), 0, n)

    def test_no_empty_blocks(self):
        self.assertNotRegex(self.text, r"_modifier = \{\s*\}")

    def test_assets_come_from_the_band(self):
        _, assets = bh.castle_assets(bh.ANBENNAR_CK3)
        self.assertGreater(len(assets["castle_03"]), 5)
        self.assertIn("asset = {", self.blocks["dwarven_hold_05"])
        self.assertIn(assets["castle_03"][1], self.blocks["dwarven_hold_05"])

    def test_dwarf_model_asset_comes_first(self):
        import build_holding_models as bhm
        _, assets = bh.castle_assets(bh.ANBENNAR_CK3)
        regions = bhm.graphical_regions(bh.ANBENNAR_CK3)
        _targets, keys = bhm.assign_gfx(bhm.culture_texts(bhm.Roots(rie=None, anbennar=bh.ANBENNAR_CK3, game=None)))
        for n in range(1, 11):
            block = self.blocks[f"dwarven_hold_{n:02d}"]
            mesh = HOLD_DWARF_MESHES[n]
            first = block[block.index("asset = {"):]
            first = first[:first.index("\n\t\t}")]
            self.assertIn(f'name = "{mesh}"', first, n)
            self.assertIn("type = pdxmesh", first, n)
            self.assertNotIn("graphical_cultures", first, n)  # any holder sees the dwarf model
            self.assertIn("provinces = { %s }" % " ".join(map(str, bhm.dwarf_model_provinces(bh.ANBENNAR_CK3))), first, n)
            self.assertIn("graphical_regions = { %s }" % " ".join(regions), first, n)
            self.assertIn("# Anbennar Overhaul: RiE dwarf hold model", first, n)
            band = assets[holds.ASSET_BAND[n]]
            # illustration and sound: the band's first asset without a DLC flag that serves western_building_gfx
            plain = [a for a in bhm.original_assets(band)
                     if "requires_dlc_flag" not in "".join(a) and "western_building_gfx" in "".join(a)][0]
            illustration = next(l for l in plain if l.strip().startswith("illustration ="))
            soundeffect = next(l for l in plain if l.strip().startswith("soundeffect ="))
            self.assertIn(illustration, first, n)
            self.assertIn(soundeffect, first, n)
            self.assertNotRegex(first, r"fp\d_|norse", n)
            # the castle asset still follows the dwarf one
            self.assertIn(band[1], block[block.index(first) + len(first):], n)

    def test_dwarf_meshes_cover_every_level(self):
        self.assertEqual(sorted(HOLD_DWARF_MESHES), list(range(1, 11)))
        self.assertEqual([HOLD_DWARF_MESHES[n] for n in (1, 2, 3, 5, 7, 9, 10)],
                         [f"dwarven_holding_0{k}_mesh" for k in (1, 1, 2, 3, 4, 5, 5)])

    def test_illustration_variables_are_redefined(self):
        vars_ = set(re.findall(r"@holding_illustration_\w+", self.text))
        self.assertTrue(vars_)
        for var in vars_:
            self.assertIn(f"{var} =", self.text)


CASTLE_LEVEL_TO_HOLD = {"01": 1, "02": 3, "03": 5, "04": 8}
REQUIREMENT_TRIGGERS = ("building_requirement_castle_city_church",
                        "building_requirement_castle_city_church_temple_citadel_tribe")
REQUIREMENT_FILE = "common/scripted_triggers/00_building_requirement_triggers.txt"
OVERRIDE_FILE = "common/scripted_triggers/zz_aov_building_requirement_triggers.txt"
DWARVEN_BRANCH = re.compile(r"\t# Anbennar Overhaul[^\n]*\n\ttrigger_else_if = \{\n"
                            r"\t\tlimit = \{ has_holding_type = dwarven_hold_holding \}\n.*?\n\t\}\n", re.S)


@unittest.skipUnless(LIVE, "Anbennar CK3 not present")
class BuildingRequirementOverrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = SUBMOD / OVERRIDE_FILE
        cls.ours = parse_blocks(path.read_text(encoding="utf-8-sig")) if path.is_file() else {}
        cls.base = parse_blocks((bh.ANBENNAR_CK3 / REQUIREMENT_FILE).read_text(encoding="utf-8-sig"))

    def test_castle_level_triggers_are_all_overridden(self):
        castle_level = {k for k, v in self.base.items() if "has_building_or_higher = castle_$LEVEL$" in v
                        and "has_holding_type = castle_holding" in v}
        self.assertEqual(castle_level, set(REQUIREMENT_TRIGGERS))
        self.assertEqual(set(self.ours), set(REQUIREMENT_TRIGGERS))

    def test_override_is_anbennar_plus_dwarven_branch(self):
        for name in REQUIREMENT_TRIGGERS:
            body = self.ours.get(name, "")
            self.assertEqual(len(DWARVEN_BRANCH.findall(body)), 1, name)
            self.assertEqual(DWARVEN_BRANCH.sub("", body), self.base[name], name)

    def test_dwarven_branch_maps_castle_levels(self):
        bands = {n for n, band in holds.ASSET_BAND.items() if band != holds.ASSET_BAND.get(n - 1)}
        self.assertEqual(set(CASTLE_LEVEL_TO_HOLD.values()), bands)
        for name in REQUIREMENT_TRIGGERS:
            branch = DWARVEN_BRANCH.search(self.ours.get(name, ""))
            self.assertTrue(branch, name)
            found = re.findall(r"(?:limit = \{ \$LEVEL\$ >= (\d) \}\n\t+|trigger_else = \{\n\t+)"
                               r"has_building_or_higher = dwarven_hold_(\d\d)", branch.group(0))
            self.assertEqual({f"{int(lv or 1):02d}": int(hold) for lv, hold in found}, CASTLE_LEVEL_TO_HOLD, name)


class ValueAndLocTests(unittest.TestCase):
    def test_values(self):
        v = bh.render_values()
        self.assertIn("aov_hold_level = {", v)
        self.assertIn("has_building_or_higher = dwarven_hold_10", v)

    def test_dig_months_and_cost(self):
        self.assertEqual([holds.dig_months(n) for n in (2, 10)], [144, 528])
        self.assertEqual(holds.DIG_COST_PER_LEVEL, 150)
        v = bh.render_values()
        for name in ("aov_dig_target_value", "aov_dig_cost", "aov_dig_months"):
            self.assertIn(f"{name} = {{", v)
        for gone in ("aov_dig_campaign_cost", "aov_dig_campaign_base", "aov_dig_target ="):
            self.assertNotIn(gone, v)

    def test_delving_modifiers(self):
        m = bh.render_modifiers()
        for n in range(2, 11):
            self.assertIn(f"aov_delving_{n:02d} = {{", m)
            self.assertIn(f" aov_delving_{n:02d}:0 \"Delving to Level {n}\"", bh.render_loc())
        self.assertNotIn("aov_delving_01", m)

    def test_removed_constants(self):
        for name in ("PACE", "INVESTMENT", "PHASE_MONTHS", "CAMPAIGN_BASE", "CAMPAIGN_COST_PER_LEVEL",
                     "TRAIT_BONUS", "DIG_TARGET_PER_LEVEL"):
            self.assertFalse(hasattr(holds, name), name)

    def test_loc_for_every_level(self):
        loc = bh.render_loc()
        self.assertTrue(loc.startswith("l_english:"))
        for key in KEYS:
            for k in (f"building_{key}", f"building_{key}_desc", f"building_type_{key}", f"building_type_{key}_desc"):
                self.assertIn(f" {k}:0 \"", loc)


class SetupTests(unittest.TestCase):
    def block_for(self, name):
        t = bh.render_setup()
        m = re.search(r"\t# " + re.escape(name) + r"\n(.*?)\n\t\}\n", t, re.S)
        return m.group(1)

    def test_setup_covers_every_hold(self):
        t = bh.render_setup()
        for h in holds.HOLDS:
            self.assertIn(f"title:{h['barony']}.title_province", t)
        self.assertEqual(t.count("set_variable = aov_hold_ruined"), 1)
        self.assertEqual(t.count("aov_dig_progress"), len(holds.HOLDS))
        self.assertIn("add_building = dwarven_hold_02", self.block_for("Rubyhold"))
        self.assertNotIn("add_building = dwarven_hold_02", self.block_for("Anvilwright"))
        self.assertIn("aov_ruined_hold", self.block_for("Khugdihr"))

    def test_conversion_keeps_special_buildings(self):
        t = bh.render_setup()
        self.assertNotIn("remove_building", t)
        self.assertNotIn("special_building", t)
        self.assertEqual(t.count("set_holding_type"), len(holds.HOLDS))
        # the setup text never mentions a special building, so the history slots of the baronies stay as they are
        self.assertNotIn("special_building_slot", t)

    def test_game_start_hooks_setup(self):
        t = (SUBMOD / "common/on_action/aov_hold_on_actions.txt").read_text(encoding="utf-8-sig")
        self.assertRegex(t, r"on_game_start = \{\s*on_actions = \{ aov_hold_game_start \}")
        self.assertRegex(t, r"aov_hold_game_start = \{\s*effect = \{\s*aov_hold_setup_effect = yes")

    def test_modifiers_match_data(self):
        t = bh.render_modifiers()
        for k, v in holds.RUINED_MODIFIER.items():
            self.assertIn(f"{k} = {bh.fmt(v)}", t)
        for key in ("aov_ruined_hold", "aov_restoring_hold", "aov_hold_rich_vein"):
            self.assertIn(f"{key} = {{", t)
            self.assertIn(f" {key}_desc:0", bh.render_loc())

    def test_triggers_defined(self):
        t = (SUBMOD / "common/scripted_triggers/aov_hold_triggers.txt").read_text(encoding="utf-8-sig")
        for k in ("aov_is_hold", "aov_hold_is_ruined", "aov_hold_is_working", "aov_can_start_dig_base",
                  "aov_can_dig_at"):
            self.assertIn(f"{k} = {{", t)


TRIGGER_BLOCK = re.compile(r"^(aov_hold_dig_requirements_\w+) = \{\n(.*?)^\}", re.M | re.S)


class DigRequirementTests(unittest.TestCase):
    """The dig prerequisites: RiE's depths can_construct, checked when a dig starts and never while it runs."""

    def hand(self, rel):
        return (SUBMOD / rel).read_text(encoding="utf-8-sig")

    def test_dig_requirements_for_levels_2_to_10(self):
        triggers = dict(TRIGGER_BLOCK.findall(self.hand(rd.TRIGGERS_FILE)))
        self.assertEqual(set(triggers), {f"aov_hold_dig_requirements_{n}_trigger" for n in range(2, 11)}
                         | {"aov_hold_dig_requirements_met_trigger"})
        for n in range(2, 11):
            body = triggers[f"aov_hold_dig_requirements_{n}_trigger"]
            self.assertNotIn(f"dwarven_hold_{n - 1:02d}", body, n)
            self.assertNotRegex(body, r"dwarven_(?:hold|depths)_\d", n)
            self.assertNotRegex(body, r"\b(?:OR|AND) = \{\s*\}", n)
        five = triggers["aov_hold_dig_requirements_5_trigger"]
        self.assertIn("has_building_or_higher = dwarven_quarry_03", five)
        self.assertIn("text = has_mines_04_or_higher", five)
        mines = re.search(r"text = has_mines_04_or_higher\n\t+OR = \{\n(.*?)\n\t+\}", five, re.S).group(1)
        self.assertEqual(sorted(re.findall(r"has_building_or_higher = (\w+)_mines_04", mines)), sorted(rd.data.ORES))
        self.assertIn("has_building_or_higher = dwarven_quarry_01", triggers["aov_hold_dig_requirements_2_trigger"])
        met = triggers["aov_hold_dig_requirements_met_trigger"]
        for n in range(2, 11):
            self.assertRegex(met, rf"trigger_(?:else_)?if = \{{\n\t+limit = \{{ aov_hold_level = {n - 1} \}}\n"
                                  rf"\t+aov_hold_dig_requirements_{n}_trigger = yes\n", n)
        self.assertNotIn("aov_hold_level = 10", met)

    def test_requirement_tooltips_have_loc(self):
        loc = self.hand(rd.LOC_FILE)
        bodies = "".join(body for _name, body in TRIGGER_BLOCK.findall(self.hand(rd.TRIGGERS_FILE)))
        keys = set(re.findall(r"\btext = (\w+)", bodies))
        self.assertIn("has_specialization_01_or_higher", keys)
        for key in keys:
            self.assertRegex(loc, rf"(?m)^ {key}:\d* ?\"", key)

    def test_dig_start_checks_requirements(self):
        triggers = parse_blocks(self.hand("common/scripted_triggers/aov_hold_triggers.txt"))
        self.assertEqual(triggers["aov_can_dig_at"],
                         "\taov_can_start_dig_base = yes\n\taov_hold_dig_requirements_met_trigger = yes\n")
        base = triggers["aov_can_start_dig_base"]
        for line in ("aov_hold_is_working = yes", "aov_hold_level < 10", "NOT = { aov_hold_dig_running = yes }",
                     "is_occupied = no", "barony.holder = scope:digger", "is_dwarvish_culture = yes"):
            self.assertIn(line, base)
        self.assertNotIn("aov_hold_dig_requirements", base)

    def test_decision_opens_picker_for_holds_lacking_buildings(self):
        text = (SUBMOD / "common/decisions/aov_hold_decisions.txt").read_text(encoding="utf-8-sig")
        decision = parse_blocks(text)["aov_delve_deeper_decision"]
        valid = re.search(r"(?m)^\tis_valid = \{\n(.*?)^\t\}\n", decision, re.S).group(1)
        no_hold = re.search(r"text = aov_delve_deeper_no_hold\n(.*?)\n\t\t\}\n", valid, re.S).group(1)
        self.assertIn("aov_can_start_dig_base = yes", no_hold)
        self.assertNotIn("aov_can_dig_at", no_hold)
        self.assertNotIn("aov_hold_dig_requirements", no_hold)
        no_gold = re.search(r"text = aov_delve_deeper_no_gold\n(.*?)\n\t\t\}\n", valid, re.S).group(1)
        ai, player = no_gold.split("trigger_else = {")
        self.assertIn("limit = { is_ai = yes }", ai)
        self.assertIn("aov_can_dig_at = yes", ai)  # the AI never opens a picker it cannot use
        self.assertNotIn("aov_can_start_dig_base", ai)
        self.assertIn("aov_can_start_dig_base = yes", player)
        ai_will_do = decision[decision.index("\tai_will_do = {"):]
        self.assertIn("aov_can_dig_at = yes", ai_will_do)
        self.assertNotIn("aov_can_start_dig_base", ai_will_do)

    def test_running_dig_ignores_requirements(self):
        for rel in ("common/on_action/aov_hold_on_actions.txt", "common/on_action/aov_hold_dig_on_actions.txt",
                    "common/scripted_effects/aov_hold_effects.txt", "events/aov_hold_dig_events.txt"):
            text = self.hand(rel)
            self.assertNotIn("aov_hold_dig_requirements", text, rel)
            self.assertNotIn("aov_can_dig_at = yes", text, rel)
            self.assertNotIn("aov_can_start_dig_base", text, rel)

    def test_picker_shows_blocked_holds(self):
        text = self.hand("events/aov_hold_delve_events.txt")
        options = re.findall(r"\toption = \{\n\t\tname = aov_hold_delve\.1\.hold_\d\n.*?\n\t\}\n", text, re.S)
        self.assertEqual(len(options), len(holds.HOLDS))
        for h, option in zip(holds.HOLDS, options):
            self.assertIn(f"\t\t\ttitle:{h['barony']} = {{ holder = root }}\n", option, h["name"])
            self.assertIn(f"\t\tshow_as_unavailable = {{\n\t\t\ttitle:{h['barony']} = {{ holder = root }}\n"
                          "\t\t\tsave_temporary_scope_as = digger\n"
                          f"\t\t\ttitle:{h['barony']}.title_province = {{ aov_can_start_dig_base = yes }}\n\t\t}}\n",
                          option, h["name"])
            trigger = re.search(r"\t\ttrigger = \{\n(.*?)\n\t\t\}\n", option, re.S).group(1)
            self.assertIn("aov_can_dig_at = yes", trigger, h["name"])  # the option itself needs the buildings

    def test_game_start_sets_deposits(self):
        effect = parse_blocks(self.hand("common/on_action/aov_hold_on_actions.txt"))["aov_hold_game_start"]
        self.assertRegex(effect, r"aov_hold_setup_effect = yes\n\t+aov_rie_deposit_setup_effect = yes\n")


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class FreshTests(unittest.TestCase):
    def test_written_files_are_fresh(self):
        for rel, text in bh.render_all(roots=REAL).items():
            data = (SUBMOD / rel).read_bytes()
            self.assertTrue(data.startswith(b"\xef\xbb\xbf"), rel)
            self.assertEqual(data[3:].decode("utf-8"), text, rel)


if __name__ == "__main__":
    unittest.main()
