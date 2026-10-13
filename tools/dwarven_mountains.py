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


def spaced_sites(sites, border, titles, min_spacing):
    """Drop gate sites closer than `min_spacing` map units to a stronger one.

    The strength of a site is the length of the border (pixels of `border`) between the provinces of its
    dwarven county and those of its normal-land county; ties go to the earlier site in `sites`. Sites are
    taken strongest first and kept when no kept site is closer than `min_spacing`; the result keeps the
    order of `sites`."""
    provinces = defaultdict(list)
    for pid, (_, _, county) in titles.items():
        provinces[county].append(pid)

    def strength(site):
        return sum(len(border.get((a, b), ())) for a in provinces[site.dwarven_county]
                   for b in provinces[site.normal_county])

    order = sorted(range(len(sites)), key=lambda i: (-strength(sites[i]), i))
    kept = []
    for i in order:
        s = sites[i]
        if all(math.hypot(s.x - sites[j].x, s.y - sites[j].y) >= min_spacing for j in kept):
            kept.append(i)
    return [sites[i] for i in sorted(kept)]


def soft_ceiling(v):
    """`v` unchanged up to SOFT_CEILING; above it, compressed so it never reaches 65536."""
    c = data.SOFT_CEILING
    if v <= c:
        return int(round(v))
    span = 65535 - c
    return min(65535, c + int(round(span * (1 - math.exp(-(v - c) / span)))))


def lift_factor(peak, ground):
    """The factor that takes a range's `peak` to LIFT_PEAK measured from `ground`, between 1 and LIFT_MAX."""
    if peak <= ground:
        return 1
    return max(1, min(data.LIFT_MAX, (data.LIFT_PEAK - ground) / (peak - ground)))


def _lookup(provinces):
    table = bytearray(65536)
    for p in provinces:
        table[p] = 1
    return table


_NEIGHBOURS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def _reach(sources, radius, pm, blocked):
    """{pixel: (distance, nearest source)} for the pixels within `radius` of `sources` (flat indices).

    Spreads through 8-neighbours over provinces whose `blocked` entry is 0 (so never into dwarven land);
    the distance is the Euclidean distance to the source that reached the pixel first."""
    w, h, ids = pm.width, pm.height, pm.ids
    seen = {s: s for s in sources}
    frontier = list(sources)
    for _ in range(radius):
        nxt = []
        for i in frontier:
            o = seen[i]
            y, x = divmod(i, w)
            for dx, dy in _NEIGHBOURS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    j = ny * w + nx
                    if j not in seen and not blocked[ids[j]]:
                        seen[j] = o
                        nxt.append(j)
        frontier = nxt
    reach = {}
    for i, o in seen.items():
        if i != o:
            d = math.hypot(i % w - o % w, i // w - o // w)
            if d <= radius:
                reach[i] = (d, o)
    return reach


def _ground(old, pm, reach, water):
    ids = pm.ids
    samples = sorted(old[i] for i, (d, _) in reach.items()
                     if d <= data.LIFT_GROUND_RING and ids[i] and not water[ids[i]])
    return samples[len(samples) // 2] if samples else None


def range_ground(grid, pm, rng, dwarven, water):
    """Median height of the non-dwarven, non-water pixels within LIFT_GROUND_RING px of the range `rng`."""
    dw = _lookup(dwarven)
    px = [i for i, v in enumerate(pm.ids) if v in rng]
    return _ground(grid.values, pm, _reach(px, data.LIFT_GROUND_RING, pm, dw), _lookup(water))


def _range_groups(dwarven, pm, pixels):
    """Groups of dwarven provinces that touch each other (by pixel contact), largest first."""
    w, h, ids = pm.width, pm.height, pm.ids
    parent = {p: p for p in pixels}

    def find(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    dw = _lookup(dwarven)
    for p, idx in pixels.items():
        for i in idx:
            y, x = divmod(i, w)
            if x + 1 < w and dw[ids[i + 1]] and ids[i + 1] != p:
                parent[find(ids[i + 1])] = find(p)
            if y + 1 < h and dw[ids[i + w]] and ids[i + w] != p:
                parent[find(ids[i + w])] = find(p)
    groups = defaultdict(set)
    for p in pixels:
        groups[find(p)].add(p)
    return sorted(groups.values(), key=lambda g: (-len(g), min(g)))


def _pad_height(old, pm, site, dw, blocked, search=40):
    """Height of the normal-land pixel nearest the site (not dwarven, water, impassable or 0)."""
    w, h, ids = pm.width, pm.height, pm.ids
    best = None
    for y in range(max(0, site.y - search), min(h, site.y + search + 1)):
        for x in range(max(0, site.x - search), min(w, site.x + search + 1)):
            v = ids[y * w + x]
            if v and not dw[v] and not blocked[v]:
                key = ((x - site.x) ** 2 + (y - site.y) ** 2, y, x)
                if best is None or key < best[0]:
                    best = (key, old[y * w + x])
    return best[1] if best else old[site.y * w + site.x]


def raise_heights(grid, pm, dwarven, water, impassable, sites):
    """Lift every dwarven range and shape the gate sites; returns (new grid, report).

    Per range: ground = `range_ground`, factor = `lift_factor(peak, ground)`; a pixel above the ground is
    moved to `ground + (h - ground) * factor` (soft ceiling applied, never lowered), and the change fades
    out over FADE_PX px into the surrounding land and water. Per site: a flat pad of radius GATE_PAD at the
    height of the nearest normal-land pixel (the only pixels that may go down) and, behind it on the
    dwarven side, a cliff: pixels within GATE_RISE_DIST px raised to at least pad + GATE_RISE.
    The report is {"ranges": [{provinces, ground, factor, peak_before, peak_after}],
    "sites": [{dwarven_county, normal_county, x, y, pad, rise}]}; `rise` is the lowest cliff pixel above the pad."""
    w, h, ids = pm.width, pm.height, pm.ids
    old = grid.values
    new = array("H", old)
    dw = _lookup(dwarven)
    wat = _lookup(water)
    blocked = _lookup(set(water) | set(impassable))
    pixels = defaultdict(list)
    for y in range(h):
        row = ids[y * w:(y + 1) * w]
        if dwarven.isdisjoint(row):
            continue
        for x, v in enumerate(row):
            if dw[v]:
                pixels[v].append(y * w + x)
    report = {"ranges": [], "sites": []}
    for group in _range_groups(dwarven, pm, pixels):
        px = [i for p in group for i in pixels[p]]
        reach = _reach(px, max(data.LIFT_GROUND_RING, data.FADE_PX), pm, dw)
        ground = _ground(old, pm, reach, wat)
        peak = max(old[i] for i in px)
        factor = 1 if ground is None else lift_factor(peak, ground)
        if factor > 1:
            for i in px:
                if old[i] > ground:
                    new[i] = max(old[i], soft_ceiling(ground + (old[i] - ground) * factor))
            for i, (d, o) in reach.items():
                if d < data.FADE_PX and new[o] > old[o]:
                    value = min(65535, old[i] + int(round((new[o] - old[o]) * (1 - d / data.FADE_PX))))
                    if value > new[i]:
                        new[i] = value
        report["ranges"].append({"provinces": sorted(group), "ground": ground, "factor": factor,
                                 "peak_before": peak, "peak_after": max(new[i] for i in px)})
    reach_px = max(data.GATE_RISE_DIST, data.GATE_PAD)
    for site in sites:
        pad = _pad_height(old, pm, site, dw, blocked)
        cliff = soft_ceiling(pad + data.GATE_RISE)
        ix, iy = site.inward
        rise = None
        for y in range(max(0, site.y - reach_px), min(h, site.y + reach_px + 1)):
            for x in range(max(0, site.x - reach_px), min(w, site.x + reach_px + 1)):
                dx, dy = x - site.x, y - site.y
                d = math.hypot(dx, dy)
                i = y * w + x
                if d <= data.GATE_PAD:
                    new[i] = pad
                elif d <= data.GATE_RISE_DIST and dx * ix + dy * iy > 0 and ids[i] and not wat[ids[i]]:
                    if new[i] < cliff:
                        new[i] = cliff
                    rise = new[i] - pad if rise is None else min(rise, new[i] - pad)
        report["sites"].append({"dwarven_county": site.dwarven_county, "normal_county": site.normal_county,
                                "x": site.x, "y": site.y, "pad": pad, "rise": rise or 0})
    return type(grid)(w, h, new), report
