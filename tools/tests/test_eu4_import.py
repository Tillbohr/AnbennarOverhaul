import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import eu4_import as ei  # noqa: E402

EU4 = ei.EU4_ROOTS["anbennar"]
LIVE = EU4.is_dir()


def dds_header(w, h, fourcc):
    head = bytearray(128)
    head[0:4] = b"DDS "
    struct.pack_into("<II", head, 12, h, w)
    struct.pack_into("<I", head, 80, 0x4)  # DDPF_FOURCC
    head[84:88] = fourcc
    return bytes(head)


def dx10(w, h, dxgi, pixels):
    return dds_header(w, h, b"DX10") + struct.pack("<IIIII", dxgi, 3, 0, 1, 0) + pixels


class DdsTests(unittest.TestCase):
    def test_dx10_bgra_converts_to_legacy_header(self):
        w, h = 6, 2
        pixels = bytes(range(w * h * 4))
        out = ei.dx10_bgra_to_legacy(dx10(w, h, 91, pixels))
        self.assertEqual(len(out), 128 + len(pixels))
        self.assertEqual(out[128:], pixels)
        self.assertEqual(struct.unpack("<II", out[12:20]), (h, w))
        self.assertEqual(struct.unpack("<I", out[80:84])[0], 0x41)  # DDPF_RGB | DDPF_ALPHAPIXELS
        self.assertEqual(struct.unpack("<5I", out[88:108]), (32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000))
        with self.assertRaises(ei.EU4ImportError):
            ei.dx10_bgra_to_legacy(dx10(w, h, 98, pixels))  # BC7

    def test_bgra_round_trip(self):
        px = bytes(range(4 * 3 * 4))
        self.assertEqual(ei.read_dds(ei.write_bgra(4, 3, px)), (4, 3, px))

    def test_dxt1_block(self):
        # c0 pure red > c1 pure blue: four-colour block; indices 0,1,2,3 in the first row, then all 0
        bits = 0 | (1 << 2) | (2 << 4) | (3 << 6)
        data = dds_header(4, 4, b"DXT1") + struct.pack("<HHI", 0xF800, 0x001F, bits)
        w, h, px = ei.read_dds(data)
        texel = lambda i: tuple(px[i * 4:i * 4 + 4])  # noqa: E731  (b, g, r, a)
        self.assertEqual((w, h), (4, 4))
        self.assertEqual(texel(0), (0, 0, 255, 255))
        self.assertEqual(texel(1), (255, 0, 0, 255))
        self.assertEqual(texel(2), (85, 0, 170, 255))
        self.assertEqual(texel(4), (0, 0, 255, 255))

    def test_dxt5_alpha(self):
        alpha_bits = 1 | (7 << 3)  # texel 0 -> a1, texel 1 -> index 7
        block = bytes([200, 100]) + alpha_bits.to_bytes(6, "little") + struct.pack("<HHI", 0xFFFF, 0, 0)
        w, h, px = ei.read_dds(dds_header(4, 4, b"DXT5") + block)
        self.assertEqual(px[3], 100)  # a1
        self.assertEqual(px[7], (1 * 200 + 6 * 100) // 7)  # 8-value ramp, index 7
        self.assertEqual(px[11], 200)  # index 0
        self.assertEqual(tuple(px[0:3]), (255, 255, 255))

    def test_mips_header_and_size(self):
        out = ei.write_dds_mips(4, 2, bytes(4 * 2 * 4))
        self.assertEqual(struct.unpack("<I", out[28:32])[0], 3)  # 4x2, 2x1, 1x1
        self.assertEqual(len(out), 128 + (8 + 2 + 1) * 4)


class TgaTests(unittest.TestCase):
    def test_rle_bottom_up_24bit(self):
        head = bytearray(18)
        head[2] = 10
        struct.pack_into("<HH", head, 12, 2, 2)
        head[16] = 24
        # bottom row: one run of 2 blue pixels; top row: raw red, green
        body = bytes([0x81, 255, 0, 0]) + bytes([0x01, 0, 0, 255, 0, 255, 0])
        w, h, px = ei.read_tga(bytes(head) + body)
        self.assertEqual((w, h), (2, 2))
        self.assertEqual(px, bytes([0, 0, 255, 255, 0, 255, 0, 255, 255, 0, 0, 255, 255, 0, 0, 255]))


class ResampleTests(unittest.TestCase):
    def test_upscale_2x_keeps_flat_colour_and_range(self):
        flat = bytes([10, 20, 30, 255]) * (8 * 4)
        w, h, px = ei.upscale_2x(8, 4, flat)
        self.assertEqual((w, h), (16, 8))
        self.assertEqual(px, bytes([10, 20, 30, 255]) * (16 * 8))
        row = [0] * 4 + [255] * 4
        edge = bytes(v for x in row for v in (x, x, x, 255)) * 2
        w, h, px = ei.upscale_2x(8, 2, edge)
        blues = list(px[0:w * 4:4])
        self.assertEqual((blues[0], blues[-1]), (0, 255))
        self.assertTrue(all(0 <= v <= 255 for v in px))
        self.assertTrue(any(0 < v < 255 for v in blues[6:10]), blues)

    def test_convert_passes_compressed_dds_through(self):
        data = dds_header(4, 4, b"DXT1") + bytes(8)
        self.assertIs(ei.convert(data, False), data)

    def test_convert_resize(self):
        out = ei.convert(ei.write_bgra(4, 4, bytes([1, 2, 3, 255]) * 16), False, size=(2, 2))
        self.assertEqual(ei.read_dds(out), (2, 2, bytes([1, 2, 3, 255]) * 4))


def png_pixels(data):
    """(width, height, RGBA bytes) of a PNG written by write_png (one IDAT, filter 0 on every row)."""
    import zlib
    w, h = struct.unpack(">II", data[16:24])
    length = struct.unpack(">I", data[33:37])[0]
    raw = zlib.decompress(data[41:41 + length])
    rows = [raw[y * (w * 4 + 1):(y + 1) * (w * 4 + 1)] for y in range(h)]
    assert all(r[0] == 0 for r in rows)
    return w, h, b"".join(r[1:] for r in rows)


class PngTests(unittest.TestCase):
    def test_write_png_rgba_from_bgra(self):
        data = ei.write_png(2, 1, bytes([1, 2, 3, 4, 5, 6, 7, 8]))
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(data[12:16], b"IHDR")
        self.assertEqual(data[24:26], bytes([8, 6]))  # 8 bits, RGBA
        self.assertEqual(png_pixels(data), (2, 1, bytes([3, 2, 1, 4, 7, 6, 5, 8])))
        self.assertEqual(data[-8:-4], b"IEND")

    def test_read_png_round_trip(self):
        px = bytes((x * 7 + c * 50) % 256 for x in range(5 * 3) for c in range(4))
        self.assertEqual(ei.read_png(ei.write_png(5, 3, px)), (5, 3, px))

    def test_from_png_writes_bgra_dds(self):
        px = bytes([9, 8, 7, 255]) * 16
        self.assertEqual(ei.read_dds(ei.from_png(ei.write_png(4, 4, px))), (4, 4, px))
        self.assertEqual(ei.read_dds(ei.from_png(ei.write_png(4, 4, px), (2, 2))), (2, 2, px[:16]))

    def test_fade_edges(self):
        w, h, rows = 8, 40, 20
        px = bytes([100, 150, 200, 255]) * (w * h)
        fw, fh, out = ei.fade_edges(w, h, px, rows)
        self.assertEqual((fw, fh), (w, h + 2 * rows))
        row = lambda y: out[y * w * 4:(y + 1) * w * 4]  # noqa: E731
        self.assertEqual(row(rows + h // 2), px[:w * 4])  # the middle of the picture is untouched
        self.assertLess(row(0)[0], 30)  # the far edges fade to dark
        self.assertLess(row(fh - 1)[0], 30)
        self.assertEqual(set(out[3::4]), {255})  # alpha untouched
        self.assertTrue(all(row(y)[0] >= row(y - 1)[0] for y in range(1, rows + 1)))  # brightens towards the picture

    def test_from_png_stretch_and_fade(self):
        png = ei.write_png(4, 10, bytes([9, 8, 7, 255]) * 40)
        self.assertEqual(ei.read_dds(ei.from_png(png, stretch_y=1.3, fade=3))[:2], (4, 13 + 6))

    def test_read_png_filters_and_rgb(self):
        """An RGB PNG whose rows use the Sub, Up, Average and Paeth filters decodes to the same pixels."""
        import zlib
        w, rows = 3, [bytes((x * 40 + y * 30 + c * 9) % 256 for x in range(3) for c in range(3)) for y in range(4)]

        def predict(kind, row, prev, i):
            a = row[i - 3] if i >= 3 else 0
            b, c = prev[i], prev[i - 3] if i >= 3 else 0
            p = a + b - c
            paeth = min((abs(p - a), 0, a), (abs(p - b), 1, b), (abs(p - c), 2, c))[2]
            return {1: a, 2: b, 3: (a + b) // 2, 4: paeth}[kind]

        raw, prev = b"", bytes(w * 3)
        for kind, row in zip((1, 2, 3, 4), rows):
            raw += bytes([kind]) + bytes((row[i] - predict(kind, row, prev, i)) & 255 for i in range(w * 3))
            prev = row
        chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))  # noqa: E731
        png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, 4, 8, 2, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
        expected = b"".join(bytes((r[i + 2], r[i + 1], r[i], 255)) for r in rows for i in range(0, w * 3, 3))
        self.assertEqual(ei.read_png(png), (w, 4, expected))


class PaintingTests(unittest.TestCase):
    def test_crop_frame(self):
        w, h = 20, 18
        px = bytes((x, y, 0, 255)[c] for y in range(h) for x in range(w) for c in range(4))
        cw, ch, out = ei.crop_frame(w, h, px)
        self.assertEqual((cw, ch), (w - 2 * ei.FRAME_CROP, h - 2 * ei.FRAME_CROP))
        self.assertEqual(out[0:2], bytes([ei.FRAME_CROP, ei.FRAME_CROP]))

    def test_lift_title_strip_brightens_only_the_plate(self):
        w, h = 300, 40
        px = ei.lift_title_strip(w, h, bytes([100, 100, 100, 255]) * (w * h))
        at = lambda x, y: px[(y * w + x) * 4]  # noqa: E731
        self.assertGreater(at(20, 15), 200)  # full darkening at the left (0.46)
        self.assertEqual(at(160, 15), 100)  # right of the plate
        self.assertEqual(at(20, 35), 100)  # below the plate
        self.assertEqual(px[(15 * w + 20) * 4 + 3], 255)  # alpha untouched


@unittest.skipUnless(LIVE, "EU4 Anbennar not installed")
class RealImportTests(unittest.TestCase):
    """The helpers reproduce what the earlier one-time imports committed."""

    def test_monument_painting(self):
        """The committed paintings are the cleaned EU4 painting (286x136) upscaled 4x outside (Upscayl)."""
        key = "adenica_longlance_knights_academy"
        w, h, px = ei.clean_painting(*ei.read_dds(ei.eu4_file(f"gfx/interface/great_projects/great_project_{key}.dds")
                                                   .read_bytes()))
        self.assertEqual((w, h), (286, 136))
        committed = (ei.SUBMOD / f"gfx/interface/illustrations/aov_monuments/{key}.dds").read_bytes()
        self.assertEqual(ei.read_dds(committed)[:2], (4 * w, 4 * h))

    def test_invention_buttons(self):
        for c in ("economic", "military", "society"):
            src = (EU4 / "gfx/interface/custom_gui/artificery" / f"artificery_innovation_{c}.dds").read_bytes()
            committed = (ei.SUBMOD / "gfx/interface/icons/aov_inventions" / f"aov_invention_button_{c}.dds").read_bytes()
            self.assertEqual(ei.convert(src, False), committed, c)

    def test_grove_flag_emblem(self):
        src = (EU4 / "gfx/flags/I26.tga").read_bytes()
        committed = (ei.SUBMOD / "gfx/coat_of_arms/textured_emblems/aov_grove_salla_elyn.dds").read_bytes()
        self.assertEqual(ei.convert(src, True, upscale2x=True, mips=True), committed)

    def test_province_names_and_regions(self):
        self.assertTrue(ei.province_names(EU4))
        self.assertTrue(ei.region_provinces(("west_deepwoods_region",), EU4))


if __name__ == "__main__":
    unittest.main()
