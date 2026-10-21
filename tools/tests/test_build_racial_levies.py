"""Tests for tools/build_racial_levies.py (the per-holding racial levy correction).

    python -I -m unittest discover -s tools/tests -p "test_build_racial_levies*.py"
"""

import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_racial_levies as brl  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data.racial_levies import RACES, S_MAX, S_MIN, STEP  # noqa: E402

REAL = brl.Roots.default()
HAVE_REAL = REAL.anbennar.is_dir() and REAL.game.is_dir()
BASE = {"elven": -0.75, "dwarven": -0.40, "gnomish": -0.50, "kobold": 0.50}

BUILDING = """
farm_01 = {
	province_modifier = { levy_size = 0.05 }
	county_culture_modifier = { parameter = farm_param levy_size = 0.1 }
	province_terrain_modifier = { terrain = hills is_coastal = yes levy_size = 0.15 }
	duchy_capital_county_modifier = { levy_size = 0.2 }
	character_modifier = { levy_size = 0.25 }
	county_modifier = { tax_mult = 0.1 }
}
"""


def tree(base, files):
    """Write {relative path: text} under base and return base."""
    for rel, text in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return base


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game, self.anb, self.sub = root / "game", root / "anbennar", root / "submod"
        for path in (self.game, self.anb, self.sub):
            path.mkdir()
        self.roots = brl.Roots(rie=root, anbennar=self.anb, game=self.game)
        self.vanilla = self.game / "game"  # Roots.game is the install folder; its scripts are under game/

    def tearDown(self):
        self.tmp.cleanup()

    def sources(self):
        return brl.collect_sources(self.roots, submod=self.sub)


class CollectTests(Fixture):
    def test_collects_each_block_kind(self):
        tree(self.vanilla, {"common/buildings/00_test.txt": BUILDING})
        found = {(s.key, s.block, s.value) for s in self.sources()}
        self.assertEqual(found, {("farm_01", "province_modifier", 0.05), ("farm_01", "county_culture_modifier", 0.1),
                                 ("farm_01", "province_terrain_modifier", 0.15),
                                 ("farm_01", "duchy_capital_county_modifier", 0.2),
                                 ("farm_01", "character_modifier", 0.25)})
        terrain = next(s for s in self.sources() if s.block == "province_terrain_modifier")
        self.assertEqual(terrain.condition, {"terrain": "hills", "is_coastal": "yes"})

    def test_unclassified_folder_raises(self):
        tree(self.vanilla, {"common/foo/x.txt": "thing = { modifier = { levy_size = 0.1 } }"})
        with self.assertRaises(GeneratorError):
            self.sources()

    def test_ignored_folders_and_own_heritages_skipped(self):
        tree(self.vanilla, {"common/modifiers/x.txt": "event_mod = { levy_size = 0.2 }",
                         "common/culture/pillars/p.txt": "heritage_elven = { character_modifier = { levy_size = -0.75 } }"})
        self.assertEqual(self.sources(), [])

    def test_later_root_replaces_same_path(self):
        tree(self.vanilla, {"common/buildings/00_test.txt": BUILDING})
        tree(self.anb, {"common/buildings/00_test.txt": "farm_01 = { province_modifier = { levy_size = 0.3 } }"})
        self.assertEqual([(s.block, s.value) for s in self.sources()], [("province_modifier", 0.3)])

    def test_named_values_resolve(self):
        tree(self.vanilla, {"common/script_values/v.txt": "farm_levy_value = 0.02\n",
                         "common/buildings/00_test.txt": "@local = 0.07\nfarm_01 = { province_modifier = { levy_size = "
                                                         "farm_levy_value } county_modifier = { levy_size = @local } }"})
        self.assertEqual(sorted(s.value for s in self.sources()), [0.02, 0.07])

    def test_unresolvable_value_raises(self):
        tree(self.vanilla, {"common/buildings/00_test.txt": "farm_01 = { province_modifier = { levy_size = nope } }"})
        with self.assertRaises(GeneratorError):
            self.sources()

    def test_terrain_levy_keys_collected_with_their_terrain(self):
        tree(self.vanilla, {"common/terrain_types/t.txt": "forest = { movement_speed = 1 }\n",
                         "common/culture/traditions/t.txt": "tradition_woods = { county_modifier = { forest_levy_size = 0.1 "
                                                            "bp2_yearly_6203_levy_size = 0.5 } }"})
        self.assertEqual([(s.key, s.value, s.condition) for s in self.sources()],
                         [("tradition_woods", 0.1, {"levy_terrain": "forest"})])

    def test_anbennar_replace_path_drops_vanilla_folder(self):
        tree(self.vanilla, {"common/religion/holy_site_types/00_sites.txt":
                            "damascus = { character_modifier = { levy_size = 0.05 } }"})
        tree(self.anb, {"descriptor.mod": 'name="Anbennar"\nreplace_path="common/religion/holy_site_types"\n'})
        self.assertEqual(self.sources(), [])

    def test_same_key_in_two_files_counts_once_last_loaded_wins(self):
        tree(self.vanilla, {"common/buildings/00_city.txt": "city_01 = { province_modifier = { levy_size = 0.1 } }"})
        tree(self.sub, {"common/buildings/zz_aov_city.txt": "city_01 = { province_modifier = { levy_size = 0.2 } }"})
        self.assertEqual([(s.key, s.value) for s in self.sources()], [("city_01", 0.2)])

    def test_building_is_enabled_copied_with_holder_as_owner(self):
        tree(self.vanilla, {"common/buildings/00_test.txt":
                            "farm_01 = {\n\tis_enabled = {\n\t\tscope:holder = { is_dwarvish_culture = yes } # gate\n"
                            "\t\tscope:county = { development_level >= 5 }\n\t}\n"
                            "\tprovince_modifier = { levy_size = 0.05 }\n}\n"})
        src, = self.sources()
        self.assertEqual(src.condition["enabled"],
                         "province_owner = { is_dwarvish_culture = yes } county = { development_level >= 5 }")
        self.assertEqual(" ".join(brl.source_script(src).split()),
                         "if = { limit = { has_building = farm_01 province_owner = { is_dwarvish_culture = yes } "
                         "county = { development_level >= 5 } } add = 0.05 }")

    def test_nested_object_keys(self):
        tree(self.vanilla, {"common/laws/l.txt": "decree = { decree_a = { modifier = { levy_size = -0.1 } } }",
                         "common/religion/doctrine_types/d.txt": "tenet_x = { character_modifier = { levy_size = 0.1 } }"})
        self.assertEqual({(s.database, s.key) for s in self.sources()},
                         {("laws", "decree_a"), ("religion/doctrine_types", "tenet_x")})


class ScriptValueTests(unittest.TestCase):
    def cond(self, database, key, block, condition=None):
        return " ".join(brl.source_script(brl.Source(database, key, block, 0.1, condition or {})).split())

    def test_script_value_conditions(self):
        cases = {
            ("buildings", "b", "province_modifier"): "if = { limit = { has_building = b } add = 0.1 }",
            ("buildings", "b", "county_modifier"):
                "county = { every_county_province = { limit = { has_building = b } add = 0.1 } }",
            ("buildings", "b", "duchy_capital_county_modifier"):
                # title_province only works on counties and baronies: a duchy is reached through its capital county
                "if = { limit = { exists = county.duchy "
                "county.duchy.title_capital_county.title_province = { has_building = b } } add = 0.1 }",
            ("buildings", "b", "character_modifier"):
                "if = { limit = { province_owner = { any_directly_owned_province = { has_building = b } } } add = 0.1 }",
            ("culture/traditions", "t", "character_modifier"):
                "if = { limit = { province_owner.culture = { has_cultural_tradition = t } } add = 0.1 }",
            ("culture/traditions", "t", "county_modifier"):
                "if = { limit = { county.culture = { has_cultural_tradition = t } } add = 0.1 }",
            ("religion/doctrine_types", "d", "character_modifier"):
                "if = { limit = { province_owner.faith = { has_doctrine = d } } add = 0.1 }",
            ("governments", "g", "character_modifier"):
                "if = { limit = { province_owner = { has_government = g } } add = 0.1 }",
            ("laws", "l", "modifier"): "if = { limit = { province_owner = { has_realm_law = l } } add = 0.1 }",
            ("culture/innovations", "i", "character_modifier"):
                "if = { limit = { province_owner.culture = { has_innovation = i } } add = 0.1 }",
            ("culture/innovations", "i", "county_modifier"):
                "if = { limit = { county.culture = { has_innovation = i } } add = 0.1 }",
            ("traits", "tr", ""): "if = { limit = { province_owner = { has_trait = tr } } add = 0.1 }",
        }
        for args, want in cases.items():
            self.assertEqual(self.cond(*args), want, args)

    def test_terrain_levy_key_wraps_in_terrain_check(self):
        self.assertEqual(self.cond("culture/traditions", "t", "county_modifier", {"levy_terrain": "forest"}),
                         "if = { limit = { terrain = forest } "
                         "if = { limit = { county.culture = { has_cultural_tradition = t } } add = 0.1 } }")

    def test_culture_parameter_and_terrain_conditions(self):
        self.assertEqual(self.cond("buildings", "b", "province_culture_modifier", {"parameter": "p"}),
                         "if = { limit = { has_building = b county.culture = { has_cultural_parameter = p } } add = 0.1 }")
        self.assertEqual(self.cond("buildings", "b", "province_terrain_modifier", {"terrain": "hills", "is_coastal": "no"}),
                         "if = { limit = { has_building = b terrain = hills is_coastal = no } add = 0.1 }")


class TierTests(unittest.TestCase):
    def test_tier_math(self):
        for race, f in RACES.items():
            for s in (-0.5, 0.0, 0.3, 0.6, 2.0):
                final = 1 + BASE[race] + s - f * STEP * brl.tier(s)
                self.assertAlmostEqual(final, (1 + BASE[race]) * (1 + s), delta=abs(f) * STEP, msg=(race, s))
                self.assertGreaterEqual(final, 0, (race, s))

    def test_negative_bonus_gets_positive_correction(self):
        text = brl.modifiers_file()
        key = brl.tier_key("elven", brl.tier(-0.5))
        self.assertEqual(key, "aov_racial_levy_elven_m10")
        self.assertRegex(text, rf"{key} = {{\n\tlevy_size = 0.375\n}}")

    def test_bonus_beyond_range_clamps_to_end_tier(self):
        self.assertEqual(brl.tier(5.0), brl.tier(S_MAX))
        self.assertEqual(brl.tier(-3.0), brl.tier(S_MIN))

    def test_every_nonzero_tier_has_a_modifier(self):
        keys = set(re.findall(r"^(\w+) = \{", brl.modifiers_file(), re.M))
        want = {brl.tier_key(r, n) for r in RACES for n in range(brl.tier(S_MIN), brl.tier(S_MAX) + 1) if n}
        self.assertEqual(keys, want)

    def test_refresh_removes_before_adding_and_skips_non_racial(self):
        text = brl.effects_file()
        remove, add = text.find("remove_province_modifier"), text.find("add_province_modifier")
        self.assertTrue(0 <= remove < add)
        racial = text.find("has_cultural_parameter = aov_racial_levy_elven")
        self.assertTrue(remove < racial < add)

    def test_every_tier_modifier_has_loc(self):
        loc = brl.loc_file().decode("utf-8-sig")
        for key in re.findall(r"^(\w+) = \{", brl.modifiers_file(), re.M):
            self.assertIn(f" {key}:0 ", loc)
            self.assertIn(f" {key}_desc:0 ", loc)


@unittest.skipUnless(HAVE_REAL, "needs Anbennar and the CK3 install")
class FreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = brl.build_all(REAL)

    def test_generated_files_match_the_mod(self):
        stale = [rel for rel, content in self.files.items()
                 if not (brl.SUBMOD / rel).is_file() or (brl.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_racial_levies.py")


if __name__ == "__main__":
    unittest.main()
