import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import serpentreach_layout as sl  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402


def connected(pixels):
    pixels = set(pixels)
    start = next(iter(pixels))
    seen, stack = {start}, [start]
    while stack:
        x, y = stack.pop()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n in pixels and n not in seen:
                seen.add(n)
                stack.append(n)
    return len(seen) == len(pixels)


class GeometryTests(unittest.TestCase):
    def test_fit_affine_recovers_transform(self):
        pts = [(10, 20), (50, 25), (33, 80), (90, 60), (5, 5)]
        pairs = [(x, y, 3.5 * x + 1, 3.6 * y - 2) for x, y in pts]
        ax, ay = sl.fit_affine(pairs)
        for got, want in zip(ax + ay, (3.5, 0, 1, 0, 3.6, -2)):
            self.assertAlmostEqual(got, want, places=6)

    def test_slug_and_display_name(self):
        self.assertEqual(sl.slug("Argrod | 3 |"), "argrod_3")
        self.assertEqual(sl.slug("Gor Búrad"), "gor_burad")
        self.assertEqual(sl.slug("Arg-Ördstun"), "arg_ordstun")
        self.assertEqual(sl.slug("King's Border"), "kings_border")
        self.assertEqual(sl.display_name("Argrod | 3 |"), "Argrod 3")
        self.assertEqual(sl.display_name("Nez Argrod | 1 |"), "Nez Argrod 1")
        self.assertEqual(sl.display_name("Ovdal Lodhum"), "Ovdal Lodhum")

    def test_split_deterministic_and_connected(self):
        pixels = [(x, y) for y in range(10) for x in range(40)]
        a = sl.split(pixels, 4, 10, "c_test")
        b = sl.split(list(reversed(pixels)), 4, 10, "c_test")
        self.assertEqual(a, b)
        self.assertEqual(len(a), 4)
        self.assertEqual(sum(len(p) for p in a), 400)
        for piece in a:
            self.assertTrue(connected(piece))
        self.assertIn((19, 4), a[0])  # the capital holds the pixel nearest the centroid; ties: smallest (y, x)

    def test_split_one_piece_is_everything(self):
        pixels = [(x, 0) for x in range(30)]
        self.assertEqual(sl.split(pixels, 1, 10, "c_test"), [sorted(pixels, key=lambda p: (p[1], p[0]))])

    def test_split_too_small_raises(self):
        with self.assertRaisesRegex(GeneratorError, "c_tiny"):
            sl.split([(x, 0) for x in range(30)], 4, 10, "c_tiny")

    def test_chamfer(self):
        d = sl.chamfer({(5, 5)}, (0, 0, 11, 11), 3)
        self.assertEqual(d[(5, 5)], 0)
        self.assertEqual(d[(6, 5)], 1)
        self.assertEqual(d[(6, 6)], 1)
        self.assertEqual(d[(7, 5)], 2)
        self.assertEqual(d[(8, 8)], 3)
        self.assertNotIn((9, 5), d)  # beyond the limit


def synthetic(width=60, height=30):
    """A 2426 mountain (20000) over land province 1 (5000, rows y < 5) with a 10x4 cavern floor at x 20-29,
    y 12-15 (province 100), as (grid, layout, province map)."""
    from array import array
    import dwarven_mountains as dm
    import heightpack as hp
    ids = array("H", [1 if y < 5 else 2426 for y in range(height) for x in range(width)])
    vals = array("H", [5000 if y < 5 else 20000 for y in range(height) for x in range(width)])
    floor = sorted(((x, y) for x in range(20, 30) for y in range(12, 16)), key=lambda p: (p[1], p[0]))
    county = sl.County("c_a", 1, "A", "a_area", "cavern", [100])
    prov = sl.Province(100, (1, 2, 3), "c_a", 0, floor, (24, 13))
    lay = sl.Layout(width, height, [county], {100: prov}, {p: 100 for p in floor}, [], {"a_area": "A"}, [])
    return hp.Grid(width, height, vals), lay, dm.ProvinceMap(width, height, ids)


def material_layout():
    """Counties in four regions: a plain road, a Shazstundihr road, Gor Bûrad's two-barony hold, Lavawater."""
    counties = [sl.County("c_road", 1, "R", "argrod_origin_area", "dwarven_road", [1]),
                sl.County("c_marble_road", 2, "M", "shazstundihr_area", "dwarven_road", [2]),
                sl.County("c_marble_hold", 3, "H", "shazstundihr_area", "dwarven_hold_surface", [3]),
                sl.County("c_gor_burad", 4, "G", "gor_burad_area", "dwarven_hold", [4, 5]),
                sl.County("c_lavawater", 5, "L", "buradforge_area", "cavern", [6]),
                sl.County("c_cave", 6, "C", "thievesbane_area", "cavern", [7]),
                sl.County("c_molten_core", 7, "MC", "buradforge_area", "cavern", [8])]
    provinces = {}
    for c in counties:
        for i, pid in enumerate(c.baronies):
            provinces[pid] = sl.Province(pid, (pid, 0, 0), c.key, i, [(pid * 10, 0)], (pid * 10, 0))
    return sl.Layout(100, 10, counties, provinces, {}, [], {}, [])


class MaterialTests(unittest.TestCase):
    def test_regional_styles_and_overrides(self):
        m = sl.province_materials(material_layout())
        self.assertEqual(m[1], ("mayik_tiles_01", "rock_13_05_10"))  # tiled road, grey cliff
        self.assertEqual(m[2], ("desert_cracked_white", "mountains_white"))  # Shazstundihr's white road
        self.assertEqual(m[3], ("mayik_tiles_02", "mountains_white"))  # its marble-tiled hold
        self.assertEqual(m[4], ("hardened_lava_b", "rock_14_05_05"))  # the Basalt Hold
        self.assertEqual(m[5], ("lava", "rock_14_05_05"))  # its barony facing the lava caves
        self.assertEqual(m[6], ("lava", "rock_14_05_05"))  # Lavawater
        self.assertEqual(m[7], ("mountain_02_d_granitegrey", "rock_13_05_10"))  # a plain grey cave

    def test_used_materials_cover_every_choice(self):
        used = set(sl.used_materials())
        for pid, (floor, wall) in sl.province_materials(material_layout()).items():
            self.assertIn(floor, used)
            self.assertIn(wall, used)
        self.assertEqual(sl.used_materials(), sorted(used))

    def test_style_for_an_unknown_area_stops(self):
        from data import serpentreach as data
        with self.assertRaisesRegex(GeneratorError, "no_such"):
            sl.check_terrain_data({**data.AREA_STYLES, "x_area": "no_such"}, data.TERRAIN_STYLES)


class SmoothTests(unittest.TestCase):
    def test_smooth_fills_notches_and_drops_spurs(self):
        labels = {(x, y): "a" for x in range(10) for y in range(10)}
        del labels[(9, 5)]  # a notch in the edge
        labels[(14, 5)] = "a"  # a lone spur
        out = sl.smooth_labels(labels, radius=2, passes=1)
        self.assertEqual(out.get((9, 5)), "a")
        self.assertNotIn((14, 5), out)
        self.assertEqual(out.get((4, 4)), "a")

    def test_smooth_cuts_stairs(self):
        """A 3-px staircase edge (like EU4 pixels scaled 3.5x) loses its corner pixels."""
        labels = {(x, y): "a" for y in range(30) for x in range(0, 3 * (y // 3) + 3)}
        out = sl.smooth_labels(labels, radius=2, passes=3)

        def jumps(pixels):
            right = [max(x for x in range(40) if (x, y) in pixels) for y in range(6, 24)]
            return max(b - a for a, b in zip(right, right[1:]))
        self.assertEqual(jumps(labels), 3)
        self.assertLess(jumps(out), 3)

    def test_smooth_keeps_label_boundaries_between_counties(self):
        labels = {(x, y): ("a" if x < 10 else "b") for x in range(20) for y in range(10)}
        out = sl.smooth_labels(labels, radius=2, passes=3)
        self.assertEqual(out[(5, 5)], "a")
        self.assertEqual(out[(15, 5)], "b")


class CarveTests(unittest.TestCase):
    def test_carve_profile(self):
        from data import serpentreach as data
        grid, lay, pm = synthetic()
        new, report = sl.carve(grid, lay, pm, water=set())
        base = 5000
        self.assertEqual(report["base"], base)
        floor_h = base + data.TERRACE["cavern"] * data.TERRACE_STEP
        for p in lay.owner:
            self.assertEqual(new.get(*p), floor_h)
        row = [new.get(x, 13) for x in range(29, 29 + data.WALL_WIDTH + data.WALL_FADE + 2)]
        self.assertEqual(row, sorted(row))  # walls rise away from the floor
        self.assertLess(new.get(30, 13), grid.get(30, 13))  # a sloped wall, not a 1 px cliff
        self.assertEqual(new.get(29 + data.WALL_WIDTH, 13), grid.get(29 + data.WALL_WIDTH, 13))
        for y in range(pm.height):
            for x in range(pm.width):
                if math.hypot(max(20 - x, 0, x - 29), max(12 - y, 0, y - 15)) > data.WALL_WIDTH:
                    self.assertGreaterEqual(new.get(x, y), grid.get(x, y), (x, y))  # never lowered beyond the wall
        far = 29 + data.WALL_WIDTH + data.WALL_FADE + 1
        self.assertEqual(new.get(far, 13), grid.get(far, 13))
        self.assertEqual(new.get(10, 2), 5000)  # land untouched

    def test_carve_raises_low_rock_to_the_rim(self):
        from data import serpentreach as data
        grid, lay, pm = synthetic()
        for i in range(len(grid.values)):
            if pm.ids[i] == 2426:
                grid.values[i] = 4500  # rock lower than the rim
        new, _ = sl.carve(grid, lay, pm, water=set())
        floor_h = 5000 + data.TERRACE["cavern"] * data.TERRACE_STEP
        self.assertEqual(new.get(29 + data.WALL_WIDTH, 13), floor_h + data.MIN_WALL)

    def test_paint(self):
        import terrain_fill as tf
        from data import serpentreach as data
        _, lay, _ = synthetic()
        w, h = 60, 30
        blank = tf.Tga(w, h, bytes(18), bytearray(w * h * 4), b"")
        index, intensity = sl.paint(blank, blank, lay, {100: (7, 9)})

        def px(img, x, y):
            return bytes(img.pixels[(y * w + x) * 4:(y * w + x) * 4 + 4])
        self.assertEqual(px(index, 24, 13), bytes((7, 0, 0, 0)))  # the cavern's own floor material
        self.assertEqual(px(intensity, 24, 13), bytes((255, 0, 0, 0)))
        self.assertEqual(px(index, 29 + data.WALL_WIDTH, 13), bytes((7, 9, 0, 0)))
        self.assertEqual(px(intensity, 29 + data.WALL_WIDTH, 13), bytes((0, 255, 0, 0)))  # wall at full weight
        mid = px(intensity, 30, 13)
        self.assertTrue(0 < mid[1] < 255 and mid[0] + mid[1] == 255, mid)  # blended on the slope
        self.assertEqual(px(index, 45, 13), bytes(4))  # untouched
        self.assertEqual(bytes(blank.pixels), bytes(w * h * 4))  # inputs not modified


LOCATORS = """\ufeffgame_object_locator={
\tname="buildings"
\tinstances={
\t\t{
\t\t\tid=1
\t\t\tposition={ 1.000000 0.000000 2.000000 }
\t\t\trotation={ -0.000000 -0.000000 -0.000000 1.000000 }
\t\t\tscale={ 1.000000 1.000000 1.000000 }
\t\t}
\t\t{
\t\t\tid=2
\t\t\tposition={ 3.000000 0.000000 4.000000 }
\t\t\trotation={ -0.000000 -0.000000 -0.000000 1.000000 }
\t\t\tscale={ 1.000000 1.000000 1.000000 }
\t\t}
\t}
}
"""


class OutputTests(unittest.TestCase):
    def test_locators_keep_existing_instances(self):
        import build_serpentreach as bs
        out = bs.locator_override(LOCATORS, [(7, 10.5, 20.5)])
        self.assertTrue(out.startswith("\ufeff# Anbennar Overhaul: generated by tools/build_serpentreach.py"))
        body = LOCATORS.lstrip("\ufeff")
        self.assertIn(body[:body.index("\t}\n}\n")], out)  # every original instance, byte for byte
        self.assertEqual(out.count("\t\t\tid="), 3)
        self.assertIn("\t\t\tid=7\n\t\t\tposition={ 10.500000 0.000000 20.500000 }\n", out)
        self.assertTrue(out.endswith("\t\t}\n\t}\n}\n"))

    def test_title_collision_raises(self):
        import build_serpentreach as bs
        with self.assertRaisesRegex(GeneratorError, "c_x"):
            bs.check_new_keys({"c_x", "c_y"}, "e_a = {\n\tc_x = {\n\t}\n}\n")
        bs.check_new_keys({"c_y"}, "e_a = {\n\tc_x = {\n\t}\n}\n")

    def test_life_dates_deterministic_and_in_range(self):
        import build_serpentreach as bs
        a = bs.life_date("aov_sr_x_1", (830, 845))
        self.assertEqual(a, bs.life_date("aov_sr_x_1", (830, 845)))
        y, m, d = map(int, a.split("."))
        self.assertTrue(830 <= y <= 845 and 1 <= m <= 12 and 1 <= d <= 28)


EU4 = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355")
ANBENNAR = Path(__file__).resolve().parents[2].parent / "anbennar-ck3-dev-master"


@unittest.skipUnless(EU4.is_dir() and ANBENNAR.is_dir(), "needs EU4 Anbennar and Anbennar CK3")
class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_serpentreach as bs
        cls.bs = bs
        cls.files = bs.build_all(ANBENNAR, EU4)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (self.bs.SUBMOD / rel).is_file() or (self.bs.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_serpentreach.py")

    def test_only_province_2426_changed(self):
        import dwarven_mountains as dm
        definition = self.files["map_data/definition.csv"].decode("utf-8", errors="replace")
        new = dm.load_province_map(self.files["map_data/provinces.png"], definition)
        old = dm.load_province_map((ANBENNAR / "map_data/provinces.png").read_bytes(), definition)
        from data import serpentreach as data
        changed = {o for o, n in zip(old.ids, new.ids) if o != n}
        self.assertEqual(changed, {2426} | set(data.OPENING_CUT_THROUGH))
        self.assertGreater(len(set(new.ids)), len(set(old.ids)) + 100)

    def test_every_barony_has_history_and_loc(self):
        import re
        titles = self.files["common/landed_titles/aov_serpentreach.txt"].decode("utf-8-sig")
        history = self.files["history/provinces/aov_serpentreach.txt"].decode("utf-8-sig")
        loc = self.files["localization/english/aov_serpentreach_l_english.yml"].decode("utf-8-sig")
        provinces = re.findall(r"province = (\d+)", titles)
        self.assertEqual(len(provinces), len(set(provinces)))
        for pid in provinces:
            self.assertRegex(history, rf"(?m)^{pid} = \{{")
        for key in re.findall(r"(?m)^\t*([ekdcb]_\w+) = \{", titles):
            self.assertRegex(loc, rf"(?m)^ {key}:0 \"")


if __name__ == "__main__":
    unittest.main()
