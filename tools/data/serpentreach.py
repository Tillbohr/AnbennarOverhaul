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
# Range rock (tools/range_rock.py): each range's rock is cut out of 2426 as its own impassable province, small enough
# for the game to fill with the realm's map colour, as Segbandal's 2608. (name in definition.csv, index in `layouts`).
RANGE_ROCKS = (("Serpentreach Wasteland", 0), ("West Dwarovar Wasteland", 2))
ROCK_SOURCE = SOURCE_PROVINCE
ROCK_AVOID = (2608,)  # rock nearer Segbandal's stays 2426: West Dwarovar's must not run along Segbandal's northern rim
ROCK_MIN_HEIGHT = 48  # 0-255: the range's foot; the Big Waste's plain is ~21
ROCK_ALWAYS = 16  # px around a floor that are rock at any height (the tunnels crossing the plain)
ROCK_REACH = 450  # px from a floor; wide enough to end on the range's own foot
ROCK_MAX_Y = 3496  # the surround fog's edge (SURROUND_BOX, mask row 300)
ROCK_SLIVER = 10  # waste narrower than 2 * this against a range joins it
ROCK_ISLAND_GAP = 30  # px of land a ridge may be cut off by and still join (the ridge around Dwaroval)
PIECE_FLOOR_CLEARANCE = 3  # px: a gate's mountain pieces closer than this to the floor are dropped
MIN_BARONY_PX = 60  # a county needs at least this many floor px per barony
MIN_FRAGMENT_PX = 0  # floor pieces cut off from their county's main piece are dropped (reported)

BARONIES = {"dwarven_hold": 4, "dwarven_hold_surface": 4, "cavern": 2, "dwarven_road": 1}
BARONY_OVERRIDES = {}  # county key -> barony count
OPENING_TARGETS = {}  # (EU4 Serpentreach province, EU4 neighbour) -> CK3 province id
BARONY_SUFFIXES = ("Halls", "Deeps", "Vaults")  # names of a county's 2nd, 3rd and 4th baronies

# Province ids (from 6944) are numbered area by area in this order. Keep it fixed: reordering renumbers every
# Serpentreach province (provinces.png, locators, history), so a kingdom change only touches KINGDOMS.
AREA_ORDER = ("orlghelovar_area", "south_altar_area", "north_altar_area", "argrod_origin_area", "arg_ordstun_area",
              "shazstundihr_area", "kings_caverns_area", "argrod_6_8_area", "stunad_skomdihr_area", "thievesbane_area",
              "ovdal_lodhum_area", "argrod_9_11_area", "shroomfissure_area", "still_caverns_area",
              "argrod_junction_area", "zarn_area", "argrod_14_16_area", "buradforge_area", "gor_burad_area")

# One kingdom per dwarven hold, west to east: EU4 area keys, the hold's area first (each kingdom is contiguous).
KINGDOMS = {
    "k_orlghelovar": ("Orlghelovar", ["orlghelovar_area", "argrod_origin_area", "north_altar_area"]),
    "k_shazstundihr": ("Shazstundihr", ["shazstundihr_area", "south_altar_area"]),
    "k_arg_ordstun": ("Arg-Ôrdstun", ["arg_ordstun_area", "kings_caverns_area"]),
    "k_verkal_skomdihr": ("Verkal Skomdihr", ["stunad_skomdihr_area", "argrod_6_8_area", "thievesbane_area"]),
    "k_ovdal_lodhum": ("Ovdal Lodhum", ["ovdal_lodhum_area", "argrod_9_11_area", "shroomfissure_area",
                                        "still_caverns_area"]),
    "k_gor_burad": ("Gor Bûrad", ["gor_burad_area", "buradforge_area", "zarn_area", "argrod_14_16_area",
                                  "argrod_junction_area"]),
}
EMPIRE = ("e_serpentreach", "Serpentreach")
KINGDOM_CAPITALS = {"k_orlghelovar": "c_orlghelovar", "k_shazstundihr": "c_shazstundihr",
                    "k_arg_ordstun": "c_arg_ordstun", "k_verkal_skomdihr": "c_verkal_skomdihr",
                    "k_ovdal_lodhum": "c_ovdal_lodhum", "k_gor_burad": "c_gor_burad"}
EMPIRE_CAPITAL = "c_arg_ordstun"

# Map colours and arms. Each kingdom takes its EU4 hold's country colour (common/countries/<name>.txt); its duchies
# are lighter and darker shades of it and its counties vary slightly around their duchy's. Arg-Ôrdstun's EU4 grey
# (200 200 200) is darkened to steel so it does not merge with Shazstundihr's off-white next to it.
EMPIRE_COLOUR = (150, 105, 50)  # dwarven bronze; e_middle_dwarovar is blue (36 96 143)
DUCHY_SHADES = (0.0, -0.12, 0.12, -0.22, 0.22)  # HLS lightness offsets by duchy position; mirrored when out of range
COUNTY_JITTER = 0.05  # +/- lightness around the duchy's colour
# kingdom -> (EU4 tag, map colour, arms background colour: the flag's most common pixel). The flag, gfx/flags/<tag>.tga,
# was converted once into gfx/coat_of_arms/textured_emblems/aov_<kingdom key without k_>.dds with
# `python -I tools/eu4_import.py convert gfx/flags/<tag>.tga <dds> --upscale2x --mips`; the kingdom, its hold's duchy
# and its hold county carry it.
KINGDOM_ARMS = {
    "k_orlghelovar": ("I12", (0, 71, 171), (18, 34, 108)),
    "k_shazstundihr": ("I11", (241, 242, 227), (96, 96, 96)),
    "k_arg_ordstun": ("H76", (120, 124, 132), (43, 48, 57)),
    "k_verkal_skomdihr": ("I13", (55, 144, 90), (111, 111, 102)),
    "k_ovdal_lodhum": ("H77", (247, 179, 215), (48, 52, 61)),
    "k_gor_burad": ("I16", (240, 72, 72), (162, 163, 162)),
}
# Arms of the other duchies (EU4 has no country there): a dwarven charge on a field of the duchy's map colour, metal on
# dark fields and black on pale ones. Generic emblems only, none of another hold's own arms (ce_anb_seghdihr, ...).
# area -> charges, each (colored emblem, (x, y), (scale x, scale y)).
_CENTRE = ((0.5, 0.5), (0.65, 0.65))
DUCHY_CHARGES = {
    "argrod_origin_area": (("ce_mjolnir.dds",) + _CENTRE,),  # where the Argrod, the dwarven road, begins
    "north_altar_area": (("ce_zoroastrian_fire_altar.dds",) + _CENTRE,),
    "south_altar_area": (("ce_zoroastrian_fire_altar.dds",) + _CENTRE,),
    "kings_caverns_area": (("ce_crown.dds",) + _CENTRE,),
    "argrod_6_8_area": (("ce_axe.dds",) + _CENTRE,),
    "thievesbane_area": (("ce_keys_crossed.dds",) + _CENTRE,),
    "argrod_9_11_area": (("ce_anb_lamp.dds",) + _CENTRE,),
    "shroomfissure_area": (("ce_flaming_jewel.dds",) + _CENTRE,),  # the glow of its mushroom caverns
    "still_caverns_area": (("ce_anb_gem.dds",) + _CENTRE,),
    "argrod_junction_area": (("ce_anb_cog.dds",) + _CENTRE,),
    "zarn_area": (("ce_fire.dds",) + _CENTRE,),
    "argrod_14_16_area": (("ce_anb_redgarhavn_runestone.dds",) + _CENTRE,),  # a road's waymark
    # the forge: Anbennar's d_silverforge layout, a flame over an anvil
    "buradforge_area": (("ce_fire.dds", (0.5, 0.3), (0.3, 0.4)), ("ce_anb_anvil.dds", (0.5, 0.62), (0.7, 0.7))),
}
# Field divisions, picked per duchy by a hash of its key; color2 is a darker shade of the field.
DUCHY_PATTERNS = ("pattern_solid.dds", "pattern_chief.dds", "pattern_horizontal_split_01.dds",
                  "pattern_stepped_pyramid.dds", "pattern_chevron_01.dds")
CHARGE_METAL = ((212, 175, 55), (225, 225, 225))  # on dark fields: charge gold, its accents silver
CHARGE_DARK = ((35, 35, 40), (212, 175, 55))  # on pale fields (HLS lightness above PALE_FIELD)
PALE_FIELD = 0.65

# Each kingdom's counties, characters and dynasties take its hold's EU4 culture (common/cultures/anb_cultures.txt,
# primary = the hold's tag). Spec: docs/superpowers/specs/2026-11-03-serpentreach-dwarf-cultures-draft.md
KINGDOM_CULTURES = {
    "k_orlghelovar": "cobalt_dwarvish", "k_shazstundihr": "marble_dwarvish", "k_arg_ordstun": "diamond_dwarvish",
    "k_verkal_skomdihr": "flint_dwarvish", "k_ovdal_lodhum": "garnet_dwarvish", "k_gor_burad": "basalt_dwarvish",
}
# Duchy -> its dynasty's name, shown without the "az" prefix the other duchies' dynasties carry. The holds' ruling
# lines are EU4's 1444 rulers (H76 Ardeginn XXII Whiteforged; H77 Dwalra Garnetpick, as Gerin Orcrend is a human who
# marries in later); the rest come from EU4's culture dynasty_names (diamond, garnet and marble dwarves).
DYNASTY_NAMES = {
    "d_arg_ordstun": "Whiteforged", "d_kings_caverns": "Stormheart", "d_ovdal_lodhum": "Garnetpick",
    "d_still_caverns": "Slatecutter", "d_shazstundihr": "Whitebeard", "d_south_altar": "Brightbeard",
}
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

CHARACTER_PREFIX = "aov_sr"  # character ids: aov_sr_<duchy>_1 (the elder), _2 (his son); aov_sr_emperor_*

# Provinces Anbennar already has (none here; see tools/data/segbandal.py) and regions whose contacts make no opening.
EXISTING = {}
NO_LINK_REGIONS = ()
