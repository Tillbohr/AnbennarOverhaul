"""Tests for tools/build_holding_models.py.

    python -I -m unittest discover -s tools/tests -p test_build_holding_models.py -v
"""

import re
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_holding_models as bhm  # noqa: E402
from data import holding_models as data  # noqa: E402

FIXTURE = (
    "﻿# comment\n"
    "alpha = {\n"
    "\theritage = heritage_x\n"
    "\tbuilding_gfx = { western_building_gfx other_gfx }\n"
    "}\n"
    "\n"
    "#beta = {\n"
    "#\tbuilding_gfx = { nope }\n"
    "#}\n"
    "gamma = {\n"
    "\theritage = heritage_x\n"
    "\tbuilding_gfx = { western_building_gfx }\n"
    "}\n"
)
REAL = bhm.Roots.default()


class CultureTests(unittest.TestCase):
    def test_blocks_ignore_comments(self):
        self.assertEqual([b[0] for b in bhm.culture_blocks(FIXTURE)], ["alpha", "gamma"])

    def test_override_changes_only_target_line(self):
        out = bhm.override_culture_file(FIXTURE, {"alpha": "new_gfx"})
        old, new = FIXTURE.splitlines(), out.splitlines()
        self.assertEqual(len(old), len(new))
        diff = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
        self.assertEqual(diff, [3])
        self.assertEqual(new[3], "\tbuilding_gfx = { new_gfx western_building_gfx other_gfx } # Anbennar Overhaul")

    def test_missing_building_gfx_raises(self):
        with self.assertRaises(bhm.GeneratorError):
            bhm.override_culture_file("a = {\n\theritage = h\n}\n", {"a": "x"})

    def test_unknown_target_raises(self):
        with self.assertRaises(bhm.GeneratorError):
            bhm.override_culture_file(FIXTURE, {"zeta": "x"})

    def test_crlf_preserved(self):
        text = FIXTURE.replace("\n", "\r\n")
        out = bhm.override_culture_file(text, {"gamma": "g"})
        self.assertNotIn("\r\r", out)
        self.assertEqual(out.count("\r\n"), text.count("\r\n"))


GFX_FIXTURE = {
    "a.txt": (
        "x1 = {\n\theritage = heritage_x\n\tbuilding_gfx = { western_building_gfx }\n}\n"
        "x2 = {\n\theritage = heritage_x\n\tbuilding_gfx = { western_building_gfx }\n}\n"
        "x3 = {\n\theritage = heritage_x\n\tbuilding_gfx = { mena_building_gfx }\n}\n"
        "y1 = {\n\theritage = heritage_y\n\tbuilding_gfx = { mena_building_gfx }\n}\n"
    ),
}
GFX_GROUPS = {"x": {"label": "X", "gfx": "aov_x_building_gfx", "heritage": "heritage_x"},
              "y": {"label": "Y", "gfx": "aov_y_building_gfx", "heritage": "heritage_y"}}


class GfxKeyTests(unittest.TestCase):
    def test_one_key_per_sequence(self):
        with mock.patch.object(data, "GROUPS", GFX_GROUPS):
            targets, keys = bhm.assign_gfx(GFX_FIXTURE)
        self.assertEqual(targets, {"x1": "aov_x_building_gfx", "x2": "aov_x_building_gfx",
                                   "x3": "aov_x_mena_building_gfx", "y1": "aov_y_building_gfx"})
        self.assertEqual(keys, {"x": ["aov_x_building_gfx", "aov_x_mena_building_gfx"], "y": ["aov_y_building_gfx"]})

    def test_fallback_is_the_second_key_of_the_sequence(self):
        with mock.patch.object(data, "GROUPS", GFX_GROUPS):
            self.assertEqual(bhm.gfx_fallbacks(GFX_FIXTURE),
                             {"aov_x_building_gfx": "western_building_gfx", "aov_x_mena_building_gfx": "mena_building_gfx",
                              "aov_y_building_gfx": "mena_building_gfx"})

    def test_variant_without_fallback_raises(self):
        texts = {"a.txt": "x1 = {\n\theritage = heritage_x\n\tbuilding_gfx = { western_building_gfx }\n}\n"
                          "x2 = {\n\theritage = heritage_x\n\tbuilding_gfx = { }\n}\n"}
        with mock.patch.object(data, "GROUPS", {"x": GFX_GROUPS["x"]}):
            with self.assertRaises(bhm.GeneratorError):
                bhm.assign_gfx(texts)

    def test_localization_labels(self):
        group = dict(GFX_GROUPS["x"], variant_labels={"mena_building_gfx": "X (Southern)"})
        with mock.patch.object(data, "GROUPS", {"x": group}):
            out = bhm.localization_lines({"x": ["aov_x_building_gfx", "aov_x_mena_building_gfx"]})
        self.assertEqual(out, [' aov_x_building_gfx:0 "X"', ' aov_x_mena_building_gfx:0 "X (Southern)"'])

    def test_group_labels_have_no_tolkien_names(self):
        labels = [g["label"] for g in data.GROUPS.values()] + \
            [v for g in data.GROUPS.values() for v in g.get("variant_labels", {}).values()]
        self.assertEqual(sorted(labels), sorted(["High Elven", "Wood Elven", "Dwarven", "Dwarven (Southern)", "Castanorian"]))


class RegionTests(unittest.TestCase):
    def test_graphical_regions_from_text(self):
        text = ("﻿# c\ngraphical_a = {\n\tgraphical = yes\n\tprovinces = { 1 }\n}\n"
                "other = {\n\tprovinces = { 2 }\n}\n"
                "# graphical_c = {\n#\tgraphical = yes\n# }\n"
                "graphical_b = {\n\tgraphical = yes\n}\n"
                "nested = {\n\tsub = {\n\t\tgraphical = yes\n\t}\n}\n")
        self.assertEqual(bhm.graphical_regions_from_text(text), ["graphical_a", "graphical_b"])

    def test_no_graphical_regions_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "map_data/geographical_regions"
            folder.mkdir(parents=True)
            (folder / "r.txt").write_text("plain = {\n\tprovinces = { 1 }\n}\n")
            with self.assertRaises(bhm.GeneratorError):
                bhm.graphical_regions(Path(tmp))

    def test_terrain_provinces(self):
        text = "1=mountains\n2=plains\n3=cavern\n#4=mountains\n5=dwarven_road\n"
        self.assertEqual(bhm.terrain_provinces(text, ("mountains",)), [1])
        self.assertEqual(bhm.terrain_provinces(text, data.DWARF_TERRAIN_TERRAINS), [3, 5])
        self.assertEqual(bhm.terrain_provinces(text, data.DWARF_TERRAIN_TERRAINS, exclude=(3,)), [5])

    def test_dwarf_terrain_constants(self):
        self.assertFalse(hasattr(data, "DWARF_MOUNTAIN_TERRAINS"))
        self.assertEqual(data.DWARF_PROVINCE_EXCLUDE, (263,))


@unittest.skipUnless(REAL.rie.is_dir() and REAL.anbennar.is_dir(), "RiE and Anbennar needed")
class RealDataTests(unittest.TestCase):
    def test_resolution_counts(self):
        resolved = bhm.resolve_cultures(bhm.culture_texts(REAL))
        self.assertEqual(resolved["high_elf"], ["moon_elvish", "sun_elvish"])
        self.assertEqual(resolved["wood_elf"], ["wood_elvish"])
        self.assertEqual(len(resolved["dwarven"]), 11)
        self.assertEqual(len(resolved["castanorian"]), 14)

    def test_overrides_differ_only_in_target_lines(self):
        texts = bhm.culture_texts(REAL)
        files = bhm.build_cultures(REAL)
        changed = Counter()
        for rel, content in files.items():
            old = texts[Path(rel).name].splitlines(keepends=True)
            new = content.decode("utf-8").splitlines(keepends=True)
            self.assertEqual(len(old), len(new))
            for a, b in zip(old, new):
                if a != b:
                    field = a.split("=")[0].strip()
                    self.assertIn(field, ("building_gfx", "unit_gfx", "clothing_gfx"))
                    changed[field] += 1
                    self.assertTrue(b.rstrip().endswith("# Anbennar Overhaul"))
        # 28 building_gfx lines; 14 unit_gfx lines (3 elves, 11 dwarves; tools/rie_units.py); 24 clothing_gfx lines
        # (10 halflings, 3 elves, 11 dwarves; tools/build_portraits.py)
        self.assertEqual(changed, Counter(building_gfx=28, unit_gfx=14, clothing_gfx=24))

    def test_regions_cover_anbennars_graphical_regions(self):
        regions = bhm.graphical_regions(REAL.anbennar)
        self.assertEqual(len(regions), 7)
        self.assertEqual(sorted(regions), sorted(set(regions)))
        self.assertIn("graphical_western", regions)
        self.assertNotIn("graphical_aov_dwarven_mountains", regions)

    def test_dwarf_keys(self):
        targets, keys = bhm.assign_gfx(bhm.culture_texts(REAL))
        self.assertEqual(keys["dwarven"], ["aov_dwarven_building_gfx", "aov_dwarven_mena_building_gfx"])
        for group in ("high_elf", "wood_elf", "castanorian"):
            self.assertEqual(keys[group], [data.GROUPS[group]["gfx"]])
        mena = sorted(c for c, k in targets.items() if k == "aov_dwarven_mena_building_gfx")
        self.assertEqual(mena, ["copper_dwarvish", "gold_dwarvish", "marble_dwarvish"])

    def test_every_first_gfx_key_has_one_sequence(self):
        """With the overrides applied, a building_gfx list starting with a key always continues the same way."""
        texts = dict(bhm.culture_texts(REAL))
        for rel, content in bhm.build_cultures(REAL).items():
            texts[Path(rel).name] = content.decode("utf-8")
        sequences = {}
        for text in texts.values():
            for _key, _s, _e, body in bhm.culture_blocks(text):
                seq = bhm.building_gfx_sequence(body)
                if not seq:
                    continue
                sequences.setdefault(seq[0], set()).add(seq[1:])
        bad = {k: v for k, v in sequences.items() if len(v) > 1}
        self.assertEqual(bad, {})


BUILDING_FIXTURE = (
    "@illu = \"gfx/x.dds\"\n"
    "\n"
    "castle_01 = {\n"
    "\tmodifier = { x = 1 }\n"
    "\tassets = {\n"
    "\t\t### FP1 ###\n"
    "\t\tasset = {\n"
    "\t\t\ttype = pdxmesh\n"
    "\t\t\tname = \"first_mesh\"\n"
    "\t\t\tillustration = @illu\n"
    "\t\t\tsoundeffect = { soundeffect = \"event:/a\" soundparameter = { \"Tier\" = 0 } } # note {\n"
    "\t\t\tgraphical_cultures = { c }\n"
    "\t\t}\n"
    "\t\tasset = {\n"
    "\t\t\ttype = pdxmesh\n"
    "\t\t\tname = \"second_mesh\"\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
    "castle_02 = {\n"
    "\tassets = { }\n"
    "}\n"
)


DLC_FIXTURE = (
    "castle_01 = {\n"
    "\tassets = {\n"
    "\t\tasset = {\n"
    "\t\t\ttype = pdxmesh\n"
    "\t\t\tname = \"norse_mesh\"\n"
    "\t\t\trequires_dlc_flag = the_northern_lords\n"
    "\t\t\tillustration = \"gfx/norse.dds\"\n"
    "\t\t\tgraphical_cultures = { western_building_gfx }\n"
    "\t\t}\n"
    "\t\tasset = {\n"
    "\t\t\ttype = pdxmesh\n"
    "\t\t\tname = \"mena_mesh\"\n"
    "\t\t\tillustration = \"gfx/mena.dds\"\n"
    "\t\t\tgraphical_cultures = { mena_building_gfx }\n"
    "\t\t}\n"
    "\t\tasset = {\n"
    "\t\t\ttype = pdxmesh\n"
    "\t\t\tname = \"west_mesh\"\n"
    "\t\t\tillustration = \"gfx/west.dds\"\n"
    "\t\t\tsoundeffect = \"event:/w\"\n"
    "\t\t\tgraphical_cultures = {\n\t\t\t\tother_gfx\n\t\t\t\twestern_building_gfx\n\t\t\t}\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
)


class BuildingTests(unittest.TestCase):
    def test_illustration_comes_from_the_fallback_culture_asset_without_dlc(self):
        out = bhm.insert_assets(DLC_FIXTURE, [bhm.asset_block("n_mesh", "k")], {}, fallbacks=["western_building_gfx"])
        added = out[:out.index("norse_mesh")]
        self.assertIn("illustration = \"gfx/west.dds\"", added)
        self.assertIn("soundeffect = \"event:/w\"", added)
        self.assertNotIn("norse", added)
        out = bhm.insert_assets(DLC_FIXTURE, [bhm.asset_block("n_mesh", "k")], {}, fallbacks=["mena_building_gfx"])
        self.assertIn("illustration = \"gfx/mena.dds\"", out[:out.index("norse_mesh")])

    def test_fallback_without_a_match_uses_first_asset_without_dlc(self):
        out = bhm.insert_assets(DLC_FIXTURE, [bhm.asset_block("n_mesh", "k")], {}, fallbacks=["nowhere_gfx"])
        self.assertIn("illustration = \"gfx/mena.dds\"", out[:out.index("norse_mesh")])

    def test_duplicate_building_definition_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "common/buildings"
            folder.mkdir(parents=True)
            (folder / "a.txt").write_text("castle_01 = {\n}\n")
            (folder / "b.txt").write_text("﻿castle_01 = {\n}\n", encoding="utf-8")
            roots = bhm.Roots(rie=Path(tmp), anbennar=Path(tmp), game=Path(tmp))
            with self.assertRaises(bhm.GeneratorError):
                bhm.source_file(roots, "castle_01")
            (folder / "b.txt").write_text("# castle_01 = {\n")
            self.assertEqual(bhm.source_file(roots, "castle_01")[0].name, "a.txt")

    def test_building_block_bounds(self):
        start, end = bhm.building_block(BUILDING_FIXTURE, "castle_01")
        block = BUILDING_FIXTURE[start:end]
        self.assertTrue(block.startswith("castle_01 = {"))
        self.assertTrue(block.endswith("\t}\n}\n"))
        self.assertNotIn("castle_02", block)
        with self.assertRaises(bhm.GeneratorError):
            bhm.building_block(BUILDING_FIXTURE, "castle_09")

    def test_asset_block_single_and_variants(self):
        one = bhm.asset_block("a_mesh", "gfx_key")
        self.assertEqual(one, "\t\tasset = {\n\t\t\ttype = pdxmesh\n\t\t\tname = \"a_mesh\"\n"
                              "\t\t\tgraphical_cultures = { gfx_key }\n\t\t}\n")
        two = bhm.asset_block(["a_mesh", "b_mesh"], ["gfx_key", "gfx_other"], regions=["graphical_r", "graphical_s"])
        self.assertIn("\t\t\tnames = {\n\t\t\t\t\"a_mesh\"\n\t\t\t\t\"b_mesh\"\n\t\t\t}\n", two)
        self.assertIn("\t\t\tgraphical_cultures = { gfx_key gfx_other }\n", two)
        self.assertIn("\t\t\tgraphical_regions = { graphical_r graphical_s }\n", two)
        self.assertLess(two.index("graphical_cultures"), two.index("graphical_regions"))

    def test_asset_block_provinces_without_cultures(self):
        out = bhm.asset_block("a_mesh", None, regions=["graphical_r"], provinces=[5, 2])
        self.assertNotIn("graphical_cultures", out)
        self.assertIn("\t\t\tprovinces = { 2 5 }\n\t\t\tgraphical_regions = { graphical_r }\n", out)
        both = bhm.asset_block("a_mesh", "k", regions=["graphical_r"], provinces=[1])
        self.assertLess(both.index("graphical_cultures"), both.index("provinces"))

    def test_insert_assets_resolves_illustration_without_cultures(self):
        start, end = bhm.building_block(BUILDING_FIXTURE, "castle_01")
        block = BUILDING_FIXTURE[start:end]
        out = bhm.insert_assets(block, [bhm.asset_block("n_mesh", None, provinces=[1])], {"illu": "\"gfx/x.dds\""})
        added = out[:out.index("### FP1")]
        self.assertLess(added.index("illustration"), added.index("provinces"))
        self.assertEqual(added.count("illustration"), 1)

    def test_insert_assets_puts_new_assets_first(self):
        start, end = bhm.building_block(BUILDING_FIXTURE, "castle_01")
        block = BUILDING_FIXTURE[start:end]
        assets = [bhm.asset_block("new_a_mesh", "k_a"),
                  bhm.asset_block("new_b_mesh", "k_b", regions=["graphical_r"])]
        out = bhm.insert_assets(block, assets, {"illu": "\"gfx/x.dds\""})
        marker = "\t\t# Anbennar Overhaul: RiE holding model\n"
        self.assertEqual(out.count(marker), 1)
        i = out.index(marker)
        # the comment above the original first asset stays with it
        self.assertEqual(out[:i], block[:block.index("\t\t### FP1 ###")])
        j = out.index("\t\t### FP1 ###")
        self.assertEqual(out[j:], block[block.index("\t\t### FP1 ###"):])
        added = out[i + len(marker):j]
        self.assertEqual(added.count("asset = {"), 2)
        self.assertEqual(added.count("illustration = \"gfx/x.dds\"\n"), 2)
        self.assertEqual(added.count("soundeffect = { soundeffect = \"event:/a\" soundparameter = { \"Tier\" = 0 } }\n"), 2)
        self.assertNotIn("# note", added)
        self.assertLess(added.index("new_a_mesh"), added.index("new_b_mesh"))
        self.assertLess(added.index("illustration"), added.index("graphical_cultures"))

    def test_insert_assets_keeps_crlf(self):
        start, end = bhm.building_block(BUILDING_FIXTURE, "castle_01")
        block = BUILDING_FIXTURE[start:end].replace("\n", "\r\n")
        out = bhm.insert_assets(block, [bhm.asset_block("n_mesh", "k")], {"illu": "\"gfx/x.dds\""})
        self.assertNotIn("\n", out.replace("\r\n", ""))

    def test_insert_assets_needs_an_asset(self):
        with self.assertRaises(bhm.GeneratorError):
            bhm.insert_assets("castle_09 = {\n\tassets = { }\n}\n", [bhm.asset_block("n", "k")], {})

    def test_asset_files_missing_texture_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = Path(tmp) / "gfx" / "models"
            folder = models / "buildings" / "x"
            folder.mkdir(parents=True)
            asset = folder / "m.asset"
            asset.write_text('pdxmesh = {\n\tname = "m_mesh"\n\tfile = "m.mesh"\n\tmeshsettings = {\n'
                             '\t\ttexture_diffuse = "d.dds"\n#\t\ttexture_normal = "ignored.dds"\n\t}\n}\n')
            (folder / "m.mesh").write_bytes(b"x")
            with self.assertRaises(bhm.GeneratorError):
                bhm.asset_files(asset, models)
        with tempfile.TemporaryDirectory() as tmp:
            models = Path(tmp) / "gfx" / "models"
            folder = models / "buildings" / "x"
            folder.mkdir(parents=True)
            asset = folder / "m.asset"
            asset.write_text('pdxmesh = {\n\tname = "m_mesh"\n\tfile = "m.mesh"\n\tmeshsettings = {\n'
                             '\t\ttexture_diffuse = "d.dds"\n\t}\n}\n')
            (folder / "m.mesh").write_bytes(b"x")
            (models / "other").mkdir()
            (models / "other" / "d.dds").write_bytes(b"y")  # found elsewhere in the models folder
            names = [p.name for p in bhm.asset_files(asset, models)]
            self.assertEqual(sorted(names), ["d.dds", "m.asset", "m.mesh"])

    def test_find_asset_by_mesh_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = Path(tmp)
            (models / "a").mkdir()
            (models / "a" / "z.asset").write_text('pdxmesh = {\n\tname = "z_mesh"\n}\nentity = {\n\tname = "z_entity"\n}\n')
            self.assertEqual(bhm.find_asset(models, "z_mesh"), models / "a" / "z.asset")
            with self.assertRaises(bhm.GeneratorError):
                bhm.find_asset(models, "nope_mesh")


class ModelTableTests(unittest.TestCase):
    def test_table_shape(self):
        self.assertEqual(sorted(data.MODELS), [f"{k}_0{n}" for k in ("castle", "city", "temple") for n in range(1, 5)]
                         + ["tribe_01", "tribe_02"])
        self.assertEqual(data.MODELS["tribe_01"], {"wood_elf": ["sindarin_sanctuary_01_mesh"]})
        self.assertEqual(data.MODELS["tribe_02"], {"wood_elf": ["sindarin_sanctuary_02_mesh"]})
        self.assertEqual(data.WALL_MODELS, {"high_elf": "highelves_fort_wall_mesh", "wood_elf": "sindarin_hedge_wall_01_mesh"})
        self.assertEqual(data.CASTANORIAN_WALLS, {"walls_03": "dunedain_walls_03_mesh", "walls_04": "dunedain_walls_04_mesh"})
        self.assertEqual(data.WALL_LEVELS[3], ("has_building", ("castle_03", "city_03", "temple_03")))
        self.assertEqual(data.WALL_LEVELS[4], ("has_building_or_higher", ("castle_04", "city_04", "temple_04")))
        for key, groups in data.MODELS.items():
            if key.startswith("tribe"):
                continue
            expected = {"high_elf", "wood_elf", "castanorian", "dwarven"}
            self.assertEqual(set(groups), expected, key)
        self.assertEqual(set(data.MODEL_SETS), set(data.GROUPS))

    def test_table_values(self):
        m = data.MODELS
        self.assertEqual(m["castle_01"]["high_elf"], ["highelves_01_01_mesh", "highelves_01_02_mesh"])
        self.assertEqual(m["city_04"]["high_elf"], ["highelves_04_01_mesh", "highelves_04_02_mesh"])
        self.assertEqual([m[f"temple_0{n}"]["wood_elf"] for n in range(1, 5)],
                         [[f"sindarin_sanctuary_0{n}_mesh"] for n in (1, 2, 3, 3)])
        self.assertEqual([m[f"castle_0{n}"]["castanorian"] for n in range(1, 5)],
                         [[f"building_dunedain_castle_0{n}_mesh"] for n in range(1, 5)])
        self.assertEqual([m[f"city_0{n}"]["castanorian"] for n in range(1, 5)],
                         [["gondor_city_01_mesh"], ["gondor_city_01_mesh"], ["gondor_city_02_mesh"], ["gondor_city_02_mesh"]])
        self.assertEqual([m[f"temple_0{n}"]["castanorian"] for n in range(1, 5)],
                         [["building_dunedain_temple_01_a_mesh", "building_dunedain_temple_01_b_mesh"]] * 2
                         + [["building_dunedain_temple_02_a_mesh", "building_dunedain_temple_02_b_mesh"]] * 2)
        self.assertEqual([m[f"{k}_0{n}"]["dwarven"] for k in ("castle", "city", "temple") for n in range(1, 5)],
                         [[f"dwarven_holding_0{n}_mesh"] for n in range(1, 5)] * 3)


@unittest.skipUnless(REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir(), "RiE, Anbennar and game needed")
class RealBuildingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.buildings = bhm.build_buildings(REAL)[bhm.BUILDINGS_FILE].decode("utf-8")

    def test_source_selection(self):
        self.assertIn("anbennar", str(bhm.source_file(REAL, "castle_01")[0]).lower())
        self.assertIn("anbennar", str(bhm.source_file(REAL, "temple_01")[0]).lower())
        self.assertEqual(bhm.source_file(REAL, "city_01")[0].parent, REAL.game / "game/common/buildings")
        self.assertTrue(bhm.source_building(REAL, "city_01").startswith("city_01 = {"))

    def test_header_and_bom(self):
        self.assertTrue(self.buildings.startswith("﻿# Anbennar Overhaul: generated by tools/build_holding_models.py"))

    def test_all_buildings_equal_sources_outside_inserts(self):
        for key, groups in data.MODELS.items():
            kind = key.rsplit("_", 1)[0]
            extra = 0  # the dwarf model has one asset (the dwarven terrain, any holder)
            # file-local @variables get the building kind as a prefix (the sources reuse names with different values)
            source = re.sub(r"@(\w+)", lambda m: f"@{kind}_{m.group(1)}", bhm.source_building(REAL, key))
            start, end = bhm.building_block(self.buildings, key)
            block = self.buildings[start:end]
            marker = "\t\t# Anbennar Overhaul: RiE holding model" + ("\r\n" if "\r\n" in source else "\n")
            self.assertEqual(block.count(marker), 1, key)
            i = block.index(marker)
            self.assertEqual(block[:i], source[:i], key)
            self.assertNotIn("asset = {", block[:i], key)  # the new assets come before every original one
            self.assertTrue(block.endswith(source[i:]), key)
            self.assertEqual(block.count("asset = {"), source.count("asset = {") + len(groups) + extra, key)

    @staticmethod
    def _asset(block, mesh):
        at = block.index(f'"{mesh}"')
        eol = "\r\n" if "\r\n" in block else "\n"
        return block[block.rindex("asset = {", 0, at):block.index(eol + "\t\t}" + eol, at)]

    def test_assets_carry_regions_and_every_key_of_their_group(self):
        _targets, group_keys = bhm.assign_gfx(bhm.culture_texts(REAL))
        regions = bhm.graphical_regions(REAL.anbennar)
        for key, groups in data.MODELS.items():
            start, end = bhm.building_block(self.buildings, key)
            block = self.buildings[start:end]
            for group, meshes in groups.items():
                if group == "dwarven":
                    continue  # see the dwarf tests
                asset = self._asset(block, meshes[0])
                self.assertIn("graphical_cultures = { %s }" % " ".join(group_keys[group]), asset)
                self.assertIn("graphical_regions = { %s }" % " ".join(regions), asset, (key, group))

    def test_tribes_get_wood_elf_models_first(self):
        _targets, group_keys = bhm.assign_gfx(bhm.culture_texts(REAL))
        regions = bhm.graphical_regions(REAL.anbennar)
        for key, mesh in (("tribe_01", "sindarin_sanctuary_01_mesh"), ("tribe_02", "sindarin_sanctuary_02_mesh")):
            start, end = bhm.building_block(self.buildings, key)
            block = self.buildings[start:end]
            self.assertLess(block.index(f'"{mesh}"'), block.index("building_western_tribal_0"), key)
            asset = self._asset(block, mesh)
            self.assertIn("graphical_cultures = { %s }" % " ".join(group_keys["wood_elf"]), asset)
            self.assertIn("graphical_regions = { %s }" % " ".join(regions), asset)
            self.assertIn("illustration = ", asset)
            self.assertNotRegex(asset, r"fp\d_|norse")

    def _dwarf_asset(self, key):
        start, end = bhm.building_block(self.buildings, key)
        block = self.buildings[start:end]
        first = block.index("asset = {")
        nl = "\r\n" if "\r\n" in block else "\n"
        return block[first:block.index(nl + "\t\t}" + nl, first)]

    def test_dwarf_terrain_asset_only(self):
        terrain = bhm.read_text(REAL.anbennar / bhm.TERRAIN_FILE)
        any_owner = bhm.terrain_provinces(terrain, data.DWARF_TERRAIN_TERRAINS, exclude=data.DWARF_PROVINCE_EXCLUDE)
        self.assertEqual(any_owner, bhm.dwarf_model_provinces(REAL.anbennar))
        self.assertNotIn(263, any_owner)
        self.assertTrue(any_owner)
        regions = bhm.graphical_regions(REAL.anbennar)
        for kind in ("castle", "city", "temple"):
            for n in range(1, 5):
                mesh = f"dwarven_holding_0{n}_mesh"
                asset = self._dwarf_asset(f"{kind}_0{n}")
                self.assertIn(f'"{mesh}"', asset)
                self.assertIn("graphical_regions = { %s }" % " ".join(regions), asset)
                self.assertIn("illustration = ", asset)
                self.assertNotIn("graphical_cultures", asset)
                self.assertNotIn("graphical_faiths", asset)
                self.assertIn("provinces = { %s }" % " ".join(map(str, any_owner)), asset)
                start, end = bhm.building_block(self.buildings, f"{kind}_0{n}")
                self.assertEqual(self.buildings[start:end].count(f'"{mesh}"'), 1)

    def test_no_asset_combines_dwarf_keys_with_provinces(self):
        _targets, group_keys = bhm.assign_gfx(bhm.culture_texts(REAL))
        for key in data.MODELS:
            start, end = bhm.building_block(self.buildings, key)
            for asset in bhm.original_assets(self.buildings[start:end].splitlines(keepends=True)):
                code = "".join(asset)
                if "provinces =" in code:
                    for gfx in group_keys["dwarven"]:
                        self.assertNotIn(gfx, code, key)

    def test_temple_assets_list_the_anbennar_faiths(self):
        faiths = bhm.graphical_faiths(REAL.anbennar)
        self.assertIn("orthodox_gfx", faiths)
        self.assertIn("pagan_gfx", faiths)
        self.assertEqual(faiths, sorted(faiths))
        line = "graphical_faiths = { %s }" % " ".join(faiths)
        for key, groups in data.MODELS.items():
            start, end = bhm.building_block(self.buildings, key)
            block = self.buildings[start:end]
            for group, meshes in groups.items():
                asset = self._asset(block, meshes[0])
                if group == "dwarven":
                    continue
                if key.startswith("temple_"):
                    self.assertIn(line, asset, (key, group))
                else:
                    self.assertNotIn("graphical_faiths", asset, (key, group))

    def test_no_output_uses_the_removed_region(self):
        self.assertNotIn("graphical_aov_dwarven_mountains", self.buildings)

    def test_new_assets_never_copy_a_dlc_illustration(self):
        for key, groups in data.MODELS.items():
            start, end = bhm.building_block(self.buildings, key)
            block = self.buildings[start:end]
            for group, meshes in groups.items():
                asset = self._asset(block, meshes[0])
                self.assertNotRegex(asset, r"fp\d_|norse", (key, group))
                self.assertIn("illustration = ", asset)
                if key.startswith("castle"):
                    self.assertRegex(asset, r'illustration = "gfx/interface/illustrations/holding_types/castle_(western|mena)\.dds"')

    def test_every_mesh_found_in_rie(self):
        models = REAL.rie / "gfx/models"
        for key, groups in data.MODELS.items():
            for group, meshes in groups.items():
                for mesh in meshes:
                    path = bhm.find_asset(models, mesh)
                    folder = (models / "buildings" / data.MODEL_SETS[group]).resolve()
                    self.assertEqual(path.resolve().parent, folder, mesh)


WALL_KEYS = ("walls_01_tribal", "walls_01", "walls_02", "walls_03", "walls_04")
WALL_SOURCE = "common/buildings/99_background_graphics_buildings.txt"
WALLS_00_LINE = "\t\t\taov_dwarven_model_province_trigger = yes # Anbennar Overhaul: dwarven holds\n"
DWARF_LINE = "\t\tNOT = { aov_dwarven_model_province_trigger = yes } # Anbennar Overhaul: dwarven holds\n"
ALWAYS_NO = "\t\talways = no # Anbennar Overhaul: walls by holding level\n"
LEVEL_LINE = "\t\taov_holding_walls_level_%d_trigger = yes # Anbennar Overhaul: walls by holding level\n"


@unittest.skipUnless(REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir(), "RiE, Anbennar and game needed")
class RealWallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = bhm.build_walls(REAL)
        cls.elven = cls.files[bhm.WALLS_FILE].decode("utf-8")
        cls.overrides = cls.files[bhm.WALL_OVERRIDES_FILE].decode("utf-8")
        cls.keys = bhm.assign_gfx(bhm.culture_texts(REAL))[1]

    def test_elven_walls_building(self):
        self.assertTrue(self.elven.startswith("﻿# Anbennar Overhaul: generated"))
        start, end = bhm.building_block(self.elven, "aov_elven_walls")
        block = self.elven[start:end]
        self.assertIn("is_graphical_background = yes", block)
        regions = bhm.graphical_regions(REAL.anbennar)
        for group, mesh in data.WALL_MODELS.items():
            at = block.index(f'"{mesh}"')
            asset = block[block.rindex("asset = {", 0, at):block.index("\n\t\t}\n", at)]
            self.assertIn("graphical_cultures = { %s }" % " ".join(self.keys[group]), asset)
            self.assertIn("graphical_regions = { %s }" % " ".join(regions), asset)
        enabled = block[block.index("is_enabled"):]
        for key in self.keys["high_elf"] + self.keys["wood_elf"]:
            self.assertIn(f"has_building_gfx = {key}", enabled)
        self.assertIn("scope:holder ?= { culture = {", enabled)
        self.assertIn("is_county_capital = yes", enabled)
        self.assertIn("NOT = { aov_dwarven_model_province_trigger = yes }", enabled)
        self.assertIn("fort_level > 0", enabled)

    def _block_lines(self, text, key):
        a, b = bhm.building_block(text, key)
        return text[a:b].splitlines(keepends=True)

    def _without_dunedain(self, key, new):
        """(new without the inserted Dunedain asset: marker line, asset block, blank line; the asset's lines)."""
        mesh = data.CASTANORIAN_WALLS[key]
        at = next(i for i, line in enumerate(new) if f'"{mesh}"' in line)
        start = at - 2  # asset = {, type = pdxmesh, name
        self.assertEqual(new[start - 1], "\t# Anbennar Overhaul: RiE holding wall\n", key)
        end = next(i for i in range(at, len(new)) if new[i] == "\t}\n")
        self.assertEqual(new[end + 1], "\n", key)
        return new[:start - 1] + new[end + 2:], new[start:end + 1]

    def test_escanni_assets_only_in_walls_03_and_04(self):
        self.assertEqual(sorted(re.findall(r"^(\w+) = \{", self.overrides, re.MULTILINE)),
                         sorted(WALL_KEYS + ("walls_00",)))
        for key in WALL_KEYS + ("walls_00",):
            block = "".join(self._block_lines(self.overrides, key))
            self.assertEqual("dunedain_walls" in block, key in ("walls_03", "walls_04"), key)
            self.assertEqual("RiE holding wall" in block, key in ("walls_03", "walls_04"), key)
        # last, not first: vanilla's regional wall assets carry no graphical_cultures (score 4), so a first-listed
        # Dunedain asset (region 4 for any culture) would win the tie for every non-Escanni holding; listed last it
        # still wins for the Escanni (culture 2 + region 4 = 6) and loses the tie for everyone else
        for key, mesh in data.CASTANORIAN_WALLS.items():
            lines = self._block_lines(self.overrides, key)
            starts = [i for i, line in enumerate(lines) if line == "\tasset = {\n"]
            self.assertGreater(len(starts), 1, key)
            self.assertIn(f'"{mesh}"', lines[starts[-1] + 2], key)

    def _check_common(self, key, old, new):
        """new = old with the elven and dwarven lines inserted at the top of is_enabled; returns the rest of both."""
        at = next(i for i, line in enumerate(old) if line == "\tis_enabled = {\n") + 1
        self.assertEqual(new[:at], old[:at], key)
        inserted = new[at]
        self.assertEqual(new[at + 1], DWARF_LINE, key)
        self.assertTrue(inserted.startswith("\t\tNOT = { scope:holder ?= { culture = { OR = { has_building_gfx = "), key)
        self.assertTrue(inserted.endswith(" } } } } # Anbennar Overhaul: elven walls\n"), key)
        for gfx in self.keys["high_elf"] + self.keys["wood_elf"]:
            self.assertIn(f"has_building_gfx = {gfx}", inserted)
        return old[at:], new[at + 2:]

    def test_early_walls_never_show(self):
        source = bhm.read_text(REAL.anbennar / WALL_SOURCE).removeprefix(bhm.BOM)
        for key in ("walls_01_tribal", "walls_01", "walls_02"):
            old = self._block_lines(source, key)
            new = self._block_lines(self.overrides, key)
            self.assertEqual(len(new), len(old) + 3, key)
            at = next(i for i, line in enumerate(new) if line == "\tis_enabled = {\n")
            self.assertEqual(new[at + 1], ALWAYS_NO, key)
            rest_old, rest_new = self._check_common(key, old, new[:at + 1] + new[at + 2:])
            self.assertEqual(rest_new, rest_old, key)

    def test_walls_03_and_04_follow_the_holding_level(self):
        source = bhm.read_text(REAL.anbennar / WALL_SOURCE).removeprefix(bhm.BOM)
        for level in (3, 4):
            key = f"walls_0{level}"
            old = self._block_lines(source, key)
            new, _asset = self._without_dunedain(key, self._block_lines(self.overrides, key))
            text = "".join(new)
            self.assertNotIn("curtain_walls_0", text, key)
            self.assertIn(LEVEL_LINE % level, new, key)
            self.assertNotIn(LEVEL_LINE % (7 - level), new, key)
            self.assertIn("\t\t\tNOT = { government_has_flag = government_is_tribal }\n", new, key)
            self.assertIn(DWARF_LINE, new, key)
            # the assets (before is_enabled) are Anbennar's untouched
            a_old = old.index("\tis_enabled = {\n")
            a_new = new.index("\tis_enabled = {\n")
            self.assertEqual(new[:a_new], old[:a_old], key)

    def test_walls_00_is_re_emitted_with_the_dwarven_line_and_the_level_child(self):
        source = bhm.read_text(REAL.anbennar / WALL_SOURCE).removeprefix(bhm.BOM)
        old = self._block_lines(source, "walls_00")
        new = self._block_lines(self.overrides, "walls_00")
        at = next(i for i, line in enumerate(old) if line == "\tis_enabled = {\n") + 2
        self.assertEqual(old[at - 1], "\t\tOR = {\n")
        self.assertEqual(new[:at], old[:at])
        self.assertEqual(new[at], WALLS_00_LINE)
        extra = len(new) - len(old) - 1
        self.assertGreater(extra, 0)
        child = "".join(new[at + 1:at + 1 + extra])
        self.assertIn("# Anbennar Overhaul: walls by holding level", child)
        self.assertIn("NOT = { OR = { aov_holding_walls_level_3_trigger = yes aov_holding_walls_level_4_trigger = yes } }", child)
        self.assertEqual(new[at + 1 + extra:], old[at:])

    def test_walls_00_leaves_elves_with_elven_walls_alone(self):
        text = "".join(self._block_lines(self.overrides, "walls_00"))
        child = text[text.index("walls by holding level"):]
        self.assertIn("has_building_gfx = ", child)
        self.assertIn("is_county_capital = yes", child)
        self.assertIn("fort_level > 0", child)
        self.assertIn("government_is_tribal", child)

    def test_level_trigger_file(self):
        text = bhm.build_triggers(REAL)[bhm.TRIGGER_FILE].decode("utf-8")
        for level, call, keys in ((3, "has_building", ("castle_03", "city_03", "temple_03")),
                                  (4, "has_building_or_higher", ("castle_04", "city_04", "temple_04"))):
            start, end = bhm.building_block(text, f"aov_holding_walls_level_{level}_trigger")
            expected = (f"aov_holding_walls_level_{level}_trigger = {{\n\tOR = {{\n"
                        + "".join(f"\t\t{call} = {key}\n" for key in keys) + "\t}\n}\n")
            self.assertEqual(text[start:end], expected)

    def test_dwarven_trigger_file(self):
        text = bhm.build_triggers(REAL)[bhm.TRIGGER_FILE].decode("utf-8")
        self.assertTrue(text.startswith("\ufeff# Anbennar Overhaul: generated"))
        self.assertNotIn("\r", text)
        start, end = bhm.building_block(text, "aov_dwarven_model_province_trigger")
        expected = ("aov_dwarven_model_province_trigger = {\n\tOR = {\n"
                    + "".join(f"\t\tterrain = {t}\n" for t in data.DWARF_TERRAIN_TERRAINS)
                    + "\t}\n"
                    + "".join(f"\tNOT = {{ this = province:{p} }}\n" for p in data.DWARF_PROVINCE_EXCLUDE)
                    + "}\n")
        self.assertEqual(text[start:end], expected)
        self.assertEqual(bhm.TRIGGER_FILE, "common/scripted_triggers/aov_holding_model_triggers.txt")

    def test_override_file_loads_after_anbennars(self):
        self.assertGreater(Path(bhm.WALL_OVERRIDES_FILE).name, Path(WALL_SOURCE).name)

    def test_wall_meshes_are_copied(self):
        files = bhm.build_assets(REAL)
        for group, mesh in data.WALL_MODELS.items():
            asset = bhm.find_asset(REAL.rie / "gfx/models", mesh)
            self.assertIn(f"{bhm.ASSET_DIR}/{group}/{asset.name}", files)
            self.assertIn(f"{bhm.ASSET_DIR}/{group}/{asset.stem}.mesh", files)
        self.assertFalse(any("dunedain_walls_02" in rel for rel in files))
        for mesh in data.CASTANORIAN_WALLS.values():
            asset = bhm.find_asset(REAL.rie / "gfx/models", mesh)
            self.assertIn(f"{bhm.ASSET_DIR}/castanorian/{asset.name}", files)
            self.assertIn(f"{bhm.ASSET_DIR}/castanorian/{asset.stem}.mesh", files)
            for ref in re.findall(r'"([^"]+\.dds)"', asset.read_text("utf-8-sig")):
                self.assertTrue(any(rel.endswith("/" + ref) for rel in files)
                                or any((REAL.game / "game/gfx/models").rglob(ref))
                                or any((REAL.anbennar / "gfx/models").rglob(ref)), ref)


@unittest.skipUnless(REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir(), "RiE, Anbennar and game needed")
class RealAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = bhm.build_assets(REAL)  # also runs the collision and shader checks

    def test_layout_and_completeness(self):
        prefix = "gfx/models/buildings/aov_rie_holdings/"
        self.assertTrue(all(rel.startswith(prefix) for rel in self.files))
        groups = {rel[len(prefix):].split("/")[0] for rel in self.files}
        self.assertEqual(groups, set(data.GROUPS))
        import re
        for rel, content in self.files.items():
            if not rel.endswith(".asset"):
                continue
            folder = rel.rsplit("/", 1)[0]
            text = content.decode("utf-8-sig")
            for line in text.splitlines():
                line = bhm.strip_comment(line)
                for ref in re.findall(r'"([^"]+\.(?:mesh|dds))"', line):
                    beside = f"{folder}/{ref}" in self.files or any(r.endswith("/" + ref) for r in self.files)
                    vanilla = (REAL.game / "game/gfx/models/buildings" / ref).is_file() or \
                        any((REAL.anbennar / "gfx/models").rglob(ref)) or any((REAL.game / "game/gfx/models").rglob(ref))
                    self.assertTrue(beside or vanilla, f"{rel}: {ref}")

    def test_every_model_asset_copied(self):
        prefix = "gfx/models/buildings/aov_rie_holdings/"
        for groups in data.MODELS.values():
            for group, meshes in groups.items():
                for mesh in meshes:
                    asset = bhm.find_asset(REAL.rie / "gfx/models", mesh)
                    self.assertIn(f"{prefix}{group}/{asset.name}", self.files)

    def test_no_pdxmesh_name_collisions(self):
        bhm.check_collisions(REAL, self.files)  # raises on a collision

    def test_collision_check_detects(self):
        game_asset = next((REAL.game / "game/gfx/models/buildings").glob("*.asset"))
        import re
        name = re.search(r'name\s*=\s*"([^"]+)"', game_asset.read_text("utf-8-sig")).group(1)
        fake = {"gfx/models/buildings/aov_rie_holdings/x/y.asset": f'pdxmesh = {{\n\tname = "{name}"\n}}\n'.encode()}
        with self.assertRaises(bhm.GeneratorError):
            bhm.check_collisions(REAL, fake)


class RootTests(unittest.TestCase):
    def test_missing_rie_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = bhm.Roots(rie=Path(tmp) / "none", anbennar=Path(tmp), game=Path(tmp))
            with self.assertRaises(bhm.GeneratorError):
                bhm.build_all(roots)


@unittest.skipUnless(REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir(), "RiE, Anbennar and game needed")
class FreshnessTests(unittest.TestCase):
    def test_generated_files_match_the_mod(self):
        """Every file build_all writes exists in the mod with identical bytes (rerun the generator otherwise)."""
        stale = []
        for rel, content in bhm.build_all(REAL).items():
            path = bhm.SUBMOD / rel
            if not path.is_file() or path.read_bytes() != content:
                stale.append(rel)
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_holding_models.py")

    def test_region_file_is_gone(self):
        self.assertFalse((bhm.SUBMOD / "map_data/geographical_regions/aov_graphical_regions.txt").exists())
        self.assertNotIn("map_data/geographical_regions/aov_graphical_regions.txt", bhm.build_all(REAL))

    def test_no_orphan_model_files(self):
        """Files under the RiE holdings folder that build_all no longer produces are leftovers to delete."""
        produced = set(bhm.build_all(REAL))
        folder = bhm.SUBMOD / bhm.ASSET_DIR
        orphans = sorted(p.relative_to(bhm.SUBMOD).as_posix() for p in folder.rglob("*")
                         if p.is_file() and p.relative_to(bhm.SUBMOD).as_posix() not in produced)
        self.assertEqual(orphans, [], "leftover files: delete them")


if __name__ == "__main__":
    unittest.main()
