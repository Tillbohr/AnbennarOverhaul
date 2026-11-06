"""Import the gnoll head art from Victoria 3 Anbennar, once; it is then committed.

The fur is converted to linear colour for the decal, about a minute:

    python -I tools/build_gnoll_portraits.py --import [path/to/vic3/anbennar/mod/folder]

The Vic3 path defaults to ~/anbennar-vicky3-dev-main. The head assets that list the gnoll blend shape are written by
tools/build_head_assets.py.
"""

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the tools folder
import dxt5  # noqa: E402
from eu4_import import read_dds  # noqa: E402

ATTRIBUTE = "gnoll_head_bs"  # read by the aov_gnoll_head gene (common/genes/aov_gnoll_genes.txt)

SUBMOD = Path(__file__).resolve().parent.parent
DEFAULT_VIC3 = Path.home() / "anbennar-vicky3-dev-main"

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
    parser.add_argument("--import", dest="vic3", nargs="?", type=Path, const=DEFAULT_VIC3, required=True,
                        help="Victoria 3 Anbennar mod folder")
    import_vic3(parser.parse_args().vic3)


if __name__ == "__main__":
    main()
