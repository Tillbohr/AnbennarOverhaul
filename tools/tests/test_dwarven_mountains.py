import math
import sys
import unittest
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import dwarven_mountains as dm  # noqa: E402
import heightpack as hp  # noqa: E402
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


class SoftCeilingTests(unittest.TestCase):
    def test_identity_up_to_ceiling(self):
        self.assertEqual(dm.soft_ceiling(60000), 60000)
        self.assertEqual(dm.soft_ceiling(123), 123)

    def test_monotone_and_bounded(self):
        last = 60000
        for v in range(60001, 200000, 997):
            now = dm.soft_ceiling(v)
            self.assertGreaterEqual(now, last)
            self.assertLessEqual(now, 65535)
            last = now
        self.assertLess(dm.soft_ceiling(1e6), 65536)


class LiftFactorTests(unittest.TestCase):
    def test_capped(self):
        self.assertEqual(dm.lift_factor(20000, 10000), data.LIFT_MAX)

    def test_rubyhold(self):
        self.assertAlmostEqual(dm.lift_factor(40982, 15517), 1.3541, places=4)

    def test_already_high(self):
        self.assertEqual(dm.lift_factor(52000, 15000), 1)
        self.assertEqual(dm.lift_factor(9000, 10000), 1)


def fixture_range(heights=15000, ground=10000):
    """60x40 plains (province 2, height `ground`) with a dwarven block (province 1) at x 20-29, y 10-19."""
    w, h = 60, 40
    ids = array("H", [2]) * (w * h)
    vals = array("H", [ground]) * (w * h)
    for y in range(10, 20):
        for x in range(20, 30):
            ids[y * w + x] = 1
            vals[y * w + x] = heights
    return dm.ProvinceMap(w, h, ids), hp.Grid(w, h, vals)


class RaiseTests(unittest.TestCase):
    def test_range_lift(self):
        pm, grid = fixture_range()
        new, report = dm.raise_heights(grid, pm, {1}, set(), set(), [])
        self.assertEqual(new.get(25, 15), 19000)  # 10000 + 5000 * 1.8
        self.assertEqual(report["ranges"][0]["factor"], data.LIFT_MAX)
        self.assertEqual(report["ranges"][0]["ground"], 10000)
        self.assertEqual(report["ranges"][0]["peak_before"], 15000)
        self.assertEqual(report["ranges"][0]["peak_after"], 19000)
        self.assertEqual(grid.get(25, 15), 15000)  # the input is untouched

    def test_nothing_lowered_nothing_changed_far(self):
        pm, grid = fixture_range()
        new, _ = dm.raise_heights(grid, pm, {1}, set(), set(), [])
        for y in range(40):
            for x in range(60):
                self.assertGreaterEqual(new.get(x, y), grid.get(x, y))
                dist = max(max(20 - x, x - 29, 0), max(10 - y, y - 19, 0))
                if dist > data.FADE_PX:
                    self.assertEqual(new.get(x, y), grid.get(x, y))
        self.assertLessEqual(max(new.values), 65535)

    def test_fade_is_gradual(self):
        pm, grid = fixture_range()
        new, _ = dm.raise_heights(grid, pm, {1}, set(), set(), [])
        row = [new.get(x, 15) for x in range(19, 5, -1)]
        self.assertEqual(row, sorted(row, reverse=True))
        self.assertGreater(new.get(19, 15), 10000)
        self.assertEqual(new.get(19 - data.FADE_PX, 15), 10000)

    def test_water_changes_only_in_fade(self):
        pm, grid = fixture_range()
        for y in range(40):
            for x in (5, 18, 37, 45):
                pm.ids[y * 60 + x] = 3
        new, _ = dm.raise_heights(grid, pm, {1}, {3}, set(), [])
        self.assertGreater(new.get(18, 15), 10000)  # in the fade band
        self.assertEqual(new.get(5, 15), 10000)  # 15 px from the block
        self.assertGreater(new.get(37, 15), 10000)  # 8 px east: inside the band
        self.assertEqual(new.get(45, 15), 10000)  # 16 px east
        self.assertGreater(new.get(18, 0), 10000)

    def test_already_tall_range_unchanged(self):
        pm, grid = fixture_range(heights=52000)
        new, report = dm.raise_heights(grid, pm, {1}, set(), set(), [])
        self.assertEqual(report["ranges"][0]["factor"], 1)
        self.assertEqual(new.values, grid.values)

    def test_peak_above_lift_peak_unchanged(self):
        pm, grid = fixture_range(heights=62000, ground=10000)
        new, _ = dm.raise_heights(grid, pm, {1}, set(), set(), [])
        self.assertEqual(new.values, grid.values)  # peak above LIFT_PEAK: factor 1

    SITE = dm.GateSite("c_dw", "c_n", 30, 30, (-1.0, 0.0))

    def shoulder_fixture(self, islands=True):
        """80x60 flat 10000: dwarven province 1 at x < 40, normal 2 beside it, an island of normal land (2) and of
        water (3) west of the gate, off its axis."""
        w, h = 80, 60
        ids = array("H", [1 if x < 40 else 2 for y in range(h) for x in range(w)])
        vals = array("H", [10000]) * (w * h)
        for y in range(36 if islands else 0, 41 if islands else 0):
            for x in range(10, 19):
                ids[y * w + x] = 2 if x < 14 else 3
        return dm.ProvinceMap(w, h, ids), hp.Grid(w, h, vals)

    def test_shoulder_profile_along_the_axis(self):
        pm, grid = self.shoulder_fixture(islands=False)
        new, report = dm.raise_heights(grid, pm, {1}, {3}, set(), [self.SITE], inset=2.0, overrides={})
        # the gate is at (28, 30); behind it is toward -x
        row = [new.get(28 - t, 30) for t in range(0, data.SHOULDER_LENGTH + 3)]
        start, ramp, length = data.SHOULDER_START, data.SHOULDER_RAMP, data.SHOULDER_LENGTH
        self.assertTrue(all(v == 10000 for v in row[:start + 1]))  # t <= START: untouched
        self.assertTrue(all(v == 10000 for v in row[length + 1:]))  # beyond the end
        rising = row[start:start + ramp + 1]
        self.assertEqual(rising, sorted(rising))
        for v in row[start + ramp:length - 6 + 1]:
            self.assertGreaterEqual(v, 10000 + 0.95 * data.SHOULDER_RISE)
        falling = row[length - 6:length + 1]
        self.assertEqual(falling, sorted(falling, reverse=True))
        limit = data.SHOULDER_RISE * math.pi / (2 * data.SHOULDER_RAMP) + 3
        self.assertLessEqual(max(abs(a - b) for a, b in zip(row[:start + ramp + 1], row[1:])), limit)
        fall_limit = data.SHOULDER_RISE * math.pi / (2 * 6) + 3  # the last 6 px ease back down
        self.assertLessEqual(max(abs(a - b) for a, b in zip(row[length - 6:], row[length - 5:])), fall_limit)
        entry = report["sites"][0]
        self.assertEqual(entry["foot"], 10000)
        self.assertEqual(entry["shoulder_max"], 10000 + data.SHOULDER_RISE)

    def test_shoulder_is_limited_to_the_strip_and_never_lowers(self):
        pm, grid = self.shoulder_fixture()
        new, _ = dm.raise_heights(grid, pm, {1}, {3}, set(), [self.SITE], inset=2.0, overrides={})
        w = pm.width
        for y in range(pm.height):
            for x in range(w):
                i = y * w + x
                self.assertGreaterEqual(new.values[i], grid.values[i])
                t, lat = 28 - x, abs(y - 30)
                outside = (t < data.SHOULDER_START or t > data.SHOULDER_LENGTH or lat >= data.SHOULDER_HALF_WIDTH
                           or pm.ids[i] != 1)
                if outside:
                    self.assertEqual(new.values[i], grid.values[i], (x, y))
        self.assertGreater(new.get(15, 31), 10000)
        self.assertEqual(new.get(12, 38), 10000)  # normal-land island inside the strip
        self.assertEqual(new.get(17, 38), 10000)  # water island

    def test_shoulder_is_gentle_sideways_too(self):
        pm, grid = self.shoulder_fixture(islands=False)
        new, _ = dm.raise_heights(grid, pm, {1}, {3}, set(), [self.SITE], inset=2.0, overrides={})
        column = [new.get(20, y) for y in range(30, 30 + data.SHOULDER_HALF_WIDTH + 1)]
        self.assertEqual(column, sorted(column, reverse=True))
        self.assertLessEqual(max(a - b for a, b in zip(column, column[1:])),
                             data.SHOULDER_RISE * math.pi / (2 * data.SHOULDER_HALF_WIDTH) + 3)

    def test_shoulder_uses_the_final_gate_position(self):
        pm, grid = self.shoulder_fixture(islands=False)
        overrides = {("c_dw", "c_n"): {"dx": -4.0}}
        placements = dm.gate_placements([self.SITE], 2.0, overrides)
        self.assertEqual(placements[0][1], (24.0, 30.0))
        new, _ = dm.raise_heights(grid, pm, {1}, {3}, set(), [self.SITE], inset=2.0, overrides=overrides)
        self.assertEqual(new.get(25, 30), 10000)  # t = -1 from the moved gate
        self.assertGreater(new.get(12, 30), 10000 + 0.95 * data.SHOULDER_RISE)  # t = 12: on the plateau

    def test_shoulder_raises_the_foot_relative_height(self):
        pm, grid = self.shoulder_fixture(islands=False)
        for i in range(len(grid.values)):
            grid.values[i] = 20000 + (i % pm.width)  # not flat: foot is the height at the gate pixel
        new, report = dm.raise_heights(grid, pm, {1}, {3}, set(), [self.SITE], inset=2.0, overrides={})
        foot = grid.get(28, 30)
        self.assertEqual(report["sites"][0]["foot"], foot)
        self.assertGreaterEqual(new.get(14, 30), foot + 0.95 * data.SHOULDER_RISE)

    def test_shoulder_blends_from_the_local_ground_not_the_foot(self):
        """A high foot among low ground: the faint edge of the shoulder must not pull pixels up to the foot."""
        pm, grid = self.shoulder_fixture(islands=False)
        w = pm.width
        for y in range(pm.height):
            for x in range(w):
                grid.values[y * w + x] = 30000 if 26 <= x <= 30 and 28 <= y <= 32 else 8000
        new, report = dm.raise_heights(grid, pm, {1}, set(), set(), [self.SITE], inset=2.0, overrides={})
        entry = report["sites"][0]
        top = dm.soft_ceiling(entry["foot"] + data.SHOULDER_RISE)
        faint = 0
        for y in range(pm.height):
            for x in range(40):
                i = y * w + x
                weight = dm.shoulder_weight((28 - x) * 1.0, abs(y - 30.0))
                self.assertGreaterEqual(new.values[i], grid.values[i])
                if 0 < weight < 0.1:
                    faint += 1
                    self.assertLessEqual(new.values[i] - grid.values[i], weight * (top - grid.values[i]) + 1, (x, y))
        self.assertGreater(faint, 10)
        self.assertLessEqual(entry["step_after"], max(entry["step_before"], 6000) + 1)

    def test_sloped_ground_keeps_steps_gentle(self):
        pm, grid = self.shoulder_fixture(islands=False)
        w = pm.width
        for i in range(len(grid.values)):
            grid.values[i] = 8000 + 300 * min(i % w, 40)
        new, report = dm.raise_heights(grid, pm, {1}, set(), set(), [self.SITE], inset=2.0, overrides={})
        entry = report["sites"][0]
        for i in range(len(new.values)):
            self.assertGreaterEqual(new.values[i], grid.values[i])
        self.assertLessEqual(entry["step_after"], max(entry["step_before"], 6000))

    def test_shoulder_eases_down_toward_a_province_border(self):
        pm, grid = self.shoulder_fixture(islands=False)
        w = pm.width
        for y in range(pm.height):
            for x in (10, 11):
                pm.ids[y * w + x] = 2  # a strip of normal land across the shoulder
        new, report = dm.raise_heights(grid, pm, {1}, set(), set(), [self.SITE], inset=2.0, overrides={})
        self.assertEqual(new.get(11, 30), 10000)
        # (12, 30) is on the plateau (t = 16) one pixel from the strip: 1/8 of the rise
        self.assertLessEqual(new.get(12, 30) - 10000, data.SHOULDER_RISE / data.SHOULDER_EDGE_FADE + 3)
        rise = [new.get(x, 30) - 10000 for x in range(12, 17)]  # d = 1..5 px from the strip
        self.assertEqual(rise, sorted(rise))
        self.assertLessEqual(report["sites"][0]["step_after"], 6000)

    def test_overlapping_gates_do_not_depend_on_input_order(self):
        pm, grid = self.shoulder_fixture(islands=False)
        a = dm.GateSite("c_a", "c_n", 30, 30, (-1.0, 0.0))
        b = dm.GateSite("c_b", "c_n", 30, 36, (-1.0, 0.0))
        one, _ = dm.raise_heights(grid, pm, {1}, set(), set(), [a, b], inset=2.0, overrides={})
        two, _ = dm.raise_heights(grid, pm, {1}, set(), set(), [b, a], inset=2.0, overrides={})
        self.assertEqual(one.values, two.values)

    def test_shoulder_reaches_along_a_diagonal_axis(self):
        pm, grid = self.shoulder_fixture(islands=False)
        site = dm.GateSite("c_dw", "c_n", 30, 30, (-math.sqrt(0.5), -math.sqrt(0.5)))
        new, _ = dm.raise_heights(grid, pm, {1}, set(), set(), [site], inset=0.0, overrides={})
        t = data.SHOULDER_LENGTH - 8  # still on the plateau
        x, y = round(30 - t * math.sqrt(0.5)), round(30 - t * math.sqrt(0.5))
        self.assertGreater(new.get(x, y), 10000 + 0.9 * data.SHOULDER_RISE)

    def test_shoulder_changes_only_dwarven_or_impassable_land(self):
        pm, grid = self.shoulder_fixture()
        for y in range(20, 30):
            for x in range(10, 20):
                pm.ids[y * pm.width + x] = 4  # impassable
        new, _ = dm.raise_heights(grid, pm, {1}, {3}, {4}, [self.SITE], inset=2.0, overrides={})
        self.assertGreater(new.get(15, 25), 10000)

    def test_no_pixel_is_lowered_at_a_site(self):
        w, h = 60, 41
        ids = array("H", [1 if x < 30 else 2 for y in range(h) for x in range(w)])
        vals = array("H", [6000 if x < 30 else 5000 for y in range(h) for x in range(w)])
        pm, grid = dm.ProvinceMap(w, h, ids), hp.Grid(w, h, vals)
        site = dm.GateSite("c_dw", "c_n", 29, 20, (-1.0, 0.0))
        new, _ = dm.raise_heights(grid, pm, {1}, set(), set(), [site])
        for i in range(w * h):
            self.assertGreaterEqual(new.values[i], grid.values[i])

    def test_two_ranges_independent(self):
        pm, grid = fixture_range()
        for y in range(10, 20):
            for x in range(40, 50):
                pm.ids[y * 60 + x] = 4
                grid.values[y * 60 + x] = 15000
        new, report = dm.raise_heights(grid, pm, {1, 4}, set(), set(), [])
        self.assertEqual(len(report["ranges"]), 2)
        self.assertEqual(new.get(25, 15), new.get(45, 15))


def sea_fixture():
    """20x11: province 3 (lake) at x 0-4, province 1 (the hold) at x 5-14, province 2 (sea) at x 15-19."""
    w, h = 20, 11
    ids = array("H", [3] * 5 + [1] * 10 + [2] * 5) * h
    return dm.ProvinceMap(w, h, ids)


SEA_TITLES = "e_a = { k_a = { d_a = { c_hold = { b_hold = { province = 1 } } } } }\n"
HOLDS = [{"title": "c_hold", "barony": "b_hold"}, {"title": "c_other", "barony": "b_other"}]


class SeaGateTests(unittest.TestCase):
    def setUp(self):
        self.pm = sea_fixture()
        self.border = dm.border_pixels(self.pm)

    def test_sea_zone_ids_ignore_lakes_and_rivers(self):
        self.assertEqual(dm.sea_zone_ids(DEFAULT_MAP), {1, 2, 3})

    def test_barony_province(self):
        self.assertEqual(dm.barony_province(SEA_TITLES, "b_hold"), 1)
        with self.assertRaisesRegex(GeneratorError, "b_missing"):
            dm.barony_province(SEA_TITLES, "b_missing")

    def test_site_is_the_shore_pixel_nearest_the_locator_facing_the_sea(self):
        site = dm.sea_gate_site(self.pm, self.border, {2}, 1, (8.0, 5.0), "c_hold")
        self.assertEqual((site.dwarven_county, site.normal_county, site.x, site.y), ("c_hold", "sea", 14, 5))
        self.assertAlmostEqual(site.inward[0], -1.0)  # from the sea (x 15) toward the land
        self.assertAlmostEqual(site.inward[1], 0.0)

    def test_lakes_do_not_count_as_shore(self):
        # the lake side (x 5) is nearer the locator, but only sea zones count
        site = dm.sea_gate_site(self.pm, self.border, {2}, 1, (6.0, 5.0), "c_hold")
        self.assertEqual(site.x, 14)

    def test_inward_uses_only_sea_pixels_within_six_px(self):
        # site (14, 2): the touching sea pixels (15, 0..7) are within 6 px (centroid y 3.5), (15, 8..10) are not
        site = dm.sea_gate_site(self.pm, self.border, {2}, 1, (14.0, 2.0), "c_hold")
        self.assertEqual((site.x, site.y), (14, 2))
        self.assertAlmostEqual(site.inward[1] / site.inward[0], 1.5)
        self.assertAlmostEqual(math.hypot(*site.inward), 1.0)

    def test_errors(self):
        with self.assertRaisesRegex(GeneratorError, "shore"):
            dm.sea_gate_site(self.pm, self.border, {99}, 1, (8.0, 5.0), "c_hold")

    def test_with_sea_gates_replaces_land_sites_only_of_that_county(self):
        keep = dm.GateSite("c_keep", "c_x", 1, 1, (1.0, 0.0))
        land = dm.GateSite("c_hold", "c_n", 6, 5, (0.0, 1.0))
        out = dm.with_sea_gates([keep, land], ("c_hold",), HOLDS, self.pm, self.border, {2}, SEA_TITLES,
                                {1: (8.0, 5.0)})
        self.assertEqual([(s.dwarven_county, s.normal_county) for s in out],
                         [("c_keep", "c_x"), ("c_hold", "sea")])
        self.assertIs(out[0], keep)

    def test_with_sea_gates_errors(self):
        args = (self.pm, self.border, {2}, SEA_TITLES, {1: (8.0, 5.0)})
        with self.assertRaisesRegex(GeneratorError, "c_nothold"):
            dm.with_sea_gates([], ("c_nothold",), HOLDS, *args)
        with self.assertRaisesRegex(GeneratorError, "locator"):
            dm.with_sea_gates([], ("c_hold",), HOLDS, self.pm, self.border, {2}, SEA_TITLES, {})
        with self.assertRaisesRegex(GeneratorError, "b_other"):
            dm.with_sea_gates([], ("c_other",), HOLDS, *args)


class SpacedSitesTests(unittest.TestCase):
    def setUp(self):
        self.titles = {1: ("e", "k", "c_a"), 2: ("e", "k", "c_b"), 3: ("e", "k", "c_x"), 4: ("e", "k", "c_y"),
                       5: ("e", "k", "c_far"), 6: ("e", "k", "c_far2")}
        self.border = {(1, 3): [(0, 0)] * 5, (3, 1): [(0, 0)] * 5,
                       (2, 4): [(0, 0)] * 9, (4, 2): [(0, 0)] * 9,
                       (5, 6): [(0, 0)] * 2}

    def test_close_sites_keep_longer_border(self):
        a = dm.GateSite("c_a", "c_x", 100, 100, (1.0, 0.0))
        b = dm.GateSite("c_b", "c_y", 108, 100, (1.0, 0.0))
        self.assertEqual(dm.spaced_sites([a, b], self.border, self.titles, 16), [b])

    def test_tie_keeps_first(self):
        self.border[(2, 4)] = [(0, 0)] * 5
        a = dm.GateSite("c_a", "c_x", 100, 100, (1.0, 0.0))
        b = dm.GateSite("c_b", "c_y", 108, 100, (1.0, 0.0))
        self.assertEqual(dm.spaced_sites([a, b], self.border, self.titles, 16), [a])

    def test_far_sites_kept_in_order(self):
        a = dm.GateSite("c_a", "c_x", 100, 100, (1.0, 0.0))
        b = dm.GateSite("c_b", "c_y", 116, 100, (1.0, 0.0))
        self.assertEqual(dm.spaced_sites([a, b], self.border, self.titles, 16), [a, b])

    def test_chain_keeps_strongest_then_next_free(self):
        a = dm.GateSite("c_a", "c_x", 100, 100, (1.0, 0.0))
        b = dm.GateSite("c_b", "c_y", 108, 100, (1.0, 0.0))
        self.titles[7] = ("e", "k", "c_z")
        self.titles[8] = ("e", "k", "c_w")
        self.border[(7, 8)] = [(0, 0)] * 3
        c = dm.GateSite("c_z", "c_w", 126, 100, (1.0, 0.0))
        self.assertEqual(dm.spaced_sites([a, b, c], self.border, self.titles, 16), [b, c])


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
        cls.spaced = dm.spaced_sites(cls.sites, cls.border, cls.titles, data.GATE_MIN_SPACING)
        cls.old = hp.Grid.from_png(pngio.read_png(read("map_data/heightmap.png")))
        cls.new, cls.report = dm.raise_heights(cls.old, cls.pm, cls.dwarven, cls.water, cls.impassable, cls.spaced)

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

    def test_spacing_keeps_sites_apart(self):
        # c_oldpassage's three sites are 21-38 px apart, so the 16 px rule merges none of the 12 real sites.
        self.assertEqual(len(self.spaced), 12)
        for i, a in enumerate(self.spaced):
            for b in self.spaced[i + 1:]:
                self.assertGreaterEqual(math.hypot(a.x - b.x, a.y - b.y), data.GATE_MIN_SPACING)

    def test_every_range_reaches_peak_or_a_limit(self):
        self.assertEqual(len(self.report["ranges"]), 9)
        for r in self.report["ranges"]:
            self.assertTrue(r["peak_after"] >= data.LIFT_PEAK - 1 or r["factor"] in (1, data.LIFT_MAX), r)

    def test_rubyhold_range(self):
        ruby = next(r for r in self.report["ranges"] if 62 in r["provinces"])
        self.assertTrue(1.3 < ruby["factor"] < 1.4, ruby)
        self.assertAlmostEqual(ruby["peak_after"], data.LIFT_PEAK, delta=50)

    def test_nothing_lowered_anywhere(self):
        w = self.pm.width
        for y in range(self.pm.height):
            a = self.old.values[y * w:(y + 1) * w]
            b = self.new.values[y * w:(y + 1) * w]
            if a != b:
                self.assertTrue(all(q >= p for p, q in zip(a, b)), y)
        self.assertLessEqual(max(self.new.values), 65535)

    def test_far_pixels_unchanged(self):
        w, h, ids = self.pm.width, self.pm.height, self.pm.ids
        reach = data.FADE_PX + 1
        rows = []  # bit x of rows[y] = a dwarven pixel within `reach` columns of x in row y
        for y in range(h):
            bits = 0
            for x, v in enumerate(ids[y * w:(y + 1) * w]):
                if v in self.dwarven:
                    bits |= 1 << x
            wide = bits
            for k in range(1, reach + 1):
                wide |= (bits << k) | (bits >> k)
            rows.append(wide)
        near = []
        for y in range(h):
            m = 0
            for j in range(max(0, y - reach), min(h, y + reach + 1)):
                m |= rows[j]
            near.append(m)
        shoulder_reach = math.ceil(math.hypot(data.SHOULDER_LENGTH, data.SHOULDER_HALF_WIDTH)) + 1 + data.GATE_INSET
        changed = 0
        for y in range(h):
            a = self.old.values[y * w:(y + 1) * w]
            b = self.new.values[y * w:(y + 1) * w]
            if a == b:
                continue
            for x in range(w):
                if a[x] != b[x]:
                    changed += 1
                    # outside the fade band only a gate's shoulder (impassable land beside a gate) may change
                    self.assertTrue((near[y] >> x) & 1 or any(math.hypot(x - g.x, y - g.y) <= shoulder_reach
                                                              for g in self.spaced), (x, y))
        self.assertGreater(changed, 0)


if __name__ == "__main__":
    unittest.main()
