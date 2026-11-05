import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import serpentreach_layout as sl  # noqa: E402
import shared_trace  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import west_dwarovar as data  # noqa: E402

EU4 = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355")
ANBENNAR = Path(__file__).resolve().parents[2].parent / "anbennar-ck3-dev-master"
HAVE_GAME_DATA = EU4.is_dir() and ANBENNAR.is_dir()
VALE_AREAS = set(data.SURFACE_AREAS)


def titles_text():
    return "\n".join(p.read_text(encoding="utf-8-sig", errors="replace")
                     for p in sorted((ANBENNAR / "common/landed_titles").glob("*.txt")))


def area_adjacency():
    """{EU4 area: areas it touches} from EU4's provinces.bmp inside FIT_BOX."""
    import eu4_import as eu4i
    emap = sl.Eu4Map(EU4)
    areas = eu4i.province_areas(EU4)
    out = {}
    x0, y0, x1, y1 = data.FIT_BOX
    for y in range(y0, y1):
        for x in range(x0, x1):
            a, b, c = emap.at(x, y), emap.at(x + 1, y), emap.at(x, y + 1)
            for n in (b, c):
                if a != n and a and n and areas.get(a) and areas.get(n) and areas[a] != areas[n]:
                    out.setdefault(areas[a], set()).add(areas[n])
                    out.setdefault(areas[n], set()).add(areas[a])
    return out


@unittest.skipUnless(HAVE_GAME_DATA, "needs EU4 Anbennar and Anbennar CK3")
class DataTests(unittest.TestCase):
    def test_areas_cover_regions(self):
        import eu4_import as eu4i
        areas = eu4i.province_areas(EU4)
        region = {areas[p] for p in eu4i.region_provinces(data.REGIONS, EU4)} - set(data.EXCLUDE_AREAS)
        self.assertEqual(sorted(data.AREA_ORDER), sorted(region))
        listed = [a for _, (_, k) in data.KINGDOMS.items() for a in k]
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(set(listed), region)
        adj = area_adjacency()
        for kkey, (_, kareas) in data.KINGDOMS.items():
            seen, stack = {kareas[0]}, [kareas[0]]
            while stack:
                for n in adj.get(stack.pop(), ()):
                    if n in kareas and n not in seen:
                        seen.add(n)
                        stack.append(n)
            self.assertEqual(seen, set(kareas), f"{kkey} is not contiguous in EU4")

    def test_existing_names_match_anbennar(self):
        import eu4_import as eu4i
        counties = sl.county_provinces(titles_text())
        names = eu4i.province_names(EU4)
        for eu4_id, county in data.EXISTING.items():
            self.assertIn(county, counties, county)
            want = "c_" + sl.slug(sl.display_name(names[eu4_id]))
            self.assertEqual(county.replace("_", ""), want.replace("_", ""), eu4_id)


@unittest.skipUnless(HAVE_GAME_DATA, "needs EU4 Anbennar and Anbennar CK3")
class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.serp, cls.seg, cls.wd), cls.ck3 = shared_trace.layouts()
        cls.counties = sl.county_provinces(titles_text())
        cls.area_of = {c.key: c.area for c in cls.wd.counties}
        cls.old = {pid for c in data.EXISTING.values() for pid in cls.counties[c]}

    def pixels_of(self, pids):
        """Anbennar map pixels of `pids` within 300 px of the West Dwarovar floor."""
        pm = self.ck3[0]
        xs = [p[0] for p in self.wd.owner]
        ys = [p[1] for p in self.wd.owner]
        out = set()
        for y in range(max(min(ys) - 300, 0), min(max(ys) + 300, pm.height)):
            row = pm.ids[y * pm.width:(y + 1) * pm.width]
            for x in range(max(min(xs) - 300, 0), min(max(xs) + 300, pm.width)):
                if row[x] in pids:
                    out.add((x, y))
        return out

    def test_first_id_follows_segbandal(self):
        self.assertEqual(min(self.wd.provinces), max(self.seg.provinces) + 1)
        ids = sorted(self.wd.provinces)
        self.assertEqual(ids, list(range(ids[0], ids[0] + len(ids))))
        colours = [p.colour for lay in (self.serp, self.seg, self.wd) for p in lay.provinces.values()]
        self.assertEqual(len(colours), len(set(colours)))

    def test_counts(self):
        self.assertFalse({c.area for c in self.wd.counties} & set(data.EXCLUDE_AREAS))
        surface = [c for c in self.wd.counties if c.type == "surface"]
        self.assertEqual(len(surface), 12)  # the Vale's 14 provinces less its two tunnels
        self.assertEqual(sorted(c.key for c in surface), sorted(data.SURFACE_TERRAIN))
        self.assertTrue(all(len(c.baronies) == data.SURFACE_BARONIES for c in surface))
        self.assertTrue(all(c.area in VALE_AREAS for c in surface))
        self.assertFalse({c.eu4_id for c in self.wd.counties} & set(data.EXISTING))
        for key in ("c_southern_entrance", "c_eastern_entrance"):
            self.assertIn(key, {c.key for c in self.wd.counties if c.type == "dwarven_road"})

    def test_existing_county_missing_stops(self):
        cfg = SimpleNamespace(**{k: getattr(data, k) for k in dir(data) if k.isupper()})
        cfg.EXISTING = {**data.EXISTING, 2864: "c_nowhere"}
        with self.assertRaisesRegex(GeneratorError, "c_nowhere"):
            sl.layout(ANBENNAR, EU4, self.ck3, cfg=cfg)

    def test_west_dwarovar_connected(self):
        pixels = set(self.wd.owner) | self.pixels_of(self.old)
        self.assertEqual(len(sl.components(pixels)), 1)

    def test_no_floor_touches_deepwoods_or_northern_pass(self):
        # every province a new floor or Vale pixel touches is new, Khugdihr's, rock, or an opening's or link's
        # target: nothing of the Deepwoods, the Northern Pass or any other land
        pm = self.ck3[0]
        earlier = {**self.serp.owner, **self.seg.owner}
        ok = ({data.SOURCE_PROVINCE} | self.old | set(self.wd.provinces)
              | {op.target for op in self.wd.openings} | {lk.target for lk in self.wd.links})
        touched = set()
        for x, y in self.wd.owner:
            for dx, dy in sl.N4:
                n = (x + dx, y + dy)
                touched.add(self.wd.owner.get(n) or earlier.get(n) or pm.ids[n[1] * pm.width + n[0]])
        self.assertEqual(touched - ok, set())

    def test_no_floor_near_earlier_regions(self):
        earlier = set(self.serp.owner) | set(self.seg.owner)
        m = data.WALL_MARGIN - 1
        near = [p for p in self.wd.owner if
                any((p[0] + dx, p[1] + dy) in earlier for dx in range(-m, m + 1) for dy in range(-m, m + 1))]
        self.assertEqual(near, [])

    def test_connections(self):
        # Dwarfhope's EU4 neighbour Fogwood (863) lies behind Glimmerfoe (2556) on the CK3 map: it opens onto Glimmerfoe
        openings = {(self.area_of[op.county], op.target) for op in self.wd.openings}
        self.assertEqual(openings, {("fallen_asra_area", 860), ("chainlink_mines_area", 2556),
                                    ("jorkad_junction_area", 3005)})
        # no carved tunnel into Segbandal or Serpentreach: Dwarovrod 24 -> 25 and Gorrod 2 -> 1 are crossings
        earlier = set(self.seg.provinces) | set(self.serp.provinces)
        self.assertEqual([lk for lk in self.wd.links if lk.target in earlier], [])
        # Dark Depths, Dwarfbreak and Orlazam open straight into the Vale; Amldihr through its two Entrance tunnels,
        # which EU4 puts in the Vale's areas
        caves = {self.area_of[m.county] for m in self.wd.mouths} - VALE_AREAS
        self.assertEqual(caves, {"dark_depths_area", "dwarfbreak_area", "orlazam_area"})
        entrances = {m.county for m in self.wd.mouths if self.area_of[m.county] in VALE_AREAS}
        self.assertEqual(entrances, {"c_southern_entrance", "c_eastern_entrance"})
        county_at = {p: self.wd.provinces[pid].county for p, pid in self.wd.owner.items()}
        for key in entrances:
            touched = {county_at.get((x + dx, y + dy)) for (x, y), k in county_at.items() if k == key
                       for dx, dy in sl.N4}
            self.assertIn("amldihr_area", {self.area_of.get(k) for k in touched}, key)
        surface = {self.wd.provinces[m.target].county for m in self.wd.mouths}
        self.assertTrue(all(self.area_of[k] in VALE_AREAS for k in surface))
        self.assertTrue(all(c.type == "surface" for c in self.wd.counties if c.key in surface))


@unittest.skipUnless(HAVE_GAME_DATA, "needs EU4 Anbennar and Anbennar CK3")
class MapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_serpentreach as bs
        cls.bs = bs
        cls.lays, _ = shared_trace.layouts()
        cls.files = bs.build_from_layout(ANBENNAR, cls.lays)

    def test_map_files_hold_three_regions(self):
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
            for pid in list(wd.provinces)[:3] + list(wd.provinces)[-3:]:
                self.assertEqual(len(re.findall(r"\bid=" + str(pid) + r"\n", text)), 1, (name, pid))

    def test_crossings(self):
        # Gorrod 2 (EU4 4103) reaches Serpentreach's Gorrod 1 (2981), Dwarovrod 24 (2884) Segbandal's Dwarovrod 25
        # (2885), each by one adjacencies.csv crossing through the rock; Anbennar's rows stay as they are
        serp, seg, wd = self.lays
        text = self.files[self.bs.ADJACENCIES]
        rows = [r.split(";") for r in text.decode("utf-8").splitlines()]
        for a, b, lay in ((4103, 2981, serp), (2884, 2885, seg)):
            ca = next(c for c in wd.counties if c.eu4_id == a)
            cb = next(c for c in lay.counties if c.eu4_id == b)
            ours = [r for r in rows if r[0].isdigit() and int(r[0]) in ca.baronies]
            self.assertEqual(len(ours), 1, a)
            self.assertIn(int(ours[0][1]), cb.baronies)
            self.assertEqual(ours[0][2:4], ["sea", str(max(wd.provinces) + 2)])  # West Dwarovar's range rock
            text = text.replace(";".join(ours[0]).encode() + b"\r\n", b"")
        self.assertEqual(text, (ANBENNAR / "map_data/adjacencies.csv").read_bytes())

    def test_map_files_current(self):
        stale = [rel for rel, content in self.files.items()
                 if not (self.bs.SUBMOD / rel).is_file() or (self.bs.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_serpentreach.py")


KHUGDIHR_TITLES = ("k_khugdihr", "d_khugdihr", "c_khugdihr", "c_khugscave", "c_outerkhugscave", "c_dwarovrod1")
PARKED = ("d_dwarovrod_1_3", "d_fallen_asra", "d_snotslair")


@unittest.skipUnless(HAVE_GAME_DATA, "needs EU4 Anbennar and Anbennar CK3")
class TitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_segbandal as bsb
        import build_west_dwarovar as bwd
        import eu4_import as eu4i
        cls.bsb, cls.bwd = bsb, bwd
        (_, _, cls.lay), _ = shared_trace.layouts()
        cls.files = bwd.build_from_layout(ANBENNAR, cls.lay, EU4)
        cls.titles = cls.files[bwd.TITLES].decode("utf-8-sig")
        cls.history = cls.files[bwd.TITLE_HISTORY].decode("utf-8-sig")
        cls.provinces = cls.files[bwd.PROVINCE_HISTORY].decode("utf-8-sig")
        cls.areas = eu4i.province_areas(EU4)
        cls.anbennar_titles = titles_text()

    def de_jure(self):
        """Every title's de jure parent after our titles and history apply over Anbennar's."""
        parents = self.bsb.title_parents(self.anbennar_titles)
        parents.update(self.bsb.title_parents(self.titles))
        for key, liege in re.findall(r"(?m)^(\w+) = \{\n\t1\.1\.1 = \{ de_jure_liege = (\w+) \}", self.history):
            parents[key] = liege
        return parents

    def duchy_of_area(self, area):
        return "d_" + sl.slug(self.lay.area_names[area])

    def test_every_title_has_a_full_chain_at_load(self):
        parents = self.bsb.title_parents(self.titles)
        tiers = "cdke"
        for key, parent in parents.items():
            if key.startswith("e_"):
                self.assertIsNone(parent, key)
            else:
                self.assertIsNotNone(parent, f"{key} has no parent in landed titles")
                self.assertEqual(tiers.index(parent[0]), tiers.index(key[0]) + 1, f"{key} under {parent}")
        self.assertEqual(parents[data.PARKING_KINGDOM], data.EMPIRE[0])
        self.assertEqual({k for k, p in parents.items() if p == data.PARKING_KINGDOM}, set(PARKED))
        self.assertFalse(set(parents) & set(self.bsb.title_parents(self.anbennar_titles)))

    def test_de_jure_matches_areas(self):
        parents = self.de_jure()
        for c in self.lay.counties:
            self.assertEqual(parents[c.key], self.duchy_of_area(c.area), c.key)
        for eu4_id, county in data.EXISTING.items():
            self.assertEqual(parents[county], self.duchy_of_area(self.areas[eu4_id]), county)
        for kkey, (_, kareas) in data.KINGDOMS.items():
            for area in kareas:
                self.assertEqual(parents[self.duchy_of_area(area)], kkey, area)
            self.assertEqual(parents[kkey], data.EMPIRE[0], kkey)
        self.assertEqual(parents["k_khugdihr"], "e_west_dwarovar")
        self.assertEqual({k for k, p in parents.items() if p == data.PARKING_KINGDOM}, set())  # parking ends empty
        self.assertNotRegex(self.history, rf"(?m)^{data.PARKING_KINGDOM} = ")

    def test_duchies_list_capital_first(self):
        for _, duchy, body in re.findall(r"(?ms)^(\t*)(d_\w+) = \{\n(.*?)^\1\}", self.titles):
            counties = re.findall(r"(?m)^\t*(c_\w+) = \{", body)
            self.assertEqual(counties[0], re.search(r"capital = (c_\w+)", body).group(1), duchy)
        for kkey, ckey in data.KINGDOM_CAPITALS.items():
            if kkey != "k_khugdihr":
                self.assertRegex(self.titles, rf"\n\t\td_\w+ = \{{\n\t\t\tcolor = \{{[^}}]*\}}\n\t\t\tcapital = {ckey}\n")

    def test_hold_duchies_named_like_their_kingdom(self):
        """Spec §3: each hold's duchy is named like its kingdom (EU4's area names differ: Orldhûm, The Railyard, ...)."""
        loc = self.files[self.bwd.LOC].decode("utf-8-sig")
        for kkey, (kname, kareas) in data.KINGDOMS.items():
            if kkey == "k_khugdihr":
                continue
            self.assertIn(f' {self.duchy_of_area(kareas[0])}:0 "{kname}"', loc, kkey)

    def test_holders(self):
        self.assertIn("k_amldihr = {\n\t860.1.1 = { holder = aov_wd_emperor_1 }", self.history)
        self.assertIn("d_amldihr = {\n\t860.1.1 = { holder = aov_wd_emperor_1 }", self.history)
        self.assertIn("e_west_dwarovar = {\n\t860.1.1 = { holder = aov_wd_emperor_1 }", self.history)
        for kkey, ckey in data.KINGDOM_CAPITALS.items():
            if kkey in ("k_khugdihr", "k_amldihr"):
                continue
            duchy = self.duchy_of_area(data.KINGDOMS[kkey][1][0])
            self.assertIn(f"{kkey} = {{\n\t860.1.1 = {{ holder = aov_wd_{duchy[2:]}_1 liege = e_west_dwarovar }}",
                          self.history)
        khugdihr = set(KHUGDIHR_TITLES) | set(PARKED)
        khugdihr |= {c.key for c in self.lay.counties if self.duchy_of_area(c.area) in PARKED}
        for key in khugdihr:
            block = re.search(rf"(?ms)^{key} = \{{\n.*?^\}}", self.history)
            if block:
                self.assertNotIn("holder", block.group(0), key)
        self.assertNotIn("aov_wd_dwarovrod_1_3", self.files[self.bwd.CHARACTERS].decode("utf-8-sig"))

    def test_khugdihr_untouched(self):
        anbennar = sl.county_provinces(self.anbennar_titles)
        for county in data.EXISTING.values():
            for pid in anbennar[county]:
                self.assertNotRegex(self.provinces, rf"(?m)^{pid} = \{{", county)
        parked = [c for c in self.lay.counties if self.duchy_of_area(c.area) in PARKED]
        self.assertTrue(parked)
        for c in parked:
            for pid in c.baronies:
                self.assertRegex(self.provinces, rf"(?m)^{pid} = \{{\t# .*\n\tculture = darkscale\n\treligion = nimrithani\n")
        for key in KHUGDIHR_TITLES:
            self.assertNotRegex(self.titles, rf"(?m)^\t*{key} = \{{", key)

    def test_khugdihr_holder_appears_stops(self):
        history = self.bsb._read_history(ANBENNAR) + "\nc_khugscave = {\n\t1000.1.1 = { holder = 42 }\n}\n"
        with self.assertRaisesRegex(GeneratorError, "c_khugscave"):
            self.bwd.check_khugdihr(self.anbennar_titles, history)
        self.bwd.check_khugdihr(self.anbennar_titles, self.bsb._read_history(ANBENNAR))
        extra = self.anbennar_titles.replace("\t\t\tc_khugscave = {", "\t\t\tc_newcave = {\n\t\t\t}\n\t\t\tc_khugscave = {", 1)
        with self.assertRaisesRegex(GeneratorError, "c_newcave"):
            self.bwd.check_khugdihr(extra, self.bsb._read_history(ANBENNAR))

    def test_vale_terrain_and_holdings(self):
        terrain = self.files[self.bwd.TERRAIN].decode("utf-8-sig")
        for c in self.lay.counties:
            want = data.SURFACE_TERRAIN[c.key] if c.type == "surface" else c.type
            for pid in c.baronies:
                self.assertIn(f"\n{pid}={want}\n", terrain + "\n")
            if c.type == "surface":
                for pid, holding in zip(c.baronies, data.SURFACE_HOLDINGS):
                    self.assertRegex(self.provinces, rf"(?m)^{pid} = \{{\t# .*\n\tculture = kronium_dwarvish\n"
                                                     rf"\treligion = ancestor_worship\n\tholding = {holding}\n")

    def test_every_county_and_character_has_its_kingdom_culture(self):
        want = {"k_khugdihr": "darkscale", "k_amldihr": "kronium_dwarvish", "k_haraz_orldhum": "platinum_dwarvish",
                "k_mithradhum": "mithril_dwarvish", "k_er_natvir": "dagrite_dwarvish",
                "k_verkal_kozenad": "opal_dwarvish", "k_hul_jorkad": "lead_dwarvish",
                "k_orlazam_az_dihr": "ramsteel_dwarvish", "k_dur_vazhatun": "sapphire_dwarvish"}
        self.assertEqual(data.KINGDOM_CULTURES, want)
        characters = self.files[self.bwd.CHARACTERS].decode("utf-8-sig")
        dynasties = self.files[self.bwd.DYNASTIES].decode("utf-8-sig")
        for text in (self.provinces, characters, dynasties):
            self.assertNotIn("silver_dwarvish", text)
        for kkey, (_, kareas) in data.KINGDOMS.items():
            for c in (c for c in self.lay.counties if c.area in kareas):
                for pid in c.baronies:
                    self.assertRegex(self.provinces, rf"(?m)^{pid} = \{{\t# .*\n\tculture = {want[kkey]}\n")
        self.assertRegex(characters, r'aov_wd_emperor_1 = \{[^}]*culture = "kronium_dwarvish"')
        self.assertRegex(characters, r'aov_wd_orlazam_1 = \{[^}]*culture = "ramsteel_dwarvish"')
        self.assertRegex(dynasties, r"aov_wd_dynasty_riftway = \{[^}]*culture = mithril_dwarvish")

    def test_eu4_dynasty_names_without_prefix(self):
        want = {"d_mithradhum": "Strongbellow", "d_riftway": "Goldbeard", "d_dwarovrod_7_9": "Goblinslayer",
                "d_the_railyard": "Ironhelm", "d_stunad_kozenad": "Forktongue", "d_zokkorna_caverns": "Ringbeard",
                "d_westnest": "Kezdori", "d_jorkad_junction": "Leadpipe", "d_orlazam": "Fourfoot",
                "d_vazhatun": "Melmarn"}
        self.assertEqual(data.DYNASTY_NAMES, want)
        dynasties = self.files[self.bwd.DYNASTIES].decode("utf-8-sig")
        loc = self.files[self.bwd.LOC].decode("utf-8-sig")
        for dkey, name in want.items():
            block = re.search(rf"(?ms)^aov_wd_dynasty_{dkey[2:]} = \{{.*?^\}}", dynasties).group(0)
            self.assertNotIn("prefix", block, dkey)
            self.assertIn(f' dynn_aov_wd_{dkey[2:]}:0 "{name}"', loc)
        self.assertEqual(dynasties.count('prefix = "dynnp_az"'), 35 - len(want))
        names = re.findall(r'(?m)^ dynn_aov_wd_\w+:0 "([^"]*)"', loc)
        self.assertEqual(len(names), len(set(names)))

    def test_every_new_key_has_loc(self):
        loc = self.files[self.bwd.LOC].decode("utf-8-sig")
        for key in re.findall(r"(?m)^\t*([ekdcb]_\w+) = \{", self.titles):
            self.assertRegex(loc, rf"(?m)^ {key}:0 \"")
        self.assertIn(' e_west_dwarovar:0 "West Dwarovar"', loc)
        self.assertIn(' d_dwarovrod_1_3:0 "Dwarovrod 1-3"', loc)
        self.assertNotIn(" k_khugdihr:0", loc)
        regions = self.files[self.bwd.REGIONS].decode("utf-8-sig")
        self.assertIn("world_west_dwarovar = {\n\tkingdoms = { " + " ".join(data.KINGDOMS) + " }", regions)

    def test_arms(self):
        from unittest import mock
        arms = self.files[self.bwd.ARMS].decode("utf-8-sig")
        for kkey, (tag, _, field) in data.KINGDOM_ARMS.items():
            hold = "d_khugdihr" if kkey == "k_khugdihr" else self.duchy_of_area(data.KINGDOMS[kkey][1][0])
            emblem = f"aov_{kkey[2:]}.dds"
            for key in (kkey, hold, data.KINGDOM_CAPITALS[kkey]):
                self.assertRegex(arms, rf'(?m)^{key} = \{{\n\tpattern = "pattern_solid.dds"\n\tcolor1 = rgb '
                                       rf'\{{ {" ".join(map(str, field))} \}}\n\ttextured_emblem = \{{\n'
                                       rf'\t\ttexture = "{emblem}"', key)
            self.assertTrue((self.bwd.SUBMOD / "gfx/coat_of_arms/textured_emblems" / emblem).is_file(), emblem)
        self.assertIn("aov_khugdihr.dds", arms)
        self.assertEqual(len(data.DUCHY_CHARGES), 30)
        for area, ((charge, _, _),) in data.DUCHY_CHARGES.items():
            self.assertRegex(arms, rf'(?m)^{self.duchy_of_area(area)} = \{{\n(\t.*\n)*?\t\ttexture = "{charge}"', area)
        duchies = set(re.findall(r"(?m)^(d_\w+) = \{", arms))
        self.assertEqual(len(duchies), 30 + 9)
        with mock.patch.object(self.bsb, "_scripted_arms", return_value={"d_khugdihr"}):
            with self.assertRaisesRegex(GeneratorError, "d_khugdihr"):
                self.bwd.build_from_layout(ANBENNAR, self.lay, EU4)
        with mock.patch.dict(data.DUCHY_CHARGES, {"azmak_area": (("ce_nowhere.dds", (0.5, 0.5), (0.6, 0.6)),)}):
            with self.assertRaisesRegex(GeneratorError, "ce_nowhere"):
                self.bwd.build_from_layout(ANBENNAR, self.lay, EU4)

    def test_outputs_current(self):
        stale = [rel for rel, content in self.files.items()
                 if not (self.bwd.SUBMOD / rel).is_file() or (self.bwd.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_west_dwarovar.py")


if __name__ == "__main__":
    unittest.main()
