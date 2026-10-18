"""Tests for tools/build_rie_dwarves.py (RiE dwarf buildings, mines, ore deposits).

    python -I -m unittest discover -s tools/tests -p test_build_rie_dwarves.py -v
"""

import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_portraits as bp  # noqa: E402
import build_rie_dwarves as rd  # noqa: E402
import rie_dwarf_rewrite as rw  # noqa: E402
from data import rie_dwarves as data  # noqa: E402

REAL = rd.Roots.default()
HAVE_REAL = REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir()
LEFTOVER = re.compile(r"\blotr_|\bis_dwarf\b|\bis_orc\b|dwarven_depths_|elven_settlement_")


def fake_roots(tmp: Path, dwarf_text: str, anbennar_buildings: str = "") -> rd.Roots:
    rie, anbennar, game = tmp / "rie", tmp / "anbennar", tmp / "game"
    for rel, text in ((data.RIE_BUILDING_FILES[0], dwarf_text), (data.RIE_BUILDING_FILES[1], "")):
        (rie / rel).parent.mkdir(parents=True, exist_ok=True)
        (rie / rel).write_text(text, encoding="utf-8")
    (anbennar / "common/buildings").mkdir(parents=True)
    (anbennar / "common/buildings/00_test.txt").write_text(anbennar_buildings, encoding="utf-8")
    (game / "game/common").mkdir(parents=True)
    return rd.Roots(rie=rie, anbennar=anbennar, game=game)


def top_keys(text: str) -> list:
    return [names[0] for names, _s, _e in bp.blocks(text, 1, strict=False)]


def block_of(text: str, key: str) -> str:
    for names, start, end in bp.blocks(text, 1, strict=False):
        if names[0] == key:
            return text[start:end]
    raise KeyError(key)


def sub_block(body: str, name: str) -> str:
    """The first depth-2 block called name inside a building block ('' when absent)."""
    for names, start, end in bp.blocks(body, 2, strict=False):
        if names[-1] == name:
            return body[start:end]
    return ""


class StopTests(unittest.TestCase):
    def test_unknown_trigger_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tis_enabled = {\n\t\tlotr_made_up = yes\n\t}\n}\n")
            with self.assertRaises(rd.GeneratorError) as caught:
                rd.build_all(roots)
            self.assertIn("lotr_made_up", str(caught.exception))
            self.assertIn("dwarven_test_01", str(caught.exception))

    def test_key_collision_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tcost_gold = 10\n}\n",
                               "dwarven_test_01 = {\n\tcost_gold = 20\n}\n")
            with self.assertRaises(rd.GeneratorError) as caught:
                rd.build_all(roots)
            self.assertIn("dwarven_test_01", str(caught.exception))


    def test_unrenamed_rie_trigger_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tis_enabled = {\n\t\trie_only_trigger = yes\n\t}\n}\n")
            (roots.rie / "common/scripted_triggers").mkdir(parents=True)
            (roots.rie / "common/scripted_triggers/x.txt").write_text("rie_only_trigger = {\n\talways = yes\n}\n")
            with self.assertRaisesRegex(rd.GeneratorError, "RiE scripted trigger rie_only_trigger has no rename"):
                rd.build_all(roots)

    def test_unknown_modifier_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tprovince_modifier = {\n\t\tmade_up_mult = 1\n\t}\n}\n")
            with self.assertRaisesRegex(rd.GeneratorError, "dwarven_test_01: modifier made_up_mult"):
                rd.build_all(roots)

    def test_rie_value_copied_with_its_variables(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tlevy = rie_value\n}\n")
            (roots.rie / "common/script_values").mkdir(parents=True)
            (roots.rie / "common/script_values/v.txt").write_text(
                "@unused = 5\n@a = 1\n@b = @[a + 1]\nrie_value = @[b]\nother = 2\n")
            build = rd.Build(roots, [])
            rd.render_buildings(build)
            rd.render_values(build)
            text = build.files[rd.VALUES_FILE].decode("utf-8-sig")
            self.assertIn("@a = 1\n@b = @[a + 1]\n", text)
            self.assertIn("\nrie_value = @[b]\n", text)
            self.assertNotIn("unused", text)
            self.assertNotIn("other", text)

    def test_unknown_value_stops_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = fake_roots(Path(tmp), "dwarven_test_01 = {\n\tlevy = nowhere_value\n}\n")
            with self.assertRaisesRegex(rd.GeneratorError, "script value nowhere_value"):
                rd.build_all(roots)


class HelperTests(unittest.TestCase):
    def test_reindent_uses_tabs_by_depth(self):
        text = "a = {\n \tb = 1\n    c = {\n  d = 2   \n\t\t}\n}\n"
        self.assertEqual(rd.reindent(text), "a = {\n\tb = 1\n\tc = {\n\t\td = 2\n\t}\n}\n")
        self.assertEqual(rd.reindent("x = 1\n", 1), "\tx = 1\n")

    def test_removal_note_groups_levels(self):
        note = rd.removal_note("x", ["removed is_orc = yes", "removed is_orc = yes",
                                     "removed effect_desc dwarven_forge_01_artifact_crafting_buff",
                                     "removed effect_desc dwarven_forge_02_artifact_crafting_buff"])
        self.assertIn("removed is_orc = yes x2", note)
        self.assertIn("removed effect_desc dwarven_forge_NN_artifact_crafting_buff x2", note)

    def test_crafting_lifestyle_xp_dropped(self):
        out, notes = rw.rewrite_block("x_01 = {\n\tcharacter_modifier = {\n\t\tmonthly_crafting_lifestyle_xp_gain_mult"
                                      " = 0.01\n\t}\n\tcost_gold = 10\n}\n", set())
        self.assertNotIn("crafting", out)
        self.assertNotIn("character_modifier", out)
        self.assertEqual(notes, ["removed monthly_crafting_lifestyle_xp_gain_mult = 0.01"])


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class RealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notes = []
        cls.files = rd.build_all(REAL, cls.notes)
        cls.texts = {rel: c.decode("utf-8-sig") for rel, c in cls.files.items() if rel.endswith((".txt", ".yml"))}
        cls.ours = cls.texts[rd.BUILDINGS_FILE] + cls.texts[rd.MINES_FILE]
        cls.keys = top_keys(cls.ours)
        cls.rie = {}
        for rel in data.RIE_BUILDING_FILES:
            cls.rie.update(rd.rie_blocks(REAL, rel))

    def test_every_rie_building_copied_once(self):
        self.assertEqual(sorted(self.keys), sorted(self.rie))
        self.assertEqual(len(self.keys), len(set(self.keys)))
        self.assertEqual(len(self.keys), 380)

    def test_no_rie_identifiers_left(self):
        for rel, text in self.texts.items():
            if rel.endswith(".txt"):
                self.assertIsNone(LEFTOVER.search(bp.code(text)), rel)

    def test_dwarf_gates_survive(self):
        gated = [key for key, body in self.rie.items() if re.search(r"\bis_dwarf\b", bp.code(sub_block(body, "is_enabled")))]
        self.assertGreater(len(gated), 100)
        for key in gated:
            self.assertIn("is_dwarvish_culture = yes", sub_block(block_of(self.ours, key), "is_enabled"), key)

    def test_mines_need_their_deposit(self):
        for ore in data.ORES:
            for n in range(1, 11):
                body = block_of(self.texts[rd.MINES_FILE], f"{ore}_mines_{n:02d}")
                self.assertIn(f"has_province_modifier = mining_{ore}_province_modifier",
                              sub_block(body, "can_construct_potential"))

    def test_ore_modifiers_verbatim(self):
        rie = dict(rd.rie_blocks(REAL, data.ORE_FILE))
        ours = self.texts[rd.ORE_MODIFIERS_FILE]
        self.assertEqual(top_keys(ours), [f"mining_{ore}_province_modifier" for ore in data.ORES])
        for ore in data.ORES:
            key = f"mining_{ore}_province_modifier"
            self.assertEqual(block_of(ours, key), rie[key])

    def test_rie_only_script_values_copied(self):
        values = self.texts[rd.VALUES_FILE]
        self.assertRegex(values, r"(?m)^elven_building_garrison_reinforcement_factor_tier_1\s*=")
        defined = set(top_keys(values)) | set(re.findall(r"(?m)^(\w+)\s*=", bp.code(values)))
        external = rd.external_script_values(REAL)
        used = set()
        for text in (self.ours, *rd.depths_level_effects(REAL).values()):
            code = bp.code(text)
            used |= set(re.findall(r"\b(?:cost_gold|levy|max_garrison|garrison_reinforcement_factor|construction_time)"
                                   r"\s*=\s*([A-Za-z_]\w*)", code))
        self.assertIn("elven_building_garrison_reinforcement_factor_tier_1", used)
        for name in used:
            self.assertTrue(name in defined or name in external, name)
        for var in set(re.findall(r"@\[([^\]]*)\]", values)):
            for name in re.findall(r"[A-Za-z_]\w*", var):
                self.assertRegex(values, rf"(?m)^@{name}\s*=", name)

    def test_loc_for_every_building_and_tooltip(self):
        loc = set(re.findall(r"(?m)^ ([\w.\-']+):\d*\s", self.texts[rd.LOC_FILE]))
        external = rd.external_loc_keys(REAL)
        has = lambda key: key in loc or key in external  # noqa: E731
        nexts = set(re.findall(r"\bnext_building\s*=\s*(\w+)", bp.code(self.ours)))
        for key in self.keys:
            self.assertTrue(has(f"building_{key}"), key)
            if key not in nexts:
                self.assertTrue(has(f"building_type_{key}"), key)
        for key in set(re.findall(r"\b(?:text|effect_desc|desc)\s*=\s*(\w+)", bp.code(self.ours))):
            self.assertTrue(has(key), key)
        for ore in data.ORES:
            self.assertTrue(has(f"mining_{ore}_province_modifier"), ore)

    def test_type_icons_exist(self):
        icons = set(re.findall(r'\btype_icon\s*=\s*"([^"]+)"', self.ours))
        self.assertGreater(len(icons), 20)
        for icon in icons:
            rel = f"{rd.ICON_DIR}/{icon}"
            self.assertTrue(rel in self.files or bp._exists_outside(REAL, rel) is not None, icon)

    def test_files_have_bom_and_lf(self):
        for rel, content in self.files.items():
            if rel.endswith((".txt", ".yml")):
                self.assertTrue(content.startswith(rd.BOM.encode("utf-8")), rel)
                self.assertNotIn(b"\r", content, rel)
                text = content.decode("utf-8-sig")
                self.assertIn("tools/build_rie_dwarves.py", text.split("\n", 3)[0 if rel.endswith(".txt") else 1])

    def test_depths_level_effects(self):
        effects = rd.depths_level_effects(REAL)
        self.assertEqual(sorted(effects), list(range(1, 11)))
        self.assertIn("fort_level = 20", effects[10])
        self.assertIn("building_slot_add = 9", effects[10])
        for n, text in effects.items():
            self.assertRegex(text, r"(?m)^\tprovince_modifier = \{$", n)
            self.assertRegex(text, r"(?m)^\tlevy = ", n)
            self.assertNotIn("parameter", bp.code(text), n)
            self.assertIsNone(LEFTOVER.search(bp.code(text)), n)
            self.assertNotRegex(text, r"\b(?:can_construct|is_enabled|asset|ai_value|next_building|cost_gold)\b", n)

    def test_removal_note_lists_only_rule_removals(self):
        note = next(n for n in self.notes if n.startswith("removed from RiE's buildings"))
        for item in re.findall(r"(?:^|; )([^;]+?) x\d+", note.split(": ", 1)[1]):
            self.assertRegex(item, r"^(removed (is_orc = yes|has_dynasty_perk = lotr_\w+|has_innovation = "
                                   r"innovation_iron_hills_goat_domestication|has_building_or_higher = elven_settlement_NN|"
                                   r"province_dynasty_modifier \(lotr_\w+\)|effect_desc \w+_artifact_crafting_buff|"
                                   r"monthly_crafting_lifestyle_xp_gain_mult = N|\w+ block gated on parameter \w+)"
                                   r"|ungated parameter unlock_full_delving)$")


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class FreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = rd.build_all(REAL)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (rd.SUBMOD / rel).is_file() or (rd.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_rie_dwarves.py")

    def test_no_orphan_files(self):
        produced = set(self.files)
        orphans = []
        root = rd.SUBMOD / rd.ICON_DIR
        if root.is_dir():
            orphans += [p.relative_to(rd.SUBMOD).as_posix() for p in root.rglob("*") if p.is_file()]
        for folder in rd.OWNED_FOLDERS:
            root = rd.SUBMOD / folder
            if root.is_dir():
                orphans += [p.relative_to(rd.SUBMOD).as_posix() for p in root.glob("aov_rie_*") if p.is_file()]
        self.assertEqual(sorted(o for o in orphans if o not in produced), [], "leftover files: delete them")


if __name__ == "__main__":
    unittest.main()
