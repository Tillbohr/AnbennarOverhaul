import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import pdx_script  # noqa: E402
from data import holds  # noqa: E402

ANBENNAR_CK3 = pdx_script.ANBENNAR_CK3
LIVE = ANBENNAR_CK3.is_dir()
RUIN_NAMES = ("aov_hold_ruined", "aov_hold_is_ruined", "aov_hold_is_working", "aov_clear_ruins_decision",
              "aov_hold_ruin", "aov_ruined_hold", "aov_restoring_hold", "aov_restore_pending",
              "aov_hold_begin_restoration_effect", "ruined_hold")


class HoldDataTests(unittest.TestCase):
    def test_no_ruin_names_left(self):
        """The ruined holds mechanic is gone from script, interface, localization and tools."""
        root = Path(__file__).resolve().parents[2]
        here = Path(__file__).resolve()
        files = [p for top, suffixes in (("common", {".txt"}), ("events", {".txt"}), ("gui", {".gui"}),
                                         ("localization", {".yml"}), ("tools", {".py"}))
                 for p in (root / top).rglob("*") if p.suffix in suffixes and p != here]
        found = sorted(str(p.relative_to(root)) for p in files
                       if any(n in p.read_text(encoding="utf-8-sig", errors="replace") for n in RUIN_NAMES))
        self.assertEqual(found, [])

    def test_twenty_four_holds(self):
        self.assertEqual(len(holds.HOLDS), 24)
        rows = [(h["name"], h["eu4_province"], h["title"], h["barony"], h["start_level"]) for h in holds.HOLDS]
        self.assertIn(("Gor Vazumbrog", 4217, "c_gor_vazumbrog", "b_gor_vazumbrog", 2), rows)
        self.assertEqual(rows[16:], [  # West Dwarovar's, after Segbandal's
            ("Amldihr", 4119, "c_amldihr", "b_amldihr", 2),
            ("Haraz Orldhûm", 2868, "c_haraz_orldhum", "b_haraz_orldhum", 1),
            ("Mithradhûm", 4236, "c_mithradhum", "b_mithradhum", 1),
            ("Er-Natvir", 2931, "c_er_natvir", "b_er_natvir", 1),
            ("Verkal Kozenad", 4056, "c_verkal_kozenad", "b_verkal_kozenad", 1),
            ("Hul-Jorkad", 2963, "c_hul_jorkad", "b_hul_jorkad", 1),
            ("Orlazam-az-dihr", 4147, "c_orlazam_az_dihr", "b_orlazam_az_dihr", 1),
            ("Dûr-Vazhatun", 4020, "c_dur_vazhatun", "b_dur_vazhatun", 1)])

    @unittest.skipUnless(LIVE, "needs Anbennar CK3")
    def test_titles_and_baronies_exist(self):
        provinces, county_baronies = pdx_script.ck3_titles(ANBENNAR_CK3)
        ours = pdx_script.ck3_titles(Path(__file__).resolve().parents[2])  # Serpentreach's and later holds are ours
        provinces.update(ours[0])
        county_baronies.update(ours[1])
        for h in holds.HOLDS:
            self.assertIn(h["barony"], provinces)
            if h["title"].startswith("c_"):
                self.assertIn(h["barony"], county_baronies[h["title"]])
            else:
                self.assertEqual(h["title"], h["barony"])

    def test_start_levels(self):
        self.assertEqual({h["name"]: h["start_level"] for h in holds.HOLDS},
                         {"Marrhold": 1, "Anvilwright": 1, "Verkal Gulan": 2, "Seghdihr": 2, "Ovdal Tûngr": 2,
                          "Rubyhold": 2, "Hehodovar": 2, "Gor Ozumbrog": 2, "Khugdihr": 1,
                          "Arg-Ôrdstun": 2, "Ovdal Lodhum": 2, "Gor Bûrad": 2, "Shazstundihr": 1,
                          "Verkal Skomdihr": 1, "Orlghelovar": 1, "Gor Vazumbrog": 2, "Amldihr": 2,
                          "Haraz Orldhûm": 1, "Mithradhûm": 1, "Er-Natvir": 1, "Verkal Kozenad": 1, "Hul-Jorkad": 1,
                          "Orlazam-az-dihr": 1, "Dûr-Vazhatun": 1})

    def test_buildings_and_constants(self):
        self.assertEqual(set(holds.ASSET_BAND), set(range(1, 11)))


if __name__ == "__main__":
    unittest.main()
