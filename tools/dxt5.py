"""Pure-Python DXT5 (BC3) DDS writer, for art the game samples from block-compressed texture arrays.

CK3's portrait decals are all 1024 px DXT5 (a few DXT1), so a decal the overhaul makes is written the same way.
Endpoints are the block's colour bounds (inset by 1/16), which suits fur and skin, whose colours vary mostly in
brightness. Reading is eu4_import.read_dds.
"""

import struct

from eu4_import import halve


def _expand565(c: int) -> tuple:
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return (r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)


def _pack565(r: float, g: float, b: float) -> int:
    def q(v, bits):
        top = (1 << bits) - 1
        return max(0, min(top, int(v * top / 255 + 0.5)))
    return (q(r, 5) << 11) | (q(g, 6) << 5) | q(b, 5)


def _colour_block(block: list) -> bytes:
    """block: 16 (b, g, r, a) tuples."""
    lo = [min(p[c] for p in block) for c in range(3)]
    hi = [max(p[c] for p in block) for c in range(3)]
    inset = [(hi[c] - lo[c]) / 16 for c in range(3)]
    c0 = _pack565(hi[2] - inset[2], hi[1] - inset[1], hi[0] - inset[0])
    c1 = _pack565(lo[2] + inset[2], lo[1] + inset[1], lo[0] + inset[0])
    if c0 == c1:
        return struct.pack("<HHI", c0, c1, 0)
    if c0 < c1:  # four-colour mode needs c0 > c1
        c0, c1 = c1, c0
    p0, p1 = _expand565(c0), _expand565(c1)
    palette = [p0, p1, tuple((2 * a + b) / 3 for a, b in zip(p0, p1)), tuple((a + 2 * b) / 3 for a, b in zip(p0, p1))]
    bits = 0
    for i, (b, g, r, _) in enumerate(block):
        best, best_d = 0, None
        for k, (pr, pg, pb) in enumerate(palette):
            d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
            if best_d is None or d < best_d:
                best, best_d = k, d
        bits |= best << (2 * i)
    return struct.pack("<HHI", c0, c1, bits)


def _alpha_block(block: list) -> bytes:
    a0, a1 = max(p[3] for p in block), min(p[3] for p in block)
    if a0 == a1:
        return bytes((a0, a1)) + bytes(6)
    palette = [a0, a1] + [((7 - i) * a0 + i * a1) / 7 for i in range(1, 7)]
    bits = 0
    for i, p in enumerate(block):
        best = min(range(8), key=lambda k: abs(p[3] - palette[k]))
        bits |= best << (3 * i)
    return bytes((a0, a1)) + bits.to_bytes(6, "little")


def encode(width: int, height: int, bgra: bytes) -> bytes:
    """DXT5 blocks of one mip level (sides padded up to a multiple of 4 by repeating the edge)."""
    out = bytearray()
    for by in range(0, max(height, 4), 4):
        for bx in range(0, max(width, 4), 4):
            block = []
            for y in range(by, by + 4):
                row = min(y, height - 1) * width
                for x in range(bx, bx + 4):
                    o = (row + min(x, width - 1)) * 4
                    block.append(tuple(bgra[o:o + 4]))
            out += _alpha_block(block) + _colour_block(block)
    return bytes(out)


def _header(width: int, height: int, mips: int) -> bytes:
    head = bytearray(128)
    head[0:4] = b"DDS "
    linear_size = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * 16
    flags = 0x1007 | 0x80000 | (0x20000 if mips > 1 else 0)  # caps|height|width|pixelformat|linearsize(|mipmapcount)
    struct.pack_into("<7I", head, 4, 124, flags, height, width, linear_size, 0, mips)
    struct.pack_into("<2I4s", head, 76, 32, 0x4, b"DXT5")  # pixel format: FourCC
    struct.pack_into("<I", head, 108, 0x401008 if mips > 1 else 0x1000)  # (complex|mipmap|) texture
    return bytes(head)


def write_dds(width: int, height: int, bgra: bytes) -> bytes:
    """DXT5 DDS with a full mip chain down to 1x1, box-filtered from the given pixels."""
    levels = [encode(width, height, bgra)]
    w, h, px = width, height, bgra
    while w > 1 or h > 1:
        w, h, px = halve(w, h, px)
        levels.append(encode(w, h, px))
    return _header(width, height, len(levels)) + b"".join(levels)
