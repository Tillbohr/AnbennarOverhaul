"""Regenerate the teeth gene override that gives orcs Elder Kings 2's tusked teeth.

The template aov_orc_teeth belongs in the game's teeth_accessory gene, in common/genes/02_genes_accessories_misc.txt, which
Anbennar does not override. Gene files can only be overridden whole, so the submod ships the game's file with the template
added between marker comments. Run this after a CK3 patch:

    python -I tools/build_orc_portraits.py [path/to/game]

The art is imported once from Elder Kings 2 (Workshop 2887120253) and committed, under new names, unchanged except the
goblin rags' palette, which is lightened, and the fur mask, which gets the mip chain the game's texture arrays need:

    python -I tools/build_orc_portraits.py --import [path/to/elder/kings/2]

See docs/systems/orc-portraits.md.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the tools folder
import dxt5  # noqa: E402
from eu4_import import read_dds  # noqa: E402

MARKER = "# Anbennar Overhaul"

SUBMOD = Path(__file__).resolve().parent.parent
DEFAULT_ANBENNAR = SUBMOD.parent / "anbennar-ck3-dev-master"
DEFAULT_EK2 = Path("C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/2887120253")
DEFAULT_GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")

TEETH_GENE_FILE = "common/genes/02_genes_accessories_misc.txt"
GENE = "teeth_accessory"
TEMPLATE = "aov_orc_teeth"
MAX_TEMPLATE_INDEX = 255  # DNA stores a gene's template index in one byte

_PORTRAITS = "gfx/models/portraits"
_PATTERNS = "gfx/portraits/accessory_variations/textures/patterns/aov_orc"
_MALE_RAG_SHAPES = ("dwarf", "fat", "gaunt", "infant", "muscular", "old")
_FEMALE_RAG_SHAPES = _MALE_RAG_SHAPES + ("breast_size_max", "pregnant")

# EK2's palette for the rags, written lighter by --import: as shipped the hide sits too close to black skin.
RAG_PALETTE_SOURCE = "gfx/portraits/accessory_variations/textures/color_palette_riekling_02.dds"
RAG_PALETTE = "gfx/portraits/accessory_variations/textures/aov_orc_rags_palette.dds"
RAG_PALETTE_SCALE = 1.8

# EK2's fur mask, rewritten by --import with a full mip chain. The game loads pattern textures into arrays whose members must
# match the first in size, format and mip count, or it crashes on launch. The game's masks have 10 mips; all of EK2's have 2.
FUR_MASK_SOURCE = "gfx/portraits/accessory_variations/textures/patterns/fur/fur_masks.dds"
FUR_MASK = f"{_PATTERNS}/aov_orc_fur_masks.dds"


def _imports() -> dict:
    """Elder Kings 2 path -> overhaul path, copied unchanged by --import."""
    out = {}
    for sex in ("male", "female"):
        head = f"{_PORTRAITS}/{sex}_head"
        out[f"{head}/blendshapes/{sex}_orc_nose.mesh"] = f"{head}/blendshapes/aov_orc_{sex}_nose.mesh"
        out[f"{head}/blendshapes/{sex}_orc_teeth_lips.mesh"] = f"{head}/blendshapes/aov_orc_{sex}_lips.mesh"
        teeth = f"{head}/{sex}_teeth/{sex}_teeth_ek2"
        ours = f"{_PORTRAITS}/aov_orc/aov_orc_{sex}_teeth"
        out[f"{teeth}.mesh"] = f"{ours}.mesh"
        for theirs, mine in (("lower_down", "lower_down"), ("cheek_fat_neg", "cheek_fat_neg"), ("orc_tusks", "tusks")):
            out[f"{teeth}_bs_{theirs}.mesh"] = f"{ours}_bs_{mine}.mesh"
    decals = f"{_PORTRAITS}/decals"
    mine = f"{_PORTRAITS}/aov_orc"
    out[f"{_PORTRAITS}/male_head/blendshapes/male_giantish_head_spikes.mesh"] = (
        f"{_PORTRAITS}/male_head/blendshapes/aov_orc_male_horns.mesh")
    # EK2's versions of these differ from the game's, which every other character keeps
    out[f"{_PORTRAITS}/male_head/male_teeth/male_teeth_diffuse.dds"] = f"{mine}/aov_orc_teeth_diffuse.dds"
    out[f"{_PORTRAITS}/male_head/male_teeth/male_teeth_ssao_color.dds"] = f"{mine}/aov_orc_teeth_ssao_color.dds"
    out[f"{decals}/male_head/mer_head_forehead_01.dds"] = f"{mine}/aov_orc_male_forehead_normal.dds"
    out[f"{decals}/female_head/mer_head_forehead_02.dds"] = f"{mine}/aov_orc_female_forehead_normal.dds"
    for kind in ("diffuse", "normal", "properties"):
        out[f"{decals}/male_head/giant_horns/giantish_horns_01_{kind}.dds"] = f"{mine}/aov_orc_horns_{kind}.dds"
    # EK2's goblin rags, the orcs' everyday clothes
    rags = f"{mine}/rags/aov_orc_rags"
    for theirs, ours, shapes in (
            ("m_clothes/ek2_goblin/com_01/m_clothes_sec_ek2_goblin_com_01", "m_01", _MALE_RAG_SHAPES),
            ("m_clothes/ek2_goblin/com_01/m_clothes_sec_ek2_goblin_com_02", "m_02", _MALE_RAG_SHAPES),
            ("f_clothes/ek2_goblin/com_01/f_clothes_sec_ek2_goblin_com_01", "f_01", _FEMALE_RAG_SHAPES)):
        out[f"{_PORTRAITS}/{theirs}.mesh"] = f"{rags}_{ours}.mesh"
        for shape in shapes:
            out[f"{_PORTRAITS}/{theirs}_bs_{shape}.mesh"] = f"{rags}_{ours}_bs_{shape}.mesh"
    for kind in ("diffuse", "masks", "normal", "properties"):
        out[f"{_PORTRAITS}/m_clothes/ek2_goblin/com_01/m_clothes_sec_ek2_goblin_com_01_{kind}.dds"] = f"{rags}_m_01_{kind}.dds"
    for kind in ("normal", "properties"):
        out[f"gfx/portraits/accessory_variations/textures/patterns/fur/fur_{kind}.dds"] = f"{_PATTERNS}/aov_orc_fur_{kind}.dds"
    return out


IMPORTS = _imports()


def _strip_ours(text: str) -> str:
    return re.sub(rf"[ \t]*{re.escape(MARKER)}: orc teeth.*?{re.escape(MARKER)}: end of orc teeth\n", "", text,
                  flags=re.DOTALL)


def _gene_span(text: str) -> tuple:
    """(start of the gene's body, offset of its closing brace). Exits if the gene is missing."""
    match = re.search(rf"(?m)^\s*{GENE}\s*=\s*\{{", text)
    if not match:
        sys.exit(f"error: gene {GENE} not found in {TEETH_GENE_FILE}")
    depth, at = 1, match.end()
    while depth:
        if at >= len(text):
            sys.exit(f"error: gene {GENE} is not closed in {TEETH_GENE_FILE}")
        depth += {"{": 1, "}": -1}.get(text[at], 0)
        at += 1
    return match.end(), at - 1


def add_orc_teeth(text: str) -> str:
    """The gene file with the orc teeth template at the gene's lowest free index, just before the gene closes. Exits if
    the gene is missing or full."""
    text = _strip_ours(text)
    start, close = _gene_span(text)
    used = {int(i) for i in re.findall(r"\bindex\s*=\s*(\d+)", text[start:close])}
    free = [i for i in range(MAX_TEMPLATE_INDEX + 1) if i not in used]
    if not free:
        sys.exit(f"error: gene {GENE} has no free template index")
    block = (
        f"\t\t{MARKER}: orc teeth (tools/build_orc_portraits.py)\n"
        f"\t\t{TEMPLATE} = {{\n"
        f"\t\t\tindex = {free[0]}\n"
        f'\t\t\tmale = {{ 1 = "male_{TEMPLATE}" }}\n'
        f'\t\t\tfemale = {{ 1 = "female_{TEMPLATE}" }}\n'
        "\t\t\tboy = male\n"
        "\t\t\tgirl = female\n"
        "\t\t}\n"
        f"\t\t{MARKER}: end of orc teeth\n"
    )
    line_start = text.rfind("\n", 0, close) + 1
    return text[:line_start] + block + text[line_start:]


def teeth_gene_bytes(game: bytes) -> bytes:
    """The override's bytes from the game's file, keeping its BOM and line endings."""
    bom = game.startswith(b"\xef\xbb\xbf")
    text = game.decode("utf-8-sig")
    crlf = "\r\n" in text
    text = add_orc_teeth(text.replace("\r\n", "\n"))
    if crlf:
        text = text.replace("\n", "\r\n")
    return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def build(game: Path, anbennar: Path = None) -> None:
    src = game / TEETH_GENE_FILE
    if not src.is_file():
        sys.exit(f"error: game gene file not found: {src}")
    if ((anbennar or DEFAULT_ANBENNAR) / TEETH_GENE_FILE).exists():
        sys.exit(f"error: Anbennar now ships {TEETH_GENE_FILE}, which this override would replace; build from its copy")
    out = SUBMOD / TEETH_GENE_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(teeth_gene_bytes(src.read_bytes()))
    print(f"wrote {out}")


def lighter_palette(dds: bytes) -> bytes:
    """An uncompressed 32-bit palette DDS with its colour channels scaled up, alpha and header unchanged."""
    out = bytearray(dds)
    for i in range(128, len(out)):
        if (i - 128) % 4 != 3:
            out[i] = min(255, int(out[i] * RAG_PALETTE_SCALE))
    return bytes(out)


def full_mip_dds(dds: bytes) -> bytes:
    """The DDS's top level rewritten as a DXT5 with a full mip chain."""
    width, height, bgra = read_dds(dds)
    return dxt5.write_dds(width, height, bgra)


def import_ek2(ek2: Path) -> None:
    missing = [rel for rel in [*IMPORTS, RAG_PALETTE_SOURCE, FUR_MASK_SOURCE] if not (ek2 / rel).is_file()]
    if missing:
        sys.exit(f"error: Elder Kings 2 files not found under {ek2}: {missing}")
    for src_rel, out_rel in IMPORTS.items():
        out = SUBMOD / out_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ek2 / src_rel, out)
        print(f"copied {out}")
    palette = SUBMOD / RAG_PALETTE
    palette.parent.mkdir(parents=True, exist_ok=True)
    palette.write_bytes(lighter_palette((ek2 / RAG_PALETTE_SOURCE).read_bytes()))
    print(f"wrote {palette} (lighter)")
    mask = SUBMOD / FUR_MASK
    mask.write_bytes(full_mip_dds((ek2 / FUR_MASK_SOURCE).read_bytes()))
    print(f"wrote {mask} (full mip chain)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("game", nargs="?", type=Path, default=DEFAULT_GAME, help="CK3 game folder")
    parser.add_argument("--import", dest="ek2", nargs="?", type=Path, const=DEFAULT_EK2,
                        help="copy the orc art from Elder Kings 2 instead of building the gene file")
    args = parser.parse_args()
    if args.ek2:
        import_ek2(args.ek2)
    else:
        build(args.game)


if __name__ == "__main__":
    main()
