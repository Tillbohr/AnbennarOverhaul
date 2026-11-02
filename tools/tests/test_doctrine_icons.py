"""Tests for the doctrine and tenet icons of tools/data/doctrine_icons.py.

    python -I -m unittest discover -s tools/tests -p "test_doctrine_icons*.py"
"""

import re
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # python -I does not add the tools folder
from data.doctrine_icons import DOCTRINE_ICONS  # noqa: E402
from pdx_script import parse_blocks  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent.parent
ANBENNAR = SUBMOD.parent / "anbennar-ck3-dev-master"
GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
ROOTS = (GAME, ANBENNAR, SUBMOD)  # load order: a later file of the same name replaces an earlier one
ICON_DIR = "gfx/interface/icons/faith_doctrines"
# Categories whose doctrines the faith window draws with their own icon (important doctrines and tenets); the
# others show the group's icon or text only.
ICON_CATEGORIES = ("main_group", "core_tenets")
HAVE_REAL = ANBENNAR.is_dir() and GAME.is_dir()


def database(folder: str) -> dict:
    files = {}
    for root in ROOTS:
        for f in sorted((root / folder).glob("*.txt")):
            files[f.name] = f
    out = {}
    for f in files.values():
        out.update(parse_blocks(f.read_text(encoding="utf-8-sig")))
    return out


def icon_of(key: str, body: str) -> str:
    m = re.search(r'^\s*icon\s*=\s*"?(\w+)"?', body, re.M)
    return m.group(1) if m else key


def dds_size(path: Path) -> tuple:
    height, width = struct.unpack("<II", path.read_bytes()[12:20])
    return width, height


@unittest.skipUnless(HAVE_REAL, "needs Anbennar CK3 and the game")
class DoctrineIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doctrines = database("common/religion/doctrine_types")
        cls.shown = {}
        for group, body in database("common/religion/doctrine_group_types").items():
            m = re.search(r'^\s*category\s*=\s*"?(\w+)"?', body, re.M)
            listed = re.search(r"doctrine_types\s*=\s*\{([^}]*)\}", body)
            if m and m.group(1) in ICON_CATEGORIES and listed:
                for key in listed.group(1).split():
                    cls.shown[key] = group

    def test_every_shown_doctrine_has_an_icon(self):
        self.assertGreater(len(self.shown), 50)
        for key, group in self.shown.items():
            if key not in self.doctrines:
                continue  # listed in a group but defined nowhere: the engine skips it
            icon = icon_of(key, self.doctrines[key])
            self.assertTrue(any((r / ICON_DIR / f"{icon}.dds").is_file() for r in ROOTS), f"{group} {key}: {icon}")

    def test_every_icon_is_used_by_a_doctrine(self):
        used = {icon_of(k, b) for k, b in self.doctrines.items()}
        for name in DOCTRINE_ICONS:
            self.assertIn(name, used)

    def test_anbennar_does_not_ship_the_same_file(self):
        """Anbennar's own picture would be replaced by ours; drop ours (and its entry) when this fails."""
        for name in DOCTRINE_ICONS:
            self.assertFalse((ANBENNAR / ICON_DIR / f"{name}.dds").is_file(), name)


class DoctrineIconFileTests(unittest.TestCase):
    def test_files_exist_with_vanilla_sizes(self):
        for name in DOCTRINE_ICONS:
            path = SUBMOD / ICON_DIR / f"{name}.dds"
            self.assertTrue(path.is_file(), name)
            self.assertEqual(path.read_bytes()[:4], b"DDS ", name)
            expected = (260, 400) if name.startswith("anb_tenet_") else (120, 120)
            self.assertEqual(dds_size(path), expected, name)

    def test_no_stray_files(self):
        on_disk = {p.stem for p in (SUBMOD / ICON_DIR).glob("*.dds")}
        self.assertEqual(on_disk, set(DOCTRINE_ICONS))


if __name__ == "__main__":
    unittest.main()
