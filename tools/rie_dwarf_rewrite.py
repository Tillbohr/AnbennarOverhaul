"""Rewrites Realms in Exile dwarf building blocks for Anbennar (spec section 1 table; data in tools/data/rie_dwarves.py).

rewrite_block(body, known_parameters) -> (text, notes); prune_empty(text) -> text. Output uses LF line endings.

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
