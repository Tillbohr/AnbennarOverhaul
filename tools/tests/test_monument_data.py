import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import build_monuments as bm  # noqa: E402
import import_eu4_monuments as imp  # noqa: E402
from data.monuments import translation as tr  # noqa: E402
from data.monuments.cannor import EXCLUDED, MONUMENTS  # noqa: E402

ANBENNAR_CK3 = imp.DEFAULT_ANBENNAR_CK3
LIVE = ANBENNAR_CK3.is_dir()
if LIVE:
    _TITLES = imp.ck3_titles(ANBENNAR_CK3)
    CK3_PROVINCE_OF = _TITLES[1]
    ANBENNAR_SLOT_PROVINCES = set(imp.anbennar_slots(ANBENNAR_CK3))
else:
    CK3_PROVINCE_OF, ANBENNAR_SLOT_PROVINCES = {}, set()

MAX_FORT_LEVEL = 4
MAX_COUNTY_TAX_MULT = 0.3
DIRTY_TEXT = (chr(92) + "n", "---", "\ufffd", "\u00a7", "\u2018", "\u2019", "\u201c", "\u201d", "\u2013", "\u2014",
              "\u00b4")


class CannorMonumentTests(unittest.TestCase):
    def test_every_monument_is_complete(self):
        for m in MONUMENTS:
            self.assertTrue(m["barony"] and m["province"], m["eu4_key"])
            self.assertTrue(m["name"] and m["desc"], m["eu4_key"])
            self.assertIn(m["category"], tr.ICONS, m["eu4_key"])
            self.assertEqual(len(m["levels"]), 3)

    def test_text_is_clean(self):
        for m in MONUMENTS:
            for field in ("name", "desc"):
                for dirty in DIRTY_TEXT:
                    self.assertNotIn(dirty, m[field], f"{m['eu4_key']} {field}")
                self.assertEqual(m[field], m[field].strip(), f"{m['eu4_key']} {field}")
                self.assertNotIn("  ", m[field], f"{m['eu4_key']} {field}")

    def test_gates_are_explained(self):
        for m in MONUMENTS:
            self.assertEqual(bool(m["gate"]), bool(m["gate_desc"]), m["eu4_key"])
            if not m["gate"] and any(n.startswith("gate atom") for n in m["notes"]):
                self.assertTrue(any(n.startswith("Gate decision:") for n in m["notes"]), m["eu4_key"])

    @unittest.skipUnless(LIVE, "needs Anbennar CK3")
    def test_baronies_unique_and_real(self):
        baronies = [m["barony"] for m in MONUMENTS]
        self.assertEqual(len(baronies), len(set(baronies)))
        for m in MONUMENTS:
            self.assertEqual(CK3_PROVINCE_OF[m["barony"]], m["province"], m["eu4_key"])

    @unittest.skipUnless(LIVE, "needs Anbennar CK3")
    def test_new_slots_avoid_anbennar_slots(self):
        for m in MONUMENTS:
            if m["levels"][0].startswith("aov_monument_") or m["levels"][0] == "castle_dameris_01":
                self.assertNotIn(m["province"], ANBENNAR_SLOT_PROVINCES, m["eu4_key"])

    def test_accounting(self):
        self.assertEqual(len(MONUMENTS) + len(EXCLUDED), 82)
        self.assertEqual(sum(m["levels"][0].startswith("aov_monument_") for m in MONUMENTS), 64)

    @unittest.skipUnless(LIVE, "needs Anbennar CK3")
    def test_every_level_has_an_effect(self):
        """Final review I2: a level of a new chain needs a modifier or an on_complete (chains that start with an
        Anbennar building carry Anbennar's effects)."""
        known = bm.anbennar_keys()
        for m in MONUMENTS:
            if bm.chain_top(m, known):
                continue
            for level, tier in enumerate(m["tiers"], 1):
                has = any(tier[b] for b in bm.BLOCKS) or tier["on_complete"].strip()
                self.assertTrue(has, f"{m['eu4_key']} level {level}")

    def test_balance_guard(self):
        """Ruling 7: no level fortifies above 4 or adds more than 30% county tax."""
        for m in MONUMENTS:
            for level, tier in enumerate(m["tiers"], 1):
                for block in ("province_modifier", "county_modifier"):
                    self.assertLessEqual(tier[block].get("fort_level", 0), MAX_FORT_LEVEL,
                                         f"{m['eu4_key']} level {level} {block}")
                self.assertLessEqual(tier["county_modifier"].get("tax_mult", 0), MAX_COUNTY_TAX_MULT,
                                     f"{m['eu4_key']} level {level}")



class RegionMonumentTests(unittest.TestCase):
    """The same data checks as Cannor, for the regions after it (no Anbennar chains there)."""

    COUNTS = {"dwarovar": 5, "bulwar": 12, "salahad": 10, "deepwoods": 6}

    def test_complete_clean_and_translated(self):
        for region, count in self.COUNTS.items():
            monuments = bm.load_monuments(region)
            self.assertEqual(len(monuments), count, region)
            for m in monuments:
                self.assertTrue(m["barony"] and m["province"] and m["name"] and m["desc"], m["eu4_key"])
                self.assertIn(m["category"], tr.ICONS, m["eu4_key"])
                self.assertEqual(bool(m["gate"]), bool(m["gate_desc"]), m["eu4_key"])
                for field in ("name", "desc"):
                    for dirty in DIRTY_TEXT:
                        self.assertNotIn(dirty, m[field], f"{m['eu4_key']} {field}")
                    self.assertNotIn("  ", m[field], f"{m['eu4_key']} {field}")
                for level, tier in enumerate(m["tiers"], 1):
                    self.assertFalse([d for d in tier["dropped"] if d.endswith("not in the translation table")],
                                     m["eu4_key"])
                    for block in ("province_modifier", "county_modifier"):
                        self.assertLessEqual(tier[block].get("fort_level", 0), MAX_FORT_LEVEL, m["eu4_key"])
                    self.assertLessEqual(tier["county_modifier"].get("tax_mult", 0), MAX_COUNTY_TAX_MULT,
                                         m["eu4_key"])
                    has = any(tier[b] for b in bm.BLOCKS) or tier["on_complete"].strip()
                    self.assertTrue(has, f"{m['eu4_key']} level {level}")
                if not m["gate"] and any(n.startswith("gate atom") for n in m["notes"]):
                    self.assertTrue(any(n.startswith("Gate decision:") for n in m["notes"]), m["eu4_key"])

    @unittest.skipUnless(LIVE, "needs Anbennar CK3")
    def test_baronies_unique_real_and_free(self):
        provinces = []
        for region in self.COUNTS:
            for m in bm.load_monuments(region):
                self.assertEqual(CK3_PROVINCE_OF[m["barony"]], m["province"], m["eu4_key"])
                self.assertNotIn(m["province"], ANBENNAR_SLOT_PROVINCES, m["eu4_key"])
                self.assertTrue(m["levels"][0].startswith("aov_monument_"), m["eu4_key"])
                provinces.append(m["province"])
        provinces += [m["province"] for m in MONUMENTS]
        self.assertEqual(len(provinces), len(set(provinces)))


if __name__ == "__main__":
    unittest.main()
