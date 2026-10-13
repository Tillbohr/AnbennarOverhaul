"""Codec for CK3's packed heightmap (`map_data/packed_heightmap.png` + `indirection_heightmap.png`).

CK3 draws terrain from the packed files that `map_data/heightmap.heightmap` describes, not from
`heightmap.png`. The map is cut into blocks of `tile_size - 1` (32) pixels. The indirection image has one RGBA
pixel per block: (tile column, tile row, step, level), step = 2 ** level. A block's tile is `32 // step + 1`
pixels square (the extra pixel is the edge shared with the next block), sampled every `step` heightmap pixels,
and sits in the packed image at `(column * size, level_offsets[level].y + row * size)`.

Everything here works in map coordinates: x east, y north, y = 0 at the south edge. All three images run
bottom-up in this format, so PNG rows are flipped only when converting to and from `Grid` and when reading
or writing the indirection image (PNG row = height - 1 - y).
"""

import re
import sys
from array import array
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the tools folder
from build_hud_override import GeneratorError  # noqa: E402
from pngio import Image  # noqa: E402

MAX_TILE_COLUMNS = 256  # the indirection image stores tile columns and rows in one byte each


class Grid:
    """A 16-bit height grid in map coordinates: `values[y * width + x]`, y = 0 at the south edge."""

    def __init__(self, width, height, values):
        if len(values) != width * height:
            raise GeneratorError(f"{width}x{height} grid needs {width * height} values, got {len(values)}")
        self.width = width
        self.height = height
        self.values = values

    def get(self, x, y):
        return self.values[y * self.width + x]

    @classmethod
    def from_png(cls, img):
        if (img.bit_depth, img.color_type) != (16, 0):
            raise GeneratorError(f"height grids are 16-bit grey PNGs, got bit depth {img.bit_depth}, "
                                 f"colour type {img.color_type}")
        rows = array("H")
        rows.frombytes(img.pixels)
        if sys.byteorder == "little":
            rows.byteswap()  # PNG samples are big-endian
        w, h = img.width, img.height
        values = array("H")
        for y in range(h):  # map row y is PNG row h - 1 - y
            values.extend(rows[(h - 1 - y) * w:(h - y) * w])
        return cls(w, h, values)

    def to_png(self):
        w, h = self.width, self.height
        rows = array("H")
        for r in range(h):
            rows.extend(self.values[(h - 1 - r) * w:(h - r) * w])
        if sys.byteorder == "little":
            rows.byteswap()
        return Image(w, h, 16, 0, rows.tobytes())


@dataclass
class Settings:
    """The parsed `heightmap.heightmap`; `text` is the file's text, kept for `settings_text`."""
    tile_size: int
    original_size: tuple
    level_offsets: list
    max_compress_level: int
    empty_tile_offset: tuple
    text: str


@dataclass
class Block:
    """One block's tile: `(32 // step + 1) ** 2` heights, row-major, rows from the south."""
    step: int
    level: int
    tile: list


_PAIR = r"\{\s*(\d+)\s+(\d+)\s*\}"
_KEYS = {
    "tile_size": re.compile(r"(?m)^(\s*tile_size\s*=\s*)(\d+)"),
    "original_heightmap_size": re.compile(rf"(?m)^(\s*original_heightmap_size\s*=\s*){_PAIR}"),
    "level_offsets": re.compile(rf"(?m)^(\s*level_offsets\s*=\s*)(\{{(?:\s*{_PAIR})*\s*\}})"),
    "max_compress_level": re.compile(r"(?m)^(\s*max_compress_level\s*=\s*)(\d+)"),
    "empty_tile_offset": re.compile(rf"(?m)^(\s*empty_tile_offset\s*=\s*)(\{{\s*\d+\s+\d+\s*\}})"),
}


def _find(text, key):
    m = _KEYS[key].search(text)
    if not m:
        raise GeneratorError(f"heightmap.heightmap has no '{key}'")
    return m


def _pairs(text):
    return [(int(a), int(b)) for a, b in re.findall(_PAIR, text)]


def parse_settings(text):
    tile_size = int(_find(text, "tile_size").group(2))
    original = _find(text, "original_heightmap_size")
    level_offsets = _pairs(_find(text, "level_offsets").group(2)[1:])
    max_level = int(_find(text, "max_compress_level").group(2))
    empty = _pairs(_find(text, "empty_tile_offset").group(2))[0]
    if len(level_offsets) != max_level + 1:
        raise GeneratorError(f"heightmap.heightmap has {len(level_offsets)} level_offsets for "
                             f"max_compress_level={max_level}")
    if tile_size < 2 or (tile_size - 1) % (1 << max_level):
        raise GeneratorError(f"tile_size={tile_size} cannot be compressed {max_level} levels")
    return Settings(tile_size, (int(original.group(2)), int(original.group(3))), level_offsets, max_level,
                    empty, text)


def _replace(text, key, value):
    m = _find(text, key)
    return text[:m.start(2)] + value + text[m.end(2):]


def settings_text(s, level_offsets, empty_tile_offset):
    """The settings file's text with new `level_offsets` and `empty_tile_offset`; every other byte is kept."""
    if len(level_offsets) != s.max_compress_level + 1:
        raise GeneratorError(f"{len(level_offsets)} level offsets for max_compress_level={s.max_compress_level}")
    text = s.text
    if list(level_offsets) != s.level_offsets:
        text = _replace(text, "level_offsets",
                        "{ " + " ".join(f"{{ {x} {y} }}" for x, y in level_offsets) + " }")
    if tuple(empty_tile_offset) != s.empty_tile_offset:
        text = _replace(text, "empty_tile_offset", f"{{ {empty_tile_offset[0]} {empty_tile_offset[1]} }}")
    return text


def _block_px(s):
    return s.tile_size - 1


def _blocks_across(s):
    bp = _block_px(s)
    return -(-s.original_size[0] // bp), -(-s.original_size[1] // bp)


def _read_tile(packed, ox, oy, size, what):
    if ox < 0 or oy < 0 or ox + size > packed.width or oy + size > packed.height:
        raise GeneratorError(f"{what}: tile at ({ox}, {oy}) of size {size} lies outside the "
                             f"{packed.width}x{packed.height} packed heightmap")
    tile = []
    w = packed.width
    for j in range(size):
        base = (oy + j) * w + ox
        tile.extend(packed.values[base:base + size])
    return tile


def unpack(indirection, packed, s):
    """Every block's tile, keyed `(bx, by)` with by from the south."""
    nbx, nby = _blocks_across(s)
    if (indirection.width, indirection.height, indirection.bit_depth, indirection.color_type) != (nbx, nby, 8, 6):
        raise GeneratorError(f"indirection image must be {nbx}x{nby} 8-bit RGBA, got {indirection.width}x"
                             f"{indirection.height} (bit depth {indirection.bit_depth}, colour type "
                             f"{indirection.color_type})")
    bp = _block_px(s)
    px = indirection.pixels
    blocks = {}
    for by in range(nby):
        row_start = (nby - 1 - by) * nbx * 4
        for bx in range(nbx):
            o = row_start + bx * 4
            column, row, step, level = px[o], px[o + 1], px[o + 2], px[o + 3]
            if level > s.max_compress_level or step != 1 << level:
                raise GeneratorError(f"block ({bx}, {by}): step {step} and level {level} do not match")
            size = bp // step + 1
            tile = _read_tile(packed, column * size, s.level_offsets[level][1] + row * size, size,
                              f"block ({bx}, {by})")
            blocks[(bx, by)] = Block(step, level, tile)
    return blocks


def empty_tile(packed, s):
    """The tile at `empty_tile_offset` (column, row of the coarsest level)."""
    level = s.max_compress_level
    size = (_block_px(s) >> level) + 1
    column, row = s.empty_tile_offset
    return _read_tile(packed, column * size, s.level_offsets[level][1] + row * size, size, "empty tile")


def sample(grid, bx, by, step, block_px=32):
    """Heights at `(bx*32 + i*step, by*32 + j*step)`, clamped to the grid edge; row-major, rows from the south."""
    size = block_px // step + 1
    x0, y0 = bx * block_px, by * block_px
    xs = [min(x0 + i * step, grid.width - 1) for i in range(size)]
    values = grid.values
    out = []
    for j in range(size):
        base = min(y0 + j * step, grid.height - 1) * grid.width
        out.extend(values[base + x] for x in xs)
    return out


def _interpolates(tile, size, step, full, n, tolerance):
    """True when `tile`, bilinearly interpolated back to n x n, is within `tolerance` of `full` everywhere."""
    for y in range(n):
        j = min(y // step, size - 2)
        fy = (y - j * step) / step
        r0, r1 = j * size, (j + 1) * size
        for x in range(n):
            i = min(x // step, size - 2)
            fx = (x - i * step) / step
            low = tile[r0 + i] + (tile[r0 + i + 1] - tile[r0 + i]) * fx
            high = tile[r1 + i] + (tile[r1 + i + 1] - tile[r1 + i]) * fx
            if abs(low + (high - low) * fy - full[y * n + x]) > tolerance:
                return False
    return True


def choose_level(grid, bx, by, tolerance, max_level=4, block_px=32):
    """The coarsest level whose tile matches the block's heights within `tolerance`; level 0 always does."""
    n = block_px + 1
    full = sample(grid, bx, by, 1, block_px)
    for level in range(max_level, 0, -1):
        step = 1 << level
        if _interpolates(sample(grid, bx, by, step, block_px), block_px // step + 1, step, full, n, tolerance):
            return level
    return 0


def changed_blocks(old, new, block_px=32):
    """Blocks whose footprint `[bx*32, bx*32+32] x [by*32, by*32+32]` holds a changed height."""
    if (old.width, old.height) != (new.width, new.height):
        raise GeneratorError(f"grids differ in size: {old.width}x{old.height} and {new.width}x{new.height}")
    w = old.width
    changed = set()
    for y in range(old.height):
        a = old.values[y * w:(y + 1) * w]
        b = new.values[y * w:(y + 1) * w]
        if a == b:
            continue
        bys = {y // block_px}
        if y % block_px == 0 and y > 0:
            bys.add(y // block_px - 1)
        for x in range(w):
            if a[x] != b[x]:
                bxs = {x // block_px}
                if x % block_px == 0 and x > 0:
                    bxs.add(x // block_px - 1)
                changed.update((bx, by) for bx in bxs for by in bys)
    return changed


def pack(blocks, packed_width, s, empty_tile=None):
    """Lay the blocks out as a packed grid and indirection image.

    Per level, blocks in (by, bx) order fill rows of `min(256, packed_width // size)` tiles; the level bands
    are stacked from y = 0 without overlap. The empty tile (zeros unless given) follows the last tile of the
    coarsest level. Returns (packed grid, indirection image, level_offsets, empty_tile_offset).
    """
    nbx, nby = _blocks_across(s)
    bp = _block_px(s)
    top = s.max_compress_level
    expected = {(bx, by) for by in range(nby) for bx in range(nbx)}
    if set(blocks) != expected:
        missing, extra = sorted(expected - set(blocks)), sorted(set(blocks) - expected)
        raise GeneratorError(f"blocks do not cover the {nbx}x{nby} block map: missing {missing[:5]}, "
                             f"extra {extra[:5]}")
    by_level = [[] for _ in range(top + 1)]
    for key in sorted(blocks, key=lambda k: (k[1], k[0])):
        b = blocks[key]
        if not 0 <= b.level <= top or b.step != 1 << b.level:
            raise GeneratorError(f"block {key}: step {b.step} and level {b.level} do not match")
        size = bp // b.step + 1
        if len(b.tile) != size * size:
            raise GeneratorError(f"block {key}: level {b.level} tile needs {size * size} heights, "
                                 f"got {len(b.tile)}")
        by_level[b.level].append((key, b.tile))
    empty_size = (bp >> top) + 1
    empty = [0] * (empty_size * empty_size) if empty_tile is None else list(empty_tile)
    if len(empty) != empty_size * empty_size:
        raise GeneratorError(f"empty tile needs {empty_size * empty_size} heights, got {len(empty)}")
    by_level[top].append((None, empty))

    offsets = []
    placed = []  # (key, tile, size, x, y, column, row, level)
    y = 0
    for level, entries in enumerate(by_level):
        offsets.append((0, y))
        if not entries:
            continue
        size = (bp >> level) + 1
        cols = min(MAX_TILE_COLUMNS, packed_width // size)
        if cols < 1:
            raise GeneratorError(f"packed width {packed_width} cannot hold a level {level} tile ({size} px)")
        rows = -(-len(entries) // cols)
        if rows > MAX_TILE_COLUMNS:
            raise GeneratorError(f"level {level} needs {rows} tile rows; the indirection image holds 256")
        for k, (key, tile) in enumerate(entries):
            column, row = k % cols, k // cols
            placed.append((key, tile, size, column * size, y + row * size, column, row, level))
        y += rows * size

    values = array("H", bytes(2 * packed_width * y))
    ind = bytearray(nbx * nby * 4)
    empty_offset = None
    for key, tile, size, x0, y0, column, row, level in placed:
        try:
            for j in range(size):
                base = (y0 + j) * packed_width + x0
                values[base:base + size] = array("H", tile[j * size:(j + 1) * size])
        except OverflowError:
            raise GeneratorError(f"block {key}: height outside 0-65535") from None
        if key is None:
            empty_offset = (column, row)
        else:
            bx, by = key
            o = ((nby - 1 - by) * nbx + bx) * 4
            ind[o:o + 4] = bytes((column, row, 1 << level, level))
    return Grid(packed_width, y, values), Image(nbx, nby, 8, 6, bytes(ind)), offsets, empty_offset
