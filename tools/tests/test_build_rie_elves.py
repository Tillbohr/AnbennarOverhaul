"""Tests for tools/build_rie_elves.py (RiE's elven holding and elf buildings as the Elven Haven).

    python -I -m unittest discover -s tools/tests -p test_build_rie_elves.py -v
"""

import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_portraits as bp  # noqa: E402
import build_rie_dwarves as rd  # noqa: E402
import build_rie_elves as re_  # noqa: E402
from data import rie_elves as data  # noqa: E402

REAL = re_.Roots.default()
HAVE_REAL = REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir()
ONE_LINE = {"elven_test": 1}
ONE_NAME = {"elven_test_01": ("Test Glade", "A test."), "building_type_elven_test_01": ("Tests", "Testing.")}


def fake_roots(tmp: Path, elf_text: str, anbennar_buildings: str = "") -> re_.Roots:
    rie, anbennar, game = tmp / "rie", tmp / "anbennar", tmp / "game"
    for rel, text in ((data.RIE_BUILDINGS_FILE, elf_text), (data.RIE_SETTLEMENT_FILE, ""),
                      (data.RIE_TRIGGERS_FILE, "")):
        (rie / rel).parent.mkdir(parents=True, exist_ok=True)
        (rie / rel).write_text(text, encoding="utf-8")
    (anbennar / "common/buildings").mkdir(parents=True)
    (anbennar / "common/buildings/00_test.txt").write_text(anbennar_buildings, encoding="utf-8")
    (game / "game/common").mkdir(parents=True)
    return re_.Roots(rie=rie, anbennar=anbennar, game=game)


def buildings_text(roots, **patches) -> str:
    with mock.patch.object(data, "LINES", ONE_LINE), mock.patch.object(data, "NAMES", ONE_NAME):
        build = rd.Build(roots, [])
        re_.render_buildings(build)
        return build.files[re_.BUILDINGS_FILE].decode("utf-8-sig")


def block(potential: str, extra: str = "") -> str:
    return f"elven_test_01 = {{\n\tcan_construct_potential = {{\n{potential}\t}}\n{extra}\tcost_gold = 10\n}}\n"


class RewriteTests(unittest.TestCase):
    def test_is_elf_becomes_elvish_culture(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = buildings_text(fake_roots(Path(tmp), block("\t\tscope:holder = { is_elf = yes }\n")))
            self.assertIn("scope:holder = { is_elvish_culture = yes }", out)
            self.assertNotIn("is_elf ", out)

    def test_maiar_or_collapses(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = buildings_text(fake_roots(Path(tmp), block(
                "\t\tscope:holder = {\n\t\t\tOR = {\n\t\t\t\tis_elf = yes\n\t\t\t\tis_valinor_maiar_character = yes\n"
                "\t\t\t}\n\t\t}\n")))
            self.assertNotIn("maiar", out)
            self.assertIn("is_elvish_culture = yes", out)

    def test_parameter_unknown_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = buildings_text(fake_roots(Path(tmp), block(
                "\t\tscope:holder = { is_elf = yes }\n",
                "\tprovince_modifier = {\n\t\tparameter = rie_only_parameter\n\t\ttax_mult = 0.1\n\t}\n")))
            self.assertNotIn("rie_only_parameter", out)
            self.assertNotIn("province_modifier", out)


class StopTests(unittest.TestCase):
    def test_unknown_trigger_stops_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), block("\t\tscope:holder = { is_elf = yes }\n\t\tlotr_made_up = yes\n"))
            with self.assertRaisesRegex(rd.GeneratorError, "elven_test_01: unknown trigger lotr_made_up"):
                buildings_text(roots)

    def test_key_collision_stops_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), block("\t\tscope:holder = { is_elf = yes }\n"),
                               "elven_test_01 = {\n\tcost_gold = 20\n}\n")
            with self.assertRaisesRegex(rd.GeneratorError, "elven_test_01"):
                buildings_text(roots)

    def test_missing_level_stops_the_build(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(data, "LINES", {"elven_test": 2}):
            roots = fake_roots(Path(tmp), block("\t\tscope:holder = { is_elf = yes }\n"))
            with self.assertRaisesRegex(rd.GeneratorError, "elven_test.*elven_test_02"):
                re_.render_buildings(rd.Build(roots, []))

    def test_block_without_elf_check_stops_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), block("\t\talways = yes\n"))
            with self.assertRaisesRegex(rd.GeneratorError, "elven_test_01: no elven holder check"):
                buildings_text(roots)


@unittest.skipUnless(HAVE_REAL, "needs RiE, Anbennar and the game")
class RealBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = re_.build_all(REAL)
        cls.buildings = cls.files[re_.BUILDINGS_FILE].decode("utf-8-sig")
        cls.loc = cls.files[re_.LOC_FILE].decode("utf-8-sig")

    def test_every_block_checks_an_elven_holder(self):
        keys = []
        for names, start, end in bp.blocks(self.buildings, 1, strict=False):
            if "is_elvish_culture = yes" not in re_.build_gates(self.buildings[start:end]):
                keys.append(names[0])
        self.assertEqual(keys, [])

    def test_every_included_level_is_copied(self):
        copied = {names[0] for names, _s, _e in bp.blocks(self.buildings, 1, strict=False)}
        expected = {f"{line}_{n:02d}" for line, count in data.LINES.items() for n in range(1, count + 1)}
        self.assertEqual(copied, expected)

    def test_loc_is_ours(self):
        for key, (name, desc) in data.NAMES.items():
            loc_key = key if key.startswith("building_type_") else f"building_{key}"
            self.assertIn(f' {loc_key}: "{name}"\n', self.loc)
            self.assertIn(f' {loc_key}_desc: "{desc}"\n', self.loc)

    def test_no_middle_earth_in_output(self):
        for rel, content in self.files.items():
            if rel.endswith((".txt", ".yml")):
                text = content.decode("utf-8-sig")
                self.assertIsNone(re.search(r"\blotr_|\bis_elf\b|maiar|hope_or_higher", text), rel)
        self.assertIsNone(re.search(data.FORBIDDEN_LORE, self.loc))

    def test_triggers_use_known_terrains_only(self):
        triggers = self.files[re_.TRIGGERS_FILE].decode("utf-8-sig")
        for name in data.COPIED_TRIGGERS.values():
            self.assertIn(f"{name} = {{", triggers)
        self.assertNotIn("mallorn_forest", triggers)
        self.assertNotIn("deep_forest", triggers)


@unittest.skipUnless(HAVE_REAL, "needs RiE, Anbennar and the game")
class FreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = re_.build_all(REAL)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (re_.SUBMOD / rel).is_file() or (re_.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_rie_elves.py")

    def test_no_orphan_files(self):
        produced = set(self.files)
        orphans = []
        for folder, patterns in re_.OWNED_FOLDERS.items():
            root = re_.SUBMOD / folder
            if root.is_dir():
                orphans += [p.relative_to(re_.SUBMOD).as_posix() for pattern in patterns for p in root.glob(pattern)
                            if p.is_file()]
        self.assertEqual(sorted(o for o in orphans if o not in produced), [], "leftover files: delete them")


if __name__ == "__main__":
    unittest.main()
