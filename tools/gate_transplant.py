"""The Erebor transplant: Realms in Exile's Erebor gate composition copied to every dwarven gate.

RiE's Erebor gate stands in a small, specific composition: a narrow steep terrain cone starting at the gate face, ten
mountain pieces (a draped rock skin) and three mesa rocks around it. `extract_composition` reads that from RiE's map
object data and heightmap, in the Erebor gate's frame (t along the gate's inward axis, l to its right, in RiE map
units). `transplant` stamps a scaled, per-site varied copy at each of our gates: the cone into the heightmap, the
objects into a plan the generator writes as map objects.

Frame (map coordinates, x east, y north): a yaw `a` faces `u = (sin a, cos a)`; `v = (u_y, -u_x)` is the gate's local
+X (to its right). A point at (t, l) is `P + k * (t * u + l * v)`; mirrored compositions use -l.
"""

import functools
import hashlib
import math
import random
import re
import struct
import sys
from array import array
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the tools folder
from build_hud_override import GeneratorError  # noqa: E402
import dwarven_mountains as dm  # noqa: E402
import heightpack as hp  # noqa: E402
import pngio  # noqa: E402
from data import map_graphics as data  # noqa: E402

OBJECT_DATA = "gfx/map/map_object_data"
RIE_HEIGHTMAP = "map_data/heightmap.png"
OPTIONS = ("mirror", "turn", "height")  # keys of a TRANSPLANT_OVERRIDES entry


@dataclass(frozen=True)
class CompositionObject:
    """One object of the composition: mesh, t, l (RiE units), y offset, yaw relative to the gate (radians), scale."""
    mesh: str
    t: float
    l: float
    y: float
    yaw: float
    scale: float


@dataclass
class Composition:
    """What is transplanted: `objects`, and `delta(t, l)`, RiE's height above the gate foot at (t, l) in RiE px
    (zero beyond `radius`); `peak` is the largest delta within `radius`."""
    objects: list
    delta: object
    peak: float
    radius: float


@dataclass
class PlacedObject:
    mesh: str
    x: float
    y: float
    y_offset: float
    yaw: float
    scale: float


@dataclass
class GatePlan:
    key: tuple
    x: float
    y: float
    k: float
    mirror: bool
    turn: float  # radians
    factor: float
    foot: int
    peak: int = 0
    objects: list = field(default_factory=list)
    dropped: int = 0
    dropped_names: list = field(default_factory=list)
    weights: dict = field(default_factory=dict)
    size: float = 0.0  # the gate model's scale
    yaw: float = 0.0  # the composition's facing (the gate's facing plus the turn)
    gate_yaw: float = 0.0  # the gate's own facing
    pushed_names: list = field(default_factory=list)  # pieces moved back off the gate's keep-out
    join_before: int = 0  # the range behind the cone: its highest pixel before and after the join
    join_after: int = 0
    join_scale: float = 1.0
    apron_raised: int = 0  # pixels raised to the foot under the gate's footprint and front apron


def frame(yaw):
    """((u_x, u_y), (v_x, v_y)) of a gate facing `yaw`."""
    s, c = math.sin(yaw), math.cos(yaw)
    return (s, c), (c, -s)


def wrap(angle):
    """`angle` in (-pi, pi]."""
    a = math.fmod(angle, 2 * math.pi)
    if a > math.pi:
        a -= 2 * math.pi
    elif a <= -math.pi:
        a += 2 * math.pi
    return a


# --- Extraction from Realms in Exile -------------------------------------------------------------------------

def parse_map_objects(text):
    """[(pdxmesh or None, entity or None, [transform floats x10, ...])] for every `object={...}` block of a map
    object text that has a transform."""
    found = []
    for m in re.finditer(r"\bobject\s*=\s*\{", text):
        depth, i = 1, m.end()
        while depth and i < len(text):
            depth += (text[i] == "{") - (text[i] == "}")
            i += 1
        body = text[m.end():i]
        mesh = re.search(r'pdxmesh\s*=\s*"([^"]+)"', body)
        entity = re.search(r'(?<![\w])entity\s*=\s*"([^"]+)"', body)
        tr = re.search(r'transform\s*=\s*"([^"]*)"', body)
        if not tr:
            continue
        rows = [[float(v) for v in line.split("#")[0].split()] for line in tr.group(1).splitlines()
                if line.split("#")[0].strip()]
        found.append((mesh.group(1) if mesh else None, entity.group(1) if entity else None, rows))
    return found


def yaw_of(row):
    """Yaw (radians) of a transform row (x y z qx qy qz qw sx sy sz); only yaw rotations are supported."""
    if abs(row[3]) > 1e-4 or abs(row[5]) > 1e-4:
        raise GeneratorError(f"transform {row} is not a pure yaw rotation")
    return 2 * math.atan2(row[4], row[6])


class Patch:
    """RiE heights around a point, sampled bilinearly in map coordinates (pixel (x, y) holds the height at (x, y))."""

    def __init__(self, x0, y0, width, height, values):
        self.x0, self.y0, self.width, self.height, self.values = x0, y0, width, height, values

    @classmethod
    def from_grid(cls, grid, cx, cy, reach):
        x0, y0 = max(0, int(cx) - reach), max(0, int(cy) - reach)
        x1, y1 = min(grid.width, int(cx) + reach + 2), min(grid.height, int(cy) + reach + 2)
        values = []
        for y in range(y0, y1):
            values.extend(grid.values[y * grid.width + x0:y * grid.width + x1])
        return cls(x0, y0, x1 - x0, y1 - y0, values)

    def at(self, x, y):
        fx, fy = x - self.x0, y - self.y0
        ix, iy = int(math.floor(fx)), int(math.floor(fy))
        if ix < 0 or iy < 0 or ix + 1 >= self.width or iy + 1 >= self.height:
            raise GeneratorError(f"transplant patch does not cover ({x:.1f}, {y:.1f})")
        ax, ay = fx - ix, fy - iy
        w, v = self.width, self.values
        i = iy * w + ix
        return ((v[i] * (1 - ax) + v[i + 1] * ax) * (1 - ay) + (v[i + w] * (1 - ax) + v[i + w + 1] * ax) * ay)


def extract_composition(rie, radius=None, object_radius=None, exclude=None):
    """The Composition of RiE's Erebor gate (RiE root folder `rie`; settings from the data file).

    Objects: every map object with a mesh within COMPOSITION_RADIUS map units of the Erebor gate except the gate and
    COMPOSITION_EXCLUDE, sorted by (mesh, t, l). Heights: RiE's heightmap, `delta(t, l)` = height - the height at the
    gate, within TRANSPLANT_RADIUS px of it."""
    radius = data.TRANSPLANT_RADIUS if radius is None else radius
    object_radius = data.COMPOSITION_RADIUS if object_radius is None else object_radius
    exclude = data.COMPOSITION_EXCLUDE if exclude is None else exclude
    folder = Path(rie) / OBJECT_DATA
    if not folder.is_dir():
        raise GeneratorError(f"Realms in Exile not found: {folder} does not exist")
    gates, others = [], []
    for path in sorted(folder.glob("*.txt")):
        for mesh, entity, rows in parse_map_objects(path.read_text(encoding="utf-8-sig", errors="replace")):
            for row in rows:
                if len(row) == 10 and mesh is not None:
                    (gates if mesh == data.EREBOR_GATE_MESH else others).append((mesh, row))
    if len(gates) != 1:
        raise GeneratorError(f"expected one {data.EREBOR_GATE_MESH} in RiE's map objects, found {len(gates)}")
    gx, gy, yaw = gates[0][1][0], gates[0][1][2], yaw_of(gates[0][1])
    (ux, uy), (vx, vy) = frame(yaw)
    objects = []
    for mesh, row in others:
        dx, dy = row[0] - gx, row[2] - gy
        if mesh in exclude or math.hypot(dx, dy) > object_radius:
            continue
        objects.append(CompositionObject(mesh, dx * ux + dy * uy, dx * vx + dy * vy, row[1], wrap(yaw_of(row) - yaw),
                                         row[7]))
    objects.sort(key=lambda o: (o.mesh, round(o.t, 4), round(o.l, 4)))
    if not objects:
        raise GeneratorError("no map objects near RiE's Erebor gate")
    path = Path(rie) / RIE_HEIGHTMAP
    if not path.is_file():
        raise GeneratorError(f"Realms in Exile not found: {path} does not exist")
    grid = hp.Grid.from_png(pngio.read_png(path.read_bytes()))
    patch = Patch.from_grid(grid, gx, gy, math.ceil(radius) + 3)
    foot = patch.at(round(gx), round(gy))  # the height of the gate's pixel, as our own foot is

    def delta(t, l):
        if t * t + l * l > radius * radius:
            return 0.0
        return patch.at(gx + t * ux + l * vx, gy + t * uy + l * vy) - foot

    peak = max(delta(t / 2, l / 2) for t in range(-2 * radius, 2 * radius + 1)
               for l in range(-2 * radius, 2 * radius + 1))
    return Composition(objects, delta, peak, radius)


@functools.lru_cache(maxsize=2)
def load_composition(rie):
    """`extract_composition` of the RiE folder `rie`, cached (decoding RiE's heightmap takes about 15 s)."""
    return extract_composition(rie)


# --- Mesh bounds and the gate's keep-out ----------------------------------------------------------------------

MESH_MIN = re.compile(rb"!\x03minf\x03\x00\x00\x00(.{12})", re.S)
MESH_MAX = re.compile(rb"!\x03maxf\x03\x00\x00\x00(.{12})", re.S)


def mesh_bounds(blob):
    """((min x, y, z), (max x, y, z)) of a pdxmesh file's bounding box (the `min` and `max` float3 properties of its
    mesh block), in mesh units before the asset's scale."""
    lo, hi = MESH_MIN.search(blob), MESH_MAX.search(blob)
    if not lo or not hi:
        raise GeneratorError("mesh has no min/max bounding box")
    return struct.unpack("<3f", lo.group(1)), struct.unpack("<3f", hi.group(1))


def _rect_corners(x, y, yaw, t0, t1, l0, l1):
    """Map corners of the rectangle t0..t1 by l0..l1 in the frame of a point at (x, y) facing `yaw`."""
    (ux, uy), (vx, vy) = frame(yaw)
    return [(x + t * ux + l * vx, y + t * uy + l * vy) for t, l in ((t0, l0), (t1, l0), (t1, l1), (t0, l1))]


def _overlap(a, b):
    """True when convex polygons `a` and `b` overlap (separating axis test; touching is not overlapping)."""
    for poly in (a, b):
        for i in range(len(poly)):
            ex, ey = poly[(i + 1) % len(poly)][0] - poly[i][0], poly[(i + 1) % len(poly)][1] - poly[i][1]
            nx, ny = -ey, ex
            pa = [nx * px + ny * py for px, py in a]
            pb = [nx * px + ny * py for px, py in b]
            if max(pa) <= min(pb) + 1e-9 or max(pb) <= min(pa) + 1e-9:
                return False
    return True


def footprint(obj, box):
    """Map corners of a placed piece's footprint; `box` = (min x, min z, max x, max z) of its mesh in px at scale 1
    (mesh units times the asset scale). Local +X is the frame's v, local +Z its u (as for the gate)."""
    (ux, uy), (vx, vy) = frame(obj.yaw)
    x0, z0, x1, z1 = box
    return [(obj.x + obj.scale * (lx * vx + lz * ux), obj.y + obj.scale * (lx * vy + lz * uy))
            for lx, lz in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]


def keep_out(plan):
    """Map corners of the gate's keep-out: the model footprint, the front apron and a PIECE_KEEP_OUT_MARGIN."""
    m = data.PIECE_KEEP_OUT_MARGIN
    return _rect_corners(plan.x, plan.y, plan.gate_yaw, -data.GATE_APRON * plan.size / data.GATE_APRON_SCALE,
                         data.GATE_MODEL_DEPTH * plan.size + m, -(data.GATE_MODEL_HALF_WIDTH * plan.size + m),
                         data.GATE_MODEL_HALF_WIDTH * plan.size + m)


def overlaps_keep_out(plan, obj, box):
    """Whether the piece's footprint overlaps the gate's keep-out."""
    return _overlap(footprint(obj, box), keep_out(plan))


# --- Per-site variation ---------------------------------------------------------------------------------------

def site_rng(key):
    """A Random seeded from a stable hash of the site key (never Python's `hash`)."""
    digest = hashlib.sha256("/".join(key).encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def uphill_turn(values, width, height, px, py, yaw, max_turn, t_range, l_half):
    """Radians to turn a gate facing `yaw` toward uphill, at most `max_turn`.

    Uphill is the mean height gradient over the pixels with t_range[0] <= t <= t_range[1] along the facing and
    |l| <= l_half to the side; 0 when there are none or the ground is flat there."""
    (ux, uy), (vx, vy) = frame(yaw)
    reach = math.ceil(math.hypot(t_range[1], l_half)) + 1
    gx = gy = 0.0
    n = 0
    for y in range(max(0, int(py) - reach), min(height, int(py) + reach + 1)):
        for x in range(max(0, int(px) - reach), min(width, int(px) + reach + 1)):
            dx, dy = x - px, y - py
            if t_range[0] <= dx * ux + dy * uy <= t_range[1] and abs(dx * vx + dy * vy) <= l_half:
                i = y * width + x
                gx += (values[i + 1 if x + 1 < width else i] - values[i - 1 if x > 0 else i]) / 2
                gy += (values[i + width if y + 1 < height else i] - values[i - width if y > 0 else i]) / 2
                n += 1
    if n == 0 or math.hypot(gx, gy) < 1e-9:
        return 0.0
    return max(-max_turn, min(max_turn, wrap(math.atan2(gx, gy) - yaw)))


def clamp_factor(raw):
    return max(data.TRANSPLANT_HEIGHT_MIN, min(data.TRANSPLANT_HEIGHT_MAX, raw))


def height_factor(foot, scaled_peak, terrain_max):
    """The cone height factor before jitter: 1, raised so `foot + scaled_peak * f` clears `terrain_max` by
    TRANSPLANT_PEAK_MARGIN, clamped to [TRANSPLANT_HEIGHT_MIN, TRANSPLANT_HEIGHT_MAX]."""
    needed = (terrain_max + data.TRANSPLANT_PEAK_MARGIN - foot) / scaled_peak
    return clamp_factor(max(1.0, needed))


def _ease(x):
    return 0.5 + 0.5 * math.cos(math.pi * min(1.0, max(0.0, x)))


def _lookup(ids):
    table = bytearray(65536)
    for i in ids:
        table[i] = 1
    return table


def _check_overrides(placed, overrides):
    keys = {(s.dwarven_county, s.normal_county) for s, _, _ in placed}
    for key, options in overrides.items():
        if key not in keys:
            raise GeneratorError(f"TRANSPLANT_OVERRIDES key {key} matches no gate; gates are: "
                                 + ", ".join(f"{a}/{b}" for a, b in sorted(keys)))
        for name in options:
            if name not in OPTIONS:
                raise GeneratorError(f"TRANSPLANT_OVERRIDES {key}: unknown option {name!r} (use {', '.join(OPTIONS)})")


def _smoothstep(x, lo, hi):
    x = min(1.0, max(0.0, (x - lo) / (hi - lo)))
    return x * x * (3 - 2 * x)


def shape_weight(comp, t, l):
    """Cone weight 0..1 at (t, l) RiE units of the composition's own frame (l already mirrored): smoothstep of the
    delta between TRANSPLANT_CONE_MIN and _FULL (fractions of the cone's peak) x the face weight (0 in front of the
    gate face, t < 0, a cosine up to 1 at t = TRANSPLANT_FACE_RAMP) x the fade over the last TRANSPLANT_FADE px of the
    radius. Water is not considered here."""
    r = math.hypot(t, l)
    if t < 0 or r > comp.radius:
        return 0.0
    c = _smoothstep(comp.delta(t, l), data.TRANSPLANT_CONE_MIN * comp.peak, data.TRANSPLANT_CONE_FULL * comp.peak)
    if c <= 0:
        return 0.0
    c *= 1 - _ease(t / data.TRANSPLANT_FACE_RAMP)
    fade = data.TRANSPLANT_FADE
    if r > comp.radius - fade:
        c *= _ease((r - (comp.radius - fade)) / fade)
    return c


def _water_offsets():
    n = data.TRANSPLANT_WATER_FADE
    return sorted(((dx, dy) for dy in range(-n, n + 1) for dx in range(-n, n + 1)
                   if 0 < math.hypot(dx, dy) < n), key=lambda o: math.hypot(*o))


def _water_factor(blocked, x, y, w, h, offsets):
    """min(1, distance to the nearest `blocked` pixel / TRANSPLANT_WATER_FADE); `offsets` is `_water_offsets()`."""
    n = data.TRANSPLANT_WATER_FADE
    for ox, oy in offsets:
        px_, py_ = x + ox, y + oy
        if 0 <= px_ < w and 0 <= py_ < h and blocked[py_ * w + px_]:
            return math.hypot(ox, oy) / n
    return 1.0


def _cone_pixels(plan, comp, yaw, w, h, blocked, offsets):
    """[(i, weight, delta)] for the pixels of one gate's cone: weight > 0 is `shape_weight` x the water fade
    min(1, distance to the nearest `blocked` pixel (water or province 0) / TRANSPLANT_WATER_FADE)."""
    (ux, uy), (vx, vy) = frame(yaw)
    k = plan.k
    reach = math.ceil(k * comp.radius) + 1
    out = []
    for y in range(max(0, int(plan.y) - reach), min(h, int(plan.y) + reach + 1)):
        for x in range(max(0, int(plan.x) - reach), min(w, int(plan.x) + reach + 1)):
            if blocked[y * w + x]:
                continue
            dx, dy = x - plan.x, y - plan.y
            t, l = (dx * ux + dy * uy) / k, (dx * vx + dy * vy) / k
            l = -l if plan.mirror else l
            c = shape_weight(comp, t, l)
            if c <= 0:
                continue
            c *= _water_factor(blocked, x, y, w, h, offsets)
            out.append((y * w + x, c, comp.delta(t, l)))
    return out


def _join_range(new, plan, w, h, ids, blocked, ranges, offsets):
    """Scale the range behind the gate's cone up so its highest point reaches the cone's peak (see `transplant`);
    sets plan.join_before, join_after and join_scale."""
    (ux, uy), _ = frame(plan.yaw)
    radius, full = data.RANGE_JOIN_RADIUS, data.RANGE_JOIN_FULL
    region = []
    m = 0
    for y in range(max(0, int(plan.y) - radius - 1), min(h, int(plan.y) + radius + 2)):
        for x in range(max(0, int(plan.x) - radius - 1), min(w, int(plan.x) + radius + 2)):
            i = y * w + x
            if blocked[i] or not ranges[ids[i]]:
                continue
            dx, dy = x - plan.x, y - plan.y
            d = math.hypot(dx, dy)
            if d > radius or dx * ux + dy * uy < 0 or plan.weights.get(i, 0.0) >= data.RANGE_JOIN_CORE:
                continue
            region.append((i, x, y, d))
            m = max(m, new[i])
    g = plan.foot
    plan.join_before = m
    if m > g and plan.peak > m:
        plan.join_scale = min(data.RANGE_JOIN_MAX, max(1.0, (plan.peak - g) / (m - g)))
    s = plan.join_scale
    if s > 1.0:
        for i, x, y, d in region:
            cur = new[i]
            if cur <= g:
                continue
            wgt = 1.0 if d <= full else _ease((d - full) / (radius - full))
            wgt *= _water_factor(blocked, x, y, w, h, offsets)
            if wgt > 0:
                new[i] = max(cur, dm.soft_ceiling(g + (cur - g) * (1 + (s - 1) * wgt)))
    plan.join_after = max((new[i] for i, _, _, _ in region), default=0)


def _level_footprint(new, plan, w, h, blocked):
    """Raise the gate's footprint and front apron (in the gate's own frame) to at least its foot, blending out over
    GATE_APRON_FADE px; land only. Sets plan.apron_raised."""
    (ux, uy), (vx, vy) = frame(plan.gate_yaw)
    back = data.GATE_APRON * plan.size / data.GATE_APRON_SCALE
    depth = data.GATE_MODEL_DEPTH * plan.size
    half = data.GATE_MODEL_HALF_WIDTH * plan.size + 1
    fade = data.GATE_APRON_FADE
    reach = math.ceil(math.hypot(max(back, depth), half)) + fade + 1
    foot = plan.foot
    raised = 0
    for y in range(max(0, int(plan.y) - reach), min(h, int(plan.y) + reach + 2)):
        for x in range(max(0, int(plan.x) - reach), min(w, int(plan.x) + reach + 2)):
            i = y * w + x
            if blocked[i] or new[i] >= foot:
                continue
            dx, dy = x - plan.x, y - plan.y
            t, l = dx * ux + dy * uy, dx * vx + dy * vy
            d = math.hypot(max(-back - t, 0.0, t - depth), max(abs(l) - half, 0.0))
            if d > fade:
                continue
            cur = new[i]
            value = max(cur, int(round(cur + (foot - cur) * _ease(d / fade))))
            if value > cur:
                new[i] = value
                raised += 1
    plan.apron_raised = raised


def _clear_piece(plan, obj, box, axis, step=0.5):
    """The distance (0 if none is needed, a multiple of `step`) to push `obj` along `axis` until its footprint no
    longer overlaps the gate's keep-out, or None if PIECE_MAX_PUSH is not enough."""
    d = 0.0
    while d <= data.PIECE_MAX_PUSH + 1e-9:
        moved = PlacedObject(obj.mesh, obj.x + d * axis[0], obj.y + d * axis[1], obj.y_offset, obj.yaw, obj.scale)
        if not overlaps_keep_out(plan, moved, box):
            return d
        d += step
    return None


def transplant(grid, pm, water, placed, comp, overrides=None, ranges=None, piece_bounds=None):
    """Stamp the composition at every gate; returns (new grid, [GatePlan]) with plans sorted by site key.

    `placed` is [(site, size, (x, y))]: the gate's size gives k = size / EREBOR_GATE_SCALE, its position and the
    site's `inward` give the frame. Per site (seeded by its key): mirror with probability TRANSPLANT_MIRROR_CHANCE,
    turn toward uphill by at most TRANSPLANT_MAX_TURN, a height factor (see `height_factor`) plus jitter, object
    jitter; `overrides` (TRANSPLANT_OVERRIDES) pins `mirror`, `turn` (degrees) and `height`.
    The cone only blends up from the ground: a pixel with cone weight c (see `shape_weight` and `_cone_pixels`)
    becomes `max(cur, round(cur + c * (soft_ceiling(foot + k * delta * factor) - cur)))`, `foot` being the height at
    the gate in `grid`; pixels in front of the gate face, outside the cone, on water or on province 0 never change.
    Gates apply in key order, each blending from what the last left. A piece survives only if its centre has t >= 0
    and cone weight >= TRANSPLANT_PIECE_MIN_WEIGHT, and does not fall outside the map, on water or on province 0;
    `plan.dropped_names` lists the meshes; `plan.weights` is {pixel: cone weight}.

    After all cones, each gate in key order (reading what the last left) joins the range behind its cone to the cone's
    peak (`_join_range`: land of `ranges`, a set of province ids, None = all land, at t >= 0 within RANGE_JOIN_RADIUS
    px and off the cone core, is scaled up from the foot by s = (peak - foot) / (range max - foot) in
    [1, RANGE_JOIN_MAX], fading out with distance; never lowered) and then levels its footprint and front apron to the
    foot (`_level_footprint`). `piece_bounds` ({mesh: (min x, min z, max x, max z)} in px at scale 1) enables the
    keep-out: a piece whose footprint overlaps the gate's keep-out (`keep_out`) is pushed back along the cone axis by
    at most PIECE_MAX_PUSH px, filtered again there (listed in `plan.pushed_names`), else dropped."""
    overrides = overrides if overrides is not None else data.TRANSPLANT_OVERRIDES
    _check_overrides(placed, overrides)
    w, h, ids = pm.width, pm.height, pm.ids
    wat = _lookup(water)
    rng_ids = bytearray([1]) * 65536 if ranges is None else _lookup(ranges)
    blocked = bytearray(len(ids))
    for i, v in enumerate(ids):
        blocked[i] = 1 if (not v or wat[v]) else 0
    offsets = _water_offsets()
    old = grid.values
    new = array("H", old)
    plans = []
    cones = []

    def piece_ok(t, l, ox, oy):
        """The piece filter: centre behind the face (t >= 0), enough cone weight, on the map and on land."""
        return (t >= 0 and shape_weight(comp, t, l) >= data.TRANSPLANT_PIECE_MIN_WEIGHT
                and 0 <= ox < w and 0 <= oy < h and not blocked[oy * w + ox])

    for site, size, (px, py) in sorted(placed, key=lambda sp: (sp[0].dwarven_county, sp[0].normal_county)):
        key = (site.dwarven_county, site.normal_county)
        pin = overrides.get(key, {})
        k = size / data.EREBOR_GATE_SCALE
        rng = site_rng(key)
        mirror = rng.random() < data.TRANSPLANT_MIRROR_CHANCE
        jitter_h = rng.uniform(-data.TRANSPLANT_HEIGHT_JITTER, data.TRANSPLANT_HEIGHT_JITTER)
        draws = [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1), rng.random()) for _ in comp.objects]
        mirror = pin.get("mirror", mirror)
        yaw0 = math.atan2(site.inward[0] + 0.0, site.inward[1] + 0.0)
        if "turn" in pin:
            turn = math.radians(pin["turn"])
        else:
            turn = uphill_turn(old, w, h, px, py, yaw0, math.radians(data.TRANSPLANT_MAX_TURN),
                               data.TRANSPLANT_UPHILL_T, data.TRANSPLANT_UPHILL_L)
        yaw = yaw0 + turn
        gx, gy = min(w - 1, max(0, int(round(px)))), min(h - 1, max(0, int(round(py))))
        foot = old[gy * w + gx]
        plan = GatePlan(key, px, py, k, mirror, turn, 1.0, foot, size=size, yaw=yaw, gate_yaw=yaw0)
        cone = _cone_pixels(plan, comp, yaw, w, h, blocked, offsets)
        plan.weights = {i: c for i, c, _ in cone}
        if "height" in pin:
            plan.factor = pin["height"]
        else:
            ground = [old[i] for i, _, _ in cone]
            raw = height_factor(foot, k * comp.peak, max(ground, default=foot))
            plan.factor = clamp_factor(raw + jitter_h)
        sign = -1 if mirror else 1
        (ux, uy), (vx, vy) = frame(yaw)
        for obj, (jt, jl, jyaw, jscale) in zip(comp.objects, draws):
            t = obj.t + jt * data.TRANSPLANT_JITTER_POS
            l = sign * obj.l + jl * data.TRANSPLANT_JITTER_POS
            lo, hi = data.TRANSPLANT_JITTER_SCALE
            x, y = px + k * (t * ux + l * vx), py + k * (t * uy + l * vy)
            ox, oy = int(round(x)), int(round(y))
            if not piece_ok(t, sign * l, ox, oy):
                plan.dropped += 1
                plan.dropped_names.append(obj.mesh)
                continue
            piece = PlacedObject(obj.mesh, x, y, obj.y * k, yaw + sign * obj.yaw
                                 + jyaw * math.radians(data.TRANSPLANT_JITTER_YAW),
                                 k * obj.scale * (lo + (hi - lo) * jscale))
            if piece_bounds is not None:
                if obj.mesh not in piece_bounds:
                    raise GeneratorError(f"no bounding box for {obj.mesh}")
                push = _clear_piece(plan, piece, piece_bounds[obj.mesh], (ux, uy))
                if push is not None and push > 0:
                    piece.x, piece.y = x + push * ux, y + push * uy
                    if piece_ok(t + push / k, sign * l, int(round(piece.x)), int(round(piece.y))):
                        plan.pushed_names.append(obj.mesh)
                    else:
                        push = None
                if push is None:
                    plan.dropped += 1
                    plan.dropped_names.append(obj.mesh)
                    continue
            plan.objects.append(piece)
        plans.append(plan)
        cones.append(cone)
    for plan, cone in zip(plans, cones):
        for i, weight, d in cone:
            target = dm.soft_ceiling(plan.foot + plan.k * d * plan.factor)
            cur = new[i]
            value = max(cur, int(round(cur + weight * (target - cur))))
            if value > cur:
                new[i] = value
                plan.peak = max(plan.peak, value)
    for plan in plans:
        _join_range(new, plan, w, h, ids, blocked, rng_ids, offsets)
        _level_footprint(new, plan, w, h, blocked)
    return type(grid)(w, h, new), plans
