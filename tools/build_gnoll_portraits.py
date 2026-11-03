"""Regenerate the head .asset overrides that give gnolls the Vic3 Anbennar gnoll head.

The gnoll head is a blend shape on the game's own head mesh (same vertices, UVs and triangles), so it must be listed
in the head mesh and the head entity, which Anbennar defines in its copies of the game's male_head.asset and
female_head.asset. Assets can only be overridden as whole files, so the submod ships full copies of those two files with
the gnoll blend shape and its attribute added next to Anbennar's kobold head. Run this after updating the base mod:

    python -I tools/build_gnoll_portraits.py [path/to/anbennar/mod/folder]

The gnoll meshes and textures are imported once from Victoria 3 Anbennar and committed (the fur is converted to linear
colour for the decal, about a minute):

    python -I tools/build_gnoll_portraits.py --import [path/to/vic3/anbennar/mod/folder]

The base path defaults to ../anbennar-ck3-dev-master next to this submod; the Vic3 path to ~/anbennar-vicky3-dev-main.
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
ATTRIBUTE = "gnoll_head_bs"  # read by the aov_gnoll_head gene (common/genes/aov_gnoll_genes.txt)

SUBMOD = Path(__file__).resolve().parent.parent
DEFAULT_ANBENNAR = SUBMOD.parent / "anbennar-ck3-dev-master"
DEFAULT_VIC3 = Path.home() / "anbennar-vicky3-dev-main"

# sex: (asset file, blend shape id, blend shape mesh relative to the asset's folder)
HEADS = {
    "male": ("gfx/models/portraits/male_head/male_head.asset", "male_gnoll_head",
             "blendshapes/aov_gnoll_male_head_bs.mesh"),
    "female": ("gfx/models/portraits/female_head/female_head.asset", "female_gnoll_head",
               "blendshapes/aov_gnoll_female_head_bs.mesh"),
}

# Vic3 Anbennar path -> overhaul path, copied unchanged by --import
IMPORTS = {
    "gfx/models/portraits/male_head/blendshapes/gnoll_head_bs.mesh":
        "gfx/models/portraits/male_head/blendshapes/aov_gnoll_male_head_bs.mesh",
    "gfx/models/portraits/female_head/blendshapes/gnoll_female_head_bs.mesh":
        "gfx/models/portraits/female_head/blendshapes/aov_gnoll_female_head_bs.mesh",
    "gfx/models/portraits/male_head/male_eyes/pupil_gnoll_L.dds":
        "gfx/models/portraits/aov_gnoll/aov_gnoll_eyes_diffuse.dds",
}

# Vic3's fur, rewritten by --import as the head decal. Only the diffuse: Vic3's gnoll normal map is flat and its
# properties have no scattering or specular, so the head keeps CK3's own.
FUR_SOURCE = "gfx/models/portraits/decals/male_head/gnoll/gnoll_head_base_diffuse.dds"
FUR = "gfx/models/portraits/aov_gnoll/aov_gnoll_head_diffuse.dds"


def _to_linear(v: int) -> int:
    c = v / 255
    c = c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return int(c * 255 + 0.5)


_LINEAR = bytes(_to_linear(v) for v in range(256))


def linear_fur(bgra: bytes) -> bytes:
    """The fur with its colour channels converted from sRGB to linear (alpha unchanged). The skin shader reads a decal's
    colour as linear, unlike the head texture it replaces: Vic3's sRGB fur as a decal came out far too light in game
    (dark brown spots as light tan, the dark muzzle near white)."""
    out = bytearray(bgra)
    for i in range(0, len(out), 4):
        out[i], out[i + 1], out[i + 2] = _LINEAR[out[i]], _LINEAR[out[i + 1]], _LINEAR[out[i + 2]]
    return bytes(out)


def fur_dds(vic3_fur: bytes) -> bytes:
    width, height, bgra = read_dds(vic3_fur)
    return dxt5.write_dds(width, height, linear_fur(bgra))


def add_gnoll_head(text: str, sex: str) -> str:
    """Anbennar's head asset with the gnoll blend shape after the kobold head normals and its attribute after the kobold
    head proportions. Exits if either kobold line is missing or repeated."""
    _, shape_id, mesh = HEADS[sex]
    anchors = (
        (re.compile(rf'^(\s*)blend_shape = \{{ id = "{sex}_kobold_head_normals"'),
         '{indent}blend_shape = {{ id = "%s"\t\ttype = "%s" }} %s' % (shape_id, mesh, MARKER)),
        (re.compile(r'^(\s*)attribute = \{ name = "kobold_head_proportions"'),
         '{indent}attribute = {{ name = "%s"\t\tblend_shape = "%s" }} %s' % (ATTRIBUTE, shape_id, MARKER)),
    )
    lines = [l for l in text.split("\n") if not l.endswith(" " + MARKER)]  # idempotent
    for pattern, new in anchors:
        hits = [i for i, l in enumerate(lines) if pattern.match(l)]
        if len(hits) != 1:
            sys.exit(f"error: expected one line matching {pattern.pattern!r} in the {sex} head asset, found {len(hits)}")
        indent = pattern.match(lines[hits[0]]).group(1)
        lines.insert(hits[0] + 1, new.format(indent=indent))
    return "\n".join(lines)


def build(base: Path) -> None:
    for sex, (rel, _, mesh) in HEADS.items():
        src = base / rel
        if not src.is_file():
            sys.exit(f"error: base head asset not found: {src}")
        if not (SUBMOD / Path(rel).parent / mesh).is_file():
            sys.exit(f"error: {mesh} missing; run with --import first")
        raw = src.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        crlf = "\r\n" in text
        text = add_gnoll_head(text.replace("\r\n", "\n"), sex)
        header = (
            f"{MARKER}: generated by tools/build_gnoll_portraits.py from Anbennar's {rel}.\n"
            f"{MARKER}: do not edit by hand; rerun the script after an Anbennar update.\n"
        )
        text = header + text
        if crlf:
            text = text.replace("\n", "\r\n")
        out = SUBMOD / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
        print(f"wrote {out}")


def import_vic3(vic3: Path) -> None:
    for src_rel, out_rel in IMPORTS.items():
        src = vic3 / src_rel
        if not src.is_file():
            sys.exit(f"error: Vic3 Anbennar file not found: {src}")
        out = SUBMOD / out_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, out)
        print(f"copied {out}")
    src = vic3 / FUR_SOURCE
    if not src.is_file():
        sys.exit(f"error: Vic3 Anbennar file not found: {src}")
    (SUBMOD / FUR).write_bytes(fur_dds(src.read_bytes()))
    print(f"wrote {SUBMOD / FUR} (linear colour)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("base", nargs="?", type=Path, default=DEFAULT_ANBENNAR, help="Anbennar CK3 mod folder")
    parser.add_argument("--import", dest="vic3", nargs="?", type=Path, const=DEFAULT_VIC3,
                        help="copy the gnoll art from Victoria 3 Anbennar instead of building the head assets")
    args = parser.parse_args()
    if args.vic3:
        import_vic3(args.vic3)
    else:
        build(args.base)


if __name__ == "__main__":
    main()
