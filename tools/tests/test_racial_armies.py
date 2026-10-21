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


TRADITION_FILE = "common/culture/traditions/zz_aov_racial_traditions.txt"
BASE_TRADITION_FILE = "common/culture/traditions/anb_maa_traditions.txt"
ON_ACTION_FILE = "common/on_action/aov_racial_armies_on_actions.txt"
REMOVED = ("tradition_sundancer_legions", "tradition_test_maa_anb_dwarven_handgunners")


def without_blocks(body, names):
    """A block body with the named depth-0 sub-blocks removed."""
    for name in names:
        m = re.search(rf"(?<![\w.:]){name}\s*=\s*\{{", body)
        if m:
            body = body[:m.start()] + body[_balanced(body, m.end() - 1):]
    return body


class TraditionRemovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ours = blocks(TRADITION_FILE)
        cls.base = base_blocks(BASE_TRADITION_FILE)
        cls.on_actions = blocks(ON_ACTION_FILE)

    def test_removed_traditions_hidden_and_unpickable(self):
        self.assertEqual(set(self.ours), set(REMOVED))
        for key in REMOVED:
            inner = parse_blocks(self.ours[key])
            self.assertEqual(squash(inner.get("is_shown", "")), "always = no", key)
            self.assertEqual(squash(inner.get("can_pick", "")), "always = no", key)

    def test_overrides_match_anbennar_elsewhere(self):
        for key in REMOVED:
            self.assertEqual(squash(without_blocks(self.ours.get(key, ""), ("is_shown", "can_pick"))),
                             squash(without_blocks(self.base[key], ("is_shown", "can_pick"))), key)

    def test_game_start_removes_both(self):
        self.assertIn("aov_racial_armies_game_start", squash(self.on_actions.get("on_game_start", "")))
        effect = squash(self.on_actions.get("aov_racial_armies_game_start", ""))
        for key in REMOVED:
            self.assertRegex(effect, rf"every_culture_global = {{ limit = {{ has_cultural_tradition = {key} }} "
                                     rf"remove_culture_tradition = {key} }}")


VALUES_FILE = "common/script_values/aov_racial_maa_values.txt"
VANILLA = {  # regiment damage, regiment toughness, buy, low upkeep (spec, Pricing)
    "skirmishers": (1000, 1600, 45, 0.15), "archers": (2500, 1000, 55, 0.2), "crossbow": (4200, 1800, 88, 0.3),
    "pikemen": (2200, 2400, 75, 0.3), "heavy_infantry": (3200, 2200, 90, 0.4),
    "light_cavalry": (2200, 1500, 85, 0.35), "heavy_cavalry": (5000, 1750, 200, 0.7),
}
ROSTER = {  # key -> role, men, damage, toughness (spec roster tables)
    "aithchri": ("archers", 50, 120, 35), "sheahrna": ("pikemen", 50, 90, 110),
    "staochri": ("heavy_infantry", 25, 300, 200), "marcairna": ("light_cavalry", 50, 90, 60),
    "aov_elven_knights": ("heavy_cavalry", 25, 450, 160), "aov_gladeguards": ("skirmishers", 50, 45, 70),
    "sundancer_legions": ("heavy_infantry", 25, 280, 240), "jaherkadezim": ("heavy_cavalry", 25, 480, 150),
    "aov_sunspear_phalanx": ("pikemen", 50, 80, 130), "aov_phoenix_bowmen": ("archers", 50, 110, 40),
    "aov_sandwind_outriders": ("light_cavalry", 50, 80, 55), "aov_duneblades": ("skirmishers", 50, 50, 60),
    "ayethi": ("archers", 50, 110, 35), "felwyr": ("skirmishers", 50, 50, 70), "glaifes": ("pikemen", 50, 80, 110),
    "hyodeth": ("light_cavalry", 50, 90, 60), "aov_greatoak_wardens": ("heavy_infantry", 25, 260, 220),
    "dwarven_guardians": ("heavy_infantry", 80, 48, 60), "shieldwall": ("pikemen", 80, 30, 70),
    "armor_breakers": ("crossbow", 80, 55, 35), "ramriders": ("light_cavalry", 50, 50, 45),
    "aov_grudgebearers": ("pikemen", 80, 40, 60), "aov_tortoise_formation": ("pikemen", 80, 26, 110),
    "aov_giantbane_crossbows": ("crossbow", 80, 65, 35), "aov_uthojdihr_marines": ("skirmishers", 80, 30, 50),
    "aov_seg_band_gnollhunters": ("skirmishers", 80, 35, 40), "aov_golden_gate_guard": ("heavy_infantry", 50, 70, 160),
    "aov_clockwork_bows": ("crossbow", 80, 80, 30), "aov_dauvek_veker": ("heavy_infantry", 50, 110, 90),
    "aov_copper_road_wardens": ("light_cavalry", 50, 55, 55), "aov_brightbeard_hammers": ("heavy_infantry", 50, 100, 70),
}


def cost_prefix(key):
    """Script value prefix of a unit's costs: aov_ + the key without its own aov_."""
    return "aov_" + key.removeprefix("aov_")


def flat_values(text):
    """name -> number for `name = <number>` script values at the top level of a file."""
    return {k: float(v) for k, v in re.findall(r"^([A-Za-z0-9_]+)\s*=\s*(-?[0-9.]+)\s*$", strip_comments(text), re.M)}


class PricingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = _text(SUBMOD / VALUES_FILE)
        cls.values, cls.blocks = flat_values(text), parse_blocks(text)

    def test_every_unit_priced_at_vanilla_power_per_gold(self):
        for key, (role, men, dmg, tough) in ROSTER.items():
            vd, vt, vb, vu = VANILLA[role]
            factor = ((men * dmg / vd) * (men * tough / vt)) ** 0.5
            p = cost_prefix(key)
            buy, low, high = (self.values.get(f"{p}_{s}") for s in ("recruitment_cost", "low_maint_cost", "high_maint_cost"))
            self.assertIsNotNone(buy, key)
            self.assertAlmostEqual(buy, vb * factor, delta=vb * factor * 0.05, msg=key)
            self.assertAlmostEqual(low, vu * factor, delta=vu * factor * 0.05, msg=key)
            self.assertAlmostEqual(high, 3 * low, places=6, msg=key)

    def test_engineer_corps_costs_scale_bombards(self):
        for suffix, source in (("recruitment_cost", "dwarven_bombards_recruitment_cost"),
                               ("low_maint_cost", "dwarven_bombard_low_maint_cost"),
                               ("high_maint_cost", "dwarven_bombard_high_maint_cost")):
            self.assertEqual(squash(self.blocks.get(f"aov_silverforge_engineers_{suffix}", "")),
                             f"value = {source} multiply = 1.3", suffix)


OVERRIDE_MAA_FILE = "common/men_at_arms_types/zz_aov_racial_maa_overrides.txt"
NEW_MAA_FILES = ("common/men_at_arms_types/aov_elven_maa_types.txt", "common/men_at_arms_types/aov_dwarven_maa_types.txt")
BASE_MAA_FILES = ("common/men_at_arms_types/anb_cultural_maa_generics.txt",
                  "common/men_at_arms_types/anb_cultural_maa_types.txt")
LOC_FILE = "localization/english/aov_racial_armies_l_english.yml"
REPLACE_LOC_FILE = "localization/replace/english/aov_racial_armies_replace_l_english.yml"

MOON, SUN, WOOD = "aov_moon_elven_lineage_trigger", "aov_sun_elven_lineage_trigger", "aov_wood_elven_lineage_trigger"
EXPECTED = {  # key -> type, stack, damage, toughness, pursuit, screen, gate (spec roster tables)
    "aithchri": ("archers", 50, 120, 35, 0, 0, MOON),
    "sheahrna": ("pikemen", 50, 90, 110, 0, 0, MOON),
    "staochri": ("heavy_infantry", 25, 300, 200, 10, 10, MOON),
    "marcairna": ("light_cavalry", 50, 90, 60, 90, 90, MOON),
    "aov_elven_knights": ("heavy_cavalry", 25, 450, 160, 40, 0, MOON),
    "aov_gladeguards": ("skirmishers", 50, 45, 70, 30, 60, MOON),
    "sundancer_legions": ("heavy_infantry", 25, 280, 240, 20, 20, SUN),
    "jaherkadezim": ("heavy_cavalry", 25, 480, 150, 40, 0, SUN),
    "aov_sunspear_phalanx": ("pikemen", 50, 80, 130, 0, 0, SUN),
    "aov_phoenix_bowmen": ("archers", 50, 110, 40, 0, 0, SUN),
    "aov_sandwind_outriders": ("light_cavalry", 50, 80, 55, 100, 80, SUN),
    "aov_duneblades": ("skirmishers", 50, 50, 60, 40, 50, SUN),
    "ayethi": ("archers", 50, 110, 35, 0, 0, WOOD),
    "felwyr": ("skirmishers", 50, 50, 70, 20, 60, WOOD),
    "glaifes": ("pikemen", 50, 80, 110, 0, 0, WOOD),
    "hyodeth": ("light_cavalry", 50, 90, 60, 90, 90, WOOD),
    "aov_greatoak_wardens": ("heavy_infantry", 25, 260, 220, 10, 10, WOOD),
}
SUN_TERRAIN = {"desert": 0.2, "drylands": 0.2, "floodplains": 0.2, "plains": 0.2, "jungle": -0.2, "forest": -0.2}
WOOD_TERRAIN = {"forest": 0.5, "taiga": 0.5, "jungle": 0.5, "wetlands": 0.5, "desert": -0.2, "drylands": -0.2,
                "plains": -0.2}
TERRAIN_SETS = {key: {} for key in EXPECTED}  # key -> terrain -> fraction of base damage/toughness
TERRAIN_SETS.update({"aithchri": {"forest": 0.2, "hills": 0.2, "taiga": 0.2},
                     "aov_gladeguards": {"forest": 0.5, "hills": 0.2, "taiga": 0.2}})
TERRAIN_SETS.update({key: SUN_TERRAIN for key, row in EXPECTED.items() if row[6] == SUN})
TERRAIN_SETS.update({key: WOOD_TERRAIN for key, row in EXPECTED.items() if row[6] == WOOD})
WINTER_SETS = {key: {"normal_winter": -0.2, "harsh_winter": -0.2} for key, row in EXPECTED.items() if row[6] == SUN}

DWARF = "heritage_dwarven"
EXPECTED.update({  # spec dwarf tables
    "dwarven_guardians": ("heavy_infantry", 80, 48, 60, 0, 15, DWARF),
    "shieldwall": ("pikemen", 80, 30, 70, 0, 0, DWARF),
    "armor_breakers": ("archers", 80, 55, 35, 0, 0, DWARF),
    "ramriders": ("light_cavalry", 50, 50, 45, 25, 40, DWARF),
    "aov_grudgebearers": ("pikemen", 80, 40, 60, 0, 0, "aov_ruby_dwarven_lineage_trigger"),
    "aov_tortoise_formation": ("pikemen", 80, 26, 110, 0, 0, "aov_stone_dwarven_lineage_trigger"),
    "aov_giantbane_crossbows": ("archers", 80, 65, 35, 0, 0, "aov_agate_dwarven_lineage_trigger"),
    "aov_uthojdihr_marines": ("skirmishers", 80, 30, 50, 0, 0, "aov_copper_dwarven_lineage_trigger"),
    "aov_seg_band_gnollhunters": ("skirmishers", 80, 35, 40, 40, 0, "aov_citrine_dwarven_lineage_trigger"),
    "aov_golden_gate_guard": ("heavy_infantry", 50, 70, 160, 0, 0, "aov_gold_dwarven_lineage_trigger"),
    "aov_clockwork_bows": ("archers", 80, 80, 30, 0, 0, "aov_pyrite_dwarven_lineage_trigger"),
    "aov_dauvek_veker": ("heavy_infantry", 50, 110, 90, 0, 0, "aov_titanium_dwarven_lineage_trigger"),
    "aov_copper_road_wardens": ("light_cavalry", 50, 55, 55, 30, 60, "aov_topaz_dwarven_lineage_trigger"),
    "aov_brightbeard_hammers": ("heavy_infantry", 50, 100, 70, 0, 0, "aov_marble_dwarven_lineage_trigger"),
})
DWARF_TERRAIN = {"hills": 0.3, "mountains": 0.45, "desert_mountains": 0.45, "dwarven_hold": 0.65,
                 "dwarven_hold_surface": 0.65, "cavern": 0.65, "dwarven_road": 0.65, "forest": -0.15}
DWARF_EXTRA = {"aov_grudgebearers": {"plains": 0.2, "farmlands": 0.2},
               "aov_uthojdihr_marines": {"wetlands": 0.5, "floodplains": 0.5, "oasis": 0.5},
               "aov_seg_band_gnollhunters": {"desert": 0.5, "drylands": 0.5, "desert_mountains": 0.5},
               "aov_golden_gate_guard": {"dwarven_hold": 1.0}, "aov_copper_road_wardens": {"dwarven_road": 1.0}}
TERRAIN_SETS.update({key: dict(DWARF_TERRAIN, **DWARF_EXTRA.get(key, {}))
                     for key, row in EXPECTED.items() if row[6] == DWARF or "dwarven_lineage" in row[6]})
CHANGED_FIELDS = ("stack", "damage", "toughness", "pursuit", "screen")
CHANGED_BLOCKS = ("terrain_bonus", "winter_bonus", "can_recruit", "buy_cost", "low_maintenance_cost",
                  "high_maintenance_cost", "ai_quality")


def rnd(x):
    """Round half away from zero, as the MAA files do."""
    return int(abs(x) + 0.5) * (1 if x >= 0 else -1)


def loc_keys(text):
    return set(re.findall(r"^\s+([A-Za-z0-9_.]+):\d*\s", text, re.M))


def bonus_table(body):
    """terrain -> (damage, toughness) of a terrain_bonus / winter_bonus body."""
    return {t: (int(field(b, "damage") or 0), int(field(b, "toughness") or 0)) for t, b in parse_blocks(body).items()}


class MaaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.units = blocks(OVERRIDE_MAA_FILE)
        for rel in NEW_MAA_FILES:
            cls.units.update(blocks(rel))
        cls.base = {}
        for rel in BASE_MAA_FILES:
            cls.base.update(base_blocks(rel))
        cls.loc = loc_keys(_text(SUBMOD / LOC_FILE)) | loc_keys(_text(SUBMOD / REPLACE_LOC_FILE))

    def unit(self, key):
        self.assertIn(key, self.units)
        return self.units[key]

    def test_units_have_spec_stats(self):
        for key, (kind, stack, dmg, tough, pursuit, screen, _gate) in EXPECTED.items():
            body = self.unit(key)
            got = [field(body, f) for f in ("type", "stack", "damage", "toughness", "pursuit", "screen")]
            self.assertEqual(got, [kind] + [str(v) for v in (stack, dmg, tough, pursuit, screen)], key)

    def test_units_gated_by_their_lineage(self):
        for key, row in EXPECTED.items():
            gate = row[6]
            want = (f"culture = {{ has_cultural_pillar = {gate} }}" if gate.startswith("heritage_")
                    else f"culture = {{ {gate} = yes }}")
            self.assertEqual(squash(parse_blocks(self.unit(key)).get("can_recruit", "")), want, key)

    def test_units_use_their_cost_values(self):
        for key in EXPECTED:
            inner, p = parse_blocks(self.unit(key)), cost_prefix(key)
            for block, suffix in (("buy_cost", "recruitment_cost"), ("low_maintenance_cost", "low_maint_cost"),
                                  ("high_maintenance_cost", "high_maint_cost")):
                self.assertEqual(squash(inner.get(block, "")), f"gold = {p}_{suffix}", key)

    def test_retuned_units_keep_unchanged_fields(self):
        def rest(body):
            body = without_blocks(strip_comments(body), CHANGED_BLOCKS)
            return squash(re.sub(rf"(?<![\w.:])(?:{'|'.join(CHANGED_FIELDS)})\s*=\s*\S+", "", body))
        for key in EXPECTED:
            if key in self.base:
                self.assertEqual(rest(self.unit(key)), rest(self.base[key]), key)

    def test_terrain_bonuses_follow_spec_percentages(self):
        for key, terrains in TERRAIN_SETS.items():
            row, inner = EXPECTED[key], parse_blocks(self.unit(key))
            want = {t: (rnd(row[2] * f), rnd(row[3] * f)) for t, f in terrains.items()}
            self.assertEqual(bonus_table(inner.get("terrain_bonus", "")), want, key)
            winter = {t: (rnd(row[2] * f), rnd(row[3] * f)) for t, f in WINTER_SETS.get(key, {}).items()}
            self.assertEqual(bonus_table(inner.get("winter_bonus", "")), winter, key)

    def test_every_unit_has_name_and_flavor(self):
        for key in EXPECTED:
            self.assertIn(key, self.loc)
            self.assertIn(f"{key}_flavor", self.loc)

    def test_signature_counters(self):
        want = {"aov_giantbane_crossbows": {"beasts": "1", "elephant_cavalry": "1"},
                "aov_dauvek_veker": {"beasts": "2", "elephant_cavalry": "2"},
                "aov_brightbeard_hammers": {"heavy_infantry": "1"}}
        for key, counters in want.items():
            body = parse_blocks(self.unit(key)).get("counters", "")
            for target, value in counters.items():
                self.assertEqual(field(body, target), value, f"{key} {target}")

    def test_engineer_corps_siege(self):
        body = self.unit("aov_silverforge_engineers")
        got = [field(body, f) for f in ("type", "stack", "toughness", "siege_tier", "siege_value")]
        self.assertEqual(got, ["siege_weapon", "20", "40", "4", "0.9"])
        inner = parse_blocks(body)
        self.assertEqual(squash(inner.get("can_recruit", "")), "culture = { aov_silver_dwarven_lineage_trigger = yes }")
        self.assertEqual(squash(inner.get("buy_cost", "")), "gold = aov_silverforge_engineers_recruitment_cost")
        self.assertIn("aov_silverforge_engineers_flavor", self.loc)

    def test_handgunners_disabled(self):
        ours = self.unit("dwarven_handgunners")
        self.assertEqual(squash(parse_blocks(ours).get("can_recruit", "")), "always = no")
        self.assertEqual(squash(without_blocks(ours, ("can_recruit",))),
                         squash(without_blocks(self.base["dwarven_handgunners"], ("can_recruit",))))

    def test_no_racial_unit_gated_by_tradition(self):
        for key, body in self.units.items():
            self.assertNotIn("has_cultural_parameter", parse_blocks(body).get("can_recruit", ""), key)

    def test_ai_quality_uses_cultural_extra_score(self):
        for key in EXPECTED:
            self.assertEqual(squash(parse_blocks(self.unit(key)).get("ai_quality", "")),
                             "value = @cultural_maa_extra_ai_score", key)


if __name__ == "__main__":
    unittest.main()
