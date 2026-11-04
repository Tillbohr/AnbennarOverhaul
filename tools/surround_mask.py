"""Pull CK3's surround fog back from a mountain range.

`gfx/map/surround_map/surround_mask.dds` (DXT5, half the map's resolution, rows top-down like provinces.png) tells
the shaders where the playable map ends: blue hides the flat map, green draws the surround clouds and red the
surround fog that fades the terrain into black. Anbennar starts that fog on the crest of the Serpentspine, so the
range's outer face disappears into black. `push_back` lowers all three channels near the range (`range_pixels`)
inside a box: no
fog within `reveal` mask pixels of a pixel at least `threshold` high, full fog again `reveal + fade` away (smoothstep),
and never more fog than Anbennar's mask has. `patch_dxt5` re-encodes only the 4x4 blocks that changed, so the rest
of Anbennar's file stays byte for byte.
"""
import struct

from build_hud_override import GeneratorError

DDS_HEADER = 128
BLOCK = 16  # bytes per DXT5 block: 8 alpha, 8 colour


def dxt5_size(data: bytes) -> tuple:
    """(width, height) of a DXT5 DDS; stops on anything else."""
    if data[:4] != b"DDS " or data[84:88] != b"DXT5":
        raise GeneratorError("surround mask is not a DXT5 DDS")
    height, width = struct.unpack("<II", data[12:20])
    if width % 4 or height % 4:
        raise GeneratorError(f"surround mask size {width}x{height} is not a multiple of 4")
    return width, height


def range_pixels(height, fog, box: tuple, threshold: int) -> set:
    """Pixels of `box` at least `threshold` high (`height(x, y)`) that join, through such pixels (4-neighbours), a
    high pixel with less than half fog (`fog(x, y)` < 128): the range the player already sees and its slopes into
    the fog, not other heights deep in the fog."""
    x0, y0, x1, y1 = box
    high = {(x, y) for y in range(y0, y1) for x in range(x0, x1) if height(x, y) >= threshold}
    todo = [p for p in high if fog(*p) < 128]
    seen = set(todo)
    while todo:
        x, y = todo.pop()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n in high and n not in seen:
                seen.add(n)
                todo.append(n)
    return seen


def distances(points: set, box: tuple) -> dict:
    """{(x, y): distance in pixels to the nearest of `points`} for every pixel of `box` (x0, y0, x1, y1), by a
    two-pass 3-4 chamfer (within 8% of Euclidean). Points outside the box do not count."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    big = 10 ** 9
    d = [0 if (x0 + i % w, y0 + i // w) in points else big for i in range(w * h)]
    for y in range(h):
        row = y * w
        for x in range(w):
            i = row + x
            v = d[i]
            if x and d[i - 1] + 3 < v:
                v = d[i - 1] + 3
            if y:
                up = i - w
                if d[up] + 3 < v:
                    v = d[up] + 3
                if x and d[up - 1] + 4 < v:
                    v = d[up - 1] + 4
                if x + 1 < w and d[up + 1] + 4 < v:
                    v = d[up + 1] + 4
            d[i] = v
    for y in range(h - 1, -1, -1):
        row = y * w
        for x in range(w - 1, -1, -1):
            i = row + x
            v = d[i]
            if x + 1 < w and d[i + 1] + 3 < v:
                v = d[i + 1] + 3
            if y + 1 < h:
                down = i + w
                if d[down] + 3 < v:
                    v = d[down] + 3
                if x + 1 < w and d[down + 1] + 4 < v:
                    v = d[down + 1] + 4
                if x and d[down - 1] + 4 < v:
                    v = d[down - 1] + 4
            d[i] = v
    return {(x0 + i % w, y0 + i // w): v / 3 for i, v in enumerate(d)}


def fog_cap(distance: float, reveal: float, fade: float) -> int:
    """The most fog (0-255) allowed `distance` pixels from the range: 0 within `reveal`, 255 from `reveal + fade`."""
    if distance <= reveal:
        return 0
    t = min(1.0, (distance - reveal) / fade)
    return round(255 * t * t * (3 - 2 * t))


def push_back(pixels: bytearray, width: int, ridge: set, box: tuple, reveal: float, fade: float,
              feather: float = 0) -> set:
    """Lower the BGR channels of `pixels` (BGRA, `width` wide) in `box` to `fog_cap` of their distance from the
    `ridge` pixels. Within `feather` px of the box's edge the cap rises back to full fog, so the change meets the
    untouched mask without a seam. Returns the changed pixels."""
    x0, y0, x1, y1 = box
    changed = set()
    for (x, y), dist in distances(ridge, box).items():
        cap = fog_cap(dist, reveal, fade)
        if feather:
            cap = max(cap, 255 - fog_cap(min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y), 0, feather))
        i = (y * width + x) * 4
        for c in range(3):
            if pixels[i + c] > cap:
                pixels[i + c] = cap
                changed.add((x, y))
    return changed


def _rgb565(b: int, g: int, r: int) -> int:
    return ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | (b * 31 + 127) // 255


def _expand(c: int) -> tuple:
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return (b * 255 + 15) // 31, (g * 255 + 31) // 63, (r * 255 + 15) // 31


def _rgb565_down(b: int, g: int, r: int) -> int:
    """The 565 code whose colour is at or below (b, g, r) in every channel."""
    return (r * 31 // 255) << 11 | (g * 63 // 255) << 5 | b * 31 // 255


def colour_block(texels: list) -> bytes:
    """A DXT colour block (4-colour mode) for 16 BGR texels: the bounding box's corners as endpoints (the low one
    rounded down), each texel the nearest palette colour that is nowhere above it, so a mask never gains fog; the low
    corner always qualifies."""
    lo = tuple(min(t[c] for t in texels) for c in range(3))
    hi = tuple(max(t[c] for t in texels) for c in range(3))
    c0, c1 = _rgb565(*hi), _rgb565_down(*lo)
    if c0 == c1:
        return struct.pack("<HHI", c0, c1, 0)
    if c0 < c1:
        c0, c1 = c1, c0
    p0, p1 = _expand(c0), _expand(c1)
    palette = [p0, p1, tuple((2 * a + b) // 3 for a, b in zip(p0, p1)), tuple((a + 2 * b) // 3 for a, b in zip(p0, p1))]
    bits = 0
    for n, t in enumerate(texels):
        allowed = [k for k in range(4) if all(palette[k][c] <= t[c] for c in range(3))]
        best = min(allowed, key=lambda k: sum((t[c] - palette[k][c]) ** 2 for c in range(3)))
        bits |= best << (2 * n)
    return struct.pack("<HHI", c0, c1, bits)


def patch_dxt5(data: bytes, pixels: bytes, changed: set) -> bytes:
    """`data` (a DXT5 DDS whose top mip is the only level) with the colour half of every block holding a `changed`
    pixel re-encoded from `pixels` (BGRA, same size). Alpha blocks and untouched blocks stay as they were."""
    width, height = dxt5_size(data)
    out = bytearray(data)
    blocks_wide = width // 4
    for bx, by in sorted({(x // 4, y // 4) for x, y in changed}):
        texels = []
        for dy in range(4):
            for dx in range(4):
                i = ((by * 4 + dy) * width + bx * 4 + dx) * 4
                texels.append((pixels[i], pixels[i + 1], pixels[i + 2]))
        offset = DDS_HEADER + (by * blocks_wide + bx) * BLOCK + 8
        out[offset:offset + 8] = colour_block(texels)
    return bytes(out)


def max_error(a: bytes, b: bytes) -> int:
    """Largest per-channel difference between two equally sized BGRA images (for checking an encode)."""
    return max((abs(x - y) for i, (x, y) in enumerate(zip(a, b)) if i % 4 != 3), default=0)

