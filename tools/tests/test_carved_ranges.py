import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import carved_ranges as cr  # noqa: E402
import heightpack as hp  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import serpentreach as sr  # noqa: E402

W, H = 60, 30
ROCK, ROAD, LAND, OTHER_ROCK = 9, 5, 1, 8


def synthetic():
    """Land (x < 10) at 5000; rock (x >= 10) at 20000; a road (y 13..15) from x 10 to 39 opening on the land;
    a second impassable province beyond x 50."""
    ids, values = [], []
    for y in range(H):
        for x in range(W):
            if x < 10:
                pid, h = LAND, 5000
            elif 13 <= y <= 15 and x < 40:
                pid, h = ROAD, 20000
            elif x > 50:
                pid, h = OTHER_ROCK, 20000
            else:
                pid, h = ROCK, 20000
            ids.append(pid)
            values.append(h)
    pm = SimpleNamespace(width=W, height=H, ids=ids)
    return hp.Grid(W, H, values[:]), pm


class CarvedRangeTests(unittest.TestCase):
    def test_carved_range_and_rock(self):
        _, pm = synthetic()
        rng = cr.carved_range([{2}, {ROAD}], {ROAD: ("e_x", "k_x", "c_road")}, "c_road")
        self.assertEqual(rng, {ROAD})
        floor = cr.floor_pixels(pm, rng)
        self.assertEqual(len(floor), 30 * 3)
        self.assertEqual(cr.rock_around(pm, floor, {ROCK, OTHER_ROCK}, 4), {ROCK})
        with self.assertRaises(GeneratorError):
            cr.carved_range([{ROAD}], {}, "c_missing")

    def test_carve(self):
        grid, pm = synthetic()
        floor = cr.floor_pixels(pm, {ROAD})
        new, report = cr.carve(grid, floor, {ROAD: "dwarven_road"}, {ROCK}, pm, set(), ramp=6, ground_radius=20)
        self.assertEqual(report["base"], 5000)
        self.assertEqual(new.get(30, 14), 5000)  # flat floor at the ground (roads: terrace 0)
        self.assertEqual(new.get(10, 14), 5000)  # opening pixel meets the land at its height
        self.assertEqual(new.get(5, 14), 5000)  # land untouched
        self.assertEqual(new.get(30, 13 - sr.WALL_WIDTH), 20000)  # wall reaches the rock
        self.assertLess(new.get(30, 12), 20000)  # sloped, not a 1 px cliff
        self.assertEqual(new.get(30, 2), 20000)  # far rock untouched

    def test_carve_raises_low_rock_and_terraces_holds(self):
        grid, pm = synthetic()
        for i, p in enumerate(pm.ids):
            if p == ROCK:
                grid.values[i] = 6000
        floor = cr.floor_pixels(pm, {ROAD})
        new, _ = cr.carve(grid, floor, {ROAD: "dwarven_hold"}, {ROCK}, pm, set(), ramp=6, ground_radius=20)
        hold = 5000 + sr.TERRACE["dwarven_hold"] * sr.TERRACE_STEP
        self.assertEqual(new.get(30, 14), hold)
        self.assertEqual(new.get(30, 13 - sr.WALL_WIDTH), hold + sr.MIN_WALL)  # rim above low rock

    def test_unknown_terrain_stops(self):
        grid, pm = synthetic()
        with self.assertRaises(GeneratorError):
            cr.carve(grid, cr.floor_pixels(pm, {ROAD}), {ROAD: "plains"}, {ROCK}, pm, set(), ramp=6, ground_radius=20)

    def test_paint_only_walls_rock(self):
        import terrain_fill as tf
        _, pm = synthetic()
        floor = cr.floor_pixels(pm, {ROAD})
        blank = tf.Tga(W, H, bytes(18), bytearray(W * H * 4), b"")
        index, intensity = cr.paint(blank, blank, floor, {ROAD: (7, 9)}, pm, {ROCK})

        def px(img, x, y):
            return bytes(img.pixels[(y * W + x) * 4:(y * W + x) * 4 + 4])
        self.assertEqual(px(index, 20, 14), bytes((7, 0, 0, 0)))
        self.assertEqual(px(index, 20, 13 - sr.WALL_WIDTH), bytes((7, 9, 0, 0)))
        self.assertEqual(px(intensity, 8, 14), bytes(4))  # land is not painted
        self.assertEqual(cr.province_materials(floor, {ROAD: "dwarven_road"}),
                         {ROAD: (sr.TERRAIN_STYLES["default"]["dwarven_road"], sr.TERRAIN_STYLES["default"]["wall"])})


if __name__ == "__main__":
    unittest.main()
