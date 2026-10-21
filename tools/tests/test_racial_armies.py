"""Tests for the racial armies system: heritages, lineage triggers, removed traditions, MAA and refresh hooks.

    python -I -m unittest discover -s tools/tests -p "test_racial_armies*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdx_script import ANBENNAR_CK3 as ANBENNAR, _balanced, parse_blocks, strip_comments  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent.parent


def _text(path):
    return path.read_bytes().decode("utf-8-sig") if path.is_file() else ""


def blocks(rel):
    """Top-level blocks of a submod file (empty when the file is missing)."""
    return parse_blocks(_text(SUBMOD / rel))


def base_blocks(rel):
    """Top-level blocks of an Anbennar file."""
    return parse_blocks(_text(ANBENNAR / rel))


def depth0(body):
    """A block body with every nested `{ ... }` removed."""
    out, pos = [], 0
    while True:
        i = body.find("{", pos)
        if i < 0:
            return "".join(out) + body[pos:]
        out.append(body[pos:i])
        pos = _balanced(body, i)


def field(body, key):
    """First `key = value` at depth 0 of a block body, or None."""
    m = re.search(rf"(?<![\w.:]){re.escape(key)}\s*=\s*([^\s{{}}]+)", depth0(strip_comments(body)))
    return m.group(1) if m else None


def squash(body):
    """Whitespace-insensitive form of a block body, for comparing script."""
    return " ".join(strip_comments(body).split())


HERITAGE_FILE = "common/culture/pillars/zz_aov_racial_heritages.txt"
BASE_HERITAGE_FILE = "common/culture/pillars/anb_heritage.txt"
TRIGGER_FILE = "common/scripted_triggers/aov_racial_maa_triggers.txt"
CLANS = ("ruby", "silver", "stone", "agate", "copper", "citrine", "gold", "pyrite", "titanium", "topaz", "marble")

HERITAGES = {  # levy_size, levy_attack/levy_toughness, domain_limit, parameter
    "heritage_elven": ("-0.75", "30", "-1", "aov_racial_levy_elven"),
    "heritage_dwarven": ("-0.40", "7", "-2", "aov_racial_levy_dwarven"),
    "heritage_gnomish": ("-0.50", "10", "-1", "aov_racial_levy_gnomish"),
    "heritage_kobold": ("0.50", "-3", None, "aov_racial_levy_kobold"),
}


class HeritageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ours = blocks(HERITAGE_FILE)
        cls.base = base_blocks(BASE_HERITAGE_FILE)

    def test_heritages_carry_spec_values(self):
        self.assertEqual(set(self.ours), set(HERITAGES))
        for key, (levy, quality, domain, param) in HERITAGES.items():
            inner = parse_blocks(self.ours[key])
            mod = inner.get("character_modifier", "")
            self.assertEqual(field(mod, "levy_size"), levy, key)
            self.assertEqual(field(mod, "levy_attack"), quality, key)
            self.assertEqual(field(mod, "levy_toughness"), quality, key)
            self.assertEqual(field(mod, "domain_limit"), domain, key)
            self.assertEqual(field(inner.get("parameters", ""), param), "yes", key)

    def test_overrides_keep_anbennar_fields(self):
        for key in HERITAGES:
            ours, base = self.ours.get(key, ""), self.base[key]
            self.assertEqual(field(ours, "type"), field(base, "type"), key)
            self.assertEqual(field(ours, "audio_parameter"), field(base, "audio_parameter"), key)
            self.assertEqual(squash(parse_blocks(ours).get("is_shown", "")), squash(parse_blocks(base)["is_shown"]), key)


class LineageTriggerTests(unittest.TestCase):
    NAMES = (["aov_sun_elven_lineage_trigger", "aov_wood_elven_lineage_trigger", "aov_moon_elven_lineage_trigger"]
             + [f"aov_{clan}_dwarven_lineage_trigger" for clan in CLANS])
    ROOTS = dict({"aov_sun_elven_lineage_trigger": "sun_elvish", "aov_wood_elven_lineage_trigger": "wood_elvish"},
                 **{f"aov_{clan}_dwarven_lineage_trigger": f"{clan}_dwarvish" for clan in CLANS})

    @classmethod
    def setUpClass(cls):
        cls.ours = blocks(TRIGGER_FILE)

    def test_every_lineage_trigger_exists(self):
        self.assertEqual(set(self.ours), set(self.NAMES))

    def test_lineage_triggers_check_self_and_ancestors(self):
        for name, root in self.ROOTS.items():
            body = squash(self.ours.get(name, ""))
            self.assertIn(f"this = culture:{root}", body, name)
            self.assertIn(f"any_parent_culture_or_above = {{ this = culture:{root} }}", body, name)

    def test_moon_trigger_excludes_wood_and_sun_lineage(self):
        body = squash(self.ours.get("aov_moon_elven_lineage_trigger", ""))
        for part in ("has_cultural_pillar = heritage_elven", "aov_sun_elven_lineage_trigger = no",
                     "aov_wood_elven_lineage_trigger = no"):
            self.assertIn(part, body)


if __name__ == "__main__":
    unittest.main()
