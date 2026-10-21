"""Small readers for Paradox script: comments, top-level blocks, Anbennar's baronies and special building slots.

Used by the tool tests to check generated files and data against Anbennar's current titles.
"""

import re
from pathlib import Path

ANBENNAR_CK3 = Path(__file__).resolve().parent.parent.parent / "anbennar-ck3-dev-master"


def strip_comments(text):
    """Remove `#` comments, leaving quoted strings intact."""
    out = []
    for line in text.split("\n"):
        in_quote = False
        for i, ch in enumerate(line):
            if ch == '"':
                in_quote = not in_quote
            elif ch == "#" and not in_quote:
                line = line[:i]
                break
        out.append(line)
    return "\n".join(out)


def _balanced(text, open_at):
    """Index just past the brace matching text[open_at] == '{'."""
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


_KEY_BLOCK = re.compile(r"([A-Za-z0-9_.:\-]+)\s*=\s*\{")


def parse_blocks(text):
    """Top-level `key = { ... }` -> body text (without the outer braces)."""
    text = strip_comments(text)
    blocks = {}
    pos = 0
    while True:
        m = _KEY_BLOCK.search(text, pos)
        if not m:
            return blocks
        end = _balanced(text, m.end() - 1)
        blocks[m.group(1)] = text[m.end():end - 1].strip()
        pos = end


def _read(path):
    return path.read_bytes().decode("utf-8-sig", errors="replace")


_TITLE_START = re.compile(r"^\s*([ekdcb]_[A-Za-z0-9_]+)\s*=\s*\{")
_PROVINCE = re.compile(r"\bprovince\s*=\s*(\d+)")


def ck3_titles(anbennar_ck3=ANBENNAR_CK3):
    """-> (barony -> province, county -> baronies in file order)."""
    provinces, county_baronies = {}, {}
    for path in sorted((Path(anbennar_ck3) / "common" / "landed_titles").glob("*.txt")):
        stack, depth = [], 0
        for line in _read(path).split("\n"):
            code = line.split("#", 1)[0]
            m = _TITLE_START.match(code)
            if m:
                stack.append((m.group(1), depth))
                key = m.group(1)
                if key.startswith("b_"):
                    county = next((k for k, _ in reversed(stack) if k.startswith("c_")), None)
                    if county:
                        baronies = county_baronies.setdefault(county, [])
                        if key not in baronies:
                            baronies.append(key)
                elif key.startswith("c_"):
                    county_baronies.setdefault(key, [])
            if stack and stack[-1][0].startswith("b_"):
                p = _PROVINCE.search(code)
                if p:
                    provinces.setdefault(stack[-1][0], int(p.group(1)))
            depth += code.count("{") - code.count("}")
            while stack and depth <= stack[-1][1]:
                stack.pop()
    return provinces, county_baronies


_PROVINCE_START = re.compile(r"^(\d+)\s*=\s*\{")
_SPECIAL = re.compile(r"\bspecial_building(?:_slot)?\s*=\s*([A-Za-z0-9_]+)")


def anbennar_slots(anbennar_ck3=ANBENNAR_CK3):
    """province id -> special building key (or slot) in Anbennar's province history, dated blocks included."""
    slots = {}
    for path in sorted((Path(anbennar_ck3) / "history" / "provinces").glob("*.txt")):
        province, depth = None, 0
        for line in _read(path).split("\n"):
            code = line.split("#", 1)[0]
            if depth == 0:
                m = _PROVINCE_START.match(code)
                if m:
                    province = int(m.group(1))
            elif province is not None:
                s = _SPECIAL.search(code)
                if s:
                    slots[province] = s.group(1)
            depth += code.count("{") - code.count("}")
            if depth <= 0:
                depth, province = 0, None
    return slots
