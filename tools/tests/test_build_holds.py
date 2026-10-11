import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_holds as bh  # noqa: E402
from data import holds  # noqa: E402

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
                if not val:
                    self.assertNotIn(name, block)
                    continue
                self.assertAlmostEqual(value(block, name), val, msg=f"{n} {name}")

    def test_no_empty_blocks(self):
        self.assertNotRegex(self.text, r"_modifier = \{\s*\}")

    def test_assets_come_from_the_band(self):
        _, assets = bh.castle_assets(bh.ANBENNAR_CK3)
        self.assertGreater(len(assets["castle_03"]), 5)
        self.assertIn("asset = {", self.blocks["dwarven_hold_05"])
        self.assertIn(assets["castle_03"][1], self.blocks["dwarven_hold_05"])

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


class ValueAndLocTests(unittest.TestCase):
    def test_values(self):
        v = bh.render_values()
        for name in ("aov_hold_level", "aov_dig_target", "aov_dig_campaign_cost", "aov_dig_campaign_base"):
            self.assertIn(f"{name} = {{", v)
        self.assertIn("has_building_or_higher = dwarven_hold_10", v)

    def test_loc_for_every_level_and_building(self):
        loc = bh.render_loc()
        self.assertTrue(loc.startswith("l_english:"))
        for key in KEYS + BUILDING_KEYS:
            for k in (f"building_{key}", f"building_{key}_desc", f"building_type_{key}", f"building_type_{key}_desc"):
                self.assertIn(f" {k}:0 \"", loc)


@unittest.skipUnless(LIVE, "Anbennar CK3 not present")
class FreshTests(unittest.TestCase):
    def test_written_files_are_fresh(self):
        for rel, text in bh.render_all().items():
            data = (SUBMOD / rel).read_bytes()
            self.assertTrue(data.startswith(b"\xef\xbb\xbf"), rel)
            self.assertEqual(data[3:].decode("utf-8"), text, rel)


if __name__ == "__main__":
    unittest.main()
