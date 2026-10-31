"""Tests for the base art fixes (docs/systems/base-art-fixes.md): Anbennar art copied to the file name the game looks
up, Anbennar men-at-arms given the unit icons Anbennar ships for them, and icons for placeholder traits (avatars,
racial purists, planetouched, vampire, lycanthrope, bladeshunned).

    python -I -m unittest discover -s tools/tests -p "test_base_art_fixes*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdx_script import ANBENNAR_CK3 as ANBENNAR, parse_blocks  # noqa: E402
from test_cultural_maa import (ICON_SWAPS, SUBMOD, _text, anbennar_icon, base_blocks, blocks, maa_files,  # noqa: E402
                               squash)

GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
ICON_FILE = "common/men_at_arms_types/zz_aov_maa_icon_overrides.txt"
BASE_MAA_FILE = "common/men_at_arms_types/anb_cultural_maa_types.txt"
# Units whose whole block lives in ICON_FILE; the other ICON_SWAPS units are in overrides of other systems.
ICON_FILE_UNITS = {"adventurers_maa", "damerian_longbowmen", "oakfoot_rangers", "thorn_squares", "wexonard_greatswords"}
# Overhaul file -> Anbennar file it is a byte copy of.
COPIES = {
    **{f"gfx/interface/icons/traits/education_adeanic_knight_{n}.dds":
       f"gfx/interface/icons/traits/adeanic_knight_{n + 1}.dds" for n in range(6)},
    "gfx/interface/icons/regimenttypes/griffon_riders.dds": "gfx/interface/icons/regimenttypes/griffon_knights.dds",
    **{f"gfx/interface/illustrations/men_at_arms_{size}/{unit}.dds":
       f"gfx/interface/illustrations/men_at_arms_{size}/mages.dds"
       for size in ("big", "small") for unit in ("battlemages", "druids", "skalds")},
}
GAME_COPIES = {
    **{f"gfx/interface/illustrations/men_at_arms_{size}/rangers.dds":
       f"gfx/interface/illustrations/men_at_arms_{size}/bowmen.dds" for size in ("big", "small")},
    "gfx/interface/icons/traits/bladeshunned.dds": "gfx/interface/icons/traits/disinherited.dds",
}
ART = ("gfx/interface/icons/regimenttypes", "gfx/interface/illustrations/men_at_arms_big",
       "gfx/interface/illustrations/men_at_arms_small")

WORKSHOP = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310")
TRAITS = "gfx/interface/icons/traits"
TRAIT_FILE = "common/traits/zz_aov_trait_icon_overrides.txt"
BASE_TRAIT_FILE = "common/traits/00_anb_traits.txt"
ELEMENTS = {"fire": "user_of_elemental_fire_magic", "water": "user_of_elemental_water_magic",
            "earth": "user_of_elemental_earth_magic", "wind": "user_of_elemental_air_magic",
            "life": "user_of_life_magic", "shadow": "user_of_shadow_magic"}
PLANETOUCHED = {f"planetouched_{element}_{n}": f"{stem}_{n}" for element, stem in ELEMENTS.items() for n in (1, 2, 3)}
PURISTS = ("elven_purist", "human_purist", "gnomish_purist", "dwarven_purist", "half_elf_purist", "halfling_purist")
# Overhaul trait icon -> Workshop file it is a byte copy of: Supernatural (2856525601), the Warcraft TC (2949767945) and
# Elder Kings 2 (2887120253).
WORKSHOP_COPIES = {
    f"{TRAITS}/vampire.dds": f"2887120253/{TRAITS}/vampire_character.dds",
    f"{TRAITS}/lycanthrope.dds": f"2887120253/{TRAITS}/lycan_character.dds",
    **{f"{TRAITS}/{key}.dds": f"2856525601/{TRAITS}/pure_blooded.dds" for key in PURISTS},
    **{f"{TRAITS}/{key}.dds": f"2949767945/{TRAITS}/{stem}.dds" for key, stem in PLANETOUCHED.items()},
}


def icon_of(body):
    return re.search(r"(?m)^\ticon = (\S+)", body).group(1)


class IconOverrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ours = blocks(ICON_FILE)
        cls.base = base_blocks(BASE_MAA_FILE)
        cls.effective = {}
        for f in maa_files():
            cls.effective.update(parse_blocks(_text(f)))

    def test_only_the_icon_file_units_are_overridden(self):
        self.assertEqual(set(self.ours), ICON_FILE_UNITS)

    def test_blocks_are_anbennars_but_for_the_icon(self):
        for key in ICON_FILE_UNITS:
            self.assertEqual(squash(anbennar_icon(self.ours[key], key)), squash(self.base[key]), key)

    def test_anbennar_still_uses_the_old_icon(self):
        for key, (old, _new) in ICON_SWAPS.items():
            self.assertEqual(icon_of(self.base[key]), old, key)

    def test_effective_units_use_the_new_icon_and_have_its_art(self):
        for key, (_old, new) in ICON_SWAPS.items():
            self.assertEqual(icon_of(self.effective[key]), new, key)
            for folder in ART:
                self.assertTrue(any((root / folder / f"{new}.dds").is_file() for root in (SUBMOD, ANBENNAR)),
                                f"{key}: {folder}/{new}.dds")


class CopiedArtTests(unittest.TestCase):
    def test_copies_match_their_source(self):
        for ours, source in COPIES.items():
            self.assertEqual((SUBMOD / ours).read_bytes(), (ANBENNAR / source).read_bytes(), ours)
        for ours, source in GAME_COPIES.items():
            self.assertEqual((SUBMOD / ours).read_bytes(), (GAME / source).read_bytes(), ours)

    def test_sun_reborn_line_shares_the_phoenix(self):
        self.assertEqual((SUBMOD / TRAITS / "sun_reborn_descendant.dds").read_bytes(),
                         (SUBMOD / TRAITS / "sun_reborn.dds").read_bytes())

    @unittest.skipUnless(WORKSHOP.is_dir(), "Workshop mods not installed")
    def test_workshop_copies_match_their_source(self):
        for ours, source in WORKSHOP_COPIES.items():
            self.assertEqual((SUBMOD / ours).read_bytes(), (WORKSHOP / source).read_bytes(), ours)


class TraitIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ours = blocks(TRAIT_FILE)
        cls.base = base_blocks(BASE_TRAIT_FILE)

    def test_only_planetouched_overridden(self):
        self.assertEqual(set(self.ours), set(PLANETOUCHED))

    def test_overrides_are_anbennars_but_for_the_icon(self):
        for key in PLANETOUCHED:
            self.assertEqual(self.base[key].count("varangian.dds"), 2, key)
            self.assertEqual(squash(self.ours[key]), squash(self.base[key].replace("varangian.dds", f"{key}.dds")), key)

    def test_override_file_loads_after_anbennars(self):
        self.assertGreater(Path(TRAIT_FILE).name, Path(BASE_TRAIT_FILE).name)

    def test_every_fixed_trait_has_its_icon(self):
        avatars = [key for key in self.base if key.startswith("anb_avatar_")]
        self.assertEqual(len(avatars), 15)
        for key in avatars + list(PURISTS) + list(PLANETOUCHED) + ["vampire", "lycanthrope", "bladeshunned", "sun_reborn", "sun_reborn_descendant"]:
            self.assertTrue((SUBMOD / TRAITS / f"{key}.dds").is_file(), key)


if __name__ == "__main__":
    unittest.main()
