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
# EU4 contacts with these regions make no opening: Serpentreach and Segbandal are drawn already (Segbandal is reached
# by the Dwarovrod tunnel below), the Northern Pass waits for its own iteration, and the East Deepwoods openings were
# declined (spec, Connections).
NO_LINK_REGIONS = ("serpentreach_region", "middle_dwarovar_region", "northern_pass_region", "east_deepwoods_region")
NO_LINK_PAIRS = set()  # EU4 province pairs (either order) whose opening, tunnel or Vale mouth is dropped
# EU4 adjacencies.csv tunnels to provinces an earlier layout drew (Dwarovrod 24 -> Segbandal's Dwarovrod 25, ~170 px
# on the CK3 map): at most LINK_REACH px, through 2426 and Segbandal's rock.
LINK_REACH = 220
LINK_CUT_THROUGH = (2608,)
# EU4 provinces of the earlier layouts that get a tunnel. EU4 also tunnels Gorrod 2 (Jorkad Junction) to Serpentreach's
# Gorrod 1 (2981); the spec leaves Serpentreach unconnected, so that one is not listed.
LINK_TARGETS = (2885,)

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
