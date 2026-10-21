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


@unittest.skipUnless(LIVE, "EU4 Anbennar not installed")
class RealImportTests(unittest.TestCase):
    """The helpers reproduce what the earlier one-time imports committed."""

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
