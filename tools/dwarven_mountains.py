"""Dwarven mountain ranges and their gate sites, read from Anbennar's map data.

Works in map coordinates (x east, y north, y = 0 at the south edge); PNG rows are flipped only when
`provinces.png` is read. Province ids come from `provinces.png` through the colours in `definition.csv`.
A range is a set of dwarven provinces touching each other; a gate site is a place where a range borders
ordinary land, one per (dwarven county, normal-land county) pair.
"""

import math
import re
import sys
from array import array
from collections import defaultdict
from dataclasses import dataclass
from itertools import compress, repeat
from operator import ne
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the tools folder
from build_hud_override import GeneratorError  # noqa: E402
from data import map_graphics as data  # noqa: E402
from pngio import read_png  # noqa: E402


@dataclass
class ProvinceMap:
    """Province id of every pixel: `ids[y * width + x]`, y = 0 at the south edge; 0 = no province."""
    width: int
    height: int
    ids: array


@dataclass
class GateSite:
    """A border between a dwarven county and a normal-land county.

    (x, y) is a pixel on the dwarven side; `inward` is the unit vector pointing into the dwarven land."""
    dwarven_county: str
    normal_county: str
    x: int
    y: int
    inward: tuple


def load_province_map(png, definition):
    """Decode `provinces.png` bytes with `definition.csv` text into a ProvinceMap (unknown colours -> 0)."""
    colours = {}
    for line in definition.lstrip("﻿").splitlines():
        fields = line.split(";")
        if len(fields) > 3 and fields[0].strip().isdigit() and int(fields[0]) > 0:
            try:
                colours[(int(fields[1]), int(fields[2]), int(fields[3]))] = int(fields[0])
            except ValueError:
                raise GeneratorError(f"bad colour in definition.csv line: {line!r}")
    img = read_png(png)
    if img.bit_depth != 8 or img.color_type not in (2, 6):
        raise GeneratorError(f"provinces.png must be 8-bit RGB or RGBA, got bit depth {img.bit_depth}, "
                             f"colour type {img.color_type}")
    bpp = 3 if img.color_type == 2 else 4
    w, h = img.width, img.height
    stride = w * bpp
    pixels = img.pixels
    ids = array("H")
    get = colours.get
    for r in range(h - 1, -1, -1):  # map row 0 is the bottom PNG row
        row = pixels[r * stride:(r + 1) * stride]
        ids.extend(map(get, zip(row[0::bpp], row[1::bpp], row[2::bpp]), repeat(0)))
    return ProvinceMap(w, h, ids)


def _id_list(text, key):
    found = set()
    for m in re.finditer(key + r"\s*=\s*(LIST|RANGE)\s*\{([^}]*)\}", text):
        nums = [int(n) for n in m.group(2).split()]
        if m.group(1) == "LIST":
            found.update(nums)
        elif len(nums) == 2:
            found.update(range(nums[0], nums[1] + 1))
        else:
            raise GeneratorError(f"default.map: {key} RANGE needs two numbers, got {nums}")
    return found


def default_map_sets(text):
    """(water, impassable) province id sets from `default.map`."""
    text = re.sub(r"#[^\n]*", "", text)
    water = _id_list(text, "sea_zones") | _id_list(text, "lakes") | _id_list(text, "river_provinces")
    impassable = _id_list(text, "impassable_mountains") | _id_list(text, "impassable_seas")
    return water, impassable


def province_terrain(text):
    """{province id: terrain} from `00_province_terrain.txt` lines `<id>=<terrain>`."""
    return {int(m.group(1)): m.group(2) for m in re.finditer(r"^\s*(\d+)\s*=\s*(\w+)", text, re.M)}


def dwarven_provinces(terrain):
    return {pid for pid, name in terrain.items() if name in data.DWARVEN_TERRAINS}


def _strip(text):
    """Remove `#` comments outside double-quoted strings and blank the strings themselves."""
    out = []
    for line in text.splitlines():
        kept = []
        in_string = False
        for ch in line:
            if ch == '"':
                in_string = not in_string
            elif in_string:
                continue
            elif ch == "#":
                break
            else:
                kept.append(ch)
        out.append("".join(kept))
    return "\n".join(out)


def province_titles(titles_text):
    """{province id: (empire, kingdom, county)} from landed titles text; a missing level is None."""
    owner = {}
    stack = []
    for m in re.finditer(r"([ekdcb]_[A-Za-z0-9_]+)\s*=\s*\{|\bprovince\s*=\s*(\d+)|\{|\}", _strip(titles_text)):
        if m.group(1):
            stack.append(m.group(1))
        elif m.group(2):
            names = {s[0]: s for s in stack if s}
            owner[int(m.group(2))] = (names.get("e"), names.get("k"), names.get("c"))
        elif m.group(0) == "{":
            stack.append(None)
        elif stack:
            stack.pop()
    return owner


def border_pixels(pm):
    """{(a, b): [(x, y), ...]}: for every ordered pair of touching provinces, a's pixels next to b (4-neighbour)."""
    w, h, ids = pm.width, pm.height, pm.ids
    border = defaultdict(list)
    for y in range(h):
        row = ids[y * w:(y + 1) * w]
        for x in compress(range(w - 1), map(ne, row, row[1:])):  # east neighbour differs
            a, b = row[x], row[x + 1]
            border[(a, b)].append((x, y))
            border[(b, a)].append((x + 1, y))
        if y + 1 < h:
            up = ids[(y + 1) * w:(y + 2) * w]
            for x in compress(range(w), map(ne, row, up)):  # north neighbour differs
                a, b = row[x], up[x]
                border[(a, b)].append((x, y))
                border[(b, a)].append((x, y + 1))
    return border


def ranges(dwarven, border):
    """Connected groups of dwarven provinces that touch each other, largest first."""
    neighbours = defaultdict(set)
    for a, b in border:
        if a in dwarven and b in dwarven:
            neighbours[a].add(b)
    seen = set()
    found = []
    for start in sorted(dwarven):
        if start in seen:
            continue
        group, todo = set(), [start]
        while todo:
            p = todo.pop()
            if p in seen:
                continue
            seen.add(p)
            group.add(p)
            todo.extend(neighbours[p] - seen)
        found.append(group)
    found.sort(key=lambda g: (-len(g), min(g)))
    return found


def _centroid(points):
    n = len(points)
    return sum(p[0] for p in points) / n, sum(p[1] for p in points) / n


def gate_sites(pm, dwarven, water, impassable, titles, border, exclude_regions):
    """One GateSite per (dwarven county, normal-land county) pair that shares a border, sorted by county names.

    Normal land is any province that is not dwarven, water, impassable or 0. The site is the dwarven-side
    border pixel nearest the centroid of the pair's dwarven-side border pixels. Pairs whose dwarven province
    lies in an excluded empire, and provinces without a county, are skipped."""
    dwarven_px = defaultdict(list)
    normal_px = defaultdict(list)
    for (a, b), pixels in border.items():
        if a not in dwarven or b in dwarven or b in water or b in impassable or b == 0 or a == 0:
            continue
        if a not in titles or b not in titles or titles[a][0] in exclude_regions:
            continue
        key = (titles[a][2], titles[b][2])
        dwarven_px[key].extend(pixels)
        normal_px[key].extend(border[(b, a)])
    sites = []
    for key in sorted(dwarven_px):
        mine, theirs = dwarven_px[key], normal_px[key]
        cx, cy = _centroid(mine)
        x, y = min(mine, key=lambda p: ((p[0] - cx) ** 2 + (p[1] - cy) ** 2, p[1], p[0]))
        nx, ny = _centroid(theirs)
        dx, dy = cx - nx, cy - ny
        length = math.hypot(dx, dy)
        if length == 0:
            raise GeneratorError(f"gate site {key[0]}/{key[1]}: both sides of the border have the same centre")
        sites.append(GateSite(key[0], key[1], x, y, (dx / length, dy / length)))
    return sites
