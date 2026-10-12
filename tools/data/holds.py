"""Dwarven hold data: the 9 holds, level effects, dwarven buildings and dig constants.

Spec: docs/superpowers/specs/2026-10-10-dwarven-hold-digging-design.md
"""


def _hold(name, eu4_province, title, barony, start_level, ruined=False):
    return {"name": name, "eu4_province": eu4_province, "title": title, "barony": barony,
            "start_level": start_level, "ruined": ruined}


HOLDS = [
    _hold("Marrhold", 4097, "c_marrhold", "b_marrhold", 1),
    _hold("Anvilwright", 912, "b_anvilwright", "b_anvilwright", 1),
    _hold("Verkal Gulan", 2914, "c_verkal_gulan", "b_gulandhum", 2),
    _hold("Seghdihr", 4124, "c_seghdihr", "b_kar_fimthrun", 2),
    _hold("Ovdal Tûngr", 526, "c_ovdal_tungr", "b_irovar", 2),
    _hold("Rubyhold", 62, "c_rubyhold", "b_hul_az_amekh", 2),
    _hold("Hehodovar", 4078, "c_hehodovar", "b_kar_hargun", 2),
    _hold("Gor Ozumbrog", 4218, "c_gor_ozumbrog", "b_topazhjardan", 2),
    _hold("Khugdihr", 2863, "c_khugdihr", "b_aghatehargun", 1, ruined=True),
]

# fort_level, defender_holding_advantage, levy_size, tax_mult, garrison_size, building_slot_add (index 0 = level 1)
_LEVEL_ROWS = [
    (2, 2, 0.05, 0.05, 0.10, 0),
    (2, 3, 0.10, 0.08, 0.20, 0),
    (3, 4, 0.15, 0.11, 0.30, 1),
    (3, 5, 0.20, 0.14, 0.40, 1),
    (4, 6, 0.25, 0.17, 0.50, 1),
    (4, 7, 0.30, 0.20, 0.60, 2),
    (5, 8, 0.35, 0.23, 0.70, 2),
    (5, 9, 0.40, 0.26, 0.80, 2),
    (6, 10, 0.45, 0.29, 0.90, 3),
    (6, 12, 0.50, 0.32, 1.00, 3),
]

# Flat values a castle gives, as the tier of the same script values castles use (castle_01..04 = levy/reinforcement/
# income tier 2/4/6/8, garrison tier 1/3/5/7). Each level is at least the castle of its ASSET_BAND and steps up
# within the band; the script values stop at tier 8.
FLAT_VALUES = {"levy": "normal_building_levy_tier_{}", "max_garrison": "good_building_max_garrison_tier_{}",
               "garrison_reinforcement_factor": "building_garrison_reinforcement_factor_tier_{}",
               "monthly_income": "poor_building_tax_tier_{}"}
# (levy, max_garrison, garrison_reinforcement_factor, monthly_income) tiers, index 0 = level 1
_FLAT_TIERS = [
    (2, 1, 2, 2),
    (3, 2, 3, 3),
    (4, 3, 4, 4),
    (5, 4, 5, 5),
    (6, 5, 6, 6),
    (6, 6, 6, 6),
    (7, 6, 7, 7),
    (8, 7, 8, 8),
    (8, 7, 8, 8),
    (8, 8, 8, 8),
]

LEVELS = [dict(zip(("fort_level", "defender_holding_advantage", "levy_size", "tax_mult", "garrison_size",
                    "building_slot_add"), row))
          | {key: name.format(tier) for (key, name), tier in zip(FLAT_VALUES.items(), tiers)}
          for row, tiers in zip(_LEVEL_ROWS, _FLAT_TIERS)]

# Level 1 effects; building level n = n x these.
DWARVEN_BUILDINGS = [
    {"key": "deep_mine", "min_level": 3, "block": "county_modifier",
     "effects": {"tax_mult": 0.05, "supply_limit_mult": 0.10}},
    {"key": "runeforge", "min_level": 5, "block": "character_modifier",
     "effects": {"heavy_infantry_damage_mult": 0.05, "heavy_infantry_toughness_mult": 0.05}},
    {"key": "hall_of_the_ancestors", "min_level": 7, "block": "character_modifier",
     "effects": {"monthly_prestige": 0.2, "monthly_piety": 0.2}},
]

DIG_COST_PER_LEVEL = 150
EVENT_CHANCE = 40
STAGE_SHARES = (0.25, 0.75)
TICK_MONTHS = 3


def dig_months(target):
    """Months a dig to level `target` takes: 8 years for level 2, 4 more for each level after."""
    return 12 * (8 + 4 * (target - 1))


RESTORE = {"gold": 300, "prestige": 200, "years": 5}
RUINED_MODIFIER = {"tax_mult": -0.5, "development_growth_factor": -0.5, "levy_size": -0.5}
ASSET_BAND = {1: "castle_01", 2: "castle_01", 3: "castle_02", 4: "castle_02", 5: "castle_03", 6: "castle_03",
              7: "castle_03", 8: "castle_04", 9: "castle_04", 10: "castle_04"}
RUINED_ART = "gfx/interface/illustrations/event_scenes/tgp_ruined_holding.dds"
