import math
import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_map_graphics as bmg  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
import dwarven_mountains as dm  # noqa: E402
import heightpack as hp  # noqa: E402
import pngio  # noqa: E402
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
        out = bmg.skybox_transform(self.LINE, (8192, 4096))
        self.assertTrue(out.startswith('transform="') and out.endswith('\n"'))
        values = [float(v) for v in out[len('transform="'):-2].split()]
        self.assertEqual(values[:3], [4096.0, 1.743652, 2048.0])
        self.assertEqual(values[3:7], [0.0, 0.0, 0.0, 1.0])
        self.assertEqual(values[7:9], [10000.0, 1000.0])
        self.assertEqual(values[9], 7000.0)  # RiE's depth scale is kept

    def test_skybox_transform_rejects_other_lines(self):
        with self.assertRaises(GeneratorError):
            bmg.skybox_transform("name=x", (1, 1))

    def test_snow_settings(self):
        text = '"A" = 1\n"Texture_Index" = 54\t\t\t# Index of snow\n"B" = 54\n'
        out = bmg.snow_settings(text, 7)
        self.assertEqual(out, '"A" = 1\n"Texture_Index" = 7\t\t\t# Index of snow # Anbennar Overhaul\n"B" = 54\n')
        with self.assertRaises(GeneratorError):
            bmg.snow_settings('"A" = 1\n', 7)

    TILT = ("NCamera = {\n\t# note\n\tZOOM_STEPS_MIN_TILT = { 12 14 50 40 } # tail\n\tOTHER = 1\n}\n")

    def test_defines_file(self):
        out = bmg.defines_file(self.TILT).decode("utf-8")
        header = "".join(line + "\n" for line in bmg.HEADER(bmg.DEFINES_REL))
        self.assertEqual(out, "﻿" + header
                         + "NCamera = {\n\tZOOM_STEPS_MIN_TILT = { 12 14 50 40 }\n}\n")

    def test_defines_file_without_the_line_raises(self):
        with self.assertRaisesRegex(GeneratorError, "ZOOM_STEPS_MIN_TILT"):
            bmg.defines_file("NCamera = {\n\t# ZOOM_STEPS_MIN_TILT = { 1 }\n}\n")

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


TITLES = """# e_old = { k_gone = { } }
e_one = {
	color = { 1 2 3 }
	k_a = {
		d_x = { c_x = { b_x = { province = 1 } b_y = { province = 2 } } }
	}
	k_b = { # note {
		d_y = { c_y = { b_z = { province = 3 } } }
	}
}
e_two = {
	k_c = { d_z = { c_z = { b_w = { province = 4 } } } }
}
"""

VOLUMES = (
    "##reload\r\n"
    "posteffect_values = {\r\n\tname = standard\r\n}\r\n"
    "posteffect_volumes = {\r\n\tposteffect_height_volume = {\r\n\t\tname = \"flat\"\r\n\t}\r\n}\r\n"
    "#posteffect_volume = {\r\n#\tname = \"north\"\r\n#}\r\n"
    "posteffect_volume = {\r\n\tname = \"FarNorth\"\r\n\tsize = { 1.0 2.0 3.0 }\r\n}\r\n"
    "# posteffect_volume = {\r\n# \tname = \"Forodwaith\"\r\n# }\r\n"
    "posteffect_volume = {\r\n\tname = \"UtterSouth\"\r\n}"
)


class GradingUnitTests(unittest.TestCase):
    def test_title_block(self):
        block = bmg.title_block(TITLES, "k_b")
        self.assertTrue(block.startswith("k_b = {") and "province = 3" in block and "province = 4" not in block)
        with self.assertRaises(GeneratorError):
            bmg.title_block(TITLES, "k_gone")  # only in a comment
        with self.assertRaises(GeneratorError):
            bmg.title_block(TITLES + "k_a = { }\n", "k_a")

    def test_kingdoms_and_provinces(self):
        self.assertEqual(bmg.kingdoms_of(TITLES, "e_one"), ["k_a", "k_b"])
        self.assertEqual(bmg.provinces_of(TITLES, "k_a"), [1, 2])
        self.assertEqual(bmg.provinces_of(TITLES, "e_two"), [4])

    def test_locator_positions(self):
        text = ("game_object_locator={\n\tinstances={\n\t\t{\n\t\t\tid=1\n\t\t\tposition={ 1145.000000 0.000000 "
                "2440.500000 }\n\t\t\trotation={ 0 0 0 1 }\n\t\t}\n\t\t{\n\t\t\tid=22\n\t\t\tposition={ 3.0 0.0 4.0 }\n"
                "\t\t}\n\t}\n}\n")
        self.assertEqual(bmg.locator_positions(text), {1: (1145.0, 2440.5), 22: (3.0, 4.0)})

    def test_graded_kingdoms(self):
        self.assertEqual(bmg.graded_kingdoms({"e_one": "desert", "e_two": "arid"}, TITLES),
                         {"k_a": "desert", "k_b": "desert", "k_c": "arid"})
        self.assertEqual(bmg.graded_kingdoms({"e_one": "desert", "k_b": "arid"}, TITLES),
                         {"k_a": "desert", "k_b": "arid"})
        self.assertEqual(bmg.graded_kingdoms({"e_one": "desert", "k_b": None}, TITLES), {"k_a": "desert"})

    def test_duchies_of(self):
        self.assertEqual(bmg.duchies_of(TITLES, "k_a"), ["d_x"])
        self.assertEqual(bmg.duchies_of(TITLES, "k_b"), ["d_y"])

    POSITIONS = {1: (100.0, 200.0), 2: (300.0, 260.0), 3: (1000.0, 1000.0), 4: (50.0, 50.0)}

    def test_grading_boxes_one_per_duchy(self):
        boxes, notes = bmg.grading_boxes(TITLES, self.POSITIONS, {"e_one": "desert", "k_b": "arid"}, {}, 60)
        self.assertEqual(boxes, [("d_x", "desert", (40.0, 360.0, 140.0, 320.0)),
                                 ("d_y", "arid", (940.0, 1060.0, 940.0, 1060.0))])
        self.assertEqual(notes, [])

    def test_grading_boxes_honour_skip_table(self):
        boxes, notes = bmg.grading_boxes(TITLES, self.POSITIONS, {"e_one": "desert"}, {2: "far away"}, 60)
        self.assertEqual(boxes[0], ("d_x", "desert", (40.0, 160.0, 140.0, 260.0)))
        boxes, notes = bmg.grading_boxes(TITLES, self.POSITIONS, {"e_one": "desert"}, {1: "x", 2: "y"}, 60)
        self.assertEqual([b[0] for b in boxes], ["d_y"])
        self.assertTrue(any("d_x" in note and "no provinces" in note for note in notes), notes)

    def test_grading_boxes_note_missing_locators(self):
        boxes, notes = bmg.grading_boxes(TITLES, {1: (1.0, 2.0)}, {"e_one": "desert"}, {}, 10)
        self.assertEqual([b[0] for b in boxes], ["d_x"])
        self.assertTrue(any("province" in note and "2" in note for note in notes), notes)
        self.assertTrue(any("d_y" in note for note in notes), notes)

    def test_fade_distance(self):
        self.assertEqual(bmg.fade_distance((0, 1000, 0, 800), 300, 0.25), 200.0)
        self.assertEqual(bmg.fade_distance((0, 4000, 0, 3000), 300, 0.25), 300)
        self.assertEqual(bmg.fade_distance((0, 120, 0, 2000), 300, 0.25), 30.0)

    def test_box_overlaps(self):
        boxes = [("a", "desert", (0, 100, 0, 100)), ("b", "arid", (50, 150, 0, 100)),
                 ("c", "desert", (50, 150, 0, 100)), ("e", "arid", (500, 600, 0, 100))]
        found = bmg.box_overlaps(boxes, 0.25)
        # a-c share a grade and b-c overlap fully but differ in grade; e overlaps nothing
        self.assertEqual([(a, b, round(share, 2)) for a, _, b, _, share in found],
                         [("b", "c", 1.0), ("a", "b", 0.5)])
        self.assertEqual(bmg.box_overlaps(boxes, 0.6)[0][:4], ("b", "arid", "c", "desert"))
        self.assertEqual(len(bmg.box_overlaps(boxes, 0.6)), 1)
        self.assertEqual(bmg.overlap_notes(boxes, 0.6), ["b (arid) and c (desert) overlap by 100% of the smaller box"])

    def test_volume_block(self):
        block = bmg.volume_block("k_x", "desert", bmg.grading_box([(100, 200), (300, 260)], 60), 45)
        self.assertIn('name = "k_x"', block)
        self.assertIn("posteffect_values_day = desert", block)
        self.assertIn("posteffect_values_night = desert", block)
        self.assertIn("position = { 200.0 400.0 230.0 }", block)
        self.assertIn("size = { 320.0 1600.0 180.0 }", block)
        self.assertIn("fade_distance = 45.0", block)
        self.assertRegex(block, r"position = \{ \d+\.\d \d+\.\d \d+\.\d \}")

    def test_volume_block_has_no_float_noise(self):
        block = bmg.volume_block("k_x", "arid", bmg.grading_box([(0.1 + 0.2, 1 / 3)], 60.1), 0.1 + 0.2)
        self.assertIn("fade_distance = 0.3\n", block)
        for number in re.findall(r"-?\d+\.\d+", block):
            self.assertRegex(number, r"^-?\d+\.\d$")
        self.assertTrue(block.startswith("posteffect_volume = {") and block.rstrip().endswith("}"))

    def test_posteffect_volumes(self):
        boxes = bmg.volume_block("k_x", "desert", bmg.grading_box([(100, 200)], 60), 120)
        out = bmg.posteffect_volumes(VOLUMES, boxes)
        self.assertIn("posteffect_values = {\r\n\tname = standard\r\n}", out)
        self.assertIn("posteffect_height_volume", out)
        self.assertIn("#posteffect_volume = {\r\n#\tname = \"north\"", out)
        self.assertIn("# posteffect_volume = {\r\n# \tname = \"Forodwaith\"", out)
        self.assertNotIn("FarNorth", out)
        self.assertNotIn("UtterSouth", out)
        self.assertIn('name = "k_x"', out)
        self.assertEqual(out.count("\n"), out.count("\r\n"))
        self.assertTrue(out.endswith("\r\n"))


ROOTS = bmg.Roots.default()
MOD = Path(__file__).resolve().parents[2]
INSTALLED = ROOTS.rie.is_dir() and (ROOTS.anbennar / "gfx/map/terrain/materials.settings").is_file()
_BUILD = []


def real_build():
    """(files, notes) of one build_all on the installed mods, shared by every real-data test (about a minute)."""
    if not _BUILD:
        notes = []
        _BUILD.append((bmg.build_all(ROOTS, notes), notes))
    return _BUILD[0]


@unittest.skipUnless(INSTALLED, "RiE and Anbennar are not installed")
class RealFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.anb = (ROOTS.anbennar / "gfx/map/terrain/materials.settings").read_text(encoding="utf-8")
        cls.rie = (ROOTS.rie / "gfx/map/terrain/materials.settings").read_text(encoding="utf-8")

    def test_terrain_gaps_filled(self):
        """Anbennar's blend maps have unpainted pixels (drawn black); the build fills every one, large gaps with
        TERRAIN_FILL_MATERIAL at its position in Anbennar's material list (the terrain texture-array index)."""
        from array import array
        import terrain_fill as tfill
        files, notes = real_build()
        index = tfill.read_tga(files["gfx/map/terrain/detail_index.tga"])
        intensity = tfill.read_tga(files["gfx/map/terrain/detail_intensity.tga"])
        self.assertNotIn(0, array("I", intensity.pixels))
        position = [m["id"] for m in bmg.parse_materials(self.anb)].index(data.TERRAIN_FILL_MATERIAL)
        self.assertEqual(bmg.terrain_fill_index(self.anb), position)
        full = struct.unpack("<I", bytes((255, 0, 0, 0)))[0]
        filled = array("I", index.pixels)
        weights = array("I", intensity.pixels)
        self.assertTrue(any(w == full and filled[i] == position for i, w in enumerate(weights)))
        self.assertTrue(any(n.startswith("terrain gaps filled:") for n in notes))

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
        checked = bmg.defined_symbols(rie_masks) & set(bmg.IDENTIFIER.findall(snow))
        self.assertIn("GetWinterSeverityValue", checked)
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
        self.assertIn("7000.000000", sky)
        self.assertTrue(sky.startswith("﻿" + bmg.HEADER("gfx/map/map_object_data/SKYX_skybox.txt")[0]))

    def test_defines_file_real(self):
        out = bmg.build_environment(ROOTS)[bmg.DEFINES_REL].decode("utf-8")
        rie = (ROOTS.rie / bmg.RIE_DEFINES_REL).read_text(encoding="utf-8")
        line = re.search(r"(?m)^\s*(ZOOM_STEPS_MIN_TILT.*?\})", rie).group(1)
        self.assertTrue(out.startswith("﻿" + bmg.HEADER(bmg.DEFINES_REL)[0]))
        self.assertTrue(out.endswith("NCamera = {\n\t" + line + "\n}\n"), out)
        self.assertNotIn("\r", out)

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
        files = real_build()[0]
        for ref in ("gfx/map/environment/skybox.dds", "gfx/map/environment/gh_snow_layer_1.dds",
                    "gfx/map/fog_of_war/cloud.dds", "gfx/map/environment/snow.settings",
                    "gfx/map/map_object_data/SKYX_skybox.txt", "gfx/map/water/water.settings"):
            self.assertIn(ref, files)

    # Pairs of different-grade duchy boxes that overlap by more than half of the smaller box on today's data. They
    # are reported in the generator's notes; a new pair appearing here is a regression to look at.
    KNOWN_HEAVY_OVERLAPS = {("d_ardu", "d_hasr"), ("d_masusopot", "d_sad_sur"), ("d_ardu", "d_eduz_vacyn")}

    def test_grading_real(self):
        files, notes = bmg.build_grading(ROOTS)
        titles = bmg.titles_text(ROOTS)
        volumes = files["gfx/map/post_effects/posteffect_volumes.txt"].decode("utf-8")
        names = re.findall(r'(?m)^posteffect_volume = \{\s*name = "(\w+)"', volumes)
        graded = bmg.graded_kingdoms(data.GRADING, titles)
        duchies = {d: k for k in graded for d in bmg.duchies_of(titles, k)}
        self.assertEqual(sorted(names), sorted(duchies))
        self.assertTrue(all(name.startswith("d_") for name in names))
        positions = bmg.locator_positions(_read(ROOTS.anbennar / "gfx/map/map_object_data/building_locators.txt"))
        for empire in re.findall(r"(?m)^e_\w+(?= = \{)", titles):
            if empire not in data.GRADING:
                for kingdom in bmg.kingdoms_of(titles, empire):
                    self.assertNotIn(kingdom, duchies.values())
        for empire in ("e_middle_dwarovar", "e_deepwoods", "e_dragon_coast"):
            self.assertTrue(bmg.kingdoms_of(titles, empire), empire)
        for duchy in names:
            volume = re.search(r'posteffect_volume = \{\s*name = "%s".*?position = \{ ([\d. ]+) \}.*?size = '
                               r'\{ ([\d. ]+) \}.*?fade_distance = ([\d.]+)' % duchy, volumes, re.S)
            cx, _, cy = (float(v) for v in volume.group(1).split())
            w, _, h = (float(v) for v in volume.group(2).split())
            self.assertAlmostEqual(float(volume.group(3)), min(300.0, 0.25 * min(w, h)), delta=0.06, msg=duchy)
            for province in bmg.provinces_of(titles, duchy):
                if province in positions and province not in data.GRADING_SKIP_PROVINCES:
                    x, y = positions[province]
                    self.assertTrue(abs(x - cx) <= w / 2 + 0.06 and abs(y - cy) <= h / 2 + 0.06, f"{duchy} {province}")
        self.assertTrue(any("k_the_reach" in note for note in notes), notes)
        for number in re.findall(r"(?m)^\s*(?:position|size) = \{ ([\d. ]+) \}|fade_distance = ([\d.]+)",
                                   volumes[volumes.index('name = "%s"' % names[0]):]):
            for value in number:
                for token in value.split():
                    self.assertRegex(token, r"^\d+\.\d$")
        luts = re.findall(r'lut = "([^"]+)"', volumes)
        self.assertTrue(luts)
        for lut in luts:
            self.assertIn(lut, files)
            self.assertEqual(files[lut], (ROOTS.rie / lut).read_bytes())

    def test_grading_skip_table_and_overlaps_real(self):
        titles = bmg.titles_text(ROOTS)
        for province in data.GRADING_SKIP_PROVINCES:
            self.assertTrue(any(province in bmg.provinces_of(titles, k) for k in
                                (k for e in data.GRADING if e.startswith("e_") for k in bmg.kingdoms_of(titles, e))),
                            province)
        positions = bmg.locator_positions(_read(ROOTS.anbennar / "gfx/map/map_object_data/building_locators.txt"))
        boxes, _ = bmg.grading_boxes(titles, positions, data.GRADING, data.GRADING_SKIP_PROVINCES, data.GRADING_MARGIN)
        heavy = {(a, b) for a, _, b, _, share in bmg.box_overlaps(boxes, 0.5)}
        self.assertEqual(heavy, self.KNOWN_HEAVY_OVERLAPS)
        _, notes = bmg.build_grading(ROOTS)
        self.assertEqual(sum("overlap by" in note for note in notes), len(bmg.box_overlaps(boxes, data.GRADING_OVERLAP_NOTE)))

    def test_grading_empires_exist(self):
        titles = bmg.titles_text(ROOTS)
        for empire in data.GRADING:
            self.assertTrue(bmg.kingdoms_of(titles, empire), empire)

    def test_build_all_has_grading(self):
        files, notes = real_build()
        self.assertIn("gfx/map/post_effects/posteffect_volumes.txt", files)
        self.assertTrue(notes)

    def test_generated_files_are_fresh(self):
        files = real_build()[0]
        stale = [rel for rel, data_ in files.items()
                 if not (MOD / rel).is_file() or (MOD / rel).read_bytes() != data_]
        self.assertEqual(stale, [], "rerun python -I tools/build_map_graphics.py")


def _effect(name, vs="VS_standard", ps="PS_noop"):
    return f'Effect {name}\n{{\n\tVertexShader = "{vs}"\n\tPixelShader = "{ps}"\n}}\n\n'


COURT_ANB = ('Includes = {\n}\nMainCode VS_standard\n{\n}\nMainCode PS_noop\n{\n}\n\n'
             + _effect("have_one") + _effect("have_two")
             + 'Effect real\n{\n\tVertexShader = "VS_standard"\n\tPixelShader = "PS_standard"\n}\n')
COURT_RIE = (_effect("have_one") + _effect("new_one") + _effect("real_rie", ps="PS_standard") + _effect("new_two")
             + 'Effect with_defines\n{\n\tVertexShader = "VS_standard"\n\tPixelShader = "PS_noop"\n'
             '\tDefines = { "X" }\n}\n')


class CourtSceneTests(unittest.TestCase):
    def test_appends_only_missing_placeholders(self):
        out = bmg.court_scene_override(COURT_ANB, COURT_RIE, required=("new_one",))
        self.assertTrue(out.startswith(COURT_ANB))
        tail = out[len(COURT_ANB):]
        self.assertIn(bmg.MARKER, tail)
        self.assertEqual(re.findall(r"^Effect (\w+)", tail, re.M), ["new_one", "new_two"])
        self.assertIn(_effect("new_one").strip(), tail)
        self.assertIn(_effect("new_two").strip(), tail)
        self.assertNotIn("real_rie", tail)
        self.assertNotIn("with_defines", tail)
        self.assertNotIn("have_one", tail)

    def test_needs_the_main_codes(self):
        for missing in ("MainCode VS_standard", "MainCode PS_noop"):
            with self.assertRaisesRegex(GeneratorError, missing):
                bmg.court_scene_override(COURT_ANB.replace(missing, "MainCode Other"), COURT_RIE,
                                         required=("new_one",))

    def test_required_effect_must_end_up_defined(self):
        with self.assertRaisesRegex(GeneratorError, "standard_colormap"):
            bmg.court_scene_override(COURT_ANB, COURT_RIE)
        bmg.court_scene_override(COURT_ANB, COURT_RIE, required=("have_one",))  # defined by Anbennar: fine

    def test_copied_blocks_take_the_line_endings_of_anbennars_file(self):
        out = bmg.court_scene_override(COURT_ANB, COURT_RIE.replace("\n", "\r\n"), required=("new_one",))
        self.assertNotIn("\r", out)
        self.assertIn(_effect("new_one").strip(), out)

    def test_crlf_text_is_kept(self):
        anb = COURT_ANB.replace("\n", "\r\n")
        out = bmg.court_scene_override(anb, COURT_RIE.replace("\n", "\r\n"), required=("new_one",))
        self.assertTrue(out.startswith(anb))
        self.assertEqual(out.count("\r\n"), out.count("\n"))


@unittest.skipUnless(INSTALLED, "RiE and Anbennar are not installed")
class CourtSceneRealTests(unittest.TestCase):
    def test_output_extends_anbennars_file_with_the_gate_effects(self):
        files = real_build()[0]
        out = files["gfx/FX/court_scene.shader"]
        anb = (ROOTS.anbennar / "gfx/FX/court_scene.shader").read_bytes()
        self.assertTrue(out.startswith(anb))
        self.assertGreater(len(out), len(anb))
        text = out.decode("utf-8")
        for name in ("standard_winter_mapobject", "standard_winter_selection_mapobject", "standard_colormap",
                     "standard_colormap_mapobject"):
            self.assertRegex(text, rf"(?m)^Effect {name}\s*$")


class GateObjectsTests(unittest.TestCase):
    SITES = [dm.GateSite("c_b", "c_x", 100, 200, (0.0, 1.0)), dm.GateSite("c_a", "c_y", 300, 50, (-1.0, 0.0))]

    def transforms(self, *args):
        text = bmg.gate_objects(self.SITES, *args)
        body = re.search(r'transform="([^"]*)', text).group(1)
        return text, [line.split() for line in body.split("\n") if line.strip()]

    def test_block_layout(self):
        text, lines = self.transforms(0.7, 0.0)
        for needle in ('name="aov_dwarven_gates"', "render_pass=Map", "clamp_to_water_level=no",
                       "generated_content=no", 'layer="temp_layer"', 'pdxmesh="erebor_gate_mesh"', "count=2"):
            self.assertIn(needle, text)
        self.assertEqual(len(lines), 2)

    def test_transforms_sorted_by_county_keys_with_six_decimals(self):
        _, lines = self.transforms(0.7, 0.0)
        self.assertEqual(lines[0][:3], ["300.000000", "0.000000", "50.000000"])  # c_a sorts before c_b
        self.assertEqual(lines[0][7:], ["0.700000"] * 3)
        for token in lines[0] + lines[1]:
            self.assertRegex(token, r"^-?\d+\.\d{6}$")

    def test_local_z_points_along_inward(self):
        # inward (0, 1): t = atan2(0, 1) = 0, quaternion (0, 0, 0, 1): local +Z (into the mountain) = inward
        _, lines = self.transforms(1.0, 0.0)
        line = lines[1]
        self.assertEqual([float(v) for v in line[3:7]], [0.0, 0.0, 0.0, 1.0])

    def test_yaw_for_inward_along_x(self):
        # inward (1, 0): t = atan2(1, 0) = pi/2
        sites = [dm.GateSite("c_a", "c_y", 300, 50, (1.0, 0.0))]
        text = bmg.gate_objects(sites, 1.0, 0.0)
        line = re.search(r'transform="([^"]*)', text).group(1).split()
        self.assertAlmostEqual(2 * math.atan2(float(line[4]), float(line[6])), math.pi / 2, places=5)

    def test_yaw_offset_is_added(self):
        _, lines = self.transforms(1.0, 0.5)
        line = lines[1]
        self.assertAlmostEqual(math.sin(0.5 / 2), float(line[4]), places=5)
        self.assertAlmostEqual(math.cos(0.5 / 2), float(line[6]), places=5)

    def test_inset_moves_the_gate_toward_the_mountain(self):
        _, lines = self.transforms(1.0, 0.0, 2.0)
        self.assertEqual(lines[0][:3], ["298.000000", "0.000000", "50.000000"])  # inward (-1, 0)

    def with_overrides(self, overrides):
        text = bmg.gate_objects(self.SITES, 1.0, 0.0, 2.0, overrides)
        body = re.search(r'transform="([^"]*)', text).group(1)
        return [line.split() for line in body.split("\n") if line.strip()]

    def test_override_scale_yaw_inset_and_offsets_apply_to_one_gate(self):
        lines = self.with_overrides({("c_a", "c_y"): {"scale": 3.0, "inset": 5.0, "dx": 1.5, "dy": -2.0, "yaw": 0.5}})
        a, b = lines  # c_a first; inward (-1, 0)
        self.assertEqual(a[:3], ["296.500000", "0.000000", "48.000000"])  # 300 - 5 + 1.5, 50 - 2
        self.assertEqual(a[7:], ["3.000000"] * 3)
        t = math.atan2(-1.0, 0.0) + 0.5
        self.assertAlmostEqual(float(a[4]), math.sin(t / 2), places=5)
        self.assertAlmostEqual(float(a[6]), math.cos(t / 2), places=5)
        self.assertEqual(b[:3], ["100.000000", "0.000000", "202.000000"])  # untouched: default inset 2 along (0, 1)
        self.assertEqual(b[7:], ["1.000000"] * 3)

    def test_gate_position_is_shared_with_the_terrain_shoulder(self):
        overrides = {("c_a", "c_y"): {"dx": 1.5, "dy": -2.0, "inset": 5.0}}
        text = bmg.gate_objects(self.SITES, 1.0, 0.0, 2.0, overrides)
        body = re.search(r'transform="([^"]*)', text).group(1)
        lines = [line.split() for line in body.split("\n") if line.strip()]
        placed = {s.dwarven_county: pos for s, pos in dm.gate_placements(self.SITES, 2.0, overrides)}
        for line, county in zip(lines, ("c_a", "c_b")):
            self.assertAlmostEqual(float(line[0]), placed[county][0], places=5)
            self.assertAlmostEqual(float(line[2]), placed[county][1], places=5)

    def test_override_with_a_single_key_leaves_the_rest_default(self):
        a, _ = self.with_overrides({("c_a", "c_y"): {"scale": 2.0}})
        self.assertEqual(a[:3], ["298.000000", "0.000000", "50.000000"])
        self.assertEqual(a[7:], ["2.000000"] * 3)

    def test_unknown_override_key_raises(self):
        with self.assertRaisesRegex(GeneratorError, "c_nope.*c_y|GATE_OVERRIDES"):
            bmg.gate_objects(self.SITES, 1.0, 0.0, 0.0, {("c_nope", "c_y"): {"scale": 2.0}})

    def test_unknown_override_option_raises(self):
        with self.assertRaisesRegex(GeneratorError, "scaleX"):
            bmg.gate_objects(self.SITES, 1.0, 0.0, 0.0, {("c_a", "c_y"): {"scaleX": 2.0}})

    def test_data_defaults(self):
        self.assertEqual((data.GATE_SCALE, data.GATE_INSET), (1.6, 2.0))
        self.assertEqual(data.SEA_GATES, ("c_ovdal_tungr",))
        self.assertIsInstance(data.GATE_OVERRIDES, dict)
        for key in ("GATE_PAD", "GATE_RISE", "GATE_RISE_DIST", "GATE_SKIRT"):
            self.assertFalse(hasattr(data, key), key)


def _blocks(text):
    """{object name: (pdxmesh, count, [transform value lists])} of a map object text."""
    found = {}
    for block in re.findall(r"object=\{.*?\}\n", text, re.S):
        name = re.search(r'name="([^"]+)"', block).group(1)
        body = re.search(r'transform="([^"]*)', block).group(1)
        lines = [[float(v) for v in line.split()] for line in body.split("\n") if line.strip()]
        found[name] = (re.search(r'pdxmesh="([^"]+)"', block).group(1), int(re.search(r"count=(\d+)", block).group(1)),
                       lines)
    return found


LAYOUT = [{"piece": "mountain_05", "t": 5, "l": 0, "yaw": 0.0, "sx": 0.6, "sy": 4.0, "sz": 0.6},
          {"piece": "mountain_03", "t": 2, "l": -7, "yaw": 0.6, "sx": 0.45, "sy": 3.0, "sz": 0.45}]


class MoriaGateTests(unittest.TestCase):
    SITES = [dm.GateSite("c_a", "c_y", 300, 50, (0.0, 1.0)), dm.GateSite("c_b", "c_x", 100, 200, (1.0, 0.0))]

    def test_mesh_override_makes_a_second_block(self):
        text = bmg.gate_objects(self.SITES, 1.6, 0.0, 0.0, {("c_b", "c_x"): {"mesh": "moriaeast_mesh", "scale": 4.8}})
        blocks = _blocks(text)
        self.assertEqual(len(blocks), 2)
        mesh, count, lines = blocks["aov_dwarven_gates"]
        self.assertEqual((mesh, count, len(lines)), ("erebor_gate_mesh", 1, 1))
        self.assertEqual(lines[0][:3], [300.0, 0.0, 50.0])
        mesh, count, lines = blocks["aov_dwarven_gates_moriaeast"]
        self.assertEqual((mesh, count, len(lines)), ("moriaeast_mesh", 1, 1))
        self.assertEqual(lines[0][:3], [100.0, 0.0, 200.0])
        self.assertEqual(lines[0][7:], [4.8] * 3)

    def test_unknown_mesh_raises(self):
        with self.assertRaisesRegex(GeneratorError, "nope_mesh"):
            bmg.gate_objects(self.SITES, 1.6, 0.0, 0.0, {("c_a", "c_y"): {"mesh": "nope_mesh"}})

    def test_all_default_gates_stay_one_block(self):
        self.assertEqual(list(_blocks(bmg.gate_objects(self.SITES, 1.6, 0.0))), ["aov_dwarven_gates"])


class OverlayTests(unittest.TestCase):
    NORTH = dm.GateSite("c_a", "c_y", 300, 50, (0.0, 1.0))  # t = 0
    EAST = dm.GateSite("c_b", "c_x", 100, 200, (1.0, 0.0))  # t = pi/2

    def overlays(self, sites, layout=LAYOUT, overrides=None, gate_overrides=None, scale=1.6, inset=0.0):
        text = bmg.overlay_objects(sites, scale, 0.0, inset, gate_overrides, layout, overrides)
        return _blocks(text)

    def test_one_block_per_piece_type_with_the_prefixed_mesh(self):
        blocks = self.overlays([self.NORTH, self.EAST])
        self.assertEqual(sorted(blocks), ["aov_dwarven_gate_overlay_mountain_03", "aov_dwarven_gate_overlay_mountain_05"])
        mesh, count, lines = blocks["aov_dwarven_gate_overlay_mountain_05"]
        self.assertEqual((mesh, count, len(lines)), ("aov_mountain_05_mesh", 2, 2))
        text = bmg.overlay_objects([self.NORTH], 1.6, 0.0, 0.0, None, LAYOUT)
        for needle in ("render_pass=Map", "clamp_to_water_level=no", "generated_content=no", 'layer="temp_layer"'):
            self.assertIn(needle, text)

    def test_frame_for_a_gate_facing_north(self):
        # inward (0, 1): t axis is +map y; l axis (inward_y, -inward_x) = (1, 0)
        _, _, lines = self.overlays([self.NORTH])["aov_dwarven_gate_overlay_mountain_03"]
        x, y, z = lines[0][:3]
        self.assertAlmostEqual(x, 300 - 7)
        self.assertEqual(y, 0.0)
        self.assertAlmostEqual(z, 50 + 2)
        t = 0.6
        self.assertAlmostEqual(lines[0][4], math.sin(t / 2), places=5)
        self.assertAlmostEqual(lines[0][6], math.cos(t / 2), places=5)
        self.assertEqual(lines[0][7:], [0.45, 3.0, 0.45])

    def test_frame_for_a_gate_facing_east(self):
        # inward (1, 0): t axis +map x; l axis (0, -1)
        _, _, lines = self.overlays([self.EAST])["aov_dwarven_gate_overlay_mountain_03"]
        x, _, z = lines[0][:3]
        self.assertAlmostEqual(x, 100 + 2)
        self.assertAlmostEqual(z, 200 + 7)  # l = -7 along (0, -1)
        t = math.pi / 2 + 0.6
        self.assertAlmostEqual(2 * math.atan2(lines[0][4], lines[0][6]), t, places=5)

    def test_local_x_axis_is_the_l_direction(self):
        # the mesh's local +X after the yaw t is (cos t, -sin t) in (x, z): it must equal the l axis
        for site in (self.NORTH, self.EAST, dm.GateSite("c_c", "c_z", 5, 5, (0.6, 0.8))):
            t = math.atan2(site.inward[0], site.inward[1])
            self.assertAlmostEqual(math.cos(t), site.inward[1])
            self.assertAlmostEqual(-math.sin(t), -site.inward[0])

    def test_layout_scales_with_the_gate_and_includes_heights(self):
        _, _, lines = self.overlays([self.NORTH], scale=3.2)["aov_dwarven_gate_overlay_mountain_03"]
        self.assertAlmostEqual(lines[0][0], 300 - 14)
        self.assertAlmostEqual(lines[0][2], 50 + 4)
        self.assertEqual(lines[0][7:], [0.9, 6.0, 0.9])

    def test_moria_gate_uses_its_own_base_scale(self):
        go = {("c_a", "c_y"): {"mesh": "moriaeast_mesh", "scale": 4.8}}
        _, _, lines = self.overlays([self.NORTH], gate_overrides=go)["aov_dwarven_gate_overlay_mountain_03"]
        self.assertAlmostEqual(lines[0][0], 300 - 7)
        self.assertEqual(lines[0][7:], [0.45, 3.0, 0.45])

    def test_gate_yaw_override_and_position_override_carry_over(self):
        go = {("c_a", "c_y"): {"dx": 10.0, "dy": -1.0, "yaw": 0.5}}
        _, _, lines = self.overlays([self.NORTH], gate_overrides=go)["aov_dwarven_gate_overlay_mountain_05"]
        self.assertAlmostEqual(lines[0][0], 310.0)
        self.assertAlmostEqual(lines[0][2], 50 - 1 + 5)
        self.assertAlmostEqual(2 * math.atan2(lines[0][4], lines[0][6]), 0.5, places=5)

    def test_override_replaces_or_disables_a_gate_layout(self):
        only = [{"piece": "mountain_01", "t": 1, "l": 1, "yaw": 0.0, "sx": 1.0, "sy": 1.0, "sz": 1.0}]
        blocks = self.overlays([self.NORTH, self.EAST], overrides={("c_a", "c_y"): only, ("c_b", "c_x"): None})
        self.assertEqual(sorted(blocks), ["aov_dwarven_gate_overlay_mountain_01"])
        self.assertEqual(blocks["aov_dwarven_gate_overlay_mountain_01"][1], 1)

    def test_unknown_override_key_raises(self):
        with self.assertRaisesRegex(GeneratorError, "GATE_OVERLAY_OVERRIDES"):
            self.overlays([self.NORTH], overrides={("c_nope", "c_y"): None})

    def test_bad_layout_entries_raise(self):
        with self.assertRaisesRegex(GeneratorError, "mountain_99"):
            self.overlays([self.NORTH], layout=[dict(LAYOUT[0], piece="mountain_99")])
        with self.assertRaisesRegex(GeneratorError, "sq"):
            self.overlays([self.NORTH], layout=[dict(LAYOUT[0], sq=1)])
        with self.assertRaisesRegex(GeneratorError, "sz"):
            self.overlays([self.NORTH], layout=[{k: v for k, v in LAYOUT[0].items() if k != "sz"}])

    def test_deterministic_and_sorted_by_gate(self):
        a = bmg.overlay_objects([self.EAST, self.NORTH], 1.6, 0.0, 0.0, None, LAYOUT)
        b = bmg.overlay_objects([self.NORTH, self.EAST], 1.6, 0.0, 0.0, None, LAYOUT)
        self.assertEqual(a, b)
        lines = _blocks(a)["aov_dwarven_gate_overlay_mountain_05"][2]
        self.assertEqual(lines[0][0], 300.0)  # c_a before c_b

    def test_no_layout_gives_no_text(self):
        self.assertEqual(bmg.overlay_objects([self.NORTH], 1.6, 0.0, 0.0, None, []), "")


class OverlayAssetTests(unittest.TestCase):
    ASSET = ('pdxmesh = {\n\tname = "mountain_05_mesh"\n\tfile = "mountain_05.mesh"\n\tscale = 1.5\n\n'
             '\tmeshsettings = {\n\t\tname = "mountain_05"\n\t\tshader = "snap_to_terrain_alpha_to_coverage_colormap"\n\t}\n}\n\n'
             'entity = {\n\tname = "mountain_05_entity"\n\tpdxmesh = "mountain_05_mesh"\n}\n')

    def test_only_the_names_change(self):
        out = bmg.overlay_asset(self.ASSET, "mountain_05")
        self.assertEqual(out, self.ASSET.replace('"mountain_05_mesh"', '"aov_mountain_05_mesh"')
                         .replace('"mountain_05_entity"', '"aov_mountain_05_entity"'))
        self.assertIn('file = "mountain_05.mesh"', out)
        self.assertIn('name = "mountain_05"', out)

    def test_unexpected_asset_raises(self):
        with self.assertRaisesRegex(GeneratorError, "mountain_05"):
            bmg.overlay_asset("pdxmesh = { name = \"other\" }", "mountain_05")

    def test_effect_check(self):
        shader = "Effect a_mapobject\n{\n}\nEffect b_mapobject\n{\n}\n"
        asset = 'shader = "a"\nshader = "b"\n'
        bmg.check_asset_effects({bmg.GATE_ASSET_DIR + "/x.asset": asset.encode()}, shader)
        with self.assertRaisesRegex(GeneratorError, "c_mapobject"):
            bmg.check_asset_effects({bmg.GATE_ASSET_DIR + "/x.asset": (asset + 'shader = "c"\n').encode()}, shader)


@unittest.skipUnless(INSTALLED and (ROOTS.anbennar / "map_data/provinces.png").is_file(),
                     "RiE and Anbennar are not installed")
class GateOverlayRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.notes = real_build()
        cls.folder = "gfx/models/mapitems/aov_dwarven_gate/"

    def test_twelve_gates_eleven_erebor_one_moria(self):
        blocks = _blocks(self.files["gfx/map/map_object_data/aov_dwarven_gates.txt"].decode("utf-8-sig"))
        self.assertEqual({k: (v[0], v[1]) for k, v in blocks.items()},
                         {"aov_dwarven_gates": ("erebor_gate_mesh", 11),
                          "aov_dwarven_gates_moriaeast": ("moriaeast_mesh", 1)})
        for rel in ("moriaeast.asset", "moriaeast.mesh", "moriaeast_Diffuse.dds", "moriaeast_Normal.dds",
                    "moriaeast_Properties.dds"):
            self.assertIn(self.folder + rel, self.files)
        asset = (ROOTS.rie / "gfx/models/buildings/lotr_special_buildings/dwarven_wonders/moria_east/moriaeast.asset")
        self.assertEqual(self.files[self.folder + "moriaeast.asset"], asset.read_bytes())

    def test_silverforge_moria_transform(self):
        blocks = _blocks(self.files["gfx/map/map_object_data/aov_dwarven_gates.txt"].decode("utf-8-sig"))
        line = blocks["aov_dwarven_gates_moriaeast"][2][0]
        self.assertEqual(line[7:], [4.8] * 3)
        self.assertEqual(line[1], 0.0)

    def test_overlays_for_all_twelve_gates(self):
        text = self.files["gfx/map/map_object_data/aov_dwarven_gate_overlays.txt"].decode("utf-8-sig")
        self.assertTrue(text.startswith(bmg.MARKER))
        blocks = _blocks(text)
        self.assertEqual({k: (v[0], v[1]) for k, v in blocks.items()},
                         {"aov_dwarven_gate_overlay_mountain_03": ("aov_mountain_03_mesh", 12),
                          "aov_dwarven_gate_overlay_mountain_04": ("aov_mountain_04_mesh", 12),
                          "aov_dwarven_gate_overlay_mountain_05": ("aov_mountain_05_mesh", 12)})
        for _, count, lines in blocks.values():
            self.assertEqual(count, len(lines))

    def test_overlay_assets_are_prefixed_and_have_meshes(self):
        for piece in ("mountain_03", "mountain_04", "mountain_05"):
            asset = self.files[f"{self.folder}aov_{piece}.asset"].decode("utf-8-sig")
            self.assertIn(f'name = "aov_{piece}_mesh"', asset)
            self.assertIn(f'name = "aov_{piece}_entity"', asset)
            self.assertIn(f'file = "{piece}.mesh"', asset)
            self.assertIn(self.folder + f"{piece}.mesh", self.files)
        self.assertNotIn(self.folder + "mountain_01.mesh", self.files)  # unused pieces are not copied
        self.assertNotIn(self.folder + "aov_mountain_01.asset", self.files)

    def test_every_asset_effect_has_a_mapobject_variant(self):
        shader = self.files["gfx/FX/court_scene.shader"].decode("utf-8")
        names = set(bmg.EFFECT_NAME.findall(shader))
        used = set()
        for rel, content in self.files.items():
            if rel.endswith(".asset") and rel.startswith(self.folder):
                used.update(re.findall(r'shader\s*=\s*"([^"]+)"', content.decode("utf-8-sig")))
        self.assertTrue({"standard_winter", "standard_colormap", "snap_to_terrain_alpha_to_coverage_colormap"} <= used)
        for name in used:
            self.assertIn(name + "_mapobject", names)


@unittest.skipUnless(INSTALLED and (ROOTS.anbennar / "map_data/provinces.png").is_file(),
                     "RiE and Anbennar are not installed")
class SeaGateRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pm, cls.water, cls.impassable, cls.dwarven, cls.sites = bmg._analyse(ROOTS)
        folder = ROOTS.anbennar
        cls.sea = dm.sea_zone_ids((folder / "map_data/default.map").read_text(encoding="utf-8-sig"))
        cls.titles_text = "\n".join(p.read_text(encoding="utf-8-sig")
                                    for p in sorted((folder / "common/landed_titles").glob("*.txt")))
        cls.titles = dm.province_titles(cls.titles_text)
        cls.border = dm.border_pixels(cls.pm)
        land = dm.gate_sites(cls.pm, cls.dwarven, cls.water, cls.impassable, cls.titles, cls.border,
                             data.GATE_EXCLUDE_REGIONS)
        cls.land = dm.spaced_sites(land, cls.border, cls.titles, data.GATE_MIN_SPACING)

    def test_ovdal_tungr_has_one_sea_gate_on_the_irovar_shore(self):
        ovdal = [s for s in self.sites if s.dwarven_county == "c_ovdal_tungr"]
        self.assertEqual(len(ovdal), 1)
        site = ovdal[0]
        self.assertEqual(site.normal_county, "sea")
        w = self.pm.width
        province = dm.barony_province(self.titles_text, "b_irovar")
        self.assertEqual(province, 526)
        self.assertEqual(self.pm.ids[site.y * w + site.x], province)
        touching = [self.pm.ids[ny * w + nx] for nx, ny in ((site.x + 1, site.y), (site.x - 1, site.y),
                                                            (site.x, site.y + 1), (site.x, site.y - 1))
                    if 0 <= nx < w and 0 <= ny < self.pm.height]
        self.assertTrue(any(p in self.sea for p in touching), touching)
        self.assertAlmostEqual(math.hypot(*site.inward), 1.0)

    def test_inward_points_away_from_the_sea(self):
        site = next(s for s in self.sites if s.dwarven_county == "c_ovdal_tungr")
        w = self.pm.width
        ix, iy = site.inward
        seaward = [self.pm.ids[round(site.y - k * iy) * w + round(site.x - k * ix)] for k in (3,)]
        self.assertIn(seaward[0], self.sea | {0}, f"site {site}: the pixel 3 px seaward is province {seaward[0]}")

    def test_no_land_site_remains_and_the_others_are_unchanged(self):
        self.assertTrue(any(s.dwarven_county == "c_ovdal_tungr" for s in self.land))
        self.assertEqual([s for s in self.sites if s.dwarven_county != "c_ovdal_tungr"],
                         [s for s in self.land if s.dwarven_county != "c_ovdal_tungr"])
        self.assertEqual(len(self.sites), len(self.land))


@unittest.skipUnless(INSTALLED and (ROOTS.anbennar / "map_data/provinces.png").is_file(),
                     "RiE and Anbennar are not installed")
class HeightOutputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.notes = real_build()
        anb = ROOTS.anbennar / "map_data"
        cls.settings = hp.parse_settings((anb / "heightmap.heightmap").read_text(encoding="utf-8-sig"))
        cls.anb_blocks = hp.unpack(pngio.read_png((anb / "indirection_heightmap.png").read_bytes()),
                                   hp.Grid.from_png(pngio.read_png((anb / "packed_heightmap.png").read_bytes())),
                                   cls.settings)
        cls.anb_height = hp.Grid.from_png(pngio.read_png((anb / "heightmap.png").read_bytes()))
        cls.new_settings = hp.parse_settings(cls.files["map_data/heightmap.heightmap"].decode("utf-8-sig"))
        cls.new_height = hp.Grid.from_png(pngio.read_png(cls.files["map_data/heightmap.png"]))
        cls.new_blocks = hp.unpack(pngio.read_png(cls.files["map_data/indirection_heightmap.png"]),
                                   hp.Grid.from_png(pngio.read_png(cls.files["map_data/packed_heightmap.png"])),
                                   cls.new_settings)

    def test_outputs_exist(self):
        for rel in bmg.HEIGHT_OUTPUTS:
            self.assertIn(rel, self.files)

    def test_dimensions_and_depths_match_anbennar(self):
        anb = ROOTS.anbennar / "map_data"
        for name in ("heightmap", "indirection_heightmap", "packed_heightmap"):
            old = pngio.read_png((anb / f"{name}.png").read_bytes())
            new = pngio.read_png(self.files[f"map_data/{name}.png"])
            self.assertEqual((new.bit_depth, new.color_type), (old.bit_depth, old.color_type), name)
            self.assertEqual(new.width, old.width, name)
            if name != "packed_heightmap":
                self.assertEqual(new.height, old.height, name)

    def test_settings_keep_everything_else(self):
        s, n = self.settings, self.new_settings
        self.assertEqual((n.tile_size, n.original_size, n.max_compress_level),
                         (s.tile_size, s.original_size, s.max_compress_level))

    def test_unchanged_blocks_keep_anbennars_tiles_and_changed_match_heightmap(self):
        changed = hp.changed_blocks(self.anb_height, self.new_height)
        self.assertTrue(changed)
        self.assertEqual(self.anb_blocks.keys(), self.new_blocks.keys())
        for key, anb in self.anb_blocks.items():
            block = self.new_blocks[key]
            if key not in changed:
                self.assertEqual((block.level, block.tile), (anb.level, anb.tile), key)
                continue
            full = hp.sample(self.new_height, key[0], key[1], 1)
            self.assertTrue(hp._interpolates(block.tile, 32 // block.step + 1, block.step, full, 33,
                                             data.PACK_TOLERANCE), key)

    def test_gate_count_matches_sites(self):
        text = self.files["gfx/map/map_object_data/aov_dwarven_gates.txt"].decode("utf-8")
        count = sum(int(c) for c in re.findall(r"count=(\d+)", text))
        lines = [l for body in re.findall(r'transform="([^"]*)', text) for l in body.split("\n") if l.strip()]
        self.assertEqual(count, len(lines))
        self.assertEqual(count, sum(note.startswith("gate ") for note in self.notes))
        self.assertTrue(text.lstrip("﻿").startswith(bmg.MARKER))

    def test_every_texture_the_asset_names_sits_beside_it(self):
        folder = "gfx/models/mapitems/aov_dwarven_gate/"
        asset = self.files[folder + "erebor_gate.asset"].decode("utf-8-sig")
        names = re.findall(r'(?:texture_\w+|(?<![_a-z])file)\s*=\s*"([^"]+)"', asset)
        self.assertTrue(names)
        for name in names:
            self.assertIn(folder + name, self.files)

    def test_notes_cover_ranges_and_sites(self):
        self.assertEqual(sum(note.startswith("range ") for note in self.notes), 9)
        self.assertEqual(sum(note.startswith("gate ") for note in self.notes), 12)

    def test_every_gate_has_a_gentle_shoulder(self):
        found = [re.search(r"^gate (\S+) at .*foot (\d+), shoulder max (\d+), max step (\d+) -> (\d+)", n)
                 for n in self.notes if n.startswith("gate ")]
        self.assertEqual(len(found), 12)
        for m in found:
            foot, top, before, after = (int(m.group(k)) for k in (2, 3, 4, 5))
            self.assertGreaterEqual(top, min(65535 - 1, foot + 0.8 * data.SHOULDER_RISE), m.group(0))
            # steps inside the footprint stay near what the ground had (Old Passage's three overlapping gates
            # reach 6123 against the 6000 allowance, hence the small tolerance)
            self.assertLessEqual(after, max(before, 6000) + 200, m.group(0))


def _read(path):
    return path.read_bytes().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
