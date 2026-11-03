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


@unittest.skipUnless(HAVE_GAME_DATA, "needs EU4 Anbennar and Anbennar CK3")
class MapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_serpentreach as bs
        cls.bs = bs
        cls.lays = bs.layouts(ANBENNAR, EU4)
        cls.files = bs.build_from_layout(ANBENNAR, cls.lays)

    def test_map_files_hold_both_regions(self):
        serp, seg = self.lays
        rows = self.files["map_data/definition.csv"].decode("utf-8", errors="replace").splitlines()
        anbennar = (ANBENNAR / "map_data/definition.csv").read_bytes().decode("utf-8", errors="replace").splitlines()
        new = [int(r.split(";")[0]) for r in rows[len(anbennar):]]
        self.assertEqual(new, sorted(serp.provinces) + sorted(seg.provinces))
        colours = [tuple(r.split(";")[1:4]) for r in rows if r[:1].isdigit() and r.split(";")[0] != "0"]
        self.assertEqual(len(colours), len(set(colours)))
        for name in self.bs.LOCATOR_FILES:
            text = self.files[f"{self.bs.LOCATOR_DIR}/{name}.txt"].decode("utf-8")
            for pid in list(seg.provinces)[:3] + list(serp.provinces)[:3]:
                self.assertEqual(len(re.findall(r"\bid=" + str(pid) + r"\n", text)), 1, (name, pid))

    def test_serpentreach_ids_unchanged(self):
        serp, seg = self.lays
        self.assertEqual((min(serp.provinces), max(serp.provinces)), (6944, 7067))
        self.assertEqual(min(seg.provinces), 7068)



class ParseTests(unittest.TestCase):
    def test_title_parents(self):
        import build_segbandal as bsb
        text = "e_a = {\n\tk_b = {\n\t\td_c = {\n\t\t\tc_d = {\n\t\t\t\tb_e = { province = 1 }\n\t\t\t}\n\t\t}\n\t}\n}\nc_f = { }\n"
        self.assertEqual(bsb.title_parents(text), {"e_a": None, "k_b": "e_a", "d_c": "k_b", "c_d": "d_c", "c_f": None})

    def test_title_holder(self):
        import build_segbandal as bsb
        text = "k_x = {\n\t1000.1.1 = { change_development_level = 3 }\n\t921.9.24 = {\n\t\tholder = 126 #Ungrim\n\t}\n}\n"
        self.assertEqual(bsb.title_holder(text, "k_x"), ("921.9.24", "126"))
        with self.assertRaises(GeneratorError):
            bsb.title_holder(text, "k_y")


@unittest.skipUnless(HAVE_GAME_DATA, "needs EU4 Anbennar and Anbennar CK3")
class TitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_segbandal as bsb
        import build_serpentreach as bs
        import eu4_import as eu4i
        cls.bsb = bsb
        cls.lay = bs.layouts(ANBENNAR, EU4)[1]
        cls.files = bsb.build_from_layout(ANBENNAR, cls.lay)
        cls.titles = cls.files[bsb.TITLES].decode("utf-8-sig")
        cls.history = cls.files[bsb.TITLE_HISTORY].decode("utf-8-sig")
        cls.areas = eu4i.province_areas(EU4)

    def de_jure(self):
        """Every title's de jure parent after our titles and history apply over Anbennar's."""
        parents = self.bsb.title_parents(titles_text())
        parents.update(self.bsb.title_parents(self.titles))
        for key, liege in re.findall(r"(?m)^(\w+) = \{\n\t1\.1\.1 = \{ de_jure_liege = (\w+) \}", self.history):
            parents[key] = liege
        return parents

    def test_de_jure_matches_areas(self):
        parents = self.de_jure()
        want = {c: data.AREA_DUCHIES[self.areas[e]][0] for e, c in data.EXISTING.items()}
        want.update({c.key: data.AREA_DUCHIES[c.area][0] for c in self.lay.counties})
        self.assertEqual({c: parents[c] for c in want}, want)
        for area, (duchy, kingdom, _) in data.AREA_DUCHIES.items():
            self.assertEqual(parents[duchy], kingdom, duchy)
        self.assertEqual(parents["k_gor_vazumbrog"], "e_middle_dwarovar")
        for emptied in ("d_seghrod", "d_gulanrod", "d_ozumrod"):
            self.assertNotIn(emptied, parents.values())
        self.assertEqual(parents["c_heros_vale"], "d_heros_vale")

    def test_new_titles_link_by_history(self):
        tops = re.findall(r"(?m)^([kdc]_\w+) = \{", self.titles)
        self.assertIn("k_gor_vazumbrog", tops)
        for key in tops:
            self.assertRegex(self.history, rf"(?m)^{key} = \{{\n\t1\.1\.1 = \{{ de_jure_liege = \w+ \}}")
        anbennar = set(self.bsb.title_parents(titles_text()))
        self.assertFalse(set(self.bsb.title_parents(self.titles)) & anbennar)

    def test_new_duchies_list_capital_first(self):
        for duchy, body in re.findall(r"(?ms)^\t?(d_\w+) = \{\n(.*?)^\t?\}", self.titles):
            counties = re.findall(r"(?m)^\t*(c_\w+) = \{", body)
            capital = re.search(r"capital = (c_\w+)", body).group(1)
            if counties:
                self.assertEqual(counties[0], capital, duchy)
        self.assertRegex(self.titles, r"\n\td_vazumbrog = \{\n\t\tcolor = \{[^}]*\}\n\t\tcapital = c_gor_vazumbrog\n")
        self.assertRegex(self.titles, r"\nd_dwarovrod_33_35 = \{\n\tcolor = \{[^}]*\}\n\tcapital = c_dwarovrod33\n")

    def test_holders(self):
        elders = {"d_steamsource", "d_stunad_kradoz", "d_goblin_grotto", "d_greatcavern", "d_xazor"}
        held = set(re.findall(r"(?m)^(\w+) = \{\n(?:\t1\.1\.1 = \{[^\n]*\n)?\t860\.1\.1 = \{ holder = aov_sb_",
                              self.history))
        self.assertEqual({k for k in held if k.startswith("d_")}, elders)
        self.assertIn("d_steamsource = {\n\t1.1.1 = { de_jure_liege = k_seghdihr }\n"
                      "\t860.1.1 = { holder = aov_sb_steamsource_1 }\n\t921.9.24 = { liege = k_seghdihr }", self.history)
        self.assertIn("d_xazor = {\n\t1.1.1 = { de_jure_liege = k_verkal_gulan }\n"
                      "\t860.1.1 = { holder = aov_sb_xazor_1 }\n\t903.4.17 = { liege = k_verkal_gulan }", self.history)
        self.assertIn("c_stonewall = {\n\t1.1.1 = { de_jure_liege = d_seghdihr }\n\t921.9.24 = { holder = 126 }", self.history)
        for county in ("c_gor_vazumbrog", "c_hehogrims_mausoleum", "c_ulagom_canyon", "c_deep_ones_cave"):
            self.assertNotRegex(self.history, rf"(?ms)^{county} = \{{[^}}]*holder")

    def test_cultures(self):
        history = self.files[self.bsb.PROVINCE_HISTORY].decode("utf-8-sig")
        want = {"k_gor_vazumbrog": "titanium_dwarvish", "k_hehodovar": "pyrite_dwarvish",
                "k_seghdihr": "citrine_dwarvish", "k_verkal_gulan": "gold_dwarvish", "k_gor_ozumbrog": "topaz_dwarvish"}
        for c in self.lay.counties:
            culture = want[data.AREA_DUCHIES[c.area][1]]
            for pid in c.baronies:
                self.assertRegex(history, rf"(?m)^{pid} = \{{\t# .*\n\tculture = {culture}\n\treligion = ancestor_worship")

    def test_arms(self):
        arms = self.files[self.bsb.ARMS].decode("utf-8-sig")
        for key in ("k_gor_vazumbrog", "d_vazumbrog", "c_gor_vazumbrog"):
            self.assertRegex(arms, rf'(?m)^{key} = \{{\n(\t.*\n)*?\t\ttexture = "aov_gor_vazumbrog.dds"')
        new_duchies = {d for d, _, reused in data.AREA_DUCHIES.values() if not reused} - {"d_vazumbrog"}
        self.assertEqual(set(re.findall(r"(?m)^(d_\w+) = \{", arms)) - {"d_vazumbrog"}, new_duchies)
        self.assertEqual(set(data.DUCHY_CHARGES), {a for a, (d, _, _) in data.AREA_DUCHIES.items() if d in new_duchies})

    def test_every_new_key_has_loc(self):
        loc = self.files[self.bsb.LOC].decode("utf-8-sig")
        for key in re.findall(r"(?m)^\t*([ekdcb]_\w+) = \{", self.titles):
            self.assertRegex(loc, rf"(?m)^ {key}:0 \"")
        self.assertIn(' d_dwarovrod_27_29:0 "Dwarovrod 27-29"', loc)

    def test_outputs_current(self):
        stale = [rel for rel, content in self.files.items()
                 if not (self.bsb.SUBMOD / rel).is_file() or (self.bsb.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_segbandal.py")


if __name__ == "__main__":
    unittest.main()
