"""Rewrites Realms in Exile dwarf building blocks for Anbennar (spec section 1 table; data in tools/data/rie_dwarves.py).

rewrite_block(body, known_parameters) -> (text, notes); prune_empty(text) -> text; gate_surface(text, surface_line,
hold_line) -> (text, notes) and has_terrain_gate(text) for the surface-building gates. Output uses LF line endings.

Own brace scanner instead of build_portraits.blocks: removals need exact spans (a header such as
`county.holder.dynasty ?= {` and one-line blocks), which blocks() reports only as whole lines."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data import rie_dwarves as data  # noqa: E402

MASK = re.compile(r'"[^"\n]*"|#[^\n]*')
BRACE = re.compile(r'"[^"\n]*"|\{|\}')
HEADER = re.compile(r'(?:([^\s{}="]+)[ \t]*(?:\?=|>=|<=|!=|=|<|>)[ \t]*)?$')
PARAMETER = re.compile(r'(?<![\w.])parameter[ \t]*=[ \t]*(\w+)')
TEXT_ONLY = re.compile(r'text\s*=\s*[^\s{}]+')
KEPT = "\0"  # stands in for a kept `parameter` while the loop runs


def mask(text):
    """text with comments blanked (same length), so offsets match the original."""
    return MASK.sub(lambda m: m.group(0) if m.group(0)[0] == '"' else " " * len(m.group(0)), text)


def scan(masked):
    """[(header_start, name, open, close)] of every block, sorted by header start; blocks left open close at the end."""
    out, stack = [], []
    for m in BRACE.finditer(masked):
        token = m.group(0)
        if token == "{":
            head = HEADER.search(masked[max(0, m.start() - 200):m.start()])
            start = m.start() - len(head.group(0))
            stack.append((start, head.group(1) or "", m.start()))
        elif token == "}" and stack:
            start, name, op = stack.pop()
            out.append((start, name, op, m.start()))
    for start, name, op in reversed(stack):
        out.append((start, name, op, len(masked)))
    return sorted(out)


def cut(text, a, b):
    """text without [a, b); the whole lines when nothing else is on them."""
    ls = text.rfind("\n", 0, a) + 1
    le = text.find("\n", b)
    le = len(text) if le < 0 else le + 1
    if not text[ls:a].strip() and not text[b:le].strip():
        a, b = ls, le
    return text[:a] + text[b:]


def is_empty(masked, block):
    _, name, op, cl = block
    inner = masked[op + 1:cl].strip()
    return not inner or (name == "custom_tooltip" and TEXT_ONLY.fullmatch(inner) is not None)


def prune_empty(text):
    """text without blocks that hold nothing (an empty OR is false in CK3), repeated until stable. A custom_tooltip
    holding only its text counts as empty: its condition was removed."""
    text = text.replace("\r\n", "\n")
    while True:
        masked = mask(text)
        empty = [b for b in scan(masked) if is_empty(masked, b)]
        if not empty:
            return text
        for start, _, _, cl in reversed(empty):  # empty blocks never nest
            text = cut(text, start, min(cl + 1, len(text)))


def innermost(blocks, pos):
    best = None
    for b in blocks:
        if b[2] < pos < b[3] and (best is None or b[2] > best[2]):
            best = b
    return best


def rewrite_block(body, known_parameters):
    """(rewritten block text, notes of what was removed)."""
    text = body.replace("\r\n", "\n")
    notes = []

    while True:  # dropped blocks (province_dynasty_modifier)
        masked = mask(text)
        found = [b for b in scan(masked) if b[1] in data.DROP_BLOCKS]
        if not found:
            break
        start, name, op, cl = found[-1]
        perk = re.search(r'\blotr_\w+', masked[op:cl])
        notes.append(f"removed {name} ({perk.group(0) if perk else 'no perk'})")
        text = cut(text, start, min(cl + 1, len(text)))

    while True:  # parameter-gated blocks
        masked = mask(text)
        blocks = scan(masked)
        matches = list(PARAMETER.finditer(masked))
        if not matches:
            break
        m = matches[-1]
        param = m.group(1)
        block = innermost(blocks, m.start())
        if param in data.UNGATED_PARAMETERS:
            text = cut(text, m.start(), m.end())
            if block and block[1] == "county_culture_modifier":
                text = text[:block[0]] + text[block[0]:].replace("county_culture_modifier", "county_modifier", 1)
            notes.append(f"ungated parameter {param}")
        elif param in known_parameters or block is None:
            text = text[:m.start()] + KEPT + text[m.start() + len("parameter"):]
        else:
            notes.append(f"removed {block[1]} block gated on parameter {param}")
            text = cut(text, block[0], min(block[3] + 1, len(text)))
    text = text.replace(KEPT, "parameter")

    for pattern, replacement in data.BLOCK_REPLACEMENTS:  # whole statements or blocks replaced
        while True:
            m = re.search(r'(?<![\w.])' + pattern + r'(?!\w)', mask(text))
            if not m:
                break
            notes.append(f"replaced {' '.join(m.group(0).split())} with {replacement}")
            text = text[:m.start()] + replacement + text[m.end():]

    for pattern in data.DROP_STATEMENTS:  # statement drops
        while True:
            m = re.search(r'(?<![\w.])' + pattern + r'(?!\w)', mask(text))
            if not m:
                break
            notes.append("removed " + re.sub(r"\s+", " ", m.group(0)))
            text = cut(text, m.start(), m.end())

    for m in reversed(list(re.finditer(r'(?<![\w.])effect_desc[ \t]*=[ \t]*(\w+)', mask(text)))):
        if re.search(data.DROP_EFFECT_DESC, m.group(1)):
            notes.append(f"removed effect_desc {m.group(1)}")
            text = cut(text, m.start(), m.end())

    renames = data.TOKEN_RENAMES
    word = re.compile(r'"[^"\n]*"|#[^\n]*|(?<![\w])(' + "|".join(map(re.escape, renames)) + r')(?![\w])')
    text = word.sub(lambda m: renames[m.group(1)] if m.group(1) else m.group(0), text)
    pattern, repl = data.DEPTHS_RENAME
    text = re.sub(r'"[^"\n]*"|#[^\n]*|' + pattern,
                  lambda m: m.expand(repl) if m.lastindex else m.group(0), text)

    return prune_empty(text), notes


# ------------------------------------------------------------------------------------------- surface-building gates

SURFACE_USE = re.compile(r'(?<![\w.])aov_rie_surface_dwarf_trigger\s*=\s*yes\b')
HOLD_EXCLUDED = re.compile(r'(?<![\w.])aov_rie_hold_province_trigger\s*=\s*no\b')
HOLDER_CHECK = re.compile(r'(?<![\w.])scope:holder\s*=\s*\{\s*is_dwarvish_culture\s*=\s*yes\s*\}')
TERRAIN_GATED = re.compile(r'(?<![\w.])aov_rie_(?:mountain|hill)_terrain_trigger\s*=\s*yes\b')
SURFACE_USERS = ("is_enabled", "can_construct", "can_construct_showing_failures_only")


def has_terrain_gate(text):
    """text names a terrain trigger (our mountain or hill trigger, a *_requirement_terrain trigger or `terrain =`)
    outside comments."""
    return re.search(data.TERRAIN_GATE, mask(text)) is not None


def _top_blocks(masked):
    """{name: (start, open, close)} of the first block of each name directly inside the building block."""
    blocks = scan(masked)
    if not blocks:
        return None, {}
    outer = blocks[0]
    found = {}
    for b in blocks[1:]:
        if innermost(blocks, b[2]) == outer:
            found.setdefault(b[1], b[:1] + b[2:])
    return outer, found


def gate_surface(text, surface_line, hold_line):
    """(text, notes) with the surface-building gates added to can_construct_potential (data, SURFACE_*): a block
    needing a surface dwarf excludes holds and checks a dwarven holder; a block of a surface line without a terrain gate
    of its own (surface_line true) gets the hill gate, or the hill-or-hold gate in a line RiE also offers in holds
    (hold_line) when the block does not exclude holds. Notes name what was added: "not in holds", "dwarven holder",
    "hill terrain"."""
    masked = mask(text)
    outer, inner = _top_blocks(masked)
    if outer is None:
        return text, []
    uses = any(SURFACE_USE.search(masked[op:cl]) for name, (_s, op, cl) in inner.items() if name in SURFACE_USERS)
    potential = inner.get("can_construct_potential")
    code = masked[potential[1] + 1:potential[2]] if potential else ""
    added = []
    excluded = HOLD_EXCLUDED.search(code) is not None
    if uses and not excluded:
        added.append((data.SURFACE_HOLD_EXCLUSION, "not in holds"))
        excluded = True
    if uses and not HOLDER_CHECK.search(code):
        added.append((data.SURFACE_HOLDER_CHECK, "dwarven holder"))
    if surface_line and not TERRAIN_GATED.search(code):
        gate = data.SURFACE_TERRAIN_GATE_OR_HOLD if hold_line and not excluded else data.SURFACE_TERRAIN_GATE
        added.append((gate, "hill terrain"))
    if not added:
        return text, []
    lines = "".join(f"\t\t{statement} {data.SURFACE_GATE_MARK}: {why}\n" for statement, why in added)
    notes = [why for _statement, why in added]
    if potential is None:  # a new potential right after the building's opening line
        at = text.find("\n", outer[2]) + 1
        return text[:at] + "\tcan_construct_potential = {\n" + lines + "\t}\n" + text[at:], notes
    close = potential[2]
    line_start = text.rfind("\n", 0, close) + 1
    if text[line_start:close].strip():  # the closing brace shares its line: break it onto its own line
        return text[:close] + "\n" + lines + text[close:], notes
    return text[:line_start] + lines + text[line_start:], notes
