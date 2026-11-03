import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import serpentreach_layout as sl  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import segbandal as data  # noqa: E402

EU4 = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355")
ANBENNAR = Path(__file__).resolve().parents[2].parent / "anbennar-ck3-dev-master"
HAVE_GAME_DATA = EU4.is_dir() and ANBENNAR.is_dir()
REUSED = {"d_hehodovar", "d_hehorod", "d_seghdihr", "d_verkal_gulan", "d_xazorod", "d_gor_ozumbrog"}


def titles_text():
    return "\n".join(p.read_text(encoding="utf-8-sig", errors="replace")
                     for p in sorted((ANBENNAR / "common/landed_titles").glob("*.txt")))


class ClipTests(unittest.TestCase):
    def test_floor_keeps_margin_from_non_neighbours(self):
        # rock 9 everywhere; road A (id 1) a column at x 10, road B (id 2) a column at x 20; the EU4 label "a" covers
        # x 11..19 and neighbours A only in EU4
        W, H = 32, 12

        def ck(x, y):
            return 1 if x == 10 else 2 if x == 20 else 9 if 0 <= x < W and 0 <= y < H else 0
        labels = {(x, y): "a" for x in range(11, 20) for y in range(H)}
        floor = sl.clip_floor(labels, ck, (0, 0, W, H), 9, data.WALL_MARGIN, {"a": {1}})["a"]
        self.assertIn((11, 5), floor)  # touches A
        self.assertTrue(all(20 - x >= data.WALL_MARGIN for x, _ in floor))  # keeps WALL_MARGIN from B
        self.assertIn((20 - data.WALL_MARGIN, 5), floor)

    def test_no_allowed_neighbours_keeps_margin_everywhere(self):
        W, H = 32, 12

        def ck(x, y):
            return 1 if x == 10 else 9 if 0 <= x < W and 0 <= y < H else 0
        labels = {(x, y): "a" for x in range(11, 20) for y in range(H)}
        floor = sl.clip_floor(labels, ck, (0, 0, W, H), 9, 4, {})["a"]
        self.assertEqual(min(x for x, _ in floor), 14)

    def test_allowed_neighbours(self):
        adj = {7: {1, 8}, 8: {7}}
        allowed = sl.allowed_neighbours(adj, {1: "c_road"}, {"c_road": {100, 101}})
        self.assertEqual(allowed, {7: {100, 101}, 8: set()})

    def test_county_provinces(self):
        text = "e_x = { k_x = { d_x = { c_road = { b_a = { province = 5 } b_b = { province = 6 } } } } }"
        self.assertEqual(sl.county_provinces(text), {"c_road": {5, 6}})


class DataTests(unittest.TestCase):
    def test_area_duchies_cover_region_and_reuse_six(self):
        if not HAVE_GAME_DATA:
            self.skipTest("needs EU4 Anbennar")
        import eu4_import as eu4i
        areas = eu4i.province_areas(EU4)
        region = {areas[p] for p in eu4i.region_provinces((data.REGION,), EU4)}
        self.assertEqual(set(data.AREA_DUCHIES), region)
        self.assertEqual(sorted(data.AREA_ORDER), sorted(region))
        self.assertEqual({d for d, _, reused in data.AREA_DUCHIES.values() if reused}, REUSED)

    @unittest.skipUnless(HAVE_GAME_DATA, "needs EU4 Anbennar and Anbennar CK3")
    def test_existing_names_match_anbennar(self):
        import eu4_import as eu4i
        from data.holds import HOLDS
        text = titles_text()
        counties = sl.county_provinces(text)
        names = eu4i.province_names(EU4)
        holds = {h["eu4_province"]: h["title"] for h in HOLDS}
        self.assertEqual(len(data.EXISTING), 20)
        for eu4_id, county in data.EXISTING.items():
            self.assertIn(county, counties, county)
            m = re.fullmatch(r"Dwarovrod \| (\d+) \|", names[eu4_id])
            want = f"c_dwarovrod{m.group(1)}" if m else holds.get(eu4_id, "c_" + sl.slug(names[eu4_id]))
            self.assertEqual(county, want, eu4_id)


@unittest.skipUnless(HAVE_GAME_DATA, "needs EU4 Anbennar and Anbennar CK3")
class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ck3 = sl.load_ck3(ANBENNAR)
        cls.lay = sl.layout(ANBENNAR, EU4, cls.ck3, cfg=data)
        cls.counties = sl.county_provinces(titles_text())

    def test_existing_county_missing_stops(self):
        cfg = SimpleNamespace(**{k: getattr(data, k) for k in dir(data) if k.isupper()})
        cfg.EXISTING = {**data.EXISTING, 2889: "c_nowhere"}
        with self.assertRaisesRegex(GeneratorError, "c_nowhere"):
            sl.layout(ANBENNAR, EU4, self.ck3, cfg=cfg)

    def test_counts(self):
        self.assertEqual(len(self.lay.counties), 37)
        ids = sorted(self.lay.provinces)
        self.assertEqual(len(ids), 71)
        self.assertEqual(ids, list(range(ids[0], ids[0] + 71)))

    def test_only_rock_changes(self):
        pm = self.ck3[0]
        self.assertEqual({pm.ids[y * pm.width + x] for x, y in self.lay.owner}, {data.SOURCE_PROVINCE})

    def test_every_new_county_reaches_a_neighbour(self):
        pm = self.ck3[0]
        W = pm.width
        old = {pid for c in data.EXISTING.values() for pid in self.counties[c]}
        county_of = {p: self.lay.provinces[pid].county for p, pid in self.lay.owner.items()}
        for c in self.lay.counties:
            pixels = [p for pid in c.baronies for p in self.lay.provinces[pid].pixels]
            touched = set()
            for x, y in pixels:
                for dx, dy in sl.N4:
                    n = (x + dx, y + dy)
                    if n in county_of and county_of[n] != c.key:
                        touched.add(county_of[n])
                    elif n not in county_of and pm.ids[n[1] * W + n[0]] in old:
                        touched.add(pm.ids[n[1] * W + n[0]])
            self.assertTrue(touched, c.key)

    def test_segbandal_connected(self):
        pm = self.ck3[0]
        W = pm.width
        old = {pid for c in data.EXISTING.values() for pid in self.counties[c]}
        old |= {pid for c in ("c_hehodovar", "c_seghdihr", "c_verkal_gulan", "c_gor_ozumbrog") for pid in self.counties[c]}
        pixels = set(self.lay.owner) | {(i % W, i // W) for i, p in enumerate(pm.ids) if p in old}
        self.assertEqual(len(sl.components(pixels)), 1)


if __name__ == "__main__":
    unittest.main()
