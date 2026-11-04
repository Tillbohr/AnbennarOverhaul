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
# links: corridors from a new county to a province it neighbours in EU4 that the trace did not reach (Segbandal), or
# that EU4 joins to it only through adjacencies.csv (West Dwarovar's Dwarovrod 24 -> 25); mouths: where a cave floor
# meets a surface county (Serpent's Vale), `target` that county's capital barony
Layout = namedtuple("Layout", "width height counties provinces owner openings area_names notes links mouths",
                    defaults=((), ()))

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


def separate_non_neighbours(labels, adj, margin):
    """`labels` ({(x, y): EU4 id}) less every pixel with a pixel of another label within margin // 2 px (chessboard)
    that EU4 does not make its neighbour (`adj`, EU4 id -> set of EU4 ids): a `margin` px seam of rock between them.
    EU4 provinces that meet only at a corner, or a pixel apart, merge once scaled and smoothed."""
    gap = margin // 2
    out = {}
    for (x, y), a in labels.items():
        nbrs = adj.get(a, ())
        if not any(b is not None and b != a and b not in nbrs
                   for b in (labels.get((x + dx, y + dy)) for dx in range(-gap, gap + 1) for dy in range(-gap, gap + 1))):
            out[(x, y)] = a
    return out


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


def county_provinces(titles_text):
    """{county key: set of province ids} from landed titles text."""
    out = {}
    for pid, (_, _, county) in dm.province_titles(titles_text).items():
        if county:
            out.setdefault(county, set()).add(pid)
    return out


def allowed_neighbours(adj, existing, county_provinces):
    """{EU4 id: CK3 province ids its floor may touch}: the provinces of the Anbennar counties (`existing`, EU4 id ->
    county) of its EU4 neighbours (`adj`, EU4 id -> set of EU4 ids)."""
    return {a: {pid for b in sorted(nbrs) if b in existing for pid in county_provinces[existing[b]]}
            for a, nbrs in adj.items()}


AVOIDED = -1  # province id an `avoid` pixel (an earlier region's floor, still rock on Anbennar's map) reads as


def overlay(ck, avoid):
    """`ck` with the `avoid` pixels reading as other provinces: a dict gives each its province id (earlier layouts'
    `owner` maps), a set reads as AVOIDED. Earlier floors are still rock on Anbennar's map, so without this a new
    floor or corridor could run into them."""
    if not avoid:
        return ck
    get = avoid.get if isinstance(avoid, dict) else (lambda p: AVOIDED if p in avoid else None)

    def wrapped(x, y):
        pid = get((x, y))
        return ck(x, y) if pid is None else pid
    return wrapped


def clip_floor(labels, ck, box, src, margin, allowed, avoid=None):
    """{label: set of floor pixels}: a labelled pixel is floor when it is on `src` and every other province within
    `margin` - 1 px (chessboard) of it is one its label may touch (`allowed`, label -> province ids). `avoid` pixels
    (see `overlay`) count as other provinces."""
    ck = overlay(ck, avoid)
    groups = {}
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            pid = ck(x, y)
            if pid != src and any(ck(x + dx, y + dy) == src for dx, dy in N8):
                groups.setdefault(pid, []).append((x, y))
    near = {}
    for pid, edge in groups.items():
        x0, y0, x1, y1 = _box_around(edge, margin, box[2], box[3])
        for p in chamfer(edge, (max(x0, box[0]), max(y0, box[1]), x1, y1), margin - 1):
            near.setdefault(p, set()).add(pid)
    out = {}
    for p, a in labels.items():
        if ck(*p) == src and near.get(p, set()) <= allowed.get(a, set()):
            out.setdefault(a, set()).add(p)
    return out


# --- layout -------------------------------------------------------------------------------------------------------

def region_set(cfg, eu4: Path):
    """(EU4 provinces to trace, label): those of `cfg.REGIONS` (else `cfg.REGION`) less `cfg.EXCLUDE_AREAS`'s. Stops
    on an excluded area that is not one of the regions'."""
    regions = tuple(getattr(cfg, "REGIONS", None) or (cfg.REGION,))
    label = "/".join(regions)
    provinces = eu4i.region_provinces(regions, eu4)
    if not provinces:
        raise GeneratorError(f"EU4 region {label} has no provinces")
    excluded = tuple(getattr(cfg, "EXCLUDE_AREAS", ()))
    if excluded:
        areas = eu4i.province_areas(eu4)
        unknown = sorted(set(excluded) - {areas.get(p) for p in provinces})
        if unknown:
            raise GeneratorError(f"EXCLUDE_AREAS names areas not in {label}: {', '.join(unknown)}")
        provinces = {p for p in provinces if areas.get(p) not in excluded}
    return provinces, label


def county_type(kind, area, cfg, key):
    """(county type, barony count) of a traced province with EU4 terrain `kind`: a cave kind of `cfg.BARONIES`, or
    "surface" (`cfg.SURFACE_BARONIES`) for any other terrain in one of `cfg.SURFACE_AREAS`; stops otherwise."""
    if kind in cfg.BARONIES:
        return kind, cfg.BARONIES[kind]
    if area in tuple(getattr(cfg, "SURFACE_AREAS", ())):
        return "surface", getattr(cfg, "SURFACE_BARONIES", 3)
    raise GeneratorError(f"{key}: EU4 terrain {kind} is not one of {sorted(cfg.BARONIES)} and its area {area} is "
                         "not in SURFACE_AREAS")


def load_ck3(anbennar: Path):
    folder = anbennar / "map_data"
    for name in ("provinces.png", "definition.csv", "default.map"):
        if not (folder / name).is_file():
            raise GeneratorError(f"Anbennar not found: {folder / name} does not exist")
    definition = (folder / "definition.csv").read_bytes().decode("utf-8", errors="replace")
    pm = dm.load_province_map((folder / "provinces.png").read_bytes(), definition)
    water, impassable = dm.default_map_sets((folder / "default.map").read_text(encoding="utf-8-sig"))
    return pm, definition, water, impassable


def layout(anbennar: Path, eu4: Path, ck3=None, cfg=None, first_id=None, used=None, avoid=None,
           targets=None) -> Layout:
    """A traced region's provinces on Anbennar's map. `ck3` is load_ck3(anbennar), passed when already loaded; `cfg`
    is the region's data module (default Serpentreach's); new ids start at `first_id` (default: after Anbennar's
    last) and colours avoid `used` (RGB tuples) as well as Anbennar's. `avoid` holds earlier layouts' floor pixels
    (see `overlay`): the new floor keeps WALL_MARGIN from them and no corridor runs into them. `targets` maps EU4 ids
    to the CK3 provinces earlier layouts drew for them: with `cfg.LINK_REACH` set, an EU4 adjacencies.csv pair from a
    traced province to one of them (or to an EXISTING county) gets a tunnel (`adjacency_links`)."""
    cfg = cfg or data
    if not (eu4 / "map/provinces.bmp").is_file():
        raise GeneratorError(f"EU4 Anbennar not found: {eu4 / 'map/provinces.bmp'} does not exist")
    pm, definition, water, impassable = ck3 or load_ck3(anbennar)
    W, H, ids = pm.width, pm.height, pm.ids
    notes = []

    def ck_map(x, y):
        return ids[y * W + x] if 0 <= x < W and 0 <= y < H else 0
    ck = overlay(ck_map, avoid)
    if avoid:
        impassable = set(impassable) | (set(avoid.values()) if isinstance(avoid, dict) else {AVOIDED})

    emap = Eu4Map(eu4)
    serp, label = region_set(cfg, eu4)
    excluded = eu4i.region_provinces(tuple(getattr(cfg, "REGIONS", None) or (cfg.REGION,)), eu4) - serp
    enames = eu4i.province_names(eu4)
    eareas = eu4i.province_areas(eu4)
    eterrain = eu4_terrain_overrides(eu4)
    eblocked = eu4_blocked(eu4)
    loc = eu4i.eu4_loc({"anbennar": eu4})
    cnames = ck3_names(definition)
    # EU4 provinces Anbennar already has (Segbandal) are not traced; new floors may touch their CK3 provinces
    existing = dict(getattr(cfg, "EXISTING", {}))
    cprov = {}
    if existing:
        cprov = county_provinces("\n".join(p.read_text(encoding="utf-8-sig", errors="replace")
                                            for p in sorted((anbennar / "common/landed_titles").glob("*.txt"))))
        lost = sorted({c for c in existing.values() if c not in cprov})
        if lost:
            raise GeneratorError(f"EXISTING names counties Anbennar no longer has: {', '.join(lost)}")
    no_link = tuple(getattr(cfg, "NO_LINK_REGIONS", ()))
    nolink = (eu4i.region_provinces(no_link, eu4) if no_link else set()) | excluded  # excluded areas: no opening

    # fit
    ex0, ey0, ex1, ey1 = cfg.FIT_BOX
    ecent = _centroids(emap.at, cfg.FIT_BOX, _AnyId())
    wanted = {pid for pid in ecent if pid not in serp and _same_name(enames.get(pid), cnames.get(pid))}
    ccent = _centroids(ck_map, cfg.CK3_FIT_BOX, wanted)
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
    adj = {}
    for y in range(ey0, ey1):
        for x in range(ex0, ex1):
            a = emap.at(x, y)
            if a in serp:
                epix.setdefault(a, []).append((x, y))
                for dx, dy in N4:
                    b = emap.at(x + dx, y + dy)
                    if b in serp and b != a:
                        adj.setdefault(a, set()).add(b)
                    elif b and b not in serp and b not in eblocked and b not in nolink and a not in existing:
                        contacts.setdefault((a, b), []).append((x + 0.5 + dx / 2, y + 0.5 + dy / 2))
    missing = sorted(serp - set(epix))
    if missing:
        raise GeneratorError(f"EU4 provinces of {label} outside FIT_BOX: {missing}")

    # CK3 box of the transformed region
    corners = [apply(fit, x, y) for x, y in ((ex0, ey0), (ex1, ey0), (ex0, ey1), (ex1, ey1))]
    xs = [min(max(int(min(c[0] for c in corners)) - 2, 0), W), min(int(max(c[0] for c in corners)) + 3, W)]
    ys = [min(max(int(min(c[1] for c in corners)) - 2, 0), H), min(int(max(c[1] for c in corners)) + 3, H)]
    box = (xs[0], ys[0], xs[1], ys[1])
    src = cfg.SOURCE_PROVINCE

    # traced floor, kept WALL_MARGIN px from every other province but the EU4 neighbours Anbennar already has
    labels = {}
    spill = {}
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            ex, ey = apply(inv, x + 0.5, y + 0.5)
            a = emap.at(int(math.floor(ex)), int(math.floor(ey)))
            if a not in serp or a in existing:
                continue
            labels[(x, y)] = a
            if ck(x, y) != src:
                spill[ck(x, y)] = spill.get(ck(x, y), 0) + 1
    allowed = allowed_neighbours(adj, existing, cprov)
    smoothed = smooth_labels(labels, cfg.SMOOTH_RADIUS, cfg.SMOOTH_PASSES)
    if getattr(cfg, "SEPARATE_NON_NEIGHBOURS", False):
        smoothed = separate_non_neighbours(smoothed, adj, cfg.WALL_MARGIN)
    traced = clip_floor(smoothed, ck, box, src, cfg.WALL_MARGIN, allowed)
    if spill:
        notes.append("clipped (not province " + str(src) + "): " +
                     ", ".join(f"{cnames.get(p, p)} {n} px" for p, n in sorted(spill.items())))

    # counties in AREA_ORDER -> area.txt order (fixed, so regrouping kingdoms keeps the province ids)
    order = area_order(eu4)
    region_areas = {eareas[p] for p in serp}
    listed = list(cfg.AREA_ORDER)
    for name, areas in (("AREA_ORDER", listed), ("KINGDOMS", [a for _, (_, k) in cfg.KINGDOMS.items() for a in k])):
        if sorted(areas) != sorted(region_areas):
            raise GeneratorError(f"{name} must list exactly the areas of {label}: missing "
                                 f"{sorted(region_areas - set(areas))}, extra {sorted(set(areas) - region_areas)}")
    if existing:
        # an EU4 province Anbennar has since added as its own county must join EXISTING, not be traced twice
        box_ids = {ck(x, y) for y in range(box[1], box[3]) for x in range(box[0], box[2])}
        local = {c for c, pids in cprov.items() if pids & box_ids}
        candidates = [(e, "c_" + slug(display_name(enames.get(e, f"Province {e}"))),
                       display_name(enames.get(e, f"Province {e}")))
                      for area in listed for e in order[area] if e in serp and e not in existing]
        dup = anbennar_duplicates(candidates, cnames, local)
        if dup:
            raise GeneratorError(f"Anbennar now has {', '.join(dup)}; add them to EXISTING")
    counties = []
    keys = set()
    next_id = max(cnames) + 1 if first_id is None else first_id
    used = ck3_colours(definition) | set(used or ())
    provinces = {}
    owner = {}
    for area in listed:
        for e in order[area]:
            if e not in serp or e in existing:
                continue
            name = display_name(enames.get(e, f"Province {e}"))
            key = "c_" + slug(name)
            if key in keys:
                key = f"{key}_{e}"
            keys.add(key)
            kind, count = county_type(eterrain.get(e), area, cfg, f"EU4 province {e} ({name})")
            comps = components(traced.get(e, ()))
            if not comps:
                raise GeneratorError(f"{key}: no floor left after clipping to province {src}")
            dropped = sum(len(c) for c in comps[1:])
            if dropped:
                notes.append(f"{key}: dropped {dropped} px in {len(comps) - 1} stray pieces")
            k = cfg.BARONY_OVERRIDES.get(key, count)
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

    # whole floor must hang together (with Anbennar's provinces, when the region completes them: checked below)
    floor_comps = components(owner)
    if len(floor_comps) > 1 and not existing:
        raise GeneratorError(f"Serpentreach floor falls apart into {len(floor_comps)} pieces; smaller ones hold "
                             + ", ".join(sorted({provinces[owner[c[0]]].county for c in floor_comps[1:]})))

    # openings
    openings = []
    for (a, b), pts in sorted(contacts.items()):
        if dropped_pair(cfg, a, b):
            notes.append(f"opening EU4 {a} -> {b}: in NO_LINK_PAIRS; skipped")
            continue
        county = by_eu4[a]
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        cx, cy = apply(fit, mx, my)
        target = cfg.OPENING_TARGETS.get((a, b))
        if target is None:
            if _same_name(enames.get(b), cnames.get(b)):
                target = b
            else:
                try:
                    target = _nearest_land(ck, cx, cy, src, water, impassable)
                except GeneratorError:
                    target = None  # the EU4 neighbour is off the CK3 map (West Dwarovar's Eastnest): skipped below
        floor = [p for pid in county.baronies for p in provinces[pid].pixels]
        start, end, corridor = (None, None, None) if target is None else _opening(ck, floor, owner, src, target, cx,
                                                                                   cy, cfg)
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

    links = []
    if getattr(cfg, "LINK_REACH", None):
        tmap = {b: set(pids) for b, pids in (targets or {}).items()}
        tmap.update({e: set(cprov[c]) for e, c in existing.items()})
        pairs = {(a, b) for a, b in eu4_adjacencies(eu4) if a in by_eu4 and b in tmap}
        links += adjacency_links(ck, counties, provinces, owner, pairs, tmap, src, cfg, notes)
        for a, b in pairs:
            allowed.setdefault(a, set()).update(tmap[b])
    if existing:
        links += _links(ck, counties, provinces, owner, adj, allowed, src, cfg, notes)
        old = {pid for c in set(existing.values()) for pid in cprov[c]}
        old_px = {(x, y) for y in range(box[1], box[3]) for x in range(box[0], box[2]) if ck(x, y) in old}
        links += join_pieces(ck, counties, provinces, owner, allowed, old_px, src, cfg, notes)
        comps = components(set(owner) | old_px)
        if len(comps) > 1:
            cut = sorted({provinces[owner[p]].county for c in comps if not any(ck(*q) in old for q in c)
                          for p in c if p in owner})
            raise GeneratorError(f"{label}: floor falls apart into {len(comps)} pieces; cut off: {', '.join(cut)}")
        # corridors may reach what the trace kept apart: no new floor may touch a county or Anbennar province EU4
        # does not make its neighbour
        bad = foreign_contacts(ck, owner, provinces, counties, adj, allowed, old)
        if bad:
            raise GeneratorError(f"{label}: floors touch what EU4 does not make their neighbours: "
                                 + ", ".join(f"{a} -> {b}" for a, b in bad[:10]))

    area_names = {a: display_name(loc.get(a, a)) for a in listed}
    found = mouths(counties, provinces, owner, cfg)
    for m in found:
        notes.append(f"mouth {m.county} -> {provinces[m.target].county}: {len(m.pixels)} floor px")
    return Layout(W, H, counties, provinces, owner, openings, area_names, notes, links, found)


def foreign_contacts(ck, owner, provinces, counties, adj, allowed, watched):
    """Sorted (county, other) pairs where a new floor pixel 4-touches another new county (`other` its key) or a
    `watched` province (`other` its id) that its EU4 province does not neighbour (`adj`, `allowed`)."""
    eu4_of = {c.key: c.eu4_id for c in counties}
    out = set()
    for (x, y), pid in owner.items():
        a = provinces[pid].county
        for dx, dy in N4:
            n = (x + dx, y + dy)
            if n in owner:
                b = provinces[owner[n]].county
                if b != a and eu4_of[b] not in adj.get(eu4_of[a], set()):
                    out.add((a, b))
            else:
                q = ck(*n)
                if q in watched and q not in allowed.get(eu4_of[a], set()):
                    out.add((a, q))
    return sorted(out, key=lambda ab: (ab[0], str(ab[1])))


def anbennar_duplicates(candidates, cnames, local_counties):
    """Traced EU4 provinces Anbennar already has: `candidates` (EU4 id, county key, name) whose id names the same
    province in CK3's definition.csv (`cnames`), or whose key matches a nearby Anbennar county ignoring underscores."""
    squashed = {c.replace("_", ""): c for c in local_counties}
    out = []
    for e, key, name in candidates:
        if _same_name(name, cnames.get(e)):
            out.append(f"{key} (province {e})")
        elif key.replace("_", "") in squashed:
            out.append(f"{key} ({squashed[key.replace('_', '')]})")
    return out


def join_pieces(ck, counties, provinces, owner, allowed, old_px, src, cfg, notes, link=None):
    """Link every floor piece holding no pixel of `old_px` (Anbennar's provinces) to them, one corridor at a time;
    stops when a piece has no corridor or comes back unchanged after its corridor."""
    link = link or _piece_link
    links = []
    seen = set()
    while True:
        comps = components(set(owner) | old_px)
        loose = [c for c in comps if not any(p in old_px for p in c)]
        if not loose:
            return links
        piece = frozenset(provinces[owner[p]].county for p in loose[0] if p in owner)
        if piece in seen:
            raise GeneratorError(f"linking {', '.join(sorted(piece))} to Anbennar's provinces made no progress")
        seen.add(piece)
        made = link(ck, loose[0], counties, provinces, owner, allowed, src, cfg)
        if made is None:
            return links
        links.append(made)
        notes.append(f"link {made.county} -> {made.target}: {len(made.pixels)} px (joins a cut-off piece)")


def _attach(provinces, owner, start, corridor):
    pid = owner[start]
    piece = provinces[pid]
    provinces[pid] = piece._replace(pixels=sorted(set(piece.pixels) | corridor, key=_key))
    for p in corridor:
        owner[p] = pid


def _piece_link(ck, piece, counties, provinces, owner, allowed, src, cfg):
    """The shortest corridor from any county of a floor piece cut off from Anbennar's provinces to an Anbennar
    province one of those counties neighbours in EU4; None when there is none."""
    inside = {provinces[owner[p]].county for p in piece if p in owner}
    best = None
    for c in counties:
        if c.key not in inside:
            continue
        floor = [p for pid in c.baronies for p in provinces[pid].pixels]
        cx = sum(p[0] for p in floor) / len(floor)
        cy = sum(p[1] for p in floor) / len(floor)
        for target in sorted(allowed.get(c.eu4_id, ())):
            try:
                start, end, corridor = _opening(ck, floor, owner, src, target, cx, cy, cfg)
            except GeneratorError:
                continue
            if corridor is not None and (best is None or len(corridor) < len(best[4])):
                best = (c.key, target, start, end, corridor)
    if best is None:
        return None
    key, target, start, end, corridor = best
    _attach(provinces, owner, start, corridor)
    return Opening(key, target, corridor, end, start)


def _links(ck, counties, provinces, owner, adj, allowed, src, cfg, notes):
    """Corridors from each new county that touches none of its EU4 neighbours (Anbennar's provinces in `allowed`,
    or other new counties) to the nearest reachable province of an Anbennar neighbour; pixels join the barony they
    leave from. Stops when a county has none within OPENING_REACH."""
    eu4_of = {c.key: c.eu4_id for c in counties}
    links = []
    for c in counties:
        floor = [p for pid in c.baronies for p in provinces[pid].pixels]
        nbrs = adj.get(c.eu4_id, set())
        ok = allowed.get(c.eu4_id, set())
        touches = False
        for x, y in floor:
            for dx, dy in N4:
                n = (x + dx, y + dy)
                if n in owner:
                    other = provinces[owner[n]].county
                    touches = other != c.key and eu4_of[other] in nbrs
                else:
                    touches = ck(*n) in ok
                if touches:
                    break
            if touches:
                break
        if touches:
            continue
        cx = sum(p[0] for p in floor) / len(floor)
        cy = sum(p[1] for p in floor) / len(floor)
        best = None
        for target in sorted(ok):
            try:
                start, end, corridor = _opening(ck, floor, owner, src, target, cx, cy, cfg)
            except GeneratorError:
                continue
            if corridor is not None and (best is None or len(corridor) < len(best[3])):
                best = (target, start, end, corridor)
        if best is None:
            raise GeneratorError(f"{c.key}: touches none of its EU4 neighbours and no corridor within "
                                 f"{cfg.OPENING_REACH} px reaches one")
        target, start, end, corridor = best
        _attach(provinces, owner, start, corridor)
        links.append(Opening(c.key, target, corridor, end, start))
        notes.append(f"link {c.key} -> {target}: {len(corridor)} px")
    return links


def dropped_pair(cfg, a, b):
    """The EU4 pair (either order) is in `cfg.NO_LINK_PAIRS`: no opening, link or mouth between them."""
    pairs = getattr(cfg, "NO_LINK_PAIRS", ()) or ()
    return (a, b) in pairs or (b, a) in pairs


def eu4_adjacencies(eu4: Path) -> set:
    """{(from, to)} EU4 province pairs of map/adjacencies.csv, both directions."""
    out = set()
    for line in (eu4 / "map/adjacencies.csv").read_text(encoding="latin-1").splitlines():
        f = line.split(";")
        if len(f) > 2 and f[0].strip().isdigit() and f[1].strip().isdigit():
            a, b = int(f[0]), int(f[1])
            if a > 0 and b > 0:
                out |= {(a, b), (b, a)}
    return out


def mouths(counties, provinces, owner, cfg):
    """One Opening per (cave county, surface county) whose floors touch: `target` the surface county's capital
    barony, `mouth` the surface pixel nearest the middle of the contact, `start` the floor pixel beside it (smallest
    (y, x)), `pixels` the cave county's floor within OPENING_WIDTH of the mouth."""
    county = {c.key: c for c in counties}
    contact = {}
    for (x, y), pid in owner.items():
        a = county[provinces[pid].county]
        if a.type == "surface":
            continue
        for dx, dy in N4:
            q = owner.get((x + dx, y + dy))
            if q is not None and county[provinces[q].county].type == "surface":
                contact.setdefault((a.key, provinces[q].county), set()).add((x + dx, y + dy))
    out = []
    for (ckey, skey), pts in sorted(contact.items()):
        if dropped_pair(cfg, county[ckey].eu4_id, county[skey].eu4_id):
            continue
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        mouth = min(pts, key=lambda p: (_d2(p, (mx, my)), p[1], p[0]))
        floor = {p for pid in county[ckey].baronies for p in provinces[pid].pixels}
        start = min(((mouth[0] + dx, mouth[1] + dy) for dx, dy in N4 if (mouth[0] + dx, mouth[1] + dy) in floor),
                    key=_key)
        pixels = {p for p in floor if math.dist(p, mouth) <= cfg.OPENING_WIDTH}
        out.append(Opening(ckey, county[skey].baronies[0], pixels, mouth, start))
    return out


def adjacency_links(ck, counties, provinces, owner, pairs, targets, src, cfg, notes):
    """A corridor OPENING_WIDTH wide, at most LINK_REACH px, from each new county to the CK3 provinces (`targets`,
    EU4 id -> province ids) of an EU4 province it is joined to only by `pairs` (EU4 adjacencies.csv), through `src`
    and LINK_CUT_THROUGH; pixels join the barony they leave from. Stops when one has no corridor in reach."""
    by_eu4 = {c.eu4_id: c for c in counties}
    rock = {src} | set(getattr(cfg, "LINK_CUT_THROUGH", ()))
    links = []
    for a, b in sorted(pairs):
        if a not in by_eu4 or b not in targets or dropped_pair(cfg, a, b):
            continue
        c = by_eu4[a]
        floor = [p for pid in c.baronies for p in provinces[pid].pixels]
        cx = sum(p[0] for p in floor) / len(floor)
        cy = sum(p[1] for p in floor) / len(floor)
        ok = set(targets[b])
        best = None
        for target in sorted(ok):
            try:
                start, end, corridor = _opening(ck, floor, owner, src, target, cx, cy, cfg, reach=cfg.LINK_REACH,
                                                rock=rock, ok=ok)
            except GeneratorError:
                continue
            if corridor is not None and (best is None or len(corridor) < len(best[3])):
                best = (target, start, end, corridor)
        if best is None:  # land in the way of every straight tunnel: route one through the rock around it
            start, end, corridor = _routed_corridor(ck, floor, owner, ok, rock, cfg.OPENING_WIDTH / 2, cfg.LINK_REACH)
            if corridor is not None:
                best = (ck(*end), start, end, corridor)
                notes.append(f"tunnel {c.key}: no straight way, routed around land")
        if best is None:
            raise GeneratorError(f"{c.key}: no tunnel within LINK_REACH {cfg.LINK_REACH} px reaches EU4 {b}'s "
                                 f"provinces {sorted(ok)}")
        target, start, end, corridor = best
        _attach(provinces, owner, start, corridor)
        links.append(Opening(c.key, target, corridor, end, start))
        notes.append(f"tunnel {c.key} -> {target} (EU4 {a} -> {b}): {len(corridor)} px, "
                     f"{math.dist(start, end):.0f} px long")
    return links


def _routed_corridor(ck, floor, owner, ok, rock, half, reach):
    """(start, end, corridor) of a bent corridor from `floor` to a pixel of an `ok` province: the shortest 8-connected
    path (at most `reach` steps) through rock pixels (`rock`, not in `owner`) that keep ceil(half) + 1 px (chessboard)
    from every pixel that is neither rock, nor the floor, nor `ok`, widened to `half`. (None, None, None) when there
    is none."""
    fl = set(floor)
    xs = [p[0] for p in floor]
    ys = [p[1] for p in floor]
    box = (min(xs) - reach, min(ys) - reach, max(xs) + reach + 1, max(ys) + reach + 1)
    clearance = int(math.ceil(half)) + 1

    def passable(p):
        return ck(*p) in rock and p not in owner
    blocked = []
    goal = set()
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            pid = ck(x, y)
            if pid in ok:
                goal.add((x, y))
            elif pid != 0 and (x, y) not in fl and not passable((x, y)):
                blocked.append((x, y))
    if not goal:
        return None, None, None
    near = chamfer(blocked, box, clearance)
    sources = sorted({(x + dx, y + dy) for x, y in fl for dx, dy in N4
                      if passable((x + dx, y + dy)) and (x + dx, y + dy) not in near}, key=_key)
    parent = {p: None for p in sources}
    frontier = sources
    found = None
    for _ in range(reach + 1):
        for p in frontier:
            if any((p[0] + dx, p[1] + dy) in goal for dx, dy in N4):
                found = p
                break
        if found is not None:
            break
        nxt = []
        for x, y in frontier:
            for dx, dy in N8:
                n = (x + dx, y + dy)
                if n not in parent and box[0] <= n[0] < box[2] and box[1] <= n[1] < box[3] and passable(n) \
                        and n not in near:
                    parent[n] = (x, y)
                    nxt.append(n)
        frontier = nxt
        if not frontier:
            break
    if found is None:
        return None, None, None
    path = [found]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    first = path[-1]
    start = min(((first[0] + dx, first[1] + dy) for dx, dy in N4 if (first[0] + dx, first[1] + dy) in fl), key=_key)
    end = min(((found[0] + dx, found[1] + dy) for dx, dy in N4 if (found[0] + dx, found[1] + dy) in goal), key=_key)
    r = int(math.ceil(half))
    corridor = {(x + dx, y + dy) for x, y in path for dx, dy in _disk(r)
                if dx * dx + dy * dy <= half * half and passable((x + dx, y + dy))}
    touched = {ck(x + dx, y + dy) for x, y in corridor for dx, dy in N4}
    if not (touched & set(ok)) or (touched - set(rock) - set(ok) - {0}) or not _joins(corridor, start):
        return None, None, None
    return start, end, corridor


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


def _opening(ck, floor, owner, src, target, cx, cy, cfg=None, reach=None, rock=None, ok=()):
    """(start, end, corridor) of the shortest corridor from `floor` to `target` that touches no province but the
    target, `ok` and the rock (`rock`, default `rock_provinces(cfg)`) and runs at most `reach` (default OPENING_REACH)
    px; corridor None when none is found. Candidate ends are the target's pixels in order of their distance to the
    floor."""
    cfg = cfg or data
    reach = cfg.OPENING_REACH if reach is None else reach
    tpix = _province_pixels_near(ck, target, cx, cy, 250)
    if not tpix:
        raise GeneratorError(f"opening to {target}: no pixel of the target within 250 px of ({cx:.0f}, {cy:.0f})")
    xs = [p[0] for p in floor]
    ys = [p[1] for p in floor]
    box = (min(xs) - reach, min(ys) - reach, max(xs) + reach + 1, max(ys) + reach + 1)
    dist = chamfer(floor, box, reach)
    ends = sorted((t for t in tpix if t in dist), key=lambda t: (dist[t], t[1], t[0]))
    rock = rock_provinces(cfg) if rock is None else set(rock)
    tried = set()
    for end in ends[:OPENING_TRIES]:
        start = min(floor, key=lambda p: (_d2(p, end), p[1], p[0]))
        if (start, end) in tried:
            continue
        tried.add((start, end))
        corridor = _corridor(start, end, cfg.OPENING_WIDTH / 2, lambda p: ck(*p) in rock and p not in owner)
        touched = {ck(x + dx, y + dy) for x, y in corridor for dx, dy in N4}
        if target in touched and not (touched - rock - {target, 0} - set(ok)) and _joins(corridor, start):
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
