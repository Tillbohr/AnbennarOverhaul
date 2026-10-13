import math
import sys
import unittest
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import dwarven_mountains as dm  # noqa: E402
import pngio  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import map_graphics as data  # noqa: E402

ANBENNAR = Path(__file__).resolve().parents[2].parent / "anbennar-ck3-dev-master"
LIVE = (ANBENNAR / "map_data" / "provinces.png").is_file()

DEFAULT_MAP = """\
#comment
sea_zones = LIST { 1 2 3 }
lakes = RANGE { 10 12 }
river_provinces = RANGE { 20 21 }
river_provinces = LIST { 30 }
impassable_mountains = RANGE { 40 41 }
impassable_seas = LIST { 50 }
"""

TERRAIN = """\
default_land=plains
default_sea=sea
1=cavern
2=plains
3=dwarven_road
4=dwarven_hold
5=dwarven_hold_surface
6=mountains
"""

TITLES = """\
e_one = {
\tcolor = { 1 2 3 } # a comment { with brace
\tk_alive = {
\t\td_duchy = {
\t\t\tc_first = {
\t\t\t\tb_a = { province = 11 }
\t\t\t\tb_b = { province = 12 }
\t\t\t}
\t\t}
\t}
\t#k_dead = {
\t#\tc_ghost = { b_g = { province = 99 } }
\t#}
}
e_two = {
\tk_other = {
\t\tc_second = {
\t\t\tb_c = {
\t\t\t\tprovince = 13
\t\t\t}
\t\t}
\t}
}
"""


class ParserTests(unittest.TestCase):
    def test_default_map_sets(self):
        water, impassable = dm.default_map_sets(DEFAULT_MAP)
        self.assertEqual(water, {1, 2, 3, 10, 11, 12, 20, 21, 30})
        self.assertEqual(impassable, {40, 41, 50})

    def test_province_terrain(self):
        terrain = dm.province_terrain(TERRAIN)
        self.assertEqual(terrain, {1: "cavern", 2: "plains", 3: "dwarven_road", 4: "dwarven_hold",
                                   5: "dwarven_hold_surface", 6: "mountains"})
        self.assertEqual(dm.dwarven_provinces(terrain), {1, 3, 4, 5})

    def test_province_titles_ignore_comments(self):
        titles = dm.province_titles(TITLES)
        self.assertEqual(titles, {11: ("e_one", "k_alive", "c_first"), 12: ("e_one", "k_alive", "c_first"),
                                  13: ("e_two", "k_other", "c_second")})
        self.assertNotIn(99, titles)

    def test_load_province_map(self):
        # 2x2 RGB image, PNG rows top first; colour (1,2,3) = province 7, (9,9,9) unknown.
        pixels = bytes([1, 2, 3, 9, 9, 9,
                        4, 5, 6, 1, 2, 3])
        png = pngio.write_png(pngio.Image(2, 2, 8, 2, pixels))
        definition = "﻿0;0;0;0;x;x;\n7;1;2;3;Seven;x;\n8;4;5;6;Eight;x;\n"
        pm = dm.load_province_map(png, definition)
        self.assertEqual((pm.width, pm.height), (2, 2))
        # map row y = 0 is the bottom PNG row
        self.assertEqual(list(pm.ids), [8, 7, 7, 0])

    def test_load_province_map_rejects_bad_png(self):
        png = pngio.write_png(pngio.Image(1, 1, 16, 0, bytes(2)))
        with self.assertRaises(GeneratorError):
            dm.load_province_map(png, "0;0;0;0;x;x;\n")


def synthetic():
    """Provinces 1 (dwarven), 2 (normal) and 3 (water), side by side, 6 wide and 3 high."""
    ids = array("H", [1, 1, 2, 2, 3, 3] * 3)
    return dm.ProvinceMap(6, 3, ids)


SYN_TITLES = {1: ("e_d", "k_d", "c_dw"), 2: ("e_n", "k_n", "c_n")}


class GeometryTests(unittest.TestCase):
    def test_border_pixels(self):
        border = dm.border_pixels(synthetic())
        self.assertEqual(sorted(border[(1, 2)]), [(1, 0), (1, 1), (1, 2)])
        self.assertEqual(sorted(border[(2, 1)]), [(2, 0), (2, 1), (2, 2)])
        self.assertEqual(sorted(border[(2, 3)]), [(3, 0), (3, 1), (3, 2)])
        self.assertEqual(sorted(border[(3, 2)]), [(4, 0), (4, 1), (4, 2)])
        self.assertNotIn((1, 3), border)

    def test_border_pixels_vertical(self):
        pm = dm.ProvinceMap(2, 2, array("H", [1, 1, 2, 2]))
        border = dm.border_pixels(pm)
        self.assertEqual(sorted(border[(1, 2)]), [(0, 0), (1, 0)])
        self.assertEqual(sorted(border[(2, 1)]), [(0, 1), (1, 1)])

    def test_ranges(self):
        border = {(1, 2): [(0, 0)], (2, 1): [(1, 0)], (2, 3): [(1, 0)], (3, 2): [(2, 0)],
                  (4, 5): [(0, 0)], (5, 4): [(0, 0)], (1, 9): [(0, 0)], (9, 1): [(0, 0)]}
        found = dm.ranges({1, 2, 3, 4, 5, 6}, border)
        self.assertEqual(sorted(sorted(r) for r in found), [[1, 2, 3], [4, 5], [6]])

    def test_gate_site(self):
        pm = synthetic()
        border = dm.border_pixels(pm)
        sites = dm.gate_sites(pm, {1}, {3}, set(), SYN_TITLES, border, ())
        self.assertEqual(len(sites), 1)
        site = sites[0]
        self.assertEqual((site.dwarven_county, site.normal_county), ("c_dw", "c_n"))
        self.assertEqual((site.x, site.y), (1, 1))
        self.assertEqual(pm.ids[site.y * pm.width + site.x], 1)
        self.assertAlmostEqual(site.inward[0], -1.0)
        self.assertAlmostEqual(site.inward[1], 0.0)

    def test_inward_points_into_dwarven_province(self):
        # dwarven province in the south, normal land to the north: inward must point south (y negative)
        ids = array("H", [1] * 5 + [1] * 5 + [2] * 5 + [2] * 5)  # rows y=0,1 are 1; y=2,3 are 2
        pm = dm.ProvinceMap(5, 4, ids)
        sites = dm.gate_sites(pm, {1}, set(), set(), SYN_TITLES, dm.border_pixels(pm), ())
        self.assertEqual(len(sites), 1)
        self.assertAlmostEqual(math.hypot(*sites[0].inward), 1.0)
        self.assertAlmostEqual(sites[0].inward[1], -1.0)
        self.assertEqual((sites[0].x, sites[0].y), (2, 1))

    def test_excluded_empire_skipped(self):
        pm = synthetic()
        border = dm.border_pixels(pm)
        self.assertEqual(dm.gate_sites(pm, {1}, {3}, set(), SYN_TITLES, border, ("e_d",)), [])

    def test_water_and_impassable_neighbours_make_no_site(self):
        pm = synthetic()
        border = dm.border_pixels(pm)
        self.assertEqual(dm.gate_sites(pm, {1}, {2}, set(), SYN_TITLES, border, ()), [])
        self.assertEqual(dm.gate_sites(pm, {1}, set(), {2}, SYN_TITLES, border, ()), [])

    def test_dwarven_neighbour_makes_no_site(self):
        pm = synthetic()
        border = dm.border_pixels(pm)
        self.assertEqual(dm.gate_sites(pm, {1, 2}, {3}, set(), SYN_TITLES, border, ()), [])


@unittest.skipUnless(LIVE, "Anbennar map data not found")
class RealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = lambda p: (ANBENNAR / p).read_bytes()  # noqa: E731
        text = lambda p: (ANBENNAR / p).read_text(encoding="utf-8-sig")  # noqa: E731
        cls.pm = dm.load_province_map(read("map_data/provinces.png"), text("map_data/definition.csv"))
        cls.water, cls.impassable = dm.default_map_sets(text("map_data/default.map"))
        cls.terrain = dm.province_terrain(text("common/province_terrain/00_province_terrain.txt"))
        titles_text = "\n".join(p.read_text(encoding="utf-8-sig")
                                for p in sorted((ANBENNAR / "common/landed_titles").glob("*.txt")))
        cls.titles = dm.province_titles(titles_text)
        cls.dwarven = dm.dwarven_provinces(cls.terrain)
        cls.border = dm.border_pixels(cls.pm)
        cls.sites = dm.gate_sites(cls.pm, cls.dwarven, cls.water, cls.impassable, cls.titles, cls.border,
                                  data.GATE_EXCLUDE_REGIONS)

    def test_dimensions(self):
        self.assertEqual((self.pm.width, self.pm.height), (8192, 4096))

    def test_dwarven_province_count(self):
        self.assertEqual(len(self.dwarven), 119)

    def test_nine_ranges(self):
        found = dm.ranges(self.dwarven, self.border)
        self.assertEqual(sorted((len(r) for r in found), reverse=True), [52, 31, 14, 13, 3, 3, 1, 1, 1])

    def test_excluded_regions_produce_no_site(self):
        self.assertTrue(self.sites)
        for site in self.sites:
            pid = self.pm.ids[site.y * self.pm.width + site.x]
            self.assertIn(pid, self.dwarven)
            self.assertNotIn(self.titles[pid][0], data.GATE_EXCLUDE_REGIONS)
        everything = dm.gate_sites(self.pm, self.dwarven, self.water, self.impassable, self.titles, self.border, ())
        self.assertGreater(len(everything), len(self.sites))

    def test_rubyhold_sites(self):
        near = [s for s in self.sites if math.hypot(s.x - 954, s.y - 2451) <= 60]
        self.assertEqual(sorted((s.dwarven_county, s.normal_county) for s in near),
                         [("c_redgate", "c_rewanfork"), ("c_rose_mines", "c_rivergate")])
        self.assertIn(("c_redgate", "c_rewanfork"), [(s.dwarven_county, s.normal_county) for s in self.sites])
        self.assertIn(("c_rose_mines", "c_rivergate"), [(s.dwarven_county, s.normal_county) for s in self.sites])


if __name__ == "__main__":
    unittest.main()
