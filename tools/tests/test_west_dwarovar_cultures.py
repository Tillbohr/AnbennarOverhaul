"""Tests for the West Dwarovar dwarf cultures and their language (docs/systems/west-dwarovar.md).

    python -I -m unittest discover -s tools/tests -p "test_west_dwarovar_cultures*.py"
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pdx_script import ANBENNAR_CK3 as ANBENNAR, parse_blocks  # noqa: E402
from test_elven_cultures import fields  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent.parent

LANGUAGE_FILE = "common/culture/pillars/aov_west_dwarovar_language.txt"
CULTURE_FILE = "common/culture/cultures/aov_west_dwarovar_cultures.txt"
LOC_FILE = "localization/english/aov_west_dwarovar_cultures_l_english.yml"
DWARF_FILE = "common/culture/cultures/anb_dwarf.txt"  # the overhaul's generated override (gfx keys)
SERPENTREACH_FILE = "common/culture/cultures/aov_serpentreach_cultures.txt"
BASE_LANGUAGE_FILE = "common/culture/pillars/anb_language.txt"
LANGUAGE = "language_west_dwarovar_dwarven"

CULTURES = {  # key -> (color, ethos, traditions in file order)
    "kronium_dwarvish": ("60 40 80", "ethos_bureaucratic",
                         ("tradition_mountain_homes", "tradition_legalistic", "tradition_agrarian")),
    "platinum_dwarvish": ("74 80 97", "ethos_courtly",
                          ("tradition_mountain_homes", "tradition_ruling_caste", "tradition_castle_keepers")),
    "mithril_dwarvish": ("81 231 213", "ethos_stoic",
                         ("tradition_mountain_homes", "tradition_loyal_soldiers", "tradition_storytellers")),
    "dagrite_dwarvish": ("147 191 155", "ethos_egalitarian",
                         ("tradition_mountain_homes", "tradition_caravaneers", "tradition_swords_for_hire")),
    "opal_dwarvish": ("255 228 216", "ethos_spiritual",
                      ("tradition_mountain_homes", "tradition_battlefield_looters", "tradition_life_is_just_a_joke")),
    "lead_dwarvish": ("160 114 158", "ethos_communal",
                      ("tradition_mountain_homes", "tradition_city_keepers", "tradition_sorcerous_metallurgy")),
    "ramsteel_dwarvish": ("74 111 121", "ethos_bellicose",
                          ("tradition_mountain_homes", "tradition_horse_breeder", "tradition_culinary_art")),
    "sapphire_dwarvish": ("0 25 119", "ethos_bureaucratic",
                          ("tradition_mountain_homes", "tradition_philosopher_culture", "tradition_astute_diplomats")),
}
DLC_ARTISANS = ("platinum_dwarvish",)  # dlc_tradition artisans / royal_court, as stone_dwarvish
COPIED = ("heritage", "martial_custom", "head_determination", "name_list", "coa_gfx", "building_gfx",
          "clothing_gfx", "unit_gfx", "ethnicities")  # equal to stone_dwarvish in the overhaul's anb_dwarf.txt


def _text(path):
    return path.read_bytes().decode("utf-8-sig")


class FileTests(unittest.TestCase):
    def test_files_have_bom_and_lf(self):
        for rel in (LANGUAGE_FILE, CULTURE_FILE, LOC_FILE):
            data = (SUBMOD / rel).read_bytes()
            self.assertTrue(data.startswith(b"\xef\xbb\xbf"), rel)
            self.assertNotIn(b"\r", data, rel)


class LanguageTests(unittest.TestCase):
    def test_language_pillar(self):
        ours = parse_blocks(_text(SUBMOD / LANGUAGE_FILE))
        self.assertEqual(sorted(ours), [LANGUAGE])
        got = fields(ours[LANGUAGE])
        self.assertEqual(got["type"], "language")
        self.assertEqual(got["color"], "96 72 128")
        self.assertIn(f"language_is_shown_trigger = {{ LANGUAGE = {LANGUAGE} }}", got["is_shown"])
        base = fields(parse_blocks(_text(ANBENNAR / BASE_LANGUAGE_FILE))["language_segbandalic_dwarven"])
        self.assertEqual(got["ai_will_do"],
                         base["ai_will_do"].replace("language_segbandalic_dwarven", LANGUAGE))


class CultureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cultures = parse_blocks(_text(SUBMOD / CULTURE_FILE))
        cls.dwarves = parse_blocks(_text(SUBMOD / DWARF_FILE))
        cls.serpentreach = parse_blocks(_text(SUBMOD / SERPENTREACH_FILE))

    def test_cultures_have_spec_fields(self):
        self.assertEqual(sorted(self.cultures), sorted(CULTURES))
        for key, (color, ethos, traditions) in CULTURES.items():
            got = fields(self.cultures[key])
            self.assertEqual(got["color"], color, key)
            self.assertEqual(got["ethos"], ethos, key)
            self.assertEqual(tuple(got["traditions"].split()), traditions, key)
            self.assertEqual(got["language"], LANGUAGE, key)
            self.assertNotIn("parents", got, key)
            self.assertNotIn("created", got, key)
            if key in DLC_ARTISANS:
                self.assertEqual(got.get("dlc_tradition"), "trait = tradition_artisans requires_dlc_flag = royal_court",
                                 key)
            else:
                self.assertNotIn("dlc_tradition", got, key)

    def test_copies_stone_dwarvish_fields(self):
        """The overhaul's RiE buildings, clothes and armies reach Anbennar's cultures through generated gfx keys
        (build_holding_models.py, build_portraits.py), which never see this file: copy stone_dwarvish's."""
        want = fields(self.dwarves["stone_dwarvish"])
        for key in CULTURES:
            got = fields(self.cultures[key])
            for name in COPIED:
                self.assertEqual(got.get(name), want.get(name), f"{key}.{name}")

    def test_colors_distinct(self):
        ours = [fields(body)["color"] for body in self.cultures.values()]
        theirs = {fields(body).get("color") for body in self.dwarves.values()}
        theirs |= {fields(body).get("color") for body in self.serpentreach.values()}
        self.assertEqual(len(ours), len(set(ours)))
        self.assertFalse(set(ours) & theirs)


class LocalizationTests(unittest.TestCase):
    def test_localization_complete(self):
        text = _text(SUBMOD / LOC_FILE)
        self.assertTrue(text.startswith("l_english:\n"))
        for key in CULTURES:
            name = key.removesuffix("_dwarvish").capitalize()
            self.assertIn(f'\n {key}:0 "{name} Dwarven"\n', text)
            self.assertIn(f'\n {key}_prefix:0 "{name} Dwarf"\n', text)
            self.assertIn(f'\n {key}_collective_noun:0 "{name} Dwarves"\n', text)
        self.assertIn(f'\n {LANGUAGE}_name:0 "West Dwarovar Dwarven"\n', text)


if __name__ == "__main__":
    unittest.main()
