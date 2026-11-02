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


if __name__ == "__main__":
    unittest.main()
