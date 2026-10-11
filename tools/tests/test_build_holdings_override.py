"""Tests for tools/build_holdings_override.py.

    python -I -m unittest discover -s tools/tests -p test_build_holdings_override.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_holdings_override as hov  # noqa: E402
from eu4_monuments import parse_blocks  # noqa: E402

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
    def test_new_holding_copies_castle_buildings(self):
        out = hov.add_holding(FIXTURE, "dwarven_hold_holding", hov.NEW_HOLDINGS["dwarven_hold_holding"])
        block = parse_blocks(out)["dwarven_hold_holding"]
        self.assertIn("primary_building = dwarven_hold_01", block)
        for b in ("castle_walls_01", "quarries_01", "deep_mine_01", "runeforge_01", "hall_of_the_ancestors_01"):
            self.assertIn(b, block)
        self.assertNotIn("hall_of_heroes_01", block)  # commented in the source
        self.assertNotIn("castle_01", block)
        self.assertIn(hov.MARKER, out)

    def test_new_holding_includes_additions(self):
        text = hov.add_buildings(FIXTURE, "castle_holding", ["artificer_academy_01"])
        out = hov.add_holding(text, "dwarven_hold_holding", hov.NEW_HOLDINGS["dwarven_hold_holding"])
        self.assertIn("artificer_academy_01", parse_blocks(out)["dwarven_hold_holding"])

    def test_source_holdings_unchanged(self):
        out = hov.add_holding(FIXTURE, "dwarven_hold_holding", hov.NEW_HOLDINGS["dwarven_hold_holding"])
        self.assertTrue(out.startswith(FIXTURE))


class GeneratedFileTests(unittest.TestCase):
    @unittest.skipUnless((hov.DEFAULT_ANBENNAR / hov.REL_PATH).is_file() and (hov.SUBMOD / hov.REL_PATH).is_file(),
                         "needs Anbennar and the generated file")
    def test_generated_holdings(self):
        out = parse_blocks((hov.SUBMOD / hov.REL_PATH).read_bytes().decode("utf-8-sig"))
        self.assertIn("artificer_academy_01", out["castle_holding"])
        hold = out["dwarven_hold_holding"]
        self.assertIn("artificer_academy_01", hold)
        for b in ("dwarven_hold_01", "deep_mine_01", "runeforge_01", "hall_of_the_ancestors_01", "quarries_01"):
            self.assertIn(b, hold)
        base = parse_blocks((hov.DEFAULT_ANBENNAR / hov.REL_PATH).read_bytes().decode("utf-8-sig"))
        self.assertEqual(set(out) - set(base), {"dwarven_hold_holding"})


if __name__ == "__main__":
    unittest.main()
