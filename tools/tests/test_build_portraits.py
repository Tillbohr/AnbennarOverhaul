"""Tests for tools/build_portraits.py (RiE portraits for halflings, gnomes, elves and dwarves).

    python -I -m unittest discover -s tools/tests -p test_build_portraits.py -v
"""

import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_holding_models as bhm  # noqa: E402
import build_portraits as bp  # noqa: E402
from data import portraits as data  # noqa: E402

REAL = bp.Roots.default()
HAVE_REAL = REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir()
KEYS = {"hobbit", "dwarf", "dwarf_bronze", "elven", "noldor"}


class ParserTests(unittest.TestCase):
    def test_blocks_by_depth(self):
        text = 'a = {\n\tb = { c = 1 }\n\td = {\n\t\te = "}"\n\t} # }\n}\nf = { }\n'
        self.assertEqual([n for n, _s, _e in bp.blocks(text, 1)], [("a",), ("f",)])
        self.assertEqual([n for n, _s, _e in bp.blocks(text, 2)], [("a", "b"), ("a", "d")])
        names, start, end = bp.blocks(text, 2)[1]
        self.assertEqual(text[start:end], '\td = {\n\t\te = "}"\n\t} # }\n')

    def test_unbalanced_raises_unless_lenient(self):
        for text in ("a = {\n", "a = { }\n}\n"):
            with self.assertRaises(bp.GeneratorError):
                bp.blocks(text, 1)
        self.assertEqual([n for n, _s, _e in bp.blocks("a = { }\n}\nb = {\n", 1, strict=False)], [("a",), ("b",)])


class TransformTests(unittest.TestCase):
    def test_inputs_triggers_gfx_heritages_rules(self):
        text = ("portrait_commoner_clothing_trigger = { CULTURE_INPUT = dwarf }\n"
                "portrait_high_nobles_clothing_trigger = { CULTURE_INPUT = noldor }\n"
                "portrait_hobbit_clothing_trigger = yes\nportrait_dwarf_bronze_clothing_spouse_trigger = no\n"
                "has_clothing_gfx = elven_clothing_gfx\nhas_clothing_gfx = noldor_clothing_gfx\n"
                "has_cultural_pillar = heritage_blacklock\nhas_cultural_pillar = heritage_elven\n"
                "has_game_rule = short_dwarven_beards\nhas_game_rule = other_rule\n")
        out = bp.transform(text, KEYS)
        self.assertIn("CULTURE_INPUT = aov_dwarf }", out)
        self.assertIn("CULTURE_INPUT = aov_rie_none }", out)
        self.assertIn("portrait_commoner_clothing_trigger", out)  # a rank trigger, not a culture key
        self.assertIn("portrait_aov_hobbit_clothing_trigger = yes", out)
        self.assertIn("portrait_aov_rie_none_clothing_spouse_trigger = no", out)
        self.assertIn("has_clothing_gfx = aov_elven_clothing_gfx", out)
        self.assertIn("always = no\naov_rie_southern", out)  # noldor_clothing_gfx: no culture of ours
        self.assertIn("aov_rie_southern_dwarf_culture_trigger = yes", out)
        self.assertIn("has_cultural_pillar = heritage_elven", out)
        self.assertIn("always = yes\nhas_game_rule = other_rule", out)

    def test_input_override(self):
        out = bp.transform("CULTURE_INPUT = dwarf\nportrait_dwarf_clothing_trigger = yes\n", KEYS,
                           {"dwarf": "aov_western_dwarf"})
        self.assertEqual(out, "CULTURE_INPUT = aov_western_dwarf\nportrait_aov_western_dwarf_clothing_trigger = yes\n")


class CultureTests(unittest.TestCase):
    FILES = {"a.txt": "﻿one = {\n\theritage = heritage_x\n\tclothing_gfx = { western_clothing_gfx }\n}\n"
                      "two = {\n\theritage = heritage_y\n\tclothing_gfx = { western_clothing_gfx }\n}\n"
                      "three = {\n\theritage = heritage_y\n\tclothing_gfx = { mena_clothing_gfx }\n}\n"}

    def test_keys_in_group_order(self):
        groups = {"south": {"label": "S", "clothing_gfx": "aov_s_clothing_gfx", "cultures": ("three",)},
                  "all": {"label": "A", "clothing_gfx": "aov_a_clothing_gfx", "heritages": ("heritage_y",)},
                  "x": {"label": "X", "clothing_gfx": "aov_x_clothing_gfx", "heritages": ("heritage_x",)}}
        with mock.patch.object(data, "CLOTHING_GROUPS", groups):
            targets = bp.clothing_targets(self.FILES)
            self.assertEqual(targets, {"three": "aov_s_clothing_gfx aov_a_clothing_gfx", "two": "aov_a_clothing_gfx",
                                       "one": "aov_x_clothing_gfx"})
            out = bp.override_clothing_gfx(self.FILES["a.txt"], targets)
        self.assertIn("\tclothing_gfx = { aov_s_clothing_gfx aov_a_clothing_gfx mena_clothing_gfx } # Anbennar Overhaul",
                      out)

    def test_lists_starting_with_one_key_must_match(self):
        groups = {"all": {"label": "A", "clothing_gfx": "aov_a_clothing_gfx", "heritages": ("heritage_y",)}}
        with mock.patch.object(data, "CLOTHING_GROUPS", groups), self.assertRaises(bp.GeneratorError):
            bp.clothing_targets(self.FILES)


class TriggerTests(unittest.TestCase):
    def test_vanilla_shape(self):
        text = bp.triggers_file()[bp.TRIGGERS_FILE].decode("utf-8-sig")
        self.assertIn("portrait_aov_hobbit_clothing_trigger = {\n\tportrait_shared_clothing_contents_trigger = {\n"
                      "\t\tCULTURE_SCOPE = scope:culture\n\t\tCULTURE_FLAG = aov_hobbit\n\t}\n}", text)
        self.assertIn("portrait_aov_hobbit_clothing_spouse_trigger = {\n\tportrait_shared_clothing_contents_trigger = {\n"
                      "\t\tCULTURE_SCOPE = culture\n", text)
        self.assertIn("portrait_aov_western_dwarf_clothing_trigger = {\n\tportrait_aov_dwarf_clothing_trigger = yes\n"
                      "\tNOT = { portrait_aov_southern_dwarf_clothing_trigger = yes }\n}", text)
        self.assertIn("portrait_aov_rie_none_clothing_trigger = {\n\talways = no\n}", text)
        self.assertEqual(sorted(re.findall(r"^(\w+) = \{", text, re.M)), sorted(bp.TRIGGER_NAMES()))


GENE_FILE = ("special_genes = {\n\taccessory_genes = {\n\t\tclothes = {\n"
             "\t\t\tkeep = {\n\t\t\t\tindex = 0\n\t\t\t\tmale = { 1 = keep_acc }\n\t\t\t}\n"
             "\t\t\tother = {\n\t\t\t\tindex = 2\n\t\t\t}\n\t\t}\n\t}\n}\n")
RIE_GENE = ("special_genes = {\n\taccessory_genes = {\n\t\tclothes = {\n"
            "\t\t\tnew_one = {\r\n\t\t\t\tindex = 40\r\n\t\t\t\tmale = { 50 = acc_a 50 = empty }\r\n"
            "\t\t\t\tfemale = { 1 = acc_b }\r\n\t\t\t}\r\n"
            "\t\t\tnew_two = {\n\t\t\t\tindex = 41\n\t\t\t\tmale = { 1 = acc_a }\n\t\t\t}\n\t\t}\n\t}\n}\n")


def _entries(*templates):
    body = "".join(f"\taccessory = {{ mode = add gene = clothes template = {t} range = {{ 0 1 }} }}\n" for t in templates)
    return {"f.txt": {"g": ([], [f"\tx = {{\n\t\tdna_modifiers = {{\n{body}\t\t}}\n\t}}\n"])}}


class GeneTests(unittest.TestCase):
    def _roots(self, tmp):
        root = Path(tmp)
        for name, text in (("anbennar", GENE_FILE), ("rie", RIE_GENE)):
            folder = root / name / bp.GENES_DIR
            folder.mkdir(parents=True)
            (folder / "05_clothes.txt").write_text("﻿" + text, "utf-8", newline="")
        (root / "game/game").mkdir(parents=True)
        return bp.Roots(rie=root / "rie", anbennar=root / "anbennar", game=root / "game")

    def test_new_templates_get_free_indices(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._roots(tmp)
            bp._texts.cache_clear()
            files, accessories, notes = bp.build_genes(roots, _entries("keep", "new_one", "new_two"))
        text = files[f"{bp.GENES_DIR}/05_clothes.txt"].decode("utf-8")
        self.assertTrue(text.startswith("﻿special_genes"))
        self.assertIn("\t\t\t}\n\t\t# Anbennar Overhaul: Realms in Exile templates (tools/build_portraits.py)\n"
                      "\t\t\tnew_one = {\n\t\t\t\tindex = 1\n", text)
        self.assertIn("new_two = {\n\t\t\t\tindex = 3\n", text)
        self.assertNotIn("\r", text)
        self.assertTrue(text.endswith("\t\t\t}\n\t\t# Anbennar Overhaul: end of Realms in Exile templates\n\t\t}\n\t}\n}\n"))
        self.assertEqual(accessories, ["acc_a", "acc_b"])
        self.assertEqual(len(notes), 1)

    def test_full_gene_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._roots(tmp)
            bp._texts.cache_clear()
            with mock.patch.object(bp, "MAX_TEMPLATE_INDEX", 2), self.assertRaises(bp.GeneratorError):
                bp.build_genes(roots, _entries("new_one", "new_two"))

    def test_unknown_template_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._roots(tmp)
            bp._texts.cache_clear()
            with self.assertRaises(bp.GeneratorError):
                bp.build_genes(roots, _entries("nowhere"))

    def tearDown(self):
        bp._texts.cache_clear()


class CopyFileTests(unittest.TestCase):
    def test_vanilla_path_keeps_vanilla(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roots = bp.Roots(rie=root / "rie", anbennar=root / "anb", game=root / "game")
            for base, content in ((roots.rie, b"rie"), (roots.game / "game", b"vanilla")):
                (base / "gfx/x").mkdir(parents=True)
                (base / "gfx/x/same.dds").write_bytes(content)
            (roots.rie / "gfx/x/new.dds").write_bytes(b"new")
            files = {}
            bp.KEPT.clear()
            bp.copy_file(roots, "gfx/x/same.dds", files)
            bp.copy_file(roots, "gfx/x/new.dds", files)
        self.assertEqual(files, {"gfx/x/new.dds": b"new"})
        self.assertEqual(bp.KEPT, ["gfx/x/same.dds"])
        bp.KEPT.clear()


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class RealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notes = []
        cls.files = bp.build_all(REAL, cls.notes)

    def test_every_listed_entry_is_copied(self):
        entries = bp.copied_entries(REAL)
        listed = sum(len(items) for groups in data.ENTRIES.values() for items in groups.values())
        copied = sum(len(texts) for groups in entries.values() for _s, texts in groups.values())
        extra = sum(len(texts) for texts in data.EXTRA_ENTRIES.values())
        self.assertGreaterEqual(copied, listed + extra)  # repeated names copy every block

    def test_no_rie_culture_input_survives(self):
        for rel, content in self.files.items():
            if rel.startswith(bp.MODIFIERS_DIR):
                text = bp.code(content.decode("utf-8-sig"))
                inputs = set(re.findall(r"CULTURE_INPUT\s*=\s*(\w+)", text))
                self.assertLessEqual(inputs, set(bp.our_inputs()), rel)
                self.assertNotRegex(text, r"heritage_(longbeard|firebeard|broadbeam|blacklock|stonefoot|ironfist|stiffbeard)")
                self.assertNotIn("has_game_rule = short_dwarven_beards", text)

    def test_groups_are_game_only_with_rie_priority(self):
        text = self.files[f"{bp.MODIFIERS_DIR}/aov_rie_04_clothes_armor.txt"].decode("utf-8-sig")
        self.assertIn("aov_rie_clothes_armor = {\n\tusage = game\n\tpriority = 4\n", text)

    def test_gene_indices_fit_a_byte_and_are_unique(self):
        for rel, content in self.files.items():
            if rel.startswith(bp.GENES_DIR):
                text = content.decode("utf-8-sig")
                for names, start, end in bp.blocks(text, 3, strict=False):
                    indices = []
                    for _n, s, e in bp.blocks(text[start:end], 2, strict=False):
                        match = bp.INDEX.search(bp.code(text[start:end][s:e]))
                        if match:
                            indices.append(int(match.group(1)))
                    self.assertEqual(len(indices), len(set(indices)), f"{rel} {names}")
                    self.assertLessEqual(max(indices, default=0), bp.MAX_TEMPLATE_INDEX, f"{rel} {names}")

    def test_gene_files_are_anbennars_plus_insertions(self):
        for rel, content in self.files.items():
            if rel.startswith(bp.GENES_DIR):
                ours = content.decode("utf-8")
                base = (REAL.anbennar / rel).read_bytes().decode("utf-8")
                begin = "\t\t# Anbennar Overhaul: Realms in Exile templates (tools/build_portraits.py)\n"
                end = "\t\t# Anbennar Overhaul: end of Realms in Exile templates\n"
                self.assertIn(begin, ours)
                stripped = re.sub(re.escape(begin) + ".*?" + re.escape(end), "", ours, flags=re.S)
                self.assertEqual(stripped, base, f"{rel}: removing the insertions must give Anbennar's file back")

    def test_copied_files_never_shadow_anbennar_or_game(self):
        for rel in self.files:
            if rel.startswith(("gfx/models/", "gfx/portraits/accessory_variations/textures")):
                self.assertFalse((REAL.anbennar / rel).exists(), rel)
                self.assertFalse((REAL.game / "game" / rel).exists(), rel)

    def test_copied_asset_names_are_new(self):
        external = bp.external_models(REAL)
        for rel, content in self.files.items():
            if rel.endswith(".asset"):
                for names, start, end in bp.blocks(content.decode("utf-8-sig"), 1):
                    body = content.decode("utf-8-sig")[start:end]
                    self.assertNotIn((names[0], bp.block_name(body)), external, rel)

    def test_culture_files_carry_clothing_keys(self):
        cultures = bhm.build_cultures(REAL)
        halfling = cultures["common/culture/cultures/anb_halfling.txt"].decode("utf-8")
        self.assertIn("clothing_gfx = { aov_hobbit_clothing_gfx western_clothing_gfx } # Anbennar Overhaul", halfling)
        dwarf = cultures["common/culture/cultures/anb_dwarf.txt"].decode("utf-8")
        self.assertIn("clothing_gfx = { aov_southern_dwarf_clothing_gfx aov_dwarf_clothing_gfx dde_abbasid_clothing_gfx "
                      "mena_clothing_gfx } # Anbennar Overhaul", dwarf)
        loc = bhm.build_localization(REAL)[bhm.LOCALIZATION_FILE].decode("utf-8")
        for group in data.CLOTHING_GROUPS.values():
            self.assertIn(f' {group["clothing_gfx"]}:0 "{group["label"]}"', loc)


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class FreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = bp.build_all(REAL)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (bp.SUBMOD / rel).is_file() or (bp.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_portraits.py")

    def test_no_orphan_files(self):
        produced = set(self.files)
        orphans = []
        for folder in ("gfx/portraits/portrait_modifiers", "gfx/portraits/accessories",
                       "gfx/portraits/accessory_variations"):
            orphans += [p.relative_to(bp.SUBMOD).as_posix() for p in (bp.SUBMOD / folder).rglob("aov_rie_*")
                        if p.relative_to(bp.SUBMOD).as_posix() not in produced]
        models = bp.SUBMOD / "gfx/models/portraits"
        if models.is_dir():
            orphans += [p.relative_to(bp.SUBMOD).as_posix() for p in models.rglob("*")
                        if p.is_file() and p.relative_to(bp.SUBMOD).as_posix() not in produced]
        self.assertEqual(sorted(orphans), [], "leftover files: delete them")


if __name__ == "__main__":
    unittest.main()
