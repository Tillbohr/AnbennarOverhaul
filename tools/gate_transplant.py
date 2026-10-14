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
            mesh = mesh or data.COMPOSITION_SUBSTITUTES.get(entity)
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


def _cone_pixels(plan, comp, yaw, w, h):
    """[(i, weight, delta)] for the pixels of one gate's cone (delta > 0, weight 0..1), in the composition's frame."""
    (ux, uy), (vx, vy) = frame(yaw)
    k, radius = plan.k, comp.radius
    reach = math.ceil(k * radius) + 1
    fade = data.TRANSPLANT_FADE
    out = []
    for y in range(max(0, int(plan.y) - reach), min(h, int(plan.y) + reach + 1)):
        for x in range(max(0, int(plan.x) - reach), min(w, int(plan.x) + reach + 1)):
            dx, dy = x - plan.x, y - plan.y
            t, l = (dx * ux + dy * uy) / k, (dx * vx + dy * vy) / k
            r = math.hypot(t, l)
            if r > radius:
                continue
            d = comp.delta(t, -l if plan.mirror else l)
            if d > 0:
                out.append((y * w + x, 1.0 if r <= radius - fade else _ease((r - (radius - fade)) / fade), d))
    return out


def transplant(grid, pm, water, placed, comp, overrides=None):
    """Stamp the composition at every gate; returns (new grid, [GatePlan]) with plans sorted by site key.

    `placed` is [(site, size, (x, y))]: the gate's size gives k = size / EREBOR_GATE_SCALE, its position and the
    site's `inward` give the frame. Per site (seeded by its key): mirror with probability TRANSPLANT_MIRROR_CHANCE,
    turn toward uphill by at most TRANSPLANT_MAX_TURN, a height factor (see `height_factor`) plus jitter, object
    jitter; `overrides` (TRANSPLANT_OVERRIDES) pins `mirror`, `turn` (degrees) and `height`. The cone raises land of
    any kind (not water, not province 0) to at least `soft_ceiling(foot + k * delta * factor * fade)` where delta > 0,
    `foot` being the height at the gate in `grid`; nothing is lowered. Gates apply in key order, each blending from
    what the last left. Objects whose centre falls outside the map, on water or on province 0 are dropped."""
    overrides = overrides if overrides is not None else data.TRANSPLANT_OVERRIDES
    _check_overrides(placed, overrides)
    w, h, ids = pm.width, pm.height, pm.ids
    wat = _lookup(water)
    old = grid.values
    new = array("H", old)
    plans = []
    cones = []
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
        plan = GatePlan(key, px, py, k, mirror, turn, 1.0, foot)
        cone = _cone_pixels(plan, comp, yaw, w, h)
        if "height" in pin:
            plan.factor = pin["height"]
        else:
            ground = [old[i] for i, _, _ in cone if ids[i] and not wat[ids[i]]]
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
            if not (0 <= ox < w and 0 <= oy < h) or not ids[oy * w + ox] or wat[ids[oy * w + ox]]:
                plan.dropped += 1
                continue
            plan.objects.append(PlacedObject(obj.mesh, x, y, obj.y * k, yaw + sign * obj.yaw
                                             + jyaw * math.radians(data.TRANSPLANT_JITTER_YAW),
                                             k * obj.scale * (lo + (hi - lo) * jscale)))
        plans.append(plan)
        cones.append(cone)
    for plan, cone in zip(plans, cones):
        for i, weight, d in cone:
            if not ids[i] or wat[ids[i]]:
                continue
            value = dm.soft_ceiling(plan.foot + plan.k * d * plan.factor * weight)
            plan.peak = max(plan.peak, value)
            if value > new[i]:
                new[i] = value
    return type(grid)(w, h, new), plans
