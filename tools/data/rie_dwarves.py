"""Data for tools/build_rie_dwarves.py: Realms in Exile's dwarf buildings, ore deposits and the Dwarven Expedition,
laid over Anbennar's dwarven holds (spec docs/superpowers/specs/2026-10-17-rie-dwarves-design.md).

Paths are relative to RiE's mod folder; edit the data, then rerun the generator."""

RIE_BUILDING_FILES = (
    "common/buildings/lotr_buildings/lotr_dwarven_buildings.txt",
    "common/buildings/lotr_buildings/lotr_mines_buildings.txt",
)
DEPTHS_FILE = "common/buildings/lotr_buildings/lotr_dwarven_settlement_holdings.txt"
ORE_FILE = "common/modifiers/lotr_modifiers/lotr_ore_modifiers.txt"

# RiE's 15 ore deposits, in the order of its ore modifier file.
ORES = (
    "mithril", "gold", "silver", "iron", "copper", "tin", "lead", "diamond",
    "ruby", "sapphire", "emerald", "amethyst", "onyx", "peridot", "quartz",
)
ORE_WEIGHTS = {
    "iron": 40, "copper": 40, "tin": 40, "lead": 40,
    "quartz": 12, "onyx": 12, "peridot": 12, "amethyst": 12,
    "silver": 8, "gold": 6,
    "sapphire": 4, "emerald": 4, "ruby": 4,
    "diamond": 3, "mithril": 1,
}
# barony -> ore: deposits present at game start.
START_DEPOSITS = {
    "b_hul_az_amekh": "ruby",
    "b_gulandhum": "gold",
    "b_anvilwright": "silver",
}

DWARVEN_TERRAINS = ("dwarven_hold", "dwarven_hold_surface", "cavern", "dwarven_road")
MOUNTAIN_TERRAINS = ("mountains", "desert_mountains") + DWARVEN_TERRAINS
HILL_TERRAINS = MOUNTAIN_TERRAINS + ("hills",)

# --- rewrite rules (tools/rie_dwarf_rewrite.py) ---
TOKEN_RENAMES = {
    "is_dwarf": "is_dwarvish_culture",
    "lotr_subterranean_buildings": "is_dwarvish_culture",
    "lotr_dwarven_underground_buildings_requirement_terrain": "aov_rie_hold_province_trigger",
    "lotr_dwarven_mountain_buildings_requirement_terrain": "aov_rie_mountain_terrain_trigger",
    "lotr_dwarven_hill_buildings_requirement_terrain": "aov_rie_hill_terrain_trigger",
    "lotr_dwarven_is_surface_dwarf": "aov_rie_surface_dwarf_trigger",
    "lotr_dwarven_is_mountain_dwarf": "aov_rie_dwarven_holder_trigger",
}
# Regexes of whole statements to remove (a block left empty goes with them).
DROP_STATEMENTS = (
    r"is_orc\s*=\s*yes",
    r"has_dynasty_perk\s*=\s*lotr_\w+",
    r"has_innovation\s*=\s*innovation_iron_hills_goat_domestication",
    r"has_building_or_higher\s*=\s*elven_settlement_\d+",
    # RiE's crafting lifestyle (Anbennar has none, so the modifier does not exist; like the crafting effect_desc).
    r"monthly_crafting_lifestyle_xp_gain_mult\s*=\s*-?[\d.]+",
)
DROP_BLOCKS = ("province_dynasty_modifier",)
UNGATED_PARAMETERS = ("unlock_full_delving",)
DROP_EFFECT_DESC = r"_artifact_crafting_buff$"
DEPTHS_RENAME = (r"\bdwarven_depths_(\d\d)\b", r"dwarven_hold_\1")

# --- holding lists (level-01 keys) ---
MINE_BUILDINGS = [f"{ore}_mines_01" for ore in ORES]

# RiE `dwarven_holding` buildings: mines and dwarven buildings, without orc, oath and brewery buildings and
# without dwarven_depths_01 (Anbennar's hold levels replace it).
HOLD_BUILDINGS = MINE_BUILDINGS + [
    "dwarven_quarry_01", "dwarven_fungal_farm_01", "dwarven_terrace_farm_01", "dwarven_vaults_01",
    "dwarven_ale_house_01", "dwarven_toolmaker_guild_01", "dwarven_forge_01", "dwarven_crafts_01",
    "dwarven_outpost_01", "dwarven_roads_01", "dwarven_armory_01", "dwarven_hi_barracks_01",
    "dwarven_pike_barracks_01", "dwarven_archer_barracks_01", "dwarven_skirmisher_barracks_01",
    "dwarven_siege_workshop_01", "dwarven_hoard_01", "dwarven_bank_economic_01",
    "dwarven_kings_armory_military_01", "dwarven_grand_library_01",
]
# RiE castle_holding "#Dwarven buildings" block.
SURFACE_BUILDINGS = [
    "dwarven_terrace_farm_01", "dwarven_outpost_01", "dwarven_surface_farm_01", "dwarven_market_01",
    "dwarven_surface_forge_01", "dwarven_surface_workshop_01", "dwarven_mustering_grounds_01",
    "dwarven_pit_mine_01", "dwarven_tavern_01", "dwarven_forestry_01", "goat_pastures_01",
]

# key -> (picture, portrait environment, ambience), spec Section 4.
BACKGROUNDS = {
    "aov_expedition_cave": (
        "gfx/interface/illustrations/activity_backgrounds/lotr_cave_interior.dds",
        "environment_event_alley", "event:/SFX/Events/Backgrounds/city_alley_night"),
    "aov_expedition_halls": (
        "gfx/interface/illustrations/event_scenes/lotr_halls.dds",
        "environment_event_alley", "event:/SFX/Events/Backgrounds/city_alley_night"),
    "aov_expedition_gate": (
        "gfx/interface/illustrations/event_scenes/lotr_dwarven_gate.dds",
        "environment_travel_mountain_settlement", "event:/SFX/Events/Backgrounds/mountains_day"),
}
# RiE path -> our path; Task 5 fills it.
ACTIVITY_ICONS = {}
