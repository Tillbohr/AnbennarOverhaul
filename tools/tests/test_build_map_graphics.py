import re
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


class EnvironmentUnitTests(unittest.TestCase):
    LINE = ('transform="4104.552734 1.743652 2812.745605 0.000000 0.000000 0.000000 1.000000 10000.000000 '
            '1000.000000 7000.000000\n"')

    def test_skybox_transform(self):
        out = bmg.skybox_transform(self.LINE, (8192, 5632), (8192, 4096))
        self.assertTrue(out.startswith('transform="') and out.endswith('\n"'))
        values = [float(v) for v in out[len('transform="'):-2].split()]
        self.assertEqual(values[:3], [4096.0, 1.743652, 2048.0])
        self.assertEqual(values[3:7], [0.0, 0.0, 0.0, 1.0])
        self.assertEqual(values[7:9], [10000.0, 1000.0])
        self.assertAlmostEqual(values[9], 5090.909091, places=5)

    def test_skybox_transform_rejects_other_lines(self):
        with self.assertRaises(GeneratorError):
            bmg.skybox_transform("name=x", (1, 1), (1, 1))

    def test_snow_settings(self):
        text = '"A" = 1\n"Texture_Index" = 54\t\t\t# Index of snow\n"B" = 54\n'
        out = bmg.snow_settings(text, 7)
        self.assertEqual(out, '"A" = 1\n"Texture_Index" = 7\t\t\t# Index of snow # Anbennar Overhaul\n"B" = 54\n')
        with self.assertRaises(GeneratorError):
            bmg.snow_settings('"A" = 1\n', 7)

    def test_settings_paths(self):
        text = '"X" = "gfx/map/a.dds"\n# "gfx/map/c.dds"\ncubemap = "gfx/b.dds" # note\n"Y" = 3\n'
        self.assertEqual(bmg.settings_paths(text), ["gfx/map/a.dds", "gfx/b.dds"])

    def test_png_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "p.png")
            path.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 8192, 4096))
            self.assertEqual(bmg.png_size(path), (8192, 4096))
            path.write_bytes(b"nope")
            with self.assertRaises(GeneratorError):
                bmg.png_size(path)


class ShaderTests(unittest.TestCase):
    def test_includes_ignore_comments(self):
        text = 'Includes = {\n\t"cw/a.fxh"\n\t# "cw/b.fxh"\n\t"c.fxh" # tail\n}\nincludes = {\n\t"d.fxh"\n}\n'
        self.assertEqual(bmg.includes(text), ["cw/a.fxh", "c.fxh", "d.fxh"])

    def _tree(self, tmp, rie_files, extra=None):
        tmp = Path(tmp)
        dirs = {"rie": tmp / "rie", "anb": tmp / "anb", "engine": tmp / "engine"}
        for name, files in (("rie", rie_files), ("anb", extra or {}), ("engine", {"cw/e.fxh": ""})):
            for rel, text in files.items():
                path = dirs[name] / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
        return dirs

    def test_closure_resolves_and_walks_only_rie_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._tree(tmp, {"a.shader": 'Includes = {\n"b.fxh"\n"cw/e.fxh"\n"kept.fxh"\n}',
                                 "b.fxh": 'Includes = {\n"cw/e.fxh"\n}', "kept.fxh": 'Includes = {\n"nope.fxh"\n}'},
                            {"kept.fxh": ""})
            got = bmg.shader_closure(["a.shader"], d["rie"], [d["anb"], d["engine"]], ("kept.fxh",), ())
            self.assertEqual(sorted(got), ["a.shader", "b.fxh"])
            self.assertEqual(got["b.fxh"], d["rie"] / "b.fxh")

    def test_closure_never_and_unknown_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._tree(tmp, {"a.shader": 'Includes = {\n"gh_portrait_x.fxh"\n}', "gh_portrait_x.fxh": ""})
            with self.assertRaisesRegex(GeneratorError, "a.shader.*gh_portrait_x|gh_portrait_x.*a.shader"):
                bmg.shader_closure(["a.shader"], d["rie"], [d["anb"], d["engine"]], (), ("gh_portrait_*",))
        with tempfile.TemporaryDirectory() as tmp:
            d = self._tree(tmp, {"a.shader": 'Includes = {\n"unknown.fxh"\n}'})
            with self.assertRaisesRegex(GeneratorError, "a.shader.*unknown.fxh|unknown.fxh.*a.shader"):
                bmg.shader_closure(["a.shader"], d["rie"], [d["anb"], d["engine"]], (), ())

    def test_texture_refs(self):
        text = 'TextureSampler X\n{\n\tFile = "gfx/map/a.dds"\n\t# File = "gfx/map/c.dds"\n}\nFile="gfx/map/b.dds"'
        self.assertEqual(bmg.texture_refs(text), ["gfx/map/a.dds", "gfx/map/b.dds"])

    MASKS = ("TextureSampler SnowMaskMap\n{\n}\n#define WINTER_X 1\nstatic const float K = 1;\n"
             "float GetWinterSeverityValue( in float2 c )\n{\n\treturn 1;\n}\n")

    def test_defined_symbols(self):
        self.assertEqual(bmg.defined_symbols(self.MASKS), {"SnowMaskMap", "WINTER_X", "K", "GetWinterSeverityValue"})

    def test_missing_mask_symbols(self):
        snow = "float3 f() { return GetWinterSeverityValue(p) * K; }"
        self.assertEqual(bmg.missing_mask_symbols(snow, self.MASKS, self.MASKS), [])
        anb = self.MASKS.replace("GetWinterSeverityValue", "Renamed")
        self.assertEqual(bmg.missing_mask_symbols(snow, self.MASKS, anb), ["GetWinterSeverityValue"])


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

    def test_shader_closure_is_the_spec_set(self):
        closure = bmg.shader_closure(data.SHADER_ROOTS, ROOTS.rie / "gfx/FX", bmg.shader_search(ROOTS),
                                     data.SHADER_KEEP_ANBENNAR, data.SHADER_NEVER)
        extra = {"gh_snowfall.fxh", "gh_utils.fxh", "gh_vic3_fog_of_war.fxh", "gh_vic3_fog_of_war_settings.fxh"}
        self.assertEqual(set(closure), set(data.SHADER_ROOTS) | extra)
        self.assertEqual(len(closure), 16)

    def test_missing_mask_symbols_real(self):
        snow = (ROOTS.rie / "gfx/FX/gh_snowfall.fxh").read_text(encoding="utf-8")
        rie_masks = bmg.rie_dynamic_masks(ROOTS)
        anb_masks = (ROOTS.anbennar / "gfx/FX/dynamic_masks.fxh").read_text(encoding="utf-8")
        self.assertEqual(bmg.missing_mask_symbols(snow, rie_masks, anb_masks), [])

    def test_shader_textures_exist_and_rie_only_are_built(self):
        files = bmg.build_shaders(ROOTS)
        shaders = {k for k in files if k.startswith("gfx/FX/")}
        self.assertEqual(len(shaders), 16)
        for rel in shaders:
            for ref in bmg.texture_refs(files[rel].decode("utf-8", "replace")):
                found = any((root / ref).is_file() for root in (ROOTS.rie, ROOTS.anbennar, ROOTS.game / "game"))
                self.assertTrue(found, f"{rel}: {ref}")
                if not (ROOTS.anbennar / ref).is_file() and not (ROOTS.game / "game" / ref).is_file():
                    self.assertIn(ref, files)
        for ref in ("gfx/map/environment/skybox.dds", "gfx/map/environment/gh_snow_layer_1.dds",
                    "gfx/map/fog_of_war/cloud.dds"):
            self.assertIn(ref, files)

    def _exists(self, ref):
        return any((base / ref).is_file() for base in (ROOTS.anbennar, ROOTS.game / "game"))

    def test_snow_index_is_position_of_snow_material(self):
        ids = [m["id"] for m in bmg.parse_materials(self.anb)]
        index = ids.index("snow")
        out = bmg.build_environment(ROOTS)["gfx/map/environment/snow.settings"].decode("utf-8")
        self.assertRegex(out, r'(?m)^"Texture_Index" = %d\t+# Index of snow' % index)

    def test_environment_outputs(self):
        out = bmg.build_environment(ROOTS)
        for rel in data.COPY_FILES:
            self.assertEqual(out[rel], (ROOTS.rie / rel).read_bytes(), rel)
        sky = out["gfx/map/map_object_data/SKYX_skybox.txt"].decode("utf-8")
        self.assertIn("4096.000000 1.743652 2048.000000", sky)
        self.assertIn("5090.909091", sky)
        self.assertTrue(sky.startswith("﻿" + bmg.HEADER("gfx/map/map_object_data/SKYX_skybox.txt")[0]))

    def test_named_paths_exist(self):
        out = bmg.build_environment(ROOTS)
        for rel in ("gfx/map/environment/environment.txt", "gfx/map/water/water.settings"):
            refs = bmg.settings_paths(out[rel].decode("utf-8"))
            self.assertTrue(refs, rel)
            for ref in refs:
                self.assertTrue(self._exists(ref), f"{rel}: {ref}")
        asset = out["gfx/models/mapitems/SKYX_skybox.asset"].decode("utf-8")
        for name in re.findall(r'"([^"]+\.dds)"', asset):
            self.assertTrue(self._exists(f"gfx/models/{name}"), name)

    def test_build_all_has_environment_and_rie_only_textures(self):
        files = bmg.build_all(ROOTS)
        for ref in ("gfx/map/environment/skybox.dds", "gfx/map/environment/gh_snow_layer_1.dds",
                    "gfx/map/fog_of_war/cloud.dds", "gfx/map/environment/snow.settings",
                    "gfx/map/map_object_data/SKYX_skybox.txt", "gfx/map/water/water.settings"):
            self.assertIn(ref, files)


if __name__ == "__main__":
    unittest.main()
