"""Helpers for one-time imports from EU4 Anbennar: Workshop paths, localisation, map data, and image readers and
writers (DDS, TGA) to bring EU4 art into CK3.

Nothing in the mod is rebuilt from EU4: import once, commit the result, then edit it in the overhaul. Convert one
EU4 picture into a CK3-ready DDS with:

    python -I tools/eu4_import.py convert <src> <dst> [--root anbennar|cannorian|dwarven] [--upscale2x]
                                          [--resize WxH] [--mips]

<src> is relative to the EU4 mod root (or absolute); <dst> is relative to this mod. A DDS that CK3 reads as it is
(DXT1/3/5, classic BGRA) is copied unchanged unless a resize is asked for; a DX10 BGRA DDS gets a classic header;
TGA, DXT1 and DXT5 are decoded when they must be resized. Resized or decoded output is uncompressed BGRA.
"""

import argparse
import math
import re
import shutil
import struct
import sys
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
    args = parser.parse_args()
    src = args.src if args.src.is_absolute() else EU4_ROOTS[args.root] / args.src
    dst = args.dst if args.dst.is_absolute() else SUBMOD / args.dst
    size = tuple(int(n) for n in args.resize.lower().split("x")) if args.resize else None
    try:
        if not src.is_file():
            raise EU4ImportError(f"{src} not found")
        out = convert(src.read_bytes(), src.suffix.lower() == ".tga", args.upscale2x, size, args.mips)
    except EU4ImportError as e:
        sys.exit(f"error: {e}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if out == src.read_bytes():
        shutil.copyfile(src, dst)
    else:
        dst.write_bytes(out)
    print(f"wrote {dst.relative_to(SUBMOD) if dst.is_relative_to(SUBMOD) else dst} ({len(out)} bytes)")


if __name__ == "__main__":
    main()
