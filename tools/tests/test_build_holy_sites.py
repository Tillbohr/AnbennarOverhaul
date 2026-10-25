"""Tests for tools/build_holy_sites.py.

    python -I -m unittest discover -s tools/tests -p "test_build_holy_sites*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_holy_sites as bhs  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from pdx_script import parse_blocks  # noqa: E402

RELIGION_FIXTURE = """test_religion = {
\tfamily = rf_test
\tfaiths = {
\t\tfirst_faith = {
\t\t\tcolor = { 1 2 3 }
\t\t\ticon = first_faith
\t\t}
\t\tsecond_faith = { # comment
\t\t\ticon = second_faith
\t\t}
\t}
}
"""

HAVE_REAL = (bhs.ANBENNAR_CK3 / bhs.RELIGION_DIR).is_dir()


class AddHolySitesTests(unittest.TestCase):
    def test_lines_added_inside_the_faith(self):
        out = bhs.add_holy_sites(RELIGION_FIXTURE, {"second_faith": ["site_a", "site_b"]})
        faiths = parse_blocks(parse_blocks(out)["test_religion"].split("faiths = {", 1)[1])
        self.assertEqual(re.findall(r"holy_site = (\w+)", faiths["second_faith"]), ["site_a", "site_b"])
        self.assertNotIn("holy_site", faiths["first_faith"])

    def test_added_lines_marked_and_indented(self):
        out = bhs.add_holy_sites(RELIGION_FIXTURE, {"first_faith": ["site_a"]})
        added = [l for l in out.split("\n") if "holy_site" in l]
        self.assertEqual(added, [f"\t\t\tholy_site = site_a {bhs.MARKER}"])

    def test_missing_faith_is_an_error(self):
        with self.assertRaises(GeneratorError):
            bhs.add_holy_sites(RELIGION_FIXTURE, {"third_faith": ["site_a"]})


@unittest.skipUnless(HAVE_REAL, "needs Anbennar")
class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.faiths = bhs.faith_files(bhs.ANBENNAR_CK3)

    def test_every_listed_faith_has_no_anbennar_holy_site(self):
        bhs.check_sites(bhs.ANBENNAR_CK3, self.faiths)  # raises on a missing title, faith or a faith with sites

    def test_each_faith_gets_several_sites_in_distinct_counties(self):
        for faith, keys in bhs.sites_by_faith().items():
            self.assertGreaterEqual(len(keys), 3, faith)
            counties = [s["county"] for s in bhs.HOLY_SITES if s["key"] in keys]
            self.assertEqual(len(counties), len(set(counties)), faith)

    def test_modifiers_are_numbers(self):
        for site in bhs.HOLY_SITES:
            self.assertTrue(site["modifier"], site["key"])
            for value in site["modifier"].values():
                float(value)


@unittest.skipUnless(HAVE_REAL, "needs Anbennar")
class FreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = bhs.build_all(bhs.ANBENNAR_CK3)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (bhs.SUBMOD / rel).is_file() or (bhs.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_holy_sites.py")

    def test_no_leftover_religion_overrides(self):
        ours = {f"{bhs.RELIGION_DIR}/{p.name}" for p in (bhs.SUBMOD / bhs.RELIGION_DIR).glob("*.txt")}
        self.assertEqual(ours - set(self.files), set())

    def test_religion_copies_differ_only_by_marked_lines(self):
        for rel, content in self.files.items():
            if not rel.startswith(bhs.RELIGION_DIR):
                continue
            src = (bhs.ANBENNAR_CK3 / rel).read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
            lines = content.decode("utf-8-sig").replace("\r\n", "\n").split("\n")
            self.assertTrue(all(l.startswith(bhs.MARKER) for l in lines[:2]), rel)
            rest = [l for l in lines[2:] if not l.endswith(" " + bhs.MARKER)]
            self.assertEqual("\n".join(rest), src, rel)

    def test_every_site_named(self):
        loc = self.files[bhs.LOC_FILE].decode("utf-8-sig")
        for key in parse_blocks(self.files[bhs.SITES_FILE].decode("utf-8-sig")):
            self.assertIn(f" holy_site_{key}_name:0 ", loc)
            self.assertIn(f" holy_site_{key}_effect_name:0 ", loc)


if __name__ == "__main__":
    unittest.main()
