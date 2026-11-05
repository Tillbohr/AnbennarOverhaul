import re
import sys
import unittest
from array import array
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import dwarven_mountains as dm  # noqa: E402
import range_rock as rr  # noqa: E402

EU4 = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355")
ANBENNAR = Path(__file__).resolve().parents[2].parent / "anbennar-ck3-dev-master"
ROCK, LAND, OTHER_ROCK = 2426, 1, 2608


def cfg(**over):
    base = dict(ROCK_SOURCE=ROCK, ROCK_AVOID=(OTHER_ROCK,), ROCK_MIN_HEIGHT=48, ROCK_ALWAYS=2, ROCK_REACH=30,
                ROCK_MAX_Y=10_000, ROCK_SLIVER=2, ROCK_ISLAND_GAP=3)
    base.update(over)
    return SimpleNamespace(**base)


class Map:
    """A small map from rows of characters, the first row the north: # rock high, . rock low (open waste), L land,
    O the avoided province, 1 and 2 the floors of regions 0 and 1. The rows are padded with open waste, so the box
    `rock_pixels` searches ends in it."""

    PAD = 40

    def __init__(self, rows):
        width = len(rows[0]) + 2 * self.PAD
        rows = ["." * width] * self.PAD + ["." * self.PAD + r + "." * self.PAD for r in rows] + ["." * width] * self.PAD
        self.height_px, self.width = len(rows), width
        ids = array("H")
        self.high = set()
        self.floors = {"1": set(), "2": set()}
        for y in range(self.height_px):
            row = rows[self.height_px - 1 - y]
            for x, c in enumerate(row):
                ids.append({"L": LAND, "O": OTHER_ROCK}.get(c, ROCK))
                if c == "#":
                    self.high.add((x, y))
                if c in self.floors:
                    self.floors[c].add((x, y))
        self.pm = dm.ProvinceMap(width, self.height_px, ids)

    def at(self, x, row):
        """The pixel at column `x` of row `row` of the rows given."""
        return x + self.PAD, self.height_px - 1 - self.PAD - row

    def rock(self, **over):
        regions = [self.floors["1"], self.floors["2"]]
        return rr.rock_pixels(self.pm, lambda x, y: 100 if (x, y) in self.high else 20, regions, set(), cfg(**over))


class RockPixelsTests(unittest.TestCase):
    def test_takes_high_ground_and_a_ring_around_the_floor(self):
        m = Map(["LLLLLLLLLLLLLLLL",
                 "LLLL########LLLL",
                 "LLLL##1.....####",
                 "LLLLLLLLLLLLLLLL"])
        rock = m.rock(ROCK_ALWAYS=1, ROCK_SLIVER=1, ROCK_ISLAND_GAP=0)[0]
        self.assertIn(m.at(7, 1), rock)  # high ground
        self.assertIn(m.at(7, 2), rock)  # the ring: low, a pixel from the floor
        self.assertNotIn(m.at(6, 2), rock)  # the floor itself

    def test_open_waste_stays(self):
        m = Map(["1###........................"])
        rock = m.rock(ROCK_ALWAYS=1, ROCK_REACH=20)[0]
        self.assertIn(m.at(3, 0), rock)
        self.assertNotIn(m.at(20, 0), rock)

    def test_reach_limits_the_range(self):
        m = Map(["1" + "#" * 30])
        rock = m.rock(ROCK_ALWAYS=1, ROCK_REACH=5)[0]
        self.assertIn(m.at(5, 0), rock)
        self.assertNotIn(m.at(6, 0), rock)

    def test_nearest_floor_wins(self):
        m = Map(["1#########2"])
        first, second = m.rock(ROCK_ALWAYS=1, ROCK_SLIVER=1, ROCK_ISLAND_GAP=0)
        self.assertIn(m.at(3, 0), first)
        self.assertIn(m.at(7, 0), second)
        self.assertFalse(first & second)

    def test_rock_nearer_the_avoided_province_stays(self):
        m = Map(["1#########O"])
        rock = m.rock(ROCK_ALWAYS=1, ROCK_SLIVER=1, ROCK_ISLAND_GAP=0)[0]
        self.assertIn(m.at(3, 0), rock)
        self.assertNotIn(m.at(8, 0), rock)

    def test_enclosed_low_rock_joins(self):
        m = Map(["LLLLLLLLLLLLLLLLLL",
                 "L1##############LL",
                 "L##............##L",
                 "L##............##L",
                 "L##............##L",
                 "L##............##L",
                 "L##############LLL",
                 "LLLLLLLLLLLLLLLLLL"])
        rock = m.rock(ROCK_ALWAYS=1, ROCK_SLIVER=1, ROCK_ISLAND_GAP=0)[0]
        self.assertIn(m.at(8, 3), rock)

    def test_a_sliver_against_the_range_joins(self):
        m = Map(["1###.LLLLL",
                 "####.LLLLL",
                 "####.LLLLL",
                 "####......"])
        rock = m.rock(ROCK_ALWAYS=1, ROCK_ISLAND_GAP=0)[0]
        self.assertIn(m.at(4, 1), rock)

    def test_a_ridge_across_a_thin_strip_of_land_joins(self):
        m = Map(["LLLLLLLLLLLLLL",
                 "L1##LL#####LLL",
                 "LLLLLLLLLLLLLL"])
        self.assertIn(m.at(8, 1), m.rock(ROCK_ALWAYS=1)[0])
        self.assertNotIn(m.at(8, 1), m.rock(ROCK_ALWAYS=1, ROCK_ISLAND_GAP=1)[0])

    def test_above_the_cap_stays(self):
        m = Map(["#####",
                 "#####",
                 "##1##"])
        y_of_floor = m.at(2, 2)[1]
        rock = m.rock(ROCK_ALWAYS=1, ROCK_MAX_Y=y_of_floor + 1, ROCK_ISLAND_GAP=0)[0]
        self.assertIn(m.at(2, 1), rock)
        self.assertNotIn(m.at(2, 0), rock)

    def test_no_floors_no_rock(self):
        m = Map(["###"])
        self.assertEqual(m.rock(), [set(), set()])

    def test_make_rock_puts_the_locator_on_the_rock(self):
        ring = {(x, y) for x in range(10) for y in range(10)} - {(x, y) for x in range(2, 8) for y in range(2, 8)}
        rock = rr.make_rock(7, (1, 2, 3), "Ring", ring)
        self.assertIn(rock.locator, ring)
        self.assertEqual(rock.pixels, sorted(ring, key=lambda p: (p[1], p[0])))


@unittest.skipUnless(EU4.is_dir() and ANBENNAR.is_dir(), "needs EU4 Anbennar and Anbennar CK3")
class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_serpentreach as bs
        import serpentreach_layout as sl
        cls.bs = bs
        cls.ck3 = sl.load_ck3(ANBENNAR)
        cls.lays = bs.layouts(ANBENNAR, EU4, cls.ck3)
        cls.rocks = bs.range_rocks(ANBENNAR, cls.lays, cls.ck3)
        cls.serp_rock, cls.wd_rock = cls.rocks
        cls.floors = {p for lay in cls.lays for p in lay.owner}

    def test_rock_is_small_enough_to_fill(self):
        limit = self.bs.large_impassable_limit(ANBENNAR)
        self.assertEqual(limit, 500000)
        for rock in self.rocks:
            self.assertLess(len(rock.pixels), limit, rock.name)

    def test_rock_covers_each_range(self):
        # the ranges' rock, not a ring around the floors: tuning must not shrink it by accident
        self.assertGreater(len(self.serp_rock.pixels), 80_000)
        self.assertGreater(len(self.wd_rock.pixels), 250_000)

    def test_ids_follow_the_layouts(self):
        last = max(self.lays[2].provinces)
        self.assertEqual([r.id for r in self.rocks], [last + 1, last + 2])

    def test_rock_only_takes_2426_and_no_floor(self):
        pm = self.ck3[0]
        for rock in self.rocks:
            self.assertEqual({pm.ids[y * pm.width + x] for x, y in rock.pixels}, {2426}, rock.name)
            self.assertFalse(self.floors & set(rock.pixels), rock.name)
        self.assertFalse(set(self.serp_rock.pixels) & set(self.wd_rock.pixels))

    def test_no_floor_of_the_two_regions_touches_the_big_waste(self):
        # what the player would see as a hole in the range's colour
        pm = self.ck3[0]
        rock = set(self.serp_rock.pixels) | set(self.wd_rock.pixels)
        for lay in (self.lays[0], self.lays[2]):
            for x, y in lay.owner:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if pm.ids[q[1] * pm.width + q[0]] == 2426:
                        self.assertTrue(q in rock or q in self.floors, q)

    def test_rock_stays_off_segbandals_rim(self):
        # Segbandal starts at x 3344; only West Dwarovar's southern tail comes near it
        seg_x = min(p[0] for p in self.lays[1].owner)
        self.assertFalse([p for p in self.wd_rock.pixels if p[0] > seg_x + 200])

    def test_default_map_lists_the_rock_as_impassable(self):
        original = (ANBENNAR / "map_data/default.map").read_bytes()
        text = self.bs.render_default_map(original, self.rocks)
        self.assertTrue(text.startswith(original))
        _, impassable = dm.default_map_sets(text.decode("utf-8-sig"))
        self.assertLessEqual({r.id for r in self.rocks}, set(impassable))
        self.assertLessEqual({2426, 2608}, set(impassable))

    def test_locators_only_where_anbennar_lists_impassable_provinces(self):
        files = self.bs.render_locators(ANBENNAR, self.lays, self.rocks)
        for name in self.bs.LOCATOR_FILES:
            text = files[f"{self.bs.LOCATOR_DIR}/{name}.txt"].decode("utf-8")
            expected = 1 if name in self.bs.ROCK_LOCATOR_FILES else 0
            for rock in self.rocks:
                self.assertEqual(len(re.findall(rf"\bid={rock.id}\n", text)), expected, (name, rock.id))

    def test_definition_rows_are_unique(self):
        rows = self.bs.render_definition((ANBENNAR / "map_data/definition.csv").read_bytes(), self.lays, self.rocks)
        rows = rows.decode("utf-8", errors="replace").splitlines()
        self.assertEqual([r.split(";")[4] for r in rows[-2:]], [r.name for r in self.rocks])
        colours = [tuple(r.split(";")[1:4]) for r in rows if r[:1].isdigit() and r.split(";")[0] != "0"]
        self.assertEqual(len(colours), len(set(colours)))


if __name__ == "__main__":
    unittest.main()
