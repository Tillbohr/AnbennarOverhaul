"""Segbandal data: EU4 Anbennar's middle_dwarovar_region completed around Anbennar's own Segbandal (e_middle_dwarovar).

Anbennar's 54 Segbandal provinces stay; the EU4 provinces it lacks are traced into the impassable rock around them
(province 2608) by tools/serpentreach_layout.py, and the region's EU4 areas become duchies (tools/build_segbandal.py).
Values marked "as Serpentreach" are imported so both regions look and split alike.

Spec: docs/superpowers/specs/2026-11-03-segbandal-design.md
"""

from data.serpentreach import (  # noqa: F401  (as Serpentreach)
    BARONIES, BARONY_SUFFIXES, CARVE_GROUND_RADIUS, CHARGE_DARK, CHARGE_METAL, COUNTY_JITTER, DUCHY_PATTERNS,
    DUCHY_SHADES, ELDER_BIRTH, ELDER_DEATH, HOLDINGS, MIN_BARONY_PX, MIN_FRAGMENT_PX, MIN_WALL, OPENING_REACH,
    OPENING_WIDTH, PALE_FIELD, PIECE_FLOOR_CLEARANCE, RELIGION, SMOOTH_PASSES, SMOOTH_RADIUS, SON_BIRTH, START,
    TERRACE, TERRACE_STEP, TERRAIN_STYLES, WALL_FADE, WALL_MARGIN, WALL_WIDTH,
)

REGION = "middle_dwarovar_region"
SOURCE_PROVINCE = 2608  # the impassable Serpentspine rock around Anbennar's Segbandal; only its pixels are re-drawn

# Fit of the EU4 -> CK3 transform (as Serpentreach's): EU4 box (rows from the top), CK3 box (y = 0 at the south edge).
FIT_BOX = (3300, 560, 3950, 860)
CK3_FIT_BOX = (3300, 1250, 5200, 2150)

OPENING_CUT_THROUGH = ()
BARONY_OVERRIDES = {}
OPENING_TARGETS = {}
# EU4 contacts with these regions make no opening: they are not on the CK3 map (West Dwarovar) or not linked
# (Serpentreach, as decided for Serpentreach).
NO_LINK_REGIONS = ("west_dwarovar_region", "serpentreach_region")

# EU4 provinces Anbennar already has, by name: EU4 id -> Anbennar county. They are not traced; new provinces may touch
# their CK3 provinces where EU4 makes them neighbours.
EXISTING = {
    2889: "c_dwarovrod30", 2890: "c_dwarovrod31", 2891: "c_dwarovrod32", 4027: "c_dwarovrod33",
    2892: "c_dwarovrod34", 2893: "c_dwarovrod35", 2894: "c_dwarovrod36", 2895: "c_dwarovrod37",
    4231: "c_dwarovrod38", 4091: "c_dwarovrod39", 4111: "c_dwarovrod40", 4112: "c_dwarovrod41",
    4113: "c_dwarovrod42", 4114: "c_dwarovrod43", 4090: "c_dwarovrod44",
    4082: "c_seghrod", 4078: "c_hehodovar", 4124: "c_seghdihr", 2914: "c_verkal_gulan", 4218: "c_gor_ozumbrog",
}

# EU4 area -> (duchy, kingdom, reused: an Anbennar duchy). West to east; new province ids follow this order, so keep it.
AREA_DUCHIES = {
    "vazumbrog_area": ("d_vazumbrog", "k_gor_vazumbrog", False),
    "dwarovrod_27_29_area": ("d_dwarovrod_27_29", "k_gor_vazumbrog", False),
    "misty_cave_trail_area": ("d_misty_cave_trail", "k_gor_vazumbrog", False),
    "hehos_legacy_area": ("d_hehodovar", "k_hehodovar", True),
    "dwarovrod_30_32_area": ("d_hehorod", "k_hehodovar", True),
    "deep_ones_lair_area": ("d_deep_ones_lair", "k_hehodovar", False),
    "diggers_road_area": ("d_diggers_road", "k_hehodovar", False),
    "seghdihr_area": ("d_seghdihr", "k_seghdihr", True),
    "dwarovrod_33_35_area": ("d_dwarovrod_33_35", "k_seghdihr", False),
    "steamsource_area": ("d_steamsource", "k_seghdihr", False),
    "stunad_kradoz_area": ("d_stunad_kradoz", "k_seghdihr", False),
    "goblin_grotto_area": ("d_goblin_grotto", "k_seghdihr", False),
    "verkal_gulan_area": ("d_verkal_gulan", "k_verkal_gulan", True),
    "greatcavern_area": ("d_greatcavern", "k_verkal_gulan", False),
    "xazor_area": ("d_xazor", "k_verkal_gulan", False),
    "dwarovrod_38_41_area": ("d_xazorod", "k_gor_ozumbrog", True),
    "ozumbrog_area": ("d_gor_ozumbrog", "k_gor_ozumbrog", True),
    "ulagom_area": ("d_ulagom", "k_gor_ozumbrog", False),
}
AREA_ORDER = tuple(AREA_DUCHIES)
_KINGDOM_NAMES = {"k_gor_vazumbrog": "Gor Vazumbrog", "k_hehodovar": "Hehodovar", "k_seghdihr": "Seghdihr",
                  "k_verkal_gulan": "Verkal Gulan", "k_gor_ozumbrog": "Gor Ozumbrog"}
KINGDOMS = {k: (name, [a for a, (_, kk, _) in AREA_DUCHIES.items() if kk == k]) for k, name in _KINGDOM_NAMES.items()}
