"""Generate holy sites for Anbennar faiths that have none (Devouring Path, Silk Turban), real icons for the
faiths Anbennar ships with the placeholder icon (and for Jaherian Cults, which shares the generic Sun Cult icon), and
the `icon` lines that make the game draw the doctrine icons of tools/data/doctrine_icons.py.

A faith's holy sites and icon can only be set inside its religion's definition, and religions can only be overridden
as whole files, so this script writes full copies of the Anbennar religion files involved, each faith gaining a
holy_site line per site in tools/data/holy_sites.py and its icon from tools/data/faith_icons.py (the icon pictures
are imported once and committed under gfx/interface/icons/faith/). It also writes the holy sites and their names:

    common/religion/holy_site_types/aov_holy_sites.txt     the new holy sites
    common/religion/religion_types/<anbennar file>.txt     whole-file copies with holy_site and icon lines changed
    common/religion/doctrine_types/<anbennar file>.txt     whole-file copies with an icon line added per doctrine
    localization/english/aov_holy_sites_l_english.yml      holy site and modifier names

    python -I tools/build_holy_sites.py [--anbennar PATH]

Rerun after an Anbennar update (see docs/systems/holy-sites.md). It stops if a faith is missing, already has
holy sites of its own, no longer has the icon it replaces, or a site's county or barony or an icon file is missing,
and when a doctrine icon is neither the key of a doctrine without an `icon` line nor an icon some doctrine names.

CK3 1.19 does not fall back to a doctrine's key when it has no `icon` line, although _doctrine_types.info says it
does: the faith window draws the pink placeholder and logs nothing. So each doctrine with an icon of ours gets an
explicit `icon = "<key>"`. The doctrine files are copied whole because overriding one doctrine by key is untested.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the tools folder

from build_hud_override import GeneratorError  # noqa: E402
from pdx_script import ANBENNAR_CK3, _balanced, ck3_titles, parse_blocks, strip_comments  # noqa: E402
from data.doctrine_icons import DOCTRINE_ICONS  # noqa: E402
from data.faith_icons import FAITH_ICONS, PLACEHOLDER  # noqa: E402
from data.holy_sites import HOLY_SITES  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent
RELIGION_DIR = "common/religion/religion_types"
HOLY_SITE_DIR = "common/religion/holy_site_types"
DOCTRINE_DIR = "common/religion/doctrine_types"
ICON_DIR = "gfx/interface/icons/faith"
SITES_FILE = f"{HOLY_SITE_DIR}/aov_holy_sites.txt"
LOC_FILE = "localization/english/aov_holy_sites_l_english.yml"
MARKER = "# Anbennar Overhaul"
BOM = b"\xef\xbb\xbf"


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig")


def faith_files(anbennar: Path) -> dict:
    """faith -> (religion file name, its faith body) for every faith Anbennar defines."""
    found = {}
    for path in sorted((anbennar / RELIGION_DIR).glob("*.txt")):
        for religion, body in parse_blocks(strip_comments(_read(path))).items():
            m = re.search(r"\bfaiths\s*=\s*\{", body)
            if not m:
                continue
            for faith, faith_body in parse_blocks(body[m.end():_balanced(body, m.end() - 1) - 1]).items():
                if faith in found:
                    raise GeneratorError(f"faith {faith} is defined in both {found[faith][0]} and {path.name}")
                found[faith] = (path.name, faith_body)
    return found


def anbennar_holy_sites(anbennar: Path) -> set:
    keys = set()
    for path in sorted((anbennar / HOLY_SITE_DIR).glob("*.txt")):
        keys |= set(parse_blocks(strip_comments(_read(path))))
    return keys


def check_sites(anbennar: Path, faiths: dict) -> None:
    provinces, county_baronies = ck3_titles(anbennar)
    taken = anbennar_holy_sites(anbennar)
    seen = set()
    for site in HOLY_SITES:
        key = site["key"]
        if key in seen:
            raise GeneratorError(f"holy site {key} is listed twice in tools/data/holy_sites.py")
        seen.add(key)
        if key in taken:
            raise GeneratorError(f"Anbennar now defines a holy site named {key}; rename ours")
        if site["county"] not in county_baronies:
            raise GeneratorError(f"holy site {key}: county {site['county']} no longer exists")
        if site["barony"] not in county_baronies[site["county"]] or site["barony"] not in provinces:
            raise GeneratorError(f"holy site {key}: barony {site['barony']} is not in {site['county']}")
        for faith in site["faiths"]:
            if faith not in faiths:
                raise GeneratorError(f"holy site {key}: faith {faith} no longer exists")
            if re.search(r"\bholy_site\s*=", faiths[faith][1]):
                raise GeneratorError(f"faith {faith} now has Anbennar holy sites; drop it from tools/data/holy_sites.py")


def replaced(entry: dict) -> str:
    """The Anbennar icon a faith_icons.py entry replaces: the placeholder unless the entry names another."""
    return entry.get("replaces", PLACEHOLDER)


def check_icons(anbennar: Path, faiths: dict) -> None:
    for faith, entry in FAITH_ICONS.items():
        if faith not in faiths:
            raise GeneratorError(f"faith {faith} no longer exists; drop it from tools/data/faith_icons.py")
        current = re.findall(r"(?m)^\s*icon\s*=\s*(\w+)", faiths[faith][1])
        if current != [replaced(entry)]:
            raise GeneratorError(f"faith {faith} now has icon {current} in Anbennar; drop it from tools/data/faith_icons.py")
        name = f"{ICON_DIR}/{entry['icon']}.dds"
        if not (SUBMOD / name).is_file() and not (anbennar / name).is_file():
            raise GeneratorError(f"faith {faith}: icon file {name} is missing")


def set_icons(text: str, faith_icons: dict, replaces: dict = None) -> str:
    """Point each faith's icon and reformed_icon lines that hold the replaced icon (the placeholder unless `replaces`
    names another for that faith) at its new icon, marking the changed lines."""
    lines = text.split("\n")
    for faith, icon in faith_icons.items():
        old = (replaces or {}).get(faith, PLACEHOLDER)
        hits = [i for i, l in enumerate(lines) if re.match(rf"^\s*{re.escape(faith)}\s*=\s*\{{", l.split("#", 1)[0])]
        if len(hits) != 1:
            raise GeneratorError(f"faith {faith}: expected one opening line, found {len(hits)}")
        depth, changed = 0, []
        for i in range(hits[0], len(lines)):
            m = re.match(r"^(\s*)(icon|reformed_icon)\s*=\s*(\w+)\s*$", lines[i])
            if depth == 1 and m and m.group(3) == old:
                lines[i] = f"{m.group(1)}{m.group(2)} = {icon} {MARKER}, was {old}"
                changed.append(m.group(2))
            code = lines[i].split("#", 1)[0]
            depth += code.count("{") - code.count("}")
            if depth == 0:
                break
        if "icon" not in changed:
            raise GeneratorError(f"faith {faith}: no 'icon = {old}' line to replace")
    return "\n".join(lines)


def sites_by_faith() -> dict:
    out = {}
    for site in HOLY_SITES:
        for faith in site["faiths"]:
            out.setdefault(faith, []).append(site["key"])
    return out


def add_holy_sites(text: str, faith_sites: dict) -> str:
    """Insert one marked holy_site line per site right after each faith's opening line."""
    lines = text.split("\n")
    for faith, keys in faith_sites.items():
        hits = [i for i, l in enumerate(lines) if re.match(rf"^\s*{re.escape(faith)}\s*=\s*\{{", l.split("#", 1)[0])]
        if len(hits) != 1:
            raise GeneratorError(f"faith {faith}: expected one opening line, found {len(hits)}")
        i = hits[0]
        indent = re.match(r"^(\s*)", lines[i]).group(1) + "\t"
        lines[i + 1:i + 1] = [f"{indent}holy_site = {key} {MARKER}" for key in keys]
    return "\n".join(lines)


def doctrines_needing_icons(anbennar: Path) -> dict:
    """Anbennar doctrine file name -> its doctrines that have an icon of ours but no `icon` line."""
    out, named = {}, set()
    for path in sorted((anbennar / DOCTRINE_DIR).glob("*.txt")):
        for key, body in parse_blocks(_read(path)).items():
            m = re.search(r'(?m)^\s*icon\s*=\s*"?(\w+)"?', body)
            if m:
                named.add(m.group(1))
            elif key in DOCTRINE_ICONS:
                out.setdefault(path.name, []).append(key)
    found = named | {key for keys in out.values() for key in keys}
    for icon in DOCTRINE_ICONS:
        if icon not in found:
            raise GeneratorError(f"doctrine icon {icon} is used by no Anbennar doctrine; drop it from "
                                 "tools/data/doctrine_icons.py")
    return out


def add_doctrine_icons(text: str, keys: list) -> str:
    """Insert a marked `icon = "<key>"` line right after each doctrine's opening line."""
    lines = text.split("\n")
    for key in keys:
        hits = [i for i, l in enumerate(lines) if re.match(rf"^\s*{re.escape(key)}\s*=\s*\{{", l.split("#", 1)[0])]
        if len(hits) != 1:
            raise GeneratorError(f"doctrine {key}: expected one opening line, found {len(hits)}")
        i = hits[0]
        indent = re.match(r"^(\s*)", lines[i]).group(1) + "\t"
        lines.insert(i + 1, f'{indent}icon = "{key}" {MARKER}')
    return "\n".join(lines)


def copy_with_marker(anbennar: Path, rel: str, change, data: str) -> bytes:
    """A whole-file copy of Anbennar's `rel` with `change` applied to its text, headed by the generated-file marker
    naming the `data` files to edit instead."""
    raw = (anbennar / rel).read_bytes()
    text = raw.decode("utf-8-sig")
    crlf = "\r\n" in text
    text = change(text.replace("\r\n", "\n"))
    text = (f"{MARKER}: generated by tools/build_holy_sites.py from Anbennar's {rel}.\n"
            f"{MARKER}: do not edit by hand; edit {data} and rerun it.\n") + text
    if crlf:
        text = text.replace("\n", "\r\n")
    return (BOM if raw.startswith(BOM) else b"") + text.encode("utf-8")


def religion_file(anbennar: Path, name: str, faith_sites: dict, faith_icons: dict, replaces: dict = None) -> bytes:
    return copy_with_marker(anbennar, f"{RELIGION_DIR}/{name}",
                            lambda text: add_holy_sites(set_icons(text, faith_icons, replaces), faith_sites),
                            "tools/data/holy_sites.py or faith_icons.py")


def doctrine_file(anbennar: Path, name: str, keys: list) -> bytes:
    return copy_with_marker(anbennar, f"{DOCTRINE_DIR}/{name}", lambda text: add_doctrine_icons(text, keys),
                            "tools/data/doctrine_icons.py")


def sites_file() -> bytes:
    out = [f"{MARKER}: generated by tools/build_holy_sites.py; do not edit by hand. See docs/systems/holy-sites.md.", ""]
    for site in HOLY_SITES:
        key = site["key"]
        out += [f"{key} = {{", f"\tcounty = {site['county']}", f"\tbarony = {site['barony']}", "",
                "\tcharacter_modifier = {", f"\t\tname = holy_site_{key}_effect_name"]
        out += [f"\t\t{name} = {value}" for name, value in site["modifier"].items()]
        out += ["\t}", "}", ""]
    return BOM + "\n".join(out).encode("utf-8")


def loc_file() -> bytes:
    out = ["l_english:", f" {MARKER}: generated by tools/build_holy_sites.py; do not edit by hand."]
    for site in HOLY_SITES:
        key = site["key"]
        out.append(f' holy_site_{key}_name:0 "{site["name"]}"')
        out.append(f' holy_site_{key}_effect_name:0 "From [holy_site|E] #weak ($holy_site_{key}_name$)#!"')
    return BOM + ("\n".join(out) + "\n").encode("utf-8")


def build_all(anbennar: Path = ANBENNAR_CK3) -> dict:
    """-> {path relative to the submod: file bytes}."""
    faiths = faith_files(anbennar)
    check_sites(anbennar, faiths)
    check_icons(anbennar, faiths)
    sites, icons = {}, {}
    for faith, keys in sites_by_faith().items():
        sites.setdefault(faiths[faith][0], {})[faith] = keys
    replaces = {faith: replaced(entry) for faith, entry in FAITH_ICONS.items()}
    for faith, entry in FAITH_ICONS.items():
        icons.setdefault(faiths[faith][0], {})[faith] = entry["icon"]
    files = {SITES_FILE: sites_file(), LOC_FILE: loc_file()}
    for name in sorted(set(sites) | set(icons)):
        files[f"{RELIGION_DIR}/{name}"] = religion_file(anbennar, name, sites.get(name, {}), icons.get(name, {}),
                                                        replaces)
    for name, keys in doctrines_needing_icons(anbennar).items():
        files[f"{DOCTRINE_DIR}/{name}"] = doctrine_file(anbennar, name, keys)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anbennar", type=Path, default=ANBENNAR_CK3)
    args = parser.parse_args()
    try:
        files = build_all(args.anbennar)
    except (GeneratorError, OSError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for rel, content in files.items():
        target = SUBMOD / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        print(f"wrote {rel}")
    stale = [f"{d}/{p.name}" for d in (RELIGION_DIR, DOCTRINE_DIR) for p in (SUBMOD / d).glob("*.txt")
             if f"{d}/{p.name}" not in files]
    if stale:
        print(f"note: delete overrides no longer generated: {', '.join(stale)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
