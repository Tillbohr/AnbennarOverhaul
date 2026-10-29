"""Regenerate gui/hud.gui for Anbennar Overhaul.

The HUD tab bar can only be changed by overriding the whole hud.gui, so the submod ships a copy
with the Artificery and Magic main tabs inserted directly below the Situations tab, and a mage's mana
in the resource bar left of gold (as Godherja shows its magic). The copy is taken from
Anbennar's gui/hud.gui if Anbennar ships one, otherwise from the game. Rerun this after every
CK3 patch and Anbennar update:

    python -I tools/build_hud_override.py [--anbennar PATH] [--game PATH]
"""

import argparse
import sys
from pathlib import Path

MARKER = "# Anbennar Overhaul"
BEGIN = f"{MARKER}: begin Artificery and Magic tabs"
END = f"{MARKER}: end Artificery and Magic tabs"
ANCHOR = 'name = "tab_situation"'
TAB_NAME = "tab_aov_artificery"
TEXTURE = "gfx/interface/skinned/hud_maintab/aov_maintab_artificery.dds"  # EU4 Anbennar artifice_tier_emblems_strip.dds, frame 1
MAGIC_TAB_NAME = "tab_aov_magic"
MAGIC_TEXTURE = "gfx/interface/skinned/hud_maintab/aov_maintab_magic.dds"  # EU4 Anbennar magic_center_graphic.dds, 95x95 (tools/build_spells.py)
REL_PATH = Path("gui/hud.gui")

# Mana in the resource bar: shown for mages (the Magic tab's test), left of gold, with gold's end cap moved onto it
MANA_BEGIN = f"{MARKER}: begin mana"
MANA_END = f"{MARKER}: end mana"
MANA_NAME = "aov_mana"
MANA_ICON = "gfx/interface/icons/aov_magic/mana.dds"  # Godherja's icon_mixed_magic_00.dds, resized to 60x60
GOLD_ANCHOR = 'name = "gold"'
END_CAP = 'texture = "gfx/interface/skinned/resource_panel_start.dds"'
PIECE = 'texture = "gfx/interface/skinned/resource_panel_piece.dds"'
MAGE = "[GetScriptedGui('aov_magic_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"

SUBMOD = Path(__file__).resolve().parent.parent
DEFAULT_ANBENNAR = SUBMOD.parent / "anbennar-ck3-dev-master"
DEFAULT_GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")

# Inserted after the Situations tab, indented like the sibling widgets. The two windows share the main-tab
# area, so each tab closes the other's window.
BLOCK = [
    BEGIN,
    "widget_hud_main_tab = {",
    f'\tname = "{TAB_NAME}"',
    "\tvisible = \"[GetScriptedGui('aov_artificery_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\"",
    "",
    '\tblockoverride "maintab_button"',
    "\t{",
    f'\t\ttexture = "{TEXTURE}"',
    "\t\t# Opening then closing a game view closes any open vanilla main tab, which would hide this window",
    "\t\tonclick = \"[ToggleGameView( 'decisions' )]\"",
    "\t\tonclick = \"[CloseGameView( 'decisions' )]\"",
    "\t\tonclick = \"[GetVariableSystem.Clear( 'aov_magic_window' )]\"",
    "\t\tonclick = \"[GetVariableSystem.Toggle( 'aov_artificery_window' )]\"",
    '\t\ttooltip = "AOV_ARTIFICERY_BUTTON"',
    "\t\tdown = \"[GetVariableSystem.Exists( 'aov_artificery_window' )]\"",
    "\t}",
    "}",
    "",
    "widget_hud_main_tab = {",
    f'\tname = "{MAGIC_TAB_NAME}"',
    "\tvisible = \"[GetScriptedGui('aov_magic_available').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]\"",
    "",
    '\tblockoverride "maintab_button"',
    "\t{",
    f'\t\ttexture = "{MAGIC_TEXTURE}"',
    "\t\tonclick = \"[ToggleGameView( 'decisions' )]\"",
    "\t\tonclick = \"[CloseGameView( 'decisions' )]\"",
    "\t\tonclick = \"[GetVariableSystem.Clear( 'aov_artificery_window' )]\"",
    "\t\tonclick = \"[GetVariableSystem.Toggle( 'aov_magic_window' )]\"",
    '\t\ttooltip = "AOV_MAGIC_BUTTON"',
    "\t\tdown = \"[GetVariableSystem.Exists( 'aov_magic_window' )]\"",
    "\t}",
    "}",
    END,
]

# Godherja's gh_magic_resource_widget, laid out like vanilla's gold widget: value, monthly refill, divider
MANA_BLOCK = [
    MANA_BEGIN,
    "widget = {",
    f'\tname = "{MANA_NAME}"',
    f'\tvisible = "{MAGE}"',
    "\tsize = { 144 70 }",
    "",
    "\twidget = {",
    "\t\tsize = { 144 45 }",
    '\t\ttooltip = "AOV_HUD_MANA_TT"',
    "\t\tusing = tooltip_ne",
    "\t}",
    "",
    "\tbackground = {",
    f"\t\t{END_CAP}",
    "\t}",
    "",
    "\tvbox = {",
    "\t\tmargin_top = -2",
    "",
    "\t\thbox = {",
    "\t\t\tlayoutpolicy_horizontal = expanding",
    "\t\t\texpand = {}",
    "",
    "\t\t\thbox = {",
    "\t\t\t\tspacing = 7",
    "",
    "\t\t\t\ticon = {",
    '\t\t\t\t\tname = "aov_mana_icon"',
    "\t\t\t\t\tsize = { 30 30 }",
    f'\t\t\t\t\ttexture = "{MANA_ICON}"',
    "\t\t\t\t}",
    "",
    "\t\t\t\tflowcontainer = {",
    "\t\t\t\t\tmargin_bottom = 7",
    "\t\t\t\t\tspacing = -6",
    "\t\t\t\t\tdirection = vertical",
    "\t\t\t\t\tignoreinvisible = yes",
    "",
    "\t\t\t\t\ttext_single = {",
    '\t\t\t\t\t\tname = "aov_mana_value"',
    "\t\t\t\t\t\ttext = \"[GetPlayer.MakeScope.ScriptValue( 'aov_mana' )|0]\"",
    "\t\t\t\t\t\tmax_width = 50",
    '\t\t\t\t\t\tdefault_format = "#high"',
    "\t\t\t\t\t\tusing = Font_Size_Medium",
    "\t\t\t\t\t}",
    "",
    "\t\t\t\t\ttext_single = {",
    '\t\t\t\t\t\tname = "aov_mana_refill"',
    "\t\t\t\t\t\ttext = \"[GetPlayer.MakeScope.ScriptValue( 'aov_mana_refill_month' )|=1]\"",
    "\t\t\t\t\t\tmax_width = 50",
    '\t\t\t\t\t\tdefault_format = "#low"',
    "\t\t\t\t\t}",
    "\t\t\t\t}",
    "\t\t\t}",
    "\t\t\tspacer = {",
    "\t\t\t\tsize = { 10 1 }",
    "\t\t\t}",
    "\t\t\tdivider_light = {",
    "\t\t\t\tlayoutpolicy_vertical = expanding",
    "\t\t\t\talpha = 0.8",
    "\t\t\t}",
    "\t\t}",
    "\t\texpand = {}",
    "\t}",
    "}",
    MANA_END,
    "",
]


class GeneratorError(Exception):
    pass


def brace_delta(line: str) -> int:
    """Count '{' minus '}' outside double-quoted strings and '#' comments."""
    delta = 0
    in_string = False
    for ch in line:
        if ch == '"':
            in_string = not in_string
        elif in_string:
            continue
        elif ch == "#":
            break
        elif ch == "{":
            delta += 1
        elif ch == "}":
            delta -= 1
    return delta


def insert_tab(text: str) -> str:
    if TAB_NAME in text:
        raise GeneratorError(f"source already contains '{TAB_NAME}'; is it a generated file?")
    lines = text.split("\n")
    try:
        anchor = next(i for i, l in enumerate(lines) if l.strip() == ANCHOR)
    except StopIteration:
        raise GeneratorError(f"anchor '{ANCHOR}' not found; did a CK3 patch rename the Situations tab?")
    try:
        start = next(i for i in range(anchor, -1, -1) if lines[i].strip() == "widget_hud_main_tab = {")
    except StopIteration:
        raise GeneratorError("no 'widget_hud_main_tab = {' opens the Situations tab")

    depth = 0
    for end in range(start, len(lines)):
        depth += brace_delta(lines[end])
        if depth == 0:
            break
    else:
        raise GeneratorError("unbalanced braces in the Situations tab widget")

    indent = lines[start][: len(lines[start]) - len(lines[start].lstrip("\t"))]
    block = [""] + [indent + l if l else "" for l in BLOCK]
    lines[end + 1:end + 1] = block
    return "\n".join(lines)


def insert_mana(text: str) -> str:
    """The mana widget in front of the gold widget; gold's end-cap background only while mana is hidden, a plain
    piece while it shows."""
    if f'name = "{MANA_NAME}"' in text:
        raise GeneratorError(f"source already contains '{MANA_NAME}'; is it a generated file?")
    lines = text.split("\n")
    golds = [i for i, l in enumerate(lines) if l.strip() == GOLD_ANCHOR]
    if len(golds) != 1:
        raise GeneratorError(f"expected one '{GOLD_ANCHOR}' in the resource bar, found {len(golds)}")
    start = golds[0] - 1
    if lines[start].strip() != "widget = {":
        raise GeneratorError("the gold widget does not open with 'widget = {'")
    depth = 0
    for end in range(start, len(lines)):
        depth += brace_delta(lines[end])
        if depth == 0:
            break
    else:
        raise GeneratorError("unbalanced braces in the gold widget")
    try:
        cap = next(i for i in range(start, end) if lines[i].strip() == END_CAP)
    except StopIteration:
        raise GeneratorError("the gold widget has no resource_panel_start.dds background")
    if lines[cap - 1].strip() != "background = {" or lines[cap + 1].strip() != "}":
        raise GeneratorError("the gold widget's end cap is not a plain background block")
    inner = lines[cap][: len(lines[cap]) - len(lines[cap].lstrip("\t"))]
    outer = inner[:-1]
    lines[cap + 1:cap + 1] = [f'{inner}visible = "[Not( {MAGE[1:-1]} )]" {MARKER}: mana takes the end cap']
    lines[cap + 3:cap + 3] = [f"{outer}{MARKER}: begin gold under mana", f"{outer}background = {{", f"{inner}{PIECE}",
                              f'{inner}visible = "{MAGE}"', f"{outer}}}", f"{outer}{MARKER}: end gold under mana"]
    indent = lines[start][: len(lines[start]) - len(lines[start].lstrip("\t"))]
    lines[start:start] = [indent + l if l else "" for l in MANA_BLOCK]
    return "\n".join(lines)


def build(raw: bytes) -> bytes:
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    crlf = "\r\n" in text
    text = insert_mana(insert_tab(text.replace("\r\n", "\n")))
    header = (
        f"{MARKER}: generated by tools/build_hud_override.py from {REL_PATH.as_posix()}.\n"
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
