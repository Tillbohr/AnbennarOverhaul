"""Reader for EU4 Anbennar great projects (monuments) and a DXT1 decoder for their art.

Used by the great-projects generator. EU4 text is Latin-1; EU4 localisation is UTF-8 with BOM.
"""

import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

_WORKSHOP = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850")
EU4_ROOTS = {
    "anbennar": _WORKSHOP / "1385440355",
    "cannorian": _WORKSHOP / "2811184350",
    "dwarven": _WORKSHOP / "2791499822",
}
PRECEDENCE = ("cannorian", "dwarven", "anbennar")
CANNOR = ("western_cannor_superregion", "escann_superregion", "gerudia_superregion")


def strip_comments(text):
    """Remove `#` comments, leaving quoted strings intact."""
    out = []
    for line in text.split("\n"):
        in_quote = False
        for i, ch in enumerate(line):
            if ch == '"':
                in_quote = not in_quote
            elif ch == "#" and not in_quote:
                line = line[:i]
                break
        out.append(line)
    return "\n".join(out)


def _balanced(text, open_at):
    """Index just past the brace matching text[open_at] == '{'."""
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


_KEY_BLOCK = re.compile(r"([A-Za-z0-9_.:\-]+)\s*=\s*\{")


def parse_blocks(text):
    """Top-level `key = { ... }` -> body text (without the outer braces)."""
    text = strip_comments(text)
    blocks = {}
    pos = 0
    while True:
        m = _KEY_BLOCK.search(text, pos)
        if not m:
            return blocks
        end = _balanced(text, m.end() - 1)
        blocks[m.group(1)] = text[m.end():end - 1].strip()
        pos = end


_NUMBER_ASSIGN = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(-?\d+(?:\.\d+)?)\s*$")


def _modifiers(body):
    """Flat `name = number` lines of a modifier block (nested blocks are skipped)."""
    result = {}
    depth = 0
    for line in strip_comments(body).split("\n"):
        if depth == 0:
            m = _NUMBER_ASSIGN.match(line)
            if m:
                result[m.group(1)] = float(m.group(2))
        depth += line.count("{") - line.count("}")
    return result


def _top_level(body):
    """body with nested blocks removed, so scalar lookups cannot hit inner keys."""
    out = []
    depth = 0
    for ch in strip_comments(body):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 0 or ch == "\n":
            out.append(ch)
    return "".join(out)


def _scalar(body, name, default=None):
    m = re.search(rf"(?m)^\s*{name}\s*=\s*([^\s{{}}]+)", _top_level(body))
    return m.group(1) if m else default


def _number(text, default=0):
    m = re.search(r"-?\d+(?:\.\d+)?", text or "")
    return float(m.group(0)) if m else default


@dataclass
class Tier:
    cost_factor: float = 0
    months: int = 0
    province: dict = field(default_factory=dict)
    area: dict = field(default_factory=dict)
    country: dict = field(default_factory=dict)
    on_upgraded: str = ""


@dataclass
class Project:
    key: str
    source: str
    file: str
    start: int
    year: int
    type: str
    starting_tier: int
    gate: str
    tiers: list
    mission: bool = False  # start taken from a commented `# start = N` (mission-spawned monument)


def _tier(body):
    sub = parse_blocks(body)
    factor = _number(_scalar(sub.get("cost_to_upgrade", ""), "factor"))
    return Tier(
        cost_factor=int(factor) if factor == int(factor) else factor,
        months=int(_number(_scalar(sub.get("upgrade_time", ""), "months"))),
        province=_modifiers(sub.get("province_modifiers", "")),
        area=_modifiers(sub.get("area_modifier", "")),
        country=_modifiers(sub.get("country_modifiers", "")),
        on_upgraded=sub.get("on_upgraded", ""),
    )


def _project(key, body, source, file):
    sub = parse_blocks(body)
    start = _scalar(body, "start")
    mission = start is None and _scalar(body, "commented_start") is not None
    if mission:
        start = _scalar(body, "commented_start")
    return Project(
        key=key,
        source=source,
        file=file,
        start=int(_number(start)),
        year=int(_number(_scalar(body, "date"), 1)),
        type=_scalar(body, "type", "monument"),
        starting_tier=int(_number(_scalar(body, "starting_tier"))),
        gate=sub.get("can_use_modifiers_trigger", ""),
        tiers=[_tier(sub[f"tier_{n}"]) if f"tier_{n}" in sub else Tier() for n in (1, 2, 3)],
        mission=mission,
    )


def load_projects(roots):
    """Every great project; when several roots define a key, PRECEDENCE decides."""
    projects = {}
    for source in reversed(PRECEDENCE):  # lowest precedence first, so higher ones overwrite
        root = roots.get(source)
        folder = root / "common" / "great_projects" if root else None
        if not folder or not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.txt")):
            text = path.read_bytes().decode("latin-1")
            # expose `# start = N` to the comment stripper as a readable key
            text = re.sub(r"(?m)^[ \t]*#[ \t]*start[ \t]*=[ \t]*(\d+)", r"commented_start = \1", text)
            for key, body in parse_blocks(text).items():
                projects[key] = _project(key, body, source, path.name)
    return projects


_LOC_LINE = re.compile(r'^\s*([A-Za-z0-9_.\-]+):\d*\s*"(.*)"\s*(?:#.*)?$')


def _loc_pairs(root):
    folder = root / "localisation"
    if not folder.is_dir():
        return
    for path in sorted(folder.rglob("*_l_english.yml")):
        for line in path.read_bytes().decode("utf-8-sig", errors="replace").split("\n"):
            m = _LOC_LINE.match(line.rstrip("\r"))
            if m:
                yield m.group(1), m.group(2)


def province_names(anbennar):
    names = {}
    for key, value in _loc_pairs(anbennar):
        m = re.fullmatch(r"PROV(\d+)", key)
        if m:
            names.setdefault(int(m.group(1)), value)
    return names


def eu4_loc(roots):
    loc = {}
    for source in PRECEDENCE:
        root = roots.get(source)
        if root:
            for key, value in _loc_pairs(root):
                loc.setdefault(key, value)
    return loc


def _names_in(body):
    return re.findall(r"[A-Za-z0-9_]+", strip_comments(body))


def province_superregions(anbennar):
    """province id -> superregion key, through area -> region -> superregion."""
    def read(name):
        return parse_blocks((anbennar / "map" / name).read_bytes().decode("latin-1"))

    area_of = {}
    for area, body in read("area.txt").items():
        for pid in re.findall(r"\d+", _top_level(body)):  # nested color blocks dropped
            area_of.setdefault(int(pid), area)
    region_of = {}
    for region, body in read("region.txt").items():
        for area in _names_in(parse_blocks(body).get("areas", "")):
            region_of.setdefault(area, region)
    super_of = {}
    for sup, body in read("superregion.txt").items():
        for region in _names_in(_top_level(body)):
            super_of.setdefault(region, sup)
    result = {}
    for pid, area in area_of.items():
        sup = super_of.get(region_of.get(area))
        if sup:
            result[pid] = sup
    return result


def art_file(roots, key):
    rel = Path("gfx/interface/great_projects") / f"great_project_{key}.dds"
    for source in PRECEDENCE:
        root = roots.get(source)
        if root and (root / rel).is_file():
            return root / rel
    return None


def _rgb565(value):
    r, g, b = (value >> 11) & 31, (value >> 5) & 63, value & 31
    return (r * 255 + 15) // 31, (g * 255 + 31) // 63, (b * 255 + 15) // 31


def decode_dxt1(data):
    """Decode a DDS file holding DXT1 into (width, height, BGRA bytes)."""
    if data[:4] != b"DDS " or data[84:88] != b"DXT1":
        raise ValueError("not a DXT1 DDS file")
    height, width = struct.unpack_from("<II", data, 12)
    out = bytearray(width * height * 4)
    offset = 128
    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            c0, c1, bits = struct.unpack_from("<HHI", data, offset)
            offset += 8
            r0, g0, b0 = _rgb565(c0)
            r1, g1, b1 = _rgb565(c1)
            if c0 > c1:
                palette = [
                    (r0, g0, b0, 255), (r1, g1, b1, 255),
                    ((2 * r0 + r1) // 3, (2 * g0 + g1) // 3, (2 * b0 + b1) // 3, 255),
                    ((r0 + 2 * r1) // 3, (g0 + 2 * g1) // 3, (b0 + 2 * b1) // 3, 255),
                ]
            else:
                palette = [
                    (r0, g0, b0, 255), (r1, g1, b1, 255),
                    ((r0 + r1) // 2, (g0 + g1) // 2, (b0 + b1) // 2, 255),
                    (0, 0, 0, 0),
                ]
            for i in range(16):
                x, y = bx + i % 4, by + i // 4
                if x < width and y < height:
                    r, g, b, a = palette[(bits >> (2 * i)) & 3]
                    p = (y * width + x) * 4
                    out[p:p + 4] = bytes((b, g, r, a))
    return width, height, bytes(out)
