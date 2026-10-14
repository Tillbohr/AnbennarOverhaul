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


def gate_position(site, inset, option=None):
    """Where a gate mesh stands: the site moved `inset` (or the option's `inset`) along `inward`, plus the
    option's `dx`, `dy`. The transform of the gate map object and the terrain massif both use this."""
    option = option or {}
    move = option.get("inset", inset)
    return (site.x + site.inward[0] * move + option.get("dx", 0.0),
            site.y + site.inward[1] * move + option.get("dy", 0.0))


def gate_placements(sites, inset, overrides):
    """[(site, (x, y))] with each gate's final position (see `gate_position`); `overrides` maps
    (dwarven county, normal county) to option dicts."""
    overrides = overrides or {}
    return [(s, gate_position(s, inset, overrides.get((s.dwarven_county, s.normal_county)))) for s in sites]


def _ease(x):
    """Cosine ease from 1 (x = 0) to 0 (x = 1)."""
    return 0.5 + 0.5 * math.cos(math.pi * min(1.0, max(0.0, x)))


def gate_scale(site, scale, overrides):
    """The scale of a gate's mesh: the override's `scale`, else `scale`."""
    option = (overrides or {}).get((site.dwarven_county, site.normal_county), {})
    return option.get("scale", scale)


def massif_weight(t, lateral):
    """Weight 0..1 of a gate's massif `t` px behind the gate position (negative = in front) and `lateral` px off
    its axis: 1 in the core rectangle (0..MASSIF_CORE_DEPTH behind, within MASSIF_CORE_HALF_WIDTH), a cosine ease
    to 0 over MASSIF_FALLOFF px of distance from that rectangle, and 0 in front of the gate face (t <= -1)."""
    if t <= -1:
        return 0.0
    along = max(-t, t - data.MASSIF_CORE_DEPTH, 0.0)
    across = max(abs(lateral) - data.MASSIF_CORE_HALF_WIDTH, 0.0)
    dist = math.hypot(along, across)
    if dist >= data.MASSIF_FALLOFF:
        return 0.0
    return _ease(dist / data.MASSIF_FALLOFF)


def _edge_distance(i, w, blocked_px, offsets):
    """Euclidean distance from flat pixel `i` to the nearest pixel of `blocked_px`, or a large number when none
    lies within `offsets` (which are sorted by distance)."""
    y, x = divmod(i, w)
    for dx, dy in offsets:
        if (y + dy) * w + x + dx in blocked_px:
            return math.hypot(dx, dy)
    return 1e9


HIDDEN_BEHIND_FACE = 3  # px behind a gate position where the face strip ends (steps there are not measured)


def _hidden(x, y, gates):
    """True when pixel (x, y) is in a gate's face strip: from 2 px in front of the gate position to
    HIDDEN_BEHIND_FACE px behind it, across the massif's whole width. The slab hides the middle of it; the rest is
    the mountain's front face beside the gate (the massif starts at the gate face by design), so no step is
    measured there. `gates` is a list of ((px, py), (ux, uy))."""
    for (px, py), (ux, uy) in gates:
        dx, dy = x - px, y - py
        if -2 <= dx * ux + dy * uy < HIDDEN_BEHIND_FACE and abs(dx * uy - dy * ux) <= data.MASSIF_CORE_HALF_WIDTH + data.MASSIF_FALLOFF:
            return True
    return False


def _max_step(values, w, h, pixels, gates):
    """Largest height difference between horizontally or vertically adjacent pixels, at least one of them in
    `pixels` (flat indices), leaving out pairs with a pixel hidden by a gate slab (see `_hidden`)."""
    step = 0
    for i in pixels:
        y, x = divmod(i, w)
        if _hidden(x, y, gates):
            continue
        v = values[i]
        for j, ok, nx, ny in ((i - 1, x > 0, x - 1, y), (i + 1, x + 1 < w, x + 1, y),
                              (i - w, y > 0, x, y - 1), (i + w, y + 1 < h, x, y + 1)):
            if ok and abs(values[j] - v) > step and not _hidden(nx, ny, gates):
                step = abs(values[j] - v)
    return step


def raise_heights(grid, pm, dwarven, water, impassable, sites, inset=None, overrides=None, scale=None):
    """Lift every dwarven range and give each gate a massif; returns (new grid, report).

    Per range: ground = `range_ground`, factor = `lift_factor(peak, ground)`; a pixel above the ground is
    moved to `ground + (h - ground) * factor` (soft ceiling applied, never lowered), and the change fades
    out over FADE_PX px into the surrounding land and water. Then, per gate in county order (position from
    `gate_placements` with `inset`/`overrides`, size from `gate_scale`; defaults GATE_INSET, GATE_OVERRIDES,
    GATE_SCALE), with `foot` the height at the gate pixel after the range lift (before any gate):
    1. footprint: pixels of any land (not water, not province 0) from 2 px in front of the gate to
       GATE_MODEL_DEPTH * scale + 1 px behind it and within GATE_MODEL_HALF_WIDTH * scale + 1 px of its axis are
       raised to at least `foot`, so the gate does not hover;
    2. massif: pixels of dwarven or impassable provinces blend from their height toward
       `top = soft_ceiling(foot + GATE_MODEL_HEIGHT * scale * HEIGHT_UNITS_PER_WORLD_UNIT * MASSIF_TOP_FACTOR)` by
       `massif_weight(t, l)`, also eased down over MASSIF_EDGE_FADE px toward pixels that may not change, so the
       mountain reaches the top of the gate model. Each gate blends from what the last left.
    No pixel is ever lowered; normal land, water and province 0 change only in the footprint (not water, 0).
    The report is {"ranges": [{provinces, ground, factor, peak_before, peak_after}],
    "sites": [{dwarven_county, normal_county, x, y, foot, top, massif_max, footprint_raised, step_before,
    step_after}]}; `massif_max` is the highest height among the massif's pixels, the steps the largest
    adjacent-pixel height steps in the massif after the range lift and at the end, leaving out the strips the gate
    slabs hide (see `_max_step`)."""
    inset = data.GATE_INSET if inset is None else inset
    overrides = data.GATE_OVERRIDES if overrides is None else overrides
    scale = data.GATE_SCALE if scale is None else scale
    w, h, ids = pm.width, pm.height, pm.ids
    old = grid.values
    new = array("H", old)
    dw = _lookup(dwarven)
    wat = _lookup(water)
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
    fixed = bytearray(b"\x01") * 65536  # provinces the massif may not change: normal land, water, 0
    for p in set(dwarven) | set(impassable):
        fixed[p] = 0
    land = bytearray(b"\x01") * 65536  # provinces the footprint may raise: any land
    land[0] = 0
    for p in water:
        land[p] = 0
    lifted = array("H", new)
    fade = data.MASSIF_EDGE_FADE
    offsets = sorted(((dx, dy) for dy in range(-fade, fade + 1) for dx in range(-fade, fade + 1)
                      if 0 < math.hypot(dx, dy) < fade), key=lambda o: math.hypot(*o))
    reach_px = math.ceil(math.hypot(data.MASSIF_CORE_DEPTH + data.MASSIF_FALLOFF,
                                    data.MASSIF_CORE_HALF_WIDTH + data.MASSIF_FALLOFF)) + 1
    placed = sorted(gate_placements(sites, inset, overrides),
                    key=lambda sp: (sp[0].dwarven_county, sp[0].normal_county))
    feet = []
    for site, (px, py) in placed:  # feet from the lifted ground, before any gate
        gx = min(w - 1, max(0, int(round(px))))
        gy = min(h - 1, max(0, int(round(py))))
        feet.append((gx, gy, new[gy * w + gx]))
    footprints = []
    gate_axes = []
    for (site, (px, py)), (gx, gy, foot) in zip(placed, feet):
        ux, uy = site.inward
        size = gate_scale(site, scale, overrides)
        top_height = soft_ceiling(foot + data.GATE_MODEL_HEIGHT * size * data.HEIGHT_UNITS_PER_WORLD_UNIT
                                  * data.MASSIF_TOP_FACTOR)
        x0, x1 = max(0, gx - reach_px), min(w, gx + reach_px + 1)
        y0, y1 = max(0, gy - reach_px), min(h, gy + reach_px + 1)
        fp_depth = data.GATE_MODEL_DEPTH * size + 1
        fp_half = data.GATE_MODEL_HALF_WIDTH * size + 1
        raised = 0
        weights = {}
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = y * w + x
                dx, dy = x - px, y - py
                t = dx * ux + dy * uy
                lateral = abs(dx * uy - dy * ux)
                if land[ids[i]] and -2 <= t <= fp_depth and lateral <= fp_half and new[i] < foot:
                    new[i] = foot
                    raised += 1
                if not fixed[ids[i]]:
                    weight = massif_weight(t, lateral)
                    if weight > 0:
                        weights[i] = weight
        sources = [y * w + x for y in range(max(0, y0 - fade), min(h, y1 + fade))
                   for x in range(max(0, x0 - fade), min(w, x1 + fade)) if fixed[ids[y * w + x]]]
        blocked_px = set(sources)
        top = foot
        for i, weight in weights.items():
            if blocked_px:
                weight *= min(1.0, _edge_distance(i, w, blocked_px, offsets) / fade)  # ease toward fixed pixels
            cur = new[i]
            value = int(round(cur + weight * (top_height - cur)))
            if value > cur:
                new[i] = value
            top = max(top, new[i])
        footprints.append(weights)
        gate_axes.append(((px, py), (ux, uy)))
        report["sites"].append({"dwarven_county": site.dwarven_county, "normal_county": site.normal_county,
                                "x": site.x, "y": site.y, "foot": foot, "top": top_height, "massif_max": top,
                                "footprint_raised": raised})
    for entry, weights in zip(report["sites"], footprints):
        entry["step_before"] = _max_step(lifted, w, h, weights, gate_axes)
        entry["step_after"] = _max_step(new, w, h, weights, gate_axes)
    return type(grid)(w, h, new), report


SEA_SITE_RADIUS = 6  # sea pixels within this many px of a sea gate's pixel decide which way it faces


def sea_zone_ids(text):
    """Sea zone province ids from `default.map` (lakes, rivers and impassable seas do not count)."""
    return _id_list(re.sub(r"#[^\n]*", "", text), "sea_zones")


def barony_province(titles_text, barony):
    """The `province = N` number of a barony in landed titles text."""
    m = re.search(r"\b" + re.escape(barony) + r"\s*=\s*\{[^{}]*?\bprovince\s*=\s*(\d+)", _strip(titles_text))
    if not m:
        raise GeneratorError(f"landed titles: {barony} has no province")
    return int(m.group(1))


def sea_gate_site(pm, border, sea, province, locator, county):
    """The sea gate of `province` (hold county `county`): a GateSite with normal_county "sea".

    The site is the province pixel that 4-touches a sea zone (a set of ids) nearest `locator` (x, y); `inward`
    is the unit vector from the centroid of the touching sea pixels within SEA_SITE_RADIUS px of the site to the
    site, so the gate faces the sea."""
    shore = []
    sea_px = []
    for s in sorted(sea):
        shore.extend(border.get((province, s), ()))
        sea_px.extend(border.get((s, province), ()))
    if not shore:
        raise GeneratorError(f"sea gate {county}: province {province} has no shore pixel (none touches a sea zone)")
    lx, ly = locator
    x, y = min(shore, key=lambda p: ((p[0] - lx) ** 2 + (p[1] - ly) ** 2, p[1], p[0]))
    near = [p for p in sea_px if math.hypot(p[0] - x, p[1] - y) <= SEA_SITE_RADIUS]
    cx, cy = _centroid(near)
    dx, dy = x - cx, y - cy
    length = math.hypot(dx, dy)
    if length == 0:
        raise GeneratorError(f"sea gate {county}: the shore at ({x}, {y}) has no direction toward the sea")
    return GateSite(county, "sea", x, y, (dx / length, dy / length))


def with_sea_gates(sites, counties, holds, pm, border, sea, titles_text, locators):
    """`sites` with the land sites of each hold county in `counties` replaced by one sea gate site.

    `holds` are data.holds.HOLDS-style dicts (title, barony); `locators` maps province id -> (x, y). Sites of
    other counties are returned unchanged; the sea sites come last, in the order of `counties`."""
    new = []
    for county in counties:
        entry = next((h for h in holds if h["title"] == county), None)
        if entry is None:
            raise GeneratorError(f"sea gate {county}: no dwarven hold has that county title")
        province = barony_province(titles_text, entry["barony"])
        if province not in locators:
            raise GeneratorError(f"sea gate {county}: province {province} ({entry['barony']}) has no building "
                                 f"locator")
        new.append(sea_gate_site(pm, border, sea, province, locators[province], county))
    return [s for s in sites if s.dwarven_county not in counties] + new
