"""Tests for tools/rie_units.py (RiE army models, built by tools/build_holding_models.py).

    python -I -m unittest discover -s tools/tests -p test_rie_units.py -v
"""

import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_holding_models as bhm  # noqa: E402
import rie_units as ru  # noqa: E402
from data import unit_models as data  # noqa: E402

REAL = bhm.Roots.default()
CULTURES = (
    "﻿alpha = {\n"
    "\theritage = heritage_x\n"
    "\tunit_gfx = { western_unit_gfx }\n"
    "}\n"
    "beta = {\n"
    "\theritage = heritage_x\n"
    "\t# unit_gfx = { old }\n"
    "\tunit_gfx = { western_unit_gfx }\n"
    "}\n"
    "gamma = {\n"
    "\theritage = heritage_x\n"
    "\tunit_gfx = { mena_unit_gfx }\n"
    "}\n"
)
GROUPS = {"x": {"label": "X", "unit_gfx": "aov_x_unit_gfx", "cultures": ("alpha", "beta")}}
ASSETS = (
    "﻿pdxmesh = {\n"
    '\tname = "man_mesh"\n'
    '\tfile = "man.mesh"\n'
    '\tanimation = { id = "idle" type = "../animations/idle.anim" }\n'
    '\tmeshsettings = {\n\t\tname = "body"\n\t\ttexture_diffuse = "man_diffuse.dds"\n\t\tshader = "standard"\n\t}\n'
    "}\n"
    "entity = {\n"
    '\tname = "man_entity"\n'
    '\tpdxmesh = "man_mesh"\n'
    '\tstate = { name = "idle" event = { node = hand entity = "sword_entity" attachment_id = weapon } }\n'
    "}\n"
    "pdxmesh = {\n"
    '\tname = "sword_mesh"\n'
    '\tfile = "sword.mesh" # comment "unused.dds"\n'
    "}\n"
    "entity = {\n"
    '\tname = "sword_entity"\n'
    '\tpdxmesh = "sword_mesh"\n'
    "}\n"
    "entity = {\n"
    '\tname = "unused_entity"\n'
    '\tpdxmesh = "missing_mesh"\n'
    "}\n"
)


def _tree(tmp: Path) -> Path:
    models = tmp / "gfx/models"
    (models / "units/men").mkdir(parents=True)
    (models / "units/men/men.asset").write_text(ASSETS, "utf-8")
    for name in ("man.mesh", "man_diffuse.dds", "sword.mesh"):
        (models / "units/men" / name).write_bytes(name.encode())
    return models


class CultureTests(unittest.TestCase):
    def test_targets_and_override(self):
        with mock.patch.object(data, "UNIT_GROUPS", GROUPS):
            targets = ru.unit_targets({"a.txt": CULTURES})
        self.assertEqual(targets, {"alpha": "aov_x_unit_gfx", "beta": "aov_x_unit_gfx"})
        out = ru.override_unit_gfx(CULTURES, targets)
        self.assertIn("\tunit_gfx = { aov_x_unit_gfx western_unit_gfx } # Anbennar Overhaul\n", out)
        self.assertIn("\t# unit_gfx = { old }\n", out)  # the commented line is skipped
        self.assertEqual(out.count("aov_x_unit_gfx"), 2)
        self.assertIn("\tunit_gfx = { mena_unit_gfx }\n", out)

    def test_group_with_two_lists_raises(self):
        groups = {"x": dict(GROUPS["x"], cultures=("alpha", "gamma"))}
        with mock.patch.object(data, "UNIT_GROUPS", groups), self.assertRaises(bhm.GeneratorError):
            ru.unit_targets({"a.txt": CULTURES})

    def test_culture_in_two_groups_raises(self):
        groups = dict(GROUPS, y={"label": "Y", "unit_gfx": "aov_y_unit_gfx", "cultures": ("beta",)})
        with mock.patch.object(data, "UNIT_GROUPS", groups), self.assertRaises(bhm.GeneratorError):
            ru.unit_targets({"a.txt": CULTURES})

    def test_culture_without_unit_line_raises(self):
        with self.assertRaises(bhm.GeneratorError):
            ru.override_unit_gfx("a = {\n\theritage = h\n}\n", {"a": "x"})


class LinkTests(unittest.TestCase):
    def test_links_follow_the_pips(self):
        models = {"x": ((1, "one_entity"), (3, "two_entity"))}
        with mock.patch.object(data, "UNIT_GROUPS", GROUPS), mock.patch.object(data, "ARMY_MODELS", models):
            text = ru.entity_links_text()
        self.assertTrue(text.startswith("﻿"))
        self.assertIn("aov_x_army_01 = {\n\ttype = army\n\tgraphical_cultures = { aov_x_unit_gfx }\n"
                      "\tentity = one_entity\n}", text)
        self.assertIn("aov_x_army_02 = {\n\ttype = army\n\tquality = 3\n\tgraphical_cultures = { aov_x_unit_gfx }\n"
                      "\tentity = two_entity\n}", text)

    def test_localization_names_every_key(self):
        with mock.patch.object(data, "UNIT_GROUPS", GROUPS):
            self.assertEqual(ru.localization_lines(), [' aov_x_unit_gfx:0 "X"'])

    def test_bad_pips_raise(self):
        for models in ({"x": ((2, "a"),)}, {"x": ((1, "a"), (1, "b"))}, {"x": ((1, "a"), (6, "b"))}):
            with mock.patch.object(data, "UNIT_GROUPS", GROUPS), mock.patch.object(data, "ARMY_MODELS", models):
                with self.assertRaises(bhm.GeneratorError):
                    ru.entity_links_text()


class BlockTests(unittest.TestCase):
    def test_collects_attachments_first_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = _tree(Path(tmp))
            blocks = ru.collect_blocks(models, ["man_entity", "sword_entity"])
        self.assertEqual([(k, n) for k, n, _b, _p in blocks],
                         [("pdxmesh", "man_mesh"), ("pdxmesh", "sword_mesh"), ("entity", "sword_entity"),
                          ("entity", "man_entity")])
        self.assertEqual(ru.referenced_files(blocks[0][2]), ["man.mesh", "man_diffuse.dds"])
        self.assertEqual(ru.referenced_files(blocks[1][2]), ["sword.mesh"])  # the comment's file is ignored

    def test_missing_block_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = _tree(Path(tmp))
            with self.assertRaises(bhm.GeneratorError):
                ru.collect_blocks(models, ["unused_entity"])

    def test_animation_and_shader_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = _tree(Path(tmp))
            blocks = ru.collect_blocks(models, ["man_entity"])
            game = Path(tmp) / "ck3"
            with self.assertRaises(bhm.GeneratorError):
                ru.check_animations(blocks, game)
            (game / ru.ANIMATIONS_DIR).mkdir(parents=True)
            (game / ru.ANIMATIONS_DIR / "idle.anim").write_bytes(b"")
            ru.check_animations(blocks, game)
        ru.check_unit_shaders(blocks, "Effect standard\n{\n}\n")
        with self.assertRaises(bhm.GeneratorError):
            ru.check_unit_shaders(blocks, "Effect standard_usercolor\n{\n}\n")

    def test_asset_text_keeps_blocks_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = _tree(Path(tmp))
            blocks = ru.collect_blocks(models, ["sword_entity"])
            text = ru.asset_text(blocks, models)
        self.assertTrue(text.startswith("﻿"))
        self.assertIn('# pdxmesh sword_mesh from RiE gfx/models/units/men/men.asset\npdxmesh = {\n\tname = "sword_mesh"\n'
                      '\tfile = "sword.mesh" # comment "unused.dds"\n}\n', text)
        self.assertNotIn("unused_entity", text)


@unittest.skipUnless(REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir(), "RiE, Anbennar and game needed")
class RealUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = ru.build_units(REAL)
        cls.cultures = bhm.build_cultures(REAL)

    def test_every_target_culture_gets_its_unit_key(self):
        targets = ru.unit_targets(bhm.culture_texts(REAL))
        self.assertEqual({targets[c] for c in ("wood_elvish", "sun_elvish", "moon_elvish")},
                         {"aov_wood_elf_unit_gfx", "aov_sun_elf_unit_gfx", "aov_moon_elf_unit_gfx"})
        dwarves = [c for c, key in targets.items() if key == "aov_dwarven_unit_gfx"]
        self.assertGreaterEqual(len(dwarves), 11)
        blocks = {name: body for content in self.cultures.values()
                  for name, _s, _e, body in bhm.culture_blocks(content.decode("utf-8"))}
        for culture, key in targets.items():
            block = blocks[culture]
            self.assertRegex(block, r"\tunit_gfx = \{ " + key + r" \w+_unit_gfx \} # Anbennar Overhaul\n")

    def test_links_name_copied_entities(self):
        links = self.files[ru.LINKS_FILE].decode("utf-8-sig")
        assets = self.files[ru.ASSET_FILE].decode("utf-8-sig")
        linked = re.findall(r"\tentity = (\S+)", links)
        self.assertEqual(len(linked), 9)
        for entity in linked:
            self.assertIn(f'entity = {{\n\tname = "{entity}"', assets)
        self.assertIn("quality = 4", links)

    def test_every_referenced_file_is_copied(self):
        assets = self.files[ru.ASSET_FILE].decode("utf-8-sig")
        for ref in set(ru.referenced_files(assets)):
            self.assertIn(f"{ru.ASSET_DIR}/{ref}", self.files)
        self.assertEqual(len(self.files), 2 + len(set(ru.referenced_files(assets))))

    def test_no_orphan_unit_files(self):
        folder = bhm.SUBMOD / ru.ASSET_DIR
        orphans = sorted(p.relative_to(bhm.SUBMOD).as_posix() for p in folder.rglob("*")
                         if p.is_file() and p.relative_to(bhm.SUBMOD).as_posix() not in self.files)
        self.assertEqual(orphans, [], "leftover files: delete them")


if __name__ == "__main__":
    unittest.main()
