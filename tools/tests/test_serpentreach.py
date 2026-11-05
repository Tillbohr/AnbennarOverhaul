import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import serpentreach_layout as sl  # noqa: E402
import shared_trace  # noqa: E402
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


def option_cfg(**values):
    """Serpentreach's data module with `values` replaced (West Dwarovar's tracer options)."""
    from types import SimpleNamespace
    from data import serpentreach as data
    return SimpleNamespace(**{**{k: getattr(data, k) for k in dir(data) if k.isupper()}, **values})


class OptionTests(unittest.TestCase):
    """Tracer options West Dwarovar needs; each is off by default so Serpentreach and Segbandal build unchanged."""

    @unittest.skipUnless(Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355").is_dir(),
                         "needs EU4 Anbennar")
    def test_regions_union(self):
        import eu4_import as eu4i
        eu4 = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355")
        regions = ("west_dwarovar_region", "serpents_vale_region")
        got, label = sl.region_set(option_cfg(REGIONS=regions), eu4)
        self.assertEqual(got, eu4i.region_provinces(regions[:1], eu4) | eu4i.region_provinces(regions[1:], eu4))
        self.assertIn("serpents_vale_region", label)
        # REGION alone still works
        self.assertEqual(sl.region_set(option_cfg(), eu4)[0], eu4i.region_provinces(("serpentreach_region",), eu4))

    @unittest.skipUnless(Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355").is_dir(),
                         "needs EU4 Anbennar")
    def test_excluded_area_not_traced(self):
        import eu4_import as eu4i
        eu4 = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355")
        areas = eu4i.province_areas(eu4)
        excluded = ("krakdhum_area", "anvils_horn_area", "dead_end_tunnel_area")
        got, _ = sl.region_set(option_cfg(REGIONS=("west_dwarovar_region",), EXCLUDE_AREAS=excluded), eu4)
        self.assertTrue(got)
        self.assertFalse({areas[p] for p in got} & set(excluded))
        self.assertIn(4208, eu4i.region_provinces(("west_dwarovar_region",), eu4))  # Krakdhumvror, now left out
        self.assertNotIn(4208, got)
        with self.assertRaisesRegex(GeneratorError, "orlghelovar_area"):
            sl.region_set(option_cfg(REGIONS=("west_dwarovar_region",), EXCLUDE_AREAS=("orlghelovar_area",)), eu4)

    def test_surface_type_only_in_surface_areas(self):
        cfg = option_cfg(SURFACE_AREAS=("royal_terrace_area",), SURFACE_BARONIES=3)
        self.assertEqual(sl.county_type(None, "royal_terrace_area", cfg, "c_royal_terrace"), ("surface", 3))
        self.assertEqual(sl.county_type("hills", "royal_terrace_area", cfg, "c_northvale"), ("surface", 3))
        self.assertEqual(sl.county_type("dwarven_road", "royal_terrace_area", cfg, "c_southern_entrance"),
                         ("dwarven_road", 1))  # the Vale's tunnels are caves
        with self.assertRaisesRegex(GeneratorError, "c_lamb_hills"):
            sl.county_type(None, "orldhum_area", cfg, "c_lamb_hills")
        with self.assertRaisesRegex(GeneratorError, "c_x"):
            sl.county_type(None, "royal_terrace_area", option_cfg(), "c_x")  # no SURFACE_AREAS: never surface

    def test_separate_non_neighbours(self):
        # labels 1 (x 0..9) and 2 (x 10..19) touch; EU4 makes them neighbours only in the second call
        labels = {(x, y): 1 if x < 10 else 2 for x in range(20) for y in range(5)}
        apart = sl.separate_non_neighbours(labels, {}, 4)
        ones = [x for (x, _), a in apart.items() if a == 1]
        twos = [x for (x, _), a in apart.items() if a == 2]
        self.assertGreaterEqual(min(twos) - max(ones), 4 + 1)  # a 4 px seam of rock
        self.assertEqual((max(ones), min(twos)), (7, 12))
        self.assertEqual(sl.separate_non_neighbours(labels, {1: {2}, 2: {1}}, 4), labels)

    def test_avoid_keeps_margin(self):
        # rock 9 everywhere; the label "a" covers x 5..25; an earlier region's floor pixel sits at (20, 6), still rock
        # on Anbennar's map
        W, H = 32, 12

        def ck(x, y):
            return 9 if 0 <= x < W and 0 <= y < H else 0
        labels = {(x, y): "a" for x in range(5, 26) for y in range(H)}
        free = sl.clip_floor(labels, ck, (0, 0, W, H), 9, 4, {})["a"]
        self.assertIn((20, 6), free)
        floor = sl.clip_floor(labels, ck, (0, 0, W, H), 9, 4, {}, avoid={(20, 6)})["a"]
        self.assertTrue(floor)
        self.assertFalse([p for p in floor if max(abs(p[0] - 20), abs(p[1] - 6)) < 4])
        self.assertIn((24, 6), floor)


def cave_and_vale():
    """A cave county (EU4 1, province 100, x 0..9) beside a two-barony surface county (EU4 2, provinces 200 and 201,
    x 10..19), rows 0..9: (counties, provinces, owner)."""
    cave = sorted(((x, y) for x in range(10) for y in range(10)), key=lambda p: (p[1], p[0]))
    vale = [sorted(((x, y) for x in range(10 + 5 * i, 15 + 5 * i) for y in range(10)), key=lambda p: (p[1], p[0]))
            for i in range(2)]
    counties = [sl.County("c_cave", 1, "Cave", "cave_area", "cavern", [100]),
                sl.County("c_vale", 2, "Vale", "vale_area", "surface", [200, 201])]
    provinces = {100: sl.Province(100, (1, 1, 1), "c_cave", 0, cave, (5, 5)),
                 200: sl.Province(200, (2, 2, 2), "c_vale", 0, vale[0], (12, 5)),
                 201: sl.Province(201, (3, 3, 3), "c_vale", 1, vale[1], (17, 5))}
    owner = {p: pid for pid, prov in provinces.items() for p in prov.pixels}
    return counties, provinces, owner


def linked_cave(gap):
    """Rock 9 with a cave floor (EU4 1, province 100) at x 0..4 and an earlier region's province 50 at x 5 + gap ..
    34 + gap, rows 0..19: (ck, counties, provinces, owner)."""
    floor = sorted(((x, y) for x in range(5) for y in range(20)), key=lambda p: (p[1], p[0]))

    def ck(x, y):
        if not (0 <= x < 200 and 0 <= y < 20):
            return 0
        return 50 if 5 + gap <= x < 35 + gap else 9
    counties = [sl.County("c_cave", 1, "Cave", "cave_area", "dwarven_road", [100])]
    provinces = {100: sl.Province(100, (1, 1, 1), "c_cave", 0, floor, (2, 10))}
    return ck, counties, provinces, {p: 100 for p in floor}


class ConnectionTests(unittest.TestCase):
    """Vale mouths, EU4 adjacencies.csv tunnel links and NO_LINK_PAIRS."""

    @unittest.skipUnless(Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355").is_dir(),
                         "needs EU4 Anbennar")
    def test_eu4_adjacencies_reads_dwarovrod_tunnel(self):
        pairs = sl.eu4_adjacencies(Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355"))
        self.assertIn((2884, 2885), pairs)
        self.assertIn((2885, 2884), pairs)

    def test_mouth_between_cave_and_surface(self):
        counties, provinces, owner = cave_and_vale()
        mouths = sl.mouths(counties, provinces, owner, option_cfg())
        self.assertEqual(len(mouths), 1)
        m = mouths[0]
        self.assertEqual((m.county, m.target), ("c_cave", 200))  # the surface county's capital barony
        self.assertEqual(provinces[owner[m.mouth]].county, "c_vale")
        self.assertEqual(owner[m.start], 100)
        self.assertEqual(abs(m.mouth[0] - m.start[0]) + abs(m.mouth[1] - m.start[1]), 1)
        self.assertTrue(m.pixels)
        self.assertTrue(all(owner[p] == 100 and math.dist(p, m.mouth) <= 10 for p in m.pixels))

    def test_link_within_reach(self):
        ck, counties, provinces, owner = linked_cave(40)
        cfg = option_cfg(LINK_REACH=60, LINK_CUT_THROUGH=(), NO_LINK_PAIRS=set())
        notes = []
        links = sl.adjacency_links(ck, counties, provinces, owner, {(1, 7), (7, 1)}, {7: {50}}, 9, cfg, notes)
        self.assertEqual([(l.county, l.target) for l in links], [("c_cave", 50)])
        self.assertTrue(all(owner[p] == 100 for p in links[0].pixels))
        self.assertTrue(any(ck(x + 1, y) == 50 for x, y in links[0].pixels))

    def test_link_bends_around_land(self):
        # the floor (x 0..4, y 0..10) and the target (x 60..89, y 0..10) face each other across a land block (province
        # 7, x 20..30, y 0..30); the only way is through the rock below it
        floor = sorted(((x, y) for x in range(5) for y in range(11)), key=lambda p: (p[1], p[0]))

        def ck(x, y):
            if not (0 <= x < 120 and 0 <= y < 50):
                return 0
            return 50 if 60 <= x < 90 and y <= 10 else 7 if 20 <= x <= 30 and y <= 30 else 9
        counties = [sl.County("c_cave", 1, "Cave", "cave_area", "dwarven_road", [100])]
        provinces = {100: sl.Province(100, (1, 1, 1), "c_cave", 0, floor, (2, 5))}
        owner = {p: 100 for p in floor}
        cfg = option_cfg(LINK_REACH=150, LINK_CUT_THROUGH=(), NO_LINK_PAIRS=set())
        links = sl.adjacency_links(ck, counties, provinces, owner, {(1, 7)}, {7: {50}}, 9, cfg, [])
        self.assertEqual(len(links), 1)
        tunnel = links[0].pixels
        touched = {ck(x + dx, y + dy) for x, y in tunnel for dx, dy in sl.N4} - {100}
        self.assertEqual(touched - {9, 50, 0}, set())  # never touches the land
        self.assertTrue(any(y > 30 for _, y in tunnel))  # went below the land block
        self.assertTrue(connected(tunnel | set(floor)))
        self.assertIn(50, touched)

    def test_link_beyond_reach_stops(self):
        ck, counties, provinces, owner = linked_cave(80)
        cfg = option_cfg(LINK_REACH=60, LINK_CUT_THROUGH=(), NO_LINK_PAIRS=set())
        with self.assertRaisesRegex(GeneratorError, "c_cave"):
            sl.adjacency_links(ck, counties, provinces, owner, {(1, 7)}, {7: {50}}, 9, cfg, [])

    def test_no_link_pairs_drops_opening(self):
        counties, provinces, owner = cave_and_vale()
        self.assertEqual(sl.mouths(counties, provinces, owner, option_cfg(NO_LINK_PAIRS={(2, 1)})), [])
        ck, counties, provinces, owner = linked_cave(80)  # out of reach, but dropped before it is tried
        cfg = option_cfg(LINK_REACH=60, LINK_CUT_THROUGH=(), NO_LINK_PAIRS={(1, 7)})
        self.assertEqual(sl.adjacency_links(ck, counties, provinces, owner, {(1, 7)}, {7: {50}}, 9, cfg, []), [])
        self.assertTrue(sl.dropped_pair(cfg, 7, 1))
        self.assertFalse(sl.dropped_pair(option_cfg(), 1, 7))  # no NO_LINK_PAIRS: nothing dropped


class SurfacePaintTests(unittest.TestCase):
    def test_paint_surface(self):
        # a surface county (x 10..19) beside a cave (x 0..9); the blend maps start with material 3 everywhere
        import terrain_fill as tf
        counties, provinces, owner = cave_and_vale()
        lay = sl.Layout(40, 10, counties, provinces, owner, [], {}, [])
        w, h = 40, 10
        index = tf.Tga(w, h, bytes(18), bytearray(bytes((3, 0, 0, 0)) * (w * h)), b"")
        intensity = tf.Tga(w, h, bytes(18), bytearray(bytes((255, 0, 0, 0)) * (w * h)), b"")
        new_index, new_intensity = sl.paint_surface(index, intensity, lay, {200: 7, 201: 8}, 4)

        def px(img, x, y):
            return tuple(img.pixels[(y * w + x) * 4:(y * w + x) * 4 + 4])
        self.assertEqual((px(new_index, 12, 5), px(new_intensity, 12, 5)), ((7, 0, 0, 0), (255, 0, 0, 0)))
        self.assertEqual(px(new_index, 17, 5)[0], 8)
        self.assertEqual((px(new_index, 30, 5), px(new_intensity, 30, 5)), ((3, 0, 0, 0), (255, 0, 0, 0)))
        near, mid = px(new_intensity, 21, 5), px(new_intensity, 22, 5)  # feathered into material 3 east of it
        self.assertEqual(px(new_index, 21, 5)[:2], (8, 3))
        self.assertTrue(0 < mid[0] < near[0] < 255 and near[0] + near[1] == 255, (near, mid))
        self.assertEqual(px(new_index, 5, 5), (3, 0, 0, 0))  # cave floor pixels are not surface paint
        self.assertEqual(bytes(index.pixels), bytes((3, 0, 0, 0)) * (w * h))  # inputs unchanged


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

    def test_locators_replace_stray_instances_of_new_ids(self):
        # Anbennar's other_stack_locators has stray instances for ids it has no province for (up to 9659); a new
        # province's id must end with exactly one instance, ours
        import build_serpentreach as bs
        out = bs.locator_override(LOCATORS, [(2, 10.5, 20.5)])
        self.assertEqual(out.count("\t\t\tid=2\n"), 1)
        self.assertIn("\t\t\tid=2\n\t\t\tposition={ 10.500000 0.000000 20.500000 }\n", out)
        self.assertIn("\t\t\tid=1\n\t\t\tposition={ 1.000000 0.000000 2.000000 }\n", out)
        self.assertTrue(out.endswith("\t\t}\n\t}\n}\n"))

    def test_crossing_joins_the_nearest_baronies_before_the_closing_row(self):
        import build_serpentreach as bs
        prov = {1: sl.Province(1, (1, 1, 1), "c_a", 0, [(0, 0), (5, 0)], (0, 0)),
                2: sl.Province(2, (2, 2, 2), "c_a", 1, [(9, 0)], (9, 0)),
                3: sl.Province(3, (3, 3, 3), "c_b", 0, [(30, 0), (14, 1)], (30, 0))}
        counties = [sl.County("c_a", 100, "Gorrod 2", "x", "cave", [1, 2]),
                    sl.County("c_b", 200, "Gorrod 1", "y", "cave", [3])]
        lay = sl.Layout(40, 4, counties, prov, {}, [], {}, [], [], [])
        cfg = option_cfg(CROSSINGS=((100, 200),))
        self.assertEqual(bs.crossings([lay], (cfg,)), [(2, 3, (9, 0), (14, 1), "Gorrod 2-Gorrod 1")])
        original = b"From;To\r\n1;2;sea;3;-1;-1;-1;-1;x\r\n-1;-1;;-1;-1;-1;-1;-1;\r\n"
        self.assertEqual(bs.render_adjacencies(original, [lay], cfgs=(cfg,)),
                         b"From;To\r\n1;2;sea;3;-1;-1;-1;-1;x\r\n2;3;sea;2426;9;0;14;1;Gorrod 2-Gorrod 1\r\n"
                         b"-1;-1;;-1;-1;-1;-1;-1;\r\n")
        with self.assertRaisesRegex(GeneratorError, "drawn in no layout"):
            bs.crossings([lay], (option_cfg(CROSSINGS=((100, 300),)),))

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
        cls.lays, ck3 = shared_trace.layouts()
        cls.lay = cls.lays[0]
        cls.files = bs.build_from_layout(ANBENNAR, cls.lays, ck3)

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
        from data import segbandal
        self.assertEqual(changed, {2426, segbandal.SOURCE_PROVINCE} | set(data.OPENING_CUT_THROUGH))
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

    def test_a_kingdom_per_hold_with_its_flag(self):
        import re
        from data import holds, serpentreach as data
        hold_counties = {h["title"] for h in holds.HOLDS[9:15]}  # the six Serpentreach holds
        self.assertEqual(set(data.KINGDOM_CAPITALS.values()), hold_counties)
        arms = self.files[self.bs.ARMS].decode("utf-8-sig")
        hold_duchies = {"k_verkal_skomdihr": "d_stunad_skomdihr"}  # EU4's area name; the others match the kingdom
        for kkey, ckey in data.KINGDOM_CAPITALS.items():
            for key in (kkey, hold_duchies.get(kkey, "d_" + kkey[2:]), ckey):
                self.assertRegex(arms, rf'(?m)^{key} = \{{\n(\t.*\n)*?\t\ttexture = "aov_{kkey[2:]}.dds"')
            self.assertTrue((self.bs.SUBMOD / self.bs.EMBLEM_DIR / f"aov_{kkey[2:]}.dds").is_file())
        titles = self.files["common/landed_titles/aov_serpentreach.txt"].decode("utf-8-sig")
        self.assertEqual(re.findall(r"(?m)^\t(k_\w+) = \{", titles), list(data.KINGDOMS))

    def test_every_duchy_has_arms(self):
        import re
        from build_hud_override import DEFAULT_GAME
        arms = self.files[self.bs.ARMS].decode("utf-8-sig")
        titles = self.files["common/landed_titles/aov_serpentreach.txt"].decode("utf-8-sig")
        duchies = re.findall(r"(?m)^\t\t(d_\w+) = \{", titles)
        self.assertEqual(len(duchies), 19)
        self.assertEqual(sorted(re.findall(r"(?m)^(d_\w+) = \{", arms)), sorted(duchies))
        self.assertEqual(arms.count("colored_emblem = {"), 13 + 1)  # 13 duchies without a hold; the forge has two
        self.assertEqual(self.bs.missing_charges(ANBENNAR, DEFAULT_GAME), [])

    def test_duchy_colours_differ_within_each_kingdom(self):
        titles = self.files["common/landed_titles/aov_serpentreach.txt"].decode("utf-8-sig")
        import re
        for block in re.split(r"(?m)^\tk_", titles)[1:]:
            colours = re.findall(r"(?m)^\t\td_\w+ = \{\n\t\t\tcolor = (\{[^}]*\})", block)
            self.assertEqual(len(colours), len(set(colours)), block[:40])

    def test_kings_hold_under_the_emperor(self):
        history = self.files["history/titles/aov_serpentreach.txt"].decode("utf-8-sig")
        self.assertIn("k_arg_ordstun = {\n\t860.1.1 = { holder = aov_sr_emperor_1 }", history)
        self.assertIn("k_gor_burad = {\n\t860.1.1 = { holder = aov_sr_gor_burad_1 liege = e_serpentreach }", history)
        self.assertIn("d_zarn = {\n\t860.1.1 = { holder = aov_sr_zarn_1 liege = k_gor_burad }", history)
        self.assertIn("d_kings_caverns = {\n\t860.1.1 = { holder = aov_sr_kings_caverns_1 liege = e_serpentreach }",
                      history)

    def test_each_duchy_lists_its_capital_county_first(self):
        """The game puts a duchy's capital building in its first county, whatever `capital` says (seen in game:
        Shazstundihr's, Arg-Ôrdstun's and Verkal Skomdihr's went to another county), so the hold county leads."""
        import re
        titles = self.files["common/landed_titles/aov_serpentreach.txt"].decode("utf-8-sig")
        duchies = re.findall(r"(?m)^\t\t(d_\w+) = \{\n\t\t\tcolor = [^\n]*\n\t\t\tcapital = (c_\w+)\n\n\t\t\t(c_\w+) = \{",
                             titles)
        self.assertEqual(len(duchies), 19)
        for dkey, capital, first in duchies:
            self.assertEqual(first, capital, dkey)

    def test_every_county_and_character_has_its_kingdom_culture(self):
        import re
        from data import serpentreach as data
        self.assertEqual(data.KINGDOM_CULTURES, {
            "k_orlghelovar": "cobalt_dwarvish", "k_shazstundihr": "marble_dwarvish",
            "k_arg_ordstun": "diamond_dwarvish", "k_verkal_skomdihr": "flint_dwarvish",
            "k_ovdal_lodhum": "garnet_dwarvish", "k_gor_burad": "basalt_dwarvish"})
        history = self.files["history/provinces/aov_serpentreach.txt"].decode("utf-8-sig")
        self.assertNotIn("stone_dwarvish", history)
        titles = self.files["common/landed_titles/aov_serpentreach.txt"].decode("utf-8-sig")
        for block in re.split(r"(?m)^\t(?=k_)", titles)[1:]:
            kkey = block.split(" ", 1)[0]
            for pid in re.findall(r"province = (\d+)", block):
                self.assertRegex(history, rf"(?m)^{pid} = \{{\t# .*\n\tculture = {data.KINGDOM_CULTURES[kkey]}\n")
        characters = self.files["history/characters/aov_serpentreach.txt"].decode("utf-8-sig")
        self.assertNotIn("stone_dwarvish", characters)
        self.assertRegex(characters, r'aov_sr_emperor_1 = \{[^}]*culture = "diamond_dwarvish"')
        self.assertRegex(characters, r'aov_sr_zarn_1 = \{[^}]*culture = "basalt_dwarvish"')
        dynasties = self.files[self.bs.DYNASTIES].decode("utf-8-sig")
        self.assertRegex(dynasties, r"aov_dynasty_still_caverns = \{[^}]*culture = garnet_dwarvish")

    def test_eu4_dynasty_names_without_prefix(self):
        import re
        want = {"d_arg_ordstun": "Whiteforged", "d_kings_caverns": "Stormheart", "d_ovdal_lodhum": "Garnetpick",
                "d_still_caverns": "Slatecutter", "d_shazstundihr": "Whitebeard", "d_south_altar": "Brightbeard"}
        dynasties = self.files[self.bs.DYNASTIES].decode("utf-8-sig")
        loc = self.files["localization/english/aov_serpentreach_l_english.yml"].decode("utf-8-sig")
        for dkey, name in want.items():
            block = re.search(rf"(?ms)^aov_dynasty_{dkey[2:]} = \{{.*?^\}}", dynasties).group(0)
            self.assertNotIn("prefix", block, dkey)
            self.assertIn(f' dynn_aov_{dkey[2:]}:0 "{name}"', loc)
        self.assertEqual(dynasties.count('prefix = "dynnp_az"'), 19 - len(want))
        names = re.findall(r'(?m)^ dynn_aov_\w+:0 "([^"]*)"', loc)
        self.assertEqual(len(names), len(set(names)))

    def test_culture_and_dynasty_tables_checked(self):
        from unittest import mock
        from data import serpentreach as data
        cultures = {k: v for k, v in data.KINGDOM_CULTURES.items() if k != "k_gor_burad"}
        with mock.patch.object(data, "KINGDOM_CULTURES", cultures):
            with self.assertRaisesRegex(GeneratorError, "KINGDOM_CULTURES"):
                self.bs.Realm(self.lay)
        with mock.patch.dict(data.DYNASTY_NAMES, {"d_nowhere": "Nobody"}):
            with self.assertRaisesRegex(GeneratorError, "d_nowhere"):
                self.bs.Realm(self.lay)


if __name__ == "__main__":
    unittest.main()
