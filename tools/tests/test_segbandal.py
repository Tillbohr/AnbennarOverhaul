import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import serpentreach_layout as sl  # noqa: E402
import shared_trace  # noqa: E402
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



class ArmsGuardTests(unittest.TestCase):
    def test_scripted_arms_reads_anbennar_title_keys(self):
        import tempfile
        import build_segbandal as bsb
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "common/coat_of_arms/coat_of_arms"
            folder.mkdir(parents=True)
            (folder / "a.txt").write_text("k_hehodovar = {\n\tpattern = x\n}\n# d_xazorod = {\n"
                                          "template = {\n\tc_gor_ozumbrog = { }\n}\n", encoding="utf-8-sig")
            self.assertEqual(bsb._scripted_arms(Path(tmp)), {"k_hehodovar", "c_gor_ozumbrog"})
        self.assertEqual(bsb.arms_keys(), {"k_hehodovar", "d_hehodovar", "c_hehodovar", "k_gor_ozumbrog",
                                           "d_gor_ozumbrog", "c_gor_ozumbrog", "d_hehorod", "d_xazorod"})


class GuardTests(unittest.TestCase):
    """The review's guards: no contact EU4 lacks, no duplicate of a province Anbennar gained, no endless link loop."""

    def two_counties(self):
        provinces = {10: sl.Province(10, (1, 1, 1), "c_a", 0, [(5, 5)], (5, 5)),
                     11: sl.Province(11, (2, 2, 2), "c_b", 0, [(6, 5)], (6, 5))}
        counties = [sl.County("c_a", 1, "A", "x_area", "cavern", [10]), sl.County("c_b", 2, "B", "x_area", "cavern", [11])]
        owner = {(5, 5): 10, (6, 5): 11}
        return provinces, counties, owner

    def test_foreign_contacts_between_new_counties(self):
        provinces, counties, owner = self.two_counties()
        ck = lambda x, y: 2608  # noqa: E731
        self.assertEqual(sl.foreign_contacts(ck, owner, provinces, counties, {1: set(), 2: set()}, {}, set()),
                         [("c_a", "c_b"), ("c_b", "c_a")])
        self.assertEqual(sl.foreign_contacts(ck, owner, provinces, counties, {1: {2}, 2: {1}}, {}, set()), [])

    def test_foreign_contacts_with_anbennar(self):
        provinces, counties, owner = self.two_counties()
        ck = lambda x, y: 99 if (x, y) == (5, 4) else 98 if (x, y) == (6, 4) else 2608  # noqa: E731
        adj = {1: {2}, 2: {1}}
        self.assertEqual(sl.foreign_contacts(ck, owner, provinces, counties, adj, {1: {99}, 2: set()}, {98, 99}),
                         [("c_b", 98)])

    def test_anbennar_duplicates(self):
        candidates = [(7, "c_dwarovrod_25", "Dwarovrod 25"), (8, "c_longtunnel", "Longtunnel")]
        self.assertEqual(sl.anbennar_duplicates(candidates, {7: "Dwarovrod 25"}, set()), ["c_dwarovrod_25 (province 7)"])
        self.assertEqual(sl.anbennar_duplicates(candidates, {}, {"c_dwarovrod25"}), ["c_dwarovrod_25 (c_dwarovrod25)"])
        self.assertEqual(sl.anbennar_duplicates(candidates, {7: "Thissilen"}, {"c_other"}), [])

    def test_join_pieces_stops_on_a_repeating_piece(self):
        provinces, counties, owner = self.two_counties()
        provinces = {10: provinces[10]}
        counties = counties[:1]
        owner = {(5, 5): 10}

        def no_progress(*args):  # a link that leaves the piece as loose as before
            return sl.Opening("c_a", 99, set(), (0, 0), (5, 5))
        with self.assertRaisesRegex(GeneratorError, "c_a"):
            sl.join_pieces(lambda x, y: 2608, counties, provinces, owner, {}, {(0, 0)}, 2608, data, [],
                           link=no_progress)


@unittest.skipUnless(HAVE_GAME_DATA, "needs EU4 Anbennar and Anbennar CK3")
class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (_, cls.lay, _), cls.ck3 = shared_trace.layouts()
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
        cls.lays, _ = shared_trace.layouts()
        cls.files = bs.build_from_layout(ANBENNAR, cls.lays)

    def test_map_files_hold_every_region(self):
        serp, seg, wd = self.lays
        rows = self.files["map_data/definition.csv"].decode("utf-8", errors="replace").splitlines()
        anbennar = (ANBENNAR / "map_data/definition.csv").read_bytes().decode("utf-8", errors="replace").splitlines()
        new = [int(r.split(";")[0]) for r in rows[len(anbennar):]]
        rock_ids = [max(wd.provinces) + 1, max(wd.provinces) + 2]  # the range rock (test_range_rock.py)
        self.assertEqual(new, sorted(serp.provinces) + sorted(seg.provinces) + sorted(wd.provinces) + rock_ids)
        colours = [tuple(r.split(";")[1:4]) for r in rows if r[:1].isdigit() and r.split(";")[0] != "0"]
        self.assertEqual(len(colours), len(set(colours)))
        for name in self.bs.LOCATOR_FILES:
            text = self.files[f"{self.bs.LOCATOR_DIR}/{name}.txt"].decode("utf-8")
            for pid in list(seg.provinces)[:3] + list(serp.provinces)[:3]:
                self.assertEqual(len(re.findall(r"\bid=" + str(pid) + r"\n", text)), 1, (name, pid))

    def test_serpentreach_ids_unchanged(self):
        serp, seg = self.lays[:2]
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
        import eu4_import as eu4i
        cls.bsb = bsb
        cls.lay = shared_trace.layouts()[0][1]
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

    def test_every_title_has_a_full_chain_at_load(self):
        # CK3 crashes running history when a landed title has no county -> duchy -> kingdom -> empire chain in the
        # landed titles themselves (history de jure moves come too late)
        parents = self.bsb.title_parents(self.titles)
        tiers = "cdke"
        for key, parent in parents.items():
            if key.startswith("e_"):
                self.assertIsNone(parent, key)
            else:
                self.assertIsNotNone(parent, f"{key} has no parent in landed titles")
                self.assertEqual(tiers.index(parent[0]), tiers.index(key[0]) + 1, f"{key} under {parent}")

    def test_new_titles_link_by_history(self):
        parked = [k for k, p in self.bsb.title_parents(self.titles).items()
                  if p in data.PARKING and k not in data.PARKING]
        self.assertIn("k_gor_vazumbrog", parked)
        for key in parked:
            self.assertRegex(self.history, rf"(?m)^{key} = \{{\n\t1\.1\.1 = \{{ de_jure_liege = \w+ \}}")
        kept = {k: p for k, p in self.de_jure().items() if p in data.PARKING and k not in data.PARKING}
        self.assertEqual(kept, {}, "parking titles keep de jure land")
        for key in data.PARKING:
            self.assertNotRegex(self.history, rf"(?m)^{key} = ")
        anbennar = set(self.bsb.title_parents(titles_text()))
        self.assertFalse(set(self.bsb.title_parents(self.titles)) & anbennar)

    def test_new_duchies_list_capital_first(self):
        for _, duchy, body in re.findall(r"(?ms)^(\t*)(d_\w+) = \{\n(.*?)^\1\}", self.titles):
            counties = re.findall(r"(?m)^\t*(c_\w+) = \{", body)
            capital = re.search(r"capital = (c_\w+)", body).group(1)
            if counties:
                self.assertEqual(counties[0], capital, duchy)
        self.assertRegex(self.titles, r"\n\t\td_vazumbrog = \{\n\t\t\tcolor = \{[^}]*\}\n\t\t\tcapital = c_gor_vazumbrog\n")
        self.assertRegex(self.titles, r"\n\t\td_dwarovrod_33_35 = \{\n\t\t\tcolor = \{[^}]*\}\n\t\t\tcapital = c_dwarovrod33\n")

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
        anbennar = {"d_hehodovar", "d_gor_ozumbrog", "d_hehorod", "d_xazorod"}
        self.assertEqual(set(re.findall(r"(?m)^(d_\w+) = \{", arms)) - {"d_vazumbrog"}, new_duchies | anbennar)
        self.assertEqual(set(data.DUCHY_CHARGES), {a for a, (d, _, _) in data.AREA_DUCHIES.items() if d in new_duchies})

    def test_arms_of_anbennar_holds(self):
        # EU4 I15 Hehodovar and I17 Gor Ozumbrog: kingdom, hold duchy and hold county, over the flag's commonest colour
        arms = self.files[self.bsb.ARMS].decode("utf-8-sig")
        for keys, emblem, field in ((("k_hehodovar", "d_hehodovar", "c_hehodovar"), "aov_hehodovar.dds", "58 39 236"),
                                    (("k_gor_ozumbrog", "d_gor_ozumbrog", "c_gor_ozumbrog"), "aov_gor_ozumbrog.dds",
                                     "56 57 56")):
            for key in keys:
                self.assertRegex(arms, rf'(?m)^{key} = \{{\n\tpattern = "pattern_solid.dds"\n\tcolor1 = rgb \{{ {field} \}}'
                                       rf'\n\ttextured_emblem = \{{\n\t\ttexture = "{emblem}"')
            self.assertTrue((self.bsb.SUBMOD / "gfx/coat_of_arms/textured_emblems" / emblem).is_file(), emblem)
        # Hehorod and Xazorod: a charge on Anbennar's map colour
        for duchy, field, charge in (("d_hehorod", "16 55 183", "ce_anb_bridge_one_arch.dds"),
                                     ("d_xazorod", "93 160 141", "ce_anb_gem_socket.dds")):
            self.assertRegex(arms, rf'(?m)^{duchy} = \{{\n\tpattern = "[^"]+"\n\tcolor1 = rgb \{{ {field} \}}\n'
                                   rf'(\t.*\n)*?\t\ttexture = "{charge}"')

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
