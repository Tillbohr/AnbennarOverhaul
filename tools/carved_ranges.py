"""Carved dwarven ranges: Serpentreach's carved-in look (flat floors, steep rock walls) applied to an existing
Anbennar dwarven range whose provinces lie inside impassable rock (Segbandal).

The floor is every pixel of the range's dwarven provinces; the rock is every impassable province within
CARVE_ROCK_RADIUS px of it. Floors are flat at the surrounding ground +/- the Serpentreach terraces, ramping up or down
to the land outside over CARVE_RAMP px wherever the floor meets passable land; rock within WALL_WIDTH of the floor
becomes a smoothstep wall up to the rock (or to floor + MIN_WALL), as in `serpentreach_layout.carve`.
Used by tools/build_map_graphics.py; see docs/systems/map-graphics.md.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the tools folder
from build_hud_override import GeneratorError  # noqa: E402
import serpentreach_layout as sl  # noqa: E402
from data import serpentreach as sr_data  # noqa: E402

N8 = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))


def carved_range(ranges, titles, county):
    """The dwarven range (set of province ids) holding a province of `county`; stops when there is none."""
    for rng in ranges:
        if any(county in (titles.get(p) or ()) for p in rng):
            return rng
    raise GeneratorError(f"CARVED_RANGES: no dwarven range holds a province of {county}")


def floor_pixels(pm, provinces):
    """{(x, y): province id} for every pixel of `provinces`."""
    W = pm.width
    return {(i % W, i // W): p for i, p in enumerate(pm.ids) if p in provinces}


def rock_around(pm, floor, impassable, radius):
    """Impassable provinces with a pixel within `radius` (chessboard) of the floor."""
    W, H = pm.width, pm.height
    box = sl._box_around(list(floor), radius + 1, W, H)
    near = sl.chamfer(list(floor), box, radius)
    return {pm.ids[y * W + x] for (x, y) in near if pm.ids[y * W + x] in impassable}


def _open_land(pm, floor, rock, water, land=()):
    """Passable land pixels (not floor, rock, water or id 0, or a `land` pixel whatever its province) touching the
    floor: where the floor opens to the land."""
    W, H = pm.width, pm.height
    out = set()
    for x, y in floor:
        for dx, dy in N8:
            n = (x + dx, y + dy)
            if n in floor or not (0 <= n[0] < W and 0 <= n[1] < H):
                continue
            pid = pm.ids[n[1] * W + n[0]]
            if n in land or (pid and pid not in rock and pid not in water):
                out.add(n)
    return out


def carve(grid, floor, terrain, rock, pm, water, ramp, ground_radius=None, land=None):
    """(new grid, report): the floor ({(x, y): province id}) carved into `rock`. `terrain` maps a province to its
    terrain type (sr_data.TERRACE key). Only floor and rock pixels change; rock is never lowered. `land` pixels
    ({(x, y): province}) are rock on the province map but land to the carve (Serpent's Vale, other regions' floors):
    the floor ramps to them where it touches them and they are never walled; they do not count for the ground."""
    land = land or {}
    import heightpack as hp
    W, H = pm.width, pm.height
    ground_radius = ground_radius or sr_data.CARVE_GROUND_RADIUS
    pts = list(floor)
    near = sl.chamfer(pts, sl._box_around(pts, ground_radius, W, H), ground_radius)
    ground = sorted(grid.get(x, y) for (x, y) in near
                    if (x, y) not in floor and pm.ids[y * W + x] not in rock and pm.ids[y * W + x] not in water
                    and pm.ids[y * W + x] != 0)
    if not ground:
        raise GeneratorError(f"no land within {ground_radius} px of the carved floor")
    base = ground[len(ground) // 2]
    unknown = sorted({p for p in floor.values() if terrain.get(p) not in sr_data.TERRACE})
    if unknown:
        raise GeneratorError(f"carved floor provinces with no terrace: {', '.join(map(str, unknown[:5]))}")
    fh = {p: base + sr_data.TERRACE[terrain[pid]] * sr_data.TERRACE_STEP for p, pid in floor.items()}
    opening = {p: grid.get(*p) for p in _open_land(pm, floor, rock, water, land)}
    if opening:
        for p, (d, h) in sl._nearest(opening, sl._box_around(pts, 1, W, H), ramp).items():
            if p in fh:
                fh[p] = round(h + (fh[p] - h) * sl._smooth(d / ramp))
    values = grid.values[:]
    for (x, y), h in fh.items():
        values[y * W + x] = max(0, min(65535, h))
    limit = sr_data.WALL_WIDTH + sr_data.WALL_FADE
    walls = 0
    for (x, y), (d, h) in sl._nearest(fh, sl._box_around(pts, limit + 1, W, H), limit).items():
        i = y * W + x
        if d == 0 or (x, y) in floor or (x, y) in land or pm.ids[i] not in rock:
            continue
        orig = grid.values[i]
        rim = h + sr_data.MIN_WALL
        if d <= sr_data.WALL_WIDTH:
            new = h + (max(orig, rim) - h) * sl._smooth(d / sr_data.WALL_WIDTH)
        else:
            new = max(orig, rim + (orig - rim) * (d - sr_data.WALL_WIDTH) / sr_data.WALL_FADE)
        new = max(0, min(65535, round(new)))
        if new != orig:
            values[i] = new
            walls += 1
    return hp.Grid(W, H, values), {"base": base, "floor_px": len(fh), "wall_px": walls,
                                   "opening_px": len(opening), "rock": sorted(rock)}


def province_materials(floor, terrain, style="default"):
    """{province id: (floor material, wall material)} from Serpentreach's TERRAIN_STYLES by terrain type."""
    s = {**sr_data.TERRAIN_STYLES["default"], **sr_data.TERRAIN_STYLES[style]}
    return {pid: (s[terrain[pid]], s["wall"]) for pid in set(floor.values())}


def paint(index, intensity, floor, materials, pm, rock):
    """The blend maps with the floor and its rock walls painted, as `serpentreach_layout.paint`."""
    return sl.paint(index, intensity, SimpleNamespace(owner=floor), materials, pm, rock=rock)
