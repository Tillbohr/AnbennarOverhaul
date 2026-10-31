"""Tests for the base art fixes (docs/systems/base-art-fixes.md): Anbennar art copied to the file name the game looks
up, and Anbennar men-at-arms given the unit icons Anbennar ships for them.

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
GAME_COPIES = {f"gfx/interface/illustrations/men_at_arms_{size}/rangers.dds":
               f"gfx/interface/illustrations/men_at_arms_{size}/bowmen.dds" for size in ("big", "small")}
ART = ("gfx/interface/icons/regimenttypes", "gfx/interface/illustrations/men_at_arms_big",
       "gfx/interface/illustrations/men_at_arms_small")


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


if __name__ == "__main__":
    unittest.main()
