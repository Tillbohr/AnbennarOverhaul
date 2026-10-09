"""Generate the Magic lifestyle art (icons, perk node, tree backgrounds, progress bars).

Pure Python: reads and writes uncompressed 32-bit BGRA DDS only. Sources are EU4 Anbennar's magic art and a few
uncompressed vanilla CK3 files. Rerun after changing this script:

    python -I tools/build_magic_lifestyle_art.py [--eu4 PATH] [--game PATH]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script's folder
from build_inventions import GeneratorError, dx10_bgra_to_legacy  # noqa: E402
from build_spells import SCHOOLS, read_bgra, write_bgra  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent
DEFAULT_EU4 = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/236850/1385440355")
DEFAULT_GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
EU4_MAGIC = Path("gfx/interface/custom_gui/magic")
TEAL = (200, 190, 40)  # BGR

ICONS = "gfx/interface/icons"
LIFESTYLE = f"{ICONS}/lifestyles/magic_lifestyle.dds"
NODE = f"{ICONS}/lifestyles_perks/node_magic.dds"
BACKGROUND = "gfx/interface/illustrations/lifestyles_background/magic_lifestyle.dds"
BARS = ("gfx/interface/progressbars/aov_progress_magic.dds", "gfx/interface/progressbars/aov_progress_magic_bg.dds")
TREES = ("magic_lifestyle", "aov_arcane_scholar", "aov_battle_mage", "aov_mindweaver")
# name -> (school, slot): the spell frame used as icon
FOCUSES = {"magic_arcane_study_focus": ("divination", 1), "magic_duelist_focus": ("evocation", 1),
           "magic_mindweaving_focus": ("enchantment", 1)}
TRAITS = {"arcane_scholar": ("divination", 6), "battle_mage": ("evocation", 6), "mindweaver": ("enchantment", 6)}

OUTPUTS = {LIFESTYLE: (480, 160), NODE: (180, 60), BACKGROUND: (608, 1552), BARS[0]: (254, 64), BARS[1]: (254, 64)}
OUTPUTS.update({f"{ICONS}/focuses/{n}.dds": (140, 140) for n in FOCUSES})
OUTPUTS.update({f"{ICONS}/traits/{n}.dds": (120, 120) for n in TRAITS})
OUTPUTS.update({f"{ICONS}/lifestyles_perks/trait_{n}.dds": (120, 120) for n in TRAITS})
OUTPUTS.update({f"{ICONS}/lifestyle_tree_backgrounds/{n}.dds": (348, 812) for n in TREES})


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


def tint(px: bytes, bgr: tuple) -> bytes:
    """Recolour: pixel luminance (0-1) times the colour, alpha kept."""
    out = bytearray(len(px))
    for i in range(0, len(px), 4):
        lum = (0.114 * px[i] + 0.587 * px[i + 1] + 0.299 * px[i + 2]) / 255
        for c in range(3):
            out[i + c] = min(255, round(lum * bgr[c]))
        out[i + 3] = px[i + 3]
    return bytes(out)


def brighten(px: bytes, factor: float) -> bytes:
    out = bytearray(px)
    for i in range(0, len(px), 4):
        for c in range(3):
            out[i + c] = min(255, round(px[i + c] * factor))
    return bytes(out)


def crop(px: bytes, w: int, x: int, y: int, cw: int, ch: int) -> bytes:
    return b"".join(px[((y + r) * w + x) * 4:((y + r) * w + x + cw) * 4] for r in range(ch))


def over(dst: bytearray, dw: int, src: bytes, sw: int, sh: int, x: int, y: int) -> None:
    """Alpha-over src (BGRA, non-premultiplied) onto dst at (x, y), clipped to dst."""
    dh = len(dst) // 4 // dw
    for r in range(sh):
        if not 0 <= y + r < dh:
            continue
        for c in range(sw):
            if not 0 <= x + c < dw:
                continue
            s = (r * sw + c) * 4
            a = src[s + 3]
            if a == 0:
                continue
            d = ((y + r) * dw + x + c) * 4
            da = dst[d + 3]
            oa = a + da * (255 - a) / 255
            for k in range(3):
                dst[d + k] = min(255, round((src[s + k] * a + dst[d + k] * da * (255 - a) / 255) / oa))
            dst[d + 3] = min(255, round(oa))


def load(path: Path):
    if not path.is_file():
        raise GeneratorError(f"source art not found: {path}")
    data = path.read_bytes()
    if data[84:88] == b"DX10":
        data = dx10_bgra_to_legacy(data)
    return read_bgra(data)


def spell_icon(strip, school: str, size: int, canvas: int) -> bytes:
    """A 60x60 frame of an EU4 slot strip, resized and centred on a transparent canvas."""
    w, _h, px = strip
    frame = crop(px, w, SCHOOLS.index(school) * 60, 0, 60, 60)
    img = resize(frame, 60, 60, size, size)
    canvas_px = bytearray(canvas * canvas * 4)
    off = (canvas - size) // 2
    over(canvas_px, canvas, img, size, size, off, off)
    return write_bgra(canvas, canvas, bytes(canvas_px))


def build_all(eu4: Path, game: Path) -> dict:
    magic = eu4 / EU4_MAGIC
    gfx = game / "gfx/interface"
    files = {}

    cw, ch, cpx = load(magic / "magic_center_graphic.dds")
    centre = resize(cpx, cw, ch, 150, 150)
    sheet = bytearray(480 * 160 * 4)
    for n, factor in enumerate((1.0, 1.15, 1.3)):
        frame = bytearray(160 * 160 * 4)
        over(frame, 160, brighten(centre, factor), 150, 150, 5, 5)
        for r in range(160):
            o = (r * 480 + n * 160) * 4
            sheet[o:o + 640] = frame[r * 640:(r + 1) * 640]
    files[LIFESTYLE] = write_bgra(480, 160, bytes(sheet))

    w, h, px = load(gfx / "icons/lifestyles_perks/node_learning.dds")
    files[NODE] = write_bgra(w, h, tint(px, TEAL))

    strips = {}

    def strip(slot):
        if slot not in strips:
            strips[slot] = load(magic / f"magic_spell_icons_slot_{slot}_60x60.dds")
        return strips[slot]

    for name, (school, slot) in FOCUSES.items():
        files[f"{ICONS}/focuses/{name}.dds"] = spell_icon(strip(slot), school, 120, 140)
    for name, (school, slot) in TRAITS.items():
        icon = spell_icon(strip(slot), school, 112, 120)
        files[f"{ICONS}/traits/{name}.dds"] = icon
        files[f"{ICONS}/lifestyles_perks/trait_{name}.dds"] = icon

    bw, bh, bpx = load(magic / "magic_bg.dds")
    tree = write_bgra(348, 812, resize(bpx, bw, bh, 348, 812))
    for n in TREES:
        files[f"{ICONS}/lifestyle_tree_backgrounds/{n}.dds"] = tree
    files[BACKGROUND] = write_bgra(608, 1552, resize(bpx, bw, bh, 608, 1552))

    for out, src in zip(BARS, ("progress_purple.dds", "progress_purple_bg.dds")):
        w, h, px = load(gfx / "progressbars" / src)
        files[out] = write_bgra(w, h, tint(px, TEAL))
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--eu4", type=Path, default=DEFAULT_EU4)
    parser.add_argument("--game", type=Path, default=DEFAULT_GAME)
    args = parser.parse_args()
    try:
        files = build_all(args.eu4, args.game)
    except GeneratorError as e:
        sys.exit(f"error: {e}")
    for rel, data in files.items():
        out = SUBMOD / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    print(f"wrote {len(files)} art files")


if __name__ == "__main__":
    main()
