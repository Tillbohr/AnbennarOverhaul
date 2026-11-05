"""Range rock: the Serpentspine rock around Serpentreach and West Dwarovar, cut out of Anbennar's province 2426.

The game fills an impassable province with a neighbour's map colour only below LARGE_IMPASSABLE_PROVINCE_PIXELS (and
counts it in the realm's name). Segbandal's rock (2608) is small enough; 2426 "Big Waste" holds the whole outer world.
Giving each range's rock its own impassable province paints the range in its realm's colour. Only the province map
changes: the carve, terrain and gates read Anbennar's map, where this rock is still 2426.

Works on Anbennar's map (x east, y north, y = 0 at the south edge). `rock_pixels` is deterministic.
"""

from array import array
from collections import namedtuple

Rock = namedtuple("Rock", "id colour name pixels locator")  # pixels sorted by (y, x); locator: the pixel nearest its centre


def rock_pixels(pm, height, regions, avoid, cfg) -> list:
    """One pixel set per floor set in `regions`: `cfg.ROCK_SOURCE` rock reached from that floor (nearest floor wins)
    through ground at least ROCK_MIN_HEIGHT high (ROCK_ALWAYS px around a floor at any height), at most ROCK_REACH px
    away and south of ROCK_MAX_Y. Rock nearer `avoid` (pixels) or a ROCK_AVOID province is left alone. Waste left
    enclosed by a range, or narrower than 2 * ROCK_SLIVER px against it, joins the range: no strip stays uncoloured
    between the range and the land. So does a piece cut off from the open waste within ROCK_ISLAND_GAP px of the range
    across land. `height(x, y)` is the 0-255 height."""
    floors = [p for region in regions for p in region]
    if not floors:
        return [set() for _ in regions]
    margin = cfg.ROCK_REACH + 2 * cfg.ROCK_SLIVER + cfg.ROCK_ISLAND_GAP + 2  # room for open waste past the furthest rock
    x0, x1 = max(min(p[0] for p in floors) - margin, 0), min(max(p[0] for p in floors) + margin + 1, pm.width)
    y0, y1 = max(min(p[1] for p in floors) - margin, 0), min(max(p[1] for p in floors) + margin + 1, pm.height)
    w, h = x1 - x0, y1 - y0
    n = w * h
    src = bytearray(n)  # the source province, floors taken out
    label = array("b", bytes(n))  # 0 unreached, -1 left alone, i + 1 region i
    high = bytearray(n)
    capped = bytearray(n)
    avoid_ids = set(cfg.ROCK_AVOID)
    for y in range(y0, y1):
        row = (y - y0) * w
        map_row = y * pm.width
        for x in range(x0, x1):
            pid = pm.ids[map_row + x]
            if pid == cfg.ROCK_SOURCE:
                k = row + x - x0
                src[k] = 1
                high[k] = height(x, y) >= cfg.ROCK_MIN_HEIGHT
                capped[k] = y > cfg.ROCK_MAX_Y
            elif pid in avoid_ids:
                label[row + x - x0] = -1

    def index(p):
        return (p[1] - y0) * w + p[0] - x0

    for p in avoid:
        if x0 <= p[0] < x1 and y0 <= p[1] < y1:
            src[index(p)] = 0
            label[index(p)] = -1
    is_floor = bytearray(n)
    for i, region in enumerate(regions):
        for p in region:
            src[index(p)] = 0
            label[index(p)] = i + 1
            is_floor[index(p)] = 1

    def inner(k):
        """Not on the box's edge, so all eight neighbours exist."""
        return w <= k < n - w and 0 < k % w < w - 1

    steps = (1, -1, w, -w, w + 1, w - 1, -w + 1, -w - 1)

    def spread(frontier, can_enter, enter, levels=None):
        """Breadth-first from `frontier` over 8 neighbours; returns the last frontier."""
        while frontier and levels != 0:
            levels = None if levels is None else levels - 1
            nxt = []
            for k in frontier:
                if inner(k):
                    for s in steps:
                        m = k + s
                        if can_enter(m):
                            enter(m, k)
                            nxt.append(m)
            frontier = nxt
        return frontier

    def take_label(m, k):
        label[m] = label[k]

    # the range: any height close to a floor, high ground further out
    frontier = spread([k for k in range(n) if label[k]], lambda m: src[m] and not label[m] and not capped[m],
                      take_label, cfg.ROCK_ALWAYS)
    spread(frontier, lambda m: src[m] and not label[m] and not capped[m] and high[m], take_label,
           cfg.ROCK_REACH - cfg.ROCK_ALWAYS)

    # the waste that stays waste: wider than 2 * ROCK_SLIVER px and joined to the box's edge (the open Big Waste)
    waste = bytearray(1 if src[k] and label[k] <= 0 else 0 for k in range(n))

    def mark(flags):
        def enter(m, _k):
            flags[m] = 1
        return enter

    worn = bytearray(n)
    edge = [k for k in range(n) if waste[k] and inner(k) and any(not waste[k + s] for s in steps)]
    for k in edge:
        worn[k] = 1
    spread(edge, lambda m: waste[m] and not worn[m], mark(worn), cfg.ROCK_SLIVER - 1)
    kept = bytearray(1 if waste[k] and not worn[k] else 0 for k in range(n))
    spread([k for k in range(n) if kept[k]], lambda m: waste[m] and not kept[m], mark(kept), cfg.ROCK_SLIVER)
    open_waste = bytearray(n)
    rim = [k for k in range(n) if kept[k] and inner(k) and any(not inner(k + s) for s in steps)]
    for k in rim:
        open_waste[k] = 1
    spread(rim, lambda m: kept[m] and not open_waste[m], mark(open_waste))

    # what is left joins the range it touches
    def enclosed(m):
        return waste[m] and not open_waste[m] and label[m] == 0 and not capped[m]

    spread([k for k in range(n) if label[k] > 0 and not is_floor[k]], enclosed, take_label)

    # a ridge of the range cut off by a thin strip of land joins it too
    near = array("b", bytes(n))
    rock = [k for k in range(n) if label[k] > 0 and not is_floor[k]]
    for k in rock:
        near[k] = label[k]

    def take_near(m, k):
        near[m] = near[k]

    spread(rock, lambda m: not near[m], take_near, cfg.ROCK_ISLAND_GAP)
    ridges = [k for k in range(n) if near[k] > 0 and enclosed(k)]
    for k in ridges:
        label[k] = near[k]
    spread(ridges, enclosed, take_label)

    out = [set() for _ in regions]
    for k in range(n):
        if label[k] > 0 and not is_floor[k]:
            out[label[k] - 1].add((x0 + k % w, y0 + k // w))
    return out


def make_rock(pid: int, colour: tuple, name: str, pixels: set) -> Rock:
    """A Rock with its locator on the rock pixel nearest the centre of `pixels`."""
    ordered = sorted(pixels, key=lambda p: (p[1], p[0]))
    cx = sum(p[0] for p in ordered) / len(ordered)
    cy = sum(p[1] for p in ordered) / len(ordered)
    return Rock(pid, colour, name, ordered, min(ordered, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2))
