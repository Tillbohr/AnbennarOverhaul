"""Dwarven hold data: the 24 holds (9 of Anbennar's, 6 of Serpentreach's, 1 of Segbandal's, 8 of West Dwarovar's) and
the dig constants. The level effects come from Realms in Exile's
dwarven_depths_01..10 (tools/build_rie_dwarves.py, depths_level_effects).

Specs: docs/superpowers/specs/2026-10-10-dwarven-hold-digging-design.md,
docs/superpowers/specs/2026-10-17-rie-dwarves-design.md (Section 2)
"""


def _hold(name, eu4_province, title, barony, start_level):
    return {"name": name, "eu4_province": eu4_province, "title": title, "barony": barony,
            "start_level": start_level}


HOLDS = [
    _hold("Marrhold", 4097, "c_marrhold", "b_marrhold", 1),
    _hold("Anvilwright", 912, "b_anvilwright", "b_anvilwright", 1),
    _hold("Verkal Gulan", 2914, "c_verkal_gulan", "b_gulandhum", 2),
    _hold("Seghdihr", 4124, "c_seghdihr", "b_kar_fimthrun", 2),
    _hold("Ovdal Tûngr", 526, "c_ovdal_tungr", "b_irovar", 2),
    _hold("Rubyhold", 62, "c_rubyhold", "b_hul_az_amekh", 2),
    _hold("Hehodovar", 4078, "c_hehodovar", "b_kar_hargun", 2),
    _hold("Gor Ozumbrog", 4218, "c_gor_ozumbrog", "b_topazhjardan", 2),
    _hold("Khugdihr", 2863, "c_khugdihr", "b_aghatehargun", 1),
    # Serpentreach (tools/build_serpentreach.py makes these titles)
    _hold("Arg-Ôrdstun", 4093, "c_arg_ordstun", "b_arg_ordstun", 2),
    _hold("Ovdal Lodhum", 2973, "c_ovdal_lodhum", "b_ovdal_lodhum", 2),
    _hold("Gor Bûrad", 4039, "c_gor_burad", "b_gor_burad", 2),
    _hold("Shazstundihr", 2942, "c_shazstundihr", "b_shazstundihr", 1),
    _hold("Verkal Skomdihr", 4100, "c_verkal_skomdihr", "b_verkal_skomdihr", 1),
    _hold("Orlghelovar", 4238, "c_orlghelovar", "b_orlghelovar", 1),
    # Segbandal (tools/build_segbandal.py makes these titles)
    _hold("Gor Vazumbrog", 4217, "c_gor_vazumbrog", "b_gor_vazumbrog", 2),
    # West Dwarovar (tools/build_west_dwarovar.py makes these titles); Amldihr, the old capital, starts deeper
    _hold("Amldihr", 4119, "c_amldihr", "b_amldihr", 2),
    _hold("Haraz Orldhûm", 2868, "c_haraz_orldhum", "b_haraz_orldhum", 1),
    _hold("Mithradhûm", 4236, "c_mithradhum", "b_mithradhum", 1),
    _hold("Er-Natvir", 2931, "c_er_natvir", "b_er_natvir", 1),
    _hold("Verkal Kozenad", 4056, "c_verkal_kozenad", "b_verkal_kozenad", 1),
    _hold("Hul-Jorkad", 2963, "c_hul_jorkad", "b_hul_jorkad", 1),
    _hold("Orlazam-az-dihr", 4147, "c_orlazam_az_dihr", "b_orlazam_az_dihr", 1),
    _hold("Dûr-Vazhatun", 4020, "c_dur_vazhatun", "b_dur_vazhatun", 1),
]

DIG_COST_PER_LEVEL = 150
EVENT_CHANCE = 40
STAGE_SHARES = (0.25, 0.75)
TICK_MONTHS = 3


def dig_months(target):
    """Months a dig to level `target` takes: 12 years for level 2, 4 more for each level after."""
    return 12 * (8 + 4 * (target - 1))


ASSET_BAND = {1: "castle_01", 2: "castle_01", 3: "castle_02", 4: "castle_02", 5: "castle_03", 6: "castle_03",
              7: "castle_03", 8: "castle_04", 9: "castle_04", 10: "castle_04"}
