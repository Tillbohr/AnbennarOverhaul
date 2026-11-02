"""Serpentreach data: EU4 Anbennar's serpentreach_region carved into the CK3 Serpentspine block (province 2426).

Spec: docs/superpowers/specs/2026-11-02-serpentreach-design.md
"""

REGION = "serpentreach_region"
SOURCE_PROVINCE = 2426  # Anbennar's impassable "Big Waste"; only its pixels are re-drawn

# Fit of the EU4 -> CK3 transform: matched provinces (same id, same first five letters of the name) whose EU4
# centroid lies in FIT_BOX (x0, y0, x1, y1, EU4 image rows from the top) and CK3 centroid in CK3_FIT_BOX (map
# coordinates, y = 0 at the south edge).
FIT_BOX = (2950, 480, 3550, 760)
CK3_FIT_BOX = (1900, 1496, 3800, 2396)

WALL_MARGIN = 4  # px of rock kept between the floor and any other province
OPENING_WIDTH = 6  # px width of a corridor to the surface
MIN_BARONY_PX = 60  # a county needs at least this many floor px per barony
MIN_FRAGMENT_PX = 0  # floor pieces cut off from their county's main piece are dropped (reported)

BARONIES = {"dwarven_hold": 4, "dwarven_hold_surface": 4, "cavern": 2, "dwarven_road": 1}
BARONY_OVERRIDES = {}  # county key -> barony count
OPENING_TARGETS = {}  # (EU4 Serpentreach province, EU4 neighbour) -> CK3 province id
BARONY_SUFFIXES = ("Halls", "Deeps", "Vaults")  # names of a county's 2nd, 3rd and 4th baronies

# EU4 area keys of each kingdom, west to east.
KINGDOMS = {
    "k_arg_ordstun": ("Arg-Ôrdstun", ["orlghelovar_area", "south_altar_area", "north_altar_area",
                                       "argrod_origin_area", "arg_ordstun_area", "shazstundihr_area",
                                       "kings_caverns_area"]),
    "k_ovdal_lodhum": ("Ovdal Lodhum", ["argrod_6_8_area", "stunad_skomdihr_area", "thievesbane_area",
                                        "ovdal_lodhum_area", "argrod_9_11_area", "shroomfissure_area",
                                        "still_caverns_area"]),
    "k_gor_burad": ("Gor Bûrad", ["argrod_junction_area", "zarn_area", "argrod_14_16_area", "buradforge_area",
                                  "gor_burad_area"]),
}
EMPIRE = ("e_serpentreach", "Serpentreach")
KINGDOM_CAPITALS = {"k_arg_ordstun": "c_arg_ordstun", "k_ovdal_lodhum": "c_ovdal_lodhum",
                    "k_gor_burad": "c_gor_burad"}
EMPIRE_CAPITAL = "c_arg_ordstun"

CULTURE = "stone_dwarvish"
RELIGION = "ancestor_worship"

# Holdings by barony position (capital first) for each EU4 terrain type; None leaves the barony empty.
HOLDINGS = {
    "dwarven_hold": ["castle_holding", "city_holding", "church_holding", None],
    "dwarven_hold_surface": ["castle_holding", "city_holding", "church_holding", None],
    "cavern": ["castle_holding", None],
    "dwarven_road": ["castle_holding"],
}

# Carving (tools/build_map_graphics.py): heights in 16-bit heightmap units.
CARVE_GROUND_RADIUS = 40  # px around the floor sampled for the ground (median of non-2426 land)
TERRACE_STEP = 600
TERRACE = {"dwarven_road": 0, "cavern": -1, "dwarven_hold": 1, "dwarven_hold_surface": 1}  # x TERRACE_STEP
MIN_WALL = 6000  # the rim stands at least this far above the floor
WALL_WIDTH = 3
WALL_FADE = 8
FLOOR_MATERIAL = "steppe_rocks"
WALL_MATERIAL = "mountain_02_c"

# People (placeholders): an elder holds from 860.1.1, his son from the elder's death.
ELDER_BIRTH = (830, 845)
ELDER_DEATH = (1000, 1010)
SON_BIRTH = (975, 990)
START = "860.1.1"
