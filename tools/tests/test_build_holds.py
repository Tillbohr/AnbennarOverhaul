import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_holds as bh  # noqa: E402
from data import holds  # noqa: E402
from data.holding_models import HOLD_DWARF_MESHES  # noqa: E402

LIVE = bh.ANBENNAR_CK3.is_dir()
SUBMOD = bh.SUBMOD
KEYS = [f"dwarven_hold_{n:02d}" for n in range(1, 11)]
BUILDING_KEYS = [f"{b['key']}_{n:02d}" for b in holds.DWARVEN_BUILDINGS for n in (1, 2, 3)]


def parse_blocks(text):
    return {m.group(1): m.group(2) for m in re.finditer(r"^(\w+) = \{\n(.*?)^\}", text, re.M | re.S)}


def value(block, name):
    m = re.search(rf"\b{name} = (-?[\d.]+)", block)
    assert m, name
    return float(m.group(1))


@unittest.skipUnless(LIVE, "Anbennar CK3 not present")
class HoldBuildingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = bh.render_buildings()
        cls.blocks = parse_blocks(cls.text)

    def test_levels_chain_and_are_not_buildable(self):
        for n in range(1, 11):
            block = self.blocks[f"dwarven_hold_{n:02d}"]
            self.assertIn("always = no", block)
            self.assertIn("is_dwarvish_culture = yes", block)
            self.assertIn("aov_hold_ruined", block)
            self.assertEqual(f"next_building = dwarven_hold_{n + 1:02d}" in block, n < 10)

    def test_level_effects_match_data(self):
        for n, lvl in enumerate(holds.LEVELS, 1):
            block = self.blocks[f"dwarven_hold_{n:02d}"]
            for name, val in lvl.items():
                if isinstance(val, str):
                    self.assertRegex(block, rf"\b{name} = {val}\n", msg=f"{n} {name}")
                    continue
                if not val:
                    self.assertNotIn(name, block)
                    continue
                self.assertAlmostEqual(value(block, name), val, msg=f"{n} {name}")

    def test_flat_values_placed_like_castles(self):
        for n in range(1, 11):
            block = self.blocks[f"dwarven_hold_{n:02d}"]
            for name in ("levy", "max_garrison", "garrison_reinforcement_factor"):
                self.assertRegex(block, rf"(?m)^\t{name} = \w+$", f"{n} {name}")
            province = re.search(r"\tprovince_modifier = \{\n(.*?)\n\t\}", block, re.S).group(1)
            self.assertIn("monthly_income = ", province, n)

    def test_dwarven_buildings_switch_off_like_levels(self):
        for key in BUILDING_KEYS:
            enabled = re.search(r"\tis_enabled = \{\n(.*?)\n\t\}", self.blocks[key], re.S)
            self.assertTrue(enabled, key)
            self.assertRegex(enabled.group(1), r"scope:holder = \{\s*is_dwarvish_culture = yes\s*\}", key)
            self.assertIn("NOT = { has_variable = aov_hold_ruined }", enabled.group(1), key)

    def test_ai_builds_dwarven_buildings_but_never_levels(self):
        for key in BUILDING_KEYS:
            ai = re.search(r"\tai_value = \{\n(.*?)\n\t\}", self.blocks[key], re.S).group(1)
            self.assertGreater(value(ai, "base"), 0, key)
            self.assertIn("ai_general_building_modifier = yes", ai, key)
            self.assertEqual("ai_tier_1_building_modifier = yes" in ai, key.endswith("_01"), key)
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

    def test_dwarven_buildings_gated_on_level(self):
        self.assertIn("has_building_or_higher = dwarven_hold_03", self.blocks["deep_mine_01"])
        self.assertIn("has_building_or_higher = dwarven_hold_05", self.blocks["runeforge_01"])
        self.assertIn("has_building_or_higher = dwarven_hold_07", self.blocks["hall_of_the_ancestors_01"])
        for key in BUILDING_KEYS:
            self.assertIn("is_dwarvish_culture = yes", self.blocks[key])

    def test_dwarven_building_effects_scale(self):
        self.assertAlmostEqual(value(self.blocks["deep_mine_03"], "tax_mult"), 0.15)
        self.assertIn("next_building = deep_mine_02", self.blocks["deep_mine_01"])
        self.assertNotIn("next_building", self.blocks["deep_mine_03"])
        self.assertIn("normal_building_tier_3_cost", self.blocks["runeforge_03"])


FLAT_KEYS = ("levy", "max_garrison", "garrison_reinforcement_factor", "monthly_income")
BUILDING_VALUES = "common/script_values/00_building_values.txt"


def script_value_resolver(root):
    """Resolve Anbennar's flat building script values (`name = @[expr]` over `@var = expr`) to numbers."""
    text = (Path(root) / BUILDING_VALUES).read_text(encoding="utf-8-sig")
    defs = {m.group(1): m.group(2).strip() for m in re.finditer(r"^(@?\w+) = ([^{#\n]+)", text, re.M)}

    def resolve(name):
        expr = defs[name]
        if expr.startswith("@["):
            expr = expr[2:-1]
        elif expr.startswith("@"):
            expr = expr[1:]

        def sub(m):
            ident = m.group(0)
            return repr(resolve("@" + ident if "@" + ident in defs else ident))

        expr = re.sub(r"\b[a-z_]\w*\b", sub, expr)
        return eval(expr, {"__builtins__": {}})  # numbers and + - * / only

    return resolve


def castle_flat_values(root):
    """castle_0N -> {flat key: script value name} from Anbennar's castle buildings."""
    text = (Path(root) / bh.CASTLE_FILE).read_text(encoding="utf-8-sig")
    out = {}
    for key, body in parse_blocks(text).items():
        if re.fullmatch(r"castle_0\d", key):
            out[key] = {k: re.search(rf"\b{k} = (\w+)", body).group(1) for k in FLAT_KEYS}
    return out


@unittest.skipUnless(LIVE, "Anbennar CK3 not present")
class FlatValueTests(unittest.TestCase):
    def test_every_level_has_flat_values_at_least_its_castle(self):
        resolve = script_value_resolver(bh.ANBENNAR_CK3)
        castles = castle_flat_values(bh.ANBENNAR_CK3)
        self.assertEqual(set(castles), {"castle_01", "castle_02", "castle_03", "castle_04"})
        for n, lvl in enumerate(holds.LEVELS, 1):
            castle = castles[holds.ASSET_BAND[n]]
            for k in FLAT_KEYS:
                self.assertIn(k, lvl, f"{n} {k}")
                self.assertGreaterEqual(resolve(lvl[k]), resolve(castle[k]), f"level {n} {k}")

    def test_flat_values_never_fall(self):
        resolve = script_value_resolver(bh.ANBENNAR_CK3)
        for k in FLAT_KEYS:
            values = [resolve(lvl[k]) for lvl in holds.LEVELS]
            self.assertEqual(values, sorted(values), k)


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

    def test_loc_for_every_level_and_building(self):
        loc = bh.render_loc()
        self.assertTrue(loc.startswith("l_english:"))
        for key in KEYS + BUILDING_KEYS:
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
        for k in ("aov_is_hold", "aov_hold_is_ruined", "aov_hold_is_working", "aov_can_dig_at"):
            self.assertIn(f"{k} = {{", t)


@unittest.skipUnless(LIVE, "Anbennar CK3 not present")
class FreshTests(unittest.TestCase):
    def test_written_files_are_fresh(self):
        for rel, text in bh.render_all().items():
            data = (SUBMOD / rel).read_bytes()
            self.assertTrue(data.startswith(b"\xef\xbb\xbf"), rel)
            self.assertEqual(data[3:].decode("utf-8"), text, rel)


if __name__ == "__main__":
    unittest.main()
