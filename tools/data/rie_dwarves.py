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
    r"has_building_or_higher\s*=\s*elven_settlement_\d+",
    # RiE's crafting lifestyle (Anbennar has none, so the modifier does not exist; like the crafting effect_desc).
    r"monthly_crafting_lifestyle_xp_gain_mult\s*=\s*-?[\d.]+",
)
# (regex of a whole statement or block, its replacement), matched over code (comments blanked, any whitespace).
# RiE's goat pastures need its Iron Hills goat innovation, which Anbennar lacks: the holder gate becomes a dwarf check,
# so nobody else is offered a building whose is_enabled needs a dwarf. The build stops on any other innovation that
# neither Anbennar nor the game defines.
BLOCK_REPLACEMENTS = (
    (r"scope:holder\s*=\s*\{\s*culture\s*=\s*\{\s*has_innovation\s*=\s*innovation_iron_hills_goat_domestication"
     r"\s*\}\s*\}", "scope:holder = { is_dwarvish_culture = yes }"),
)
DROP_BLOCKS = ("province_dynasty_modifier",)
UNGATED_PARAMETERS = ("unlock_full_delving",)
DROP_EFFECT_DESC = r"_artifact_crafting_buff$"
DEPTHS_RENAME = (r"\bdwarven_depths_(\d\d)\b", r"dwarven_hold_\1")

# --- surface-building gates (rie_dwarf_rewrite.gate_surface, after the rewrite; user choice: surface buildings in
# dwarf-held castles and cities on mountain, hill or dwarven-surface terrain) ---
# A block that needs a surface dwarf (aov_rie_surface_dwarf_trigger in is_enabled or can_construct*) gets these in its
# can_construct_potential when absent, so a hold or a non-dwarf is never offered a building it cannot enable.
SURFACE_HOLD_EXCLUSION = "aov_rie_hold_province_trigger = no"
SURFACE_HOLDER_CHECK = "scope:holder = { is_dwarvish_culture = yes }"
# Every block of a SURFACE_BUILDINGS line with no terrain gate of its own (TERRAIN_GATE in none of the line's blocks)
# gets SURFACE_TERRAIN_GATE; in a line also in HOLD_BUILDINGS, a block that does not exclude holds gets
# SURFACE_TERRAIN_GATE_OR_HOLD instead, keeping RiE's hold availability. Lines RiE gates by terrain itself (forest,
# "not hills", "not mountains") keep RiE's gates: adding the hill gate would make them unbuildable or split a line.
SURFACE_TERRAIN_GATE = "aov_rie_hill_terrain_trigger = yes"
SURFACE_TERRAIN_GATE_OR_HOLD = "OR = { aov_rie_hold_province_trigger = yes aov_rie_hill_terrain_trigger = yes }"
TERRAIN_GATE = r"(?<![\w.])(?:aov_rie_(?:mountain|hill)_terrain_trigger|\w+_requirement_terrain|terrain)\s*="
SURFACE_GATE_MARK = "# Anbennar Overhaul: surface building gate"

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
# RiE icon -> our icon, both under gfx/interface/icons/ (RiE's Mining activity icons for the dwarven expedition;
# names follow the game's convention activities/<key>.dds, <key>_header.dds, activity_phases/<phase>.dds,
# activity_option_categories/<category>.dds, activity_types/<option>_icon.dds).
ACTIVITY_ICONS = {
    "activities/activity_mining.dds": "activities/activity_dwarven_expedition.dds",
    "activities/activity_mining_header.dds": "activities/activity_dwarven_expedition_header.dds",
    "activity_phases/mining_phase.dds": "activity_phases/aov_expedition_phase.dds",
    "activity_option_categories/mining_option_surveyors.dds": "activity_option_categories/aov_expedition_crew.dds",
    "activity_option_categories/mining_option_party_size.dds": "activity_option_categories/aov_expedition_type.dds",
    "activity_types/mining_type_prospecting_icon.dds": "activity_types/aov_expedition_mining_icon.dds",
    "activity_types/mining_type_standard_icon.dds": "activity_types/aov_expedition_archaeology_icon.dds",
}
# RiE illustration -> ours, both under gfx/interface/illustrations/ (the activity's header background
# activity_header_backgrounds/<key>.dds and each expedition type's picture activity_types/<option>.dds, which the game
# requires for every option of the special option category).
ACTIVITY_ILLUSTRATIONS = {
    "activity_header_backgrounds/activity_mining.dds": "activity_header_backgrounds/activity_dwarven_expedition.dds",
    "activity_types/mining_type_prospecting.dds": "activity_types/aov_expedition_mining.dds",
    "activity_types/mining_type_standard.dds": "activity_types/aov_expedition_archaeology.dds",
}

# --- localization (tools/build_rie_dwarves.py render_loc) ---
# RiE game concepts Anbennar and the game lack -> the words that replace `[concept|E]` in copied loc (capitalised at
# the start of a sentence). Neither Anbennar nor the game has a dwarf, orc, mineral or mithril concept, so these are
# plain words; Halann is Anbennar's world. The build stops on an undefined concept missing here.
CONCEPT_REPLACEMENTS = {
    "dwarven": "dwarven",
    "dwarves": "dwarves",
    "orc": "orc",
    "orcish": "orcish",
    "goblin": "goblin",
    "middleearth": "Halann",
    "khuzdul": "Dwarven",
    "mineral_resource": "mineral deposit",
    "metal_mithril": "mithril",
    "yavannacharacter": "nature",
}
# Copied RiE lines naming Middle-earth places, peoples or lore -> our text (Anbennar wording: Halann is the world,
# Balgar the Builder the dwarves' patron god in Anbennar's religion loc). The build stops on a copied line matching
# FORBIDDEN_LORE that has no override, and on an override whose key is not copied.
LOC_OVERRIDES = {
    "building_dwarven_ale_house_10_desc": "Tales of mythic alcohols flow from this hold like a river of red ale. "
        "Travelers and adventurers from all realms of Halann make the journey to this hold, hoping for but a drop of "
        "divine liquor.",
    "building_type_dwarven_ale_house_10_desc": "Tales of mythic alcohols flow from this hold like a river of red ale. "
        "Travelers and adventurers from all realms of Halann make the journey to this hold, hoping for but a drop of "
        "divine liquor.",
    "building_dwarven_quarry_09_desc": "Dwarven rune-carvers establish an atelier and carve runes into stones. These "
        "runes are written in the old Dwarven script and reference multiple aspects of Dwarven culture.",
    "building_dwarven_quarry_10_desc": "The very pinnacle of dwarven quarrying achievement, this quarry is now a "
        "sanctuary of masterfully crafted stones and gems, representing the very soul of Dwarven architecture, and "
        "their enduring legacy has been etched into the very bedrock of Halann.",
    "building_dwarven_crafts_10_desc": "A grand hall has been set aside for the exhibition of the finest crafts of "
        "the hold. Tales of the crafts produced at this hold have a near-mythic quality to them. It is said that the "
        "crafts made here are unrivaled in all of Halann.",
    "building_dwarven_toolmaker_guild_10_desc": "The scale of industry within this hold has reached an unfathomable "
        "scale. Within the walls of the factory complex, thousands of inhabitants live, work, and die. Tools are "
        "manufactured at a scale unseen elsewhere in Halann.",
    "building_type_dwarven_forge_01_desc": "Forges take the best materials and tools of the Dwarven people to forge "
        "artifacts to show off to the peoples of Halann.",
    "building_dwarven_hoard_05_desc": "Reaching the zenith of dwarven opulence, this Citadel is a monumental "
        "structure carved deep into the heart of the mountain. Here, the hoard is safeguarded by formidable defenses, "
        "and its treasures beyond measure are a source of awe and envy across Halann.",
    "building_dwarven_armory_10": "Arsenal of Balgar",
    "building_economic_specialization_03_desc": "Our home has been utterly transformed. Our mansion has been filled "
        "with markets that are abuzz with the constant bustle of trade and finance, spurred on by the cleverly "
        "crafted infrastructure centralizing these locations. The wealth of Halann is brought from the depths below "
        "and sculpted into the grandest finery that is the desire of the world. Our great hoard is stacked to the "
        "ceiling, and even our people are achieving such wealth that many have small hoards of their own within "
        "their homes.",
    "building_dwarven_mustering_grounds_06_desc": "Dwarven commanders of this outpost practice the innovative "
        "strategy wholly distinct from their subterranean kin, favoring rapid deployment and decisive strikes over "
        "defensive walls. Dubbed the 'Lightning Strike' by its advocates, it has proven to be a devastatingly "
        "effective form of warfare. Many an orcish army has been routed as they mustered by a surprise attack by "
        "these forces.",
    "building_dwarven_pit_mine_05_desc": "The dig site now encompasses a large plot of land outside the city walls, "
        "merging all the previous excavations into one large open pit. The labourers raise their voices in hymns to "
        "Balgar the Builder as their picks and sieves form a melody of labour.",
    "building_dwarven_pit_mine_08": "A Pockmark on the Face of Halann",
    "building_type_dwarven_forestry_01_desc": "While most Dwarves prefer to shape stone, the realities of a surface "
        "settlement often leave wood as the most readily available source of construction material. In places of "
        "particular abundance, lumber yards are established to extract the maximum amount of utility from nature's "
        "bounty.",
    "building_type_goat_pastures_01_desc": "The dwarves of these hills are among the few dwarves to domesticate "
        "animals. They have tamed the mountain goats native to the area and use them for work and war in equal "
        "measure.",
    "building_type_iron_mines_01_desc": "Iron, a stalwart metal, forms the backbone of Halann's metallurgy. Renowned "
        "for its strength and versatility, iron is the smith's choice for crafting an array of tools, weapons, and "
        "implements essential for everyday life.",
    "building_type_gold_mines_01_desc": "Gold, a timeless symbol of wealth, has been valued across Halann since "
        "ancient times. Unaffected by the passage of years, gold gleams eternally, a testament to its enduring "
        "allure. As a byword for prosperity, it is coveted and treasured by all who seek opulence.",
    "building_type_emerald_mines_01_desc": "Emerald, a lush green gem, evokes the verdant wonders of Halann. "
        "Symbolizing rebirth and growth, emerald is cherished for its rich color, adorning the crowns and jewelry of "
        "those who seek harmony and prosperity.",
    "building_type_mithril_mines_01_desc": "Mithril, the rarest metal in existence, possesses legendary qualities. "
        "Light yet harder than tempered steel, it is prized by dwarven smiths above every other metal, and its "
        "silvery sheen never tarnishes or grows dim.",
}
# Middle-earth places, peoples and lore that must not survive in copied loc.
FORBIDDEN_LORE = (r"Middle-?earth|middleearth|\bArda\b|Iron Hills|Erebor|Moria|Khazad|Durin|Cirth|Yavanna|yavanna|"
                  r"Mahal|Aul[eë]|Longbeard|Firebeard|Broadbeam|Stiffbeard|Ironfist|Blacklock|Stonefoot|Valar|"
                  r"Il[uú]vatar|Morgoth|Sauron|Mordor|Gondor|Rohan|Shire|[Kk]huzdul|Ulkhud|\bD[aá]in\b|Thr[aá]in|"
                  r"Thr[oó]r|Smaug|Balrog|Lonely Mountain|Misty Mountains|Blue Mountains|Ered |Numenor|N[uú]menor|"
                  r"Beleriand|Nogrod|Belegost|Angmar|Tolkien|metal_mithril|mineral_resource")
