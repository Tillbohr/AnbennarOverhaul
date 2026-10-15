"""Data for tools/build_holding_models.py: which cultures get which RiE holding-model graphics."""

# Culture groups: building_gfx key and either explicit culture keys or a heritage (every culture of it).
GROUPS = {
    "high_elf": {"gfx": "aov_high_elf_building_gfx", "cultures": ("moon_elvish", "sun_elvish")},
    "wood_elf": {"gfx": "aov_wood_elf_building_gfx", "cultures": ("wood_elvish",)},
    "dwarven": {"gfx": "aov_dwarven_building_gfx", "heritage": "heritage_dwarven"},
    "castanorian": {"gfx": "aov_castanorian_building_gfx", "heritage": "heritage_escanni"},
}

# Province terrains that count as dwarven mountains (dwarves keep mountain models there, land models elsewhere).
DWARF_MOUNTAIN_TERRAINS = ("mountains", "desert_mountains", "dwarven_hold", "dwarven_hold_surface",
                           "cavern", "dwarven_road")

REGION = "graphical_aov_dwarven_mountains"
REGION_COLOR = (120, 80, 40)
