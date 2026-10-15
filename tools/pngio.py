"""Minimal standard-library PNG reader and writer for the map-graphics generator.

Reads non-interlaced PNGs of colour type 0 (grey), 2 (RGB) or 6 (RGBA) at bit depth 8 or 16, with any of
the five row filters. Pixels are returned raw, in PNG row order (top row first) and PNG byte order
(16-bit samples big-endian). Writes the same formats with filter 0 rows at zlib level 6.
"""

import struct
import sys
import zlib
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the tools folder
from build_hud_override import GeneratorError  # noqa: E402

SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 6: 4}
DEPTHS = (8, 16)
IDAT_CHUNK = 1 << 20

Image = namedtuple("Image", "width height bit_depth color_type pixels")


def _stride(width, bit_depth, color_type):
    return width * CHANNELS[color_type] * bit_depth // 8


def _check_format(width, height, bit_depth, color_type):
    if color_type not in CHANNELS or bit_depth not in DEPTHS:
        raise GeneratorError(f"unsupported PNG format: colour type {color_type}, bit depth {bit_depth}")
    if width <= 0 or height <= 0:
        raise GeneratorError(f"empty PNG image {width}x{height}")


def _unfilter_paeth(line, prev, bpp):
    for i in range(bpp):  # left and upper-left are 0, so the predictor is the byte above
        line[i] = (line[i] + prev[i]) & 255
    for i in range(bpp, len(line)):
        a = line[i - bpp]
        b = prev[i]
        c = prev[i - bpp]
        pa = b - c if b > c else c - b
        pb = a - c if a > c else c - a
        pc = a + b - c - c
        if pc < 0:
            pc = -pc
        if pa <= pb and pa <= pc:
            line[i] = (line[i] + a) & 255
        elif pb <= pc:
            line[i] = (line[i] + b) & 255
        else:
            line[i] = (line[i] + c) & 255


def _unfilter(ftype, line, prev, bpp):
    if ftype == 0:
        return
    if ftype == 1:
        for i in range(bpp, len(line)):
            line[i] = (line[i] + line[i - bpp]) & 255
    elif ftype == 2:
        line[:] = bytes((x + b) & 255 for x, b in zip(line, prev))
    elif ftype == 3:
        for i in range(len(line)):
            left = line[i - bpp] if i >= bpp else 0
            line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
    elif ftype == 4:
        _unfilter_paeth(line, prev, bpp)
    else:
        raise GeneratorError(f"unknown PNG filter type {ftype}")


def read_png(data: bytes) -> Image:
    """Decode a PNG file's bytes."""
    if data[:8] != SIGNATURE:
        raise GeneratorError("not a PNG file")
    pos = 8
    header = None
    idat = []
    while pos + 8 <= len(data):
        length, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if len(body) != length:
            raise GeneratorError("truncated PNG chunk")
        if typ == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
        pos += 12 + length
    if header is None or not idat:
        raise GeneratorError("PNG has no IHDR or IDAT chunk")
    width, height, bit_depth, color_type, _compression, _filter, interlace = header
    _check_format(width, height, bit_depth, color_type)
    if interlace:
        raise GeneratorError("interlaced PNGs are not supported")
    raw = zlib.decompress(b"".join(idat))
    stride = _stride(width, bit_depth, color_type)
    if len(raw) < height * (stride + 1):
        raise GeneratorError("PNG image data is shorter than its size")
    bpp = CHANNELS[color_type] * bit_depth // 8
    out = bytearray(height * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        line = bytearray(raw[p + 1:p + 1 + stride])
        _unfilter(raw[p], line, prev, bpp)
        p += 1 + stride
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return Image(width, height, bit_depth, color_type, bytes(out))


def _chunk(typ, body):
    return struct.pack(">I", len(body)) + typ + body + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF)


def write_png(img: Image) -> bytes:
    """Encode an image (filter 0 rows, zlib level 6)."""
    _check_format(img.width, img.height, img.bit_depth, img.color_type)
    stride = _stride(img.width, img.bit_depth, img.color_type)
    if len(img.pixels) != img.height * stride:
        raise GeneratorError(f"{img.width}x{img.height} image needs {img.height * stride} bytes, "
                             f"got {len(img.pixels)}")
    pixels = bytes(img.pixels)
    raw = bytearray()
    for y in range(img.height):
        raw.append(0)
        raw += pixels[y * stride:(y + 1) * stride]
    z = zlib.compress(bytes(raw), 6)
    header = struct.pack(">IIBBBBB", img.width, img.height, img.bit_depth, img.color_type, 0, 0, 0)
    parts = [SIGNATURE, _chunk(b"IHDR", header)]
    parts += [_chunk(b"IDAT", z[i:i + IDAT_CHUNK]) for i in range(0, len(z), IDAT_CHUNK)]
    parts.append(_chunk(b"IEND", b""))
    return b"".join(parts)
