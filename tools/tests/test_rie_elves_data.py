"""Tests for tools/data/rie_elves.py (the Elven Haven's rules, maps and Anbennar names).

    python -I -m unittest discover -s tools/tests -p test_rie_elves_data.py -v
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data import rie_elves as data  # noqa: E402


def expected_name_keys() -> set:
    keys = {f"elven_settlement_{n:02d}" for n in range(1, data.SETTLEMENT_LEVELS + 1)}
    for line, levels in data.LINES.items():
        keys |= {f"{line}_{n:02d}" for n in range(1, levels + 1)}
        keys.add(f"building_type_{line}_01")
    keys.add("building_type_elven_settlement_01")
    return keys


class NameTests(unittest.TestCase):
    def test_names_cover_every_level(self):
        self.assertEqual(set(data.NAMES), expected_name_keys())
        for key, (name, desc) in data.NAMES.items():
            self.assertTrue(name.strip() and desc.strip(), key)

    def test_names_have_no_middle_earth_lore(self):
        for key, (name, desc) in data.NAMES.items():
            self.assertIsNone(re.search(data.FORBIDDEN_LORE, name + " " + desc), key)
        for key, text in data.HOLDING_LOC.items():
            self.assertIsNone(re.search(data.FORBIDDEN_LORE, text), key)

    def test_names_need_no_escaping(self):
        for key, (name, desc) in data.NAMES.items():
            self.assertNotIn('"', name + desc, key)

    def test_line_levels_are_rie_counts(self):
        self.assertEqual(len(data.LINES), 24)
        self.assertEqual(sum(data.LINES.values()), 126)


class MapTests(unittest.TestCase):
    def test_maps_target_included_lines(self):
        self.assertTrue(set(data.BUILDING_MAP.values()) <= set(data.LINES))
        self.assertEqual(data.LEVEL_MAP, {"castle_01": 1, "castle_02": 3, "castle_03": 5, "castle_04": 7,
                                          "tribe_01": 1, "tribe_02": 2})

    def test_asset_band_covers_every_level(self):
        self.assertEqual(sorted(data.HAVEN_ASSET_BAND), list(range(1, data.SETTLEMENT_LEVELS + 1)))
        self.assertEqual(data.HAVEN_ASSET_BAND[7], "castle_04")

    def test_castle_levels_are_haven_levels(self):
        self.assertEqual(data.CASTLE_EQUIVALENT, {1: 1, 2: 3, 3: 5, 4: 7})


if __name__ == "__main__":
    unittest.main()
