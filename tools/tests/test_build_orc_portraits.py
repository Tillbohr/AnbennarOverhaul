"""Tests for tools/build_orc_portraits.py and the orc portrait files (docs/systems/orc-portraits.md).

    python -I tools/run_tests.py build_orc_portraits
"""

import re
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_orc_portraits as orc  # noqa: E402

SUBMOD = orc.SUBMOD
ANBENNAR = SUBMOD.parent / "anbennar-ck3-dev-master"
PORTRAITS = "gfx/models/portraits"
HEAD_COUNTS = (2770, 2770, 5360)  # the game's male_head.mesh and female_head.mesh
TEETH_COUNTS = (447, 447, 694)  # EK2's teeth meshes

GENE_FIXTURE = """accessory_genes = {
\tother_gene = {
\t\tindex_like = {
\t\t\tindex = 7
\t\t}
\t}

\tteeth_accessory = {
\t\tinheritable = no

\t\tnormal_teeth = {
\t\t\tindex = 0
\t\t\tmale = { 1 = "male_teeth_normal" }
\t\t}
\t\tno_teeth = {
\t\t\tindex = 2
\t\t\tmale = {}
\t\t}
\t}

\teyelashes_accessory = {
\t\tinheritable = no
\t}
}
"""


def read(rel: str) -> str:
    return (SUBMOD / rel).read_bytes().decode("utf-8-sig")


def mesh_counts(path: Path) -> tuple:
    """(vertices, UVs, triangles) of a PDX binary mesh, from the lengths of its first p, u0 and tri arrays."""
    data = path.read_bytes()
    counts = []
    for key, size in ((b"!\x01pf", 3), (b"!\x02u0f", 2), (b"!\x03trii", 3)):
        at = data.find(key)
        counts.append(struct.unpack_from("<i", data, at + len(key))[0] // size if at >= 0 else None)
    return tuple(counts)


class TeethGeneTests(unittest.TestCase):
    def test_template_added_at_lowest_free_index_of_the_gene(self):
        out = orc.add_orc_teeth(GENE_FIXTURE)
        block = out[out.index("teeth_accessory = {"):out.index("eyelashes_accessory")]
        self.assertIn("aov_orc_teeth = {", block)
        self.assertIn("index = 1", block)  # 0 and 2 are used; other_gene's 7 does not count
        self.assertIn('male = { 1 = "male_aov_orc_teeth" }', block)
        self.assertIn('female = { 1 = "female_aov_orc_teeth" }', block)
        self.assertIn("boy = male", block)
        self.assertIn("girl = female", block)

    def test_only_marked_lines_change_and_idempotent(self):
        out = orc.add_orc_teeth(GENE_FIXTURE)
        self.assertEqual(orc.add_orc_teeth(out), out)
        start = out.index("\t\t" + orc.MARKER + ": orc teeth")
        end_marker = orc.MARKER + ": end of orc teeth\n"
        end = out.index(end_marker) + len(end_marker)
        self.assertEqual(out[:start] + out[end:], GENE_FIXTURE)

    def test_template_sits_inside_the_gene(self):
        out = orc.add_orc_teeth(GENE_FIXTURE)
        self.assertLess(out.index("aov_orc_teeth = {"), out.index("eyelashes_accessory"))
        self.assertGreater(out.index("aov_orc_teeth = {"), out.index("no_teeth"))

    def test_missing_gene_stops(self):
        with self.assertRaises(SystemExit):
            orc.add_orc_teeth(GENE_FIXTURE.replace("teeth_accessory", "other_accessory"))


class ArtTests(unittest.TestCase):
    def test_imported_art_present(self):
        for out_rel in orc.IMPORTS.values():
            self.assertTrue((SUBMOD / out_rel).is_file(), out_rel)

    @unittest.skipUnless(orc.DEFAULT_EK2.is_dir(), "needs Elder Kings 2")
    def test_imported_art_matches_ek2(self):
        for src_rel, out_rel in orc.IMPORTS.items():
            self.assertEqual((orc.DEFAULT_EK2 / src_rel).read_bytes(), (SUBMOD / out_rel).read_bytes(), out_rel)

    @unittest.skipUnless(orc.DEFAULT_GAME.is_dir(), "needs the game")
    def test_game_head_counts(self):
        for sex in ("male", "female"):
            path = orc.DEFAULT_GAME / f"{PORTRAITS}/{sex}_head/{sex}_head.mesh"
            self.assertEqual(mesh_counts(path), HEAD_COUNTS, sex)

    def test_head_shapes_match_the_game_head(self):
        shapes = [rel for rel in orc.IMPORTS.values() if "/blendshapes/" in rel]
        self.assertEqual(len(shapes), 5)  # nose and lips for both sexes, male horns
        for rel in shapes:
            self.assertEqual(mesh_counts(SUBMOD / rel), HEAD_COUNTS, rel)

    def test_teeth_shapes_match_their_base_mesh(self):
        teeth = [rel for rel in orc.IMPORTS.values() if re.search(r"aov_orc_(male|female)_teeth.*\.mesh$", rel)]
        self.assertEqual(len(teeth), 8)  # the mesh and three shapes, for both sexes
        for rel in teeth:
            self.assertEqual(mesh_counts(SUBMOD / rel), TEETH_COUNTS, rel)

    def test_no_import_shadows_a_game_or_anbennar_file(self):
        for rel in orc.IMPORTS.values():
            self.assertFalse((orc.DEFAULT_GAME / rel).exists(), rel)
            self.assertFalse((ANBENNAR / rel).exists(), rel)

    def test_every_new_file_name_is_ours(self):
        for rel in orc.IMPORTS.values():
            self.assertTrue(Path(rel).name.startswith("aov_orc_"), rel)


class FreshnessTests(unittest.TestCase):
    @unittest.skipUnless((orc.DEFAULT_GAME / orc.TEETH_GENE_FILE).is_file(), "needs the game")
    def test_teeth_gene_file_is_the_games_plus_marked_lines(self):
        game = (orc.DEFAULT_GAME / orc.TEETH_GENE_FILE).read_bytes()
        expected = orc.teeth_gene_bytes(game)
        self.assertEqual((SUBMOD / orc.TEETH_GENE_FILE).read_bytes(), expected, "stale: rerun build_orc_portraits.py")

    @unittest.skipUnless((orc.DEFAULT_GAME / orc.TEETH_GENE_FILE).is_file(), "needs the game")
    def test_real_template_takes_index_three(self):
        text = read(orc.TEETH_GENE_FILE).replace("\r\n", "\n")
        block = text[text.index("aov_orc_teeth = {"):]
        self.assertIn("index = 3", block[:block.index("}")])


class WiringTests(unittest.TestCase):
    """The accessories, teeth asset and copied meshes name each other."""

    ASSET = f"{PORTRAITS}/aov_orc/aov_orc_teeth.asset"
    ACCESSORIES = "gfx/portraits/accessories/aov_orc.txt"

    def test_teeth_accessories_entities_and_meshes_name_each_other(self):
        gene = read(orc.TEETH_GENE_FILE)
        accessories = read(self.ACCESSORIES)
        asset = read(self.ASSET)
        for sex in ("male", "female"):
            self.assertIn(f'1 = "{sex}_aov_orc_teeth"', gene)
            self.assertRegex(accessories, rf"(?m)^{sex}_aov_orc_teeth = \{{")
            self.assertIn(f'entity = "aov_orc_{sex}_teeth_entity"', accessories)
            self.assertIn(f'name = "aov_orc_{sex}_teeth_entity"', asset)
        for mesh in re.findall(r'"(aov_orc_\w+\.mesh)"', asset):
            self.assertTrue((SUBMOD / PORTRAITS / "aov_orc" / mesh).is_file(), mesh)

    def test_teeth_asset_has_only_the_kept_shapes(self):
        asset = re.sub(r"#[^\n]*", "", read(self.ASSET))  # the header credits EK2's files by name
        for dropped in ("kamal", "beast_fangs", "vampire_fangs", "ek2"):
            self.assertNotIn(dropped, asset)
        self.assertEqual(asset.count('name = "aov_orc_tusks_bs"'), 2)

    def test_teeth_textures_exist_by_name(self):
        asset = read(self.ASSET)
        names = set(re.findall(r'"(\w+\.dds)"', asset))
        self.assertEqual(names, {"aov_orc_teeth_diffuse.dds", "aov_orc_teeth_ssao_color.dds",
                                 "male_teeth_normal.dds", "male_teeth_properties.dds"})
        for name in names:
            if name.startswith("aov_"):
                self.assertTrue((SUBMOD / PORTRAITS / "aov_orc" / name).is_file(), name)
            elif orc.DEFAULT_GAME.is_dir():
                self.assertTrue((orc.DEFAULT_GAME / PORTRAITS / "male_head/male_teeth" / name).is_file(), name)

    def test_teeth_are_not_tinted_by_skin(self):
        # The skin shader tints a texture by its alpha. EK2's teeth texture has none, so tusks stay tooth-coloured.
        from eu4_import import read_dds
        _w, _h, pixels = read_dds((SUBMOD / PORTRAITS / "aov_orc/aov_orc_teeth_diffuse.dds").read_bytes())
        self.assertEqual(max(pixels[3::4]), 0)


if __name__ == "__main__":
    unittest.main()
