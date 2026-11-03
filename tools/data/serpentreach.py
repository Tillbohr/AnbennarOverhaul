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
SMOOTH_RADIUS = 3  # majority filter over the traced EU4 labels: removes the ~3.5 px stair steps
SMOOTH_PASSES = 3
OPENING_WIDTH = 10  # px width of a corridor to the surface (a gate at scale 1.6 is ~12.5 px wide)
OPENING_REACH = 160  # px: farthest a corridor may run from the floor to its target
# Impassable provinces an opening corridor may also cut through (their pixels on the corridor become the barony's):
# Deepwoods Wasteland, between Verkal Skomdihr and the Deepwoods.
OPENING_CUT_THROUGH = (1782,)
PIECE_FLOOR_CLEARANCE = 3  # px: a gate's mountain pieces closer than this to the floor are dropped
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
WALL_WIDTH = 4  # px of smoothstep slope from the floor up to the rock
WALL_FADE = 8
# Terrain by region, from EU4 Anbennar lore. A style gives the floor material per county type and the wall material
# blended in over WALL_WIDTH; styles other than "default" list only what they change. Material ids are Anbennar's or
# Godherja's: tools/build_map_graphics.py appends every used id Anbennar lacks from Godherja's materials.settings.
TERRAIN_STYLES = {
    # Tiled roads and holds, grey granite caves, grey layered cliffs.
    "default": {"dwarven_road": "mayik_tiles_01", "dwarven_hold": "mayik_tiles_01",
                "dwarven_hold_surface": "mayik_tiles_01", "cavern": "mountain_02_d_granitegrey",
                "wall": "rock_13_05_10"},
    # Gor Bûrad, "the Basalt Hold" inside an active volcano: basalt caves and dark cracked walls.
    "volcanic": {"cavern": "hardened_lava", "wall": "rock_14_05_05"},
    # Shazstundihr, the Marble Gate (marble quarries, mausoleums; the Marble Galleries): pale cracked roads,
    # patterned marble tiles in the hold, white rock.
    "marble": {"dwarven_road": "desert_cracked_white", "dwarven_hold": "mayik_tiles_02",
               "dwarven_hold_surface": "mayik_tiles_02", "cavern": "rock_white", "wall": "mountains_white"},
    # Arg-Ôrdstun's diamond mines: kimberlite shafts of old solidified magma.
    "diamond": {"cavern": "mountain_02_dark"},
    # Ovdal Lodhum's garnets (Garnetheart).
    "garnet": {"cavern": "red_canyon_surface_stone_2"},
    # Shroomfissure's mushroom caverns.
    "mushroom": {"cavern": "moss_ground_01"},
}
AREA_STYLES = {  # EU4 area -> style; unlisted areas use "default"
    "gor_burad_area": "volcanic", "buradforge_area": "volcanic", "zarn_area": "volcanic",
    "argrod_14_16_area": "volcanic", "shazstundihr_area": "marble", "south_altar_area": "marble",
    "arg_ordstun_area": "diamond", "ovdal_lodhum_area": "garnet", "shroomfissure_area": "mushroom",
}
COUNTY_FLOORS = {"c_lavawater": "lava", "c_molten_core": "lava", "c_gor_burad": "hardened_lava_b"}
# (county, barony index; 0 is the capital) -> floor. b_gor_burad_2 is the barony facing Lavawater and Molten Core.
BARONY_FLOORS = {("c_gor_burad", 1): "lava"}

# People (placeholders): an elder holds from 860.1.1, his son from the elder's death.
ELDER_BIRTH = (830, 845)
ELDER_DEATH = (1000, 1010)
SON_BIRTH = (975, 990)
START = "860.1.1"
