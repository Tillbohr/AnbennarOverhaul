"""Generate the Deepwoods grove duchies' EU4 coats of arms and county names from tools/data/deepwoods_groves.py.

Each grove duchy gets its EU4 Anbennar "Salla" realm's flag as a coat of arms: the flag (gfx/flags/<tag>.tga, 128x128)
is upscaled 2x (Lanczos-3) into a 256x256 textured emblem with mipmaps, drawn over the whole coat of arms. EU4 flags
are pictures (a lotus, a ribcage, thorns...), which CK3's coloured emblems cannot rebuild. Each county gets its EU4
province's name (EU4 localisation, accents kept) through localization/replace, and so does its capital barony; other
baronies get the names of the clearing's remaining EU4 provinces where the data matches one (the build lists the rest).
Rerun after an Anbennar or EU4 Anbennar update, or after editing the data:

    python -I tools/build_deepwoods_groves.py [--eu4 PATH] [--anbennar PATH]
"""

import argparse
import re
import struct
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script's folder
from build_hud_override import GeneratorError  # noqa: E402
from build_monuments import upscale_2x  # noqa: E402
import eu4_monuments  # noqa: E402
from data import deepwoods_groves as data  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent
COA_FILE = "common/coat_of_arms/coat_of_arms/aov_deepwoods_groves.txt"
LOC_FILE = "localization/replace/english/aov_deepwoods_groves_replace_l_english.yml"
EMBLEM_DIR = "gfx/coat_of_arms/textured_emblems"
EMBLEM_PREFIX = "aov_grove_"  # aov_grove_salla_<name>.dds; the build deletes other files with this prefix
TITLES = Path("common/landed_titles/anb_landed_titles.txt")
TITLE_LOC = Path("localization/english/anb_titles_l_english.yml")
FLAG_SIZE = 128


@dataclass
class Roots:
    anbennar: Path
    eu4: Path

    @classmethod
    def default(cls):
        return cls(SUBMOD.parent / "anbennar-ck3-dev-master", eu4_monuments.EU4_ROOTS["anbennar"])


# --- images -------------------------------------------------------------------------------------------------------

def read_tga(raw: bytes) -> tuple:
    """(width, height, BGRA bytes, top row first) of a true-colour TGA, raw (type 2) or RLE (type 10), 24 or 32 bpp."""
    if len(raw) < 18:
        raise GeneratorError("TGA too short for its header")
    id_len, colormap, kind = raw[0], raw[1], raw[2]
    width, height = struct.unpack("<HH", raw[12:16])
    bpp, desc = raw[16], raw[17]
    if colormap or kind not in (2, 10) or bpp not in (24, 32):
        raise GeneratorError(f"unsupported TGA (type {kind}, colour map {colormap}, {bpp} bpp)")
    size = bpp // 8
    need = width * height * size
    pos = 18 + id_len
    if kind == 2:
        px = raw[pos:pos + need]
    else:
        out = bytearray()
        while len(out) < need:
            if pos >= len(raw):
                break
            head = raw[pos]
            pos += 1
            count = (head & 0x7F) + 1
            if head & 0x80:
                out += raw[pos:pos + size] * count
                pos += size
            else:
                out += raw[pos:pos + size * count]
                pos += size * count
        px = bytes(out[:need])
    if len(px) < need:
        raise GeneratorError(f"TGA pixel data truncated ({len(px)} of {need} bytes)")
    rows = [px[y * width * size:(y + 1) * width * size] for y in range(height)]
    if not desc & 0x20:  # bottom-up
        rows.reverse()
    bgra = bytearray()
    for row in rows:
        if size == 4:
            bgra += row
        else:
            for x in range(0, len(row), 3):
                bgra += row[x:x + 3] + b"\xff"
    return width, height, bytes(bgra)


def halve(width: int, height: int, px: bytes) -> tuple:
    """Box-filter downsample to half size (each side at least 1)."""
    nw, nh = max(width // 2, 1), max(height // 2, 1)
    out = bytearray(nw * nh * 4)
    for y in range(nh):
        for x in range(nw):
            sx = [min(2 * x, width - 1), min(2 * x + 1, width - 1)]
            sy = [min(2 * y, height - 1), min(2 * y + 1, height - 1)]
            for c in range(4):
                total = sum(px[(yy * width + xx) * 4 + c] for yy in sy for xx in sx)
                out[(y * nw + x) * 4 + c] = (total + 2) // 4
    return nw, nh, bytes(out)


def write_dds_mips(width: int, height: int, px: bytes) -> bytes:
    """Uncompressed A8R8G8B8 DDS with a full mip chain (down to 1x1)."""
    levels = [px]
    w, h = width, height
    while w > 1 or h > 1:
        w, h, p = halve(w, h, levels[-1])
        levels.append(p)
    head = bytearray(128)
    head[0:4] = b"DDS "
    struct.pack_into("<7I", head, 4, 124, 0x2100F, height, width, width * 4, 0, len(levels))
    struct.pack_into("<8I", head, 76, 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    struct.pack_into("<I", head, 108, 0x401008)  # complex | texture | mipmap
    return bytes(head) + b"".join(levels)


def flag_emblem(tga: bytes) -> tuple:
    """(textured emblem DDS bytes, (r, g, b) most common flag colour) from an EU4 flag TGA."""
    w, h, px = read_tga(tga)
    if (w, h) != (FLAG_SIZE, FLAG_SIZE):
        raise GeneratorError(f"EU4 flag is {w}x{h}, expected {FLAG_SIZE}x{FLAG_SIZE}")
    b, g, r = Counter(px[i:i + 3] for i in range(0, len(px), 4)).most_common(1)[0][0]
    w2, h2, big = upscale_2x(w, h, px)
    return write_dds_mips(w2, h2, big), (r, g, b)


# --- EU4 and Anbennar data ----------------------------------------------------------------------------------------

def eu4_countries(eu4: Path) -> dict:
    """EU4 tag -> its country file's name without folder and extension (e.g. I26 -> 'Salla Elyn')."""
    out = {}
    for path in sorted((eu4 / "common" / "country_tags").glob("*.txt")):
        text = eu4_monuments.strip_comments(path.read_bytes().decode("latin-1"))
        for tag, file in re.findall(r'^\s*([A-Z0-9]{3})\s*=\s*"([^"]+)"', text, re.M):
            out.setdefault(tag, Path(file).stem)
    return out


def region_provinces(eu4: Path, regions: tuple) -> set:
    def read(name):
        return eu4_monuments.parse_blocks((eu4 / "map" / name).read_bytes().decode("latin-1"))
    areas = read("area.txt")
    region = read("region.txt")
    out = set()
    for key in regions:
        if key not in region:
            raise GeneratorError(f"EU4 region {key} not found in map/region.txt")
        for area in eu4_monuments._names_in(eu4_monuments.parse_blocks(region[key]).get("areas", "")):
            out |= {int(p) for p in re.findall(r"\d+", eu4_monuments._top_level(areas.get(area, "")))}
    return out


def _block(text: str, key: str):
    """Body of the first `key = { ... }` block in text, or None."""
    m = re.search(r"(?<![\w.])" + re.escape(key) + r"\s*=\s*\{", text)
    return text[m.end():eu4_monuments._balanced(text, m.end() - 1) - 1] if m else None


def county_baronies(titles_text: str, duchy: str) -> dict:
    """County key -> its barony keys in title order (the first is the county's capital), for a duchy's counties."""
    body = _block(titles_text, duchy)
    if body is None:
        raise GeneratorError(f"{duchy}: not in Anbennar's {TITLES.as_posix()}")
    counties = re.findall(r"(?<![\w.])(c_\w+)\s*=\s*\{", body)
    return {c: re.findall(r"(?<![\w.])(b_\w+)\s*=\s*\{", _block(body, c)) for c in counties}


def duchy_counties(titles_text: str, duchy: str) -> list:
    """County keys directly inside a duchy's block of the landed titles."""
    return list(county_baronies(titles_text, duchy))


def anbennar_loc(anbennar: Path) -> dict:
    loc = {}
    for line in (anbennar / TITLE_LOC).read_text(encoding="utf-8-sig").splitlines():
        m = re.match(r'\s*([\w.]+):\d*\s*"(.*)"', line)
        if m:
            loc.setdefault(m.group(1), m.group(2))
    return loc


def emblem_name(country: str) -> str:
    return EMBLEM_PREFIX + re.sub(r"[^a-z0-9]+", "_", country.lower()).strip("_") + ".dds"


def collect(roots: Roots, groves: dict = None) -> list:
    """Checked grove records: duchy, tag, country (name of the EU4 file), name (EU4 display name), flag path, emblem,
    counties [(key, EU4 province name)], baronies [(key, EU4 province name)] in title order (each county's capital
    with the county's name) and unnamed [barony keys without an EU4 province]."""
    groves = data.GROVES if groves is None else groves
    titles = eu4_monuments.strip_comments((roots.anbennar / TITLES).read_text(encoding="utf-8-sig"))
    countries = eu4_countries(roots.eu4)
    loc = dict(eu4_monuments._loc_pairs(roots.eu4))
    names = eu4_monuments.province_names(roots.eu4)
    deepwoods = region_provinces(roots.eu4, data.EU4_REGIONS)
    records, seen = [], {}

    def province_name(title, pid):
        name = data.NAME_FIXES.get(pid, names.get(pid))
        if not name:
            raise GeneratorError(f"{title}: EU4 province {pid} has no name")
        if pid not in deepwoods:
            raise GeneratorError(f"{title}: EU4 province {pid} ({name}) is outside {', '.join(data.EU4_REGIONS)}")
        if name.startswith(data.PATH_PREFIX):
            raise GeneratorError(f"{title}: EU4 province {pid} ({name}) is a forest path, not a clearing")
        if '"' in name:
            raise GeneratorError(f"{title}: double quote in EU4 name {name}")
        if pid in seen:
            raise GeneratorError(f"{title}: EU4 province {pid} already used by {seen[pid]}")
        seen[pid] = title
        return name

    for duchy, grove in groves.items():
        tag = grove["tag"]
        if tag not in countries:
            raise GeneratorError(f"{duchy}: EU4 tag {tag} not in common/country_tags")
        flag = roots.eu4 / "gfx" / "flags" / f"{tag}.tga"
        if not flag.is_file():
            raise GeneratorError(f"{duchy}: EU4 flag {flag} missing")
        real = county_baronies(titles, duchy)
        counties = []
        for county, pid in grove["counties"].items():
            if county not in real:
                raise GeneratorError(f"{duchy}: {county} is not one of its counties ({', '.join(real)})")
            counties.append((county, province_name(county, pid)))
        capitals = {bs[0]: c for c, bs in real.items() if bs}
        chosen = grove.get("baronies", {})
        for barony in chosen:
            if barony in capitals:
                raise GeneratorError(f"{barony}: capital of {capitals[barony]}, so it takes the county's name")
            if not any(barony in bs for bs in real.values()):
                raise GeneratorError(f"{duchy}: {barony} is not one of its baronies")
        county_names = dict(counties)
        baronies, unnamed = [], []
        for county, bs in real.items():
            for barony in bs:
                if barony in capitals and county in county_names:
                    baronies.append((barony, county_names[county]))
                elif barony in chosen:
                    baronies.append((barony, province_name(barony, chosen[barony])))
                else:
                    unnamed.append(barony)
        records.append({"duchy": duchy, "tag": tag, "country": countries[tag], "flag": flag,
                        "name": loc.get(tag, countries[tag]), "emblem": emblem_name(countries[tag]), "counties": counties,
                        "baronies": baronies, "unnamed": unnamed})
    return records


# --- output -------------------------------------------------------------------------------------------------------

def coa_text(records: list, colours: dict) -> str:
    lines = ["# Anbennar Overhaul: the Deepwoods grove duchies carry their EU4 Anbennar realm's flag.",
             "# Generated by tools/build_deepwoods_groves.py from tools/data/deepwoods_groves.py; do not edit.", ""]
    for r in records:
        red, green, blue = colours[r["duchy"]]
        lines += [f"# {r['name']} (EU4 {r['tag']})",
                  f"{r['duchy']} = {{",
                  '\tpattern = "pattern_solid.dds"',
                  f"\tcolor1 = rgb {{ {red} {green} {blue} }}",
                  "\ttextured_emblem = {",
                  f"\t\ttexture = \"{r['emblem']}\"",
                  "\t}",
                  "}", ""]
    return "\n".join(lines)


def loc_text(records: list) -> str:
    lines = ["l_english:",
             " # Anbennar Overhaul: Deepwoods counties and baronies named after their EU4 Anbennar provinces",
             " # (generated by tools/build_deepwoods_groves.py; do not edit)"]
    for r in records:
        lines.append(f" # {r['duchy']} ({r['name']})")
        lines += [f' {title}:0 "{name}"' for title, name in r["counties"] + r["baronies"]]
    return "\n".join(lines) + "\n"


def build_all(roots: Roots, groves: dict = None) -> dict:
    """Published path -> file bytes."""
    records = collect(roots, groves)
    files, colours = {}, {}
    for r in records:
        dds, colours[r["duchy"]] = flag_emblem(r["flag"].read_bytes())
        files[f"{EMBLEM_DIR}/{r['emblem']}"] = dds
    files[COA_FILE] = b"\xef\xbb\xbf" + coa_text(records, colours).encode("utf-8")
    files[LOC_FILE] = b"\xef\xbb\xbf" + loc_text(records).encode("utf-8")
    return files


def fold(name: str) -> str:
    """Lower-case name without accents, to spot Anbennar's unaccented copies of EU4 names."""
    return "".join(c for c in unicodedata.normalize("NFD", name.lower()) if not unicodedata.combining(c))


def renames(roots: Roots) -> tuple:
    """([(title, Anbennar's name or None, EU4 name)] for every county and barony whose name changes,
    [(barony, Anbennar's name or None, title now named so or None)] for every barony left without an EU4 name)."""
    loc = anbennar_loc(roots.anbennar)
    records = collect(roots)
    titles = [(t, n) for r in records for t, n in r["counties"] + r["baronies"]]
    changed = [(t, loc.get(t), n) for t, n in titles if loc.get(t) != n]
    named = {fold(n): t for t, n in titles if t.startswith("b_")}
    return changed, [(b, loc.get(b), named.get(fold(loc.get(b) or ""))) for r in records for b in r["unnamed"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default = Roots.default()
    parser.add_argument("--eu4", type=Path, default=default.eu4)
    parser.add_argument("--anbennar", type=Path, default=default.anbennar)
    args = parser.parse_args()
    roots = Roots(args.anbennar, args.eu4)
    try:
        files = build_all(roots)
        changed, unnamed = renames(roots)
    except GeneratorError as e:
        sys.exit(f"error: {e}")
    produced = set(files)
    for old in (SUBMOD / EMBLEM_DIR).glob(EMBLEM_PREFIX + "*.dds"):
        if old.relative_to(SUBMOD).as_posix() not in produced:
            old.unlink()
    for rel, content in files.items():
        out = SUBMOD / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(content)
    sys.stdout.reconfigure(encoding="utf-8")
    for title, old, new in changed:
        print(f"note: {title}: {old!r} -> {new!r}")
    for barony, old, twin in unnamed:
        kept = f"keeps Anbennar's {old!r}" if old else "has no name"
        if twin:
            kept += f", now also {twin}'s name"
        print(f"note: {barony}: no EU4 province left, {kept}")
    print(f"wrote {len(files)} files for {len(data.GROVES)} grove duchies")


if __name__ == "__main__":
    main()
