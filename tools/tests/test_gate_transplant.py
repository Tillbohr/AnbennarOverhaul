import math
import sys
import unittest
from array import array
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dwarven_mountains as dm  # noqa: E402
import gate_transplant as gt  # noqa: E402
import heightpack as hp  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import map_graphics as data  # noqa: E402

K2 = 2 * data.EREBOR_GATE_SCALE  # a gate of size K2 has transplant scale k = 2
RIE = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/2291024373")


@contextmanager
def no_jitter():
    """Object jitter and height jitter off, so positions are the plain frame maths."""
    with mock.patch.multiple(data, TRANSPLANT_JITTER_POS=0.0, TRANSPLANT_JITTER_YAW=0.0,
                             TRANSPLANT_JITTER_SCALE=(1.0, 1.0), TRANSPLANT_HEIGHT_JITTER=0.0):
        yield


def tent(radius=18.0, peak=6000.0):
    """A cone peaking at (t, l) = (6, 0): peak - 1000 * distance, within the radius."""
    def delta(t, l):
        return 0.0 if math.hypot(t, l) > radius else max(0.0, peak - 1000.0 * math.hypot(t - 6, l))
    return delta


def comp(radius=18.0, delta=None, objects=None):
    objs = objects if objects is not None else [
        gt.CompositionObject("mountain_01_mesh", 5.0, 2.0, 0.0, 0.5, 1.0),
        gt.CompositionObject("mountain_02_mesh", 4.0, -3.0, 0.76, -0.2, 0.5)]
    return gt.Composition(objs, delta or tent(radius), 6000.0, radius)


def plain(w=140, h=140, height=10000):
    """All land (province 2) at one height."""
    return dm.ProvinceMap(w, h, array("H", [2]) * (w * h)), hp.Grid(w, h, array("H", [height]) * (w * h))


def site(county="c_a", inward=(0.0, 1.0)):
    return dm.GateSite(county, "c_x", 70, 70, inward)


def run(pm, grid, sites, c=None, water=(), overrides=None):
    placed = [(s, K2, (s.x, s.y)) for s in sites]
    return gt.transplant(grid, pm, set(water), placed, c or comp(), overrides if overrides is not None else {})


class FrameTests(unittest.TestCase):
    def objects(self, inward, pin):
        pm, grid = plain()
        with no_jitter():
            _, plans = run(pm, grid, [site(inward=inward)], overrides={("c_a", "c_x"): pin})
        return plans[0].objects

    def test_gate_facing_north(self):
        # k = 2; u = (0, 1), v = (1, 0): object (t 5, l 2) -> (70 + 4, 70 + 10)
        o = self.objects((0.0, 1.0), {"mirror": False, "turn": 0})[0]
        self.assertEqual(o.mesh, "mountain_01_mesh")
        self.assertAlmostEqual(o.x, 74.0)
        self.assertAlmostEqual(o.y, 80.0)
        self.assertAlmostEqual(o.yaw, 0.5)
        self.assertAlmostEqual(o.scale, 2.0)
        self.assertEqual(o.y_offset, 0.0)

    def test_gate_facing_east(self):
        # u = (1, 0), v = (0, -1): (t 5, l 2) -> (70 + 10, 70 - 4)
        o = self.objects((1.0, 0.0), {"mirror": False, "turn": 0})[0]
        self.assertAlmostEqual(o.x, 80.0)
        self.assertAlmostEqual(o.y, 66.0)
        self.assertAlmostEqual(o.yaw, math.pi / 2 + 0.5)

    def test_mirror_flips_l_and_yaw(self):
        o = self.objects((0.0, 1.0), {"mirror": True, "turn": 0})[0]
        self.assertAlmostEqual(o.x, 66.0)
        self.assertAlmostEqual(o.y, 80.0)
        self.assertAlmostEqual(o.yaw, -0.5)

    def test_y_offset_and_scale_follow_k(self):
        rock = self.objects((0.0, 1.0), {"mirror": False, "turn": 0})[1]
        self.assertAlmostEqual(rock.y_offset, 0.76 * 2)
        self.assertAlmostEqual(rock.scale, 1.0)  # k * 0.5

    def test_pinned_turn_rotates_the_composition_and_object_yaws(self):
        turn = math.radians(10)
        o = self.objects((0.0, 1.0), {"mirror": False, "turn": 10})[0]
        s, c = math.sin(turn), math.cos(turn)  # u = (sin a, cos a), v = (cos a, -sin a)
        self.assertAlmostEqual(o.x, 70 + 2 * (5 * s + 2 * c))
        self.assertAlmostEqual(o.y, 70 + 2 * (5 * c - 2 * s))
        self.assertAlmostEqual(o.yaw, turn + 0.5)

    def test_jitter_stays_within_bounds(self):
        pm, grid = plain()
        _, plans = run(pm, grid, [site()], overrides={("c_a", "c_x"): {"mirror": False, "turn": 0}})
        o = plans[0].objects[0]
        self.assertLessEqual(math.hypot(o.x - 74.0, o.y - 80.0), 2 * data.TRANSPLANT_JITTER_POS * math.sqrt(2) + 1e-9)
        self.assertLessEqual(abs(o.yaw - 0.5), math.radians(data.TRANSPLANT_JITTER_YAW) + 1e-9)
        self.assertGreaterEqual(o.scale, 2 * data.TRANSPLANT_JITTER_SCALE[0] - 1e-9)
        self.assertLessEqual(o.scale, 2 * data.TRANSPLANT_JITTER_SCALE[1] + 1e-9)


class ConeTests(unittest.TestCase):
    PIN = {("c_a", "c_x"): {"mirror": False, "turn": 0, "height": 1.0}}

    def test_peak_is_at_the_right_distance_along_the_axis(self):
        pm, grid = plain()
        new, plans = run(pm, grid, [site()], overrides=self.PIN)
        # t = 6 RiE units = 12 px north of the gate
        self.assertEqual(new.get(70, 82), 10000 + 2 * 6000)
        self.assertEqual(plans[0].peak, 22000)
        self.assertEqual(max(new.values), 22000)
        self.assertGreater(new.get(70, 82), new.get(70, 78))
        self.assertGreater(new.get(70, 82), new.get(70, 86))

    def test_mirror_flips_the_cone(self):
        def delta(t, l):
            return 3000.0 if 0 < t < 10 and 2 < l < 6 and math.hypot(t, l) < 18 else 0.0
        pm, grid = plain()
        pin = {("c_a", "c_x"): {"mirror": True, "turn": 0, "height": 1.0}}
        new, _ = run(pm, grid, [site()], comp(delta=delta), overrides=pin)
        self.assertEqual(new.get(70 - 8, 70 + 10), 16000)  # l = +4 mirrored to the west of a north-facing gate
        self.assertEqual(new.get(70 + 8, 70 + 10), 10000)

    def test_never_lowered(self):
        pm, grid = plain()
        for x in range(60, 80):
            for y in range(76, 90):
                grid.values[y * 140 + x] = 30000
        new, _ = run(pm, grid, [site()], overrides=self.PIN)
        self.assertEqual(new.get(70, 82), 30000)
        self.assertTrue(all(a >= b for a, b in zip(new.values, grid.values)))

    def test_water_and_province_zero_untouched(self):
        pm, grid = plain()
        for y in range(75, 90):
            pm.ids[y * 140 + 70] = 5  # water
            pm.ids[y * 140 + 71] = 0
        new, _ = run(pm, grid, [site()], water={5}, overrides=self.PIN)
        self.assertEqual(new.get(70, 82), 10000)
        self.assertEqual(new.get(71, 82), 10000)
        self.assertGreater(new.get(69, 82), 10000)

    def test_land_of_any_kind_is_raised(self):
        pm, grid = plain()
        for i in range(len(pm.ids)):
            pm.ids[i] = 9  # impassable-style province: not in the water set
        new, _ = run(pm, grid, [site()], overrides=self.PIN)
        self.assertEqual(new.get(70, 82), 22000)

    def test_fade_at_the_radius(self):
        pm, grid = plain()
        flat = comp(radius=10.0, delta=lambda t, l: 5000.0 if math.hypot(t, l) <= 10 else 0.0)
        new, _ = run(pm, grid, [site()], flat, overrides=self.PIN)
        full = 10000 + 2 * 5000
        self.assertEqual(new.get(70, 70 + 2 * 6), full)  # r = 6 = radius - fade: full weight
        edge = new.get(70, 70 + 2 * 9)  # r = 9: halfway through the fade
        self.assertTrue(10000 < edge < full, edge)
        self.assertEqual(new.get(70, 70 + 2 * 10 + 2), 10000)  # beyond the radius
        self.assertLess(new.get(70, 70 + 19) - 10000, 0.1 * (full - 10000))

    def test_soft_ceiling_applies(self):
        pm, grid = plain(height=60000)
        new, _ = run(pm, grid, [site()], overrides=self.PIN)
        self.assertEqual(new.get(70, 82), dm.soft_ceiling(60000 + 12000))
        self.assertLess(max(new.values), 65536)

    def test_overlapping_gates_do_not_depend_on_input_order(self):
        pm, grid = plain()
        a = dm.GateSite("c_a", "c_x", 70, 70, (0.0, 1.0))
        b = dm.GateSite("c_b", "c_x", 80, 80, (1.0, 0.0))
        pins = {("c_a", "c_x"): {"mirror": False, "turn": 0}, ("c_b", "c_x"): {"mirror": True, "turn": 0}}
        n1, p1 = run(pm, grid, [a, b], overrides=pins)
        n2, p2 = run(pm, grid, [b, a], overrides=pins)
        self.assertEqual(n1.values, n2.values)
        self.assertEqual([p.key for p in p1], [("c_a", "c_x"), ("c_b", "c_x")])
        self.assertEqual([p.objects for p in p1], [p.objects for p in p2])
        # the second gate blends from what the first left: its pixels are the max of both stamps
        only_b, _ = run(pm, grid, [b], overrides={k: v for k, v in pins.items() if k[0] == "c_b"})
        self.assertTrue(all(x >= y for x, y in zip(n1.values, only_b.values)))


class ConeShapeTests(unittest.TestCase):
    """The cone only blends up from the ground; nothing in front of the face or outside the cone moves."""

    PIN = {("c_a", "c_x"): {"mirror": False, "turn": 0, "height": 1.0}}

    def low_ground(self):
        pm, grid = plain(height=5000)
        for y in range(68, 73):  # the gate stands on a 10,000 pad, the lowland around is 5,000
            for x in range(66, 75):
                grid.values[y * 140 + x] = 10000
        return pm, grid

    def test_ground_below_the_foot_is_not_lifted_in_front_or_outside_the_cone(self):
        pm, grid = self.low_ground()
        new, plans = run(pm, grid, [site()], overrides=self.PIN)
        weights = plans[0].weights
        changed = [i for i in range(len(new.values)) if new.values[i] != grid.values[i]]
        self.assertTrue(changed)
        self.assertLessEqual(set(changed), set(weights))
        for i in weights:
            self.assertGreaterEqual(i // 140, 70)  # t >= 0: never south of a north-facing gate
        for i in range(len(new.values)):
            if i // 140 < 70:
                self.assertEqual(new.values[i], grid.values[i])
        # the low ground beside the cone keeps its own height
        self.assertEqual(new.get(70 + 25, 80), 5000)
        self.assertEqual(new.get(70 - 25, 80), 5000)

    def test_face_ramp_starts_at_zero(self):
        c = comp(delta=lambda t, l: 5000.0)  # a delta far above the full threshold everywhere
        self.assertEqual(gt.shape_weight(c, -0.01, 0), 0.0)
        self.assertEqual(gt.shape_weight(c, 0.0, 0), 0.0)
        self.assertAlmostEqual(gt.shape_weight(c, 0.5, 0), 0.5)
        self.assertEqual(gt.shape_weight(c, 1.0, 0), 1.0)
        self.assertEqual(gt.shape_weight(c, 6.0, 0), 1.0)

    def test_weak_delta_does_not_move_ground(self):
        c = comp()
        self.assertEqual(gt.shape_weight(c, 6.0, 5.2), 0.0)  # delta 800 < 0.15 * peak

    def test_river_through_the_cone_makes_no_canyon_walls(self):
        pm, grid = plain()
        for y in range(140):
            for x in (76, 77):
                pm.ids[y * 140 + x] = 5
        new, plans = run(pm, grid, [site()], water={5}, overrides=self.PIN)
        fade = data.TRANSPLANT_WATER_FADE
        rises = []
        for y in range(70, 110):
            for x in range(60, 95):
                if pm.ids[y * 140 + x] == 5:
                    self.assertEqual(new.get(x, y), 10000)
                    continue
                d = min(abs(x - 76), abs(x - 77))
                rise = new.get(x, y) - 10000
                self.assertLessEqual(rise, 12000 * min(1, d / fade) + 1, (x, y))
                if d == 1:
                    rises.append(rise)
        self.assertTrue(max(rises) > 0)
        self.assertLessEqual(max(rises), 12000 / fade + 1)

    def test_pieces_off_the_cone_or_in_front_are_dropped_and_named(self):
        objs = [gt.CompositionObject("mountain_01_mesh", 6.0, 0.0, 0.0, 0.0, 1.0),     # on the peak
                gt.CompositionObject("mountain_04_mesh", -1.0, 0.0, 0.0, 0.0, 1.0),    # in front of the face
                gt.CompositionObject("mountain_05_mesh", 6.0, 7.0, 0.0, 0.0, 1.0),     # beside the cone
                gt.CompositionObject("mountain_06_mesh", 6.0, 1.0, 0.0, 0.0, 1.0)]     # inside it
        pm, grid = plain()
        with no_jitter():
            _, plans = run(pm, grid, [site()], comp(objects=objs), overrides=self.PIN)
        p = plans[0]
        self.assertEqual([o.mesh for o in p.objects], ["mountain_01_mesh", "mountain_06_mesh"])
        self.assertEqual((p.dropped, p.dropped_names), (2, ["mountain_04_mesh", "mountain_05_mesh"]))


class VariationTests(unittest.TestCase):
    def test_same_key_same_result(self):
        pm, grid = plain()
        a = run(pm, grid, [site()])
        b = run(pm, grid, [site()])
        self.assertEqual(a[0].values, b[0].values)
        self.assertEqual(a[1], b[1])

    def test_seed_is_a_stable_hash(self):
        # sha256 of "c_a/c_x", not Python's per-process salted hash()
        self.assertEqual(gt.site_rng(("c_a", "c_x")).random(), gt.site_rng(("c_a", "c_x")).random())
        self.assertNotEqual(gt.site_rng(("c_a", "c_x")).random(), gt.site_rng(("c_b", "c_x")).random())

    def test_different_keys_differ(self):
        pm, grid = plain()
        seen = set()
        for n in range(8):
            _, plans = run(pm, grid, [site(f"c_{n}")])
            o = plans[0].objects[0]
            seen.add((round(o.x, 4), round(o.y, 4), round(o.yaw, 4)))
        self.assertEqual(len(seen), 8)

    def test_mirror_happens_about_half_the_time(self):
        pm, grid = plain()
        mirrored = 0
        for n in range(60):
            _, plans = run(pm, grid, [site(f"c_{n}")])
            mirrored += plans[0].mirror
        self.assertTrue(15 <= mirrored <= 45, mirrored)

    def test_overrides_pin_values(self):
        pm, grid = plain()
        for mirror in (False, True):
            _, plans = run(pm, grid, [site()], overrides={("c_a", "c_x"): {"mirror": mirror, "turn": -7, "height": 1.1}})
            p = plans[0]
            self.assertEqual((p.mirror, p.factor), (mirror, 1.1))
            self.assertAlmostEqual(math.degrees(p.turn), -7)

    def test_bad_overrides_raise(self):
        pm, grid = plain()
        with self.assertRaisesRegex(GeneratorError, "TRANSPLANT_OVERRIDES.*c_nope"):
            run(pm, grid, [site()], overrides={("c_nope", "c_x"): {"mirror": True}})
        with self.assertRaisesRegex(GeneratorError, "turnn"):
            run(pm, grid, [site()], overrides={("c_a", "c_x"): {"turnn": 1}})

    def test_object_on_water_or_province_zero_or_off_map_is_dropped(self):
        pm, grid = plain()
        pin = {("c_a", "c_x"): {"mirror": False, "turn": 0}}
        with no_jitter():
            for ox, oy, other in ((74, 80, 5), (74, 80, 0)):  # the first object lands at (74, 80)
                saved = pm.ids[oy * 140 + ox]
                pm.ids[oy * 140 + ox] = other
                _, plans = run(pm, grid, [site()], water={5}, overrides=pin)
                self.assertEqual((len(plans[0].objects), plans[0].dropped), (1, 1), other)
                self.assertEqual(plans[0].objects[0].mesh, "mountain_02_mesh")
                pm.ids[oy * 140 + ox] = saved
            _, plans = run(pm, grid, [dm.GateSite("c_a", "c_x", 138, 70, (0.0, 1.0))], overrides=pin)
            self.assertEqual(plans[0].dropped, 1)  # x = 142 is off the 140 px map
            self.assertEqual([o.mesh for o in plans[0].objects], ["mountain_02_mesh"])

    def test_dropping_does_not_change_the_other_objects(self):
        pm, grid = plain()
        _, base = run(pm, grid, [site()])
        o = base[0].objects[0]
        pm.ids[round(o.y) * 140 + round(o.x)] = 5
        _, plans = run(pm, grid, [site()], water={5})
        self.assertEqual(plans[0].objects, base[0].objects[1:])


class UphillTests(unittest.TestCase):
    def slope(self, bearing, w=140, h=140):
        """Heights rising toward map bearing `bearing` (radians clockwise from north)."""
        vals = array("H")
        dx, dy = math.sin(bearing), math.cos(bearing)
        for y in range(h):
            for x in range(w):
                vals.append(int(20000 + 50 * ((x - 70) * dx + (y - 70) * dy)))
        return vals, w, h

    def turn(self, bearing, facing=0.0):
        vals, w, h = self.slope(bearing)
        return gt.uphill_turn(vals, w, h, 70, 70, facing, math.radians(25), (4, 30), 20)

    def test_turns_toward_the_gradient(self):
        self.assertAlmostEqual(math.degrees(self.turn(math.radians(10))), 10, places=0)
        self.assertAlmostEqual(math.degrees(self.turn(math.radians(-15))), -15, places=0)

    def test_bounded_by_the_maximum(self):
        self.assertAlmostEqual(math.degrees(self.turn(math.radians(60))), 25, places=6)
        self.assertAlmostEqual(math.degrees(self.turn(math.radians(-120))), -25, places=6)

    def test_relative_to_the_gate_facing(self):
        self.assertAlmostEqual(math.degrees(self.turn(math.radians(100), facing=math.radians(90))), 10, places=0)

    def test_flat_ground_does_not_turn(self):
        vals = array("H", [20000]) * (140 * 140)
        self.assertEqual(gt.uphill_turn(vals, 140, 140, 70, 70, 0.3, 0.4, (4, 30), 20), 0.0)

    def test_transplant_uses_it_and_stays_bounded(self):
        pm, _ = plain()
        vals, w, h = self.slope(math.radians(70))
        _, plans = run(pm, hp.Grid(w, h, vals), [site()], overrides={("c_a", "c_x"): {"mirror": False}})
        self.assertAlmostEqual(math.degrees(plans[0].turn), data.TRANSPLANT_MAX_TURN, places=6)


class HeightFactorTests(unittest.TestCase):
    def test_default_is_one_when_the_cone_already_clears(self):
        self.assertEqual(gt.height_factor(10000, 30000, 12000), 1.0)

    def test_raised_to_clear_the_terrain_by_the_margin(self):
        # needs foot + 30000 * f >= 41000 + 2000  ->  f = 1.1
        self.assertAlmostEqual(gt.height_factor(10000, 30000, 41000), 1.0 + 0.1, places=9)

    def test_clamped(self):
        self.assertEqual(gt.height_factor(10000, 30000, 90000), data.TRANSPLANT_HEIGHT_MAX)
        self.assertEqual(gt.clamp_factor(0.5), data.TRANSPLANT_HEIGHT_MIN)

    def test_site_factor_uses_the_terrain_in_the_footprint(self):
        pm, grid = plain()
        grid.values[82 * 140 + 70] = 10000 + 2 * 6000 + 1000  # a bump taller than the cone, in the footprint
        _, plans = run(pm, grid, [site()], overrides={("c_a", "c_x"): {"mirror": False, "turn": 0}})
        self.assertGreater(plans[0].factor, 1.0)
        self.assertLessEqual(plans[0].factor, data.TRANSPLANT_HEIGHT_MAX)
        _, plans = run(*plain(), [site()], overrides={("c_a", "c_x"): {"mirror": False, "turn": 0}})
        self.assertAlmostEqual(plans[0].factor, 1.0, delta=data.TRANSPLANT_HEIGHT_JITTER + 1e-9)

    def test_jitter_stays_inside_the_clamp(self):
        pm, grid = plain(height=10000)
        for n in range(30):
            _, plans = run(pm, grid, [site(f"c_{n}")])
            self.assertTrue(data.TRANSPLANT_HEIGHT_MIN <= plans[0].factor <= data.TRANSPLANT_HEIGHT_MAX)


class ParseTests(unittest.TestCase):
    TEXT = ('object={\n\tname="a"\n\tpdxmesh="m_mesh"\n\tcount=2\n\ttransform="1 2 3 0 0 0 1 1 1 1\n'
            '4 5 6 0 0.5 0 0.866 2 2 2 # note\n"}\n'
            'object={\n\tname="b"\n\tentity="waterfall"\n\tcount=1\n\ttransform="7 8 9 0 0 0 1 1 1 1\n"}\n'
            'object={\n\tname="c"\n\tpdxmesh="no_transform_mesh"\n\tcount=0\n}\n')

    def test_parse_map_objects(self):
        found = gt.parse_map_objects(self.TEXT)
        self.assertEqual([(m, e, len(r)) for m, e, r in found], [("m_mesh", None, 2), (None, "waterfall", 1)])
        self.assertEqual(found[0][2][1][:3], [4.0, 5.0, 6.0])

    def test_yaw_of(self):
        self.assertAlmostEqual(gt.yaw_of([0, 0, 0, 0, 0.5, 0, math.sqrt(0.75), 1, 1, 1]), math.pi / 3)
        with self.assertRaises(GeneratorError):
            gt.yaw_of([0, 0, 0, 0.5, 0, 0, 0.8, 1, 1, 1])

    def test_wrap(self):
        self.assertAlmostEqual(gt.wrap(3 * math.pi / 2), -math.pi / 2)
        self.assertAlmostEqual(gt.wrap(-3 * math.pi / 2), math.pi / 2)
        self.assertAlmostEqual(gt.wrap(math.pi), math.pi)


# Erebor's mountain pieces relative to its gate (the brief's table without the waterfall substitutes, which are gone): mesh, t, l, y, yaw degrees, scale.
EREBOR = [
    ("mountain_01_mesh", 6.05, 0.79, 0.0, 40.7, 1.0),
    ("mountain_02_mesh", 7.24, 2.68, 0.0, -31.4, 1.0),
    ("mountain_03_mesh", 3.70, -3.79, 0.0, 45.2, 1.0),
    ("mountain_03_mesh", 2.96, -0.13, 0.0, 178.9, 0.701),
    ("mountain_04_mesh", -0.99, -7.79, 0.0, 138.0, 1.0),
    ("mountain_04_mesh", 12.91, -3.74, 0.0, 62.3, 1.0),
    ("mountain_05_mesh", 0.44, 7.40, 0.0, 7.3, 1.0),
    ("mountain_05_mesh", 6.38, -9.69, 0.0, -13.3, 1.0),
    ("mountain_05_mesh", 6.90, 10.22, 0.0, -10.7, 0.628),
    ("mountain_06_mesh", 13.36, 5.27, 0.0, -101.1, 1.0),
]


@unittest.skipUnless((RIE / "map_data/heightmap.png").is_file(), "Realms in Exile is not installed")
class ExtractionRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.comp = gt.load_composition(RIE)

    def test_the_thirteen_objects(self):
        self.assertEqual(len(self.comp.objects), 10)
        for want in EREBOR:
            hits = [o for o in self.comp.objects if o.mesh == want[0] and abs(o.t - want[1]) < 0.05
                    and abs(o.l - want[2]) < 0.05]
            self.assertEqual(len(hits), 1, want)
            o = hits[0]
            self.assertAlmostEqual(o.y, want[3], delta=0.01)
            self.assertAlmostEqual(math.degrees(o.yaw), want[4], delta=0.2)
            self.assertAlmostEqual(o.scale, want[5], delta=0.001)

    def test_gate_and_neighbouring_buildings_are_excluded(self):
        names = {o.mesh for o in self.comp.objects}
        self.assertEqual(names, {"mountain_01_mesh", "mountain_02_mesh", "mountain_03_mesh", "mountain_04_mesh",
                                 "mountain_05_mesh", "mountain_06_mesh"})

    def test_cone_profile_along_the_inward_axis(self):
        for t, want in ((0, 0), (2, 10536), (4, 11261), (6, 14087), (10, 7452), (14, 514)):
            self.assertAlmostEqual(self.comp.delta(t, 0), want, delta=800 if t else 600, msg=str(t))
        self.assertAlmostEqual(self.comp.peak, 14601, delta=700)
        self.assertEqual(self.comp.radius, data.TRANSPLANT_RADIUS)

    def test_cone_is_narrow_and_zero_outside_the_radius(self):
        self.assertLess(self.comp.delta(6, 8), 0.4 * self.comp.delta(6, 0))
        self.assertEqual(self.comp.delta(data.TRANSPLANT_RADIUS, 1), 0.0)

    def test_load_is_cached(self):
        self.assertIs(gt.load_composition(RIE), self.comp)


if __name__ == "__main__":
    unittest.main()
