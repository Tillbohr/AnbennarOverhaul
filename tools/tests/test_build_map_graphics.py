import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_map_graphics as bmg  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import map_graphics as data  # noqa: E402

ANB = """# comment
{
\t{
\t\tname     = "Rock"
\t\tdiffuse  = "rock_diffuse.dds"
\t\tnormal   = "rock_normal.dds"
\t\tmaterial = "rock_properties.dds"
\t\tmask     = "masks/rock_mask.png"
\t\tid       = "rock"
\t\ttile_factor = 3
\t}
\t{ # odd block
\t\tname     = "Grass"
\t\t\tdiffuse  = "grass_diffuse.dds"
\t\tnormal   = "grass_normal.dds"
\t\tmaterial = "grass_properties.dds"
\t\tmask     = "masks/grass_mask.png"
\t\tid       = "grass"
\t}
}
"""

RIE = (
    "# rie\r\n{\r\n"
    "\t{\r\n\t\tname = \t\t\"Hard\"\r\n\t\tdiffuse =\t\"hard_diffuse.dds\"\r\n"
    "\t\tnormal =\t\"desert_cracked_normal.dds\"\r\n\t\tmaterial =\t\"hard_properties.dds\"\r\n"
    "\t\tmask = \t\t\"hard_mask.bmp\"\r\n\t\tid =\t\t\"hard\"\r\n\t}\r\n"
    "}\r\n"
)


def dds_header(width, height, fourcc):
    head = bytearray(128)
    head[0:4] = b"DDS "
    struct.pack_into("<I", head, 4, 124)
    struct.pack_into("<I", head, 12, height)
    struct.pack_into("<I", head, 16, width)
    head[84:88] = fourcc
    return bytes(head)


class RemapTests(unittest.TestCase):
    def test_parse_materials(self):
        mats = bmg.parse_materials(ANB)
        self.assertEqual([m["id"] for m in mats], ["rock", "grass"])
        self.assertEqual(mats[0]["diffuse"], "rock_diffuse.dds")
        self.assertEqual(mats[1]["material"], "grass_properties.dds")

    def test_remap_changes_only_texture_lines(self):
        out = bmg.remap_materials(ANB, RIE, {"rock": "hard"})
        old, new = ANB.splitlines(), out.splitlines()
        self.assertEqual(len(old), len(new))
        changed = [(a, b) for a, b in zip(old, new) if a != b]
        self.assertEqual(len(changed), 3)
        for _, b in changed:
            self.assertTrue(b.endswith("# Anbennar Overhaul"), b)
        text = "\n".join(b for _, b in changed)
        self.assertIn('"hard_diffuse.dds"', text)
        self.assertIn('"desert_cracked_normal.dds"', text)
        self.assertIn('"hard_properties.dds"', text)
        for keep in ('name     = "Rock"', 'id       = "rock"', 'mask     = "masks/rock_mask.png"',
                     "tile_factor = 3", 'id       = "grass"'):
            self.assertIn(keep, out)
        self.assertLess(out.index('"rock"'), out.index('"grass"'))

    def test_remap_unknown_ids_raise(self):
        with self.assertRaisesRegex(GeneratorError, "nope_anb"):
            bmg.remap_materials(ANB, RIE, {"nope_anb": "hard"})
        with self.assertRaisesRegex(GeneratorError, "nope_rie"):
            bmg.remap_materials(ANB, RIE, {"rock": "nope_rie"})


class SourcesTests(unittest.TestCase):
    def test_terrain_sources_skip_vanilla_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            rie, game = Path(tmp, "rie"), Path(tmp, "game")
            rie.mkdir()
            game.mkdir()
            for name in ("hard_diffuse.dds", "hard_properties.dds"):
                (rie / name).write_bytes(b"x")
            (game / "desert_cracked_normal.dds").write_bytes(b"y")
            got = bmg.terrain_sources(RIE, {"rock": "hard"}, rie, game)
            self.assertEqual(sorted(got), ["hard_diffuse.dds", "hard_properties.dds"])
            self.assertEqual(got["hard_diffuse.dds"], rie / "hard_diffuse.dds")

    def test_terrain_sources_missing_texture_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            rie, game = Path(tmp, "rie"), Path(tmp, "game")
            rie.mkdir()
            game.mkdir()
            with self.assertRaisesRegex(GeneratorError, "hard_diffuse.dds"):
                bmg.terrain_sources(RIE, {"rock": "hard"}, rie, game)

    def test_dds_info_reads_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "a.dds")
            path.write_bytes(dds_header(1024, 1024, b"DXT5"))
            self.assertEqual(bmg.dds_info(path), (1024, 1024, "DXT5"))


class BuildAllTests(unittest.TestCase):
    def test_missing_rie_raises_before_building(self):
        roots = bmg.Roots(rie=Path("Z:/no/such/rie"), anbennar=Path("Z:/no/anb"), game=Path("Z:/no/game"))
        with self.assertRaisesRegex(GeneratorError, r"no.such.rie"):
            bmg.build_all(roots)

    def test_merge_conflict_raises(self):
        bmg.merge_parts([{"a": b"1"}, {"a": b"1"}])
        with self.assertRaisesRegex(GeneratorError, "a"):
            bmg.merge_parts([{"a": b"1"}, {"a": b"2"}])


ROOTS = bmg.Roots.default()
INSTALLED = ROOTS.rie.is_dir() and (ROOTS.anbennar / "gfx/map/terrain/materials.settings").is_file()


@unittest.skipUnless(INSTALLED, "RiE and Anbennar are not installed")
class RealFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.anb = (ROOTS.anbennar / "gfx/map/terrain/materials.settings").read_text(encoding="utf-8")
        cls.rie = (ROOTS.rie / "gfx/map/terrain/materials.settings").read_text(encoding="utf-8")

    def test_map_keys_and_values_exist(self):
        anb_ids = {m["id"] for m in bmg.parse_materials(self.anb)}
        rie_ids = {m["id"] for m in bmg.parse_materials(self.rie)}
        for key, value in data.TEXTURE_MAP.items():
            self.assertIn(key, anb_ids)
            self.assertIn(value, rie_ids)

    def test_copied_textures_are_1024_dxt5(self):
        files = bmg.build_terrain(ROOTS)
        textures = {k: v for k, v in files.items() if k.endswith(".dds")}
        self.assertTrue(textures)
        for rel, content in textures.items():
            if Path(rel).name in bmg.NOT_ARRAY_MEMBERS:
                continue
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp, "t.dds")
                path.write_bytes(content)
                self.assertEqual(bmg.dds_info(path), (1024, 1024, "DXT5"), rel)

    def test_drop_ins_exist_in_game(self):
        for name in data.DROP_INS:
            self.assertTrue((ROOTS.game_terrain / name).is_file(), name)

    def test_materials_settings_differs_only_in_header_and_mapped_lines(self):
        out = bmg.build_terrain(ROOTS)["gfx/map/terrain/materials.settings"].decode("utf-8")
        old, new = self.anb.splitlines(), out.splitlines()
        header = len(bmg.HEADER("gfx/map/terrain/materials.settings"))
        self.assertEqual(len(new), len(old) + header)
        changed = [b for a, b in zip(old, new[header:]) if a != b]
        self.assertEqual(len(changed), 3 * len(data.TEXTURE_MAP))
        self.assertTrue(all(c.endswith("# Anbennar Overhaul") for c in changed))


if __name__ == "__main__":
    unittest.main()
