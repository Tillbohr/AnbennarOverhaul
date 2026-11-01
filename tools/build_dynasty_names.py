"""Generate Anbennar dynasty names for the culture name lists that Anbennar ships with vanilla placeholders.

The game names a new dynasty from its culture's name list whenever a lowborn character gains land, which happens at
game start for every ruler Anbennar's history leaves without a dynasty. Most Anbennar name lists still hold vanilla's
English dynasty names (gnomes and halflings vanilla's Frisian ones), so those rulers start as de Bohun or Abdena. This
script writes a copy of each such name list whose dynasty_names and cadet_dynasty_names are replaced by the EU4
Anbennar names in tools/data/dynasty_names.py, and the loc for names no loaded file already has:

    common/culture/name_lists/zz_aov_dynasty_names.txt     single-object overrides of the placeholder name lists
    localization/english/aov_dynasty_names_l_english.yml   dynn_ keys for the new names

    python -I tools/build_dynasty_names.py [--anbennar PATH]

Names already borne by an Anbennar game-start dynasty or house are left out, so no second house of that name appears.
Rerun after an Anbennar update (see docs/systems/dynasty-names.md). It stops if a listed name list is gone or no longer
holds placeholders, or a name lists an EU4 source with no names.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the tools folder

from build_hud_override import GeneratorError  # noqa: E402
from pdx_script import ANBENNAR_CK3, parse_blocks, strip_comments  # noqa: E402
from data.dynasty_names import EU4_DYNASTY_NAMES, NAME_LISTS  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent
GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
NAME_LIST_DIR = "common/culture/name_lists"
LISTS_FILE = f"{NAME_LIST_DIR}/zz_aov_dynasty_names.txt"
LOC_FILE = "localization/english/aov_dynasty_names_l_english.yml"
MARKER = "# Anbennar Overhaul"
BOM = b"\xef\xbb\xbf"
PLACEHOLDERS = ("dynn_Bohun", "dynn_Abdena")  # first entries of vanilla's English and Frisian lists
TODO_LINE = re.compile(r"^\s*#\s*TODO - replace placeholder dynasty names\s*$")
NAME_BLOCKS = ("cadet_dynasty_names", "dynasty_names")

# EU4 name prefix -> Anbennar's dynnp_ key (longest first, so "síl na " is not read as "síl ").
PREFIXES = (
    ("síl na ", "dynnp_sil_na"),
    ("sílna ", "dynnp_silna"),
    ("síl ", "dynnp_sil"),
    ("sína ", "dynnp_sina"),
    ("sina ", "dynnp_sina"),
    ("of ", "dynnp_of"),
    ("az-", "dynnp_az"),
)

_LOC_LINE = re.compile(r'^\s*([A-Za-z0-9_.\-]+):\d*\s*"(.*)"\s*(?:#.*)?$')


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig")


def split_prefix(name: str) -> tuple:
    """'síl Vivin' -> ('dynnp_sil', 'Vivin'); 'Gerwick' -> (None, 'Gerwick')."""
    for text, key in PREFIXES:
        if name.startswith(text) and len(name) > len(text):
            return key, name[len(text):]
    return None, name


def slug(text: str) -> str:
    """ASCII key part for a name: 'Dhánaenn' -> 'Dhanaenn', 'Ór Esta' -> 'Or_Esta'."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    out = re.sub(r"[^A-Za-z0-9]+", "_", ascii_text).strip("_")
    if not out:
        raise GeneratorError(f"name {text!r} has no ASCII letters to build a loc key from")
    return out


def dynasty_loc(roots: list) -> dict:
    """dynn_ key -> text over the English loc of roots, the first root winning."""
    loc = {}
    for root in roots:
        folder = root / "localization" / "english"
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*_l_english.yml")):
            for line in path.read_bytes().decode("utf-8-sig", errors="replace").split("\n"):
                m = _LOC_LINE.match(line.rstrip("\r"))
                if m and m.group(1).startswith("dynn_"):
                    loc.setdefault(m.group(1), m.group(2))
    return loc


def start_dynasty_names(anbennar: Path, loc: dict) -> set:
    """Shown names of Anbennar's game-start dynasties and houses."""
    names = set()
    for folder in ("common/dynasties", "common/dynasty_houses"):
        for path in sorted((anbennar / folder).glob("*.txt")):
            for body in parse_blocks(_read(path)).values():
                m = re.search(r'^\s*name\s*=\s*"?([A-Za-z0-9_.\-]+)', body, re.M)
                if m and m.group(1) in loc:
                    names.add(loc[m.group(1)])
    return names


def list_names(name_list: str, taken: set) -> list:
    """Shown names for a name list: its sources' names in order, each once, without game-start dynasty names."""
    out = []
    for source in NAME_LISTS[name_list]:
        names = EU4_DYNASTY_NAMES.get(source)
        if not names:
            raise GeneratorError(f"{name_list}: EU4 source {source} has no names in tools/data/dynasty_names.py")
        for name in names:
            if name not in out and split_prefix(name)[1] not in taken:
                out.append(name)
    return out


class LocKeys:
    """Picks a dynn_ key for each name: the existing key that shows it, else a new one no loaded key uses."""

    def __init__(self, loc: dict):
        self.loc = loc
        self.by_text = {}
        for key, text in loc.items():
            self.by_text.setdefault(text, key)
        self.new = {}  # key -> text, in first-use order

    def key(self, text: str) -> str:
        if text in self.by_text:
            return self.by_text[text]
        base = slug(text)
        for n in range(1, 100):
            key = f"dynn_{base}" if n == 1 else f"dynn_aov_{base}" if n == 2 else f"dynn_aov_{base}_{n}"
            if key not in self.loc and key not in self.new:
                self.new[key] = text
                self.by_text[text] = key
                return key
        raise GeneratorError(f"no free loc key for {text!r}")


def entry(name: str, keys: LocKeys) -> str:
    prefix, base = split_prefix(name)
    key = keys.key(base)
    return f'{{ "{prefix}" "{key}" }}' if prefix else f'"{key}"'


def name_list_blocks(anbennar: Path) -> dict:
    """name list key -> (file name, its whole block as written, comments kept)."""
    found = {}
    for path in sorted((anbennar / NAME_LIST_DIR).glob("*.txt")):
        lines = _read(path).replace("\r\n", "\n").split("\n")
        i = 0
        while i < len(lines):
            m = re.match(r"^(\w+)\s*=\s*\{", strip_comments(lines[i]))
            if not m:
                i += 1
                continue
            depth, j = 0, i
            while j < len(lines):
                code = strip_comments(lines[j])
                depth += code.count("{") - code.count("}")
                if depth == 0:
                    break
                j += 1
            found[m.group(1)] = (path.name, "\n".join(lines[i:j + 1]))
            i = j + 1
    return found


def replace_names(block: str, entries: list) -> str:
    """block with the entries of each top-level cadet_dynasty_names and dynasty_names swapped for `entries`, and
    Anbennar's placeholder TODO line dropped."""
    lines = [l for l in block.split("\n") if not TODO_LINE.match(l)]
    out, depth, i, replaced = [], 0, 0, []
    while i < len(lines):
        line = lines[i]
        code = strip_comments(line)
        m = re.match(r"^(\s*)(\w+)\s*=\s*\{\s*$", code)
        if depth == 1 and m and m.group(2) in NAME_BLOCKS:
            indent = m.group(1)
            j, inner = i, 0
            while True:
                inner += strip_comments(lines[j]).count("{") - strip_comments(lines[j]).count("}")
                if inner == 0:
                    break
                j += 1
            out.append(line)
            out += [f"{indent}\t{e}" for e in entries]
            out.append(f"{indent}}}")
            replaced.append(m.group(2))
            i = j + 1
            continue
        out.append(line)
        depth += code.count("{") - code.count("}")
        i += 1
    if "dynasty_names" not in replaced:
        raise GeneratorError("name list has no dynasty_names block")
    return "\n".join(out)


def build_all(anbennar: Path = ANBENNAR_CK3, game: Path = GAME) -> dict:
    """-> {path relative to the submod: file bytes}."""
    loc = dynasty_loc([anbennar, game])
    taken = start_dynasty_names(anbennar, loc)
    blocks = name_list_blocks(anbennar)
    keys = LocKeys(loc)
    out = [f"{MARKER}: generated by tools/build_dynasty_names.py; do not edit by hand. See docs/systems/dynasty-names.md.",
           f"{MARKER}: each name list is Anbennar's, with its placeholder dynasty names replaced by EU4 Anbennar's.", ""]
    for name_list in NAME_LISTS:
        if name_list not in blocks:
            raise GeneratorError(f"{name_list} no longer exists in Anbennar; drop it from tools/data/dynasty_names.py")
        source_file, block = blocks[name_list]
        if not any(p in block for p in PLACEHOLDERS):
            raise GeneratorError(f"{name_list} ({source_file}) no longer holds placeholder dynasty names; "
                                 f"drop it from tools/data/dynasty_names.py")
        entries = [entry(name, keys) for name in list_names(name_list, taken)]
        out += [f"# from {NAME_LIST_DIR}/{source_file}", replace_names(block, entries), ""]
    loc_lines = ["l_english:", f" {MARKER}: generated by tools/build_dynasty_names.py; do not edit by hand."]
    loc_lines += [f' {key}: "{text}"' for key, text in keys.new.items()]
    return {
        LISTS_FILE: BOM + "\n".join(out).encode("utf-8"),
        LOC_FILE: BOM + ("\n".join(loc_lines) + "\n").encode("utf-8"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anbennar", type=Path, default=ANBENNAR_CK3)
    args = parser.parse_args()
    try:
        files = build_all(args.anbennar)
    except (GeneratorError, OSError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for rel, content in files.items():
        target = SUBMOD / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        print(f"wrote {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
