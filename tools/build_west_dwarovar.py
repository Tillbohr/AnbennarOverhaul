"""Generate West Dwarovar's titles, history, people, terrain, region and localization: EU4 Anbennar's
west_dwarovar_region (without the Krakdhum pocket) and serpents_vale_region under one placeholder empire,
e_west_dwarovar, with Anbennar's k_khugdihr moved in.

The new provinces come from tools/build_serpentreach.py (`layouts`, which also draws them into the shared map files).
Every EU4 area becomes a duchy under its hold's kingdom (tools/data/west_dwarovar.py, KINGDOMS). Anbennar's Khugdihr
keeps its kobolds: no culture, faith, holder or province change, only history `de_jure_liege` moves at 1.1.1, so no
Anbennar file is overridden. Run after tools/build_serpentreach.py and tools/build_segbandal.py:

    python -I tools/build_west_dwarovar.py [--anbennar PATH] [--eu4 PATH]

Spec: docs/superpowers/specs/2026-11-03-west-dwarovar-design.md
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script's folder
from build_hud_override import GeneratorError  # noqa: E402
import build_segbandal as bsb  # noqa: E402
import build_serpentreach as bs  # noqa: E402
import eu4_import as eu4i  # noqa: E402
import serpentreach_layout as sl  # noqa: E402
from data import west_dwarovar as data  # noqa: E402

SUBMOD = bs.SUBMOD
ANBENNAR = bs.ANBENNAR
EU4 = bs.EU4

TITLES = "common/landed_titles/aov_west_dwarovar.txt"
PROVINCE_HISTORY = "history/provinces/aov_west_dwarovar.txt"
TITLE_HISTORY = "history/titles/aov_west_dwarovar.txt"
CHARACTERS = "history/characters/aov_west_dwarovar.txt"
DYNASTIES = "common/dynasties/aov_west_dwarovar_dynasties.txt"
TERRAIN = "common/province_terrain/aov_west_dwarovar_terrain.txt"
REGIONS = "map_data/geographical_regions/aov_west_dwarovar_regions.txt"
LOC = "localization/english/aov_west_dwarovar_l_english.yml"
DE_JURE_DATE = "1.1.1"


def header_lines() -> list:
    return bs.header_lines(data)


def _text(lines) -> bytes:
    return (bs.BOM + "\n".join(lines) + "\n").encode("utf-8")


def _blocks(text: str, key: str) -> list:
    """Every `key = { ... }` block of history text (comments stripped), outermost braces included."""
    body = bsb._strip_comments(text)
    out = []
    for m in re.finditer(rf"(?m)^\s*{re.escape(key)}\s*=\s*\{{", body):
        depth, i = 1, m.end()
        while depth and i < len(body):
            depth += {"{": 1, "}": -1}.get(body[i], 0)
            i += 1
        out.append(body[m.start():i])
    return out


def kingdom_titles(parents: dict, kingdom: str) -> set:
    """`kingdom` and every title nested under it (`parents` from title_parents)."""
    out = {kingdom}
    for key in parents:
        p = parents[key]
        while p is not None:
            if p == kingdom:
                out.add(key)
                break
            p = parents.get(p)
    return out


def check_khugdihr(titles_text: str, history_text: str) -> None:
    """Stop when Anbennar's kobold kingdoms (KOBOLD_KINGDOMS) gain a county EXISTING does not list, or any of their
    titles a holder: the build writes none of their history but the de jure moves, so it would silently keep or
    duplicate the change."""
    parents = bsb.title_parents(titles_text)
    for kingdom in data.KOBOLD_KINGDOMS:
        if kingdom not in parents:
            raise GeneratorError(f"Anbennar no longer has {kingdom}")
        titles = kingdom_titles(parents, kingdom)
        extra = sorted(k for k in titles if k.startswith("c_") and k not in data.EXISTING.values())
        if extra:
            raise GeneratorError(f"Anbennar's {kingdom} now holds {', '.join(extra)}; add them to EXISTING")
        held = sorted(k for k in titles if any(re.search(r"\bholder\s*=", b) for b in _blocks(history_text, k)))
        if held:
            raise GeneratorError(f"Anbennar now gives {', '.join(held)} a holder; decide who rules Khugdihr")


class WestDwarovar:
    """The realm (build_serpentreach.Realm with this region's data), its people (none in the kobold kingdoms) and the
    de jure moves of Anbennar's titles."""

    def __init__(self, lay: sl.Layout, titles_text: str, areas: dict, names: list):
        self.lay = lay
        self.realm = bs.Realm(lay, data)
        self.people = bs.People(self.realm, names, data)
        for dkey in list(self.people.lines):
            if self.realm.kingdom_of[dkey] in data.KOBOLD_KINGDOMS:
                del self.people.lines[dkey]
        surface = {c.key for c in lay.counties if c.type == "surface"}
        if set(data.SURFACE_TERRAIN) != surface:
            raise GeneratorError(f"SURFACE_TERRAIN must list exactly the surface counties: missing "
                                 f"{sorted(surface - set(data.SURFACE_TERRAIN))}, "
                                 f"extra {sorted(set(data.SURFACE_TERRAIN) - surface)}")
        parents = bsb.title_parents(titles_text)
        area_duchy = {area: dkey for dkey, area in self.realm.duchy_area.items()}
        for dkey in self.realm.existing_duchies:
            if dkey not in parents:
                raise GeneratorError(f"{dkey} (EU4 {self.realm.duchy_area[dkey]}) is not one of Anbennar's duchies")
        self.moves = {}  # Anbennar title or parked duchy -> its de jure parent from 1.1.1
        for kkey in self.realm.existing_kingdoms:
            if parents.get(kkey) != data.EMPIRE[0]:
                self.moves[kkey] = data.EMPIRE[0]
            for dkey in self.realm.kingdoms[kkey][1]:
                if dkey not in self.realm.existing_duchies or parents.get(dkey) != kkey:
                    self.moves[dkey] = kkey
        for eu4_id, county in sorted(data.EXISTING.items()):
            target = area_duchy[areas[eu4_id]]
            if parents.get(county) != target:
                self.moves[county] = target

    def province_lines(self) -> list:
        lines = []
        realm = self.realm
        for c in self.lay.counties:
            kingdom = realm.kingdom_of[realm.duchy_of[c.key]]
            culture, religion = data.KOBOLD_KINGDOMS.get(kingdom, (realm.culture_of(realm.duchy_of[c.key]),
                                                                   data.RELIGION))
            holdings = data.HOLDINGS[c.type]
            for i, (pid, name) in enumerate(zip(c.baronies, realm.barony_names(c.key))):
                holding = holdings[i] if i < len(holdings) else None
                lines += ["", f"{pid} = {{\t# {name}", f"\tculture = {culture}", f"\treligion = {religion}",
                          f"\tholding = {holding or 'none'}", "}"]
        return lines


def render_title_history(wd: WestDwarovar) -> bytes:
    """The rulers (build_serpentreach's: the emperor on Amldihr, each other kingdom's hold duke under him, the other
    dukes under their king), then the de jure moves: k_khugdihr into e_west_dwarovar, the parked duchies into
    k_khugdihr, Dwarovrod 1 into Dwarovrod 1-3."""
    text = bs.render_title_history(wd.realm, wd.people, data)
    lines = []
    for key, target in wd.moves.items():
        lines += ["", f"{key} = {{", f"\t{DE_JURE_DATE} = {{ de_jure_liege = {target} }}", "}"]
    return text + ("\n".join(lines) + "\n").encode("utf-8")


def render_province_history(wd: WestDwarovar) -> bytes:
    return _text(header_lines() + wd.province_lines())


def render_terrain(lay: sl.Layout) -> bytes:
    lines = header_lines() + [""]
    for c in lay.counties:
        kind = data.SURFACE_TERRAIN[c.key] if c.type == "surface" else c.type
        lines += [f"{pid}={kind}" for pid in c.baronies]
    return _text(lines)


def build_from_layout(anbennar: Path, lay: sl.Layout, eu4: Path = EU4) -> dict:
    """West Dwarovar's files from its layout (build_serpentreach.layouts(...)[2]); nothing is written here."""
    titles_text = bsb._read_titles(anbennar)
    check_khugdihr(titles_text, bsb._read_history(anbennar))
    wd = WestDwarovar(lay, titles_text, eu4i.province_areas(eu4), bs.male_names(anbennar))
    bs.check_new_keys(wd.realm.all_keys(), titles_text)
    return {
        TITLES: bs.render_titles(wd.realm, data),
        TITLE_HISTORY: render_title_history(wd),
        PROVINCE_HISTORY: render_province_history(wd),
        CHARACTERS: bs.render_characters(wd.people, data),
        DYNASTIES: bs.render_dynasties(wd.people, data),
        TERRAIN: render_terrain(lay),
        REGIONS: bs.render_regions(data, list(data.KINGDOMS), data.REGION_NAME),
        LOC: bs.render_loc(wd.realm, wd.people, data),
    }


def build_all(anbennar: Path = ANBENNAR, eu4: Path = EU4) -> dict:
    """Every output (rel path -> bytes); nothing is written here."""
    return build_from_layout(anbennar, bs.layouts(anbennar, eu4)[2], eu4)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anbennar", type=Path, default=ANBENNAR)
    parser.add_argument("--eu4", type=Path, default=EU4)
    args = parser.parse_args()
    try:
        files = build_all(args.anbennar, args.eu4)
    except (GeneratorError, OSError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for rel, content in files.items():
        target = SUBMOD / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    print(f"wrote {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
