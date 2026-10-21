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


if __name__ == "__main__":
    unittest.main()
