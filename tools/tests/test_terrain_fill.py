import struct
import sys
import unittest
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import terrain_fill as tf  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402

ANB_TERRAIN = Path(__file__).resolve().parents[2].parent / "anbennar-ck3-dev-master" / "gfx/map/terrain"
FOOTER = b"\0" * 8 + b"TRUEVISION-XFILE.\0"


def tga(width, height, pixels, descriptor=0x08):
    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, width, height, 32, descriptor)
    return header + bytes(pixels) + FOOTER


def grid(width, height, painted):
    """Index and intensity images: pixel value v for painted cells (index (v, v+1, 0, 0), weights (200, 55, 0, 0)),
    nothing elsewhere. `painted` maps (x, y) -> v; y counts from the bottom row like the file."""
    index = bytearray(width * height * 4)
    intensity = bytearray(width * height * 4)
    for (x, y), v in painted.items():
        o = (y * width + x) * 4
        index[o:o + 4] = bytes((v, v + 1, 0, 0))
        intensity[o:o + 4] = bytes((200, 55, 0, 0))
    return tga(width, height, index), tga(width, height, intensity)


def unpainted(intensity_img):
    weights = array("I", intensity_img.pixels)
    return [i for i, w in enumerate(weights) if not w]


class TgaTests(unittest.TestCase):
    def test_round_trip_keeps_header_and_footer(self):
        data = tga(3, 2, range(24))
        img = tf.read_tga(data)
        self.assertEqual((img.width, img.height), (3, 2))
        self.assertEqual(tf.write_tga(img), data)

    def test_rejects_other_formats(self):
        with self.assertRaises(GeneratorError):
            tf.read_tga(tga(2, 2, bytes(16))[:2] + b"\x0a" + tga(2, 2, bytes(16))[3:])  # RLE type 10
        with self.assertRaises(GeneratorError):
            tf.read_tga(tga(2, 2, bytes(16), descriptor=0x28))  # top-left origin
        with self.assertRaises(GeneratorError):
            tf.read_tga(tga(2, 2, bytes(8))[:18 + 8])  # truncated pixels, no footer


class FillTests(unittest.TestCase):
    W, H = 12, 6

    def build(self, holes, large=6):
        painted = {(x, y): 10 + x for y in range(self.H) for x in range(self.W) if (x, y) not in holes}
        index, intensity = grid(self.W, self.H, painted)
        return tf.read_tga(index), tf.read_tga(intensity), tf.fill_unpainted(
            tf.read_tga(index), tf.read_tga(intensity), fill_material=42, large=large)

    def test_no_unpainted_pixel_left(self):
        small = {(2, 2), (3, 2)}
        big = {(x, y) for x in range(7, 10) for y in range(1, 4)}  # 9 pixels >= large
        _, _, (index, intensity, report) = self.build(small | big)
        self.assertEqual(unpainted(intensity), [])
        self.assertEqual(report, {"small_groups": 1, "small_pixels": 2, "large_groups": 1, "large_pixels": 9})

    def test_painted_pixels_unchanged(self):
        holes = {(2, 2), (3, 2)} | {(x, y) for x in range(7, 10) for y in range(1, 4)}
        index0, intensity0, (index, intensity, _) = self.build(holes)
        for y in range(self.H):
            for x in range(self.W):
                if (x, y) in holes:
                    continue
                o = (y * self.W + x) * 4
                self.assertEqual(index.pixels[o:o + 4], index0.pixels[o:o + 4])
                self.assertEqual(intensity.pixels[o:o + 4], intensity0.pixels[o:o + 4])

    def test_small_gap_copies_a_painted_neighbour(self):
        _, _, (index, intensity, _) = self.build({(2, 2), (3, 2)})
        for x in (2, 3):
            o = (2 * self.W + x) * 4
            self.assertIn(index.pixels[o], (11, 12, 13, 14))  # a material of a 4-neighbour (column value 10 + x)
            self.assertEqual(index.pixels[o + 1], index.pixels[o] + 1)  # the whole pixel is copied
            self.assertEqual(bytes(intensity.pixels[o:o + 4]), bytes((200, 55, 0, 0)))

    def test_large_gap_gets_the_fill_material(self):
        big = {(x, y) for x in range(7, 10) for y in range(1, 4)}
        _, _, (index, intensity, _) = self.build(big)
        for x, y in big:
            o = (y * self.W + x) * 4
            self.assertEqual(bytes(index.pixels[o:o + 4]), bytes((42, 0, 0, 0)))
            self.assertEqual(bytes(intensity.pixels[o:o + 4]), bytes((255, 0, 0, 0)))

    def test_deterministic(self):
        holes = {(2, 2), (3, 2), (5, 5)}
        _, _, first = self.build(holes)
        _, _, second = self.build(holes)
        self.assertEqual(first[0].pixels, second[0].pixels)
        self.assertEqual(first[1].pixels, second[1].pixels)

    def test_size_mismatch_raises(self):
        index, intensity = grid(4, 4, {})
        other, _ = grid(4, 3, {})
        with self.assertRaises(GeneratorError):
            tf.fill_unpainted(tf.read_tga(other), tf.read_tga(intensity), fill_material=1, large=10)


@unittest.skipUnless((ANB_TERRAIN / "detail_intensity.tga").is_file(), "needs Anbennar")
class RealDataTests(unittest.TestCase):
    result = None

    @classmethod
    def setUpClass(cls):
        cls.index0 = tf.read_tga((ANB_TERRAIN / "detail_index.tga").read_bytes())
        cls.intensity0 = tf.read_tga((ANB_TERRAIN / "detail_intensity.tga").read_bytes())
        cls.result = tf.fill_unpainted(tf.read_tga((ANB_TERRAIN / "detail_index.tga").read_bytes()),
                                       tf.read_tga((ANB_TERRAIN / "detail_intensity.tga").read_bytes()),
                                       fill_material=40, large=1000)

    def test_anbennar_has_gaps_and_none_remain(self):
        self.assertGreater(len(unpainted(self.intensity0)), 400000)
        self.assertEqual(unpainted(self.result[1]), [])

    def test_only_unpainted_pixels_change(self):
        before = array("I", self.intensity0.pixels)
        index_before = array("I", self.index0.pixels)
        index_after = array("I", self.result[0].pixels)
        intensity_after = array("I", self.result[1].pixels)
        for i, w in enumerate(before):
            if w:
                self.assertEqual(intensity_after[i], w)
                self.assertEqual(index_after[i], index_before[i])

    def test_report_counts(self):
        report = self.result[2]
        self.assertEqual(report["small_pixels"] + report["large_pixels"], len(unpainted(self.intensity0)))
        self.assertGreaterEqual(report["large_pixels"], 390000)  # impassable province 2426's block


if __name__ == "__main__":
    unittest.main()
