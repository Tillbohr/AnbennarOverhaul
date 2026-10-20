"""Dwarven hold data: the 9 holds and the dig constants. The level effects come from Realms in Exile's
dwarven_depths_01..10 (tools/build_rie_dwarves.py, depths_level_effects).

Specs: docs/superpowers/specs/2026-10-10-dwarven-hold-digging-design.md,
docs/superpowers/specs/2026-10-17-rie-dwarves-design.md (Section 2)
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

DIG_COST_PER_LEVEL = 150
EVENT_CHANCE = 40
STAGE_SHARES = (0.25, 0.75)
TICK_MONTHS = 3


def dig_months(target):
    """Months a dig to level `target` takes: 12 years for level 2, 4 more for each level after."""
    return 12 * (8 + 4 * (target - 1))


RESTORE = {"gold": 300, "prestige": 200, "years": 5}
RUINED_MODIFIER = {"tax_mult": -0.5, "development_growth_factor": -0.5, "levy_size": -0.5}
ASSET_BAND = {1: "castle_01", 2: "castle_01", 3: "castle_02", 4: "castle_02", 5: "castle_03", 6: "castle_03",
              7: "castle_03", 8: "castle_04", 9: "castle_04", 10: "castle_04"}
RUINED_ART = "gfx/interface/illustrations/event_scenes/tgp_ruined_holding.dds"
