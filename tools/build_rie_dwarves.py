"""Import Realms in Exile's dwarf buildings, mines and ore deposits into Anbennar Overhaul.

Every block of RiE's dwarf and mine building files is rewritten for Anbennar by tools/rie_dwarf_rewrite.py (rules in
tools/data/rie_dwarves.py; spec docs/superpowers/specs/2026-10-17-rie-dwarves-design.md) and checked: every building,
scripted trigger, cultural parameter, script value and modifier it names must exist in Anbennar or the game or be
copied with it (RiE-only script values go to VALUES_FILE), and no building key may be one Anbennar or the game
defines. Also writes RiE's 15 ore deposit modifiers verbatim, the localization of everything copied and the building
type icons, gives tools/build_holds.py the hold level effects (depths_level_effects) and writes the dig
prerequisites of each hold level (aov_hold_dig_requirements_<n>_trigger, from RiE's depths levels). Rerun after an
RiE, Anbennar or CK3 update:

    python -I tools/build_rie_dwarves.py [--rie PATH] [--anbennar PATH] [--game PATH]
"""

import argparse
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_holding_models as bhm  # noqa: E402
import build_portraits as bp  # noqa: E402
import rie_dwarf_rewrite as rw  # noqa: E402
from build_hud_override import GeneratorError  # noqa: E402
from data import rie_dwarves as data  # noqa: E402

Roots = bp.Roots
SUBMOD = bp.SUBMOD
MARKER = bp.MARKER
BOM = bp.BOM

BUILDINGS_FILE = "common/buildings/aov_rie_dwarven_buildings.txt"
MINES_FILE = "common/buildings/aov_rie_mines.txt"
ORE_MODIFIERS_FILE = "common/modifiers/aov_rie_ore_modifiers.txt"
VALUES_FILE = "common/script_values/aov_rie_dwarf_values.txt"
TRIGGERS_FILE = "common/scripted_triggers/aov_rie_dwarf_triggers.txt"
# zz_: loads after Anbennar's and the game's trigger files, so its single-object overrides win.
TERRAIN_GATES_FILE = "common/scripted_triggers/zz_aov_rie_dwarf_terrain_gates.txt"
# graphics/zz_: sorts after Anbennar's defines/graphics/00_graphics.txt and the game's defines/graphic/00_graphics.txt.
LEVEL_DEFINES_FILE = "common/defines/graphics/zz_aov_rie_building_level_defines.txt"
DEPOSIT_EFFECTS_FILE = "common/scripted_effects/aov_rie_deposit_effects.txt"
RIE_HOLDINGS_FILE = "common/holdings/lotr_holdings.txt"
RIE_CASTLE_FILE = "common/holdings/00_holdings.txt"
BACKGROUNDS_FILE = "common/event_backgrounds/aov_dwarven_expedition_backgrounds.txt"
LOC_FILE = "localization/english/aov_rie_dwarves_l_english.yml"
ICON_DIR = "gfx/interface/icons/building_types"
OUTPUTS = {data.RIE_BUILDING_FILES[0]: BUILDINGS_FILE, data.RIE_BUILDING_FILES[1]: MINES_FILE}
# Folders where this generator's files are the aov_rie_* ones (FreshnessTests scans them for orphans).
OWNED_FOLDERS = {"common/buildings": ("aov_rie_*",), "common/modifiers": ("aov_rie_*",),
                 "common/script_values": ("aov_rie_*",), "localization/english": ("aov_rie_*",),
                 "common/scripted_triggers": ("aov_rie_dwarf_*", "zz_aov_rie_dwarf_*"),
                 "common/scripted_effects": ("aov_rie_deposit_*",),
                 "common/event_backgrounds": ("aov_dwarven_expedition_*",),
                 "gfx/interface/illustrations/activity_backgrounds": ("lotr_cave_interior.dds",),
                 "gfx/interface/illustrations/event_scenes": ("lotr_halls.dds", "lotr_dwarven_gate.dds"),
                 "gfx/interface/icons/activities": ("activity_dwarven_expedition*.dds",),
                 "gfx/interface/icons/activity_phases": ("aov_expedition_*.dds",),
                 "gfx/interface/icons/activity_option_categories": ("aov_expedition_*.dds",),
                 "gfx/interface/icons/activity_types": ("aov_expedition_*.dds",),
                 "gfx/interface/illustrations/activity_header_backgrounds": ("activity_dwarven_expedition.dds",),
                 "gfx/interface/illustrations/activity_types": ("aov_expedition_*.dds",),
                 "gfx/interface/icons/holding_types_tab": ("dwarven_hold_holding.dds",),
                 "common/defines/graphics": ("zz_aov_rie_*",)}
# Localization of keys the generator itself defines (not copied from RiE).
OWN_LOC = {
    "aov_rie_surface_dwarf_tt": "Held by a dwarf outside a dwarven hold",
    "aov_rie_mountain_terrain_tt": "In mountains or dwarven terrain",
    "aov_rie_hill_terrain_tt": "In hills, mountains or dwarven terrain",
    "aov_rie_vanilla_building_ground_tt": "Not held by a dwarf in a dwarven hold, hills, mountains or dwarven "
                                          "terrain, where dwarves raise dwarven buildings instead",
}
HOLD_LEVELS = tuple(f"dwarven_hold_{n:02d}" for n in range(1, 11))  # defined by tools/build_holds.py
VALUE_FIELDS = ("cost_gold", "cost_prestige", "cost_piety", "levy", "max_garrison", "garrison_reinforcement_factor",
                "construction_time")
LEVEL_FIELDS = ("levy", "max_garrison", "garrison_reinforcement_factor")
DEPTHS_KEY = re.compile(r"dwarven_depths_(\d\d)$")
TERRAIN_REQUIREMENT = re.compile(r"building_\w+_requirement_terrain")
NEGATED_TERRAIN_REQUIREMENT = re.compile(r"\b(building_\w+_requirement_terrain)\s*=\s*no\b")
GROUND_GATE = "aov_rie_vanilla_building_ground_trigger = yes"
GROUND_GATE_MARK = "# Anbennar Overhaul: no vanilla building for a dwarf on dwarven ground"

ITEM_START = re.compile(r"\s*([A-Za-z_@][\w.\-]*)\s*=")
YES_NO = re.compile(r"(?<![\w.:])([A-Za-z_]\w*)\s*=\s*(?:yes|no)\b")
BLOCK_NAME = re.compile(r"(?<![\w.:])([A-Za-z_]\w*)\s*=\s*\{")
BUILDING_REF = re.compile(r"\b(has_building|has_building_or_higher|next_building)\s*=\s*(\w+)")
PARAMETER_REF = re.compile(r"\b(?:parameter|has_cultural_parameter)\s*=\s*(\w+)")
INNOVATION_REF = re.compile(r"\bhas_innovation\s*=\s*(\w+)")
VALUE_REF = re.compile(r"(?m)^\s*(" + "|".join(VALUE_FIELDS) + r")\s*=\s*([A-Za-z_]\w*)\s*$")
MODIFIER_LINE = re.compile(r"(?m)^\s*([A-Za-z_]\w*)\s*=\s*([^\s{}#]+)")
LOC_REF = re.compile(r"\b(?:text|effect_desc|desc)\s*=\s*([A-Za-z_]\w*)")
LOC_LINE = re.compile(r"^\s*([\w.\-']+):\d*\s*\"")
DOLLAR_REF = re.compile(r"\$([A-Za-z_][\w.\-]*)(?:\|[^$]*)?\$")
CONCEPT_REF = re.compile(r"\[([A-Za-z_]\w*)\|[Ee]\]")
ICON_REF = re.compile(r'\btype_icon\s*=\s*"?([\w.\-]+\.dds)"?')


def HEADER(comment="#") -> list:
    return [f"{comment} Anbennar Overhaul: generated by tools/build_rie_dwarves.py from Realms in Exile and Anbennar.",
            f"{comment} Anbennar Overhaul: do not edit by hand; rerun the generator after an RiE, Anbennar or CK3 update."]


def txt_file(pieces: list) -> bytes:
    return (BOM + "\n".join(HEADER()) + "\n\n" + "\n".join(pieces)).encode("utf-8")


# ---------------------------------------------------------------------------------------------------------- parsing

def top_level_items(text: str) -> list:
    """[(name, text)] of the top-level `name = value` and `name = { ... }` items, in file order (comments outside
    them skipped)."""
    items, depth, current = [], 0, None
    for line in text.split("\n"):
        code = bhm.strip_comment(line)
        if depth == 0 and current is None:
            match = ITEM_START.match(code)
            if not match:
                continue
            current = (match.group(1), [])
        if current is not None:
            current[1].append(line)
        depth += code.count("{") - code.count("}")
        if depth <= 0:
            depth = 0
            if current is not None:
                items.append((current[0], "\n".join(current[1]) + "\n"))
                current = None
    return items


def rie_blocks(roots: Roots, rel: str) -> list:
    """[(key, LF text)] of the top-level blocks of an RiE file (from the start of the key's line to the end of the
    closing line)."""
    text = bp.lf(bp.read(roots.rie / rel))
    return [(names[0], text[start:end]) for names, start, end in bp.blocks(text, 1, strict=False)]


def reindent(text: str, base: int = 0) -> str:
    """text with every line indented by tabs by its brace depth (plus base) and trailing blanks removed."""
    out, depth = [], base
    for line in text.split("\n"):
        stripped = line.strip()
        code = bhm.strip_comment(line).strip()
        if not stripped:
            out.append("")
            continue
        closing = len(re.match(r"[}\s]*", code).group(0).replace(" ", "").replace("\t", ""))
        out.append("\t" * max(depth - closing, 0) + stripped)
        depth += code.count("{") - code.count("}")
    return "\n".join(out)


def removal_note(title: str, notes: list) -> str:
    """One note listing the rewrite's removals grouped by rule, levels (_NN) and amounts (N) merged, with counts."""
    counts = Counter(re.sub(r"(=\s*)-?\d+(?:\.\d+)?$", r"\1N", re.sub(r"_\d\d(?!\d)", "_NN", note)) for note in notes)
    return f"{title} ({sum(counts.values())} in all): " + "; ".join(f"{item} x{n}" for item, n in sorted(counts.items()))


# ------------------------------------------------------------------------------------------- Anbennar and game

def _names(texts) -> frozenset:
    return frozenset(name for _path, text in texts for name, _item in top_level_items(text))


@lru_cache(maxsize=None)
def external_buildings(roots: Roots) -> frozenset:
    return _names(bp.effective_texts(roots, "common/buildings"))


@lru_cache(maxsize=None)
def external_innovations(roots: Roots) -> frozenset:
    return _names(bp.effective_texts(roots, "common/culture/innovations"))


@lru_cache(maxsize=None)
def external_script_values(roots: Roots) -> frozenset:
    return _names(bp.effective_texts(roots, "common/script_values"))


@lru_cache(maxsize=None)
def external_scripted(roots: Roots) -> frozenset:
    """Scripted triggers and scripted modifiers (ai_value) of Anbennar and the game."""
    return _names(bp.effective_texts(roots, "common/scripted_triggers")) | _names(
        bp.effective_texts(roots, "common/scripted_modifiers"))


@lru_cache(maxsize=None)
def external_static_modifiers(roots: Roots) -> frozenset:
    return _names(bp.effective_texts(roots, "common/modifiers"))


@lru_cache(maxsize=None)
def external_tokens(roots: Roots) -> tuple:
    """(every key used in Anbennar's and the game's common/ files, every name used there as `name = yes|no`): what
    script really uses, so engine triggers, fields and modifiers count as known."""
    keys, yes_no = set(), set()
    for root in (roots.anbennar / "common", roots.game / "game/common"):
        for _path, text in bp._texts(str(root), "*.txt"):
            code = bp.code(text)
            keys.update(re.findall(r"\b([A-Za-z_]\w*)\s*(?:=|<|>)", code))
            yes_no.update(YES_NO.findall(code))
    return frozenset(keys), frozenset(yes_no)


@lru_cache(maxsize=None)
def known_parameters(roots: Roots) -> frozenset:
    """Cultural parameters Anbennar or the game define (`parameters = { X = yes }` in common/culture)."""
    found = set()
    for _path, text in bp.effective_texts(roots, "common/culture"):
        for names, start, end in bp.blocks(text, None, strict=False):
            if names[-1] == "parameters":
                found.update(re.findall(r"\b(\w+)\s*=\s*yes\b", bp.code(text[start:end])))
    return frozenset(found)


@lru_cache(maxsize=None)
def external_loc_keys(roots: Roots) -> frozenset:
    keys = set()
    for root in (roots.anbennar, roots.game / "game"):
        for _path, text in bp._texts(str(root / "localization/english"), "*.yml"):
            for line in text.split("\n"):
                match = LOC_LINE.match(line)
                if match:
                    keys.add(match.group(1))
    return frozenset(keys)


@lru_cache(maxsize=None)
def external_concepts(roots: Roots) -> frozenset:
    """Game concepts of Anbennar and the game, with their aliases."""
    texts = bp.effective_texts(roots, "common/game_concepts")
    aliases = {word for _path, text in texts for body in re.findall(r"\balias\s*=\s*\{([^}]*)\}", bp.code(text))
               for word in body.split()}
    return _names(texts) | frozenset(aliases)


# ------------------------------------------------------------------------------------------------------------ RiE

@lru_cache(maxsize=None)
def rie_scripted_triggers(roots: Roots) -> frozenset:
    return _names(bp._texts(str(roots.rie / "common/scripted_triggers"), "*.txt"))


@lru_cache(maxsize=None)
def rie_values(roots: Roots) -> dict:
    """name -> (file, text) of RiE's script values and file-local @variables (first definition wins); @variables
    are keyed (file, @name)."""
    index = {}
    for path, text in bp._texts(str(roots.rie / "common/script_values"), "*.txt"):
        for name, item in top_level_items(bp.lf(text)):
            index.setdefault((path, name) if name.startswith("@") else name, (path, item))
    return index


@lru_cache(maxsize=None)
def rie_loc(roots: Roots) -> dict:
    """key -> line (stripped) of RiE's English localization; the first definition wins."""
    index = {}
    for _path, text in bp._texts(str(roots.rie / "localization/english"), "*.yml"):
        for line in bp.lf(text).split("\n"):
            match = LOC_LINE.match(line)
            if match:
                index.setdefault(match.group(1), line.strip())
    return index


# ---------------------------------------------------------------------------------------------------------- build

class Build:
    """The files under construction and what they still need (loc keys, RiE script values)."""

    def __init__(self, roots: Roots, notes: list):
        self.roots = roots
        self.notes = notes
        self.files = {}
        self.loc = {}  # key -> required
        self.values = {}  # RiE script value -> first block using it

    def want_loc(self, key: str, required: bool = True) -> None:
        self.loc[key] = self.loc.get(key, False) or required


def check_trigger_names(roots: Roots, key: str, code: str) -> None:
    """Rule (b): every `name = yes|no` is a renamed RiE trigger or known to Anbennar or the game, and no RiE-only
    scripted trigger is left (as `name = yes|no` or `name = { ... }`)."""
    renamed = set(data.TOKEN_RENAMES.values())
    scripted = external_scripted(roots)
    _keys, yes_no = external_tokens(roots)
    rie = rie_scripted_triggers(roots)
    for name in YES_NO.findall(code):
        if name in renamed or name in scripted or name in yes_no:
            continue
        if name in rie:
            raise GeneratorError(f"{key}: RiE scripted trigger {name} has no rename in TOKEN_RENAMES")
        raise GeneratorError(f"{key}: unknown trigger {name} (not in RiE's renames, Anbennar or the game)")
    for name in BLOCK_NAME.findall(code):
        if name in rie and name not in scripted and name not in renamed:
            raise GeneratorError(f"{key}: RiE scripted trigger {name} has no rename in TOKEN_RENAMES")


def check_values_and_modifiers(build: Build, key: str, text: str) -> None:
    """Rule (d): value names on cost/levy/garrison/construction lines and in modifier blocks are Anbennar's or the
    game's script values, else RiE's (copied to VALUES_FILE); modifier keys must be used in Anbennar or the game."""
    roots = build.roots
    code = bp.code(text)
    names = [value for _field, value in VALUE_REF.findall(code)]
    keys, _yes_no = external_tokens(roots)
    for block_names, start, end in bp.blocks(code, 2, strict=False):
        if not block_names[-1].endswith("modifier"):
            continue
        body = code[start:end].split("\n", 1)[1] if "\n" in code[start:end] else ""
        for modifier, value in MODIFIER_LINE.findall(body):
            if modifier == "parameter":
                continue
            if modifier not in keys:
                raise GeneratorError(f"{key}: modifier {modifier} ({block_names[-1]}) is used nowhere in Anbennar or "
                                     "the game")
            if re.match(r"[A-Za-z_]", value) and value not in ("yes", "no"):
                names.append(value)
    for name in names:
        if name in external_script_values(roots):
            continue
        if name not in rie_values(roots):
            raise GeneratorError(f"{key}: script value {name} is in neither Anbennar, the game nor RiE")
        build.values.setdefault(name, key)


def check_block(build: Build, key: str, text: str, buildings: set) -> None:
    roots = build.roots
    code = bp.code(text)
    for field, name in BUILDING_REF.findall(code):
        if name not in buildings:
            raise GeneratorError(f"{key}: {field} {name} is neither copied nor defined by Anbennar or the game")
    check_trigger_names(roots, key, code)
    for name in PARAMETER_REF.findall(code):
        if name not in known_parameters(roots):
            raise GeneratorError(f"{key}: cultural parameter {name} is not defined by Anbennar or the game")
    for name in INNOVATION_REF.findall(code):
        if name not in external_innovations(roots):
            raise GeneratorError(f"{key}: innovation {name} is not defined by Anbennar or the game")
    check_values_and_modifiers(build, key, text)


def place_icons(build: Build, key: str, text: str) -> str:
    """Copy the RiE type icons the block names (bp.place_file: never over Anbennar's or the game's own file; a
    different file of the same name goes in as aov_rie_<name>, and the block is pointed at it)."""
    roots = build.roots
    for icon in sorted(set(ICON_REF.findall(text))):
        rel = f"{ICON_DIR}/{icon}"
        if (roots.rie / rel).is_file():
            new = bp.place_file(roots, icon, rel, build.files, ICON_DIR)
            if new:
                text = re.sub(rf'(\btype_icon\s*=\s*"?){re.escape(icon)}', rf"\g<1>{new}", text)
        elif bp._exists_outside(roots, rel) is None:
            raise GeneratorError(f"{key}: type icon {icon} is in neither RiE, Anbennar nor the game")
    return text


def render_expedition_art(build: Build) -> None:
    """The event backgrounds of the dwarven expedition, RiE's pictures at RiE's paths and its Mining activity icons
    and illustrations under our names. A picture Anbennar or the game has with other bytes is an error (it would change their events)."""
    roots = build.roots
    blocks = []
    for key, (picture, environment, ambience) in data.BACKGROUNDS.items():
        if (roots.rie / picture).is_file():
            if bp.place_file(roots, picture, picture, build.files, picture.rsplit("/", 1)[0]):
                raise GeneratorError(f"{key}: picture {picture} exists in Anbennar or the game with other content")
        elif bp._exists_outside(roots, picture) is None:
            raise GeneratorError(f"{key}: picture {picture} is in neither RiE, Anbennar nor the game")
        blocks.append(f'{key} = {{\n\tbackground = {{\n\t\treference = "{picture}"\n'
                      f'\t\tenvironment = "{environment}"\n\t\tambience = "{ambience}"\n\t}}\n}}\n')
    build.files[BACKGROUNDS_FILE] = txt_file(blocks)
    for folder, art in (("icons", data.ACTIVITY_ICONS), ("illustrations", data.ACTIVITY_ILLUSTRATIONS)):
        for source, target in art.items():
            src, dest = f"gfx/interface/{folder}/{source}", f"gfx/interface/{folder}/{target}"
            if not (roots.rie / src).is_file():
                raise GeneratorError(f"activity art {src} is not in RiE")
            if bp._exists_outside(roots, dest) is not None:
                raise GeneratorError(f"activity art {dest} already exists in Anbennar or the game")
            build.files[dest] = (roots.rie / src).read_bytes()


def render_ui_icons(build: Build) -> None:
    """RiE's interface icons under our names (UI_ICONS): never over a file Anbennar or the game has."""
    for source, target in data.UI_ICONS.items():
        src, dest = f"gfx/interface/icons/{source}", f"gfx/interface/icons/{target}"
        if not (build.roots.rie / src).is_file():
            raise GeneratorError(f"interface icon {src} is not in RiE")
        if bp._exists_outside(build.roots, dest) is not None:
            raise GeneratorError(f"interface icon {dest} already exists in Anbennar or the game")
        build.files[dest] = (build.roots.rie / src).read_bytes()


LEVEL_ICON_LIST = re.compile(r"\bBUILDING_LEVEL_ICONS\s*=\s*\{([^{}]*)\}")


def render_level_icon_defines(build: Build) -> None:
    """NGameIcons.BUILDING_LEVEL_ICONS (the building window's level circles, one picture per level) as the effective
    list of Anbennar and the game plus the UI_ICONS level pictures, as RiE extends it: without it levels IX and X
    show empty circles even with the pictures in place."""
    current = None
    for _path, text in sorted(bp.effective_texts(build.roots, "common/defines")):
        for match in LEVEL_ICON_LIST.finditer(bp.code(text)):
            current = re.findall(r'"([^"]+)"', match.group(1))
    if not current:
        raise GeneratorError("no NGameIcons BUILDING_LEVEL_ICONS list in Anbennar's or the game's defines")
    extra = sorted(f"gfx/interface/icons/{target}" for target in data.UI_ICONS.values()
                   if re.fullmatch(r"building_types/building_level_\d\d\.dds", target))
    icons = current + [icon for icon in extra if icon not in current]
    build.files[LEVEL_DEFINES_FILE] = txt_file(
        ["NGameIcons = {\n\tBUILDING_LEVEL_ICONS = {\n" + "".join(f'\t\t"{icon}"\n' for icon in icons) + "\t}\n}\n"])


def render_buildings(build: Build) -> None:
    roots = build.roots
    sources = {out: rie_blocks(roots, rel) for rel, out in OUTPUTS.items()}
    keys = [key for blocks in sources.values() for key, _body in blocks]
    twice = sorted(key for key, n in Counter(keys).items() if n > 1)
    if twice:
        raise GeneratorError(f"RiE defines these buildings twice: {', '.join(twice)}")
    clash = sorted(set(keys) & external_buildings(roots))
    if clash:
        raise GeneratorError(f"RiE building keys Anbennar or the game already define: {', '.join(clash)}")
    buildings = set(keys) | external_buildings(roots) | set(HOLD_LEVELS)
    parameters = known_parameters(roots)
    removed, nexts, copied = [], set(), []
    rewritten = {out: [(key, *rw.rewrite_block(body, parameters)) for key, body in blocks]
                 for out, blocks in sources.items()}
    surface, hold = {line_of(key) for key in data.SURFACE_BUILDINGS}, {line_of(key) for key in data.HOLD_BUILDINGS}
    own_terrain = {line_of(key) for blocks in rewritten.values() for key, text, _notes in blocks
                   if line_of(key) in surface and rw.has_terrain_gate(text)}
    gated = {}  # what was added -> lines
    for out, blocks in rewritten.items():
        pieces = []
        for key, text, notes in blocks:
            removed += notes
            line = line_of(key)
            text, added = rw.gate_surface(text, line in surface - own_terrain, line in hold)
            for why in added:
                gated.setdefault(why, set()).add(line)
            check_block(build, key, text, buildings)
            text = place_icons(build, key, text)
            nexts.update(re.findall(r"\bnext_building\s*=\s*(\w+)", bp.code(text)))
            build.want_loc(f"building_{key}")
            build.want_loc(f"building_{key}_desc", False)
            build.want_loc(f"building_type_{key}_desc", False)
            for loc_key in LOC_REF.findall(bp.code(text)):
                build.want_loc(loc_key)
            copied.append(key)
            pieces.append(re.sub(r"\n{3,}", "\n\n", reindent(text)))
        build.files[out] = txt_file(pieces)
    for key in copied:
        build.want_loc(f"building_type_{key}", key not in nexts)
    build.notes.append(removal_note("removed from RiE's buildings", removed))
    build.notes.append("surface buildings gated (rie_dwarf_rewrite.gate_surface): " + "; ".join(
        f"{why}: {', '.join(sorted(lines))}" for why, lines in sorted(gated.items()))
        + f"; RiE's own terrain gates kept: {', '.join(sorted(own_terrain))}")


def line_of(key: str) -> str:
    """The building line of a level key (dwarven_tavern_03 -> dwarven_tavern)."""
    return re.sub(r"_\d\d$", "", key)


def render_ore_modifiers(build: Build) -> None:
    roots = build.roots
    rie = dict(rie_blocks(roots, data.ORE_FILE))
    pieces = []
    for ore in data.ORES:
        key = f"mining_{ore}_province_modifier"
        if key not in rie:
            raise GeneratorError(f"{data.ORE_FILE} has no {key}")
        if key in external_static_modifiers(roots):
            raise GeneratorError(f"modifier {key} is already defined by Anbennar or the game")
        pieces.append(rie[key])
        build.want_loc(key)
        build.want_loc(f"{key}_desc", False)
    build.files[ORE_MODIFIERS_FILE] = txt_file(pieces)


# ---------------------------------------------------------------------------------------------- hold level effects

def _effect_lines(text: str) -> str:
    """The levy, max_garrison and garrison_reinforcement_factor lines and the modifier blocks of a rewritten
    building block, in their order, indented one tab."""
    out, depth, taking = [], 0, False
    for line in text.split("\n"):
        code = bhm.strip_comment(line)
        before = depth
        depth += code.count("{") - code.count("}")
        if taking:
            out.append(line)
            taking = depth > 1
            continue
        if before != 1:
            continue
        match = re.match(r"\s*(\w+)\s*=\s*(\{)?", code)
        if not match:
            continue
        if match.group(2) and match.group(1).endswith("modifier"):
            out.append(line)
            taking = depth > 1
        elif not match.group(2) and match.group(1) in LEVEL_FIELDS:
            out.append(line)
    return reindent("\n".join(out) + "\n", 1)


@lru_cache(maxsize=None)
def _depths_texts(roots: Roots) -> tuple:
    """((n, rewritten block text), ...) and the rewrite notes of RiE's dwarven_depths_01..10."""
    levels, notes = {}, []
    for key, body in rie_blocks(roots, data.DEPTHS_FILE):
        match = DEPTHS_KEY.match(key)
        if match:
            text, block_notes = rw.rewrite_block(body, known_parameters(roots))
            notes += block_notes
            levels[int(match.group(1))] = text
    if sorted(levels) != list(range(1, 11)):
        raise GeneratorError(f"{data.DEPTHS_FILE}: expected dwarven_depths_01..10, found {sorted(levels)}")
    return tuple(sorted(levels.items())), tuple(notes)


@lru_cache(maxsize=None)
def _depths(roots: Roots) -> tuple:
    """((n, effects), ...) and the rewrite notes of RiE's dwarven_depths_01..10."""
    levels, notes = _depths_texts(roots)
    return tuple((n, _effect_lines(text)) for n, text in levels), notes


def depths_level_effects(roots: Roots) -> dict:
    """n -> the effect lines of RiE's dwarven_depths_<n> (levy, max_garrison, garrison_reinforcement_factor and the
    modifier blocks), rewritten, one tab deep: ready to paste into dwarven_hold_<n>."""
    return dict(_depths(roots)[0])


def render_depth_values(build: Build) -> None:
    """Rule (d) for the hold level effects: their RiE-only script values go to VALUES_FILE too."""
    levels, notes = _depths(build.roots)
    for n, effects in levels:
        key = f"dwarven_depths_{n:02d}"
        check_values_and_modifiers(build, key, f"{key} = {{\n{effects}}}\n")
    build.notes.append(removal_note("hold level effects from RiE's dwarven_depths", list(notes)))


# ------------------------------------------------------------------------------------------- dig prerequisites

SINGLE_STATEMENT = re.compile(r"[\w:.@$?]+\s*(?:\?=|>=|<=|!=|=|<|>)\s*[^\s{}=]+")


def _unwrap_single(text: str) -> str:
    """text with every OR/AND block that holds one plain statement replaced by that statement (a one-item OR or AND
    only adds a tiger warning)."""
    while True:
        masked = rw.mask(text)
        for start, name, op, cl in rw.scan(masked):
            inner = masked[op + 1:cl].strip()
            if name in ("OR", "AND") and SINGLE_STATEMENT.fullmatch(inner):
                text = text[:start] + inner + text[cl + 1:]
                break
        else:
            return text


def requirement_body(n: int, text: str, notes=None) -> str:
    """The prerequisites to dig a hold to level n: the can_construct of RiE's rewritten dwarven_depths_<n> block
    without its "previous level" line (a dig to n starts at n - 1), one tab deep; `always = yes` when it has none.
    An OR holding the previous-level line is RiE's orc alternative around the dwarf requirements (depths_04: `OR =
    { is_orc quarry depths_03 mines }`); with the orc branch gone its items are all required, so it is flattened
    (spec Section 2 table: quarry 3 and any mine 3) and noted."""
    found = [(start, end) for names, start, end in bp.blocks(text, 2, strict=False) if names[-1] == "can_construct"]
    if not found:
        return "\talways = yes\n"
    block = text[found[0][0]:found[0][1]]
    inner = block[block.index("{") + 1:block.rindex("}")]
    previous = rf"has_building_or_higher\s*=\s*dwarven_hold_{n - 1:02d}\b"
    while True:
        masked = rw.mask(inner)
        match = re.search(previous, masked)
        holder = match and rw.innermost(rw.scan(masked), match.start())
        if not holder or holder[1] != "OR":
            break
        start, _name, op, cl = holder
        inner = inner[:start] + inner[op + 1:cl] + inner[cl + 1:]
        if notes is not None:
            notes.append(f"dwarven_depths_{n:02d}: the OR around the previous level is read as all required")
    inner = re.sub(rf"(?m)^[ \t]*{previous}[ \t]*(?:#[^\n]*)?\n", "", inner)
    inner = re.sub(previous, "", inner)
    inner = _unwrap_single(rw.prune_empty(inner))
    left = re.search(r"\b(?:dwarven_hold|dwarven_depths)_\d\d\b", bp.code(inner))
    if left:
        raise GeneratorError(f"dwarven_depths_{n:02d}: can_construct names {left.group(0)} besides the previous level")
    lines = [line for line in reindent(inner, 1).split("\n") if line.strip() and not line.strip().startswith("#")]
    return "\n".join(lines) + "\n" if lines else "\talways = yes\n"


def requirements_met_trigger() -> str:
    """Province scope: the prerequisites of the dig to the hold's next level (a level-10 hold never digs)."""
    return _block("aov_hold_dig_requirements_met_trigger", *[
        line for n in range(2, 11) for line in (
            "trigger_if = {", f"\tlimit = {{ aov_hold_level = {n - 1} }}",
            f"\taov_hold_dig_requirements_{n}_trigger = yes", "}")])


def render_dig_requirements(build: Build) -> None:
    """aov_hold_dig_requirements_<n>_trigger (n = 2..10, province scope) from RiE's depths levels and the dispatcher
    on the hold's level, appended to TRIGGERS_FILE; Delve Deeper checks them when a dig starts (never while it runs).
    Their tooltip keys are copied with the other loc."""
    roots = build.roots
    levels, _notes = _depths_texts(roots)
    buildings = ({key for rel in OUTPUTS for key, _body in rie_blocks(roots, rel)} | external_buildings(roots)
                 | set(HOLD_LEVELS))
    pieces = []
    for n, text in levels:
        if n == 1:
            continue
        key = f"aov_hold_dig_requirements_{n}_trigger"
        body = requirement_body(n, text, build.notes)
        for field, name in BUILDING_REF.findall(body):
            if name not in buildings:
                raise GeneratorError(f"{key}: {field} {name} is neither copied nor defined by Anbennar or the game")
        check_trigger_names(roots, key, body)
        for loc_key in LOC_REF.findall(body):
            build.want_loc(loc_key)
        pieces += [f"# Province scope: RiE's prerequisites to dig a hold to level {n} (dwarven_depths_{n:02d}).",
                   f"{key} = {{\n{body}}}\n"]
    pieces += ["# Province scope: the prerequisites of the dig to the hold's next level.", requirements_met_trigger()]
    build.files[TRIGGERS_FILE] += ("\n" + "\n".join(pieces)).encode("utf-8")


# --------------------------------------------------------------------------------- triggers and deposit effects

def _block(name: str, *lines: str) -> str:
    return f"{name} = {{\n" + "\n".join(f"\t{line}" if line else "" for line in lines) + "\n}\n"


def _terrain_trigger(name: str, terrains) -> str:
    """OR of terrains inside a custom_tooltip (an untooltipped OR is too complex for failure-only tooltips)."""
    return _block(name, "custom_tooltip = {", f"\ttext = {name[:-len('_trigger')]}_tt", "\tOR = {",
                  *(f"\t\tterrain = {terrain}" for terrain in terrains), "\t}", "}")


def render_triggers(build: Build) -> None:
    """The scripted triggers the rewritten buildings name (province scope; see TOKEN_RENAMES)."""
    deposits = [f"\thas_province_modifier = mining_{ore}_province_modifier" for ore in data.ORES]
    pieces = [
        "# Province scope: a dwarven hold.",
        _block("aov_rie_hold_province_trigger", "has_holding_type = dwarven_hold_holding"),
        "# Province scope: mountain terrains (RiE's mountain building requirement).",
        _terrain_trigger("aov_rie_mountain_terrain_trigger", data.MOUNTAIN_TERRAINS),
        "# Province scope: mountain or hill terrains (RiE's hill building requirement).",
        _terrain_trigger("aov_rie_hill_terrain_trigger", data.HILL_TERRAINS),
        "# Province scope: the holder is a dwarf.",
        _block("aov_rie_dwarven_holder_trigger", "scope:holder = { is_dwarvish_culture = yes }"),
        "# Province scope: a dwarf holding something other than a dwarven hold.",
        _block("aov_rie_surface_dwarf_trigger", "custom_tooltip = {", "\ttext = aov_rie_surface_dwarf_tt",
               "\taov_rie_dwarven_holder_trigger = yes", "\tNOT = { has_holding_type = dwarven_hold_holding }", "}"),
        "# Province scope: false for a dwarf's holding in a hold, hills, mountains or dwarven terrain, where RiE's",
        "# dwarven buildings replace the vanilla ones (TERRAIN_GATES_FILE puts it first in every vanilla building",
        "# terrain trigger); true elsewhere and where no holder is in scope.",
        _block("aov_rie_vanilla_building_ground_trigger", "custom_tooltip = {",
               "\ttext = aov_rie_vanilla_building_ground_tt", "\tNAND = {",
               "\t\tscope:holder ?= { is_dwarvish_culture = yes }", "\t\tOR = {",
               "\t\t\thas_holding_type = dwarven_hold_holding", "\t\t\taov_rie_hill_terrain_trigger = yes", "\t\t}",
               "\t}", "}"),
        "# Province scope: the province has one of the 15 ore deposits.",
        _block("aov_rie_has_deposit_trigger", "OR = {", *deposits, "}"),
    ]
    build.files[TRIGGERS_FILE] = txt_file(pieces)


def render_terrain_gates(build: Build) -> None:
    """Single-object overrides of every building_*_requirement_terrain trigger of Anbennar and the game (the last
    definition in load order), each with GROUND_GATE first: vanilla buildings name these triggers in
    can_construct_potential, so a dwarf cannot build them in a hold, hills, mountains or dwarven terrain, where
    RiE's dwarven buildings replace them (as RiE closes vanilla buildings to dwarves). A trigger one of our
    buildings uses negated (`= no`) keeps its definition: the gate would open that building instead."""
    negated = set()
    for rel, content in build.files.items():
        if rel.startswith("common/buildings/"):
            negated |= set(NEGATED_TERRAIN_REQUIREMENT.findall(bp.code(content.decode("utf-8-sig"))))
    found = {}
    for path, text in sorted(bp.effective_texts(build.roots, "common/scripted_triggers")):
        text = bp.lf(text)
        for names, start, end in bp.blocks(text, 1, strict=False):
            if TERRAIN_REQUIREMENT.fullmatch(names[0]):
                found.pop(names[0], None)  # a later definition wins and moves to the end
                found[names[0]] = (path, text[start:end])
    pieces = []
    for key, (path, block) in found.items():
        if key in negated:
            continue
        brace = block.index("{") + 1
        pieces.append(f"# {path}\n{block[:brace]}\n\t{GROUND_GATE} {GROUND_GATE_MARK}{block[brace:]}")
    build.files[TERRAIN_GATES_FILE] = txt_file(pieces)
    build.notes.append(f"{len(pieces)} building terrain triggers closed to dwarves on dwarven ground"
                       + (f"; left open (used negated): {', '.join(sorted(negated))}" if negated else ""))


def render_deposit_effects(build: Build) -> None:
    """Ore deposit effects: the Dwarven Expedition's weighted roll (province scope, skips a province that has a
    deposit) and the game-start deposits (no scope, same guard)."""
    ores = set(data.ORES)
    if set(data.ORE_WEIGHTS) != ores:
        raise GeneratorError("ORE_WEIGHTS must have exactly the ores of ORES: "
                             + ", ".join(sorted(set(data.ORE_WEIGHTS) ^ ores)))
    unknown = sorted({ore for ore in data.START_DEPOSITS.values() if ore not in ores})
    if unknown:
        raise GeneratorError(f"START_DEPOSITS names ores that have no modifier: {', '.join(unknown)}")
    guard = ["if = {", "\tlimit = { NOT = { aov_rie_has_deposit_trigger = yes } }"]
    roll = []
    for ore in data.ORES:
        roll += [f"\t\t{data.ORE_WEIGHTS[ore]} = {{", f"\t\t\tadd_province_modifier = mining_{ore}_province_modifier",
                 f"\t\t\tscope:activity ?= {{ set_variable = {{ name = aov_expedition_ore value = flag:{ore} }} }}",
                 "\t\t}"]
    setup = []
    for barony, ore in data.START_DEPOSITS.items():
        setup += [f"title:{barony}.title_province = {{", *[f"\t{line}" for line in guard],
                  f"\t\tadd_province_modifier = mining_{ore}_province_modifier", "\t}", "}"]
    pieces = [
        "# Province scope; scope:activity is the Dwarven Expedition. Gives the province one ore deposit unless it has one.",
        _block("aov_expedition_roll_deposit_effect", *guard, "\trandom_list = {", *roll, "\t}", "}"),
        "# No scope: the ore deposits present at game start.",
        _block("aov_rie_deposit_setup_effect", *setup),
    ]
    build.files[DEPOSIT_EFFECTS_FILE] = txt_file(pieces)


# ------------------------------------------------------------------------------------------------- holding lists

def rie_holding_groups(roots: Roots, rel: str, holding: str) -> dict:
    """{group heading (lower case) -> [building keys]} of RiE's holding `holding` build list: a group starts at an
    own-line comment of several words (`#Dwarven buildings`) and runs to the next one."""
    text = bp.lf(bp.read(roots.rie / rel))
    body = dict(top_level_items(text)).get(holding)
    if body is None:
        raise GeneratorError(f"{rel} has no {holding}")
    groups, current = {}, None
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if " " in heading:
                current = heading.lower()
            continue
        name = bhm.strip_comment(line).strip()
        if current and re.fullmatch(r"\w+", name):
            groups.setdefault(current, []).append(name)
    return groups


def check_holding_lists(roots: Roots) -> None:
    """The data's HOLD_BUILDINGS, SURFACE_BUILDINGS and MINE_BUILDINGS agree with RiE's dwarven_holding and
    castle_holding build lists (mines may differ in order only)."""
    hold = rie_holding_groups(roots, RIE_HOLDINGS_FILE, "dwarven_holding")
    castle = rie_holding_groups(roots, RIE_CASTLE_FILE, "castle_holding")
    mines, dwarven = "crafting resource mines", "dwarven buildings"
    problems = []
    count = len(hold.get(mines, []))
    if (sorted(data.HOLD_BUILDINGS[:count]) != sorted(hold.get(mines, []))
            or data.HOLD_BUILDINGS[count:] != hold.get(dwarven, [])):
        problems.append("HOLD_BUILDINGS differs from RiE's dwarven_holding mines and dwarven buildings")
    if data.SURFACE_BUILDINGS != castle.get(dwarven, []):
        problems.append("SURFACE_BUILDINGS differs from RiE's castle_holding dwarven buildings")
    if sorted(data.MINE_BUILDINGS) != sorted(castle.get(mines, [])):
        problems.append("MINE_BUILDINGS differs from RiE's castle_holding mines")
    if problems:
        raise GeneratorError("; ".join(problems))


# --------------------------------------------------------------------------------------------------- script values

def _variable_refs(code: str) -> list:
    """The @variables an expression names: `@name` and the words inside `@[ ... ]`."""
    return re.findall(r"@([A-Za-z_]\w*)", code) + [
        word for expr in re.findall(r"@\[([^\]]*)\]", code) for word in re.findall(r"[A-Za-z_]\w*", expr)]


def render_values(build: Build) -> None:
    """RiE's script values the copies use, with every RiE script value and file-local @variable they need (the
    @variables first, in their RiE file order)."""
    roots = build.roots
    index = rie_values(roots)
    position = {key: i for i, key in enumerate(index)}
    external = external_script_values(roots)
    values, variables = {}, {}  # name -> text; @name -> (position, text)
    queue = list(build.values)
    while queue:
        name = queue.pop(0)
        if name in values:
            continue
        path, item = index[name]
        values[name] = item
        code = bp.code(item)
        queue += [ref for ref in re.findall(r"\b(?:value|add|subtract|multiply|divide|min|max)\s*=\s*([A-Za-z_]\w*)",
                                            code) if ref not in external and ref in index]
        pending = _variable_refs(code.split("=", 1)[1])
        while pending:
            var = "@" + pending.pop()
            if (path, var) not in index:
                raise GeneratorError(f"{name}: {var} is not defined in RiE's common/script_values/{path}")
            definition = index[(path, var)][1]
            if var in variables:
                if variables[var][1] != definition:
                    raise GeneratorError(f"{var} has two different RiE definitions")
                continue
            variables[var] = (position[(path, var)], definition)
            pending += _variable_refs(bp.code(definition).split("=", 1)[1])
    pieces = ["# RiE's file-local variables used by the values below."]
    pieces += [text.rstrip("\n") for _pos, text in sorted(variables.values())]
    pieces += ["", "# RiE script values the copied buildings use (Anbennar and the game lack them)."]
    pieces += [values[name].rstrip("\n") for name in values]
    build.files[VALUES_FILE] = txt_file(["\n".join(pieces) + "\n"])
    build.notes.append(f"RiE script values copied: {', '.join(values) or 'none'}")


# ---------------------------------------------------------------------------------------------------- localization

def render_loc(build: Build) -> None:
    """RiE's lines for the wanted keys Anbennar and the game lack, with the keys they name as $key$."""
    roots = build.roots
    rie, external = rie_loc(roots), external_loc_keys(roots)
    copied, missing, unresolved = {}, [], set()
    queue = list(build.loc.items())
    while queue:
        key, required = queue.pop(0)
        if key in external or key in copied:
            continue
        line = rie.get(key)
        if line is None:
            if required:
                missing.append(key)
            elif required is None:
                unresolved.add(key)
            continue
        copied[key] = line
        queue += [(ref, None) for ref in DOLLAR_REF.findall(line)]
    if missing:
        raise GeneratorError(f"no localization in RiE, Anbennar or the game for: {', '.join(sorted(set(missing)))}")
    stale = sorted(set(data.LOC_OVERRIDES) - set(copied))
    if stale:
        raise GeneratorError(f"LOC_OVERRIDES keys that are no longer copied: {', '.join(stale)}")
    known = external_concepts(roots)
    replaced = Counter()
    for key, line in copied.items():
        if key in data.LOC_OVERRIDES:
            line = f'{key}: "{data.LOC_OVERRIDES[key]}"'
        copied[key] = replace_concepts(key, line, known, replaced)
    lore = sorted(key for key, line in copied.items() if re.search(data.FORBIDDEN_LORE, line))
    if lore:
        raise GeneratorError(f"copied loc names Middle-earth lore; add LOC_OVERRIDES for: {', '.join(lore)}")
    lines = [BOM + "l_english:"] + [f" {line}" for line in HEADER()] + [f" {line}" for line in copied.values()]
    lines += [f' {key}: "{text}"' for key, text in OWN_LOC.items()]
    build.files[LOC_FILE] = ("\n".join(lines) + "\n").encode("utf-8")
    build.notes.append(f"{len(copied)} localization lines copied from RiE, {len(data.LOC_OVERRIDES)} of them with "
                       "our wording (LOC_OVERRIDES)")
    if unresolved:
        build.notes.append(f"$...$ references found nowhere (left as RiE has them): {', '.join(sorted(unresolved))}")
    if replaced:
        build.notes.append("RiE game concepts replaced by words (CONCEPT_REPLACEMENTS): "
                           + ", ".join(f"{name} x{n}" for name, n in sorted(replaced.items())))


SENTENCE_START = re.compile(r'(?::\d*\s*"|[.!?]\s+|\\[nN]\s*)$')


def replace_concepts(key: str, line: str, known: frozenset, replaced: Counter) -> str:
    """line with every `[concept|E]` Anbennar and the game lack replaced by its CONCEPT_REPLACEMENTS words
    (capitalised at the start of a sentence); an undefined concept missing there stops the build."""
    def sub(match):
        name = match.group(1)
        if name in known:
            return match.group(0)
        if name not in data.CONCEPT_REPLACEMENTS:
            raise GeneratorError(f"{key}: game concept {name} is defined neither by Anbennar, the game nor "
                                 "CONCEPT_REPLACEMENTS")
        replaced[name] += 1
        words = data.CONCEPT_REPLACEMENTS[name]
        if SENTENCE_START.search(line[:match.start()]) and words[:1].isalpha():
            words = words[0].upper() + words[1:]
        return words
    return CONCEPT_REF.sub(sub, line)


# ------------------------------------------------------------------------------------------------------------ main

def build_all(roots: Roots, notes=None) -> dict:
    """{relative path: bytes} of every generated file."""
    roots.check()
    check_holding_lists(roots)
    notes = [] if notes is None else notes
    bp.RENAMED.clear()
    build = Build(roots, notes)
    render_buildings(build)
    render_terrain_gates(build)
    render_expedition_art(build)
    render_ui_icons(build)
    render_level_icon_defines(build)
    render_ore_modifiers(build)
    render_triggers(build)
    render_dig_requirements(build)
    render_deposit_effects(build)
    render_depth_values(build)
    render_values(build)
    render_loc(build)
    if bp.RENAMED:
        notes.append("icons copied under aov_rie_ names (Anbennar or the game has its own): "
                     + ", ".join(target for _rel, target in bp.RENAMED))
    icons = sorted(rel for rel in build.files if rel.startswith(ICON_DIR))
    notes.append(f"{len(icons)} building type icons copied: {', '.join(rel.rsplit('/', 1)[1] for rel in icons)}")
    return build.files


def main() -> int:
    default = Roots.default()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rie", type=Path, default=default.rie)
    parser.add_argument("--anbennar", type=Path, default=default.anbennar)
    parser.add_argument("--game", type=Path, default=default.game, help="CK3 install folder")
    args = parser.parse_args()
    notes = []
    try:
        files = build_all(Roots(rie=args.rie, anbennar=args.anbennar, game=args.game), notes)
    except (GeneratorError, OSError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for note in notes:
        print(f"note: {note}")
    for rel, content in files.items():
        target = SUBMOD / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    print(f"wrote {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
