import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import eu4_import as eu4i  # noqa: E402
import surround_mask as sm  # noqa: E402


def dds(width: int, height: int, bgr: tuple) -> bytes:
    """A DXT5 DDS of one flat colour (alpha 255)."""
    header = bytearray(128)
    header[:4] = b"DDS "
    struct.pack_into("<IIII", header, 4, 124, 0x1007, height, width)
    header[84:88] = b"DXT5"
    block = bytes((255, 255, 0, 0, 0, 0, 0, 0)) + sm.colour_block([bgr] * 16)
    return bytes(header) + block * (width // 4 * height // 4)


class FogCapTests(unittest.TestCase):
    def test_cap_rises_from_reveal_to_reveal_plus_fade(self):
        self.assertEqual(sm.fog_cap(0, 20, 40), 0)
        self.assertEqual(sm.fog_cap(20, 20, 40), 0)
        self.assertEqual(sm.fog_cap(40, 20, 40), 128)
        self.assertEqual(sm.fog_cap(60, 20, 40), 255)
        self.assertEqual(sm.fog_cap(500, 20, 40), 255)


class DistanceTests(unittest.TestCase):
    def test_chamfer_close_to_euclidean(self):
        d = sm.distances({(0, 0)}, (0, 0, 30, 30))
        self.assertEqual(d[(0, 0)], 0)
        self.assertAlmostEqual(d[(20, 0)], 20, delta=0.01)
        self.assertAlmostEqual(d[(20, 20)], 20 * 2 ** 0.5, delta=20 * 2 ** 0.5 * 0.08)


class RangeTests(unittest.TestCase):
    def test_only_high_ground_joined_to_visible_high_ground(self):
        # columns 0-2 high and visible, 3 low, 4-5 high but cut off behind the low column; 6-7 high, joined via row 5
        def height(x, y):
            if x == 3 and y < 5:
                return 10
            return 100 if x != 3 or y == 5 else 10

        def fog(x, y):
            return 0 if x < 2 else 255

        box = (0, 0, 8, 6)
        got = sm.range_pixels(height, fog, box, threshold=50)
        self.assertIn((0, 0), got)
        self.assertIn((3, 5), got)
        self.assertIn((7, 0), got)  # reached around through row 5
        lonely = sm.range_pixels(lambda x, y: 100 if x != 3 else 10, fog, box, threshold=50)
        self.assertNotIn((5, 0), lonely)
        self.assertIn((2, 0), lonely)


class PushBackTests(unittest.TestCase):
    def test_lowers_fog_near_range_and_never_raises_it(self):
        w = 40
        px = bytearray()
        for y in range(4):
            for x in range(w):
                fog = 0 if x < 5 else 255
                px += bytes((fog if x > 30 else 0, fog, fog, 255))
        changed = sm.push_back(px, w, {(x, y) for x in range(0, 4) for y in range(4)}, (0, 0, w, 4), reveal=5, fade=10)
        at = lambda x, c: px[(1 * w + x) * 4 + c]  # noqa: E731
        self.assertEqual(at(6, 2), 0)  # within reveal of the range
        self.assertEqual(at(25, 2), 255)  # far away
        self.assertTrue(0 < at(12, 2) < 255)
        self.assertEqual(at(6, 0), 0)
        self.assertIn((6, 1), changed)
        self.assertNotIn((2, 1), changed)  # was clear already


    def test_box_edges_feather_back_to_the_original_fog(self):
        w = 60
        px = bytearray(bytes((255, 255, 255, 255)) * w * w)
        ridge = {(x, y) for x in range(w) for y in range(w)}
        sm.push_back(px, w, ridge, (0, 0, w, w), reveal=5, fade=10, feather=20)
        at = lambda x: px[(30 * w + x) * 4 + 2]  # noqa: E731
        self.assertEqual(at(30), 0)  # middle of the box: fully cleared
        self.assertEqual(at(0), 255)  # on the box edge: Anbennar's fog
        self.assertEqual(at(w - 1), 255)
        self.assertTrue(0 < at(10) < 255)


class EncodeTests(unittest.TestCase):
    def test_patch_reencodes_only_changed_blocks(self):
        data = dds(8, 8, (0, 255, 255))
        w, h, px = eu4i.read_dds(data)
        px = bytearray(px)
        for y in range(4):
            for x in range(4):
                i = (y * 8 + x) * 4
                fade = 85 * x  # a fog edge: the channels fade together, as in the mask
                px[i:i + 3] = bytes((0, fade, min(255, fade + 40)))
        out = sm.patch_dxt5(data, px, {(1, 1)})
        self.assertEqual(out[:128], data[:128])
        self.assertEqual(out[128 + 16:], data[128 + 16:])
        self.assertEqual(out[128:136], data[128:136])  # alpha half kept
        _, _, back = eu4i.read_dds(out)
        self.assertLessEqual(sm.max_error(back[:4 * 4], px[:4 * 4]), 48)

    def test_encode_never_adds_fog(self):
        import random
        rng = random.Random(7)
        for _ in range(300):
            texels = []
            for _ in range(16):
                v = rng.randrange(256)
                texels.append((rng.randrange(v + 1), v, min(255, v + rng.randrange(60))))
            data = dds(4, 4, (0, 0, 0))
            px = bytearray(b"".join(bytes(t + (255,)) for t in texels))
            _, _, back = eu4i.read_dds(sm.patch_dxt5(data, px, {(0, 0)}))
            over = [(back[i], px[i]) for i in range(64) if i % 4 != 3 and back[i] > px[i]]
            self.assertEqual(over, [], texels)

    def test_flat_block_round_trips(self):
        for bgr in ((0, 0, 0), (255, 255, 255), (0, 255, 255), (0, 128, 200)):
            data = dds(4, 4, bgr)
            _, _, px = eu4i.read_dds(data)
            self.assertLessEqual(sm.max_error(px, bytes(bgr + (255,)) * 16), 4, bgr)


if __name__ == "__main__":
    unittest.main()
