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
KEYS = {"hobbit", "dwarf", "dwarf_bronze", "elven", "noldor", "sindar"}


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
                "portrait_high_nobles_clothing_trigger = { CULTURE_INPUT = sindar }\n"
                "portrait_hobbit_clothing_trigger = yes\nportrait_dwarf_bronze_clothing_spouse_trigger = no\n"
                "has_clothing_gfx = elven_clothing_gfx\nhas_clothing_gfx = sindar_clothing_gfx\n"
                "has_cultural_pillar = heritage_blacklock\nhas_cultural_pillar = heritage_elven\n"
                "has_game_rule = short_dwarven_beards\nhas_game_rule = other_rule\n")
        out = bp.transform(text, KEYS)
        self.assertIn("CULTURE_INPUT = aov_dwarf }", out)
        self.assertIn("CULTURE_INPUT = aov_rie_none }", out)
        self.assertIn("portrait_commoner_clothing_trigger", out)  # a rank trigger, not a culture key
        self.assertIn("portrait_aov_hobbit_clothing_trigger = yes", out)
        self.assertIn("portrait_aov_rie_none_clothing_spouse_trigger = no", out)
        self.assertIn("has_clothing_gfx = aov_vanyar_clothing_gfx", out)  # RiE's Vanyar have the generic elven key
        self.assertIn("always = no\naov_rie_other", out)  # sindar_clothing_gfx: no culture of ours
        self.assertIn("aov_rie_other_dwarf_culture_trigger = yes", out)  # RiE's southern clans: none of ours
        self.assertIn("has_cultural_pillar = heritage_elven", out)
        self.assertIn("always = no\nhas_game_rule = other_rule", out)  # no female dwarf beards

    def test_input_parameter_is_renamed_like_culture_input(self):
        out = bp.transform("court_fashion_level_5_modifier = { INPUT_PARAMETER = northern }\n", KEYS,
                           {"northern": "aov_dwarf"})
        self.assertEqual(out, "court_fashion_level_5_modifier = { INPUT_PARAMETER = aov_dwarf }\n")

    def test_input_override(self):
        out = bp.transform("CULTURE_INPUT = dwarf\nportrait_dwarf_clothing_trigger = yes\n", KEYS,
                           {"dwarf": "aov_western_dwarf"})
        self.assertEqual(out, "CULTURE_INPUT = aov_western_dwarf\nportrait_aov_western_dwarf_clothing_trigger = yes\n")

    def test_up_to_emperor(self):
        out = bp.up_to_emperor("x = {\n\tportrait_high_nobles_clothing_trigger = {\n\t\tCULTURE_INPUT = aov_noldor\n\t}\n}\n")
        self.assertEqual(out, "x = {\n\tOR = { portrait_high_nobles_clothing_trigger = { CULTURE_INPUT = aov_noldor } "
                              "portrait_royalty_clothing_trigger = { CULTURE_INPUT = aov_noldor } "
                              "portrait_imperial_clothing_trigger = { CULTURE_INPUT = aov_noldor } }\n}\n")
        with self.assertRaises(bp.GeneratorError):
            bp.up_to_emperor("x = { }\n")

    def test_apply_template_renames_only_in_that_gene(self):
        entries = {"f.txt": {"g": ([], ["\ta = {\n\t\tdna_modifiers = {\n"
                                        "\t\t\taccessory = { mode = add gene = hairstyles template = dwarven_hairstyles }\n"
                                        "\t\t\taccessory = { mode = add gene = beards template = dwarven_hairstyles }\n"
                                        "\t\t}\n\t}\n"])}}
        out = bp.apply_template_renames(entries, {("hairstyles", "dwarven_hairstyles"): "aov_rie_dwarven_hairstyles"})
        text = out["f.txt"]["g"][1][0]
        self.assertIn("gene = hairstyles template = aov_rie_dwarven_hairstyles }", text)
        self.assertIn("gene = beards template = dwarven_hairstyles }", text)


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
        self.assertIn("portrait_aov_rie_none_clothing_trigger = {\n\talways = no\n}", text)
        self.assertEqual(sorted(re.findall(r"^(\w+) = \{", text, re.M)), sorted(bp.TRIGGER_NAMES()))

    def test_combined_input(self):
        with mock.patch.object(data, "COMBINED_INPUTS", {"aov_x": ("aov_dwarf", "aov_hobbit")}):
            text = bp.triggers_file()[bp.TRIGGERS_FILE].decode("utf-8-sig")
        self.assertIn("portrait_aov_x_clothing_trigger = {\n\tportrait_aov_dwarf_clothing_trigger = yes\n"
                      "\tNOT = { portrait_aov_hobbit_clothing_trigger = yes }\n}", text)
        self.assertIn("portrait_aov_x_clothing_spouse_trigger = {\n\tportrait_aov_dwarf_clothing_spouse_trigger = yes\n",
                      text)


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


class AccessoryRenameTests(unittest.TestCase):
    def test_only_names_inside_our_insertions_change(self):
        begin = "\t\t# Anbennar Overhaul: Realms in Exile templates (tools/build_portraits.py)\n"
        end = "\t\t# Anbennar Overhaul: end of Realms in Exile templates\n"
        text = ("\t\t\tkheteratan = {\n\t\t\t\tfemale = { 1 = female_hair_custom_05 }\n\t\t\t}\n" + begin +
                "\t\t\tdwarven = {\n\t\t\t\tfemale = { 1 = female_hair_custom_05 1 = female_hair_custom_050 }\n"
                "\t\t\t}\n" + end)
        out = bp.rename_accessories_in_templates({"g.txt": text.encode()},
                                                 {"female_hair_custom_05": "aov_rie_female_hair_custom_05"})
        new = out["g.txt"].decode()
        self.assertIn("kheteratan = {\n\t\t\t\tfemale = { 1 = female_hair_custom_05 }", new)  # Anbennar's own
        self.assertIn("1 = aov_rie_female_hair_custom_05 1 = female_hair_custom_050 }", new)


class PlaceFileTests(unittest.TestCase):
    def test_vanilla_path_is_never_overridden(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roots = bp.Roots(rie=root / "rie", anbennar=root / "anb", game=root / "game")
            for base, content in ((roots.rie, b"rie"), (roots.game / "game", b"vanilla")):
                (base / "gfx/x").mkdir(parents=True)
                (base / "gfx/x/edited.dds").write_bytes(content)
                (base / "gfx/x/same.dds").write_bytes(b"same")
            (roots.rie / "gfx/x/new.dds").write_bytes(b"new")
            files = {}
            bp.RENAMED.clear()
            self.assertIsNone(bp.place_file(roots, "new.dds", "gfx/x/new.dds", files, "gfx/shared"))
            self.assertIsNone(bp.place_file(roots, "same.dds", "gfx/x/same.dds", files, "gfx/shared"))
            self.assertEqual(bp.place_file(roots, "edited.dds", "gfx/x/edited.dds", files, "gfx/shared"),
                             "aov_rie_edited.dds")
            self.assertEqual(bp.place_file(roots, "gfx/x/edited.dds", "gfx/x/edited.dds", files, "gfx/x"),
                             "gfx/x/aov_rie_edited.dds")
        self.assertEqual(files, {"gfx/x/new.dds": b"new", "gfx/shared/aov_rie_edited.dds": b"rie",
                                 "gfx/x/aov_rie_edited.dds": b"rie"})
        bp.RENAMED.clear()


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

    def test_no_female_dwarf_beards(self):
        text = self.files[f"{bp.MODIFIERS_DIR}/aov_rie_01_beards_base.txt"].decode("utf-8-sig")
        self.assertNotIn("dwarven_females", text)
        self.assertIn("dwarven_males_vanilla", text)

    def test_elves_and_hobbit_men_wear_no_vanilla_cloak(self):
        text = self.files[f"{bp.MODIFIERS_DIR}/aov_rie_01_cloaks_base.txt"].decode("utf-8-sig")
        self.assertIn("aov_elf_no_cloak", text)
        self.assertIn("aov_hobbit_no_cloak", text)

    def test_high_elves_wear_their_rie_culture(self):
        text = self.files[f"{bp.MODIFIERS_DIR}/aov_rie_01_clothes_base.txt"].decode("utf-8-sig")
        self.assertIn("template = noldor_high_clothes", text)
        self.assertIn("template = vanyar_high_clothes", text)
        self.assertNotIn("elven_low_clothes", text)  # RiE's generic elves wear vanilla clothes
        self.assertIn("portrait_royalty_clothing_trigger = { CULTURE_INPUT = aov_noldor }", text)

    def test_clashing_template_is_copied_under_a_new_name(self):
        hair = self.files[f"{bp.MODIFIERS_DIR}/aov_rie_01_hairstyles_base.txt"].decode("utf-8-sig")
        self.assertIn("template = aov_rie_dwarven_hairstyles", hair)
        self.assertNotRegex(hair, r"template = dwarven_hairstyles\b")
        genes = self.files[f"{bp.GENES_DIR}/03_genes_special_accessories_hairstyles.txt"].decode("utf-8-sig")
        self.assertRegex(genes, r"\n\t+aov_rie_dwarven_hairstyles = \{")

    def test_edited_vanilla_textures_are_copied_once_under_new_names(self):
        braid = next(c.decode("utf-8-sig") for rel, c in self.files.items()
                     if rel.endswith("female_hair_custom_43/aov_rie_female_hair_custom_43.asset"))
        self.assertIn('"aov_rie_f_hair_western_08_diffuse.dds"', braid)
        self.assertNotIn('"f_hair_western_08_diffuse.dds"', braid)
        renamed = [rel for rel in self.files if rel.rsplit("/", 1)[-1].startswith(bp.RENAMED_PREFIX)
                   and rel.endswith(".dds")]
        self.assertTrue(renamed)
        names = [rel.rsplit("/", 1)[-1] for rel in renamed]
        self.assertEqual(len(names), len(set(names)))  # one copy each (CK3 finds textures by name)

    def test_anbennars_reused_model_names_get_rie_copies(self):
        """Anbennar reuses female_hair_custom_01..08 for Kheteratan hairstyles; RiE's lists mean its AGOT hairs."""
        hair = self.files[f"{bp.GENES_DIR}/03_genes_special_accessories_hairstyles.txt"].decode("utf-8-sig")
        inserted = "".join(re.findall(r"Realms in Exile templates \(tools/build_portraits.py\)\n(.*?)# Anbennar Overhaul: "
                                      r"end", hair, re.S))
        self.assertIn("= aov_rie_female_hair_custom_05", inserted)
        self.assertNotRegex(inserted, r"= female_hair_custom_0[1-8]\b")
        base = (REAL.anbennar / bp.GENES_DIR / "03_genes_special_accessories_hairstyles.txt").read_bytes().decode("utf-8-sig")
        outside = hair.replace(inserted, "")
        self.assertEqual(outside.count("female_hair_custom_05"), base.count("female_hair_custom_05"))  # Kheteratan's
        accessories = self.files[bp.ACCESSORIES_FILE].decode("utf-8-sig")
        self.assertIn('entity = "aov_rie_female_hair_custom_05_entity"', accessories)
        asset = next(c.decode("utf-8-sig") for rel, c in self.files.items()
                     if rel.endswith("female_hair_custom_05/aov_rie_female_hair_custom_05.asset"))
        self.assertIn('name = "aov_rie_female_hair_custom_05_mesh"', asset)
        self.assertIn('pdxmesh = "aov_rie_female_hair_custom_05_mesh"', asset)

    def test_no_copied_block_names_a_clashing_model(self):
        for rel, content in self.files.items():
            if rel.endswith(".asset") or rel == bp.ACCESSORIES_FILE:
                for kind, name in re.findall(r'\b(pdxmesh|entity)\s*=\s*"?([A-Za-z_][A-Za-z0-9_.]*)',
                                             bp.code(content.decode("utf-8-sig"))):
                    self.assertFalse(bp.model_clash(REAL, kind, name), f"{rel}: {kind} {name}")

    def test_dwarves_wear_anbennars_northern_clothes(self):
        text = self.files[f"{bp.MODIFIERS_DIR}/aov_rie_01_clothes_base.txt"].decode("utf-8-sig")
        for template in ("northern_commoner_clothes", "northern_low_nobility_clothes", "northern_high_nobility_clothes"):
            self.assertIn(f"template = {template}", text)
        self.assertIn("portrait_royalty_clothing_trigger = { CULTURE_INPUT = aov_dwarf }", text)
        self.assertNotIn("western_dwarf", text)
        for rel, content in self.files.items():
            if rel.startswith(bp.MODIFIERS_DIR):
                self.assertNotRegex(content.decode("utf-8-sig"), r"southern_dwarf|blacklock|stonefoot|dwarven_eastern", rel)

    def test_gnomes_keep_anbennars_look(self):
        self.assertNotIn("common/culture/cultures/anb_gnome.txt", bhm.build_cultures(REAL))
        self.assertFalse((bp.SUBMOD / "common/culture/cultures/anb_gnome.txt").exists())

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
        # Lichdom's skeleton portrait is imported once from Godherja, not built here (docs/systems/magic.md)
        imported = "gfx/models/portraits/aov_lich/"
        if models.is_dir():
            orphans += [p.relative_to(bp.SUBMOD).as_posix() for p in models.rglob("*")
                        if p.is_file() and p.relative_to(bp.SUBMOD).as_posix() not in produced
                        and not p.relative_to(bp.SUBMOD).as_posix().startswith(imported)]
        self.assertEqual(sorted(orphans), [], "leftover files: delete them")


if __name__ == "__main__":
    unittest.main()
