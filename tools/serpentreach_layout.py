"""Serpentreach layout: EU4 Anbennar's serpentreach_region traced onto CK3 province 2426 (the Serpentspine block).

Works in map coordinates (x east, y north, y = 0 at the south edge), like tools/dwarven_mountains.py; EU4 pixels are
(x, row from the top of provinces.bmp). `layout` is deterministic: tools/build_serpentreach.py writes the province
map and scripts from it and tools/build_map_graphics.py carves the heightmap from the same result.

Spec: docs/superpowers/specs/2026-11-02-serpentreach-design.md
"""

import hashlib
import math
import re
import struct
import sys
import unicodedata
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the tools folder
from build_hud_override import GeneratorError  # noqa: E402
import dwarven_mountains as dm  # noqa: E402
import eu4_import as eu4i  # noqa: E402
from data import serpentreach as data  # noqa: E402

County = namedtuple("County", "key eu4_id name area type baronies")  # baronies: new province ids, capital first
Province = namedtuple("Province", "id colour county index pixels interior")  # pixels sorted by (y, x)
# corridor pixels (a set); mouth: the target pixel it opens onto; start: the floor pixel it leaves from
Opening = namedtuple("Opening", "county target pixels mouth start")
# links: corridors from a new county to a province it neighbours in EU4 that the trace did not reach (Segbandal)
Layout = namedtuple("Layout", "width height counties provinces owner openings area_names notes links", defaults=((),))

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
LLOYD_ROUNDS = 20


# --- pure helpers -------------------------------------------------------------------------------------------------

def _solve3(m, v):
    m = [row[:] for row in m]
    v = v[:]
    for i in range(3):
        p = max(range(i, 3), key=lambda k: abs(m[k][i]))
        m[i], m[p], v[i], v[p] = m[p], m[i], v[p], v[i]
        if abs(m[i][i]) < 1e-12:
            raise GeneratorError("affine fit is degenerate (matched points are collinear)")
        for k in range(i + 1, 3):
            f = m[k][i] / m[i][i]
            for j in range(i, 3):
                m[k][j] -= f * m[i][j]
            v[k] -= f * v[i]
    out = [0.0] * 3
    for i in (2, 1, 0):
        out[i] = (v[i] - sum(m[i][j] * out[j] for j in range(i + 1, 3))) / m[i][i]
    return tuple(out)


def fit_affine(pairs):
    """Least-squares affine (ex, ey) -> (cx, cy) from (ex, ey, cx, cy) pairs: ((ax, bx, tx), (ay, by, ty)) with
    cx = ax * ex + bx * ey + tx."""
    if len(pairs) < 3:
        raise GeneratorError(f"affine fit needs at least 3 matched provinces, got {len(pairs)}")
    m = [[0.0] * 3 for _ in range(3)]
    vx, vy = [0.0] * 3, [0.0] * 3
    for ex, ey, cx, cy in pairs:
        row = (ex, ey, 1.0)
        for i in range(3):
            vx[i] += row[i] * cx
            vy[i] += row[i] * cy
            for j in range(3):
                m[i][j] += row[i] * row[j]
    return _solve3(m, vx), _solve3(m, vy)


def apply(fit, x, y):
    (ax, bx, tx), (ay, by, ty) = fit
    return ax * x + bx * y + tx, ay * x + by * y + ty


def invert(fit):
    """The inverse affine of `fit`, in the same form."""
    (a, b, tx), (c, d, ty) = fit
    det = a * d - b * c
    if abs(det) < 1e-12:
        raise GeneratorError("affine fit is not invertible")
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    return (ia, ib, -(ia * tx + ib * ty)), (ic, id_, -(ic * tx + id_ * ty))


def slug(name):
    """A title-key fragment: accents folded, apostrophes dropped, other non-alphanumerics to single underscores."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"['‘’`]", "", s).lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def display_name(name):
    """EU4's road names `Argrod | 3 |` as `Argrod 3`; curly apostrophes made straight."""
    s = re.sub(r"\|\s*([^|]*?)\s*\|", r"\1", name)
    s = s.replace("‘", "'").replace("’", "'")
    return re.sub(r"\s+", " ", s).strip()


def _key(p):
    return p[1], p[0]


def components(pixels):
    """4-connected components of a pixel set, largest first (ties: the one holding the smallest (y, x))."""
    left = set(pixels)
    out = []
    for start in sorted(left, key=_key):
        if start not in left:
            continue
        left.discard(start)
        comp, stack = [start], [start]
        while stack:
            x, y = stack.pop()
            for dx, dy in N4:
                n = (x + dx, y + dy)
                if n in left:
                    left.discard(n)
                    comp.append(n)
                    stack.append(n)
        out.append(sorted(comp, key=_key))
    out.sort(key=lambda c: (-len(c), _key(c[0])))
    return out


def _d2(p, c):
    return (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2


def _make_connected(pieces):
    """Move every stray component of a piece to the neighbouring piece it shares most edges with."""
    for _ in range(20):
        owner = {p: i for i, piece in enumerate(pieces) for p in piece}
        moved = False
        for i, piece in enumerate(pieces):
            comps = components(piece)
            for comp in comps[1:]:
                votes = {}
                for x, y in comp:
                    for dx, dy in N4:
                        j = owner.get((x + dx, y + dy))
                        if j is not None and j != i:
                            votes[j] = votes.get(j, 0) + 1
                if not votes:
                    continue
                j = min(votes, key=lambda k: (-votes[k], k))
                for p in comp:
                    owner[p] = j
                moved = True
            if moved:
                break
        pieces = [[] for _ in pieces]
        for p, i in owner.items():
            pieces[i].append(p)
        pieces = [sorted(piece, key=_key) for piece in pieces]
        if not moved:
            return pieces
    return pieces


def split(pixels, k, min_px, label):
    """`pixels` cut into `k` 4-connected pieces by k-means (farthest-point seeds, LLOYD_ROUNDS rounds), each sorted
    by (y, x). The first piece (the capital) holds the pixel nearest the centroid (ties: smallest (y, x)); the rest
    follow by their first pixel."""
    pts = sorted(set(pixels), key=_key)
    if len(pts) < k * min_px:
        raise GeneratorError(f"{label}: {len(pts)} floor px, needs {k * min_px} for {k} baronies")
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    cap = min(pts, key=lambda p: (_d2(p, (cx, cy)), p[1], p[0]))
    if k == 1:
        return [pts]
    centers = [cap]
    nearest = {p: _d2(p, cap) for p in pts}
    while len(centers) < k:
        far = max(pts, key=lambda p: (nearest[p], -p[1], -p[0]))
        centers.append(far)
        for p in pts:
            nearest[p] = min(nearest[p], _d2(p, far))
    centers = [(float(x), float(y)) for x, y in centers]
    for _ in range(LLOYD_ROUNDS):
        groups = [[] for _ in range(k)]
        for p in pts:
            groups[min(range(k), key=lambda i: (_d2(p, centers[i]), i))].append(p)
        centers = [(sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g)) if g else centers[i]
                   for i, g in enumerate(groups)]
    groups = [g for g in _make_connected(groups) if g]
    if len(groups) < k:
        raise GeneratorError(f"{label}: only {len(groups)} of {k} baronies could be cut from its floor")
    first = next(g for g in groups if cap in set(g))
    rest = sorted((g for g in groups if g is not first), key=lambda g: _key(g[0]))
    return [first] + rest


def _disk(radius):
    r2 = radius * radius + radius
    return [(dx, dy) for dy in range(-radius, radius + 1) for dx in range(-radius, radius + 1) if dx * dx + dy * dy <= r2]


def smooth_labels(labels, radius, passes):
    """A majority (mode) filter over a disk of `radius`, `passes` times: each pixel takes the label most common
    around it, unlabelled counting as one more label; a tie keeps the pixel's own label (else the smallest). Removes
    the stair steps of an upscaled outline and stray pixels. {(x, y): label} in, the same out."""
    disk = _disk(radius)
    cur = dict(labels)
    for _ in range(passes):
        candidates = {(x + dx, y + dy) for x, y in cur for dx, dy in disk}
        nxt = {}
        for p in sorted(candidates, key=_key):
            counts = {}
            for dx, dy in disk:
                label = cur.get((p[0] + dx, p[1] + dy))
                counts[label] = counts.get(label, 0) + 1
            mine = cur.get(p)
            top = max(counts.values())
            if counts.get(mine, 0) == top:
                new = mine
            else:
                new = min((l for l, c in counts.items() if c == top), key=lambda l: (l is None, str(l)))
            if new is not None:
                nxt[p] = new
        cur = nxt
    return cur


def chamfer(sources, box, limit):
    """Chessboard (8-neighbour) distance from `sources` to every pixel within `limit` inside `box` (x0, y0, x1, y1,
    end-exclusive): {(x, y): d}."""
    x0, y0, x1, y1 = box
    dist = {p: 0 for p in sources}
    frontier = list(sources)
    for d in range(1, limit + 1):
        nxt = []
        for x, y in frontier:
            for dx, dy in N8:
                n = (x + dx, y + dy)
                if n not in dist and x0 <= n[0] < x1 and y0 <= n[1] < y1:
                    dist[n] = d
                    nxt.append(n)
        frontier = nxt
    return dist


def interior(pixels):
    """The pixel farthest (chessboard) from the piece's edge; ties: smallest (y, x)."""
    inside = set(pixels)
    edge = [p for p in pixels if any((p[0] + dx, p[1] + dy) not in inside for dx, dy in N4)]
    dist = {p: 0 for p in edge}
    frontier = edge
    d = 0
    while frontier:
        d += 1
        nxt = []
        for x, y in frontier:
            for dx, dy in N8:
                n = (x + dx, y + dy)
                if n in inside and n not in dist:
                    dist[n] = d
                    nxt.append(n)
        frontier = nxt
    return min(pixels, key=lambda p: (-dist[p], p[1], p[0]))


def colour_for(pid, used):
    """A deterministic province colour not in `used` (and never black)."""
    attempt = 0
    while True:
        h = hashlib.sha256(f"aov_serpentreach:{pid}:{attempt}".encode()).digest()
        c = (h[0], h[1], h[2])
        if c not in used and c != (0, 0, 0):
            return c
        attempt += 1


# --- EU4 ----------------------------------------------------------------------------------------------------------

class Eu4Map:
    """EU4 provinces.bmp with id lookup by (x, row from the top)."""

    def __init__(self, root: Path):
        raw = (root / "map/provinces.bmp").read_bytes()
        self.off = struct.unpack_from("<I", raw, 10)[0]
        self.width, self.height = struct.unpack_from("<ii", raw, 18)
        if struct.unpack_from("<H", raw, 28)[0] != 24:
            raise GeneratorError("EU4 provinces.bmp is not 24-bit")
        self.stride = (self.width * 3 + 3) & ~3
        self.raw = raw
        self.colours = {}
        for line in (root / "map/definition.csv").read_text(encoding="latin-1").splitlines():
            f = line.split(";")
            if len(f) > 3 and f[0].strip().isdigit():
                try:
                    self.colours[(int(f[1]), int(f[2]), int(f[3]))] = int(f[0])
                except ValueError:
                    continue

    def at(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 0
        k = self.off + (self.height - 1 - y) * self.stride + 3 * x
        b, g, r = self.raw[k:k + 3]
        return self.colours.get((r, g, b), 0)


def eu4_terrain_overrides(root: Path) -> dict:
    """EU4 province id -> terrain category from map/terrain.txt's terrain_override lists."""
    text = eu4i.strip_comments(eu4i.read_script(root / "map/terrain.txt"))
    out = {}
    for m in re.finditer(r"\n\t(\w+)\s*=\s*\{(.*?)\n\t\}", text, re.S):
        o = re.search(r"terrain_override\s*=\s*\{([^}]*)\}", m.group(2))
        if o:
            for n in re.findall(r"\d+", o.group(1)):
                out[int(n)] = m.group(1)
    return out


def _id_block(text, key):
    return {int(n) for m in re.finditer(key + r"\s*=\s*\{([^}]*)\}", text) for n in re.findall(r"\d+", m.group(1))}


def eu4_blocked(root: Path) -> set:
    """EU4 impassable (climate.txt), sea and lake provinces."""
    climate = eu4i.strip_comments(eu4i.read_script(root / "map/climate.txt"))
    default = eu4i.strip_comments(eu4i.read_script(root / "map/default.map"))
    return _id_block(climate, "impassable") | _id_block(default, "sea_starts") | _id_block(default, "lakes")


def area_order(root: Path) -> dict:
    """EU4 area key -> its province ids in area.txt order."""
    blocks = parse_area_blocks(root)
    return {area: [int(n) for n in re.findall(r"\d+", eu4i.top_level(body))] for area, body in blocks.items()}


def parse_area_blocks(root: Path) -> dict:
    return eu4i.parse_blocks(eu4i.read_script(root / "map/area.txt"))


# --- CK3 ----------------------------------------------------------------------------------------------------------

def ck3_names(definition: str) -> dict:
    out = {}
    for line in definition.lstrip("﻿").splitlines():
        f = line.split(";")
        if len(f) > 4 and f[0].strip().isdigit():
            out[int(f[0])] = f[4]
    return out


def ck3_colours(definition: str) -> set:
    out = set()
    for line in definition.lstrip("﻿").splitlines():
        f = line.split(";")
        if len(f) > 3 and f[0].strip().isdigit():
            try:
                out.add((int(f[1]), int(f[2]), int(f[3])))
            except ValueError:
                continue
    return out


def _centroids(get, box, wanted):
    x0, y0, x1, y1 = box
    acc = {}
    for y in range(y0, y1):
        for x in range(x0, x1):
            pid = get(x, y)
            if pid in wanted:
                a = acc.setdefault(pid, [0.0, 0.0, 0])
                a[0] += x + 0.5
                a[1] += y + 0.5
                a[2] += 1
    return {pid: (a[0] / a[2], a[1] / a[2]) for pid, a in acc.items()}


def _same_name(a, b):
    return bool(a and b) and slug(a)[:5] == slug(b)[:5]


# --- layout -------------------------------------------------------------------------------------------------------

def load_ck3(anbennar: Path):
    folder = anbennar / "map_data"
    for name in ("provinces.png", "definition.csv", "default.map"):
        if not (folder / name).is_file():
            raise GeneratorError(f"Anbennar not found: {folder / name} does not exist")
    definition = (folder / "definition.csv").read_bytes().decode("utf-8", errors="replace")
    pm = dm.load_province_map((folder / "provinces.png").read_bytes(), definition)
    water, impassable = dm.default_map_sets((folder / "default.map").read_text(encoding="utf-8-sig"))
    return pm, definition, water, impassable


def layout(anbennar: Path, eu4: Path, ck3=None, cfg=None, first_id=None, used=None) -> Layout:
    """A traced region's provinces on Anbennar's map. `ck3` is load_ck3(anbennar), passed when already loaded; `cfg`
    is the region's data module (default Serpentreach's); new ids start at `first_id` (default: after Anbennar's
    last) and colours avoid `used` (RGB tuples) as well as Anbennar's."""
    cfg = cfg or data
    if not (eu4 / "map/provinces.bmp").is_file():
        raise GeneratorError(f"EU4 Anbennar not found: {eu4 / 'map/provinces.bmp'} does not exist")
    pm, definition, water, impassable = ck3 or load_ck3(anbennar)
    W, H, ids = pm.width, pm.height, pm.ids
    notes = []

    def ck(x, y):
        return ids[y * W + x] if 0 <= x < W and 0 <= y < H else 0

    emap = Eu4Map(eu4)
    serp = eu4i.region_provinces((cfg.REGION,), eu4)
    if not serp:
        raise GeneratorError(f"EU4 region {cfg.REGION} has no provinces")
    enames = eu4i.province_names(eu4)
    eareas = eu4i.province_areas(eu4)
    eterrain = eu4_terrain_overrides(eu4)
    eblocked = eu4_blocked(eu4)
    loc = eu4i.eu4_loc({"anbennar": eu4})
    cnames = ck3_names(definition)

    # fit
    ex0, ey0, ex1, ey1 = cfg.FIT_BOX
    ecent = _centroids(emap.at, cfg.FIT_BOX, _AnyId())
    wanted = {pid for pid in ecent if pid not in serp and _same_name(enames.get(pid), cnames.get(pid))}
    ccent = _centroids(ck, cfg.CK3_FIT_BOX, wanted)
    pairs = [(ecent[p][0], ecent[p][1], ccent[p][0], ccent[p][1]) for p in sorted(ccent)]
    fit = fit_affine(pairs)
    res = sorted(math.dist(apply(fit, ex, ey), (cx, cy)) for ex, ey, cx, cy in pairs)
    cut = 3 * res[len(res) // 2]
    pairs = [q for q in pairs if math.dist(apply(fit, q[0], q[1]), (q[2], q[3])) <= cut]
    fit = fit_affine(pairs)
    res = sorted(math.dist(apply(fit, ex, ey), (cx, cy)) for ex, ey, cx, cy in pairs)
    notes.append(f"fit on {len(pairs)} provinces: x = {fit[0][0]:.3f} ex + {fit[0][1]:.3f} ey + {fit[0][2]:.1f}, "
                 f"y = {fit[1][0]:.3f} ex + {fit[1][1]:.3f} ey + {fit[1][2]:.1f}; residual median "
                 f"{res[len(res) // 2]:.1f} px, max {res[-1]:.1f} px")
    inv = invert(fit)

    # EU4 region pixels and entrances
    epix = {}
    contacts = {}
    for y in range(ey0, ey1):
        for x in range(ex0, ex1):
            a = emap.at(x, y)
            if a in serp:
                epix.setdefault(a, []).append((x, y))
                for dx, dy in N4:
                    b = emap.at(x + dx, y + dy)
                    if b and b not in serp and b not in eblocked:
                        contacts.setdefault((a, b), []).append((x + 0.5 + dx / 2, y + 0.5 + dy / 2))
    missing = sorted(serp - set(epix))
    if missing:
        raise GeneratorError(f"EU4 provinces of {cfg.REGION} outside FIT_BOX: {missing}")

    # CK3 box of the transformed region
    corners = [apply(fit, x, y) for x, y in ((ex0, ey0), (ex1, ey0), (ex0, ey1), (ex1, ey1))]
    xs = [min(max(int(min(c[0] for c in corners)) - 2, 0), W), min(int(max(c[0] for c in corners)) + 3, W)]
    ys = [min(max(int(min(c[1] for c in corners)) - 2, 0), H), min(int(max(c[1] for c in corners)) + 3, H)]
    box = (xs[0], ys[0], xs[1], ys[1])
    src = cfg.SOURCE_PROVINCE

    # traced floor, kept WALL_MARGIN px from every other province
    edge = []
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            if ck(x, y) != src and any(ck(x + dx, y + dy) == src for dx, dy in N8):
                edge.append((x, y))
    near = chamfer(edge, box, cfg.WALL_MARGIN - 1)
    labels = {}
    spill = {}
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            ex, ey = apply(inv, x + 0.5, y + 0.5)
            a = emap.at(int(math.floor(ex)), int(math.floor(ey)))
            if a not in serp:
                continue
            labels[(x, y)] = a
            if ck(x, y) != src:
                spill[ck(x, y)] = spill.get(ck(x, y), 0) + 1
    traced = {}
    for (x, y), a in smooth_labels(labels, cfg.SMOOTH_RADIUS, cfg.SMOOTH_PASSES).items():
        if ck(x, y) == src and (x, y) not in near:
            traced.setdefault(a, set()).add((x, y))
    if spill:
        notes.append("clipped (not province " + str(src) + "): " +
                     ", ".join(f"{cnames.get(p, p)} {n} px" for p, n in sorted(spill.items())))

    # counties in AREA_ORDER -> area.txt order (fixed, so regrouping kingdoms keeps the province ids)
    order = area_order(eu4)
    region_areas = {eareas[p] for p in serp}
    listed = list(cfg.AREA_ORDER)
    for name, areas in (("AREA_ORDER", listed), ("KINGDOMS", [a for _, (_, k) in cfg.KINGDOMS.items() for a in k])):
        if sorted(areas) != sorted(region_areas):
            raise GeneratorError(f"{name} must list exactly the areas of {cfg.REGION}: missing "
                                 f"{sorted(region_areas - set(areas))}, extra {sorted(set(areas) - region_areas)}")
    counties = []
    keys = set()
    next_id = max(cnames) + 1 if first_id is None else first_id
    used = ck3_colours(definition) | set(used or ())
    provinces = {}
    owner = {}
    for area in listed:
        for e in order[area]:
            if e not in serp:
                continue
            name = display_name(enames.get(e, f"Province {e}"))
            key = "c_" + slug(name)
            if key in keys:
                key = f"{key}_{e}"
            keys.add(key)
            kind = eterrain.get(e)
            if kind not in cfg.BARONIES:
                raise GeneratorError(f"EU4 province {e} ({name}) has terrain {kind}, not one of {sorted(cfg.BARONIES)}")
            comps = components(traced.get(e, ()))
            if not comps:
                raise GeneratorError(f"{key}: no floor left after clipping to province {src}")
            dropped = sum(len(c) for c in comps[1:])
            if dropped:
                notes.append(f"{key}: dropped {dropped} px in {len(comps) - 1} stray pieces")
            k = cfg.BARONY_OVERRIDES.get(key, cfg.BARONIES[kind])
            pieces = split(comps[0], k, cfg.MIN_BARONY_PX, key)
            pids = []
            for i, piece in enumerate(pieces):
                pid = next_id
                next_id += 1
                colour = colour_for(pid, used)
                used.add(colour)
                provinces[pid] = Province(pid, colour, key, i, piece, interior(piece))
                for p in piece:
                    owner[p] = pid
                pids.append(pid)
            counties.append(County(key, e, name, area, kind, pids))
    by_eu4 = {c.eu4_id: c for c in counties}

    # whole floor must hang together
    floor_comps = components(owner)
    if len(floor_comps) > 1:
        raise GeneratorError(f"Serpentreach floor falls apart into {len(floor_comps)} pieces; smaller ones hold "
                             + ", ".join(sorted({provinces[owner[c[0]]].county for c in floor_comps[1:]})))

    # openings
    openings = []
    for (a, b), pts in sorted(contacts.items()):
        county = by_eu4[a]
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        cx, cy = apply(fit, mx, my)
        target = cfg.OPENING_TARGETS.get((a, b))
        if target is None:
            if _same_name(enames.get(b), cnames.get(b)):
                target = b
            else:
                target = _nearest_land(ck, cx, cy, src, water, impassable)
        floor = [p for pid in county.baronies for p in provinces[pid].pixels]
        start, end, corridor = _opening(ck, floor, owner, src, target, cx, cy, cfg)
        if corridor is None and (a, b) not in cfg.OPENING_TARGETS:
            wanted = target
            for target in _land_near(ck, cx, cy, src, water, impassable, cfg.OPENING_REACH):
                start, end, corridor = _opening(ck, floor, owner, src, target, cx, cy, cfg)
                if corridor is not None:
                    notes.append(f"opening {county.key}: {cnames.get(wanted, wanted)} cannot be reached, using "
                                 f"{cnames.get(target, target)} instead")
                    break
        if corridor is None:
            if (a, b) in cfg.OPENING_TARGETS:
                raise GeneratorError(f"opening {county.key} -> {cnames.get(target, target)}: no corridor within "
                                     f"{cfg.OPENING_REACH} px touches only the target")
            notes.append(f"opening {county.key} (EU4 {a} -> {b}): no surface province reachable through province "
                         f"{src} within {cfg.OPENING_REACH} px; skipped")
            continue
        pid = owner[start]
        piece = provinces[pid]
        merged = sorted(set(piece.pixels) | corridor, key=_key)
        provinces[pid] = piece._replace(pixels=merged)
        for p in corridor:
            owner[p] = pid
        openings.append(Opening(county.key, target, corridor, end, start))
        notes.append(f"opening {county.key} -> {target} {cnames.get(target, '')}: {len(corridor)} px, "
                     f"{math.dist(start, end):.0f} px long")

    area_names = {a: display_name(loc.get(a, a)) for a in listed}
    return Layout(W, H, counties, provinces, owner, openings, area_names, notes)


class _AnyId:
    """`in` test that accepts every non-zero id (for collecting all EU4 centroids)."""

    def __contains__(self, pid):
        return pid != 0


def _nearest_land(ck, cx, cy, src, water, impassable, radius=150):
    best = None
    x0, y0 = int(cx), int(cy)
    for y in range(y0 - radius, y0 + radius + 1):
        for x in range(x0 - radius, x0 + radius + 1):
            pid = ck(x, y)
            if pid and pid != src and pid not in water and pid not in impassable:
                d = (x - cx) ** 2 + (y - cy) ** 2
                if best is None or (d, y, x) < best[0]:
                    best = ((d, y, x), pid)
    if best is None:
        raise GeneratorError(f"no land province within {radius} px of ({cx:.0f}, {cy:.0f})")
    return best[1]


def _land_near(ck, cx, cy, src, water, impassable, radius):
    """Land provinces within `radius` of (cx, cy), nearest first."""
    best = {}
    x0, y0 = int(cx), int(cy)
    for y in range(y0 - radius, y0 + radius + 1):
        for x in range(x0 - radius, x0 + radius + 1):
            pid = ck(x, y)
            if pid and pid != src and pid not in water and pid not in impassable:
                d = (x - cx) ** 2 + (y - cy) ** 2
                if pid not in best or d < best[pid]:
                    best[pid] = d
    return sorted(best, key=lambda p: (best[p], p))


def _province_pixels_near(ck, pid, cx, cy, radius):
    x0, y0 = int(cx), int(cy)
    return [(x, y) for y in range(y0 - radius, y0 + radius + 1) for x in range(x0 - radius, x0 + radius + 1)
            if ck(x, y) == pid]


# --- carving ------------------------------------------------------------------------------------------------------

def _box_around(pixels, margin, width, height):
    xs = [p[0] for p in pixels]
    ys = [p[1] for p in pixels]
    return (max(min(xs) - margin, 0), max(min(ys) - margin, 0),
            min(max(xs) + margin + 1, width), min(max(ys) + margin + 1, height))


def _nearest(sources, box, limit):
    """Euclidean distance to, and the payload of, the nearest pixel of `sources` ({(x, y): payload}) for every
    pixel within `limit` inside `box`: {(x, y): (d, payload)}. The nearest source is carried outward ring by ring
    (vector propagation); among equally near sources the largest payload wins."""
    x0, y0, x1, y1 = box
    best = {p: (0.0, v, p) for p, v in sources.items()}
    frontier = sorted(sources, key=_key)
    for _ in range(int(math.ceil(limit)) + 1):
        reached = {}
        for x, y in frontier:
            _, v, s = best[(x, y)]
            for dx, dy in N8:
                n = (x + dx, y + dy)
                if n in best or not (x0 <= n[0] < x1 and y0 <= n[1] < y1):
                    continue
                d = math.dist(n, s)
                if d > limit:
                    continue
                old = reached.get(n)
                if old is None or d < old[0] or (d == old[0] and v > old[1]):
                    reached[n] = (d, v, s)
        best.update(reached)
        frontier = sorted(reached, key=_key)
        if not frontier:
            break
    return {p: (d, v) for p, (d, v, _) in best.items()}


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def floor_heights(lay, base, grid):
    """Height of every floor pixel: base + TERRACE[type] x TERRACE_STEP, opening corridors ramping from the floor
    to the ground at their mouth."""
    county = {c.key: c for c in lay.counties}
    out = {p: base + data.TERRACE[county[lay.provinces[pid].county].type] * data.TERRACE_STEP
           for p, pid in lay.owner.items()}
    for op in lay.openings:
        outside = grid.get(*op.mouth)
        far = max(math.dist(p, op.mouth) for p in op.pixels) or 1.0
        fh = base + data.TERRACE[county[op.county].type] * data.TERRACE_STEP
        for p in op.pixels:
            out[p] = round(outside + (fh - outside) * math.dist(p, op.mouth) / far)
    return out


def carve(grid, lay, pm, water):
    """(new grid, report) with the Serpentreach floor carved into the mountain (spec §2): floors flat; within
    WALL_WIDTH (Euclidean) a smoothstep slope from the floor up to the rock, or to the rim (floor + MIN_WALL) where
    the rock is lower; beyond it, low rock fades from the rim back to its own height over WALL_FADE and is never
    lowered. Only floor and province-2426 rock pixels change."""
    import heightpack as hp
    W, H = pm.width, pm.height
    src = data.SOURCE_PROVINCE
    rock = rock_provinces()
    floor = list(lay.owner)
    near = chamfer(floor, _box_around(floor, data.CARVE_GROUND_RADIUS, W, H), data.CARVE_GROUND_RADIUS)
    ground = sorted(grid.get(x, y) for (x, y) in near
                    if pm.ids[y * W + x] != 0 and pm.ids[y * W + x] not in rock and pm.ids[y * W + x] not in water and (x, y) not in lay.owner)
    if not ground:
        raise GeneratorError(f"no land within {data.CARVE_GROUND_RADIUS} px of the Serpentreach floor")
    base = ground[len(ground) // 2]
    values = grid.values[:]
    fh = floor_heights(lay, base, grid)
    for (x, y), h in fh.items():
        values[y * W + x] = max(0, min(65535, h))
    limit = data.WALL_WIDTH + data.WALL_FADE
    walls = 0
    for (x, y), (d, h) in _nearest(fh, _box_around(floor, limit + 1, W, H), limit).items():
        i = y * W + x
        if d == 0 or pm.ids[i] not in rock or (x, y) in lay.owner:
            continue
        orig = grid.values[i]
        rim = h + data.MIN_WALL
        if d <= data.WALL_WIDTH:
            new = h + (max(orig, rim) - h) * _smooth(d / data.WALL_WIDTH)
        else:
            new = max(orig, rim + (orig - rim) * (d - data.WALL_WIDTH) / data.WALL_FADE)
        new = max(0, min(65535, round(new)))
        if new != orig:
            values[i] = new
            walls += 1
    return hp.Grid(W, H, values), {"base": base, "floor_px": len(fh), "wall_px": walls}


def check_terrain_data(area_styles, styles):
    """Stop on a style no TERRAIN_STYLES entry defines, a style key that is not a county type or "wall", or a
    default style that leaves a type out."""
    keys = set(data.BARONIES) | {"wall"}
    missing = sorted(keys - set(styles.get("default", {})))
    if missing:
        raise GeneratorError(f"TERRAIN_STYLES default lacks {', '.join(missing)}")
    for name, style in styles.items():
        bad = sorted(set(style) - keys)
        if bad:
            raise GeneratorError(f"TERRAIN_STYLES {name}: unknown keys {', '.join(bad)}")
    for area, name in area_styles.items():
        if name not in styles:
            raise GeneratorError(f"AREA_STYLES {area}: no style {name}")


def province_materials(lay, cfg=None):
    """{province id: (floor material id, wall material id)} from the county's area style (TERRAIN_STYLES,
    AREA_STYLES), with COUNTY_FLOORS and BARONY_FLOORS overriding the floor."""
    cfg = cfg or data
    check_terrain_data(cfg.AREA_STYLES, cfg.TERRAIN_STYLES)
    county = {c.key: c for c in lay.counties}
    unknown = sorted({k for k in cfg.COUNTY_FLOORS if k not in county} |
                     {k for k, i in cfg.BARONY_FLOORS if k not in county or i >= len(county[k].baronies)})
    if unknown:
        raise GeneratorError(f"COUNTY_FLOORS/BARONY_FLOORS name counties or baronies the region lacks: "
                             f"{', '.join(unknown)}")
    out = {}
    for pid, prov in lay.provinces.items():
        c = county[prov.county]
        style = {**cfg.TERRAIN_STYLES["default"], **cfg.TERRAIN_STYLES[cfg.AREA_STYLES.get(c.area, "default")]}
        floor = cfg.BARONY_FLOORS.get((c.key, prov.index)) or cfg.COUNTY_FLOORS.get(c.key) or style[c.type]
        out[pid] = (floor, style["wall"])
    return out


def used_materials(cfg=None):
    """Every material id the terrain data names, sorted."""
    cfg = cfg or data
    ids = {m for style in cfg.TERRAIN_STYLES.values() for m in style.values()}
    return sorted(ids | set(cfg.COUNTY_FLOORS.values()) | set(cfg.BARONY_FLOORS.values()))


def paint(index, intensity, lay, materials, pm=None, rock=None):
    """Copies of the blend maps (terrain_fill.Tga): floor pixels get their province's floor material from
    `materials` ({province id: (floor index, wall index)}) at full weight; wall pixels within WALL_WIDTH
    (impassable rock only when `pm` is given: `rock`, default Serpentreach's) blend the nearest floor's material
    into that province's wall material by smoothstep of the distance, full wall at WALL_WIDTH."""
    import terrain_fill as tf
    rock = rock_provinces() if rock is None else rock
    W, H = index.width, index.height
    idx = bytearray(index.pixels)
    wgt = bytearray(intensity.pixels)
    missing = sorted(set(lay.owner.values()) - set(materials))
    if missing:
        raise GeneratorError(f"no terrain material for provinces {', '.join(map(str, missing[:5]))}")
    floor = list(lay.owner)
    sources = {p: materials[pid] for p, pid in lay.owner.items()}
    for (x, y), (d, (fi, wi)) in _nearest(sources, _box_around(floor, data.WALL_WIDTH + 1, W, H),
                                          data.WALL_WIDTH).items():
        if d and pm is not None and pm.ids[y * W + x] not in rock:
            continue
        k = (y * W + x) * 4
        w = round(255 * _smooth(d / data.WALL_WIDTH))
        idx[k:k + 4] = bytes((fi, wi if d else 0, 0, 0))
        wgt[k:k + 4] = bytes((255 - w, w, 0, 0))
    return (tf.Tga(W, H, index.header, idx, index.footer), tf.Tga(W, H, intensity.header, wgt, intensity.footer))


OPENING_TRIES = 400


def rock_provinces(cfg=None):
    """Impassable provinces whose pixels the floor and its corridors may take and whose rock gets walls."""
    cfg = cfg or data
    return {cfg.SOURCE_PROVINCE} | set(cfg.OPENING_CUT_THROUGH)


def _opening(ck, floor, owner, src, target, cx, cy, cfg=None):
    """(start, end, corridor) of the shortest corridor from `floor` to `target` that touches no province but the
    target and `src`; corridor None when none is found. Candidate ends are the target's pixels in order of their
    distance to the floor."""
    cfg = cfg or data
    tpix = _province_pixels_near(ck, target, cx, cy, 250)
    if not tpix:
        raise GeneratorError(f"opening to {target}: no pixel of the target within 250 px of ({cx:.0f}, {cy:.0f})")
    xs = [p[0] for p in floor]
    ys = [p[1] for p in floor]
    box = (min(xs) - cfg.OPENING_REACH, min(ys) - cfg.OPENING_REACH, max(xs) + cfg.OPENING_REACH + 1, max(ys) + cfg.OPENING_REACH + 1)
    dist = chamfer(floor, box, cfg.OPENING_REACH)
    ends = sorted((t for t in tpix if t in dist), key=lambda t: (dist[t], t[1], t[0]))
    rock = rock_provinces(cfg)
    tried = set()
    for end in ends[:OPENING_TRIES]:
        start = min(floor, key=lambda p: (_d2(p, end), p[1], p[0]))
        if (start, end) in tried:
            continue
        tried.add((start, end))
        corridor = _corridor(start, end, cfg.OPENING_WIDTH / 2, lambda p: ck(*p) in rock and p not in owner)
        touched = {ck(x + dx, y + dy) for x, y in corridor for dx, dy in N4}
        if target in touched and not (touched - rock - {target, 0}) and _joins(corridor, start):
            return start, end, corridor
    return None, None, None


def _joins(corridor, start):
    """The corridor is one 4-connected piece touching the start pixel."""
    comps = components(corridor)
    return len(comps) == 1 and any((start[0] + dx, start[1] + dy) in corridor for dx, dy in N4)


def _corridor(start, end, half, allowed):
    """Pixels within `half` of the segment start-end (pixel centres) for which `allowed` holds."""
    (sx, sy), (tx, ty) = start, end
    vx, vy = tx - sx, ty - sy
    ll = vx * vx + vy * vy or 1
    r = int(math.ceil(half)) + 1
    out = set()
    for y in range(min(sy, ty) - r, max(sy, ty) + r + 1):
        for x in range(min(sx, tx) - r, max(sx, tx) + r + 1):
            t = max(0.0, min(1.0, ((x - sx) * vx + (y - sy) * vy) / ll))
            if math.dist((x, y), (sx + t * vx, sy + t * vy)) <= half and allowed((x, y)):
                out.add((x, y))
    return out
