import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import eu4_monuments as eu4  # noqa: E402
import import_eu4_monuments as imp  # noqa: E402
from data import holds  # noqa: E402

ANBENNAR_CK3 = imp.DEFAULT_ANBENNAR_CK3
LIVE = ANBENNAR_CK3.is_dir()
EU4_HISTORY = eu4.EU4_ROOTS["anbennar"] / "history" / "provinces"
LIVE_EU4 = EU4_HISTORY.is_dir()

EXPECTED_EU4 = {4097: "dig_1", 912: "dig_1", 2914: "dig_2", 4124: "dig_2", 526: "dig_2", 62: "dig_2",
                4078: "infested_hold", 4218: "infested_hold", 2863: "ruined_hold"}


class HoldDataTests(unittest.TestCase):
    def test_nine_holds_one_ruined(self):
        self.assertEqual(len(holds.HOLDS), 9)
        self.assertEqual([h["name"] for h in holds.HOLDS if h["ruined"]], ["Khugdihr"])

    @unittest.skipUnless(LIVE, "needs Anbennar CK3")
    def test_titles_and_baronies_exist(self):
        _names, provinces, county_baronies, _caps = imp.ck3_titles(ANBENNAR_CK3)
        for h in holds.HOLDS:
            self.assertIn(h["barony"], provinces)
            if h["title"].startswith("c_"):
                self.assertIn(h["barony"], county_baronies[h["title"]])
            else:
                self.assertEqual(h["title"], h["barony"])

    @unittest.skipUnless(LIVE_EU4, "needs EU4 Anbennar")
    def test_eu4_provinces_are_eu4_holds(self):
        for h in holds.HOLDS:
            files = list(EU4_HISTORY.glob(f"{h['eu4_province']} - *.txt"))
            self.assertEqual(len(files), 1, h["name"])
            text = files[0].read_text(encoding="latin-1")
            self.assertIn(EXPECTED_EU4[h["eu4_province"]], re.findall(r"\b(?:dig_\d+|ruined_hold|infested_hold)\b", text),
                          h["name"])

    def test_levels_rise(self):
        self.assertEqual(len(holds.LEVELS), 10)
        for key in ("fort_level", "defender_holding_advantage", "levy_size", "tax_mult", "garrison_size"):
            values = [l[key] for l in holds.LEVELS]
            self.assertEqual(values, sorted(values), key)
        self.assertLessEqual(max(l["fort_level"] for l in holds.LEVELS), 8)

    def test_start_levels(self):
        self.assertEqual({h["name"]: h["start_level"] for h in holds.HOLDS},
                         {"Marrhold": 1, "Anvilwright": 1, "Verkal Gulan": 2, "Seghdihr": 2, "Ovdal Tûngr": 2,
                          "Rubyhold": 2, "Hehodovar": 2, "Gor Ozumbrog": 2, "Khugdihr": 1})

    def test_buildings_and_constants(self):
        self.assertEqual([(b["key"], b["min_level"]) for b in holds.DWARVEN_BUILDINGS],
                         [("deep_mine", 3), ("runeforge", 5), ("hall_of_the_ancestors", 7)])
        self.assertEqual(set(holds.ASSET_BAND), set(range(1, 11)))


if __name__ == "__main__":
    unittest.main()
