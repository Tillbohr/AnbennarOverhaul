"""Data for tools/rie_units.py (built by tools/build_holding_models.py): which cultures get which RiE army models."""

# Culture groups: the unit_gfx key prepended to their unit_gfx lists, and either explicit culture keys or a heritage
# (every culture of it). Every culture of a group must have the same unit_gfx list.
UNIT_GROUPS = {
    "wood_elf": {"label": "Wood Elven", "unit_gfx": "aov_wood_elf_unit_gfx", "cultures": ("wood_elvish",)},
    "sun_elf": {"label": "Sun Elven", "unit_gfx": "aov_sun_elf_unit_gfx", "cultures": ("sun_elvish",)},
    "moon_elf": {"label": "Moon Elven", "unit_gfx": "aov_moon_elf_unit_gfx", "cultures": ("moon_elvish",)},
    "dwarven": {"label": "Dwarven", "unit_gfx": "aov_dwarven_unit_gfx", "heritage": "heritage_dwarven"},
}

# Group -> (lowest army quality in pips, RiE army entity), lowest first; each model shows up to the next one's pips
# (CK3 army quality is 1-5 pips). User choice: the elves get their RiE culture's models 1 and 2 (Woodland Realm for
# the Lasgalendrim, Lindon for the Sindar, Imladris for the Noldor), the dwarves RiE's Firebeards model 1, Durin's
# Folk (RiE's Longbeards, Erebor) model 2 and Broadbeams (Khazad) model 3.
ARMY_MODELS = {
    "wood_elf": ((1, "acg_elves_woodlandrealm_army_01_single_entity"),
                 (3, "acg_elves_woodlandrealm_army_02_single_entity")),
    "sun_elf": ((1, "acg_elves_lindon_army_01_single_entity"),
                (3, "acg_elves_lindon_army_02_single_entity")),
    "moon_elf": ((1, "acg_elves_imladris_army_01_single_entity"),
                 (3, "acg_elves_imladris_army_02_single_entity")),
    "dwarven": ((1, "acg_dwarves_khazad_firebeards_army_01_single_entity"),
                (3, "acg_dwarves_erebor_army_02_single_entity"),
                (4, "acg_dwarves_khazad_army_03_single_entity")),
}
