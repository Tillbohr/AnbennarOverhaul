import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import serpentreach_layout as sl  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import west_dwarovar as data  # noqa: E402

EU4 = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355")
ANBENNAR = Path(__file__).resolve().parents[2].parent / "anbennar-ck3-dev-master"
HAVE_GAME_DATA = EU4.is_dir() and ANBENNAR.is_dir()
VALE_AREAS = set(data.SURFACE_AREAS)

_CACHE = {}


def titles_text():
    return "\n".join(p.read_text(encoding="utf-8-sig", errors="replace")
                     for p in sorted((ANBENNAR / "common/landed_titles").glob("*.txt")))


def layouts():
    """(Serpentreach's, Segbandal's, West Dwarovar's) layouts and Anbennar's map, traced once for the whole module."""
    if "lays" not in _CACHE:
        import build_serpentreach as bs
        ck3 = sl.load_ck3(ANBENNAR)
        _CACHE["ck3"] = ck3
        _CACHE["lays"] = bs.layouts(ANBENNAR, EU4, ck3)
    return _CACHE["lays"], _CACHE["ck3"]


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
        (cls.serp, cls.seg, cls.wd), cls.ck3 = layouts()
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
        # every province a new floor or Vale pixel touches is new, Khugdihr's, rock, or an opening's or tunnel's
        # target: nothing of the Deepwoods, the Northern Pass or any other land
        pm = self.ck3[0]
        earlier = {**self.serp.owner, **self.seg.owner}
        ok = ({data.SOURCE_PROVINCE} | set(data.LINK_CUT_THROUGH) | self.old | set(self.wd.provinces)
              | {op.target for op in self.wd.openings} | {lk.target for lk in self.wd.links})
        touched = set()
        for x, y in self.wd.owner:
            for dx, dy in sl.N4:
                n = (x + dx, y + dy)
                touched.add(self.wd.owner.get(n) or earlier.get(n) or pm.ids[n[1] * pm.width + n[0]])
        self.assertEqual(touched - ok, set())

    def test_no_floor_near_earlier_regions(self):
        link = {p for lk in self.wd.links if lk.target in self.seg.provinces for p in lk.pixels}
        earlier = set(self.serp.owner) | set(self.seg.owner)
        m = data.WALL_MARGIN - 1
        near = [p for p in self.wd.owner if p not in link and
                any((p[0] + dx, p[1] + dy) in earlier for dx in range(-m, m + 1) for dy in range(-m, m + 1))]
        self.assertEqual(near, [])

    def test_connections(self):
        # Dwarfhope's EU4 neighbour Fogwood (863) lies behind Glimmerfoe (2556) on the CK3 map: it opens onto Glimmerfoe
        openings = {(self.area_of[op.county], op.target) for op in self.wd.openings}
        self.assertEqual(openings, {("fallen_asra_area", 860), ("chainlink_mines_area", 2556),
                                    ("jorkad_junction_area", 3005)})
        dwarovrod_25 = {pid for c in self.seg.counties if c.eu4_id == 2885 for pid in c.baronies}
        tunnels = [lk for lk in self.wd.links if lk.target in dwarovrod_25]
        self.assertEqual(len(tunnels), 1)
        self.assertEqual(self.area_of[tunnels[0].county], "dwarovrod_21_24_area")
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
        cls.lays, _ = layouts()
        cls.files = bs.build_from_layout(ANBENNAR, cls.lays)

    def test_map_files_hold_three_regions(self):
        serp, seg, wd = self.lays
        rows = self.files["map_data/definition.csv"].decode("utf-8", errors="replace").splitlines()
        anbennar = (ANBENNAR / "map_data/definition.csv").read_bytes().decode("utf-8", errors="replace").splitlines()
        new = [int(r.split(";")[0]) for r in rows[len(anbennar):]]
        self.assertEqual(new, sorted(serp.provinces) + sorted(seg.provinces) + sorted(wd.provinces))
        colours = [tuple(r.split(";")[1:4]) for r in rows if r[:1].isdigit() and r.split(";")[0] != "0"]
        self.assertEqual(len(colours), len(set(colours)))
        for name in self.bs.LOCATOR_FILES:
            text = self.files[f"{self.bs.LOCATOR_DIR}/{name}.txt"].decode("utf-8")
            for pid in list(wd.provinces)[:3] + list(wd.provinces)[-3:]:
                self.assertEqual(len(re.findall(r"\bid=" + str(pid) + r"\n", text)), 1, (name, pid))

    def test_map_files_current(self):
        stale = [rel for rel, content in self.files.items()
                 if not (self.bs.SUBMOD / rel).is_file() or (self.bs.SUBMOD / rel).read_bytes() != content]
        self.assertEqual(stale, [], "stale: rerun python -I tools/build_serpentreach.py")


if __name__ == "__main__":
    unittest.main()
