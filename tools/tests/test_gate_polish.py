"""Transplant polish: range join, gate apron and mountain-piece keep-out (spec addendum 2026-10-15)."""

import math
import struct
import sys
import unittest
from array import array
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dwarven_mountains as dm  # noqa: E402
import gate_transplant as gt  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import map_graphics as data  # noqa: E402
from test_gate_transplant import K2, RIE, comp, no_jitter, plain, run, site  # noqa: E402

PIN0 = {("c_a", "c_x"): {"mirror": False, "turn": 0, "height": 1.0}}
G = 10000  # the foot of the fixtures below; the cone (tent peak 6000, k = 2) peaks at 22000


def set_rect(grid, x0, x1, y0, y1, value, w=140):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            grid.values[y * w + x] = value


class RangeJoinTests(unittest.TestCase):
    """A ridge behind the cone is scaled up from the foot so its highest point reaches the cone's peak."""

    def ridge(self, height, x0=92, x1=95, y0=72, y1=85, slope=None):
        pm, grid = plain()
        set_rect(grid, x0, x1, y0, y1, height)
        if slope:
            set_rect(grid, x0 - 1, x0 - 1, y0, y1, slope)
        return pm, grid

    def test_ridge_reaches_the_cone_peak_and_keeps_its_shape(self):
        pm, grid = self.ridge(16000, slope=13000)
        new, plans = run(pm, grid, [site()], overrides=PIN0)
        p = plans[0]
        self.assertEqual(p.peak, 22000)
        self.assertEqual((p.join_before, p.join_after), (16000, 22000))
        self.assertAlmostEqual(p.join_scale, 2.0, places=3)
        self.assertEqual(new.get(93, 80), 22000)
        self.assertEqual(new.get(91, 80), G + 2 * 3000)  # (cur - foot) scaled by the same factor
        self.assertEqual(new.get(100, 80), G)  # flat ground at the foot stays
        ratio = (new.get(91, 80) - G) / (new.get(93, 80) - G)
        self.assertAlmostEqual(ratio, 3000 / 6000, places=3)

    def test_scale_is_clamped_to_the_maximum(self):
        pm, grid = self.ridge(11000)
        new, plans = run(pm, grid, [site()], overrides=PIN0)
        self.assertAlmostEqual(plans[0].join_scale, data.RANGE_JOIN_MAX)
        self.assertEqual(new.get(93, 80), G + 2 * 1000)

    def test_a_range_already_at_the_peak_is_left_alone(self):
        pm, grid = self.ridge(23000)
        new, plans = run(pm, grid, [site()], overrides=PIN0)
        self.assertEqual(plans[0].join_scale, 1.0)
        self.assertEqual(new.get(93, 80), 23000)
        self.assertEqual((plans[0].join_before, plans[0].join_after), (23000, 23000))

    def test_cone_and_front_unchanged_by_the_join(self):
        pm, grid = self.ridge(16000)
        joined, plans = run(pm, grid, [site()], overrides=PIN0)
        with mock.patch.object(data, "RANGE_JOIN_MAX", 1.0):
            plain_, _ = run(pm, grid, [site()], overrides=PIN0)
        core = {i for i, c in plans[0].weights.items() if c >= data.RANGE_JOIN_CORE}
        self.assertTrue(core)
        for i in core:
            self.assertEqual(joined.values[i], plain_.values[i])
        for i in range(len(joined.values)):
            if i // 140 < 70:  # south of a north-facing gate
                self.assertEqual(joined.values[i], plain_.values[i])
        self.assertNotEqual(joined.get(93, 80), plain_.get(93, 80))

    def test_never_lowered(self):
        pm, grid = self.ridge(16000)
        new, _ = run(pm, grid, [site()], overrides=PIN0)
        self.assertTrue(all(a >= b for a, b in zip(new.values, grid.values)))

    def test_water_untouched_and_faded_beside_it(self):
        pm, grid = self.ridge(16000, x0=92, x1=99)
        for y in range(72, 86):
            pm.ids[y * 140 + 99] = 5
        new, _ = run(pm, grid, [site()], water={5}, overrides=PIN0)
        self.assertEqual(new.get(99, 80), 16000)
        self.assertEqual(new.get(98, 80), G + 6000 + int(round(6000 / data.TRANSPLANT_WATER_FADE)))
        self.assertEqual(new.get(93, 80), 22000)

    def test_only_range_provinces_join(self):
        pm, grid = self.ridge(16000)
        for y in range(72, 86):
            for x in range(92, 96):
                pm.ids[y * 140 + x] = 9
        new, _ = run(pm, grid, [site()], overrides=PIN0, ranges={2})
        self.assertEqual(new.get(93, 80), 16000)
        new, _ = run(pm, grid, [site()], overrides=PIN0, ranges={9})
        self.assertEqual(new.get(93, 80), 22000)

    def test_fades_out_to_the_radius(self):
        full, rad = data.RANGE_JOIN_FULL, data.RANGE_JOIN_RADIUS
        pm, grid = plain(w=200, h=200)
        near = (full + rad) // 2
        set_rect(grid, 70 + near, 70 + near, 72, 74, 16000, w=200)
        set_rect(grid, 70 + rad + 2, 70 + rad + 2, 72, 74, 16000, w=200)
        s = dm.GateSite("c_a", "c_x", 70, 70, (0.0, 1.0))
        new, plans = run(pm, grid, [s], overrides=PIN0)
        d = math.hypot(near, 73 - 70)
        wgt = 0.5 + 0.5 * math.cos(math.pi * (d - full) / (rad - full))
        want = G + 6000 * (1 + (plans[0].join_scale - 1) * wgt)
        self.assertAlmostEqual(new.get(70 + near, 73), want, delta=2)
        self.assertEqual(new.get(70 + rad + 2, 73), 16000)

    def test_the_scale_is_solved_for_the_faded_height_not_a_far_maximum(self):
        """The highest pixel stands in the fade (weight 0.5); s is raised so the scaled range still reaches the peak."""
        pm, grid = plain(w=200, h=200)
        set_rect(grid, 70 + 45, 70 + 45, 72, 74, 18000, w=200)
        set_rect(grid, 92, 95, 72, 85, 17000, w=200)  # a nearer, lower ridge at full weight
        new, plans = run(pm, grid, [dm.GateSite("c_a", "c_x", 70, 70, (0.0, 1.0))], overrides=PIN0)
        self.assertEqual(plans[0].join_before, 18000)
        self.assertGreater(plans[0].join_scale, 1.7)  # 12000 / 7000; a plain (peak - g) / (m - g) gives 1.5
        self.assertEqual(plans[0].join_after, 22000)
        self.assertEqual(max(new.values), 22000)

    def test_gates_join_in_key_order_whatever_the_input_order(self):
        pm, grid = self.ridge(16000)
        a = dm.GateSite("c_a", "c_x", 70, 70, (0.0, 1.0))
        b = dm.GateSite("c_b", "c_x", 60, 70, (0.0, 1.0))
        pins = {("c_a", "c_x"): PIN0[("c_a", "c_x")], ("c_b", "c_x"): PIN0[("c_a", "c_x")]}
        n1, _ = run(pm, grid, [a, b], overrides=pins)
        n2, _ = run(pm, grid, [b, a], overrides=pins)
        self.assertEqual(n1.values, n2.values)


class ApronTests(unittest.TestCase):
    """The gate's footprint and a front apron are raised to the foot, blending out over GATE_APRON_FADE px."""

    def lowland(self):
        pm, grid = plain(height=8000)
        set_rect(grid, 69, 71, 69, 71, G)  # the pad under the gate pixel: the foot is 10000
        return pm, grid

    def test_front_and_footprint_raised_to_the_foot_never_lowered(self):
        pm, grid = self.lowland()
        set_rect(grid, 66, 68, 66, 66, 12000)
        new, plans = run(pm, grid, [site()], overrides=PIN0)
        self.assertEqual(plans[0].foot, G)
        self.assertEqual(new.get(70, 67), G)  # t = -3, inside the apron (3.5)
        self.assertEqual(new.get(76, 68), G)  # |l| = 6 <= half width 5.5 + 1
        self.assertGreaterEqual(new.get(70, 74), G)  # t = 4 <= depth 4.57 (the cone may add to it)
        self.assertEqual(new.get(67, 66), 12000)
        self.assertGreater(plans[0].apron_raised, 50)
        # beyond the blend nothing moves
        self.assertEqual(new.get(70, 60), 8000)
        self.assertEqual(new.get(84, 70), 8000)
        # the blend is monotone from the foot down to the ground, with no wall
        row = [new.get(x, 70) for x in range(70 + 6, 70 + 12)]
        self.assertEqual(row, sorted(row, reverse=True))
        col = [new.get(70, y) for y in range(60, 68)]
        self.assertEqual(col, sorted(col))
        self.assertLessEqual(max(b - a for a, b in zip(col, col[1:])), 1400)

    def test_water_untouched(self):
        pm, grid = self.lowland()
        for y in range(60, 76):
            pm.ids[y * 140 + 72] = 5
            pm.ids[y * 140 + 73] = 0
        new, _ = run(pm, grid, [site()], water={5}, overrides=PIN0)
        for y in range(60, 76):
            self.assertEqual(new.get(72, y), 8000)
            self.assertEqual(new.get(73, y), 8000)

    def test_uses_the_gate_frame_not_the_turn(self):
        pm, grid = self.lowland()
        east = dm.GateSite("c_a", "c_x", 70, 70, (1.0, 0.0))
        pin = {("c_a", "c_x"): {"mirror": False, "turn": 25, "height": 1.0}}
        new, _ = run(pm, grid, [east], overrides=pin)
        self.assertEqual(new.get(67, 70), G)  # t = -3 along east
        self.assertEqual(new.get(73, 76), G)  # t 3, l -6: inside the gate's rectangle, outside the turned one
        self.assertEqual(new.get(70, 80), 8000)  # |l| = 10, beyond the width and the blend

    def test_flat_foot_raises_nothing(self):
        pm, grid = plain()
        _, plans = run(pm, grid, [site()], overrides=PIN0)
        self.assertEqual(plans[0].apron_raised, 0)


def bounds(half=2.0):
    return {"mountain_01_mesh": (-half, -half, half, half)}


class PieceKeepOutTests(unittest.TestCase):
    def one(self, piece, delta=None, half=2.0):
        pm, grid = plain()
        c = comp(objects=[piece], delta=delta)
        with no_jitter():
            return gt.transplant(grid, pm, set(), [(site(), K2, (70, 70))], c, PIN0,
                                 piece_bounds=bounds(half))[1][0]

    def test_overlapping_piece_is_pushed_back_clear_and_named(self):
        p = self.one(gt.CompositionObject("mountain_01_mesh", 2.0, 0.0, 0.0, 0.0, 1.0))
        self.assertEqual(p.pushed_names, ["mountain_01_mesh"])
        self.assertEqual(len(p.objects), 1)
        o = p.objects[0]
        self.assertAlmostEqual(o.x, 70.0)
        self.assertGreater(o.y, 74.0)
        self.assertLessEqual(o.y - 74.0, data.PIECE_MAX_PUSH)
        box = bounds()["mountain_01_mesh"]
        self.assertFalse(gt.overlaps_keep_out(p, o, box))
        back = gt.PlacedObject(o.mesh, o.x, o.y - 0.5, o.y_offset, o.yaw, o.scale)
        self.assertTrue(gt.overlaps_keep_out(p, back, box))  # pushed no further than needed

    def test_clear_piece_is_not_moved(self):
        p = self.one(gt.CompositionObject("mountain_01_mesh", 7.0, 0.0, 0.0, 0.0, 1.0))
        self.assertEqual(p.pushed_names, [])
        self.assertAlmostEqual(p.objects[0].y, 70 + 14.0)

    def test_piece_that_cannot_clear_within_the_limit_is_dropped(self):
        p = self.one(gt.CompositionObject("mountain_01_mesh", 4.0, 0.0, 0.0, 0.0, 1.0), half=12.0)
        self.assertEqual(p.objects, [])
        self.assertEqual(p.dropped_names, ["mountain_01_mesh"])
        self.assertEqual(p.dropped, 1)

    def test_pushed_piece_is_filtered_again(self):
        def delta(t, l):
            return 3000.0 if 0 < t < 5 and abs(l) < 8 else 0.0
        p = self.one(gt.CompositionObject("mountain_01_mesh", 3.0, 0.0, 0.0, 0.0, 1.0), delta=delta)
        self.assertEqual(p.objects, [])
        self.assertEqual(p.dropped_names, ["mountain_01_mesh"])

    def test_missing_bounds_raise(self):
        pm, grid = plain()
        c = comp(objects=[gt.CompositionObject("mountain_09_mesh", 6.0, 0.0, 0.0, 0.0, 1.0)])
        with self.assertRaises(GeneratorError):
            gt.transplant(grid, pm, set(), [(site(), K2, (70, 70))], c, PIN0, piece_bounds=bounds())

    def test_rotated_footprint(self):
        plan = gt.GatePlan(("a", "b"), 70, 70, 2.0, False, 0.0, 1.0, G, size=K2, yaw=0.0, gate_yaw=0.0)
        o = gt.PlacedObject("mountain_01_mesh", 70, 80, 0, math.pi / 4, 1.0)
        self.assertFalse(gt.overlaps_keep_out(plan, o, (-2, -2, 2, 2)))
        o = gt.PlacedObject("mountain_01_mesh", 70, 76, 0, math.pi / 4, 1.0)
        self.assertTrue(gt.overlaps_keep_out(plan, o, (-2, -2, 2, 2)))


class MeshBoundsTests(unittest.TestCase):
    def test_reads_min_and_max(self):
        blob = (b"junk!\x03minf\x03\x00\x00\x00" + struct.pack("<3f", -1, -2, -3) + b"!\x03maxf\x03\x00\x00\x00"
                + struct.pack("<3f", 4, 5, 6) + b"tail")
        self.assertEqual(gt.mesh_bounds(blob), ((-1.0, -2.0, -3.0), (4.0, 5.0, 6.0)))

    def test_missing_raises(self):
        with self.assertRaises(GeneratorError):
            gt.mesh_bounds(b"nothing")

    @unittest.skipUnless((RIE / "gfx/models/mapitems/mountains/mountain_01/mountain_01.mesh").is_file(),
                         "Realms in Exile is not installed")
    def test_real_mesh(self):
        blob = (RIE / "gfx/models/mapitems/mountains/mountain_01/mountain_01.mesh").read_bytes()
        lo, hi = gt.mesh_bounds(blob)
        self.assertAlmostEqual(lo[0], -6.71, delta=0.05)
        self.assertAlmostEqual(hi[0], 7.07, delta=0.05)
        self.assertLess(lo[1], hi[1])
        self.assertLess(lo[2], hi[2])


if __name__ == "__main__":
    unittest.main()
