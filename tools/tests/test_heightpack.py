import random
import struct
import sys
import unittest
import zlib
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import heightpack as hp  # noqa: E402
import pngio  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402

ANBENNAR_MAP = Path(__file__).resolve().parents[2].parent / "anbennar-ck3-dev-master" / "map_data"
LIVE = (ANBENNAR_MAP / "packed_heightmap.png").is_file()

ANBENNAR_SETTINGS = (
    "﻿heightmap_file=\"map_data/packed_heightmap.png\"\n"
    "indirection_file=\"map_data/indirection_heightmap.png\"\n"
    "original_heightmap_size={ 8192 4096 }\n"
    "tile_size=33\n"
    "should_wrap_x=no\n"
    "level_offsets={ { 0 0 } { 0 2788 } { 0 3646 } { 0 3776 } { 0 3813 } }\n"
    "max_compress_level=4\n"
    "empty_tile_offset={ 243 77 }\n"
)


def small_settings(width, height):
    """Settings for a small test map; the offsets are placeholders that pack() replaces."""
    text = ANBENNAR_SETTINGS.replace("{ 8192 4096 }", f"{{ {width} {height} }}")
    return hp.parse_settings(text)


# --- an independent PNG encoder (the filter equations of the PNG spec, encode direction) ---

def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _filter_row(ftype, row, prev, bpp):
    out = bytearray()
    for i, x in enumerate(row):
        a = row[i - bpp] if i >= bpp else 0
        b = prev[i]
        c = prev[i - bpp] if i >= bpp else 0
        pred = (0, a, b, (a + b) // 2, _paeth(a, b, c))[ftype]
        out.append((x - pred) & 255)
    return bytes(out)


def _chunk(typ, body):
    return struct.pack(">I", len(body)) + typ + body + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF)


def encode_fixture(width, height, bit_depth, color_type, pixels, interlace=0):
    """PNG whose row y uses filter y % 5, with a pHYs chunk and the data split over two IDATs."""
    channels = {0: 1, 2: 3, 6: 4}[color_type]
    bpp = channels * bit_depth // 8
    stride = width * bpp
    raw = bytearray()
    prev = bytes(stride)
    for y in range(height):
        row = pixels[y * stride:(y + 1) * stride]
        raw.append(y % 5)
        raw += _filter_row(y % 5, row, prev, bpp)
        prev = row
    z = zlib.compress(bytes(raw), 9)
    half = len(z) // 2
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, interlace))
            + _chunk(b"pHYs", struct.pack(">IIB", 2835, 2835, 1))
            + _chunk(b"IDAT", z[:half]) + _chunk(b"IDAT", z[half:])
            + _chunk(b"IEND", b""))


def noise_bytes(n, seed):
    rng = random.Random(seed)
    return bytes(rng.randrange(256) for _ in range(n))


class PngTests(unittest.TestCase):
    def test_png_round_trip(self):
        cases = [
            ("8-bit RGB", 7, 10, 8, 2, 3),
            ("8-bit RGBA", 6, 10, 8, 6, 4),
            ("16-bit grey", 9, 10, 16, 0, 2),
        ]
        for name, w, h, depth, ctype, bpp in cases:
            with self.subTest(name):
                pixels = noise_bytes(w * h * bpp, seed=w * 100 + ctype)
                img = pngio.read_png(encode_fixture(w, h, depth, ctype, pixels))
                self.assertEqual((img.width, img.height, img.bit_depth, img.color_type), (w, h, depth, ctype))
                self.assertEqual(img.pixels, pixels)  # every filter type (rows 0-9 use filters 0-4 twice)
                again = pngio.read_png(pngio.write_png(img))
                self.assertEqual(again, img)

    def test_png_rejects_unsupported(self):
        with self.assertRaises(GeneratorError):
            pngio.read_png(b"not a png at all")
        with self.assertRaises(GeneratorError):
            pngio.read_png(encode_fixture(2, 2, 8, 2, bytes(12), interlace=1))
        with self.assertRaises(GeneratorError):
            pngio.write_png(pngio.Image(2, 2, 8, 2, bytes(11)))


class GridTests(unittest.TestCase):
    def test_png_rows_are_flipped_to_map_coordinates(self):
        # PNG top row = north: values 1, 2 on top, 3, 4 at the bottom (south, y = 0)
        img = pngio.Image(2, 2, 16, 0, struct.pack(">4H", 1, 2, 3, 4))
        grid = hp.Grid.from_png(img)
        self.assertEqual(list(grid.values), [3, 4, 1, 2])
        self.assertEqual(grid.get(0, 1), 1)
        self.assertEqual(grid.to_png(), img)


class SettingsTests(unittest.TestCase):
    def test_settings_round_trip(self):
        s = hp.parse_settings(ANBENNAR_SETTINGS)
        self.assertEqual(s.tile_size, 33)
        self.assertEqual(s.original_size, (8192, 4096))
        self.assertEqual(s.level_offsets, [(0, 0), (0, 2788), (0, 3646), (0, 3776), (0, 3813)])
        self.assertEqual(s.max_compress_level, 4)
        self.assertEqual(s.empty_tile_offset, (243, 77))
        self.assertEqual(hp.settings_text(s, s.level_offsets, s.empty_tile_offset), ANBENNAR_SETTINGS)

        new = hp.settings_text(s, [(0, 0), (0, 2805), (0, 3655), (0, 3790), (0, 3825)], (100, 77))
        old_lines, new_lines = ANBENNAR_SETTINGS.split("\n"), new.split("\n")
        changed = [(a, b) for a, b in zip(old_lines, new_lines) if a != b]
        self.assertEqual(changed, [
            ("level_offsets={ { 0 0 } { 0 2788 } { 0 3646 } { 0 3776 } { 0 3813 } }",
             "level_offsets={ { 0 0 } { 0 2805 } { 0 3655 } { 0 3790 } { 0 3825 } }"),
            ("empty_tile_offset={ 243 77 }", "empty_tile_offset={ 100 77 }"),
        ])
        self.assertEqual(len(old_lines), len(new_lines))
        same_empty = hp.settings_text(s, [(0, 0), (0, 2805), (0, 3655), (0, 3790), (0, 3825)], (243, 77))
        self.assertIn("empty_tile_offset={ 243 77 }", same_empty)

    def test_settings_errors(self):
        with self.assertRaises(GeneratorError):
            hp.parse_settings(ANBENNAR_SETTINGS.replace("tile_size=33\n", ""))
        s = hp.parse_settings(ANBENNAR_SETTINGS)
        with self.assertRaises(GeneratorError):
            hp.settings_text(s, [(0, 0)], (0, 0))


def tile_values(size, base):
    return [base + j * 40 + i for j in range(size) for i in range(size)]


class CodecTests(unittest.TestCase):
    def test_unpack_fixture(self):
        # A 64x32 map = 2x1 blocks. Block (0, 0) is level 0 (33x33 tile at column 0, row 0 of level 0),
        # block (1, 0) is level 1 (17x17 tile at column 0, row 0 of level 1, which starts at y = 33).
        text = ANBENNAR_SETTINGS.replace("{ 8192 4096 }", "{ 64 32 }").replace(
            "{ { 0 0 } { 0 2788 } { 0 3646 } { 0 3776 } { 0 3813 } }",
            "{ { 0 0 } { 0 33 } { 0 50 } { 0 50 } { 0 50 } }")
        s = hp.parse_settings(text)
        packed = hp.Grid(33, 50, array("H", bytes(2 * 33 * 50)))
        t0, t1 = tile_values(33, 1000), tile_values(17, 5000)
        for j in range(33):
            for i in range(33):
                packed.values[j * 33 + i] = t0[j * 33 + i]
        for j in range(17):
            for i in range(17):
                packed.values[(33 + j) * 33 + i] = t1[j * 17 + i]
        ind = pngio.Image(2, 1, 8, 6, bytes([0, 0, 1, 0, 0, 0, 2, 1]))
        blocks = hp.unpack(ind, packed, s)
        self.assertEqual(blocks, {(0, 0): hp.Block(1, 0, t0), (1, 0): hp.Block(2, 1, t1)})

    def test_unpack_reads_indirection_bottom_up(self):
        # 32x64 map = 1x2 blocks; the PNG's top indirection row is block (0, 1), the north one.
        text = ANBENNAR_SETTINGS.replace("{ 8192 4096 }", "{ 32 64 }").replace(
            "{ { 0 0 } { 0 2788 } { 0 3646 } { 0 3776 } { 0 3813 } }",
            "{ { 0 0 } { 0 0 } { 0 0 } { 0 0 } { 0 0 } }")
        s = hp.parse_settings(text)
        packed = hp.Grid(6, 3, array("H", range(18)))
        ind = pngio.Image(1, 2, 8, 6, bytes([1, 0, 16, 4, 0, 0, 16, 4]))  # north -> tile 1, south -> tile 0
        blocks = hp.unpack(ind, packed, s)
        self.assertEqual(blocks[(0, 0)].tile, [0, 1, 2, 6, 7, 8, 12, 13, 14])
        self.assertEqual(blocks[(0, 1)].tile, [3, 4, 5, 9, 10, 11, 15, 16, 17])

    def test_unpack_rejects_bad_indirection(self):
        s = small_settings(32, 32)
        packed = hp.Grid(33, 33, array("H", bytes(2 * 33 * 33)))
        for pixel in ([0, 0, 2, 0], [0, 0, 3, 1], [5, 0, 1, 0]):  # step/level mismatch, bad step, outside
            with self.subTest(pixel=pixel), self.assertRaises(GeneratorError):
                hp.unpack(pngio.Image(1, 1, 8, 6, bytes(pixel)), packed, s)

    def test_pack_unpack_round_trip(self):
        rng = random.Random(7)
        s = small_settings(160, 96)  # 5x3 blocks
        blocks = {}
        for by in range(3):
            for bx in range(5):
                level = rng.randrange(5)
                size = (32 >> level) + 1
                blocks[(bx, by)] = hp.Block(1 << level, level, [rng.randrange(65536) for _ in range(size * size)])
        empty = [9] * 9
        packed, ind, offsets, empty_offset = hp.pack(blocks, 40, s, empty_tile=empty)
        self.assertEqual((ind.width, ind.height, ind.bit_depth, ind.color_type), (5, 3, 8, 6))
        self.assertEqual(packed.width, 40)
        s2 = hp.parse_settings(hp.settings_text(s, offsets, empty_offset))
        self.assertEqual(s2.level_offsets, offsets)
        self.assertEqual(hp.unpack(ind, packed, s2), blocks)
        self.assertEqual(hp.empty_tile(packed, s2), empty)

        # bands stack bottom-up from y = 0, x stays 0, and every tile lies inside its own band
        self.assertEqual(offsets[0], (0, 0))
        self.assertTrue(all(x == 0 for x, _ in offsets))
        tops = [y for _, y in offsets[1:]] + [packed.height]
        covered = set()
        rects = []
        for (bx, by), b in blocks.items():
            o = ((2 - by) * 5 + bx) * 4
            column, row = ind.pixels[o], ind.pixels[o + 1]
            rects.append((b.level, column, row))
        rects.append((4, empty_offset[0], empty_offset[1]))
        for level, column, row in rects:
            size = (32 >> level) + 1
            x0, y0 = column * size, offsets[level][1] + row * size
            self.assertLessEqual(x0 + size, 40)
            self.assertGreaterEqual(y0, offsets[level][1])
            self.assertLessEqual(y0 + size, tops[level])
            pixels = {(x, y) for x in range(x0, x0 + size) for y in range(y0, y0 + size)}
            self.assertFalse(pixels & covered, "tiles overlap")
            covered |= pixels
        # the empty tile follows the last level-4 tile
        n4 = sum(1 for b in blocks.values() if b.level == 4)
        cols4 = min(256, 40 // 3)
        self.assertEqual(empty_offset, (n4 % cols4, n4 // cols4))

    def test_pack_fills_rows_in_block_order(self):
        s = small_settings(96, 32)  # 3x1 blocks, all level 4: tiles 0, 1, 2 then the empty tile
        blocks = {(bx, 0): hp.Block(16, 4, [bx] * 9) for bx in range(3)}
        packed, ind, offsets, empty_offset = hp.pack(blocks, 6, s)  # 2 level-4 tiles per row
        self.assertEqual(offsets, [(0, 0)] * 5)
        self.assertEqual(list(ind.pixels), [0, 0, 16, 4, 1, 0, 16, 4, 0, 1, 16, 4])
        self.assertEqual(empty_offset, (1, 1))
        self.assertEqual(packed.height, 6)
        self.assertEqual(hp.empty_tile(packed, hp.parse_settings(hp.settings_text(s, offsets, empty_offset))), [0] * 9)

    def test_pack_rejects_bad_blocks(self):
        s = small_settings(64, 32)
        good = hp.Block(16, 4, [0] * 9)
        bad = [
            {(0, 0): good},  # block (1, 0) missing
            {(0, 0): good, (1, 0): hp.Block(8, 4, [0] * 9)},  # step does not match level
            {(0, 0): good, (1, 0): hp.Block(16, 4, [0] * 8)},  # wrong tile size
            {(0, 0): good, (1, 0): hp.Block(16, 4, [70000] * 9)},  # height out of range
        ]
        for blocks in bad:
            with self.subTest(blocks=blocks), self.assertRaises(GeneratorError):
                hp.pack(blocks, 40, s)


def ramp_grid(width, height, f):
    return hp.Grid(width, height, array("H", [f(x, y) for y in range(height) for x in range(width)]))


class SamplingTests(unittest.TestCase):
    def test_sample_clamps_to_the_grid_edge(self):
        grid = ramp_grid(64, 32, lambda x, y: y * 64 + x)
        self.assertEqual(hp.sample(grid, 1, 0, 16), [
            0 * 64 + 32, 0 * 64 + 48, 0 * 64 + 63,
            16 * 64 + 32, 16 * 64 + 48, 16 * 64 + 63,
            31 * 64 + 32, 31 * 64 + 48, 31 * 64 + 63,
        ])
        self.assertEqual(len(hp.sample(grid, 0, 0, 1)), 33 * 33)

    def test_choose_level(self):
        flat = ramp_grid(65, 65, lambda x, y: 1000)
        self.assertEqual(hp.choose_level(flat, 0, 0, 257), 4)
        slope = ramp_grid(65, 65, lambda x, y: 100 * x + 37 * y)  # bilinear interpolation is exact
        self.assertEqual(hp.choose_level(slope, 1, 1, 0), 4)
        spike = ramp_grid(65, 65, lambda x, y: 10000 if (x, y) == (4, 4) else 0)
        self.assertEqual(hp.choose_level(spike, 0, 0, 257), 0)
        def tent(v):
            return max(0, 4000 - 500 * abs(v - 16))  # knots at 8, 16 and 24
        bump = ramp_grid(65, 65, lambda x, y: tent(x) * tent(y) // 4000)
        self.assertEqual(hp.choose_level(bump, 0, 0, 257), 3)  # step 8 hits every knot, step 16 misses 8 and 24
        self.assertEqual(hp.choose_level(bump, 0, 0, 257, max_level=2), 2)

    def test_changed_blocks_include_neighbours(self):
        old = ramp_grid(96, 64, lambda x, y: 500)
        self.assertEqual(hp.changed_blocks(old, old), set())
        new = hp.Grid(96, 64, array("H", old.values))
        new.values[5 * 96 + 32] = 600  # pixel (32, 5): the shared edge of blocks (0, 0) and (1, 0)
        self.assertEqual(hp.changed_blocks(old, new), {(0, 0), (1, 0)})
        new.values[32 * 96 + 64] = 600  # pixel (64, 32): the corner of four blocks
        self.assertEqual(hp.changed_blocks(old, new), {(0, 0), (1, 0), (2, 0), (1, 1), (2, 1)})
        new.values[63 * 96 + 95] = 600  # pixel (95, 63): the map corner, block (2, 1) only
        self.assertEqual(hp.changed_blocks(old, new), {(0, 0), (1, 0), (2, 0), (1, 1), (2, 1)})
        with self.assertRaises(GeneratorError):
            hp.changed_blocks(old, ramp_grid(64, 64, lambda x, y: 0))


@unittest.skipUnless(LIVE, "Anbennar CK3 not present")
class AnbennarRepackTests(unittest.TestCase):
    """Repacking Anbennar's own packed tiles unchanged reproduces every tile (decoded once for the class)."""

    @classmethod
    def setUpClass(cls):
        cls.text = (ANBENNAR_MAP / "heightmap.heightmap").read_bytes().decode("utf-8")
        cls.settings = hp.parse_settings(cls.text)
        cls.indirection = pngio.read_png((ANBENNAR_MAP / "indirection_heightmap.png").read_bytes())
        cls.packed = hp.Grid.from_png(pngio.read_png((ANBENNAR_MAP / "packed_heightmap.png").read_bytes()))
        cls.blocks = hp.unpack(cls.indirection, cls.packed, cls.settings)
        cls.empty = hp.empty_tile(cls.packed, cls.settings)
        packed, ind, cls.offsets, cls.empty_offset = hp.pack(cls.blocks, cls.packed.width, cls.settings,
                                                             empty_tile=cls.empty)
        cls.new_text = hp.settings_text(cls.settings, cls.offsets, cls.empty_offset)
        cls.new_settings = hp.parse_settings(cls.new_text)
        # through the PNG writer and reader, as the generator will ship them
        cls.new_packed = hp.Grid.from_png(pngio.read_png(pngio.write_png(packed.to_png())))
        cls.new_indirection = pngio.read_png(pngio.write_png(ind))
        cls.new_blocks = hp.unpack(cls.new_indirection, cls.new_packed, cls.new_settings)

    def test_settings_file_round_trips(self):
        self.assertEqual(hp.settings_text(self.settings, self.settings.level_offsets,
                                          self.settings.empty_tile_offset), self.text)

    def test_orientation(self):
        # bottom-up: the south-west corner block (sea) is level 4, block (99, 0) is Anbennar's first level-0 block
        self.assertEqual(len(self.blocks), 256 * 128)
        self.assertEqual(self.blocks[(0, 0)].level, 4)
        self.assertEqual(self.blocks[(99, 0)].level, 0)

    def test_repack_reproduces_every_tile(self):
        self.assertEqual(len(self.new_blocks), 32768)
        self.assertEqual(self.new_blocks, self.blocks)
        self.assertEqual(self.new_blocks[(0, 0)].level, 4)

    def test_empty_tile_kept_after_the_last_level_4_tile(self):
        self.assertEqual(self.empty, [0] * 9)
        self.assertEqual(hp.empty_tile(self.new_packed, self.new_settings), self.empty)
        n4 = sum(1 for b in self.blocks.values() if b.level == 4)
        self.assertEqual(self.empty_offset, (n4 % 256, n4 // 256))

    def test_bands_do_not_overlap(self):
        self.assertEqual(self.offsets[0], (0, 0))
        counts = [sum(1 for b in self.blocks.values() if b.level == lv) for lv in range(5)]
        counts[4] += 1  # the empty tile
        y = 0
        for level, n in enumerate(counts):
            size = (32 >> level) + 1
            cols = min(256, self.packed.width // size)
            self.assertEqual(self.offsets[level], (0, y))
            y += -(-n // cols) * size
        self.assertEqual(self.new_packed.height, y)
        self.assertEqual(self.new_packed.width, self.packed.width)


if __name__ == "__main__":
    unittest.main()
