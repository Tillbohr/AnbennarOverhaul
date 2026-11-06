"""Which orc and goblin tribe holds which EU4 area in the Serpentspine in 1022, and the system's starting values.

The first county of each tribe is its seat. Dwarves keep DWARF_REALMS; kobolds keep what Anbennar gives them around
Khugdihr. Every other carved county has a tribe (test_dwarovar_tribes.py checks this against the traced regions).

Spec: docs/superpowers/specs/2026-11-05-dwarovar-tribes-design.md
"""

from collections import namedtuple

# race: "orc" or "goblin"; seat: an EU4 province id; areas: EU4 area keys; extra, removed: single EU4 province ids added
# to or taken from those areas; tag: the EU4 country whose flag is the dynasty's arms, or None for generated arms.
Tribe = namedtuple("Tribe", "name race seat areas extra removed tag")


def _tribe(name, race, seat, areas, extra=(), removed=(), tag=None):
    return Tribe(name, race, seat, tuple(f"{a}_area" for a in areas), tuple(extra), tuple(removed), tag)


LAVAWATER, BURAD_DEPTHS, MOLTEN_CORE, BURADFORGE = 4040, 4042, 4041, 2949
ARG_ORDSTUN_HOLD = 4093  # the hold county stays dwarven; the rest of arg_ordstun_area is Diamond Mines orcs'

TRIBES = {
    # Orcs
    "masked_butcher": _tribe("Masked Butcher", "orc", 4033, ("north_altar", "south_altar", "orlghelovar", "argrod_origin"),
                             tag="H81"),
    "moltenbrand": _tribe("Moltenbrand", "orc", 4039, ("gor_burad", "argrod_14_16", "argrod_junction", "argrod_9_11"),
                          extra=(LAVAWATER, BURAD_DEPTHS)),
    "diamond_mines_orcs": _tribe("Diamond Mines orcs", "orc", 2947, ("arg_ordstun", "kings_caverns"),
                                 removed=(ARG_ORDSTUN_HOLD,)),
    "still_caverns_orcs": _tribe("Still Caverns orcs", "orc", 2977, ("still_caverns",)),
    "amldihr_orcs": _tribe("Amldihr orcs", "orc", 4119,
                           ("amldihr", "royal_terrace", "common_terrace", "assembly_terrace", "castle_hill")),
    "orldhum_orcs": _tribe("Orldhûm orcs", "orc", 2868,
                           ("orldhum", "dwarovrod_4_6", "dwarfbreak", "dark_depths", "chainlink_mines")),
    "mithradhum_orcs": _tribe("Mithradhûm orcs", "orc", 4236, ("mithradhum", "dwarovrod_7_9", "dwarovrod_10_12", "riftway")),
    "kozenad_orcs": _tribe("Kozenad orcs", "orc", 4056,
                           ("stunad_kozenad", "dwarovrod_15_17", "travelers_refuge", "zokkorna_caverns")),
    "orlazam_orcs": _tribe("Orlazam orcs", "orc", 4147, ("orlazam", "dagrinrod_4_6", "dagrinrod_7_9", "old_dagrinrod")),
    "wretched_skull": _tribe("Wretched Skull", "orc", 2963, ("jorkad_junction", "azmak", "dwarovrod_21_24"), tag="H86"),
    "railyard_orcs": _tribe("Railyard orcs", "orc", 2931, ("railyard", "railyard_exchange", "dagrite_depths")),
    "skewered_drake": _tribe("Skewered Drake", "orc", 4217, ("vazumbrog", "dwarovrod_27_29", "misty_cave_trail"), tag="H73"),
    "deep_ones_orcs": _tribe("Deep One's orcs", "orc", 4079, ("deep_ones_lair",)),
    # Goblins
    "skomdihr_goblins": _tribe("Skomdihr goblins", "goblin", 4100, ("stunad_skomdihr", "argrod_6_8")),
    "burnt_skin": _tribe("Burnt Skin", "goblin", MOLTEN_CORE, ("zarn",), extra=(MOLTEN_CORE, BURADFORGE), tag="M05"),
    "shazstundihr_squatters": _tribe("Shazstundihr squatters", "goblin", 2942, ("shazstundihr",)),
    "thieving_arrow": _tribe("Thieving Arrow", "goblin", 2964, ("thievesbane",), tag="H87"),
    "shroomfissure": _tribe("Shroomfissure", "goblin", 2975, ("shroomfissure",)),
    "vazhatun_goblins": _tribe("Vazhatun goblins", "goblin", 4020, ("vazhatun", "dagrinrod_13_15")),
    "spiderwretch": _tribe("Spiderwretch", "goblin", 4071, ("westnest", "eastnest"), tag="H90"),
    "goblins_bypass": _tribe("Goblin's Bypass", "goblin", 4150, ("goblins_bypass",)),
    "railskulker": _tribe("Railskulker", "goblin", 4165, ("skulkers_lair",), tag="H75"),
    "truedagger": _tribe("Truedagger", "goblin", 4144, ("broken_dagger_pass",), tag="H85"),
    "snotfinger": _tribe("Snotfinger", "goblin", 2898, ("snotslair",), tag="H89"),
    "trolltamer": _tribe("Trolltamer", "goblin", 4092, ("greatcavern", "stunad_kradoz")),
    "greedy_grin": _tribe("Greedy Grin", "goblin", 4086, ("goblin_grotto", "diggers_road"), tag="H82"),
    "xazor_goblins": _tribe("Xazor goblins", "goblin", 4219, ("xazor", "ulagom")),
}

# Kingdom -> the EU4 areas its dwarves keep. Arg-Ôrdstun keeps only its hold county, ARG_ORDSTUN_HOLD.
DWARF_REALMS = {
    "k_arg_ordstun": (),
    "k_ovdal_lodhum": ("ovdal_lodhum_area",),
    "k_hehodovar": ("hehos_legacy_area", "dwarovrod_30_32_area"),
    "k_seghdihr": ("seghdihr_area", "dwarovrod_33_35_area", "steamsource_area"),
    "k_verkal_gulan": ("verkal_gulan_area",),
    "k_gor_ozumbrog": ("ozumbrog_area", "dwarovrod_38_41_area"),
}

_BY_EXTRA = {e: t for t in TRIBES.values() for e in t.extra}
_BY_AREA = {a: t for t in TRIBES.values() for a in t.areas}


def tribe_of(eu4_id: int, area: str):
    """The Tribe holding this EU4 province, or None for a dwarven or kobold county."""
    if eu4_id in _BY_EXTRA:
        return _BY_EXTRA[eu4_id]
    tribe = _BY_AREA.get(area)
    return None if tribe is None or eu4_id in tribe.removed else tribe


# People (placeholders): a chief holds from TRIBE_START, their child from the chief's death. Orcs and goblins live
# human lifespans, so these are not the dwarven regions' 860 start and 170-year elders.
TRIBE_START = "980.1.1"
CHIEF_BIRTH = (940, 955)
CHIEF_DEATH = (1000, 1015)
CHILD_BIRTH = (985, 998)  # before CHIEF_DEATH's first year, so an heir is always alive to take over

# Starting values to tune.
POOL = {"orc": {"duchy": 40, "kingdom": 20, "empire": 6}, "goblin": {"duchy": 40, "kingdom": 15, "empire": 4}}
FORM = {"duchy": (3, 250), "kingdom": (15, 500), "empire": (40, 1000)}  # tier -> counties in the realm, prestige
RAISE_PRESTIGE = 200
REFUSAL_OPINION = -50
CHALLENGE_COOLDOWN_YEARS = 5
CULTURE = {"orc": "black_orc", "goblin": "cave_goblin"}
FAITH = {"orc": "old_dookan", "goblin": "goblinic_shamanism"}
