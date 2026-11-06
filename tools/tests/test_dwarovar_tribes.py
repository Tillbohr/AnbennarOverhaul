"""The tribe placement data against the traced regions and the province map."""

import re
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
import dwarven_mountains as dm  # noqa: E402
import eu4_import as ei  # noqa: E402
import shared_trace  # noqa: E402
from data import dwarovar_tribes as dt  # noqa: E402
from data import segbandal, serpentreach, west_dwarovar  # noqa: E402

SUBMOD = Path(__file__).resolve().parents[2]
ANBENNAR = SUBMOD.parent / "anbennar-ck3-dev-master"
SPEC_COUNTS = {
    "masked_butcher": 14, "moltenbrand": 14, "diamond_mines_orcs": 6, "still_caverns_orcs": 4, "amldihr_orcs": 18,
    "orldhum_orcs": 17, "mithradhum_orcs": 14, "kozenad_orcs": 13, "orlazam_orcs": 13, "wretched_skull": 11,
    "railyard_orcs": 11, "skewered_drake": 9, "deep_ones_orcs": 4,
    "skomdihr_goblins": 7, "burnt_skin": 6, "shazstundihr_squatters": 4, "thieving_arrow": 4, "shroomfissure": 3,
    "vazhatun_goblins": 6, "spiderwretch": 6, "goblins_bypass": 4, "railskulker": 3, "truedagger": 3, "snotfinger": 3,
    "trolltamer": 7, "greedy_grin": 6, "xazor_goblins": 5,
}
TAGS = {"masked_butcher": "H81", "thieving_arrow": "H87", "burnt_skin": "M05", "wretched_skull": "H86",
        "spiderwretch": "H90", "railskulker": "H75", "truedagger": "H85", "snotfinger": "H89", "skewered_drake": "H73",
        "greedy_grin": "H82"}
KOBOLD_AREAS = {"khugdihr_area", "dwarovrod_1_3_area", "fallen_asra_area"}
AREA_OF = ei.province_areas()


def all_counties() -> dict:
    """EU4 id -> (region, county key, CK3 province ids): every carved county and every one of Anbennar's."""
    (serp, seg, wd), _ck3 = shared_trace.layouts()
    out = {}
    for region, lay, cfg in (("serpentreach", serp, serpentreach), ("segbandal", seg, segbandal),
                             ("west", wd, west_dwarovar)):
        for c in lay.counties:
            out[c.eu4_id] = (region, c.key, list(c.baronies))
        for eu4_id, key in cfg.EXISTING.items():
            out[eu4_id] = (region, key, None)
    text = "\n".join(p.read_text(encoding="utf-8-sig", errors="replace")
                     for p in (ANBENNAR / "common/landed_titles").glob("*.txt"))
    text = re.sub(r"#.*", "", text)
    for eu4_id, (region, key, provinces) in list(out.items()):
        if provinces is None:
            m = re.search(rf"\b{key}\s*=\s*\{{", text)
            depth, j = 1, m.end()
            while depth:
                depth += {"{": 1, "}": -1}.get(text[j], 0)
                j += 1
            out[eu4_id] = (region, key, [int(x) for x in re.findall(r"province\s*=\s*(\d+)", text[m.end():j])])
    return out


def county_adjacency(counties: dict) -> dict:
    """EU4 id -> neighbouring EU4 ids, from the overhaul's province map and West Dwarovar's two crossings."""
    pmap = dm.load_province_map((SUBMOD / "map_data/provinces.png").read_bytes(),
                                (SUBMOD / "map_data/definition.csv").read_text(encoding="utf-8-sig", errors="replace"))
    county_of = {p: e for e, (_r, _k, provinces) in counties.items() for p in provinces}
    adj = defaultdict(set)
    width, ids = pmap.width, pmap.ids
    for y in range(pmap.height):
        row = y * width
        for x in range(width):
            a = county_of.get(ids[row + x])
            if a is None:
                continue
            for b in ((county_of.get(ids[row + x + 1]) if x + 1 < width else None),
                      (county_of.get(ids[row + width + x]) if y + 1 < pmap.height else None)):
                if b is not None and b != a:
                    adj[a].add(b)
                    adj[b].add(a)
    for a, b in west_dwarovar.CROSSINGS:
        adj[a].add(b)
        adj[b].add(a)
    return adj


def pieces(nodes, adj) -> list:
    nodes, out = set(nodes), []
    while nodes:
        stack, comp = [nodes.pop()], set()
        while stack:
            n = stack.pop()
            comp.add(n)
            for m in adj[n] & nodes:
                nodes.discard(m)
                stack.append(m)
        out.append(comp)
    return out


class PlacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.counties = all_counties()
        cls.owner = {e: dt.tribe_of(e, AREA_OF.get(e)) for e in cls.counties}
        cls.adj = county_adjacency(cls.counties)

    def test_twenty_seven_tribes(self):
        self.assertEqual(set(dt.TRIBES), set(SPEC_COUNTS))

    def test_totals(self):
        races = Counter(t.race for t in self.owner.values() if t)
        self.assertEqual(races, {"orc": 148, "goblin": 67})

    def test_region_totals(self):
        found = Counter((self.counties[e][0], t.race) for e, t in self.owner.items() if t)
        self.assertEqual(found, {("serpentreach", "orc"): 38, ("serpentreach", "goblin"): 24,
                                 ("west", "orc"): 97, ("west", "goblin"): 25,
                                 ("segbandal", "orc"): 13, ("segbandal", "goblin"): 18})

    def test_tribe_counts(self):
        found = Counter(t.name for t in self.owner.values() if t)
        self.assertEqual({k: found[t.name] for k, t in dt.TRIBES.items()}, SPEC_COUNTS)

    def test_tags(self):
        self.assertEqual({k: t.tag for k, t in dt.TRIBES.items() if t.tag}, TAGS)

    def test_every_county_at_most_once(self):
        seen = Counter()
        for tribe in dt.TRIBES.values():
            for e, _county in self.counties.items():
                if (AREA_OF.get(e) in tribe.areas or e in tribe.extra) and e not in tribe.removed:
                    seen[e] += 1
        self.assertEqual([e for e, n in seen.items() if n > 1], [])
        dwarves = [e for e, t in self.owner.items() if t is None and AREA_OF.get(e) not in KOBOLD_AREAS]
        kobolds = [e for e, t in self.owner.items() if t is None and AREA_OF.get(e) in KOBOLD_AREAS]
        self.assertEqual((len(dwarves), len(kobolds), len(seen)), (31, 10, 215))
        self.assertEqual(len(self.counties), 256)

    def test_dwarf_realms_cover_the_rest(self):
        kept = {e for e, t in self.owner.items() if t is None and AREA_OF.get(e) not in KOBOLD_AREAS}
        listed = {e for e in self.counties
                  if any(AREA_OF.get(e) in areas for areas in dt.DWARF_REALMS.values())} | {dt.ARG_ORDSTUN_HOLD}
        self.assertEqual(kept, listed)
        self.assertEqual(Counter(k for e in kept for k, areas in dt.DWARF_REALMS.items() if AREA_OF.get(e) in areas),
                         {"k_ovdal_lodhum": 4, "k_hehodovar": 6, "k_seghdihr": 9, "k_verkal_gulan": 3,
                          "k_gor_ozumbrog": 8})

    def test_each_tribe_is_one_piece(self):
        members = defaultdict(list)
        for e, t in self.owner.items():
            if t:
                members[t.name].append(e)
        split = {name: len(pieces(cs, self.adj)) for name, cs in members.items() if len(pieces(cs, self.adj)) > 1}
        self.assertEqual(split, {})

    def test_segbandal_holds_connected(self):
        holds = {4124: "Seghdihr", 4078: "Hehodovar", 2914: "Verkal Gulan", 4218: "Gor Ozumbrog"}
        segbandal_dwarves = [e for e, t in self.owner.items() if t is None and self.counties[e][0] == "segbandal"]
        together = next(c for c in pieces(segbandal_dwarves, self.adj) if 4124 in c)
        self.assertEqual({e for e in holds if e in together}, set(holds))

    def test_no_tribe_on_anbennars_counties(self):
        taken = [e for e in list(segbandal.EXISTING) + list(west_dwarovar.EXISTING) if self.owner[e] is not None]
        self.assertEqual(taken, [])

    def test_seat_inside_tribe(self):
        for key, tribe in dt.TRIBES.items():
            self.assertIs(dt.tribe_of(tribe.seat, AREA_OF.get(tribe.seat)), tribe, key)

    def test_unknown_area_stops(self):  # a test failure names any area EU4 does not have
        known = set(AREA_OF.values())
        for key, tribe in dt.TRIBES.items():
            self.assertEqual([a for a in tribe.areas if a not in known], [], key)
        for key, areas in dt.DWARF_REALMS.items():
            self.assertEqual([a for a in areas if a not in known], [], key)

    def test_arg_ordstun_hold_stays_dwarven(self):
        self.assertIsNone(dt.tribe_of(4093, "arg_ordstun_area"))
        self.assertEqual(dt.tribe_of(2947, AREA_OF[2947]).name, dt.TRIBES["diamond_mines_orcs"].name)

    def test_unknown_county_has_no_tribe(self):
        self.assertIsNone(dt.tribe_of(999999, "no_such_area"))


class ValueTests(unittest.TestCase):
    def test_races(self):
        self.assertEqual({t.race for t in dt.TRIBES.values()}, {"orc", "goblin"})

    def test_starting_values(self):
        self.assertEqual(dt.POOL, {"orc": {"duchy": 40, "kingdom": 20, "empire": 6},
                                   "goblin": {"duchy": 40, "kingdom": 15, "empire": 4}})
        self.assertEqual(dt.FORM, {"duchy": (3, 250), "kingdom": (15, 500), "empire": (40, 1000)})
        self.assertEqual((dt.RAISE_PRESTIGE, dt.REFUSAL_OPINION, dt.CHALLENGE_COOLDOWN_YEARS), (200, -50, 5))
        self.assertEqual(dt.CULTURE, {"orc": "black_orc", "goblin": "cave_goblin"})
        self.assertEqual(dt.FAITH, {"orc": "old_dookan", "goblin": "goblinic_shamanism"})


if __name__ == "__main__":
    unittest.main()
