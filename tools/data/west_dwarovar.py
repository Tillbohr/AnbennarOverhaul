"""West Dwarovar data: EU4 Anbennar's west_dwarovar_region (without the Krakdhum pocket) and serpents_vale_region
traced into the CK3 Serpentspine block (province 2426) around Anbennar's Khugdihr, under one placeholder empire.

The caves are traced by tools/serpentreach_layout.py (third run, after Serpentreach and Segbandal) and carved by
tools/build_map_graphics.py; Serpent's Vale is drawn as surface land (never carved). Titles, history and people come
from tools/build_west_dwarovar.py. Values marked "as Serpentreach" are imported so the regions look and split alike.

Spec: docs/superpowers/specs/2026-11-03-west-dwarovar-design.md
"""

from data.serpentreach import (  # noqa: F401  (as Serpentreach)
    BARONIES, BARONY_SUFFIXES, CARVE_GROUND_RADIUS, CHARGE_DARK, CHARGE_METAL, COUNTY_JITTER, DUCHY_PATTERNS,
    DUCHY_SHADES, ELDER_BIRTH, ELDER_DEATH, HOLDINGS, MIN_BARONY_PX, MIN_FRAGMENT_PX, MIN_WALL, OPENING_REACH,
    OPENING_WIDTH, PALE_FIELD, PIECE_FLOOR_CLEARANCE, RELIGION, SMOOTH_PASSES, SMOOTH_RADIUS, SON_BIRTH, START,
    TERRACE, TERRACE_STEP, TERRAIN_STYLES, WALL_FADE, WALL_MARGIN, WALL_WIDTH,
)

REGION = "west_dwarovar_region"  # the generated files' header names it
REGIONS = ("west_dwarovar_region", "serpents_vale_region")
SOURCE_PROVINCE = 2426  # Anbennar's impassable "Big Waste", as Serpentreach

# Fit of the EU4 -> CK3 transform (as Serpentreach's): the regions' EU4 bounding box (3122-3473 x 118-641, rows from
# the top) widened by 250/150 px, and that box mapped through the fit on the CK3 map (y = 0 at the south edge). The
# planning probe matched 508 provinces, residual median 16 px, max 48 px.
FIT_BOX = (2870, 0, 3720, 790)
CK3_FIT_BOX = (1380, 1420, 4410, 4096)

# The Krakdhum pocket reaches the rest only through Krakdhum or the Northern Pass and sits under the map-edge fog: left
# out (neither traced nor linked; EU4 contacts with it make no opening).
EXCLUDE_AREAS = ("krakdhum_area", "anvils_horn_area", "dead_end_tunnel_area")
# Serpent's Vale: provinces whose EU4 terrain is none of BARONIES' cave kinds are surface land here (never carved or
# walled), split into SURFACE_BARONIES baronies. Its two dwarven_road provinces (Southern and Eastern Entrance) are
# ordinary cave floors: the Vale's tunnels.
# EU4 provinces that meet only at a corner or a pixel apart (Dwarovrod 12 and Massive Shaft) merge once scaled and
# smoothed: a WALL_MARGIN seam of rock keeps such non-neighbours apart.
SEPARATE_NON_NEIGHBOURS = True
SURFACE_AREAS = ("royal_terrace_area", "common_terrace_area", "assembly_terrace_area", "castle_hill_area")
SURFACE_BARONIES = 3
# CK3 terrain of each Vale county (spec §3).
SURFACE_TERRAIN = {
    "c_royal_terrace": "farmlands", "c_common_terrace": "farmlands", "c_assembly_terrace": "farmlands",
    "c_porgirs_valley": "plains", "c_serpents_vale": "plains", "c_terraceway": "plains", "c_hornriver": "plains",
    "c_lamb_hills": "hills", "c_kingsrock_hill": "hills", "c_northvale": "hills", "c_verkal_hul": "hills",
    "c_kheness_swamp": "wetlands",
}

OPENING_CUT_THROUGH = ()  # no Deepwoods opening, so no Deepwoods Wasteland cut
BARONY_OVERRIDES = {}
OPENING_TARGETS = {}
# EU4 contacts with these regions make no opening: Serpentreach and Segbandal are drawn already (both are reached by
# the CROSSINGS below), the Northern Pass waits for its own iteration, and the East Deepwoods openings were declined
# (spec, Connections).
NO_LINK_REGIONS = ("serpentreach_region", "middle_dwarovar_region", "northern_pass_region", "east_deepwoods_region")
NO_LINK_PAIRS = set()  # EU4 province pairs (either order) whose opening, tunnel or Vale mouth is dropped
# EU4 provinces of the earlier layouts that get a carved tunnel (with LINK_REACH and LINK_CUT_THROUGH): none, the EU4
# adjacencies.csv tunnels are CROSSINGS.
LINK_TARGETS = ()
# EU4 adjacencies.csv tunnels to provinces an earlier layout drew, as crossings (EU4 pairs): a CK3 adjacencies.csv
# row through SOURCE_PROVINCE, so armies step from one floor to the other like over a strait and nothing is carved.
# Gorrod 2 (Jorkad Junction) -> Serpentreach's Gorrod 1; Dwarovrod 24 -> Segbandal's Dwarovrod 25.
CROSSINGS = ((4103, 2981), (2884, 2885))

# EU4 provinces Anbennar already has: EU4 id -> Anbennar county. Not traced; new floors may touch them where EU4 makes
# them neighbours.
EXISTING = {2863: "c_khugdihr", 2896: "c_khugscave", 2897: "c_outerkhugscave", 2864: "c_dwarovrod1"}

# One kingdom per EU4 hold, west to east; the hold's area first (spec §3 kingdom table). k_khugdihr is Anbennar's,
# moved in by history.
KINGDOMS = {
    "k_khugdihr": ("Khugdihr", ["khugdihr_area", "dwarovrod_1_3_area", "fallen_asra_area", "snotslair_area"]),
    "k_haraz_orldhum": ("Haraz Orldhûm", ["orldhum_area", "dwarovrod_4_6_area", "dwarfbreak_area", "dark_depths_area",
                                          "chainlink_mines_area"]),
    "k_mithradhum": ("Mithradhûm", ["mithradhum_area", "dwarovrod_7_9_area", "dwarovrod_10_12_area", "riftway_area"]),
    "k_er_natvir": ("Er-Natvir", ["railyard_area", "railyard_exchange_area", "dagrite_depths_area",
                                  "goblins_bypass_area", "skulkers_lair_area"]),
    "k_verkal_kozenad": ("Verkal Kozenad", ["stunad_kozenad_area", "dwarovrod_15_17_area", "zokkorna_caverns_area",
                                            "travelers_refuge_area", "westnest_area", "eastnest_area"]),
    "k_hul_jorkad": ("Hul-Jorkad", ["jorkad_junction_area", "azmak_area", "dwarovrod_21_24_area"]),
    "k_orlazam_az_dihr": ("Orlazam-az-dihr", ["orlazam_area", "dagrinrod_4_6_area", "dagrinrod_7_9_area",
                                              "broken_dagger_pass_area", "old_dagrinrod_area"]),
    "k_dur_vazhatun": ("Dûr-Vazhatun", ["vazhatun_area", "dagrinrod_13_15_area"]),
    "k_amldihr": ("Amldihr", ["amldihr_area", "royal_terrace_area", "common_terrace_area", "assembly_terrace_area",
                              "castle_hill_area"]),
}
# Province ids (from Segbandal's last + 1) are numbered area by area in this order. Keep it fixed: reordering renumbers
# every West Dwarovar province, so a kingdom change only touches KINGDOMS.
AREA_ORDER = tuple(a for _, areas in KINGDOMS.values() for a in areas)

# --- titles, people and arms (tools/build_west_dwarovar.py) ------------------------------------------------------------
GENERATOR = "tools/build_west_dwarovar.py"  # named in the generated files' header
DATA_FILE = "tools/data/west_dwarovar.py"
EMPIRE = ("e_west_dwarovar", "West Dwarovar")
EMPIRE_CAPITAL = "c_amldihr"
EMPIRE_COLOUR = (60, 40, 80)  # Amldihr's EU4 purple (I01); e_serpentreach is bronze, e_middle_dwarovar blue
# Anbennar's k_khugdihr (de jure e_castanor) moves in by history; its new duchies are defined in PARKING_KINGDOM
# (inside e_west_dwarovar, so every title has a full chain at load) and moved to it on 1.1.1. The parking kingdom ends
# with no de jure land and no holder.
EXISTING_KINGDOMS = ("k_khugdihr",)
PARKING_KINGDOM = "k_aov_west_dwarovar_parking"
PARKING_NAME = "West Dwarovar Unsorted"
PARKING_COLOUR = (90, 90, 90)
KINGDOM_CAPITALS = {
    "k_khugdihr": "c_khugdihr", "k_haraz_orldhum": "c_haraz_orldhum", "k_mithradhum": "c_mithradhum",
    "k_er_natvir": "c_er_natvir", "k_verkal_kozenad": "c_verkal_kozenad", "k_hul_jorkad": "c_hul_jorkad",
    "k_orlazam_az_dihr": "c_orlazam_az_dihr", "k_dur_vazhatun": "c_dur_vazhatun", "k_amldihr": "c_amldihr",
}
# CK3 has none of the holds' EU4 cultures (kronium, platinum, mithril, dagrite, opal, lead, ramsteel, sapphire
# dwarves): silver_dwarvish (EU4's dwarves of the fallen west) stands in until a cultures spec. Khugdihr stays the
# darkscale kobolds' land Anbennar makes it.
KINGDOM_CULTURES = {k: "silver_dwarvish" for k in KINGDOMS}
KINGDOM_CULTURES["k_khugdihr"] = "darkscale"
# Kingdoms left to kobolds: kingdom -> (culture, faith) of their new baronies; no rulers, no characters.
KOBOLD_KINGDOMS = {"k_khugdihr": ("darkscale", "nimrithani")}
# Each new kingdom's hold duchy is named like the kingdom (spec §3); EU4 names the areas otherwise (Orldhûm, The
# Railyard, Stunad Kozenad, Jorkad Junction, Orlazam, Vazhatun).
HOLD_DUCHIES_NAMED_LIKE_KINGDOM = True
CHARACTER_PREFIX = "aov_wd"  # aov_wd_<duchy>_1 (the elder), _2 (his son); aov_wd_emperor_*
DYNASTY_PREFIX = ("aov_wd_dynasty_", "dynn_aov_wd_")
DYNASTY_NAMES = {}
REGION_NAME = "world_west_dwarovar"
# Vale counties (type "surface") by barony position: castle, city, church.
SURFACE_HOLDINGS = ["castle_holding", "city_holding", "church_holding"]
HOLDINGS = {**HOLDINGS, "surface": SURFACE_HOLDINGS}
# kingdom -> (EU4 tag, map colour, arms background: the flag's most common pixel). Map colours are the EU4 countries'
# (spec §3); k_khugdihr keeps Anbennar's map colour and only takes I07's flag. Flags converted once into
# gfx/coat_of_arms/textured_emblems/aov_<kingdom key without k_>.dds (python -I tools/eu4_import.py convert
# gfx/flags/<tag>.tga <dds> --upscale2x --mips).
KINGDOM_ARMS = {
    "k_khugdihr": ("I07", (149, 131, 101), (128, 106, 76)),
    "k_haraz_orldhum": ("I08", (74, 80, 97), (255, 255, 255)),
    "k_mithradhum": ("I05", (81, 231, 213), (181, 181, 189)),
    "k_er_natvir": ("I06", (147, 191, 155), (32, 32, 32)),
    "k_verkal_kozenad": ("I09", (255, 228, 216), (8, 53, 29)),
    "k_hul_jorkad": ("I10", (160, 114, 158), (79, 79, 79)),
    "k_orlazam_az_dihr": ("I04", (74, 111, 121), (178, 169, 154)),
    "k_dur_vazhatun": ("I03", (0, 25, 119), (39, 36, 95)),
    "k_amldihr": ("I01", (60, 40, 80), (53, 66, 109)),
}
# Arms of the other new duchies (as Serpentreach's): one dwarven charge from the area's EU4 lore, generic game and
# Anbennar emblems only. area -> charges, each (colored emblem, (x, y), (scale x, scale y)).
_CENTRE = ((0.5, 0.5), (0.65, 0.65))
DUCHY_CHARGES = {area: ((f"{charge}.dds",) + _CENTRE,) for area, charge in (
    ("dwarovrod_1_3_area", "ce_anb_bridge_two_arch"),  # the Dwarovrod's first stretch
    ("fallen_asra_area", "ce_swords_crossed"),
    ("snotslair_area", "ce_bat"),
    ("dwarovrod_4_6_area", "ce_wheel"),
    ("dwarfbreak_area", "ce_india_small_dagger"),
    ("dark_depths_area", "ce_wyvern"),
    ("chainlink_mines_area", "ce_chains"),
    ("dwarovrod_7_9_area", "ce_anb_bridge_one_arch"),
    ("dwarovrod_10_12_area", "ce_pagan_wheel"),
    ("riftway_area", "ce_india_small_arched_hill"),
    ("railyard_exchange_area", "ce_anb_waterwheel"),
    ("dagrite_depths_area", "ce_anb_crystal"),
    ("goblins_bypass_area", "ce_portcullis"),
    ("skulkers_lair_area", "ce_snake"),
    ("dwarovrod_15_17_area", "ce_anb_bridge_three_arch"),
    ("zokkorna_caverns_area", "ce_wyvern_rising"),
    ("travelers_refuge_area", "ce_anb_lamp"),
    ("westnest_area", "ce_african_snake"),
    ("eastnest_area", "ce_snake_fylfot"),
    ("azmak_area", "ce_anb_skull"),
    ("dwarovrod_21_24_area", "ce_key"),
    ("dagrinrod_4_6_area", "ce_anb_aramari_horseshoe"),
    ("dagrinrod_7_9_area", "ce_bull_horn"),
    ("broken_dagger_pass_area", "ce_india_small_dagger_02"),
    ("old_dagrinrod_area", "ce_ram_horn"),
    ("dagrinrod_13_15_area", "ce_tower"),
    ("royal_terrace_area", "ce_crown"),
    ("common_terrace_area", "ce_sheep"),
    ("assembly_terrace_area", "ce_bell"),
    ("castle_hill_area", "ce_castle"),
)}

# --- look (tools/build_map_graphics.py) ---------------------------------------------------------------------------------
# The caves are carved with Anbennar's Khugdihr as one range (data/map_graphics.py CARVED_RANGES c_khugdihr). Floors by
# EU4 area in Serpentreach's TERRAIN_STYLES: the spider nests of Westnest and Eastnest and Zokkorna's caverns moss;
# every other area "default" (tiled roads and holds, granite caves, grey walls).
AREA_STYLES = {"westnest_area": "mushroom", "eastnest_area": "mushroom", "zokkorna_caverns_area": "mushroom"}
COUNTY_FLOORS = {}
BARONY_FLOORS = {}
# Serpent's Vale is never carved; each county is painted at full weight with the Anbennar material of its CK3 terrain
# (SURFACE_TERRAIN), blended into the paint around over SURFACE_FEATHER px.
SURFACE_MATERIALS = {"farmlands": "farmland_01", "plains": "plains_01", "hills": "hills_01", "wetlands": "wetlands_02"}
SURFACE_FEATHER = 4
