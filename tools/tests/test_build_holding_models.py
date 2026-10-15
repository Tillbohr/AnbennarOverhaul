"""Tests for tools/build_holding_models.py.

    python -I -m unittest discover -s tools/tests -p test_build_holding_models.py -v
"""

import re
import sys
import tempfile
import unittest
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

    def test_mountain_provinces(self):
        text = "1=mountains\n2=plains\n3=cavern\n#4=mountains\n"
        self.assertEqual(bhm.mountain_provinces(text, data.DWARF_MOUNTAIN_TERRAINS), [1, 3])

    def test_region_file(self):
        out = bhm.region_file([3, 1, 12])
        self.assertTrue(out.startswith("﻿# Anbennar Overhaul: generated by tools/build_holding_models.py"))
        self.assertIn("graphical = yes", out)
        body = out.split("provinces = {")[1]
        self.assertEqual(body.split("}")[0].split(), ["1", "3", "12"])


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
        changed = 0
        for rel, content in files.items():
            old = texts[Path(rel).name].splitlines(keepends=True)
            new = content.decode("utf-8").splitlines(keepends=True)
            self.assertEqual(len(old), len(new))
            for a, b in zip(old, new):
                if a != b:
                    changed += 1
                    self.assertIn("building_gfx", a)
                    self.assertTrue(b.rstrip().endswith("# Anbennar Overhaul"))
        self.assertEqual(changed, 28)

    def test_region_has_provinces(self):
        out = bhm.build_region(REAL)[bhm.REGION_FILE].decode("utf-8")
        self.assertIn("graphical = yes", out)

    def test_regions_cover_anbennars_graphical_regions(self):
        regions = bhm.graphical_regions(REAL.anbennar)
        self.assertEqual(len(regions), 7)
        self.assertEqual(sorted(regions), sorted(set(regions)))
        self.assertIn("graphical_western", regions)
        self.assertNotIn(data.REGION, regions)

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
        self.assertEqual(sorted(data.MODELS), [f"{k}_0{n}" for k in ("castle", "city", "temple") for n in range(1, 5)])
        for key, groups in data.MODELS.items():
            expected = {"high_elf", "wood_elf", "castanorian"} | ({"dwarven"} if not key.startswith("temple") else set())
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
        self.assertEqual([m[f"{k}_0{n}"]["dwarven"] for k in ("castle", "city") for n in range(1, 5)],
                         [[f"dwarven_holding_0{n}_mesh"] for n in range(1, 5)] * 2)


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

    def test_twelve_buildings_equal_sources_outside_inserts(self):
        for key, groups in data.MODELS.items():
            kind = key.rsplit("_", 1)[0]
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
            self.assertEqual(block.count("asset = {"), source.count("asset = {") + len(groups), key)

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
                asset = self._asset(block, meshes[0])
                self.assertIn("graphical_cultures = { %s }" % " ".join(group_keys[group]), asset)
                expected = [data.REGION] if group == "dwarven" else regions
                self.assertIn("graphical_regions = { %s }" % " ".join(expected), asset, (key, group))

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
                    beside = f"{folder}/{ref}" in self.files
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

    def test_no_orphan_model_files(self):
        """Files under the RiE holdings folder that build_all no longer produces are leftovers to delete."""
        produced = set(bhm.build_all(REAL))
        folder = bhm.SUBMOD / bhm.ASSET_DIR
        orphans = sorted(p.relative_to(bhm.SUBMOD).as_posix() for p in folder.rglob("*")
                         if p.is_file() and p.relative_to(bhm.SUBMOD).as_posix() not in produced)
        self.assertEqual(orphans, [], "leftover files: delete them")


if __name__ == "__main__":
    unittest.main()
