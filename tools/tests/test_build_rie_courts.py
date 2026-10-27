"""Tests for tools/build_rie_courts.py (RiE character backgrounds and royal courts).

    python -I -m unittest discover -s tools/tests -p test_build_rie_courts.py -v
"""

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_portraits as bp  # noqa: E402
import build_rie_dwarves  # noqa: E402
import build_rie_courts as rc  # noqa: E402
from data import rie_courts as data  # noqa: E402

REAL = rc.Roots.default()
HAVE_REAL = REAL.rie.is_dir() and REAL.anbennar.is_dir() and REAL.game.is_dir()
BEGIN = "\t# Anbennar Overhaul: Realms in Exile backgrounds"
END = "\t# Anbennar Overhaul: end of Realms in Exile backgrounds\n\n"


class TriggerTests(unittest.TestCase):
    def test_every_tier_has_a_view_trigger_with_rie_fallbacks(self):
        text = rc.triggers_file()[rc.TRIGGERS_FILE].decode("utf-8-sig")
        for group, court in data.COURTS.items():
            self.assertIn(f"{rc.holder(group)} = {{\n\texists = capital_province\n", text)
            for tier, _texture, _environment in court["backgrounds"]:
                view = rc.view_trigger(group, tier)
                block = re.search(rf"^{view} = \{{.*?^\}}", text, re.S | re.M).group(0)
                inner = rc.tier_trigger(group, tier)
                for part in (f"\t\t{inner} = yes", f"primary_spouse = {{ is_ruler = no {inner} = yes }}",
                             f"betrothed ?= {{ {inner} = yes }}", f"host ?= {{ {inner} = yes }}"):
                    self.assertIn(part, block)
                self.assertIn(f"{inner} = {{\n\t{rc.holder(group)} = yes\n\t{data.TIERS[tier]}\n}}", text)
        self.assertIn(f"{rc.ALL_SCENES_TRIGGER} = {{\n\tOR = {{\n", text)

    def test_dwarves_need_dwarven_terrain(self):
        text = rc.triggers_file()[rc.TRIGGERS_FILE].decode("utf-8-sig")
        for terrain in data.DWARF_TERRAINS:
            self.assertIn(f"terrain = {terrain}", text)

    def test_bad_tier_raises(self):
        courts = {"x": dict(data.COURTS["dwarf"], backgrounds=[("nope", "a.dds", "e")])}
        with mock.patch.object(data, "COURTS", courts), self.assertRaises(rc.GeneratorError):
            rc.check_data()

    def test_dwarf_backgrounds_cover_every_realm_level(self):
        tiers = [tier for tier, _t, _e in data.COURTS["dwarf"]["backgrounds"]]
        self.assertEqual(tiers, ["above_kingdom", "kingdom", "duchy", "below_duchy"])

    def test_lich_triggers(self):
        text = rc.triggers_file()[rc.TRIGGERS_FILE].decode("utf-8-sig")
        landed = re.search(r"^aov_lich_court_landed_trigger = \{.*?^\}", text, re.S | re.M).group(0)
        self.assertIn("has_trait = lich", landed)
        self.assertIn("is_landed = yes", landed)
        # The landed hall is shown like a court: also to a non-ruling spouse, the betrothed and the host
        view = re.search(r"^aov_lich_court_view_landed_trigger = \{.*?^\}", text, re.S | re.M).group(0)
        for part in ("\t\taov_lich_court_landed_trigger = yes",
                     "primary_spouse = { is_ruler = no aov_lich_court_landed_trigger = yes }",
                     "betrothed ?= { aov_lich_court_landed_trigger = yes }",
                     "host ?= { aov_lich_court_landed_trigger = yes }"):
            self.assertIn(part, view)
        # The crypt is the unlanded Lich's own
        crypt = re.search(r"^aov_lich_court_view_unlanded_trigger = \{.*?^\}", text, re.S | re.M).group(0)
        self.assertIn("aov_lich_court_unlanded_trigger = yes", crypt)
        self.assertNotIn("host", crypt)
        unlanded = re.search(r"^aov_lich_court_unlanded_trigger = \{.*?^\}", text, re.S | re.M).group(0)
        self.assertIn("is_landed = no", unlanded)

    def test_lich_backgrounds_first(self):
        files = {}
        with mock.patch.object(rc, "_illustration_file", lambda roots, ref, files: ref):
            entries = rc.background_entries(None, files)
        crypt = entries.index('reference = "event_scenes/lotr_throneroom_evil.dds"')
        hall = entries.index('reference = "aov_lich/lichdom_court.dds"')
        self.assertLess(crypt, hall)
        self.assertLess(hall, entries.index("# RiE dwarven court"))
        self.assertIn("aov_lich_court_view_unlanded_trigger = yes", entries[crypt:hall])
        self.assertIn('reference = "environment_evil_throneroom"', entries[crypt:hall])
        self.assertIn('reference = "environment_cw_india_main"', entries[hall:])

    def test_lich_hall_is_imported(self):
        self.assertTrue((rc.SUBMOD / rc.ILLUSTRATION_DIR / "aov_lich/lichdom_court.dds").is_file())


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class RealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = rc.build_all(REAL)

    def test_backgrounds_sit_before_anbennars_first_throneroom(self):
        ours = self.files[rc.ILLUSTRATIONS_FILE].decode("utf-8")
        base = (REAL.anbennar / rc.ILLUSTRATIONS_FILE).read_bytes().decode("utf-8")
        start = ours.index(BEGIN)
        end = ours.index(END) + len(END)
        self.assertEqual(ours[:start] + ours[end:], base)
        self.assertIn(f'reference = "{data.BACKGROUND_ANCHOR}"', ours[end:end + 400])
        for court in data.COURTS.values():
            for _tier, texture, environment in court["backgrounds"]:
                self.assertIn(f'reference = "{texture}"', ours[start:end])
                self.assertIn(f'reference = "{environment}"', ours[start:end])

    def test_pictures_and_environments_exist(self):
        environments = self.files[rc.ENVIRONMENTS_FILE].decode("utf-8-sig")
        backgrounds = [b for court in data.COURTS.values() for b in court["backgrounds"]]
        backgrounds += [(name, texture, environment) for name, _c, _v, texture, environment in data.LICH_BACKGROUNDS]
        for _tier, texture, environment in backgrounds:
            rel = f"{rc.ILLUSTRATION_DIR}/{texture}"
            # Godherja's lichdom hall is imported once, not generated
            self.assertTrue(rel in self.files or bp._exists_outside(REAL, rel) is not None
                            or (rc.SUBMOD / rel).is_file(), rel)
            defined = environment in environments or any(
                re.search(rf"^{environment}\s*=", text, re.M)
                for _p, text in bp.effective_texts(REAL, rc.ENVIRONMENTS_DIR))
            self.assertTrue(defined, environment)

    def test_scene_cultures_ours_first_and_excluded_elsewhere(self):
        text = self.files[rc.CULTURES_FILE].decode("utf-8-sig")
        sets = [names[0] for names, _s, _e in bp.blocks(text, 1, strict=False)]
        ours = [court["scene_culture"] for court in data.COURTS.values()]
        self.assertEqual(sets[:len(ours)], ours)
        others = len(sets) - len(ours)
        self.assertEqual(text.count(rc.EXCLUDE_LINE), others)
        base = (REAL.anbennar / rc.CULTURES_FILE).read_bytes().decode("utf-8").lstrip(bp.BOM)
        stripped = text.replace(rc.EXCLUDE_LINE, "")
        self.assertTrue(stripped.endswith(base[base.index(sets[len(ours)]):]))

    def test_grandeur_levels_add_our_cultures_only(self):
        text = self.files[rc.GRANDEUR_FILE].decode("utf-8-sig")
        base = (REAL.game / "game" / rc.GRANDEUR_FILE).read_bytes().decode("utf-8-sig")
        inserted = re.search(r"\t# Anbennar Overhaul: Realms in Exile courts.*?end of Realms in Exile courts\n", text,
                             re.S).group(0)
        self.assertEqual(text.replace(inserted, ""), base)
        for court in data.COURTS.values():
            self.assertRegex(inserted, rf'culture\s*=\s*"{court["scene_culture"]}"')

    def test_scenes_are_rie_verbatim_and_their_models_copied(self):
        external = bp.external_models(REAL)
        for court in data.COURTS.values():
            for name in court["scenes"]:
                rel = f"{rc.SCENES_DIR}/{name}"
                self.assertEqual(self.files[rel], (REAL.rie / rel).read_bytes())
                copied = set()
                for content in (c for r, c in self.files.items() if r.endswith(".asset")):
                    copied |= set(re.findall(r'name\s*=\s*"([^"]+)"', content.decode("utf-8-sig")))
                for asset in re.findall(r'asset="([^"]+)"', self.files[rel].decode("utf-8-sig")):
                    self.assertTrue(asset in copied or ("entity", asset) in external, asset)


@unittest.skipUnless(HAVE_REAL, "RiE, Anbennar and game needed")
class FreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = rc.build_all(REAL)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (rc.SUBMOD / rel).is_file() or (rc.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_rie_courts.py")

    def test_no_orphan_files(self):
        produced = set(self.files) | set(build_rie_dwarves.build_all(REAL))
        orphans = []
        for folder in ("gfx/models/court", "gfx/models/artifacts", "gfx/court_scene/scene_settings",
                       "gfx/interface/illustrations/character_view", "gfx/interface/illustrations/event_scenes"):
            root = rc.SUBMOD / folder
            if root.is_dir():
                orphans += [p.relative_to(rc.SUBMOD).as_posix() for p in root.rglob("*")
                            if p.is_file() and p.relative_to(rc.SUBMOD).as_posix() not in produced]
        self.assertEqual(sorted(orphans), [], "leftover files: delete them")


if __name__ == "__main__":
    unittest.main()
