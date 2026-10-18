"""Tests for tools/build_deepwoods_groves.py (EU4 flags and province names for the Deepwoods grove duchies).

    python -I -m unittest discover -s tools/tests -p test_build_deepwoods_groves.py -v
"""

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_deepwoods_groves as dg  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import deepwoods_groves as data  # noqa: E402

REAL = dg.Roots.default()
HAVE_REAL = REAL.anbennar.is_dir() and (REAL.eu4 / "gfx" / "flags").is_dir()


def tga_header(kind, w, h, bpp, desc=0):
    return bytes([0, 0, kind]) + bytes(9) + struct.pack("<HH", w, h) + bytes([bpp, desc])


class TgaTests(unittest.TestCase):
    # 2x2 image, bottom-up rows: bottom row red, blue; top row green, white (BGR order on disk)
    BOTTOM = b"\x00\x00\xff" + b"\xff\x00\x00"
    TOP = b"\x00\xff\x00" + b"\xff\xff\xff"
    EXPECTED = (b"\x00\xff\x00\xff" + b"\xff\xff\xff\xff" + b"\x00\x00\xff\xff" + b"\xff\x00\x00\xff")

    def test_raw_bottom_up_24_bit(self):
        w, h, px = dg.read_tga(tga_header(2, 2, 2, 24) + self.BOTTOM + self.TOP)
        self.assertEqual((w, h, px), (2, 2, self.EXPECTED))

    def test_rle_packets(self):
        # one raw packet of 2 pixels, then a run packet of 2 identical pixels
        body = bytes([0x01]) + self.BOTTOM + bytes([0x81]) + b"\x10\x20\x30"
        _, _, px = dg.read_tga(tga_header(10, 2, 2, 24) + body)
        self.assertEqual(px[:8], b"\x10\x20\x30\xff" * 2)
        self.assertEqual(px[8:], b"\x00\x00\xff\xff\xff\x00\x00\xff")

    def test_top_down_32_bit_keeps_alpha(self):
        px_in = bytes(range(16))
        _, _, px = dg.read_tga(tga_header(2, 2, 2, 32, 0x20) + px_in)
        self.assertEqual(px, px_in)

    def test_rejects_colour_mapped_and_truncated(self):
        with self.assertRaises(GeneratorError):
            dg.read_tga(tga_header(1, 2, 2, 8) + bytes(4))
        with self.assertRaises(GeneratorError):
            dg.read_tga(tga_header(2, 2, 2, 24) + bytes(5))


class DdsTests(unittest.TestCase):
    def test_full_mip_chain(self):
        px = bytes([10, 20, 30, 255]) * 16
        dds = dg.write_dds_mips(4, 4, px)
        height, width = struct.unpack("<II", dds[12:20])
        mips = struct.unpack("<I", dds[28:32])[0]
        self.assertEqual((width, height, mips), (4, 4, 3))
        self.assertEqual(len(dds), 128 + (16 + 4 + 1) * 4)
        self.assertEqual(dds[-4:], bytes([10, 20, 30, 255]))

    def test_halve_averages_blocks(self):
        px = bytes([0, 0, 0, 255, 100, 100, 100, 255, 0, 0, 0, 255, 100, 100, 100, 255])
        self.assertEqual(dg.halve(2, 2, px), (1, 1, bytes([50, 50, 50, 255])))

    def test_emblem_name(self):
        self.assertEqual(dg.emblem_name("Salla Ghul"), "aov_grove_salla_ghul.dds")


class DataTests(unittest.TestCase):
    def test_nine_groves_with_distinct_tags_and_provinces(self):
        self.assertEqual(len(data.GROVES), 9)
        tags = [g["tag"] for g in data.GROVES.values()]
        self.assertEqual(len(set(tags)), 9)
        provinces = [p for g in data.GROVES.values() for part in ("counties", "baronies") for p in g[part].values()]
        self.assertEqual(len(provinces), len(set(provinces)))

    def test_county_baronies_keeps_title_order(self):
        text = ("d_x = { capital = c_a c_a = { b_2 = { province = 2 } b_1 = { province = 1 } }"
                " c_b = { b_3 = { province = 3 } } } d_y = { c_c = { b_4 = { province = 4 } } }")
        self.assertEqual(dg.county_baronies(text, "d_x"), {"c_a": ["b_2", "b_1"], "c_b": ["b_3"]})
        self.assertEqual(dg.duchy_counties(text, "d_x"), ["c_a", "c_b"])
        with self.assertRaises(GeneratorError):
            dg.county_baronies(text, "d_z")

    def test_fold_drops_accents_and_case(self):
        self.assertEqual(dg.fold("Elynáile"), dg.fold("elynaile"))


@unittest.skipUnless(HAVE_REAL, "Anbennar or EU4 Anbennar not installed")
class RealDataTests(unittest.TestCase):
    def test_every_county_of_each_duchy_is_named(self):
        titles = dg.eu4_monuments.strip_comments((REAL.anbennar / dg.TITLES).read_text(encoding="utf-8-sig"))
        for duchy, grove in data.GROVES.items():
            self.assertEqual(sorted(dg.duchy_counties(titles, duchy)), sorted(grove["counties"]), duchy)

    def test_flags_are_salla_realms(self):
        for r in dg.collect(REAL):
            self.assertTrue(r["name"].startswith("Salla "), r)

    def test_capital_baronies_share_the_county_name(self):
        titles = dg.eu4_monuments.strip_comments((REAL.anbennar / dg.TITLES).read_text(encoding="utf-8-sig"))
        for r in dg.collect(REAL):
            baronies = dict(r["baronies"])
            for county, name in r["counties"]:
                capital = dg.county_baronies(titles, r["duchy"])[county][0]
                self.assertEqual(baronies[capital], name, capital)

    def test_every_barony_is_named_or_listed(self):
        titles = dg.eu4_monuments.strip_comments((REAL.anbennar / dg.TITLES).read_text(encoding="utf-8-sig"))
        for r in dg.collect(REAL):
            real = [b for bs in dg.county_baronies(titles, r["duchy"]).values() for b in bs]
            self.assertEqual(sorted([b for b, _ in r["baronies"]] + r["unnamed"]), sorted(real), r["duchy"])

    def test_name_fixes_apply(self):
        arrow = next(r for r in dg.collect(REAL) if r["duchy"] == "d_arrow_grove_1")
        self.assertEqual(dict(arrow["baronies"])["b_arrow_grove_4"], "Llannlar")

    def test_bad_barony_stops_the_build(self):
        def grove(baronies):
            return {"d_lake_grove_1": {"tag": "I26", "counties": {"c_lake_grove_1_1": 7000}, "baronies": baronies}}
        with self.assertRaisesRegex(GeneratorError, "capital of c_lake_grove_1_1"):
            dg.collect(REAL, grove({"b_lake_grove_1": 3005}))
        with self.assertRaisesRegex(GeneratorError, "not one of its baronies"):
            dg.collect(REAL, grove({"b_bone_grove_5": 3005}))
        with self.assertRaisesRegex(GeneratorError, "already used by c_lake_grove_1_1"):
            dg.collect(REAL, grove({"b_lake_grove_2": 7000}))
        with self.assertRaisesRegex(GeneratorError, "forest path"):
            dg.collect(REAL, grove({"b_lake_grove_2": 3049}))

    def test_unknown_county_stops_the_build(self):
        bad = {"d_lake_grove_1": {"tag": "I26", "counties": {"c_bone_grove_1_1": 7000}}}
        with self.assertRaisesRegex(GeneratorError, "not one of its counties"):
            dg.collect(REAL, bad)

    def test_forest_path_and_outside_province_stop_the_build(self):
        path = {"d_lake_grove_1": {"tag": "I26", "counties": {"c_lake_grove_1_1": 3049}}}  # Vyr Bór
        with self.assertRaisesRegex(GeneratorError, "forest path"):
            dg.collect(REAL, path)
        outside = {"d_lake_grove_1": {"tag": "I26", "counties": {"c_lake_grove_1_1": 1}}}
        with self.assertRaisesRegex(GeneratorError, "outside"):
            dg.collect(REAL, outside)


@unittest.skipUnless(HAVE_REAL, "Anbennar or EU4 Anbennar not installed")
class FreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = dg.build_all(REAL)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (dg.SUBMOD / rel).is_file() or (dg.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_deepwoods_groves.py")

    def test_no_orphan_emblems(self):
        orphans = [p.name for p in (dg.SUBMOD / dg.EMBLEM_DIR).glob(dg.EMBLEM_PREFIX + "*")
                   if f"{dg.EMBLEM_DIR}/{p.name}" not in self.files]
        self.assertEqual(orphans, [], "leftover emblems: rerun the build")

    def test_every_duchy_draws_its_emblem(self):
        coa = self.files[dg.COA_FILE].decode("utf-8-sig")
        for duchy in data.GROVES:
            self.assertIn(f"\n{duchy} = {{\n", coa)
        for rel in self.files:
            if rel.startswith(dg.EMBLEM_DIR):
                self.assertIn(f'texture = "{rel.rsplit("/", 1)[1]}"', coa)


if __name__ == "__main__":
    unittest.main()
