"""Tests for tools/build_gnoll_portraits.py and the gnoll portrait files (head assets: test_build_head_assets.py).

    python -I -m unittest discover -s tools/tests -p test_build_gnoll_portraits.py
"""

import re
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_gnoll_portraits as gnoll  # noqa: E402
import dxt5  # noqa: E402
from eu4_import import read_dds  # noqa: E402

SUBMOD = gnoll.SUBMOD


def read(rel: str) -> str:
    return (SUBMOD / rel).read_bytes().decode("utf-8-sig")


class ArtTests(unittest.TestCase):
    def test_imported_art_present(self):
        for out_rel in gnoll.IMPORTS.values():
            self.assertTrue((SUBMOD / out_rel).is_file(), out_rel)

    @unittest.skipUnless(gnoll.DEFAULT_VIC3.is_dir(), "needs Victoria 3 Anbennar")
    def test_imported_art_matches_vic3(self):
        for src_rel, out_rel in gnoll.IMPORTS.items():
            self.assertEqual((gnoll.DEFAULT_VIC3 / src_rel).read_bytes(), (SUBMOD / out_rel).read_bytes(), out_rel)

    def test_fur_is_a_linear_dxt5_decal(self):
        # the game's decals are 1024 px DXT5; the decal colour is read as linear, so the fur is darker than Vic3's sRGB
        raw = (SUBMOD / gnoll.FUR).read_bytes()
        self.assertEqual(raw[84:88], b"DXT5")
        self.assertEqual(struct.unpack("<II", raw[12:20]), (1024, 1024))
        self.assertEqual(struct.unpack_from("<I", raw, 28)[0], 11)
        _, _, px = read_dds(raw)
        self.assertLess(sum(px[2::4 * 101]) / len(px[2::4 * 101]), 140)  # red mean: Vic3's sRGB fur is about 173

    @unittest.skipUnless((gnoll.DEFAULT_VIC3 / gnoll.FUR_SOURCE).is_file(), "needs Victoria 3 Anbennar")
    def test_fur_matches_a_fresh_conversion(self):
        fresh = gnoll.fur_dds((gnoll.DEFAULT_VIC3 / gnoll.FUR_SOURCE).read_bytes())
        self.assertEqual(fresh, (SUBMOD / gnoll.FUR).read_bytes(), "stale: rerun build_gnoll_portraits.py --import")

    def test_linear_conversion(self):
        self.assertEqual(gnoll.linear_fur(bytes((0, 128, 255, 77))), bytes((0, 55, 255, 77)))


class Dxt5Tests(unittest.TestCase):
    def test_round_trip_and_mips(self):
        # 8x8: a smooth brown-to-tan gradient (channels moving together, as in fur; a DXT block's colours lie on one
        # line) with a varying alpha decodes back closely; the chain runs down to 1x1
        px = bytes(v for y in range(8) for x in range(8)
                   for t in [x + 8 * y] for v in (20 + t, 40 + 2 * t, 60 + 3 * t, 255 - 3 * t))
        raw = dxt5.write_dds(8, 8, px)
        self.assertEqual(raw[84:88], b"DXT5")
        self.assertEqual(struct.unpack_from("<I", raw, 28)[0], 4)  # 8, 4, 2, 1
        self.assertEqual(len(raw), 128 + 4 * 16 + 16 + 16 + 16)
        w, h, out = read_dds(raw)
        self.assertEqual((w, h), (8, 8))
        self.assertLessEqual(max(abs(a - b) for a, b in zip(px, out)), 12)

    def test_flat_block(self):
        raw = dxt5.write_dds(4, 4, bytes((10, 20, 30, 255)) * 16)
        _, _, out = read_dds(raw)
        self.assertLessEqual(max(abs(a - b) for a, b in zip(bytes((10, 20, 30, 255)) * 16, out)), 4)


class WiringTests(unittest.TestCase):
    """The gene, accessories, eye entities and portrait modifier name each other."""

    def test_gene_reads_the_head_attribute_and_existing_textures(self):
        genes = read("common/genes/aov_gnoll_genes.txt")
        self.assertIn(f'attribute = "{gnoll.ATTRIBUTE}"', genes)
        # fur as one diffuse decal above the game's eyebrow and lip decals (priority 10), not a texture_override
        # (ignored in game); the head keeps the game's normal map and properties
        self.assertNotRegex(genes, r"(?m)^\s*texture_override")
        self.assertEqual(genes.count("body_part = head"), 1)
        self.assertEqual(re.findall(r"priority = (\d+)", genes), ["20"])
        textures = re.findall(r'"(gfx/[^"]+\.dds)"', genes)
        self.assertEqual(textures, ["gfx/models/portraits/aov_gnoll/aov_gnoll_head_diffuse.dds"])
        for tex in textures:
            self.assertTrue((SUBMOD / tex).is_file(), tex)

    def test_eye_accessories_and_entities_exist(self):
        genes = read("common/genes/aov_gnoll_genes.txt")
        accessories = read("gfx/portraits/accessories/aov_gnoll.txt")
        asset = read("gfx/models/portraits/aov_gnoll/aov_gnoll_eyes.asset")
        for sex in ("male", "female"):
            self.assertIn(f"1 = aov_{sex}_gnoll_eyes", genes)
            self.assertRegex(accessories, rf"(?m)^aov_{sex}_gnoll_eyes = \{{")
            self.assertIn(f"entity = aov_{sex}_gnoll_eyes_entity", accessories)
            self.assertIn(f'name = "aov_{sex}_gnoll_eyes_entity"', asset)
        for tex in re.findall(r'texture_diffuse = "([^"]+)"', asset):
            self.assertTrue((SUBMOD / "gfx/models/portraits/aov_gnoll" / tex).is_file(), tex)

    def test_modifier_uses_defined_templates(self):
        genes = read("common/genes/aov_gnoll_genes.txt")
        modifier = read("gfx/portraits/portrait_modifiers/aov_gnoll.txt")
        for gene, template in re.findall(r"gene = (aov_gnoll_\w+)\s+template = (\w+)", modifier):
            self.assertRegex(genes, rf"(?m)^\s*{gene} = \{{", gene)
            self.assertRegex(genes, rf"(?m)^\s*{template} = \{{", template)
        self.assertEqual(modifier.count("has_trait = race_gnoll"), 2)

    def test_head_is_a_special_gene_added_like_gene_wounded(self):
        # As a regular gene set by mode = replace, its blend shape showed in game but its textures did not
        genes = read("common/genes/aov_gnoll_genes.txt")
        special = genes[genes.index("special_genes = {"):genes.index("accessory_genes = {")]
        self.assertIn("aov_gnoll_head = {", special)
        modifier = read("gfx/portraits/portrait_modifiers/aov_gnoll.txt")
        modes = re.findall(r"mode = (\w+)\s+gene = aov_gnoll_head\b", modifier)
        self.assertEqual(modes, ["add", "add"])


if __name__ == "__main__":
    unittest.main()
