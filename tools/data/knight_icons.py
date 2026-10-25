"""Data for tools/build_knight_icons.py: the race knight badges (docs/systems/knight-icons.md).

Each race shows its EU4 Anbennar tech group icon, without the gear, instead of the knight badge for knights of its
rulers. RACES order is the custom loc order (first match wins). To add a race (goblins, orcs):
  1. add a row: key, name, EU4 icon number in gfx/interface/tech_group_strip.dds (= position of the tech group in
     common/technology.txt groups; 32 Orcish, 35 Goblin), its tech group key, the culture check (trigger, value) and
     the gear mask: {row: last x to clear}, clearing x 0..last in that row (the gear sits top left, behind the art);
  2. python -I tools/build_knight_icons.py --import <key>   (cuts the icon out of EU4 Anbennar; check it);
  3. python -I tools/build_knight_icons.py                  (custom loc, trigger, loc and interface overrides).
"""

STRIP = "gfx/interface/tech_group_strip.dds"  # in EU4 Anbennar
SOURCE_SIZE = 38  # each icon in the strip is 38 x 38
ICON_SIZE = 50  # vanilla gfx/interface/icons/icon_knight_small.dds
ICON_DIR = "gfx/interface/icons/aov_knight_icons"
VANILLA_ICON = "gfx/interface/icons/icon_knight_small.dds"

# key, name, EU4 icon number (1-based), EU4 tech group, culture check, gear mask {row: last x cleared}
RACES = [
    ("moon_elven", "Moon elves", 20, "tech_elven", ('aov_moon_elven_lineage_trigger', 'yes'),
     {0: 25, 1: 25, 2: 25, 3: 21, 4: 21, 5: 21, 6: 22, 7: 17, 8: 15, 9: 14,
      10: 13, 11: 12, 12: 12, 13: 11, 14: 10, 15: 9, 16: 9, 17: 9, 18: 9, 19: 9,
      20: 9, 21: 9, 22: 9, 23: 9, 24: 9, 25: 9, 26: 9}),
    ("sun_elven", "Sun elves", 21, "tech_east_elven", ('aov_sun_elven_lineage_trigger', 'yes'),
     {2: 15, 3: 15, 4: 15, 5: 15, 6: 16, 7: 16, 8: 16, 9: 16, 10: 15, 11: 14,
      12: 13, 13: 13, 14: 12, 15: 11, 16: 11, 17: 10, 18: 10, 19: 9, 20: 9, 21: 9,
      22: 9, 23: 9, 24: 9, 25: 9, 26: 9}),
    ("wood_elven", "Wood elves", 22, "tech_wood_elf", ('aov_wood_elven_lineage_trigger', 'yes'),
     {2: 18, 3: 17, 4: 17, 5: 17, 6: 17, 7: 17, 8: 15, 9: 14, 10: 13, 11: 12,
      12: 12, 13: 11, 14: 10, 15: 10, 16: 9, 17: 9, 18: 9, 19: 9, 20: 9, 21: 9,
      22: 10, 23: 9, 24: 9, 25: 9, 26: 9}),
    ("dwarven", "Dwarves", 18, "tech_west_dwarven", ('has_cultural_pillar', 'heritage_dwarven'),
     {0: 25, 1: 25, 2: 25, 3: 22, 4: 21, 5: 21, 6: 20, 7: 19, 8: 17, 9: 13,
      10: 11, 11: 11, 12: 11, 13: 11, 14: 11, 15: 11, 16: 11, 17: 11, 18: 13, 19: 11,
      20: 11, 21: 10, 22: 10, 23: 9, 24: 9, 25: 9}),
    ("gnomish", "Gnomes", 23, "tech_gnomish", ('has_cultural_pillar', 'heritage_gnomish'),
     {0: 25, 1: 25, 2: 25, 3: 22, 4: 21, 5: 21, 6: 20, 7: 18, 8: 18, 9: 17,
      10: 15, 11: 15, 12: 14, 13: 13, 14: 13, 15: 12, 16: 11, 17: 10, 18: 10, 19: 9,
      20: 8, 21: 8, 22: 8}),
    ("kobold", "Kobolds", 26, "tech_kobold", ('has_cultural_pillar', 'heritage_kobold'),
     {0: 21, 1: 21, 2: 21, 3: 20, 4: 19, 5: 18, 6: 17, 7: 16, 8: 15, 9: 14,
      10: 14, 11: 14, 12: 14, 13: 13, 14: 13, 15: 13, 16: 13, 17: 13, 18: 13, 19: 12,
      20: 11, 21: 10, 22: 10, 23: 9, 24: 9, 25: 9}),
]

# Realms in Exile's levy and knight pictures for the military window, by race key (RACES order, first match wins):
# race -> (levies picture, knights picture), file names in ILLUSTRATION_DIR, copied once from RiE's men_at_arms_big
# (docs/systems/racial-armies.md). Races not listed keep the engine's culture pictures. RiE gives every elf its elven
# levies; sun elves (its Calaquendi) its elven knights, moon elves (Lomiquendi) its Falathrim knights, wood elves
# (Moriquendi) its Silvan knights; dwarves its Longbeard levies and knights.
ILLUSTRATION_DIR = "gfx/interface/illustrations/men_at_arms_big"
MILITARY_ART = {
    "moon_elven": ("aov_rie_levies_elven.dds", "aov_rie_knights_falathrim.dds"),
    "sun_elven": ("aov_rie_levies_elven.dds", "aov_rie_knights_elven.dds"),
    "wood_elven": ("aov_rie_levies_elven.dds", "aov_rie_knights_silvan.dds"),
    "dwarven": ("aov_rie_levies_longbeard.dds", "aov_rie_knights_longbeard.dds"),
}
# Military window pictures: the icon's name in gui/window_military.gui -> index into a MILITARY_ART pair.
MILITARY_ICONS = {"icon_levies": 0, "icon_knights": 1}

# Interface files whose knight badge becomes the race badge: path -> (whose race: the character or army scope the
# badge can reach, number of badges). Anbennar's copy of a file is used when it has one, else the game's.
GUI_TARGETS = {
    "gui/window_military.gui": ("Character", 1),  # the ruler whose military window it is
    "gui/window_knights.gui": ("Character", 1),  # a knight (the custom loc takes their court owner)
    "gui/window_army.gui": ("Army.GetOwner", 2),  # the army's ruler
    "gui/window_battle_summary.gui": ("RegimentCombatStats.GetKnight", 2),  # a knight
    "gui/shared/cooltip.gui": ("Army.GetOwner", 2),  # army tooltip: the army's ruler
}
