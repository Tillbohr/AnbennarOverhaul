"""Fill the unpainted pixels of CK3's terrain blend maps.

`gfx/map/terrain/detail_index.tga` holds up to four material indices per pixel and `detail_intensity.tga` their
weights (32-bit BGRA, uncompressed, bottom-up rows). A pixel whose four weights are all zero has no material and the
game draws it black. Anbennar's maps have such gaps (a large block in impassable province 2426 and small blocks
scattered over land), so the map-graphics generator fills them:

- a gap smaller than `large` pixels copies the index and weights of a painted 4-neighbour, growing inward pass by pass;
- a gap of `large` pixels or more gets one material at full weight (copying neighbours across it would smear streaks).

Painted pixels are never changed. Standard library only.
"""

import struct
import sys
from array import array
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script's folder
from build_hud_override import GeneratorError  # noqa: E402

Tga = namedtuple("Tga", "width height header pixels footer")

HEADER_SIZE = 18
TYPE_TRUECOLOR = 2
TOP_ORIGIN = 0x20


def read_tga(data: bytes) -> Tga:
    """An uncompressed 32-bit bottom-up TGA (the only kind CK3's terrain blend maps use)."""
    if len(data) < HEADER_SIZE:
        raise GeneratorError("TGA too short for its header")
    id_length, colormap_type, image_type = data[0], data[1], data[2]
    width, height, bpp, descriptor = struct.unpack_from("<HHBB", data, 12)
    if image_type != TYPE_TRUECOLOR or colormap_type != 0 or bpp != 32:
        raise GeneratorError(f"unsupported TGA (type {image_type}, colour map {colormap_type}, {bpp} bpp); "
                             "expected uncompressed 32-bit")
    if descriptor & TOP_ORIGIN:
        raise GeneratorError("unsupported TGA: top-left origin; expected bottom-up rows")
    start = HEADER_SIZE + id_length
    end = start + width * height * 4
    if len(data) < end:
        raise GeneratorError(f"TGA pixel data truncated ({len(data) - start} of {width * height * 4} bytes)")
    return Tga(width, height, data[:start], bytearray(data[start:end]), data[end:])


def write_tga(img: Tga) -> bytes:
    return bytes(img.header) + bytes(img.pixels) + bytes(img.footer)


def _groups(gap: bytearray, width: int, height: int) -> list:
    """Connected groups (4-neighbour) of the pixels flagged in `gap`, each a list of pixel indices, in scan order."""
    seen = bytearray(len(gap))
    groups = []
    for start in range(len(gap)):
        if not gap[start] or seen[start]:
            continue
        seen[start] = 1
        stack = [start]
        group = []
        while stack:
            i = stack.pop()
            group.append(i)
            x = i % width
            for j, ok in ((i - 1, x > 0), (i + 1, x < width - 1), (i - width, i >= width),
                          (i + width, i < len(gap) - width)):
                if ok and gap[j] and not seen[j]:
                    seen[j] = 1
                    stack.append(j)
        groups.append(sorted(group))
    return groups


def fill_unpainted(index: Tga, intensity: Tga, fill_material: int, large: int):
    """Returns (index, intensity, report) with every zero-weight pixel filled; the inputs are not modified.

    report = {"small_groups", "small_pixels", "large_groups", "large_pixels"}."""
    if (index.width, index.height) != (intensity.width, intensity.height):
        raise GeneratorError(f"detail_index is {index.width}x{index.height} but detail_intensity is "
                             f"{intensity.width}x{intensity.height}")
    if not 0 <= fill_material <= 255:
        raise GeneratorError(f"fill material index {fill_material} does not fit a byte")
    width, height = index.width, index.height
    idx = array("I", bytes(index.pixels))
    wgt = array("I", bytes(intensity.pixels))
    gap = bytearray(1 if not w else 0 for w in wgt)
    report = {"small_groups": 0, "small_pixels": 0, "large_groups": 0, "large_pixels": 0}
    fill_index = struct.unpack("<I", bytes((fill_material, 0, 0, 0)))[0]
    fill_weight = struct.unpack("<I", bytes((255, 0, 0, 0)))[0]
    for group in _groups(gap, width, height):
        if len(group) >= large:
            for i in group:
                idx[i] = fill_index
                wgt[i] = fill_weight
                gap[i] = 0
            report["large_groups"] += 1
            report["large_pixels"] += len(group)
            continue
        report["small_groups"] += 1
        report["small_pixels"] += len(group)
        left = group
        while left:
            filled = []
            for i in left:
                x = i % width
                for j, ok in ((i - 1, x > 0), (i + 1, x < width - 1), (i - width, i >= width),
                              (i + width, i < len(gap) - width)):
                    if ok and not gap[j]:
                        filled.append((i, idx[j], wgt[j]))
                        break
            if not filled:  # no painted neighbour at all (cannot happen on a real map): use the fill material
                filled = [(i, fill_index, fill_weight) for i in left]
            for i, iv, wv in filled:  # apply after the pass so a pass only reads the previous state
                idx[i] = iv
                wgt[i] = wv
                gap[i] = 0
            left = [i for i in left if gap[i]]
    return (Tga(width, height, index.header, bytearray(idx.tobytes()), index.footer),
            Tga(width, height, intensity.header, bytearray(wgt.tobytes()), intensity.footer),
            report)
