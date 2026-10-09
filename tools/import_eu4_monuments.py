"""Import EU4 Anbennar great projects (monuments) as CK3 special building data.

    python -I tools/import_eu4_monuments.py --region cannor [--anbennar-ck3 PATH]

Reads the EU4 projects (tools/eu4_monuments.py), translates them with tools/data/monuments/translation.py,
places each on a CK3 barony and writes tools/data/monuments/<region>.py. Fields in
tools/data/monuments/<region>_hand.py replace the imported ones and survive every re-import.
Prints the open items (unmatched or unresolved placements, open gates, untranslated keys); exits 1 while
any monument has no barony.
"""

import argparse
import copy
import importlib
import pprint
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script's folder
import eu4_monuments as em  # noqa: E402
from data.monuments import translation as tr  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DEFAULT_ANBENNAR_CK3 = REPO.parent / "anbennar-ck3-dev-master"
START_YEAR = 1022  # Anbennar CK3 bookmark; monuments dated 1022 or later are not built yet
CANAL = "canal: no CK3 canal mechanic"
EXTRA_NAMES = {"imperial_palace_anbenncost": "Castle Dameris"}


def _chain(anbennar_first, key, tier2_anbennar=None):
    """Level keys: Anbennar's building(s) first, then the overhaul's `aov_monument_<key>_NN` for the rest."""
    levels = [anbennar_first, tier2_anbennar or f"aov_monument_{key}_02", f"aov_monument_{key}_03"]
    return levels


CHAINS = {
    # Castanorian citadels: the rebuilt `_02` where Anbennar has a ruins stage, else `_01`.
    **{key: _chain(f"castanorian_citadel_{key}_02", key) for key in ("bal_mire", "bal_ouord", "bal_vroren")},
    **{key: _chain(f"castanorian_citadel_{key}_01", key) for key in ("bal_dostan", "bal_hyl", "bal_vertesk")},
    "the_north_citadel": _chain("castanorian_citadel_north_citadel_01", "the_north_citadel"),
    "the_south_citadel": _chain("castanorian_citadel_south_citadel_01", "the_south_citadel"),
    **{key: _chain(f"calasandur_castle_{key}_01", key) for key in ("aelcandar", "escandar", "calascandar")},
    "bladeskeep_monument": _chain("castle_bladeskeep_02", "bladeskeep_monument"),
    "the_lake_palace": ["lake_palace_01", "lake_palace_02", "aov_monument_the_lake_palace_03"],
    "the_necropolis": _chain("holy_site_the_necropolis_01", "the_necropolis"),
    "damish_temple_temple_of_the_highest_moon": _chain(
        "temple_highest_moon_01", "damish_temple_temple_of_the_highest_moon"),
    "lorenans_rest": _chain("lorenans_rest_01", "lorenans_rest"),
    "imperial_palace_anbenncost": ["castle_dameris_01", "castle_dameris_02", "castle_dameris_03"],
}

# Monuments placed in a named county, in this order (Castle Dameris takes Anbenncost's capital barony first).
COUNTY_OVERRIDES = {
    "imperial_palace_anbenncost": "c_anbenncost",
    "palace_of_unity": "c_anbenncost",
    "kobildzan_kobildzex_guild_of_trapsmiths": "c_soxun_kobildzex",
    "the_dragonhoard": "c_soxun_kobildzex",
}

CATEGORIES = [
    ("fortress", r"citadel|(?:^|_)bal_|castle|bastion|keep"),
    ("temple", r"temple|shrine"),
    ("academy", r"academy|institute|school|university"),
    ("library", r"library|archives"),
    ("port", r"port|harbou?r|dockyard"),
    ("market", r"exchange|market"),
    ("guild", r"guild"),
    ("foundry", r"foundry|armory|forge"),
    ("mine", r"mine"),
    ("tomb", r"tomb|grave|necropolis|memorial"),
    ("palace", r"palace"),
    ("theatre", r"theatre"),
    ("lighthouse", r"lighthouse"),
    ("bath", r"baths"),
]


# --- Small helpers -----------------------------------------------------------------------------------------------

def normalise(name):
    folded = unicodedata.normalize("NFKD", name.lower())
    return "".join(ch for ch in folded if ch.isalpha() and not unicodedata.combining(ch))


def match_title(name, titles):
    return titles.get(normalise(name))


def start_level(starting_tier, year):
    return 1 if starting_tier >= 1 and year < START_YEAR else 0


def default_levels(key):
    return [f"aov_monument_{key}_{n:02d}" for n in (1, 2, 3)]


def guess_category(key, name):
    text = f"{key} {name}".lower()
    for category, pattern in CATEGORIES:
        if re.search(pattern, text):
            return category
    return "monument"


def to_integer(value):
    """Round half away from zero; a nonzero value never becomes 0."""
    if value == 0:
        return 0
    rounded = max(1, int(abs(value) + 0.5))
    return rounded if value > 0 else -rounded


def family(building):
    return re.sub(r"_\d+$", "", building)


def _read(path):
    return path.read_bytes().decode("utf-8-sig", errors="replace")


# --- Anbennar CK3 titles and history -----------------------------------------------------------------------------

_TITLE_START = re.compile(r"^\s*([ekdcb]_[A-Za-z0-9_]+)\s*=\s*\{")
_PROVINCE = re.compile(r"\bprovince\s*=\s*(\d+)")
_TITLE_LOC = re.compile(r'^\s*([cb]_[A-Za-z0-9_]+):\d*\s*"(.*)"')


def ck3_titles(anbennar_ck3):
    """-> (normalised name -> title key, barony -> province, county -> baronies in file order, county -> capital).

    A county wins over a barony of the same name. The capital is the county's first barony (Anbennar sets no
    `capital = b_...`)."""
    anbennar_ck3 = Path(anbennar_ck3)
    provinces, county_baronies = {}, {}
    for path in sorted((anbennar_ck3 / "common" / "landed_titles").glob("*.txt")):
        stack, depth = [], 0
        for line in _read(path).split("\n"):
            code = line.split("#", 1)[0]
            m = _TITLE_START.match(code)
            if m:
                stack.append((m.group(1), depth))
                key = m.group(1)
                if key.startswith("b_"):
                    county = next((k for k, _ in reversed(stack) if k.startswith("c_")), None)
                    if county:
                        baronies = county_baronies.setdefault(county, [])
                        if key not in baronies:
                            baronies.append(key)
                elif key.startswith("c_"):
                    county_baronies.setdefault(key, [])
            if stack and stack[-1][0].startswith("b_"):
                p = _PROVINCE.search(code)
                if p:
                    provinces.setdefault(stack[-1][0], int(p.group(1)))
            depth += code.count("{") - code.count("}")
            while stack and depth <= stack[-1][1]:
                stack.pop()
    loc = {}
    for path in sorted((anbennar_ck3 / "localization" / "english").glob("*titles*_l_english.yml")):
        if "cultural" in path.name:
            continue
        for line in _read(path).split("\n"):
            m = _TITLE_LOC.match(line)
            if m:
                loc.setdefault(m.group(1), m.group(2))
    names = {}
    for key in county_baronies:  # counties first, then baronies
        if key in loc:
            names.setdefault(normalise(loc[key]), key)
    for key in provinces:
        if key in loc:
            names.setdefault(normalise(loc[key]), key)
    capitals = {county: baronies[0] for county, baronies in county_baronies.items() if baronies}
    return names, provinces, county_baronies, capitals


_PROVINCE_START = re.compile(r"^(\d+)\s*=\s*\{")
_SPECIAL = re.compile(r"\bspecial_building(?:_slot)?\s*=\s*([A-Za-z0-9_]+)")


def anbennar_slots(anbennar_ck3):
    """province id -> special building key (or slot) in Anbennar's province history, dated blocks included."""
    slots = {}
    for path in sorted((Path(anbennar_ck3) / "history" / "provinces").glob("*.txt")):
        province, depth = None, 0
        for line in _read(path).split("\n"):
            code = line.split("#", 1)[0]
            if depth == 0:
                m = _PROVINCE_START.match(code)
                if m:
                    province = int(m.group(1))
            elif province is not None:
                s = _SPECIAL.search(code)
                if s:
                    slots[province] = s.group(1)
            depth += code.count("{") - code.count("}")
            if depth <= 0:
                depth, province = 0, None
    return slots


# --- Placement ---------------------------------------------------------------------------------------------------

def place(monuments, titles, slots=None):
    """Fill `barony` and `province` of every monument without a barony; return the open items as report lines.

    Order: chains (Anbennar's barony of the tier-1 building), then COUNTY_OVERRIDES, then the rest by key. A
    monument's `place` is the name of its EU4 start province; the CK3 title with that name (a county first)
    gives its barony. A shared county gives its next free barony, skipping provinces with an Anbennar slot."""
    names, province_of, county_baronies, capitals = titles
    slots = slots or {}
    report = []
    barony_of_province = {p: b for b, p in province_of.items()}
    taken = {m["barony"] for m in monuments if m.get("barony")}
    for m in monuments:
        if m.get("barony"):
            m["province"] = province_of.get(m["barony"], m.get("province"))

    def free_baronies(county):
        ordered = [capitals[county]] if county in capitals else []
        ordered += [b for b in county_baronies.get(county, []) if b not in ordered]
        return [b for b in ordered if b not in taken and province_of.get(b) not in slots]

    def take(m, barony):
        taken.add(barony)
        m["barony"], m["province"] = barony, province_of.get(barony)

    def take_from_county(m, county):
        free = free_baronies(county)
        if free:
            take(m, free[0])
        else:
            report.append(f"{m['eu4_key']}: county {county} has no free barony")

    def priority(m):
        key = m["eu4_key"]
        if key in CHAINS:
            return (0, key)
        if key in COUNTY_OVERRIDES:
            return (1, list(COUNTY_OVERRIDES).index(key))
        return (2, key)

    for m in sorted((m for m in monuments if not m.get("barony")), key=priority):
        key = m["eu4_key"]
        if key in CHAINS:
            wanted = family(CHAINS[key][0])
            provinces = sorted(p for p, building in slots.items() if family(building) == wanted)
            barony = barony_of_province.get(provinces[0]) if provinces else None
            if barony and barony not in taken:
                take(m, barony)
                if len(provinces) > 1:
                    report.append(f"{key}: Anbennar places {wanted} in {len(provinces)} provinces; took {provinces[0]}")
                continue
            if key not in COUNTY_OVERRIDES:
                report.append(f"{key}: Anbennar history has no {wanted} building to take the barony from")
        if key in COUNTY_OVERRIDES:
            take_from_county(m, COUNTY_OVERRIDES[key])
            continue
        title = match_title(m.get("place") or "", names)
        if title is None:
            report.append(f"{key}: no CK3 title named {m.get('place')!r}")
        elif title.startswith("b_"):
            if title not in taken and province_of.get(title) not in slots:
                take(m, title)
            else:
                report.append(f"{key}: barony {title} ({m.get('place')}) is not free")
        else:
            take_from_county(m, title)
    return report


# --- Translation -------------------------------------------------------------------------------------------------

def _statements(text):
    """`key = value` / `key = { ... }` statements at the top level of a script snippet."""
    statements, pos = [], 0
    for m in re.finditer(r"[A-Za-z0-9_.:]+\s*=\s*", text):
        if m.start() < pos:
            continue
        rest = text[m.end():]
        if rest[:1] == "{":
            end = em._balanced(text, m.end())
        else:
            words = rest.split()
            end = m.end() + (len(words[0]) if words else 0)
        statements.append(text[m.start():end])
        pos = end
    return statements


_SCOPES = {"owner", "hidden_effect", "if", "else_if", "else"}


def _leaves(text, condition=""):
    """(effect statement, condition) pairs of a snippet. Scope blocks (owner, hidden_effect) and if/else blocks are
    opened up; ONE_OFF texts are written in the monument's province scope and name the holder themselves, so the
    wrapper scope is not needed. The condition is "" for an unconditional effect, else the text of the enclosing
    non-empty `limit`s (an `else`/`else_if` is always conditional)."""
    leaves = []
    for statement in _statements(text):
        key = re.match(r"[A-Za-z0-9_.:]+", statement).group(0)
        brace = statement.find("{")
        if key in _SCOPES and brace != -1:
            body = statement[brace + 1:statement.rfind("}")]
            inner = condition
            if key in ("if", "else_if", "else"):
                limits = [_short(st[st.find("{") + 1:st.rfind("}")]) for st in _statements(body)
                          if st.startswith("limit") and "{" in st]
                limit = " ".join(l for l in limits if l)
                if limit or key != "if":
                    inner = "; ".join(c for c in (condition, f"{key} {limit}".strip()) if c)
            leaves += _leaves(body, inner)
        elif key != "limit":
            leaves.append((statement, condition))
    return leaves


def _short(text):
    return re.sub(r"\s+", " ", text).strip()


def _number(value):
    value = round(value, 6)
    return int(value) if value == int(value) else value


def translate_tier(tier):
    blocks = {"province_modifier": {}, "county_modifier": {}, "character_modifier": {}}
    dropped = []
    sources = (
        (tier.province, lambda row: "province_modifier" if row.scope == tr.P else "county_modifier"),
        (tier.area, lambda row: "county_modifier"),
        (tier.country, lambda row: "character_modifier"),
    )
    for modifiers, block_of in sources:
        for key, value in modifiers.items():
            row = tr.MODIFIERS.get(key)
            if row is None:
                dropped.append(f"{key}: not in the translation table")
            elif isinstance(row, tr.Drop):
                dropped.append(f"{key}: {row.reason}")
            else:
                block = blocks[block_of(row)]
                block[row.ck3] = block.get(row.ck3, 0) + value * row.mult
    for name, block in blocks.items():
        result = {}
        for key, value in block.items():
            value = to_integer(value) if key in tr.INTEGER else _number(value)
            if value == 0:
                dropped.append(f"{key}: sums to 0")
            else:
                result[key] = value
        blocks[name] = result
    effects = []
    for statement, condition in _leaves(tier.on_upgraded):
        effect = None
        for pattern, candidate in (() if condition else tr.ONE_OFF):
            if re.search(pattern, statement):
                effect = candidate
                break
        if effect:
            effects.append(effect)
        elif condition:
            dropped.append(f"on_upgraded: {condition}: {_short(statement)}")
        else:
            dropped.append(f"on_upgraded: {_short(statement)}")
    return {
        **blocks,
        "on_complete": "\n".join(effects),
        "cost": int(round(tier.cost_factor * tr.COST)),
        "days": int(tier.months * tr.DAYS_PER_MONTH),
        "dropped": dropped,
    }


def translate_gate(body, loc):
    """-> (CK3 gate trigger text or "", comma-separated EU4 names of the mapped atoms, notes)."""
    triggers, names, notes = [], [], []
    for atom in em.gate_atoms(body):
        if atom not in tr.CULTURES:
            notes.append(f"gate atom {atom} not in the translation table")
        elif tr.CULTURES[atom] is None:
            notes.append(f"gate atom {atom} ignored (no CK3 equivalent)")
        elif tr.CULTURES[atom] not in triggers:
            triggers.append(tr.CULTURES[atom])
            value = atom.split(":", 1)[1]
            names.append(loc.get(value) or value)
    if not triggers:
        gate = ""
    elif len(triggers) == 1:
        gate = triggers[0]
    else:
        gate = "OR = { " + " ".join(triggers) + " }"
    return gate, ", ".join(names), notes


def merge(monument, hand):
    """The imported monument with its HAND[eu4_key] fields laid over it. `tiers` merges key by key (None removes
    a key); every other field is replaced."""
    out = copy.deepcopy(monument)
    for field, value in hand.get(monument["eu4_key"], {}).items():
        if field != "tiers":
            out[field] = copy.deepcopy(value)
            continue
        for tier, patch in zip(out["tiers"], value):
            for block, content in patch.items():
                if isinstance(content, dict) and isinstance(tier.get(block), dict):
                    for key, number in content.items():
                        if number is None:
                            tier[block].pop(key, None)
                        else:
                            tier[block][key] = number
                else:
                    tier[block] = copy.deepcopy(content)
    return out


# --- Run ---------------------------------------------------------------------------------------------------------

def _clean(text):
    return re.sub(r"§.", "", text).strip()


def build(project, place_name, loc, art):
    name = EXTRA_NAMES.get(project.key) or _clean(loc.get(project.key, project.key.replace("_", " ").title()))
    gate, gate_desc, notes = translate_gate(project.gate, loc)
    if project.mission:
        notes.append("mission-spawned in EU4 (start province read from a commented start)")
    return {
        "eu4_key": project.key,
        "source": project.source,
        "name": name,
        "desc": _clean(loc.get(f"{project.key}_desc", "")),
        "levels": list(CHAINS.get(project.key) or default_levels(project.key)),
        "barony": None,
        "province": None,
        "start_level": start_level(project.starting_tier, project.year),
        "category": guess_category(project.key, name),
        "gate": gate,
        "gate_desc": gate_desc,
        "tiers": [translate_tier(t) for t in project.tiers],
        "art": art,
        "notes": notes,
        "place": place_name,
    }


def load_hand(region):
    try:
        return importlib.import_module(f"data.monuments.{region}_hand").HAND
    except ModuleNotFoundError:
        return {}


def run(region, anbennar_ck3=None, roots=None, hand=None):
    if region != "cannor":
        raise ValueError(f"unknown region {region!r}")
    anbennar_ck3 = Path(anbennar_ck3 or DEFAULT_ANBENNAR_CK3)
    roots = roots or em.EU4_ROOTS
    hand = load_hand(region) if hand is None else hand
    projects = em.load_projects(roots)
    superregions = em.province_superregions(roots["anbennar"])
    province_name = em.province_names(roots["anbennar"])
    loc = em.eu4_loc(roots)
    monuments, excluded = [], {}
    for key in sorted(projects):
        project = projects[key]
        if superregions.get(project.start) not in em.CANNOR:
            continue
        if project.type == "canal":
            excluded[key] = CANAL
            continue
        art = em.art_file(roots, key)
        rel = "gfx/" + art.as_posix().split("/gfx/", 1)[1] if art else None
        monuments.append(merge(build(project, province_name.get(project.start, ""), loc, rel), hand))
    report = place(monuments, ck3_titles(anbennar_ck3), anbennar_slots(anbennar_ck3))
    report += _quality_report(monuments)
    for m in monuments:
        del m["place"]
    return {"MONUMENTS": monuments, "EXCLUDED": excluded, "REPORT": report}


def _quality_report(monuments):
    lines = []
    for m in monuments:
        if not m["gate"] and any(n.startswith("gate atom") for n in m["notes"]):
            lines.append(f"{m['eu4_key']}: gate is open ({'; '.join(n for n in m['notes'] if n.startswith('gate'))})")
        for n in m["notes"]:
            if n.endswith("not in the translation table"):
                lines.append(f"{m['eu4_key']}: {n}")
    untranslated = Counter(d.split(":")[0] for m in monuments for t in m["tiers"] for d in t["dropped"]
                           if d.endswith("not in the translation table"))
    for key, count in sorted(untranslated.items()):
        lines.append(f"modifier {key} is not in the translation table ({count} tiers)")
    dropped = Counter(d.split(":", 1)[0] for m in monuments for t in m["tiers"] for d in t["dropped"]
                      if not d.endswith("not in the translation table") and not d.startswith("on_upgraded"))
    if dropped:
        lines.append("dropped modifiers: " + ", ".join(f"{k} x{c}" for k, c in sorted(dropped.items())))
    one_offs = sum(1 for m in monuments for t in m["tiers"] for d in t["dropped"] if d.startswith("on_upgraded"))
    lines.append(f"{one_offs} one-off effects dropped (see each tier's `dropped` list)")
    return lines


def write_region(region, data):
    out = REPO / "tools" / "data" / "monuments" / f"{region}.py"
    monuments = sorted(data["MONUMENTS"], key=lambda m: m["eu4_key"])
    text = (
        "# generated by tools/import_eu4_monuments.py; edit cannor_hand.py, not this file\n\n"
        f"MONUMENTS = {pprint.pformat(monuments, width=110, sort_dicts=False)}\n\n"
        f"EXCLUDED = {pprint.pformat(data['EXCLUDED'], width=110)}\n"
    )
    out.write_bytes(text.encode("utf-8"))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--region", required=True)
    parser.add_argument("--anbennar-ck3", type=Path, default=DEFAULT_ANBENNAR_CK3)
    args = parser.parse_args(argv)
    data = run(args.region, args.anbennar_ck3)
    out = write_region(args.region, data)
    placed = sum(1 for m in data["MONUMENTS"] if m["barony"])
    print(f"{out.relative_to(REPO)}: {len(data['MONUMENTS'])} monuments ({placed} placed), "
          f"{len(data['EXCLUDED'])} excluded")
    for line in data["REPORT"]:
        print(" -", line)
    return 0 if placed == len(data["MONUMENTS"]) else 1


if __name__ == "__main__":
    sys.exit(main())
