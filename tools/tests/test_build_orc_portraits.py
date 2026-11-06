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


class PatternArrayTests(unittest.TestCase):
    """The game loads all pattern textures into texture arrays, whose members must match the first one in size, format
    and mip count. One mismatch makes CreateTexture2D fail and the game crash on launch."""

    def test_every_pattern_texture_fits_the_games_arrays(self):
        folder = SUBMOD / "gfx/portraits/accessory_variations/textures/patterns"
        files = list(folder.rglob("*.dds"))
        self.assertTrue(files)
        for path in files:
            head = path.read_bytes()[:128]
            size = struct.unpack("<II", head[12:20])
            mips = struct.unpack_from("<I", head, 28)[0]
            self.assertEqual((size, mips, head[84:88]), ((512, 512), 10, b"DXT5"), path.name)

    def test_every_pattern_set_the_mod_declares_fits_the_games_arrays(self):
        checked = 0
        for variations in (SUBMOD / "gfx/portraits/accessory_variations").glob("*.txt"):
            text = variations.read_bytes().decode("utf-8-sig")
            for block in re.findall(r"(?s)pattern_textures\s*=\s*\{(.*?)\}", re.sub(r"#[^\n]*", "", text)):
                for rel in re.findall(r'"(gfx/[^"]+\.dds)"', block):
                    path = SUBMOD / rel
                    if not path.is_file():
                        continue  # the game's own, which fit by definition
                    head = path.read_bytes()[:128]
                    self.assertEqual((struct.unpack("<II", head[12:20]), struct.unpack_from("<I", head, 28)[0], head[84:88]),
                                     ((512, 512), 10, b"DXT5"), rel)
                    checked += 1
        self.assertGreater(checked, 3)

    def test_fur_mask_is_eks_with_a_full_mip_chain(self):
        source = orc.DEFAULT_EK2 / orc.FUR_MASK_SOURCE
        if not source.is_file():
            self.skipTest("needs Elder Kings 2")
        self.assertEqual((SUBMOD / orc.FUR_MASK).read_bytes(), orc.full_mip_dds(source.read_bytes()))

    def test_fur_mask_keeps_eks_picture(self):
        from eu4_import import read_dds
        source = orc.DEFAULT_EK2 / orc.FUR_MASK_SOURCE
        if not source.is_file():
            self.skipTest("needs Elder Kings 2")
        _w, _h, before = read_dds(source.read_bytes())
        _w, _h, after = read_dds((SUBMOD / orc.FUR_MASK).read_bytes())
        difference = sum(abs(a - b) for a, b in zip(before[::97], after[::97])) / len(before[::97])
        self.assertLess(difference, 6)


class ShadowTests(unittest.TestCase):
    def test_build_stops_if_anbennar_ships_the_gene_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            game, anbennar = Path(tmp) / "game", Path(tmp) / "anbennar"
            for root in (game, anbennar):
                (root / "common/genes").mkdir(parents=True)
                (root / orc.TEETH_GENE_FILE).write_text(GENE_FIXTURE, "utf-8")
            with self.assertRaises(SystemExit) as stopped:
                orc.build(game, anbennar)
            self.assertIn("Anbennar", str(stopped.exception))

    def test_anbennar_does_not_ship_it_today(self):
        self.assertFalse((ANBENNAR / orc.TEETH_GENE_FILE).exists())


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


GENES_FILE = "common/genes/aov_orc_genes.txt"
ORC_GENES = {"aov_orc_nose": "orc_nose", "aov_orc_forehead": "orc_forehead", "aov_orc_tusks": "orc_tusk_size",
             "aov_orc_wrinkles": "orc_wrinkles", "aov_orc_horns": "orc_horns"}


def block_of(text: str, key: str) -> str:
    """The body of the first block named key."""
    match = re.search(rf"(?m)^\s*{key}\s*=\s*\{{", text)
    if not match:
        raise AssertionError(f"no block {key}")
    depth, at = 1, match.end()
    while depth:
        depth += {"{": 1, "}": -1}.get(text[at], 0)
        at += 1
    return text[match.end():at - 1]


def code(text: str) -> str:
    return re.sub(r"#[^\n]*", "", text)


class GeneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.genes = code(read(GENES_FILE))

    def test_genes_have_empty_index_zero_and_are_inherited(self):
        for gene, template in ORC_GENES.items():
            body = block_of(self.genes, gene)
            self.assertIn("inheritable = yes", body, gene)
            first = re.search(r"(\w+)\s*=\s*\{\s*(?:visible = no\s*)?index = 0\s*male = \{\}", body)
            self.assertIsNotNone(first, f"{gene}: index 0 must be empty so everyone else is unchanged")
            self.assertRegex(block_of(body, template), r"index = 1\b", gene)

    def test_only_the_orc_templates_are_kept(self):
        for dropped in ("mer_nose", "kamal", "dremora", "no_dimorphism", "ek_", "male_orc_nose_bs"):
            self.assertNotIn(dropped, self.genes)

    def test_gene_textures_exist(self):
        textures = re.findall(r'"(gfx/[^"]+\.dds)"', self.genes)
        self.assertTrue(textures)
        for tex in textures:
            ours, game = SUBMOD / tex, orc.DEFAULT_GAME / tex
            self.assertTrue(ours.is_file() or game.is_file(), tex)

    def test_gene_attributes_are_on_an_entity(self):
        import build_head_assets as head
        asset = read(WiringTests.ASSET)
        on_head = {attribute for sex in head.ATTRIBUTES for attribute, _shape in head.ATTRIBUTES[sex]}
        for attribute in set(re.findall(r'attribute = "(\w+)"', self.genes)):
            self.assertTrue(attribute in on_head or f'name = "{attribute}"' in asset, attribute)

    def test_every_new_attribute_is_on_both_heads_except_horns(self):
        import build_head_assets as head
        for attribute in ("aov_orc_nose_bs", "aov_orc_lips_bs", "aov_orc_tusks_bs"):
            for sex in ("male", "female"):
                self.assertIn(attribute, [a for a, _s in head.ATTRIBUTES[sex]], f"{sex} {attribute}")

    def test_horns_are_male_only(self):
        import build_head_assets as head
        template = block_of(block_of(self.genes, "aov_orc_horns"), "orc_horns")
        self.assertRegex(template, r"female = \{\s*\}")
        self.assertIn("girl = female", template)
        self.assertNotIn("aov_orc_horns_bs", [a for a, _s in head.ATTRIBUTES["female"]])
        self.assertIn("aov_orc_horns_bs", [a for a, _s in head.ATTRIBUTES["male"]])

    def test_tusks_keep_eks_values(self):
        gene = block_of(self.genes, "aov_orc_tusks")
        self.assertIn("sync_inheritance_with = skin_color", gene)
        template = block_of(gene, "orc_tusk_size")
        male, female = block_of(template, "male"), block_of(template, "female")
        for attribute in ("aov_orc_tusks_bs", "aov_orc_lips_bs"):
            self.assertRegex(male, rf'attribute = "{attribute}"\s+value = \{{ min = 0\.0 max = 1\.0 \}}')
            self.assertRegex(female, rf'attribute = "{attribute}"\s+value = \{{ min = 0\.0 max = 0\.9 \}}')

    def test_tusks_map_to_the_neutral_head_shape(self):
        # EK2's way for a teeth shape set by a head gene: the head needs the attribute too, doing nothing
        import build_head_assets as head
        for sex in ("male", "female"):
            self.assertIn(("aov_orc_tusks_bs", f"{sex}_bs_neutral"), head.ATTRIBUTES[sex])

    def test_age_preset_exists(self):
        presets = set(re.findall(r"age = (age_preset\w+)", self.genes))
        self.assertEqual(presets, {"age_preset_child_features_wide_range"})
        found = False
        for folder in (ANBENNAR / "common/genes", orc.DEFAULT_GAME / "common/genes", SUBMOD / "common/genes"):
            for path in folder.glob("*.txt"):
                if re.search(r"(?m)^\s*age_preset_child_features_wide_range\s*=\s*\{",
                             path.read_bytes().decode("utf-8-sig", "replace")):
                    found = True
        self.assertTrue(found, "age_preset_child_features_wide_range is defined nowhere: copy EK2's definition")


ETHNICITIES_FILE = "common/ethnicities/aov_orc_ethnicities.txt"
MODIFIER_FILE = "gfx/portraits/portrait_modifiers/aov_orc.txt"
CULTURES_FILE = "common/culture/cultures/aov_tribes_cultures.txt"
COLOUR_GENES = ("skin_color", "eye_color", "hair_color")
LEFT_OUT = ("race_gene_skin_color", "race_gene_skin_metallic", "eye_sclera", "eye_pupil", "race_gene_mer_eyebrows_01",
            "hairline_type", "teeth_accessory", "gene_eye_size", "beast_teeth", "race_gene_mer_nose",
            "race_gene_mer_forehead", "race_extra_wrinkly_gene", "race_giantish_horns")


def defined_genes() -> dict:
    """gene -> templates, from this mod's gene files over Anbennar's over the game's (by file name)."""
    import build_portraits as bp
    files = {}
    for folder in (orc.DEFAULT_GAME / "common/genes", ANBENNAR / "common/genes", SUBMOD / "common/genes"):
        for path in folder.glob("*.txt"):
            files[path.name] = path
    genes = {}
    for path in files.values():
        text = bp.code(path.read_bytes().decode("utf-8-sig", "replace"))
        for names, _start, _end in bp.blocks(text, strict=False):
            inner = names[1:] if names[0] != "special_genes" else names[2:]
            if names[0] in ("morph_genes", "accessory_genes", "special_genes") and len(inner) == 1:
                genes.setdefault(inner[0], set())
            elif names[0] in ("morph_genes", "accessory_genes", "special_genes") and len(inner) == 2:
                genes.setdefault(inner[0], set()).add(inner[1])
    return genes


def ethnicity_genes(body: str) -> dict:
    """gene -> template names an ethnicity's block sets, leaving out its plain values."""
    out = {}
    for match in re.finditer(r"(?m)^\t(\w+) = \{", body):
        out[match.group(1)] = set(re.findall(r"name\s*=\s*(\w+)", block_of(body, match.group(1))))
    return out


class EthnicityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = code(read(ETHNICITIES_FILE))

    def _all(self) -> dict:
        return {name: ethnicity_genes(block_of(self.text, name))
                for name in ("orc_base", "orc_brown", "orc_gray", "orc_black")}

    @unittest.skipUnless(orc.DEFAULT_GAME.is_dir() and ANBENNAR.is_dir(), "needs the game and Anbennar")
    def test_every_gene_and_template_in_the_ethnicities_is_defined(self):
        known = defined_genes()
        for name, genes in self._all().items():
            for gene, templates in genes.items():
                if gene in COLOUR_GENES:
                    continue
                self.assertIn(gene, known, f"{name}: gene {gene}")
                self.assertEqual(templates - known[gene], set(), f"{name}: {gene}")

    def test_no_left_out_gene_is_named(self):
        for name, genes in self._all().items():
            for gene in LEFT_OUT:
                self.assertNotIn(gene, genes, name)

    def test_base_sets_the_five_orc_genes(self):
        base = self._all()["orc_base"]
        for gene, template in ORC_GENES.items():
            self.assertIn(template, base.get(gene, set()), gene)
        self.assertEqual(base["aov_orc_horns"], {"orc_horns", "no_orc_horns"})  # 3 in 11 men have horns

    def test_base_has_no_skin_so_only_the_colours_set_it(self):
        self.assertNotIn("skin_color", self._all()["orc_base"])
        self.assertNotIn("skin_color_saturation", self._all()["orc_base"])

    def test_colours_build_on_the_base(self):
        for name in ("orc_brown", "orc_gray", "orc_black"):
            self.assertIn('template = "orc_base"', block_of(self.text, name), name)

    def test_colours_are_the_specs(self):
        boxes = {"orc_brown": "0.4 0.65 0.8 0.85", "orc_gray": "0.0 0.5 0.2 0.75", "orc_black": "0.0 0.85 0.2 1.0"}
        saturations = {"orc_brown": "0.5 0.5", "orc_gray": "0.0 0.05", "orc_black": "0.0 0.05"}
        for name, box in boxes.items():
            body = block_of(self.text, name)
            self.assertRegex(block_of(body, "skin_color"), rf"= \{{ {box} \}}", name)
            self.assertRegex(block_of(body, "skin_color_saturation"),
                             rf"name = skin_color_saturation\s+range = \{{ {saturations[name]} \}}", name)

    def test_eye_size_uses_the_games_gene(self):
        self.assertRegex(block_of(block_of(self.text, "orc_base"), "gene_bs_eye_size"),
                         r"name = eye_size_neg\s+range = \{ 0\.0 0\.4 \}")

    def test_hair_colour_and_tusks_keep_eks_weights(self):
        base = block_of(self.text, "orc_base")
        self.assertRegex(block_of(base, "aov_orc_tusks"), r"50 = \{\s*name = orc_tusk_size\s+range = \{ 0\.8 1\.0 \}")
        horns = block_of(base, "aov_orc_horns")
        self.assertRegex(horns, r"2 = \{ name = orc_horns\s+range = \{ 0\.5 1\.0 \}")
        self.assertRegex(horns, r"8 = \{ name = no_orc_horns\s+range = \{ 0\.0 0\.0 \}")

    def test_black_orc_lists_the_three_colours_and_cave_goblin_is_unchanged(self):
        cultures = code(read(CULTURES_FILE))
        black, goblin = block_of(cultures, "black_orc"), block_of(cultures, "cave_goblin")
        self.assertEqual(re.findall(r"(\d+) = (\w+)", block_of(black, "ethnicities")),
                         [("1", "orc_brown"), ("1", "orc_gray"), ("1", "orc_black")])
        self.assertIn("western_clothing_gfx", black)  # clothes are chosen separately
        self.assertEqual(re.findall(r"(\d+) = (\w+)", block_of(goblin, "ethnicities")), [("100", "arab")])


class ModifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = code(read(MODIFIER_FILE))
        cls.teeth = block_of(cls.text, "aov_orc_teeth")
        cls.hair = block_of(cls.text, "aov_orc_hair")
        cls.beards = block_of(cls.text, "aov_orc_beards")

    def test_teeth_skip_liches(self):
        self.assertRegex(self.teeth, r"has_trait = race_orc")
        self.assertRegex(self.teeth, r"has_trait = race_half_orc")
        self.assertRegex(self.teeth, r"NOT = \{ has_trait = lich \}")

    def test_teeth_replace_the_gene_with_our_template(self):
        self.assertRegex(self.teeth, r"mode = replace\s+gene = teeth_accessory\s+template = aov_orc_teeth\s+value = 0\.5")

    def test_age_conditions(self):
        self.assertRegex(self.text, r"(?m)^@baby_hair_age = 5\s*$")  # comments are stripped, leaving a space
        self.assertIn("scope:age >= @baby_hair_age", self.hair)
        self.assertIn("scope:age >= 18", self.beards)

    def test_baby_hair_age_matches_anbennars(self):
        base = ANBENNAR / "gfx/portraits/portrait_modifiers/01_hairstyles_base.txt"
        if base.is_file():
            self.assertRegex(base.read_bytes().decode("utf-8-sig", "replace"), r"(?m)^@baby_hair_age = 5\b")

    def test_hair_and_beards_use_mode_add_and_race_orc_only(self):
        # the engine rejects replace on these special genes
        for body, gene, template in ((self.hair, "hairstyles", "aov_orc_hairstyles"), (self.beards, "beards", "aov_orc_beards")):
            self.assertRegex(body, rf"mode = add\s+gene = {gene}\s+template = {template}\s+range = \{{ 0 1 \}}")
            self.assertIn("has_trait = race_orc", body)
            self.assertNotIn("race_half_orc", body)

    def test_hair_and_beards_keep_eks_exclusions_and_no_priority(self):
        for body in (self.hair, self.beards):
            self.assertIn("is_from_ruler_designer = yes", body)
            self.assertIn("has_character_flag = has_scripted_appearance", body)
            self.assertNotIn("priority", body)

    def test_forced_shaving_still_wins_over_the_beard_group(self):
        # Later groups of equal priority win, so a eunuch or a monk would otherwise get a full beard
        for condition in ("has_trait = beardless_eunuch", "has_character_flag = no_beard"):
            self.assertIn(condition, self.beards)

    def test_forced_baldness_still_wins_over_the_hair_group(self):
        for condition in ("has_nickname = nick_the_actually_bald", "has_character_modifier = hajj_halq_modifier",
                          "has_character_modifier = shaven_bald_modifier", "has_character_flag = bald_head"):
            self.assertIn(condition, self.hair)

    def test_women_get_no_beard_list(self):
        self.assertIn("is_female = no", self.beards)


def gene_file_template(filename: str, template: str) -> str:
    return block_of(code(read(f"common/genes/{filename}")), template)


HAIR_GENES = "03_genes_special_accessories_hairstyles.txt"
BEARD_GENES = "04_genes_special_accessories_beards.txt"
CLOTHES_GENES = "05_genes_special_accessories_clothes.txt"
HEADGEAR_GENES = "06_genes_special_accessories_headgear.txt"
LEGWEAR_GENES = "07_genes_special_accessories_misc.txt"
# Clean, styled human looks: what made orcs look like bearded men in the first in-game test.
HUMAN_HAIR = re.compile(r"\b(male_hair_(western_0[2-9]|mena|sub_saharan|rtt|steppe|indian|northern|byzantine)\w*)\b")
HUMAN_BEARDS = re.compile(r"\bmale_beard_(western|mena|northern|steppe|sub_saharan|indian)\w*")


def weights(body: str) -> dict:
    return {name: int(weight) for weight, name in re.findall(r'(\d+)\s*=\s*"?([A-Za-z_]\w*)', body)}


class GruffHairTests(unittest.TestCase):
    def test_no_styled_human_hair_for_men(self):
        male = block_of(gene_file_template(HAIR_GENES, "aov_orc_hairstyles"), "male")
        self.assertEqual(HUMAN_HAIR.findall(male), [])

    def test_hair_favours_shaved_heads_and_rie_orc_hair(self):
        male = weights(block_of(gene_file_template(HAIR_GENES, "aov_orc_hairstyles"), "male"))
        self.assertIn("empty", male)
        self.assertIn("male_hair_mountain_orc_01", male)
        self.assertIn("male_hair_uruk_01", male)
        self.assertEqual(max(male, key=male.get), "male_hair_mountain_orc_01")

    def test_no_human_beards(self):
        self.assertEqual(HUMAN_BEARDS.findall(gene_file_template(BEARD_GENES, "aov_orc_beards")), [])

    def test_most_men_are_clean_shaven_so_the_tusks_show(self):
        male = weights(block_of(gene_file_template(BEARD_GENES, "aov_orc_beards"), "male"))
        self.assertEqual(male, {"empty": 40, "male_beard_mountain_orc_01": 5, "male_beard_mountain_orc_02": 1,
                                "beard_tywins_muttonchops": 4})  # RiE's orc_beards

    def test_eks_lists_are_gone(self):
        for filename in (HAIR_GENES, BEARD_GENES):
            self.assertNotIn("orc_hairstyles = {" if filename == HAIR_GENES else "\torc_beards = {",
                             read(f"common/genes/{filename}").replace("aov_orc_hairstyles", "").replace("aov_orc_beards", ""))

    def test_modifier_uses_the_new_lists(self):
        modifier = code(read(MODIFIER_FILE))
        self.assertIn("template = aov_orc_hairstyles", modifier)
        self.assertIn("template = aov_orc_beards", modifier)


RAGS = "gfx/models/portraits/aov_orc/rags"


class WardrobeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = code(read(MODIFIER_FILE))

    def _accessories_exist(self, names):
        ours = read("gfx/portraits/accessories/aov_orc.txt") + read("gfx/portraits/accessories/aov_rie_portraits.txt")
        for name in names:
            self.assertRegex(ours, rf"(?m)^{name}\s*=\s*\{{", name)

    def test_templates_hold_the_recommended_mix(self):
        expected = {
            (CLOTHES_GENES, "aov_orc_common_clothes"): ({"m_clothes_sec_ek2_goblin_com_01", "m_clothes_sec_ek2_goblin_com_02"},
                                                        {"fem_clothes_sec_ek2_goblin_com_01"}),
            (CLOTHES_GENES, "aov_orc_chief_clothes"): ({"male_clothes_secular_riekling_01"},
                                                       {"female_clothes_secular_riekling_01"}),
            (CLOTHES_GENES, "aov_orc_ruler_clothes"): ({"male_clothes_moria_orc_01"}, {"female_clothes_goblin_armor_01"}),
            (CLOTHES_GENES, "aov_orc_war_clothes"): ({"male_clothes_mordor_uruk_01"}, {"female_clothes_mordor_uruk_01"}),
            (LEGWEAR_GENES, "aov_orc_chief_legwear"): ({"male_legwear_uruk_beserker_1"}, {"female_legwear_uruk_beserker_1"}),
            (LEGWEAR_GENES, "aov_orc_ruler_legwear"): ({"male_legwear_orc_war_01"}, {"female_legwear_mordor_uruk_02"}),
            (LEGWEAR_GENES, "aov_orc_war_legwear"): ({"male_legwear_uruk_soldier"}, {"female_legwear_uruk_soldier"}),
            (HEADGEAR_GENES, "aov_orc_crown_headgear"): ({"male_headgear_goblin_king"}, {"female_headgear_goblin_king"}),
            (HEADGEAR_GENES, "aov_orc_war_headgear"): ({"male_headgear_uruk_isengard_1"}, {"female_headgear_uruk_isengard_1"}),
        }
        for (filename, template), (male, female) in expected.items():
            body = gene_file_template(filename, template)
            self.assertEqual(set(weights(block_of(body, "male"))), male, template)
            self.assertEqual(set(weights(block_of(body, "female"))), female, template)
            self.assertRegex(self.text, rf"template = {template}\b", template)
            self._accessories_exist(male | female)

    def _group(self, name):
        return block_of(self.text, name)

    def test_rank_clothes_use_their_triggers(self):
        clothes = self._group("aov_orc_clothes")
        self.assertRegex(clothes, r"priority = 1\b")
        self.assertRegex(block_of(clothes, "aov_orc_common"), r"portrait_commoner_clothing_trigger = \{\s*CULTURE_INPUT = aov_orc")
        self.assertRegex(block_of(clothes, "aov_orc_chief"), r"portrait_low_nobles_clothing_trigger = \{\s*CULTURE_INPUT = aov_orc")
        ruler = block_of(clothes, "aov_orc_ruler")
        for rank in ("high_nobles", "royalty", "imperial"):
            self.assertRegex(ruler, rf"portrait_{rank}_clothing_trigger = \{{\s*CULTURE_INPUT = aov_orc")

    def test_children_wear_the_rags_because_the_armour_has_no_child_shape(self):
        clothes = self._group("aov_orc_clothes")
        self.assertIn("scope:age < 16", block_of(clothes, "aov_orc_child"))
        for entry in ("aov_orc_chief", "aov_orc_ruler"):
            self.assertIn("scope:age >= 16", block_of(clothes, entry))
        self.assertIn("template = aov_orc_common_clothes", block_of(clothes, "aov_orc_child"))

    def test_war_clothes_are_armour_for_every_rank(self):
        armor = self._group("aov_orc_clothes_armor")
        self.assertRegex(armor, r"priority = 4\b")
        self.assertIn("military_outfit", armor)
        self.assertIn("portrait_wear_armor_trigger = yes", armor)
        for rank in ("commoner", "low_nobles", "high_nobles", "royalty"):
            self.assertRegex(armor, rf"portrait_{rank}_armor_trigger = \{{\s*CULTURE_INPUT = aov_orc", rank)
        self.assertRegex(armor, r"portrait_imperial_trigger = \{\s*CULTURE_INPUT = aov_orc")  # no imperial armour trigger exists

    def test_helmets_only_in_war(self):
        helmets = self._group("aov_orc_headgear_armor")
        self.assertRegex(helmets, r"priority = 4\b")
        self.assertIn("portrait_wear_helmet_trigger = yes", helmets)
        self.assertIn("template = aov_orc_war_headgear", helmets)

    def test_only_great_rulers_are_crowned_and_no_one_else_wears_a_western_hat(self):
        headgear = self._group("aov_orc_headgear")
        self.assertRegex(headgear, r"priority = 1\b")
        crown = block_of(headgear, "aov_orc_crown")
        for rank in ("high_nobles", "royalty", "imperial"):
            self.assertRegex(crown, rf"portrait_{rank}_headgear_trigger = \{{\s*CULTURE_INPUT = aov_orc")
        self.assertIn("template = no_headgear", block_of(headgear, "aov_orc_no_hat"))
        self.assertLess(headgear.index("aov_orc_crown"), headgear.index("aov_orc_no_hat"))  # the first at 100 or more wins

    def test_no_western_cloaks(self):
        self.assertIn("template = no_cloak", self._group("aov_orc_cloaks"))

    def test_clothes_follow_the_culture_key(self):
        cultures = code(read(CULTURES_FILE))
        self.assertEqual(re.findall(r"\w+", block_of(block_of(cultures, "black_orc"), "clothing_gfx")),
                         ["aov_orc_clothing_gfx", "western_clothing_gfx"])
        self.assertNotIn("aov_orc", block_of(cultures, "cave_goblin"))
        triggers = read("common/scripted_triggers/aov_rie_portrait_triggers.txt")
        self.assertIn("portrait_aov_orc_clothing_trigger = {", triggers)
        self.assertIn("portrait_aov_orc_clothing_spouse_trigger = {", triggers)

    def test_rags_are_wired(self):
        accessories = read("gfx/portraits/accessories/aov_orc.txt")
        asset = read(f"{RAGS}/aov_orc_rags.asset")
        variations = read("gfx/portraits/accessory_variations/aov_orc.txt")
        for entity in re.findall(r'entity = "?(aov_orc_rags\w+)', accessories):
            self.assertIn(f'name = "{entity}"', asset)
        self.assertEqual(len(re.findall(r'entity = "?aov_orc_rags', accessories)), 3)
        self.assertEqual(set(re.findall(r'variation = "(\w+)"', asset)), {"aov_orc_rags"})
        self.assertIn('name = "aov_orc_rags"', variations)
        self.assertNotIn("ek2", re.sub(r"#[^\n]*", "", asset))
        for mesh in re.findall(r'"(aov_orc_rags\w+\.mesh)"', asset):
            self.assertTrue((SUBMOD / RAGS / mesh).is_file(), mesh)
        for tex in re.findall(r'"(aov_orc_rags\w+\.dds)"', asset):
            self.assertTrue((SUBMOD / RAGS / tex).is_file(), tex)
        for path in re.findall(r'"(gfx/[^"]+\.dds)"', asset + variations):
            self.assertTrue((SUBMOD / path).is_file() or (orc.DEFAULT_GAME / path).is_file(), path)

    def test_rag_palette_is_lighter_so_it_reads_on_black_skin(self):
        from eu4_import import read_dds
        ek2 = orc.DEFAULT_EK2 / orc.RAG_PALETTE_SOURCE
        if not ek2.is_file():
            self.skipTest("needs Elder Kings 2")
        _w, _h, before = read_dds(ek2.read_bytes())
        raw = (SUBMOD / orc.RAG_PALETTE).read_bytes()
        _w, _h, after = read_dds(raw)
        self.assertEqual(raw, orc.lighter_palette(ek2.read_bytes()))
        mean = lambda px: sum(px[i] for i in range(len(px)) if i % 4 != 3) / (len(px) * 3 / 4)
        self.assertGreater(mean(after), 1.5 * mean(before))
        self.assertEqual(after[3::4], before[3::4])

    def test_lighter_palette_keeps_alpha_and_caps_at_white(self):
        header = bytes(128)
        out = orc.lighter_palette(header + bytes((10, 200, 100, 77)))
        self.assertEqual(out[:128], header)
        self.assertEqual(out[128:], bytes((18, 255, 180, 77)))


class LocalizationTests(unittest.TestCase):
    def test_each_gene_is_named(self):
        text = read("localization/english/aov_orc_portraits_l_english.yml")
        self.assertTrue(text.startswith("l_english:"))
        for gene in ORC_GENES:
            self.assertRegex(text, rf'(?m)^ {gene}: "')

    def test_clothing_key_is_named(self):
        self.assertRegex(read("localization/english/aov_orc_portraits_l_english.yml"), r'(?m)^ aov_orc_clothing_gfx: "')

    def test_each_ethnicity_is_named(self):
        text = read("localization/english/aov_orc_portraits_l_english.yml")
        for ethnicity in ("orc_base", "orc_brown", "orc_gray", "orc_black"):
            self.assertRegex(text, rf'(?m)^ {ethnicity}: "')


if __name__ == "__main__":
    unittest.main()
