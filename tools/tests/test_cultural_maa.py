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

BASE_VALUES_FILE = "common/script_values/anb_men_at_arms_values.txt"

ACADEMY_GATE = "aov_battlemage_academy_tier_at_least = { TIER = 2 }"
GATES = {"battlemages": ACADEMY_GATE, "storm_sorcerers": "always = no"}
# Mage units retuned to vanilla armored footmen's power per gold (docs/systems/magic.md, Mage men-at-arms): only
# damage, toughness and the terrain and winter bonuses differ from Anbennar. Druids and Skalds live in the faith file.
RETUNED_MAGES = {"battlemages", "druids", "skalds", "wren_hedge_witches", "bladedancers"}
RETUNED_BLOCKS = ("terrain_bonus", "winter_bonus")
# sqrt(regiment damage x regiment toughness) / buy cost of vanilla armored footmen: 32 / 22 per man, 100 men, 90 gold.
PARITY = (3200 * 2200) ** 0.5 / 90
# Cultural mage units not gated by the academy (Skalds and Druids are recruited by faith: test_faith_maa.py).
KEPT_MAGES = {"skalds", "druids", "wren_hedge_witches", "bladedancers"}
RETIRED = ("tradition_test_maa_anb_storm_sorcerers",)
# Anbennar flavor keys left as "LOC TO-DO": units nobody can recruit, and keys no unit uses.
NO_FLAVOR_NEEDED = {"storm_sorcerers", "dwarven_handgunners", "bulwari_phalanx", "dwarven_bombard"}
# Units the overhaul gives the icon Anbennar ships for them (docs/systems/base-art-fixes.md): Anbennar icon, ours.
ICON_SWAPS = {
    "battlemages": ("mages", "battlemages"),
    "druids": ("mages", "druids"),
    "skalds": ("mages", "skalds"),
    "smallknights": ("heavy_cavalry", "smallknights"),
    "adventurers_maa": ("heavy_infantry", "adventurers"),
    "damerian_longbowmen": ("bowmen", "damerian_longbowmen"),
    "oakfoot_rangers": ("bowmen", "rangers"),
    "thorn_squares": ("pikemen", "thorn_square"),
    "wexonard_greatswords": ("heavy_infantry", "wexonard_greatswords"),
}


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


def anbennar_icon(body, key):
    """Our block with its swapped icon (ICON_SWAPS) put back to Anbennar's, to compare the rest with Anbennar."""
    if key not in ICON_SWAPS:
        return body
    old, new = ICON_SWAPS[key]
    return re.sub(rf"(?m)^(\s*)icon = {new}\s*$", rf"\g<1>icon = {old}", body)


def without_stats(body, key):
    """A retuned mage unit's block without the fields the retune changes; any other block unchanged."""
    if key not in RETUNED_MAGES:
        return body
    return re.sub(r"(?m)^[ \t]*(damage|toughness)[ \t]*=.*$", "", without_blocks(body, RETUNED_BLOCKS))


def stat(body, name):
    """A depth-0 integer field of a men-at-arms block."""
    flat = strip_comments(without_blocks(body, RETUNED_BLOCKS))
    return int(re.search(rf"(?m)^\s*{name}\s*=\s*(-?\d+)", flat).group(1))


def bonuses(body):
    """{(block, terrain or winter): (damage, toughness)} from a block's terrain and winter bonuses."""
    inner = parse_blocks(body)
    found = {}
    for block in RETUNED_BLOCKS:
        for where, d, t in re.findall(r"(\w+)\s*=\s*\{\s*damage\s*=\s*(-?\d+)\s+toughness\s*=\s*(-?\d+)\s*\}",
                                      strip_comments(inner.get(block, ""))):
            found[(block, where)] = (int(d), int(t))
    return found


def mage_buy_cost(key):
    """A cultural mage unit's buy cost from Anbennar's script values (@mages_recruitment_cost times its factor)."""
    text = strip_comments(_text(ANBENNAR / BASE_VALUES_FILE))
    base = float(re.search(r"(?m)^@mages_recruitment_cost\s*=\s*([\d.]+)", text).group(1))
    m = re.search(rf"(?m)^{key}_recruitment_cost\s*=\s*@\[mages_recruitment_cost(?:\s*\*\s*([\d.]+))?\]", text)
    return base * float(m.group(1) or 1)


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

    def test_only_regated_and_retuned_units_are_overridden(self):
        self.assertEqual(set(self.ours), set(GATES) | {"wren_hedge_witches", "bladedancers"})

    def test_units_regated_and_otherwise_anbennars(self):
        for key, gate in GATES.items():
            self.assertEqual(squash(parse_blocks(self.ours[key]).get("can_recruit", "")), gate, key)
        for key in self.ours:
            ours = without_stats(anbennar_icon(self.ours[key], key), key)
            self.assertEqual(squash(without_blocks(ours, ("can_recruit",) if key in GATES else ())),
                             squash(without_blocks(without_stats(self.base[key], key),
                                                   ("can_recruit",) if key in GATES else ())), key)

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


class RetunedMageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.effective = {}
        for f in maa_files():
            cls.effective.update(parse_blocks(_text(f)))
        cls.base = base_blocks(BASE_MAA_FILE)

    def test_power_per_gold_matches_armored_footmen(self):
        for key in RETUNED_MAGES:
            body = self.effective[key]
            men = stat(body, "stack")
            power = (men * stat(body, "damage") * men * stat(body, "toughness")) ** 0.5
            self.assertAlmostEqual(power / mage_buy_cost(key) / PARITY, 1, delta=0.02, msg=key)

    def test_costs_are_anbennars(self):
        for key in RETUNED_MAGES:
            for cost in ("buy_cost", "low_maintenance_cost", "high_maintenance_cost"):
                self.assertEqual(squash(parse_blocks(self.effective[key])[cost]),
                                 squash(parse_blocks(self.base[key])[cost]), key)

    def test_bonuses_keep_their_share_of_the_stats(self):
        for key in RETUNED_MAGES:
            ours, base = self.effective[key], self.base[key]
            scale = (stat(ours, "damage") / stat(base, "damage"), stat(ours, "toughness") / stat(base, "toughness"))
            old, new = bonuses(base), bonuses(ours)
            self.assertEqual(set(new), set(old), key)
            for where, values in old.items():
                for value, factor, got in zip(values, scale, new[where]):
                    self.assertLessEqual(abs(got - value * factor), 1, (key, where))


class GnomeMaaTests(unittest.TestCase):
    def test_generic_artificers_disabled_and_otherwise_anbennars(self):
        ours, base = blocks(GNOME_MAA_FILE), base_blocks(BASE_GENERICS_FILE)
        self.assertEqual(set(ours), {"artificers", "armored_artificers"})
        self.assertEqual(squash(parse_blocks(ours["artificers"]).get("can_recruit", "")), "always = no")
        self.assertEqual(squash(without_blocks(ours["artificers"], ("can_recruit",))),
                         squash(without_blocks(base["artificers"], ("can_recruit",))))
        # armored_artificers is re-enabled as gunpowder troops (test_artificery_research.py)
        self.assertNotEqual(squash(parse_blocks(ours["armored_artificers"]).get("can_recruit", "")), "always = no")

    def test_handgunners_are_the_artificers(self):
        self.assertRegex(_text(SUBMOD / "localization/english/aov_artificery_l_english.yml"),
                         r'(?m)^ artificer_handgunners: "Artificers"$')


class HalflingMaaTests(unittest.TestCase):
    def test_small_knights_lose_only_the_era_gate(self):
        ours, base = blocks(HALFLING_MAA_FILE), base_blocks(BASE_TYPES_FILE)
        self.assertEqual(set(ours), {"smallknights"})
        self.assertEqual(squash(parse_blocks(ours["smallknights"]).get("can_recruit", "")),
                         "culture = { has_cultural_parameter = unlock_maa_anb_smallknights }")
        knights = anbennar_icon(ours["smallknights"], "smallknights")
        self.assertEqual(squash(without_blocks(knights, ("can_recruit",))),
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
