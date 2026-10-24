"""Tests for Anbennar's cultural men-at-arms in the overhaul: Storm Sorcerers disabled, Battlemages recruited from a
Battlemage Academy, and the flavor text that replaces Anbennar's "LOC TO-DO".

    python -I -m unittest discover -s tools/tests -p "test_cultural_maa*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdx_script import ANBENNAR_CK3 as ANBENNAR, _balanced, parse_blocks, strip_comments  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent.parent

MAA_FILE = "common/men_at_arms_types/zz_aov_mage_maa_overrides.txt"
BASE_MAA_FILE = "common/men_at_arms_types/anb_cultural_maa_types.txt"
TRADITION_FILE = "common/culture/traditions/zz_aov_mage_traditions.txt"
BASE_TRADITION_FILE = "common/culture/traditions/anb_maa_traditions.txt"
INNOVATION_FILE = "common/culture/innovations/zz_aov_mage_innovations.txt"
BASE_INNOVATION_FILE = "common/culture/innovations/anb_cultural_innovations.txt"
ON_ACTION_FILE = "common/on_action/aov_mage_maa_on_actions.txt"
HALFLING_MAA_FILE = "common/men_at_arms_types/zz_aov_halfling_maa_overrides.txt"
BASE_TYPES_FILE = "common/men_at_arms_types/anb_cultural_maa_types.txt"
GNOME_MAA_FILE = "common/men_at_arms_types/zz_aov_gnome_maa_overrides.txt"
BASE_GENERICS_FILE = "common/men_at_arms_types/anb_cultural_maa_generics.txt"
JOKE_FLAVOR_FILE = "localization/replace/english/aov_maa_joke_flavor_replace_l_english.yml"
FLAVOR_FILE = "localization/replace/english/aov_maa_flavor_replace_l_english.yml"
BASE_LOC_FILE = "localization/english/culture/anb_cultural_maa_innovations_l_english.yml"

ACADEMY_GATE = "aov_battlemage_academy_tier_at_least = { TIER = 2 }"
GATES = {"battlemages": ACADEMY_GATE, "storm_sorcerers": "always = no"}
# Cultural mage units not gated by the academy (Skalds and Druids are recruited by faith: test_faith_maa.py).
KEPT_MAGES = {"skalds", "druids", "wren_hedge_witches", "bladedancers"}
RETIRED = ("tradition_test_maa_anb_storm_sorcerers",)
# Anbennar flavor keys left as "LOC TO-DO": units nobody can recruit, and keys no unit uses.
NO_FLAVOR_NEEDED = {"storm_sorcerers", "dwarven_handgunners", "bulwari_phalanx", "dwarven_bombard"}


def _text(path):
    return path.read_bytes().decode("utf-8-sig") if path.is_file() else ""


def blocks(rel):
    return parse_blocks(_text(SUBMOD / rel))


def base_blocks(rel):
    return parse_blocks(_text(ANBENNAR / rel))


def squash(body):
    return " ".join(strip_comments(body).split())


def without_blocks(body, names):
    """A block body with the named depth-0 sub-blocks removed."""
    for name in names:
        m = re.search(rf"(?<![\w.:]){name}\s*=\s*\{{", body)
        if m:
            body = body[:m.start()] + body[_balanced(body, m.end() - 1):]
    return body


def maa_files():
    """Every men-at-arms file of the game, Anbennar and the overhaul, in load order (a same-named file of a later
    mod replaces the earlier one; objects defined twice: the last file wins)."""
    game = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
    by_name = {}
    for root in (game, ANBENNAR, SUBMOD):
        for f in (root / "common/men_at_arms_types").glob("*.txt"):
            by_name[f.name] = f
    return [by_name[n] for n in sorted(by_name)]


class MageMaaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ours = blocks(MAA_FILE)
        cls.base = base_blocks(BASE_MAA_FILE)

    def test_only_battlemages_and_storm_sorcerers_are_overridden(self):
        self.assertEqual(set(self.ours), set(GATES))

    def test_units_regated_and_otherwise_anbennars(self):
        for key, gate in GATES.items():
            self.assertEqual(squash(parse_blocks(self.ours[key]).get("can_recruit", "")), gate, key)
            self.assertEqual(squash(without_blocks(self.ours[key], ("can_recruit",))),
                             squash(without_blocks(self.base[key], ("can_recruit",))), key)

    def test_no_other_cultural_mage_unit_changes_hands(self):
        effective = {}
        for f in maa_files():
            effective.update(parse_blocks(_text(f)))
        open_mages = {key for key, body in effective.items()
                      if re.search(r"\btype\s*=\s*mages\b", strip_comments(body))
                      and squash(parse_blocks(body).get("can_recruit", "")) != "always = no"
                      and not key.startswith("aov_")}
        gated = {key for key in open_mages if squash(parse_blocks(effective[key]).get("can_recruit", "")) == ACADEMY_GATE}
        self.assertEqual(open_mages - gated, KEPT_MAGES)
        self.assertEqual(gated, {"battlemages"})


class GnomeMaaTests(unittest.TestCase):
    def test_generic_artificers_disabled_and_otherwise_anbennars(self):
        ours, base = blocks(GNOME_MAA_FILE), base_blocks(BASE_GENERICS_FILE)
        self.assertEqual(set(ours), {"artificers", "armored_artificers"})
        for key in ours:
            self.assertEqual(squash(parse_blocks(ours[key]).get("can_recruit", "")), "always = no", key)
            self.assertEqual(squash(without_blocks(ours[key], ("can_recruit",))),
                             squash(without_blocks(base[key], ("can_recruit",))), key)

    def test_handgunners_are_the_artificers(self):
        self.assertRegex(_text(SUBMOD / "localization/english/aov_artificery_l_english.yml"),
                         r'(?m)^ artificer_handgunners: "Artificers"$')


class HalflingMaaTests(unittest.TestCase):
    def test_small_knights_lose_only_the_era_gate(self):
        ours, base = blocks(HALFLING_MAA_FILE), base_blocks(BASE_TYPES_FILE)
        self.assertEqual(set(ours), {"smallknights"})
        self.assertEqual(squash(parse_blocks(ours["smallknights"]).get("can_recruit", "")),
                         "culture = { has_cultural_parameter = unlock_maa_anb_smallknights }")
        self.assertEqual(squash(without_blocks(ours["smallknights"], ("can_recruit",))),
                         squash(without_blocks(base["smallknights"], ("can_recruit",))))


class MageTraditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ours = blocks(TRADITION_FILE)
        cls.base = base_blocks(BASE_TRADITION_FILE)
        cls.on_actions = blocks(ON_ACTION_FILE)

    def test_retired_traditions_hidden_and_unpickable(self):
        self.assertEqual(set(self.ours), set(RETIRED))
        for key in RETIRED:
            inner = parse_blocks(self.ours[key])
            self.assertEqual(squash(inner.get("is_shown", "")), "always = no", key)
            self.assertEqual(squash(inner.get("can_pick", "")), "always = no", key)

    def test_overrides_match_anbennar_elsewhere(self):
        for key in RETIRED:
            self.assertEqual(squash(without_blocks(self.ours[key], ("is_shown", "can_pick"))),
                             squash(without_blocks(self.base[key], ("is_shown", "can_pick"))), key)

    def test_game_start_removes_them(self):
        self.assertIn("aov_mage_maa_game_start", squash(self.on_actions.get("on_game_start", "")))
        effect = squash(self.on_actions.get("aov_mage_maa_game_start", ""))
        for key in RETIRED:
            self.assertRegex(effect, rf"every_culture_global = {{ limit = {{ has_cultural_tradition = {key} }} "
                                     rf"remove_culture_tradition = {key} }}")


class MageInnovationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ours = blocks(INNOVATION_FILE)
        cls.base = base_blocks(BASE_INNOVATION_FILE)

    def test_battlemages_innovation_loses_only_its_unit(self):
        self.assertEqual(squash(self.ours["innovation_battlemages"]),
                         squash(self.base["innovation_battlemages"].replace("custom = unlock_maa_battlemages", "")))

    def test_only_magic_schools_is_overridden(self):
        self.assertEqual(set(self.ours), {"innovation_battlemages"})

    def test_icon_variables_defined(self):
        text = _text(SUBMOD / INNOVATION_FILE)
        for var in set(re.findall(r"icon = @(\w+)", text)):
            self.assertRegex(text, rf"(?m)^@{var} = ", var)


class FlavorTests(unittest.TestCase):
    def test_every_recruitable_unit_replaces_loc_to_do(self):
        base = _text(ANBENNAR / BASE_LOC_FILE)
        todo = set(re.findall(r"^\s+(\w+)_flavor:\d*\s+\"#F LOC TO-DO\.#!\"", base, re.M))
        ours = dict(re.findall(r"^\s+(\w+)_flavor:\d*\s+\"(.*)\"$", _text(SUBMOD / FLAVOR_FILE), re.M))
        self.assertEqual(todo - set(ours), NO_FLAVOR_NEEDED - set(ours))
        self.assertFalse(NO_FLAVOR_NEEDED & set(ours))
        for key, value in ours.items():
            self.assertRegex(value, r"^#F .+#!$", key)
            self.assertNotIn("TO-DO", value, key)

    def test_joke_flavor_replaced(self):
        base = _text(ANBENNAR / BASE_LOC_FILE)
        ours = dict(re.findall(r"^\s+(\w+)_flavor:\d*\s+\"(.*)\"$", _text(SUBMOD / JOKE_FLAVOR_FILE), re.M))
        self.assertTrue(ours)
        self.assertFalse(set(ours) & {"artificers", "armored_artificers"})
        for key, value in ours.items():
            self.assertRegex(base, rf"(?m)^\s+{key}_flavor:\d*\s+\"(?!#F)", key)
            self.assertRegex(value, r"^#F .+#!$", key)

    def test_base_battlemages_renamed(self):
        self.assertRegex(_text(SUBMOD / FLAVOR_FILE), r'(?m)^ battlemages:0 "War Mages"$')


if __name__ == "__main__":
    unittest.main()
