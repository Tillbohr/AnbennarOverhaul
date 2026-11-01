"""Tests for tools/build_dynasty_names.py.

    python -I -m unittest discover -s tools/tests -p "test_build_dynasty_names*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_dynasty_names as bdn  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from pdx_script import parse_blocks  # noqa: E402

NAME_LIST_FIXTURE = """name_list_test = {

\t#TODO - replace placeholder dynasty names
\tcadet_dynasty_names = {
\t\t{ "dynnp_de" "dynn_Bohun" }
\t\t"dynn_Myall"
\t}

\tdynasty_names = {
\t\t{ "dynnp_de" "dynn_Bohun" } # a comment {
\t}

\tmale_names = {
\t\tAlen Godric
\t}
\tmercenary_names = {
\t\t{ name = "mercenary_company_test" }
\t}
}"""

HAVE_REAL = (bdn.ANBENNAR_CK3 / bdn.NAME_LIST_DIR).is_dir()


class SplitPrefixTests(unittest.TestCase):
    def test_prefixes(self):
        self.assertEqual(bdn.split_prefix("síl na Trísfer"), ("dynnp_sil_na", "Trísfer"))
        self.assertEqual(bdn.split_prefix("sílna Galvin"), ("dynnp_silna", "Galvin"))
        self.assertEqual(bdn.split_prefix("síl Vivin"), ("dynnp_sil", "Vivin"))
        self.assertEqual(bdn.split_prefix("sina Gabelf"), ("dynnp_sina", "Gabelf"))
        self.assertEqual(bdn.split_prefix("sína Gren"), ("dynnp_sina", "Gren"))
        self.assertEqual(bdn.split_prefix("of the Greatmarch"), ("dynnp_of", "the Greatmarch"))
        self.assertEqual(bdn.split_prefix("az-Segh"), ("dynnp_az", "Segh"))

    def test_no_prefix(self):
        self.assertEqual(bdn.split_prefix("Gerwick"), (None, "Gerwick"))
        self.assertEqual(bdn.split_prefix("Silurion"), (None, "Silurion"))  # síl fused into the name
        self.assertEqual(bdn.split_prefix("Offenbach"), (None, "Offenbach"))


class LocKeysTests(unittest.TestCase):
    def test_existing_text_reuses_its_key(self):
        keys = bdn.LocKeys({"dynn_Vivin": "Vivin"})
        self.assertEqual(keys.key("Vivin"), "dynn_Vivin")
        self.assertEqual(keys.new, {})

    def test_new_text_gets_an_ascii_key(self):
        keys = bdn.LocKeys({})
        self.assertEqual(keys.key("Ór Esta"), "dynn_Or_Esta")
        self.assertEqual(keys.key("Ór Esta"), "dynn_Or_Esta")
        self.assertEqual(keys.new, {"dynn_Or_Esta": "Ór Esta"})

    def test_key_taken_by_other_text_is_not_reused(self):
        keys = bdn.LocKeys({"dynn_Ros": "Ros"})
        self.assertEqual(keys.key("Rós"), "dynn_aov_Ros")
        self.assertEqual(keys.key("Ròs"), "dynn_aov_Ros_3")


class ReplaceNamesTests(unittest.TestCase):
    def test_both_name_blocks_replaced_and_todo_dropped(self):
        out = bdn.replace_names(NAME_LIST_FIXTURE, ['"dynn_A"', '{ "dynnp_sil" "dynn_B" }'])
        body = parse_blocks(out)["name_list_test"]
        blocks = parse_blocks(body)
        for name in bdn.NAME_BLOCKS:
            self.assertEqual(blocks[name].split("\n"), ['"dynn_A"', '\t\t{ "dynnp_sil" "dynn_B" }'])
        self.assertNotIn("TODO", out)
        self.assertNotIn("Bohun", out)

    def test_other_blocks_kept_verbatim(self):
        out = bdn.replace_names(NAME_LIST_FIXTURE, ['"dynn_A"'])
        self.assertIn("\tmale_names = {\n\t\tAlen Godric\n\t}", out)
        self.assertIn('\t\t{ name = "mercenary_company_test" }', out)

    def test_missing_dynasty_names_is_an_error(self):
        with self.assertRaises(GeneratorError):
            bdn.replace_names("name_list_test = {\n\tmale_names = {\n\t\tAlen\n\t}\n}", ['"dynn_A"'])


@unittest.skipUnless(HAVE_REAL, "needs Anbennar")
class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loc = bdn.dynasty_loc([bdn.ANBENNAR_CK3, bdn.GAME])
        cls.taken = bdn.start_dynasty_names(bdn.ANBENNAR_CK3, cls.loc)
        cls.blocks = bdn.name_list_blocks(bdn.ANBENNAR_CK3)

    def test_every_placeholder_list_is_covered(self):
        placeholder = {k for k, (_, block) in self.blocks.items() if any(p in block for p in bdn.PLACEHOLDERS)}
        self.assertEqual(placeholder, set(bdn.NAME_LISTS))

    def test_every_source_used_and_named(self):
        used = {k for sources in bdn.NAME_LISTS.values() for k in sources}
        self.assertEqual(used, set(bdn.EU4_DYNASTY_NAMES))
        for source, names in bdn.EU4_DYNASTY_NAMES.items():
            self.assertTrue(names, source)
            self.assertEqual(len(names), len(set(names)), source)

    def test_each_list_keeps_enough_names(self):
        for name_list in bdn.NAME_LISTS:
            self.assertGreaterEqual(len(bdn.list_names(name_list, self.taken)), 15, name_list)

    def test_no_game_start_dynasty_name_repeated(self):
        for name_list in bdn.NAME_LISTS:
            for name in bdn.list_names(name_list, self.taken):
                self.assertNotIn(bdn.split_prefix(name)[1], self.taken, name_list)

    def test_prefixes_have_loc(self):
        prefixes = {p for _, p in bdn.PREFIXES}
        loc = set()
        for root in (bdn.ANBENNAR_CK3, bdn.GAME):
            for path in (root / "localization" / "english").rglob("*_l_english.yml"):
                loc.update(re.findall(r"^\s*(dynnp_\w+):", path.read_bytes().decode("utf-8-sig", "replace"), re.M))
        self.assertEqual(prefixes - loc, set())


@unittest.skipUnless(HAVE_REAL, "needs Anbennar")
class FreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = bdn.build_all(bdn.ANBENNAR_CK3)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (bdn.SUBMOD / rel).is_file() or (bdn.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_dynasty_names.py")

    def test_every_used_key_has_loc(self):
        lists = self.files[bdn.LISTS_FILE].decode("utf-8-sig")
        ours = set(re.findall(r"^ (dynn_\w+):", self.files[bdn.LOC_FILE].decode("utf-8-sig"), re.M))
        loc = bdn.dynasty_loc([bdn.ANBENNAR_CK3, bdn.GAME])
        for key in set(re.findall(r'"(dynn_\w+)"', lists)):
            self.assertTrue(key in ours or key in loc, key)
        self.assertEqual(ours & set(loc), set())  # new keys never shadow a loaded one

    def test_no_placeholder_left(self):
        lists = self.files[bdn.LISTS_FILE].decode("utf-8-sig")
        for placeholder in bdn.PLACEHOLDERS:
            self.assertNotIn(placeholder, lists)
        self.assertEqual(set(parse_blocks(lists)), set(bdn.NAME_LISTS))


if __name__ == "__main__":
    unittest.main()
