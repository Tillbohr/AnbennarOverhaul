"""Tests for tools/build_magic_lifestyle_art.py.

    python -I -m unittest discover -s tools/tests -v
"""

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import build_magic_lifestyle_art as art  # noqa: E402
import build_spells as bs  # noqa: E402

EU4 = art.DEFAULT_EU4
GAME = art.DEFAULT_GAME


class ArtTests(unittest.TestCase):
    def test_resize_keeps_flat_colour(self):
        px = bytes([10, 20, 30, 255]) * 4
        out = art.resize(px, 2, 2, 5, 3)
        self.assertEqual(len(out), 5 * 3 * 4)
        self.assertEqual(set(out[i:i + 4] for i in range(0, len(out), 4)), {bytes([10, 20, 30, 255])})

    def test_tint_keeps_alpha(self):
        out = art.tint(bytes([255, 255, 255, 77]), (200, 190, 40))
        self.assertEqual(out, bytes([200, 190, 40, 77]))

    def test_over_respects_alpha(self):
        dst = bytearray(bytes([0, 0, 0, 255]))
        art.over(dst, 1, bytes([255, 255, 255, 0]), 1, 1, 0, 0)
        self.assertEqual(bytes(dst), bytes([0, 0, 0, 255]))

    def test_crop(self):
        px = bytes(range(16)) * 1  # 2 x 2 pixels... as 4x1 px of 4 bytes
        self.assertEqual(art.crop(px, 4, 1, 0, 2, 1), px[4:12])

    @unittest.skipUnless(EU4.is_dir() and GAME.is_dir(), "needs EU4 Anbennar and CK3 installed")
    def test_outputs_have_declared_sizes(self):
        files = art.build_all(EU4, GAME)
        self.assertEqual(set(files), set(art.OUTPUTS))
        for path, data in files.items():
            w, h, px = bs.read_bgra(data)
            self.assertEqual((w, h), art.OUTPUTS[path], path)
            self.assertEqual(len(px), w * h * 4)


if __name__ == "__main__":
    unittest.main()
