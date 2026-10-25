"""Tests for tools/build_holdings_override.py.

    python -I -m unittest discover -s tools/tests -p test_build_holdings_override.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_holdings_override as hov  # noqa: E402
from data import rie_dwarves as rie  # noqa: E402
from pdx_script import parse_blocks  # noqa: E402

FIXTURE = """castle_holding = {
\tprimary_building = castle_01
\tbuildings = {
\t\tcastle_walls_01
\t\t# hall_of_heroes_01 # Anbennar
\t\tquarries_01
\t}
}

city_holding = {
\tprimary_building = city_01
\tbuildings = {
\t\tquarries_01
\t}
}
"""


class NewHoldingTests(unittest.TestCase):
    def test_hold_has_only_rie_dwarven_buildings(self):
        # RiE's dwarven_holding lists only dwarven buildings and mines: no castle (vanilla) building in a hold
        text = hov.add_buildings(FIXTURE, "castle_holding", ["artificer_academy_01"])
        out = hov.add_holding(text, "dwarven_hold_holding", hov.NEW_HOLDINGS["dwarven_hold_holding"])
        block = parse_blocks(out)["dwarven_hold_holding"]
        self.assertIn("primary_building = dwarven_hold_01", block)
        self.assertEqual(listed(block), rie.HOLD_BUILDINGS)
        for b in ("castle_walls_01", "quarries_01", "artificer_academy_01", "castle_01"):
            self.assertNotIn(b, block)
        self.assertIn(hov.MARKER, out)

    def test_copy_buildings_from_still_copies(self):
        spec = {"copy_buildings_from": "castle_holding", "primary_building": "x_01", "extra": ["a_01"]}
        block = parse_blocks(hov.add_holding(FIXTURE, "new_holding", spec))["new_holding"]
        self.assertEqual(listed(block), ["castle_walls_01", "quarries_01", "a_01"])
        self.assertNotIn("hall_of_heroes_01", block)  # commented in the source

    def test_source_holdings_unchanged(self):
        out = hov.add_holding(FIXTURE, "dwarven_hold_holding", hov.NEW_HOLDINGS["dwarven_hold_holding"])
        self.assertTrue(out.startswith(FIXTURE))


def listed(block: str) -> list:
    """The building keys of a holding block's buildings list, in order (comments dropped)."""
    keys = []
    for line in block.split("\n"):
        name = line.split("#")[0].strip()
        if name and "=" not in name and name != "}":
            keys.append(name)
    return keys


class GeneratedFileTests(unittest.TestCase):
    @unittest.skipUnless((hov.DEFAULT_ANBENNAR / hov.REL_PATH).is_file() and (hov.SUBMOD / hov.REL_PATH).is_file(),
                         "needs Anbennar and the generated file")
    def test_generated_holdings(self):
        out = parse_blocks((hov.SUBMOD / hov.REL_PATH).read_bytes().decode("utf-8-sig"))
        self.assertIn("artificer_academy_01", out["castle_holding"])
        hold = out["dwarven_hold_holding"]
        self.assertIn("primary_building = dwarven_hold_01", hold)
        self.assertEqual(listed(hold), rie.HOLD_BUILDINGS)
        base = parse_blocks((hov.DEFAULT_ANBENNAR / hov.REL_PATH).read_bytes().decode("utf-8-sig"))
        self.assertEqual(set(out) - set(base), {"dwarven_hold_holding", "elven_holding"})

    @unittest.skipUnless((hov.SUBMOD / hov.REL_PATH).is_file(), "needs the generated file")
    def test_haven_lists_the_elf_buildings(self):
        import build_rie_elves
        haven = parse_blocks((hov.SUBMOD / hov.REL_PATH).read_bytes().decode("utf-8-sig"))["elven_holding"]
        self.assertIn("primary_building = elven_settlement_01", haven)
        self.assertEqual(listed(haven), build_rie_elves.haven_buildings())
        self.assertNotIn("cereal_fields_01", listed(haven))

    @unittest.skipUnless((hov.SUBMOD / hov.REL_PATH).is_file(), "needs the generated file")
    def test_hold_gets_rie_buildings_once(self):
        keys = listed(parse_blocks((hov.SUBMOD / hov.REL_PATH).read_bytes().decode("utf-8-sig"))["dwarven_hold_holding"])
        for b in rie.HOLD_BUILDINGS:
            self.assertEqual(keys.count(b), 1, b)
        for b in ("deep_mine_01", "runeforge_01", "hall_of_the_ancestors_01"):
            self.assertNotIn(b, keys)
        self.assertEqual(len(keys), len(set(keys)))

    @unittest.skipUnless((hov.SUBMOD / hov.REL_PATH).is_file(), "needs the generated file")
    def test_castle_and_city_get_surface_and_mines(self):
        out = parse_blocks((hov.SUBMOD / hov.REL_PATH).read_bytes().decode("utf-8-sig"))
        for holding in ("castle_holding", "city_holding"):
            keys = listed(out[holding])
            for b in rie.SURFACE_BUILDINGS + rie.MINE_BUILDINGS:
                self.assertEqual(keys.count(b), 1, f"{holding} {b}")

    def test_additions_and_extra_come_from_the_data(self):
        for holding in ("castle_holding", "city_holding"):
            self.assertEqual(hov.ADDITIONS[holding], ["artificer_academy_01", "battlemage_academy_01"] + rie.SURFACE_BUILDINGS + rie.MINE_BUILDINGS)
        self.assertEqual(hov.NEW_HOLDINGS["dwarven_hold_holding"]["extra"], rie.HOLD_BUILDINGS)

    def test_add_holding_drops_duplicates_keeping_the_first(self):
        spec = {"copy_buildings_from": "castle_holding", "primary_building": "x_01", "extra": ["a_01", "quarries_01", "a_01"]}
        keys = listed(parse_blocks(hov.add_holding(FIXTURE, "new_holding", spec))["new_holding"])
        self.assertEqual(keys, ["castle_walls_01", "quarries_01", "a_01"])


if __name__ == "__main__":
    unittest.main()
