"""Helpers for one-time imports from EU4 Anbennar: Workshop paths, localisation, map data, and image readers and
writers (DDS, TGA) to bring EU4 art into CK3.

Nothing in the mod is rebuilt from EU4: import once, commit the result, then edit it in the overhaul. Convert one
EU4 picture into a CK3-ready DDS with:

    python -I tools/eu4_import.py convert <src> <dst> [--root anbennar|cannorian|dwarven] [--upscale2x]
                                          [--resize WxH] [--mips]

<src> is relative to the EU4 mod root (or absolute); <dst> is relative to this mod. A DDS that CK3 reads as it is
(DXT1/3/5, classic BGRA) is copied unchanged unless a resize is asked for; a DX10 BGRA DDS gets a classic header;
TGA, DXT1 and DXT5 are decoded when they must be resized. Resized or decoded output is uncompressed BGRA.

Export EU4 pictures as PNG for an outside (AI) upscaler, into the git-ignored art_work/ folder:

    python -I tools/eu4_import.py png <src> <dst.png> [--root ...] [--painting]
    python -I tools/eu4_import.py monument-pngs <out dir>

--painting lifts a great-project painting's name plate and crops its frame (clean_painting), as the committed
monument paintings were; monument-pngs does that for every monument with a painting in tools/data/monuments.
"""

import argparse
import math
import re
import shutil
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script's folder
from pdx_script import parse_blocks, strip_comments  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent
_WORKSHOP = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850")
EU4_ROOTS = {
    "anbennar": _WORKSHOP / "1385440355",
    "cannorian": _WORKSHOP / "2811184350",  # Cannorian Monuments
    "dwarven": _WORKSHOP / "2791499822",  # Dwarven Monuments
}
PRECEDENCE = ("cannorian", "dwarven", "anbennar")  # the submods override Anbennar's files


class EU4ImportError(ValueError):
    pass


# --- script and localisation --------------------------------------------------------------------------------------

def read_script(path: Path) -> str:
    """EU4 script files are Latin-1."""
    return path.read_bytes().decode("latin-1")


def top_level(body: str) -> str:
    """body with nested blocks removed, so scalar lookups cannot hit inner keys."""
    out = []
    depth = 0
    for ch in strip_comments(body):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 0 or ch == "\n":
            out.append(ch)
    return "".join(out)


def names_in(body: str) -> list:
    return re.findall(r"[A-Za-z0-9_]+", strip_comments(body))


_LOC_LINE = re.compile(r'^\s*([A-Za-z0-9_.\-]+):\d*\s*"(.*)"\s*(?:#.*)?$')


def _decode_line(raw: bytes) -> str:
    """A loc line as UTF-8; some EU4 Anbennar lines are Windows-1252 (e.g. `Ebbu\\x9aubtu`) inside UTF-8 files."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def loc_pairs(root: Path):
    """(key, text) of every English loc line under root/localisation."""
    folder = root / "localisation"
    if not folder.is_dir():
        return
    for path in sorted(folder.rglob("*_l_english.yml")):
        for line in map(_decode_line, path.read_bytes().removeprefix(b"\xef\xbb\xbf").split(b"\n")):
            m = _LOC_LINE.match(line.rstrip("\r"))
            if m:
                yield m.group(1), m.group(2)


def eu4_loc(roots: dict = EU4_ROOTS) -> dict:
    """key -> text over all roots, the submods winning (PRECEDENCE)."""
    loc = {}
    for source in PRECEDENCE:
        root = roots.get(source)
        if root:
            for key, value in loc_pairs(root):
                loc.setdefault(key, value)
    return loc


def culture_dynasty_names(eu4: Path = EU4_ROOTS["anbennar"]) -> dict:
    """EU4 culture group or culture key -> its dynasty_names, in file order. The cultures file is Windows-1252
    (`Gill\\x9a` and similar), not plain Latin-1."""
    text = strip_comments((eu4 / "common" / "cultures" / "anb_cultures.txt").read_bytes().decode("cp1252"))
    out = {}
    for group, group_body in parse_blocks(text).items():
        children = parse_blocks(group_body)
        for key, body in [(group, children)] + [(k, parse_blocks(v)) for k, v in children.items()]:
            if "dynasty_names" in body:
                out[key] = [a or b for a, b in re.findall(r'"([^"]*)"|([^\s"]+)', body["dynasty_names"])]
    return out


# --- map ----------------------------------------------------------------------------------------------------------

def province_names(eu4: Path = EU4_ROOTS["anbennar"]) -> dict:
    """EU4 province id -> its PROV<id> name."""
    names = {}
    for key, value in loc_pairs(eu4):
        m = re.fullmatch(r"PROV(\d+)", key)
        if m:
            names.setdefault(int(m.group(1)), value)
    return names


def _map_blocks(eu4: Path, name: str) -> dict:
    return parse_blocks(read_script(eu4 / "map" / name))


def province_areas(eu4: Path = EU4_ROOTS["anbennar"]) -> dict:
    """EU4 province id -> area key."""
    area_of = {}
    for area, body in _map_blocks(eu4, "area.txt").items():
        for pid in re.findall(r"\d+", top_level(body)):  # nested color blocks dropped
            area_of.setdefault(int(pid), area)
    return area_of


def region_provinces(regions: tuple, eu4: Path = EU4_ROOTS["anbennar"]) -> set:
    """EU4 province ids of the given region keys (map/region.txt -> areas -> provinces)."""
    areas = _map_blocks(eu4, "area.txt")
    region = _map_blocks(eu4, "region.txt")
    out = set()
    for key in regions:
        if key not in region:
            raise EU4ImportError(f"EU4 region {key} not found in map/region.txt")
        for area in names_in(parse_blocks(region[key]).get("areas", "")):
            out |= {int(p) for p in re.findall(r"\d+", top_level(areas.get(area, "")))}
    return out


def province_superregions(eu4: Path = EU4_ROOTS["anbennar"]) -> dict:
    """EU4 province id -> superregion key, through area -> region -> superregion."""
    region_of = {}
    for region, body in _map_blocks(eu4, "region.txt").items():
        for area in names_in(parse_blocks(body).get("areas", "")):
            region_of.setdefault(area, region)
    super_of = {}
    for sup, body in _map_blocks(eu4, "superregion.txt").items():
        for region in names_in(top_level(body)):
            super_of.setdefault(region, sup)
    result = {}
    for pid, area in province_areas(eu4).items():
        sup = super_of.get(region_of.get(area))
        if sup:
            result[pid] = sup
    return result


def eu4_countries(eu4: Path = EU4_ROOTS["anbennar"]) -> dict:
    """EU4 tag -> its country file's name without folder and extension (e.g. I26 -> 'Salla Elyn'). The flag is
    gfx/flags/<tag>.tga."""
    out = {}
    for path in sorted((eu4 / "common" / "country_tags").glob("*.txt")):
        for tag, file in re.findall(r'^\s*([A-Z0-9]{3})\s*=\s*"([^"]+)"', strip_comments(read_script(path)), re.M):
            out.setdefault(tag, Path(file).stem)
    return out


# --- DDS ----------------------------------------------------------------------------------------------------------

def _dds_header(width: int, height: int, mips: int = 1) -> bytes:
    """Classic A8R8G8B8 DDS header (128 bytes)."""
    head = bytearray(128)
    head[0:4] = b"DDS "
    flags = 0x100F | (0x20000 if mips > 1 else 0)  # caps|height|width|pitch|pixelformat (|mipmapcount)
    struct.pack_into("<7I", head, 4, 124, flags, height, width, width * 4, 0, mips)
    struct.pack_into("<8I", head, 76, 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    struct.pack_into("<I", head, 108, 0x401008 if mips > 1 else 0x1000)  # (complex|mipmap|) texture
    return bytes(head)


def write_bgra(width: int, height: int, pixels: bytes) -> bytes:
    """Classic A8R8G8B8 DDS, no mips."""
    return _dds_header(width, height) + pixels


def halve(width: int, height: int, px: bytes) -> tuple:
    """Box-filter downsample to half size (each side at least 1)."""
    nw, nh = max(width // 2, 1), max(height // 2, 1)
    out = bytearray(nw * nh * 4)
    for y in range(nh):
        for x in range(nw):
            sx = [min(2 * x, width - 1), min(2 * x + 1, width - 1)]
            sy = [min(2 * y, height - 1), min(2 * y + 1, height - 1)]
            for c in range(4):
                total = sum(px[(yy * width + xx) * 4 + c] for yy in sy for xx in sx)
                out[(y * nw + x) * 4 + c] = (total + 2) // 4
    return nw, nh, bytes(out)


def write_dds_mips(width: int, height: int, px: bytes) -> bytes:
    """Uncompressed A8R8G8B8 DDS with a full mip chain (down to 1x1), as CK3 wants for textured emblems."""
    levels = [px]
    w, h = width, height
    while w > 1 or h > 1:
        w, h, p = halve(w, h, levels[-1])
        levels.append(p)
    return _dds_header(width, height, len(levels)) + b"".join(levels)


def dx10_bgra_to_legacy(data: bytes) -> bytes:
    """Rewrite an uncompressed BGRA DDS with a DX10 header (EU4 Anbennar's GUI art) as a classic A8R8G8B8 DDS.
    Same pixels; only the header changes, so the engine needs no DX10 support. Top mip level only."""
    if data[:4] != b"DDS " or data[84:88] != b"DX10":
        raise EU4ImportError("not a DX10 DDS")
    dxgi = struct.unpack("<I", data[128:132])[0]
    if dxgi not in (87, 91):  # B8G8R8A8_UNORM, B8G8R8A8_UNORM_SRGB
        raise EU4ImportError(f"unsupported DXGI format {dxgi}")
    height, width = struct.unpack("<II", data[12:20])
    return write_bgra(width, height, data[148:148 + width * height * 4])


def _rgb565(value: int) -> tuple:
    r, g, b = (value >> 11) & 31, (value >> 5) & 63, value & 31
    return (r * 255 + 15) // 31, (g * 255 + 31) // 63, (b * 255 + 15) // 31


def _colour_block(data: bytes, offset: int, four_colour: bool) -> list:
    """The 16 (r, g, b, a) texels of one DXT colour block."""
    c0, c1, bits = struct.unpack_from("<HHI", data, offset)
    r0, g0, b0 = _rgb565(c0)
    r1, g1, b1 = _rgb565(c1)
    if four_colour or c0 > c1:
        palette = [(r0, g0, b0, 255), (r1, g1, b1, 255),
                   ((2 * r0 + r1) // 3, (2 * g0 + g1) // 3, (2 * b0 + b1) // 3, 255),
                   ((r0 + 2 * r1) // 3, (g0 + 2 * g1) // 3, (b0 + 2 * b1) // 3, 255)]
    else:
        palette = [(r0, g0, b0, 255), (r1, g1, b1, 255),
                   ((r0 + r1) // 2, (g0 + g1) // 2, (b0 + b1) // 2, 255), (0, 0, 0, 0)]
    return [palette[(bits >> (2 * i)) & 3] for i in range(16)]


def _alpha_block(data: bytes, offset: int) -> list:
    """The 16 alpha values of one DXT5 alpha block."""
    a0, a1 = data[offset], data[offset + 1]
    bits = int.from_bytes(data[offset + 2:offset + 8], "little")
    if a0 > a1:
        palette = [a0, a1] + [((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)]
    else:
        palette = [a0, a1] + [((5 - i) * a0 + i * a1) // 5 for i in range(1, 5)] + [0, 255]
    return [palette[(bits >> (3 * i)) & 7] for i in range(16)]


def _decode_blocks(data: bytes, width: int, height: int, dxt5: bool) -> bytes:
    out = bytearray(width * height * 4)
    offset = 128
    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            alpha = None
            if dxt5:
                alpha = _alpha_block(data, offset)
                offset += 8
            texels = _colour_block(data, offset, dxt5)
            offset += 8
            for i, (r, g, b, a) in enumerate(texels):
                x, y = bx + i % 4, by + i // 4
                if x < width and y < height:
                    p = (y * width + x) * 4
                    out[p:p + 4] = bytes((b, g, r, alpha[i] if alpha else a))
    return bytes(out)


def read_dds(data: bytes) -> tuple:
    """(width, height, BGRA bytes) of the top mip level of a classic BGRA, DX10 BGRA, DXT1 or DXT5 DDS."""
    if data[:4] != b"DDS ":
        raise EU4ImportError("not a DDS")
    height, width = struct.unpack("<II", data[12:20])
    flags, fourcc, bits = struct.unpack("<I4sI", data[80:92])
    if fourcc == b"DX10":
        return read_dds(dx10_bgra_to_legacy(data))
    if fourcc in (b"DXT1", b"DXT5"):
        return width, height, _decode_blocks(data, width, height, fourcc == b"DXT5")
    if flags & 0x40 and bits == 32:
        return width, height, data[128:128 + width * height * 4]
    raise EU4ImportError(f"unsupported DDS format {fourcc!r} / {bits} bpp")


# --- TGA ----------------------------------------------------------------------------------------------------------

def read_tga(raw: bytes) -> tuple:
    """(width, height, BGRA bytes, top row first) of a true-colour TGA, raw (type 2) or RLE (type 10), 24 or 32 bpp.
    EU4 flags (gfx/flags/<tag>.tga) are 128x128 RLE."""
    if len(raw) < 18:
        raise EU4ImportError("TGA too short for its header")
    id_len, colormap, kind = raw[0], raw[1], raw[2]
    width, height = struct.unpack("<HH", raw[12:16])
    bpp, desc = raw[16], raw[17]
    if colormap or kind not in (2, 10) or bpp not in (24, 32):
        raise EU4ImportError(f"unsupported TGA (type {kind}, colour map {colormap}, {bpp} bpp)")
    size = bpp // 8
    need = width * height * size
    pos = 18 + id_len
    if kind == 2:
        px = raw[pos:pos + need]
    else:
        out = bytearray()
        while len(out) < need and pos < len(raw):
            head = raw[pos]
            pos += 1
            count = (head & 0x7F) + 1
            if head & 0x80:
                out += raw[pos:pos + size] * count
                pos += size
            else:
                out += raw[pos:pos + size * count]
                pos += size * count
        px = bytes(out[:need])
    if len(px) < need:
        raise EU4ImportError(f"TGA pixel data truncated ({len(px)} of {need} bytes)")
    rows = [px[y * width * size:(y + 1) * width * size] for y in range(height)]
    if not desc & 0x20:  # bottom-up
        rows.reverse()
    bgra = bytearray()
    for row in rows:
        if size == 4:
            bgra += row
        else:
            for x in range(0, len(row), 3):
                bgra += row[x:x + 3] + b"\xff"
    return width, height, bytes(bgra)


# --- resampling ---------------------------------------------------------------------------------------------------

def resize(px: bytes, w: int, h: int, nw: int, nh: int) -> bytes:
    """Bilinear resize of BGRA pixels, interpolating premultiplied colour."""
    pre = []
    for i in range(0, w * h * 4, 4):
        a = px[i + 3]
        pre.append((px[i] * a, px[i + 1] * a, px[i + 2] * a, a * 255))
    xs = []
    for ox in range(nw):
        fx = min(max((ox + 0.5) * w / nw - 0.5, 0.0), w - 1.0)
        x0 = int(fx)
        xs.append((x0, min(x0 + 1, w - 1), fx - x0))
    out = bytearray(nw * nh * 4)
    for oy in range(nh):
        fy = min(max((oy + 0.5) * h / nh - 0.5, 0.0), h - 1.0)
        y0 = int(fy)
        y1 = min(y0 + 1, h - 1)
        ty = fy - y0
        for ox, (x0, x1, tx) in enumerate(xs):
            p00, p01, p10, p11 = pre[y0 * w + x0], pre[y0 * w + x1], pre[y1 * w + x0], pre[y1 * w + x1]
            acc = [(p00[c] * (1 - tx) + p01[c] * tx) * (1 - ty) + (p10[c] * (1 - tx) + p11[c] * tx) * ty
                   for c in range(4)]
            if acc[3] > 0:
                o = (oy * nw + ox) * 4
                for c in range(3):
                    out[o + c] = min(255, round(acc[c] / acc[3] * 255))
                out[o + 3] = min(255, round(acc[3] / 255))
    return bytes(out)


LANCZOS_A = 3


def _lanczos(x: float, a: int = LANCZOS_A) -> float:
    if x == 0:
        return 1.0
    if abs(x) >= a:
        return 0.0
    px = math.pi * x
    return a * math.sin(px) * math.sin(px / a) / (px * px)


def _kernels() -> tuple:
    """The two Lanczos kernels of an exact 2x upscale. Output pixel 2i sits at source i - 0.25 (taps i-3..i+2),
    output pixel 2i+1 at source i + 0.25 (taps i-2..i+3); each kernel is normalised to sum 1."""
    even = [_lanczos(-0.25 - d) for d in range(-LANCZOS_A, LANCZOS_A)]
    odd = [_lanczos(0.25 - d) for d in range(-LANCZOS_A + 1, LANCZOS_A + 1)]
    return [w / sum(even) for w in even], [w / sum(odd) for w in odd]


def _upscale_line(values: list, kernels: tuple) -> list:
    """One row or column of samples upscaled 2x (edges clamped)."""
    n, a = len(values), LANCZOS_A
    padded = [values[0]] * a + values + [values[-1]] * a  # padded[k + a] = values[k]
    even_w, odd_w = kernels
    even = [sum(w * v for w, v in zip(even_w, taps))
            for taps in zip(*(padded[s:s + n] for s in range(0, 2 * a)))]  # padded index i + d + a, d = -a..a-1
    odd = [sum(w * v for w, v in zip(odd_w, taps))
           for taps in zip(*(padded[s:s + n] for s in range(1, 2 * a + 1)))]  # d = -a+1..a
    out = [0.0] * (2 * n)
    out[0::2], out[1::2] = even, odd
    return out


def upscale_2x(width: int, height: int, pixels: bytes) -> tuple:
    """(2*width, 2*height, BGRA bytes): separable Lanczos-3 resampling, clamped to 0..255. Sharper than the game's
    bilinear stretch, without inventing detail (used for the EU4 monument paintings and grove flags)."""
    kernels = _kernels()
    rows = []
    for y in range(height):
        row = pixels[y * width * 4:(y + 1) * width * 4]
        rows.append([_upscale_line(list(row[c::4]), kernels) for c in range(4)])
    w2, h2, a = 2 * width, 2 * height, LANCZOS_A
    out = bytearray(w2 * h2 * 4)
    clamp = lambda v: 0 if v < 0 else 255 if v > 255 else int(v + 0.5)  # noqa: E731
    for i in range(height):
        for parity, (weights, first) in enumerate(((kernels[0], -a), (kernels[1], -a + 1))):
            sources = [rows[min(max(i + d, 0), height - 1)] for d in range(first, first + 2 * a)]
            base = (2 * i + parity) * w2 * 4
            for c in range(4):
                mixed = [sum(w * v for w, v in zip(weights, column)) for column in zip(*(s[c] for s in sources))]
                out[base + c:base + w2 * 4:4] = bytes(clamp(v) for v in mixed)
    return w2, h2, bytes(out)


# --- PNG ----------------------------------------------------------------------------------------------------------

def write_png(width: int, height: int, pixels: bytes) -> bytes:
    """8-bit RGBA PNG of BGRA pixels (for an outside upscaler; the game reads DDS)."""
    px = bytearray(pixels)
    px[0::4], px[2::4] = pixels[2::4], pixels[0::4]
    stride = width * 4
    raw = b"".join(b"\0" + px[y * stride:(y + 1) * stride] for y in range(height))

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def _unfilter(kind: int, row: bytearray, prev: bytes, bpp: int) -> None:
    """Undo one PNG row filter in place (None, Sub, Up, Average, Paeth)."""
    n = len(row)
    if kind == 1:
        for i in range(bpp, n):
            row[i] = (row[i] + row[i - bpp]) & 255
    elif kind == 2:
        row[:] = bytes((a + b) & 255 for a, b in zip(row, prev))
    elif kind == 3:
        for i in range(n):
            row[i] = (row[i] + ((row[i - bpp] if i >= bpp else 0) + prev[i]) // 2) & 255
    elif kind == 4:
        for i in range(n):
            a = row[i - bpp] if i >= bpp else 0
            b, c = prev[i], prev[i - bpp] if i >= bpp else 0
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            row[i] = (row[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
    elif kind != 0:
        raise EU4ImportError(f"bad PNG filter {kind}")


def read_png(data: bytes) -> tuple:
    """(width, height, BGRA bytes) of an 8-bit RGB or RGBA PNG, not interlaced (what upscalers write)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise EU4ImportError("not a PNG")
    pos, idat, head = 8, [], None
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            head = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
        pos += 12 + length
    width, height, depth, colour, _, _, interlace = head
    if depth != 8 or colour not in (2, 6) or interlace:
        raise EU4ImportError(f"unsupported PNG: {depth}-bit, colour type {colour}, interlace {interlace}")
    bpp = 4 if colour == 6 else 3
    raw = zlib.decompress(b"".join(idat))
    stride = width * bpp
    prev, rows = bytes(stride), []
    for y in range(height):
        start = y * (stride + 1)
        row = bytearray(raw[start + 1:start + 1 + stride])
        _unfilter(raw[start], row, prev, bpp)
        rows.append(row)
        prev = row
    rgb = b"".join(rows)
    out = bytearray(width * height * 4)
    out[0::4], out[1::4], out[2::4] = rgb[2::bpp], rgb[1::bpp], rgb[0::bpp]
    out[3::4] = rgb[3::4] if bpp == 4 else b"\xff" * (width * height)
    return width, height, bytes(out)


# --- great-project paintings --------------------------------------------------------------------------------------

# Every EU4 great-project painting (300x150) has a 6 px black and gold frame and a ~50% dark name plate baked
# into its top left (rows 9-29, fading out by x=150).
FRAME_CROP = 7  # the 6 px frame and the row of DXT1 bleed next to it
STRIP_END = 150
STRIP_ROWS = {7: 0.2, 8: 0.06, 9: 0.78, **{y: 1.0 for y in range(10, 29)}, 29: 0.71}


def eu4_file(rel: str) -> Path:
    """The EU4 file at `rel` in the first mod of PRECEDENCE that has it."""
    for source in PRECEDENCE:
        if (EU4_ROOTS[source] / rel).is_file():
            return EU4_ROOTS[source] / rel
    raise EU4ImportError(f"{rel} not found in {', '.join(PRECEDENCE)}")


def _strip_factor(x: int) -> float:
    """How much EU4's name plate darkens column x of a 300x150 painting: 0.46 at the left, back to 1 at x=150
    (median over all 72 paintings, fitted to within ~0.03)."""
    if x >= STRIP_END:
        return 1.0
    return 0.46 + 0.54 * (max(x - 18, 0) / (STRIP_END - 18)) ** 1.4


def lift_title_strip(width: int, height: int, pixels: bytes) -> bytes:
    """Undo the dark name plate EU4 bakes into the top left of every great-project painting (EU4 prints the
    project's name there): divide the plate's rows by the darkening (STRIP_ROWS: share of the full darkening per
    row; the plate's top and bottom rows are partly covered). Colour channels only, clamped to 255."""
    px = bytearray(pixels)
    for y, share in STRIP_ROWS.items():
        if y >= height:
            continue
        for x in range(min(STRIP_END, width)):
            factor = 1 - share * (1 - _strip_factor(x))
            i = (y * width + x) * 4
            for c in range(3):
                px[i + c] = min(255, int(px[i + c] / factor + 0.5))
    return bytes(px)


def crop_frame(width: int, height: int, pixels: bytes) -> tuple:
    """(width, height, BGRA) without EU4's black and gold frame (6 px): FRAME_CROP px off each side, which also drops
    the picture row next to the frame, whose DXT1 blocks mix in frame colours. No more: spires reach the frame."""
    m = FRAME_CROP
    rows = [pixels[(y * width + m) * 4:(y * width + width - m) * 4] for y in range(m, height - m)]
    return width - 2 * m, height - 2 * m, b"".join(rows)


def clean_painting(width: int, height: int, pixels: bytes) -> tuple:
    """A great-project painting with its name plate lifted and its frame cropped (300x150 -> 286x136)."""
    return crop_frame(width, height, lift_title_strip(width, height, pixels))


# --- taller pictures for the county view ------------------------------------------------------------------------

def _blur_row(row: bytes, width: int, radius: int) -> bytearray:
    """Horizontal box blur of one BGRA row (edges clamped)."""
    out = bytearray(len(row))
    for c in range(4):
        v = row[c::4]
        acc = v[0] * (radius + 1) + sum(v[min(i, width - 1)] for i in range(1, radius + 1))
        for x in range(width):
            out[x * 4 + c] = acc // (2 * radius + 1)
            acc += v[min(x + radius + 1, width - 1)] - v[max(x - radius, 0)]
    return out


def _blur_rows(rows: list, radius: int) -> list:
    """Vertical box blur over a list of equal rows (edges clamped to the rows that exist)."""
    out = []
    for y in range(len(rows)):
        window = rows[max(0, y - radius):y + radius + 1]
        out.append(bytearray(sum(col) // len(window) for col in zip(*window)))
    return out


FADE_BLUR = 40  # horizontal blur radius of the fade bands (applied twice)
FADE_DARK = 0.85  # the far edge of a band keeps 15% of the colour
FADE_SEAM = 16  # picture rows next to a band softened into it


def fade_edges(width: int, height: int, pixels: bytes, rows: int) -> tuple:
    """(width, height + 2*rows, BGRA): the picture with `rows` added above and below, its edge rows mirrored,
    blurred hard and fading to dark, so a wide strip (EU4's 4:1 terrain pictures) needs less zoom to fill the 2:1
    county view panel; the FADE_SEAM picture rows at each edge blend into the band."""
    src = [pixels[y * width * 4:(y + 1) * width * 4] for y in range(height)]

    def band(edge: list) -> list:
        out = _blur_rows([_blur_row(_blur_row(edge[min(i, height - 1)], width, FADE_BLUR), width, FADE_BLUR)
                          for i in range(rows)], 12)
        for i, row in enumerate(out):
            f = 1 - FADE_DARK * (i + 1) / rows
            row[:] = bytes(int(v * f) if k % 4 != 3 else v for k, v in enumerate(row))
        return out

    above, below = band(src)[::-1], band(src[::-1])
    all_rows = above + [bytearray(r) for r in src] + below
    seam = min(FADE_SEAM, rows, height // 2)
    for edge in (rows, rows + height):  # the first picture row, the first row of the band below
        lo = max(0, edge - 2 * seam)
        soft = _blur_rows(all_rows[lo:edge + 2 * seam], max(1, seam // 2))
        for i in range(-seam, seam):
            weight = 1 - abs(i + 0.5) / seam
            row, blurred = all_rows[edge + i], soft[edge + i - lo]
            row[:] = bytes(int(a + (b - a) * weight + 0.5) for a, b in zip(row, blurred))
    return width, height + 2 * rows, b"".join(bytes(r) for r in all_rows)


# --- convert ------------------------------------------------------------------------------------------------------

def convert(data: bytes, is_tga: bool, upscale2x: bool = False, size: tuple = None, mips: bool = False) -> bytes:
    """CK3-ready DDS bytes from an EU4 DDS or TGA (see the module docstring)."""
    if not is_tga and not (upscale2x or size or mips):
        if data[84:88] == b"DX10":
            return dx10_bgra_to_legacy(data)
        if data[:4] != b"DDS ":
            raise EU4ImportError("not a DDS")
        return data
    w, h, px = read_tga(data) if is_tga else read_dds(data)
    if upscale2x:
        w, h, px = upscale_2x(w, h, px)
    if size:
        px = resize(px, w, h, *size)
        w, h = size
    return write_dds_mips(w, h, px) if mips else write_bgra(w, h, px)


def to_png(src: Path, painting: bool = False) -> bytes:
    """PNG bytes of an EU4 DDS or TGA, optionally cleaned as a great-project painting (clean_painting)."""
    if not src.is_file():
        raise EU4ImportError(f"{src} not found")
    data = src.read_bytes()
    w, h, px = read_tga(data) if src.suffix.lower() == ".tga" else read_dds(data)
    return write_png(*(clean_painting(w, h, px) if painting else (w, h, px)))


def from_png(data: bytes, size: tuple = None, stretch_y: float = None, fade: int = 0) -> bytes:
    """Uncompressed BGRA DDS (no mips, as the holding illustrations) of an upscaled PNG: optionally resized, then
    stretched vertically by stretch_y, then given `fade` rows above and below (fade_edges)."""
    w, h, px = read_png(data)
    if size:
        px, (w, h) = resize(px, w, h, *size), size
    if stretch_y:
        nh = round(h * stretch_y)
        px, h = resize(px, w, h, w, nh), nh
    if fade:
        w, h, px = fade_edges(w, h, px, fade)
    return write_bgra(w, h, px)


def monument_pngs(out_dir: Path) -> list:
    """Write <eu4_key>.png into out_dir for every monument with a painting (tools/data/monuments), cleaned as the
    committed paintings are; the paths written."""
    import build_monuments  # here: build_monuments imports this module
    written = []
    for m in build_monuments.all_monuments():
        if m["art"]:
            dst = out_dir / f"{m['eu4_key']}.png"
            _write(dst, to_png(eu4_file(m["art"]), painting=True))
            written.append(dst)
    return written


def _write(dst: Path, data: bytes) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)


def _shown(path: Path) -> Path:
    return path.relative_to(SUBMOD) if path.is_relative_to(SUBMOD) else path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("convert", help="convert one EU4 DDS/TGA into a CK3 DDS in this mod")
    c.add_argument("src", type=Path)
    c.add_argument("dst", type=Path)
    c.add_argument("--root", choices=sorted(EU4_ROOTS), default="anbennar")
    c.add_argument("--upscale2x", action="store_true", help="Lanczos-3 2x upscale")
    c.add_argument("--resize", metavar="WxH", help="bilinear resize after any upscale")
    c.add_argument("--mips", action="store_true", help="write a full mip chain (textured emblems)")
    p = sub.add_parser("png", help="export one EU4 DDS/TGA as a PNG (for an outside upscaler)")
    p.add_argument("src", type=Path)
    p.add_argument("dst", type=Path)
    p.add_argument("--root", choices=sorted(EU4_ROOTS), default="anbennar")
    p.add_argument("--painting", action="store_true", help="lift the name plate and crop the frame (great projects)")
    m = sub.add_parser("monument-pngs", help="export every monument painting as a cleaned PNG")
    m.add_argument("out_dir", type=Path)
    d = sub.add_parser("from-png", help="convert upscaled PNGs (a file or a folder) into CK3 DDS files")
    d.add_argument("src", type=Path, help="a PNG, or a folder of PNGs")
    d.add_argument("dst", type=Path, help="the DDS, or the folder for <name>.dds")
    d.add_argument("--resize", metavar="WxH", help="bilinear resize")
    d.add_argument("--stretch-y", type=float, help="stretch vertically by this factor (after any resize)")
    d.add_argument("--fade", type=int, default=0, metavar="ROWS",
                   help="add ROWS blurred rows fading to dark above and below (wide terrain strips)")
    args = parser.parse_args()
    try:
        if args.command == "monument-pngs":
            out_dir = args.out_dir if args.out_dir.is_absolute() else SUBMOD / args.out_dir
            print(f"wrote {len(monument_pngs(out_dir))} PNGs to {_shown(out_dir)}")
            return
        if args.command == "from-png":
            src = args.src if args.src.is_absolute() else SUBMOD / args.src
            dst = args.dst if args.dst.is_absolute() else SUBMOD / args.dst
            size = tuple(int(n) for n in args.resize.lower().split("x")) if args.resize else None
            pairs = ([(p, dst / f"{p.stem}.dds") for p in sorted(src.glob("*.png"))] if src.is_dir()
                     else [(src, dst)])
            if not pairs or not pairs[0][0].is_file():
                raise EU4ImportError(f"no PNG at {src}")
            for png, dds in pairs:
                _write(dds, from_png(png.read_bytes(), size, args.stretch_y, args.fade))
                print(f"wrote {_shown(dds)}")
            return
        src = args.src if args.src.is_absolute() else EU4_ROOTS[args.root] / args.src
        dst = args.dst if args.dst.is_absolute() else SUBMOD / args.dst
        if args.command == "png":
            out = to_png(src, args.painting)
        else:
            if not src.is_file():
                raise EU4ImportError(f"{src} not found")
            size = tuple(int(n) for n in args.resize.lower().split("x")) if args.resize else None
            out = convert(src.read_bytes(), src.suffix.lower() == ".tga", args.upscale2x, size, args.mips)
    except EU4ImportError as e:
        sys.exit(f"error: {e}")
    if out == src.read_bytes():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    else:
        _write(dst, out)
    print(f"wrote {_shown(dst)} ({len(out)} bytes)")


if __name__ == "__main__":
    main()
