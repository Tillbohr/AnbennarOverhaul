"""Regenerate gui/window_county_view.gui for Anbennar Overhaul.

The county view can only be changed by overriding the whole file, so the submod ships a copy that adds the
monument paintings over the holding panel: one background per EU4 painting (build_monuments.
painting_backgrounds), shown when the province has that monument. It also adds a dwarven hold's dig progress bar
(Delve Deeper) where vanilla shows a barony's construction progress. The copy is taken from Anbennar's
gui/window_county_view.gui if Anbennar ships one, otherwise from the game. Rerun this after every CK3 patch and
Anbennar update, and after tools/build_monuments.py when the monument data changes:

    python -I tools/build_county_view_override.py [--anbennar PATH] [--game PATH]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script's folder
import build_monuments  # noqa: E402
from build_hud_override import GeneratorError, brace_delta  # noqa: E402

MARKER = "# Anbennar Overhaul"
REL_PATH = Path("gui/window_county_view.gui")
ANCHOR = "HoldingView.GetHolding.GetIllustration"
DIG_ANCHOR = 'name = "constructing_holding"'

SUBMOD = Path(__file__).resolve().parent.parent
DEFAULT_ANBENNAR = SUBMOD.parent / "anbennar-ck3-dev-master"
DEFAULT_GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")

# The paintings are inline backgrounds right after the vanilla holding illustration, so they cover the holding
# panel as the vanilla art does and draw above the panel's dark background. Never a `using` template: template
# backgrounds are drawn beneath every inline background. They are top-aligned (fittype start), so the top of a
# painting is never trimmed. The vanilla holding illustration is hidden where a painting shows.
VANILLA_VISIBLE = "[HoldingView.HasHolding]"
HIDDEN_UNDER_MONUMENT = ("[And( HoldingView.HasHolding, "
                         "StringIsEmpty( HoldingView.GetProvince.Custom('AovMonumentIllustration') ) )]")


def block() -> list:
    """The inserted lines: a marker and one background per monument painting of every region."""
    return [f"{MARKER}: monument painting"] + build_monuments.painting_backgrounds(build_monuments.all_monuments())


# A running dig (province variable aov_dig_target_level) shows a bar like vanilla's holding construction bar, in the
# same vbox: a hold is never a barony under construction, so the two never show together. The values come from
# common/script_values/aov_hold_view_values.txt, the text from localization/english/aov_hold_view_l_english.yml.
DIG_BLOCK = """\
hbox = {
\tvisible = "[HoldingView.GetProvince.MakeScope.Var('aov_dig_target_level').IsSet]"
\tmargin_bottom = 30

\tprogressbar_standard = {
\t\tname = "aov_hold_dig_progress"
\t\tsize = { 380 30 }
\t\tmin = 0
\t\tmax = 100
\t\tvalue = "[FixedPointToFloat( HoldingView.GetProvince.MakeScope.ScriptValue('aov_dig_percent') )]"
\t\tdirection = horizontal
\t\ttooltip = "AOV_HOLD_DIG_PROGRESS_TT"

\t\ttext_single = {
\t\t\tparentanchor = center
\t\t\ttext = "AOV_HOLD_DIG_PROGRESS"
\t\t\tdefault_format = "#high"
\t\t\talign = nobaseline
\t\t\tusing = Font_Size_Medium
\t\t}
\t}
}"""


def dig_block() -> list:
    """The inserted dig progress lines: a marker and the hbox with the bar."""
    return [f"{MARKER}: hold dig progress"] + DIG_BLOCK.split("\n")


# A dwarven hold has up to 9 more building slots than a castle, and vanilla's one right-aligned row of slots runs off
# the panel. As in RiE's delving view, a hold's buildings sit in a two-row grid at the bottom left of the holding
# panel (datamodel_wrap = 2 without flipdirection: two rows, filled column by column); the duchy, special and great
# building slots stay under the holding box. IS_HOLD is the scripted GUI in common/scripted_guis/aov_hold_view_sgui.txt.
IS_HOLD = "GetScriptedGui('aov_hold_view_is_hold').IsShown( GuiScope.SetRoot( HoldingView.GetProvince.MakeScope ).End )"
GRID_ANCHOR = 'name = "buildings_grid"'
SPECIAL_ANCHOR = 'name = "special_building_no_others"'
GRID_HIDDEN = f'visible = "[Not( {IS_HOLD} )]"'
HOLD_GRID_BLOCK = f"""\
vbox = {{
\tname = "aov_hold_buildings_area"
\tvisible = "[{IS_HOLD}]"
\tlayoutpolicy_vertical = expanding
\tmargin_left = 5

\texpand = {{}}

\tfixedgridbox = {{
\t\tname = "aov_hold_buildings_grid"
\t\tdatamodel = "[HoldingView.GetBuildings]"
\t\tdatamodel_wrap = 2
\t\taddcolumn = 58
\t\taddrow = 58

\t\titem = {{
\t\t\twidget_building_item = {{}}
\t\t}}
\t}}
}}"""


def hold_grid_block() -> list:
    """The inserted hold building grid lines: a marker and the vbox with the grid."""
    return [f"{MARKER}: hold buildings grid"] + HOLD_GRID_BLOCK.split("\n")


def insert_hold_grid(lines: list) -> None:
    """Put the hold grid in the bottom hbox before the expand that follows the BOTTOM LEFT vbox (so it sits left),
    and hide vanilla's building row in a hold."""
    try:
        special = next(i for i, l in enumerate(lines) if SPECIAL_ANCHOR in l)
    except StopIteration:
        raise GeneratorError(f"anchor '{SPECIAL_ANCHOR}' not found; did a CK3 or Anbennar update change the county view?")
    try:
        start = next(i for i in range(special, -1, -1)
                     if lines[i].strip() == "vbox = {" and block_end(lines, i, "a vbox") > special)
        expand = next(i for i in range(start - 1, -1, -1) if lines[i].strip())
    except StopIteration:
        raise GeneratorError("no vbox encloses the special building slot")
    if lines[expand].strip() != "expand = {}":
        raise GeneratorError("the vbox with the special building slot does not follow an 'expand = {}'")
    indent = lines[expand][: len(lines[expand]) - len(lines[expand].lstrip("\t"))]
    lines[expand:expand] = [indent + l if l else "" for l in hold_grid_block()] + [""]
    try:
        grid = next(i for i, l in enumerate(lines) if GRID_ANCHOR in l)
    except StopIteration:
        raise GeneratorError(f"anchor '{GRID_ANCHOR}' not found; did a CK3 or Anbennar update change the county view?")
    indent = lines[grid][: len(lines[grid]) - len(lines[grid].lstrip("\t"))]
    lines.insert(grid + 1, indent + GRID_HIDDEN)


def block_end(lines: list, start: int, what: str) -> int:
    """The line closing the block opened on lines[start]."""
    depth = 0
    for end in range(start, len(lines)):
        depth += brace_delta(lines[end])
        if depth == 0:
            return end
    raise GeneratorError(f"unbalanced braces in {what}")


def insert_dig(lines: list) -> None:
    """Add the dig bar after the hbox holding vanilla's construction progress bar."""
    try:
        anchor = next(i for i, l in enumerate(lines) if DIG_ANCHOR in l)
    except StopIteration:
        raise GeneratorError(f"anchor '{DIG_ANCHOR}' not found; did a CK3 or Anbennar update change the county view?")
    try:
        start = next(i for i in range(anchor, -1, -1)
                     if lines[i].strip() == "hbox = {" and "HoldingView.IsBeingConstructed" in lines[i + 1])
    except StopIteration:
        raise GeneratorError("no 'hbox = {' visible while the holding is being constructed encloses the anchor")
    end = block_end(lines, start, "the holding construction hbox")
    indent = lines[start][: len(lines[start]) - len(lines[start].lstrip("\t"))]
    lines[end + 1:end + 1] = [""] + [indent + l if l else "" for l in dig_block()]


def insert(text: str) -> str:
    if "AovMonumentIllustration" in text:
        raise GeneratorError("source already contains the monument illustration; is it a generated file?")
    lines = text.split("\n")
    try:
        anchor = next(i for i, l in enumerate(lines) if ANCHOR in l)
    except StopIteration:
        raise GeneratorError(f"anchor '{ANCHOR}' not found; did a CK3 or Anbennar update change the county view?")
    try:
        start = next(i for i in range(anchor, -1, -1) if lines[i].strip() == "background = {")
    except StopIteration:
        raise GeneratorError("no 'background = {' opens the holding illustration")
    end = block_end(lines, start, "the holding illustration background")
    visible = [i for i in range(start, end) if lines[i].strip() == f'visible = "{VANILLA_VISIBLE}"']
    if len(visible) != 1:
        raise GeneratorError(f"the holding illustration has no single 'visible = \"{VANILLA_VISIBLE}\"' line")
    lines[visible[0]] = lines[visible[0]].replace(VANILLA_VISIBLE, HIDDEN_UNDER_MONUMENT)
    indent = lines[start][: len(lines[start]) - len(lines[start].lstrip("\t"))]
    lines[end + 1:end + 1] = [""] + [indent + l if l else "" for l in block()]
    insert_dig(lines)
    insert_hold_grid(lines)
    return "\n".join(lines)


def build(raw: bytes) -> bytes:
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    crlf = "\r\n" in text
    text = insert(text.replace("\r\n", "\n"))
    header = (
        f"{MARKER}: generated by tools/build_county_view_override.py from {REL_PATH.as_posix()}.\n"
        f"{MARKER}: do not edit by hand; edit the script and rerun it.\n"
    )
    text = header + text
    if crlf:
        text = text.replace("\n", "\r\n")
    return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def find_source(anbennar: Path, game: Path) -> Path:
    for root in (anbennar, game):
        path = root / REL_PATH
        if path.is_file():
            return path
    raise GeneratorError(f"no {REL_PATH.as_posix()} in {anbennar} or {game}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anbennar", type=Path, default=DEFAULT_ANBENNAR)
    parser.add_argument("--game", type=Path, default=DEFAULT_GAME)
    args = parser.parse_args()
    try:
        src = find_source(args.anbennar, args.game)
        data = build(src.read_bytes())
    except GeneratorError as e:
        sys.exit(f"error: {e}")
    out = SUBMOD / REL_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"wrote {out} (from {src})")


if __name__ == "__main__":
    main()
