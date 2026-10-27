"""Data for tools/build_rie_courts.py: Realms in Exile's character-window backgrounds and royal court scenes for the
dwarves, wood elves and moon elves (user choice)."""

# Terrains of a dwarven court: dwarves get RiE's dwarf backgrounds and court only while their capital is on one of them
# (user choice: holds, dwarven roads and caverns).
DWARF_TERRAINS = ("dwarven_hold", "dwarven_hold_surface", "dwarven_road", "cavern")

TIERS = {
    "above_kingdom": "highest_held_title_tier > tier_kingdom",
    "kingdom": "highest_held_title_tier = tier_kingdom",
    "kingdom_or_above": "highest_held_title_tier >= tier_kingdom",
    "duchy": "highest_held_title_tier = tier_duchy",
    "below_duchy": "highest_held_title_tier < tier_duchy",
    "below_kingdom": "highest_held_title_tier < tier_kingdom",
}

# Court groups: who (character scope: the condition is tested on the character, else a non-ruling spouse, the
# betrothed or the host, as in RiE and vanilla), the character-window backgrounds by realm level (tier, texture under
# gfx/interface/illustrations, portrait environment; first match wins), and the royal court: RiE's scene culture set,
# its scene files and its grandeur entry (by RiE culture name).
COURTS = {
    "dwarf": {
        "label": "RiE dwarven court (Durin's Folk)",
        "condition": ["culture = { has_clothing_gfx = aov_dwarf_clothing_gfx }",
                      "capital_province = { OR = { " + " ".join(f"terrain = {t}" for t in DWARF_TERRAINS) + " } }"],
        "backgrounds": [
            ("above_kingdom", "character_view/throneroom_dwarf_highest.dds", "environment_throneroom_dwarf_highest"),
            ("kingdom", "character_view/throneroom_dwarf_high.dds", "environment_throneroom_dwarf_high"),
            ("duchy", "character_view/throneroom_dwarf_mid.dds", "environment_throneroom_dwarf_mid"),
            ("below_duchy", "character_view/throneroom_dwarf_low.dds", "environment_throneroom_dwarf_low"),
        ],
        "scene_culture": "dwarven",
        "scenes": ["scene_settings_Dwarven_1_g3.txt"],
    },
    "wood_elf": {
        "label": "RiE Lasgalendrim court (Greenwood)",
        "condition": ["culture = { has_clothing_gfx = aov_lasgalendrim_clothing_gfx }"],
        # Thranduil's halls for kings and above; counts and dukes (and below) get RiE's forest hall with mountain
        # windows (its Forest Avari throneroom, user choice), with the lighting RiE pairs it with.
        "backgrounds": [
            ("kingdom_or_above", "event_scenes/lotr_throneroom_thranduils_halls.dds", "environment_event_study"),
            ("below_kingdom", "character_view/throneroom_forest_avari_ai.dds", "environment_event_forest_pine"),
        ],
        "scene_culture": "moriquendi",
        "scenes": ["scene_settings_rie_elf_1.txt"],
    },
    "moon_elf": {
        "label": "RiE Falathrim court (Lindon; RiE's Noldor thronerooms)",
        "condition": ["culture = { has_clothing_gfx = aov_noldor_clothing_gfx }"],
        "backgrounds": [
            ("kingdom_or_above", "character_view/throneroom_noldor_high.dds", "environment_noldor_king"),
            ("duchy", "character_view/throneroom_noldor_mid.dds", "environment_noldor_duke"),
            ("below_duchy", "character_view/throneroom_noldor_low.dds", "environment_noldor_count"),
        ],
        "scene_culture": "noldor",
        "scenes": [f"scene_settings_ek_yespest_{layout}_g{level}.txt" for layout in (1, 2) for level in (1, 2, 3)],
    },
}

# Liches (Anbennar's lich trait) come before the race courts (user choice): a landed Lich holds court in Godherja's
# lichdom hall (imported once to gfx/interface/illustrations/aov_lich/, not copied by the generator; the lighting
# Godherja pairs it with), shown like the courts above also for a non-ruling spouse, the betrothed or the host; an
# unlanded Lich (courtier, prisoner's guest, adventurer) stands in RiE's Nazgul crypt. First match wins.
# (name, character-scope condition, view fallbacks, texture, environment)
LICH_BACKGROUNDS = [
    ("unlanded", ["has_trait = lich", "is_landed = no"], False,
     "event_scenes/lotr_throneroom_evil.dds", "environment_evil_throneroom"),
    ("landed", ["has_trait = lich", "is_landed = yes"], True,
     "aov_lich/lichdom_court.dds", "environment_cw_india_main"),
]

# Anbennar's character_view_bg entry our backgrounds go in front of (its first throneroom; everything above it covers
# death, prison, activities, travel and camps, which should keep winning).
BACKGROUND_ANCHOR = "character_view/fp1_throneroom_nontribal.dds"
