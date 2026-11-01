"""Tests for the regional elven cultures: definitions, localization, game-start assignment, purist roll override.

    python -I -m unittest discover -s tools/tests -p "test_elven_cultures*.py"
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdx_script import ANBENNAR_CK3 as ANBENNAR, parse_blocks, strip_comments  # noqa: E402

SUBMOD = Path(__file__).resolve().parent.parent.parent

CULTURE_FILE = "common/culture/cultures/aov_elven_cultures.txt"
PARENT_FILE = "common/culture/cultures/anb_elven.txt"  # the overhaul's generated override (gfx keys)
LOC_FILE = "localization/english/aov_elven_cultures_l_english.yml"
ON_ACTION_FILE = "common/on_action/aov_elven_cultures_on_actions.txt"
EFFECT_FILE = "common/scripted_effects/aov_elven_cultures_effects.txt"
OVERRIDE_FILE = "common/scripted_effects/zz_aov_elven_culture_overrides.txt"
BASE_PURIST_FILE = "common/scripted_effects/anb_scripted_effects/anb_racial_effects.txt"
MARK = "# Anbennar Overhaul: regional elven cultures"

CULTURES = {  # culture -> parent
    "lake_elvish": "wood_elvish", "mountain_elvish": "wood_elvish", "thorn_elvish": "wood_elvish",
    "bone_elvish": "wood_elvish", "hunter_elvish": "wood_elvish", "flower_elvish": "wood_elvish",
    "river_elvish": "wood_elvish", "arrow_elvish": "wood_elvish", "shadow_elvish": "wood_elvish",
    "redglader": "moon_elvish", "ibevari": "moon_elvish", "celmaldorian": "moon_elvish", "venaili": "moon_elvish",
}
# Fields a regional culture copies from its parent (everything but color, created, parents, ethos, traditions and
# history loc).
COPIED = ("heritage", "language", "martial_custom", "head_determination", "name_list", "coa_gfx",
          "building_gfx", "clothing_gfx", "unit_gfx", "ethnicities")
# Traditions in the culture file, chosen from each realm's EU4 ideas (racial-traditions.md grants two more at game
# start). Every culture keeps Equal Inheritance, and every wood elf culture Forest Folk.
TRADITIONS = {
    "lake_elvish": "philosopher_culture", "mountain_elvish": "mountain_homes", "thorn_elvish": "sacred_groves",
    "bone_elvish": "hit_and_run", "hunter_elvish": "hunters", "flower_elvish": "medicinal_plants",
    "river_elvish": "xenophilic", "arrow_elvish": "artisans", "shadow_elvish": "mystical_ancestors",
    "redglader": "astute_diplomats poetry", "ibevari": "stalwart_defenders artisans",
    "celmaldorian": "maritime_mercantilism seafaring", "venaili": "seafaring isolationist",
}


def _text(path):
    return path.read_bytes().decode("utf-8-sig")


def fields(body):
    """Top-level `key = value` and `key = { ... }` of a block body -> whitespace-squashed value."""
    out, code, pos = {}, strip_comments(body), 0
    pattern = re.compile(r"([A-Za-z0-9_]+)\s*=\s*(\{|[^\s{}]+)")
    while True:
        m = pattern.search(code, pos)
        if not m:
            return out
        if m.group(2) == "{":
            depth, i = 0, m.end() - 1
            for i in range(m.end() - 1, len(code)):
                depth += {"{": 1, "}": -1}.get(code[i], 0)
                if depth == 0:
                    break
            out.setdefault(m.group(1), " ".join(code[m.end():i].split()))
            pos = i + 1
        else:
            out.setdefault(m.group(1), m.group(2))
            pos = m.end()


def title_counties():
    """Anbennar landed titles: title -> its de jure counties (a county maps to itself)."""
    counties, stack, depth = {}, [], 0
    for path in sorted((ANBENNAR / "common/landed_titles").glob("*.txt")):
        for line in _text(path).split("\n"):
            code = line.split("#", 1)[0]
            m = re.match(r"\s*([ekdc]_[A-Za-z0-9_]+)\s*=\s*\{", code)
            if m:
                stack.append((m.group(1), depth))
                counties.setdefault(m.group(1), [])
                if m.group(1).startswith("c_"):
                    for title, _ in stack:
                        counties[title].append(m.group(1))
            depth += code.count("{") - code.count("}")
            while stack and depth <= stack[-1][1]:
                stack.pop()
    return counties


def county_cultures():
    """Anbennar county -> culture of its capital (first) barony's province at game start."""
    province_culture = {}
    for path in (ANBENNAR / "history/provinces").glob("*.txt"):
        for key, body in parse_blocks(_text(path)).items():
            m = re.search(r"^\s*culture\s*=\s*\"?(\w+)", re.sub(r"\d+\.\d+\.\d+\s*=\s*\{[^}]*\}", "", body), re.M)
            if key.isdigit() and m:
                province_culture[int(key)] = m.group(1)
    from pdx_script import ck3_titles
    provinces, county_baronies = ck3_titles()
    return {county: province_culture.get(provinces.get(baronies[0])) for county, baronies in county_baronies.items()
            if baronies}


class CultureDefinitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cultures = parse_blocks(_text(SUBMOD / CULTURE_FILE))
        cls.parents = parse_blocks(_text(SUBMOD / PARENT_FILE))

    def test_every_culture_defined_once(self):
        self.assertEqual(sorted(self.cultures), sorted(CULTURES))
        text = strip_comments(_text(SUBMOD / CULTURE_FILE))
        for key in CULTURES:
            self.assertEqual(len(re.findall(rf"^{key} = \{{", text, re.M)), 1, key)

    def test_parent_created_and_ethos(self):
        for key, parent in CULTURES.items():
            got = fields(self.cultures[key])
            self.assertEqual(got["parents"], parent, key)
            self.assertRegex(got["created"], r"^\d+\.\d+\.\d+$", key)
            self.assertTrue(got["ethos"].startswith("ethos_"), key)
            self.assertEqual(got["history_loc_override"], f"{key}_history_loc", key)

    def test_copies_parent_fields(self):
        """Gfx, traditions, name list and the rest match the parent as the overhaul's anb_elven.txt defines it, so
        the holding, unit and portrait models (build_holding_models.py, build_portraits.py) show for them too."""
        for key, parent in CULTURES.items():
            got, want = fields(self.cultures[key]), fields(self.parents[parent])
            for name in COPIED:
                self.assertEqual(got.get(name), want.get(name), f"{key}.{name}")

    def test_traditions_chosen_per_culture(self):
        for key, parent in CULTURES.items():
            want = {f"tradition_{t}" for t in TRADITIONS[key].split()} | {"tradition_equal_inheritance"}
            if parent == "wood_elvish":
                want.add("tradition_forest_folk")
            self.assertEqual(set(fields(self.cultures[key])["traditions"].split()), want, key)

    def test_colors_distinct(self):
        colors = [fields(body)["color"] for body in self.cultures.values()]
        self.assertEqual(len(colors), len(set(colors)))


class LocalizationTests(unittest.TestCase):
    def test_every_key(self):
        text = _text(SUBMOD / LOC_FILE)
        self.assertTrue(text.startswith("l_english:\n"))
        for key in CULTURES:
            for suffix in ("", "_prefix", "_collective_noun", "_history_loc"):
                self.assertRegex(text, rf"\n {key}{suffix}:0 \"[^\"]+\"\n", key + suffix)


class GameStartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.effects = _text(SUBMOD / EFFECT_FILE)
        cls.counties = title_counties()
        cls.county_culture = county_cultures()

    def test_hooked_on_game_start(self):
        blocks = parse_blocks(_text(SUBMOD / ON_ACTION_FILE))
        self.assertIn("aov_elven_cultures_game_start", blocks["on_game_start"])
        self.assertIn("aov_elven_cultures_game_start_effect = yes", blocks["aov_elven_cultures_game_start"])

    def assignments(self):
        return re.findall(r"title:(\w+) = \{ (aov_set_regional_elven(?:_county)?_culture_effect) = \{ "
                          r"PARENT = (\w+) CULTURE = (\w+) \} \}", self.effects)

    def test_every_culture_assigned_from_its_parent(self):
        found = self.assignments()
        self.assertEqual({culture for *_, culture in found}, set(CULTURES))
        for title, effect, parent, culture in found:
            self.assertEqual(parent, CULTURES[culture], title)
            self.assertEqual(effect.endswith("_county_culture_effect"), title.startswith("c_"), title)

    def test_titles_still_hold_parent_culture_counties(self):
        """After an Anbennar update: each title exists and still has counties of the parent culture to convert."""
        for title, _effect, parent, culture in self.assignments():
            self.assertIn(title, self.counties, title)
            of_parent = [c for c in self.counties[title] if self.county_culture.get(c) == parent]
            self.assertTrue(of_parent, f"{title} has no {parent} county left for {culture}")

    def test_no_grove_county_left_wood_elvish(self):
        """Every wood elf county at game start is in a grove duchy, so wood_elvish keeps no land."""
        groves = [t for t, _e, parent, _c in self.assignments() if parent == "wood_elvish"]
        covered = {c for t in groves for c in self.counties[t]}
        wood = {c for c, culture in self.county_culture.items() if culture == "wood_elvish"}
        self.assertEqual(wood - covered, set())

    def test_characters_follow_their_county(self):
        for parent in ("wood_elvish", "moon_elvish"):
            self.assertIn(f"aov_adopt_regional_elven_culture_effect = {{ PARENT = {parent} }}", self.effects)
        self.assertIn("set_culture = location.county.culture", self.effects)
        self.assertIn("has_cultural_pillar = heritage_elven", self.effects)


class PuristOverrideTests(unittest.TestCase):
    def test_copy_matches_anbennar_but_marked_lines(self):
        """Fails when Anbennar changes roll_racial_purity_trait_for_character: re-copy it (docs/systems/updating.md)."""
        ours = parse_blocks(_text(SUBMOD / OVERRIDE_FILE))["roll_racial_purity_trait_for_character"]
        base = parse_blocks(_text(ANBENNAR / BASE_PURIST_FILE))["roll_racial_purity_trait_for_character"]
        raw = _text(SUBMOD / OVERRIDE_FILE)
        self.assertEqual(raw.count(MARK), 2)
        restored = (ours.replace("culture = { aov_sun_elven_lineage_trigger = yes }", "has_culture = culture:sun_elvish")
                    .replace("culture = { aov_moon_elven_lineage_trigger = yes }", "has_culture = culture:moon_elvish"))
        self.assertEqual(" ".join(restored.split()), " ".join(base.split()))


if __name__ == "__main__":
    unittest.main()
