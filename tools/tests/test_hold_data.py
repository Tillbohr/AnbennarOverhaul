import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import pdx_script  # noqa: E402
from data import holds  # noqa: E402

ANBENNAR_CK3 = pdx_script.ANBENNAR_CK3
LIVE = ANBENNAR_CK3.is_dir()


class HoldDataTests(unittest.TestCase):
    def test_nine_holds_one_ruined(self):
        self.assertEqual(len(holds.HOLDS), 9)
        self.assertEqual([h["name"] for h in holds.HOLDS if h["ruined"]], ["Khugdihr"])

    @unittest.skipUnless(LIVE, "needs Anbennar CK3")
    def test_titles_and_baronies_exist(self):
        provinces, county_baronies = pdx_script.ck3_titles(ANBENNAR_CK3)
        for h in holds.HOLDS:
            self.assertIn(h["barony"], provinces)
            if h["title"].startswith("c_"):
                self.assertIn(h["barony"], county_baronies[h["title"]])
            else:
                self.assertEqual(h["title"], h["barony"])

    def test_start_levels(self):
        self.assertEqual({h["name"]: h["start_level"] for h in holds.HOLDS},
                         {"Marrhold": 1, "Anvilwright": 1, "Verkal Gulan": 2, "Seghdihr": 2, "Ovdal Tûngr": 2,
                          "Rubyhold": 2, "Hehodovar": 2, "Gor Ozumbrog": 2, "Khugdihr": 1})

    def test_buildings_and_constants(self):
        self.assertEqual(set(holds.ASSET_BAND), set(range(1, 11)))


if __name__ == "__main__":
    unittest.main()
