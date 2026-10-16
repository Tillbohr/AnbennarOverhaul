"""Data for tools/build_portraits.py: which cultures wear which Realms in Exile look, and which RiE portrait
modifiers are copied (spec docs/superpowers/specs/2026-10-15-rie-portraits-design.md)."""

# Clothing groups: the clothing_gfx key prepended to the cultures' clothing_gfx lists (in data order, so a culture in
# two groups lists both keys, the earlier group's first), and either explicit culture keys or heritages.
CLOTHING_GROUPS = {
    "hobbit": {"label": "Hobbit", "clothing_gfx": "aov_hobbit_clothing_gfx",
               "heritages": ("heritage_halfling", "heritage_gnomish")},
    "elven": {"label": "Elven", "clothing_gfx": "aov_elven_clothing_gfx", "cultures": ("sun_elvish", "moon_elvish")},
    "lasgalendrim": {"label": "Silvan Elven", "clothing_gfx": "aov_lasgalendrim_clothing_gfx",
                     "cultures": ("wood_elvish",)},
    "southern_dwarf": {"label": "Dwarven (Southern)", "clothing_gfx": "aov_southern_dwarf_clothing_gfx",
                       "cultures": ("copper_dwarvish", "gold_dwarvish", "marble_dwarvish")},
    "dwarf": {"label": "Dwarven", "clothing_gfx": "aov_dwarf_clothing_gfx", "heritages": ("heritage_dwarven",)},
}

# CULTURE_INPUT values (and portrait_<input>_clothing_trigger names) of the copied entries: RiE key -> ours. Every
# other RiE clothing key becomes NONE_INPUT, whose triggers are always false.
INPUTS = {"hobbit": "aov_hobbit", "elven": "aov_elven", "lasgalendrim": "aov_lasgalendrim", "dwarf": "aov_dwarf"}
NONE_INPUT = "aov_rie_none"
# Our inputs whose triggers test the culture's clothing_gfx key (through vanilla's
# portrait_shared_clothing_contents_trigger, flag = the input), and inputs made of others: input -> (input it needs,
# input it excludes). "aov_dwarf" counts every dwarf; "aov_western_dwarf" excludes the southern ones.
FLAG_INPUTS = ("aov_hobbit", "aov_elven", "aov_lasgalendrim", "aov_dwarf", "aov_southern_dwarf")
COMBINED_INPUTS = {"aov_western_dwarf": ("aov_dwarf", "aov_southern_dwarf")}

# RiE dwarf heritages (culture scope) -> our culture triggers (generated with the portrait triggers).
HERITAGES = {
    "heritage_longbeard": "aov_rie_western_dwarf_culture_trigger",
    "heritage_firebeard": "aov_rie_western_dwarf_culture_trigger",
    "heritage_broadbeam": "aov_rie_western_dwarf_culture_trigger",
    "heritage_blacklock": "aov_rie_southern_dwarf_culture_trigger",
    "heritage_stonefoot": "aov_rie_southern_dwarf_culture_trigger",
    "heritage_ironfist": "aov_rie_eastern_dwarf_culture_trigger",
    "heritage_stiffbeard": "aov_rie_eastern_dwarf_culture_trigger",
}
CULTURE_TRIGGERS = {
    "aov_rie_western_dwarf_culture_trigger": "has_clothing_gfx = aov_dwarf_clothing_gfx "
                                             "NOT = { has_clothing_gfx = aov_southern_dwarf_clothing_gfx }",
    "aov_rie_southern_dwarf_culture_trigger": "has_clothing_gfx = aov_southern_dwarf_clothing_gfx",
    "aov_rie_eastern_dwarf_culture_trigger": "always = no",
}

# RiE game rules -> fixed values (RiE's default: short female dwarf beards).
GAME_RULES = {"short_dwarven_beards": "yes", "long_dwarven_beards": "no", "long_and_short_dwarven_beards": "no"}

# Literal replacements in every copied entry (after the renames above).
REPLACE = (
    ("scope:culture = culture:lasgalendrim", "scope:culture = { has_clothing_gfx = aov_lasgalendrim_clothing_gfx }"),
    ("is_elf = yes", "culture ?= { has_elvish_heritage = yes }"),  # RiE's race trigger; Anbennar's heritage one
    ("cannot_be_killed = yes", "always = no"),  # RiE's immortals (Maiar, Nazgul)
    ("dynasty = dynasty:dynasty_oropher", "always = no"),  # elven_war_silvan_king leaves Oropher's house to its entry
)

_WESTERN = {"inputs": {"dwarf": "aov_western_dwarf"}}

# RiE portrait modifiers to copy: RiE file -> RiE group -> entries; an entry is a name (every block of that name, in
# file order; a repeated name gets _2, _3) or (name, options). Options: "inputs" overrides INPUTS for the entry.
ENTRIES = {
    "01_clothes_base.txt": {"clothes_base": [
        "hobbit_clothes_low", "hobbit_clothes_high",
        "elven_clothes_common", "elven_clothes_low", "elven_clothes_high",
        "lasgalendrim_clothes_common", "lasgalendrim_clothes_low", "lasgalendrim_clothes_high",
        "lasgalendrim_clothes_royalty",
        ("western_dwarf_commoners", _WESTERN), ("western_dwarf_low_nobles", _WESTERN),
        ("western_dwarf_high_nobles", _WESTERN), ("western_dwarf_kings", _WESTERN),
        "southern_dwarf_common", "southern_dwarf_high",
    ]},
    "01_headgear_base.txt": {"headgear": [
        "hobbit_commoners",
        "elven_commoners", "elven_counts", "elven_dukes", "elven_royalty_base",
        "silvan_commoner", "silvan_low", "silvan_high", "silvan_royalty",
        ("dwarf_western_commoner", _WESTERN), ("dwarf_western_low", _WESTERN),
        ("dwarf_western_low_female", _WESTERN), ("dwarf_western_high", _WESTERN),
        "dwarf_southern_low", "dwarf_southern_high", "dwarf_royalty",
    ]},
    "01_legwear_base.txt": {"legwear": [
        "hobbit_legwear",
        "elven_legwear", "elven_war_legwear",
        "silvan_legwear_common", "silvan_nobility_legwear", "silvan_high_nobility_legwear",
        "elven_war_silvan_legwear", "elven_war_silvan_king_legwear",
        "dwarf_common_legwear", "dwarf_longbeard_legwear", "dwarf_longbeard_royalty_legwear", "dwarf_southern_legwear",
    ]},
    "01_cloaks_base.txt": {"cloaks": ["dwarf_western_royalty"]},
    "01_hairstyles_base.txt": {"hairstyles": [
        "hobbit_hairstyles", "low_elven", "low_elven_no_dlc",
        "dwarven_straight", "dwarven_wavy", "dwarven_curly", "dwarven_eastern_all",
    ]},
    "01_beards_base.txt": {"beards": [
        "dwarven_males_vanilla", "dwarven_males_fp1", "dwarven_males_fp2",
        "dwarven_females_vanilla_short", "dwarven_females_vanilla_long",
        "dwarven_females_ep2_short", "dwarven_females_ep2_long",
        "dwarven_females_fp1_short", "dwarven_females_fp1_long",
        "dwarven_females_fp2_short", "dwarven_females_fp2_long", "dwarven_females_fp3_long",
        "dwarven_males_eastern",
    ]},
    "04_clothes_armor.txt": {"clothes_armor": [
        "hobbit_war",
        "elven_war", "elven_war_silvan", "elven_war_silvan_king",
        "dwarf_mercenary", "dwarf_war_steel", "dwarf_war_longbeard", "dwarf_war_longbeard_royalty",
        "dwarf_war_blacklock_commoner", "dwarf_war_blacklock_noble",
        "dwarf_war_stonefoot_commoner", "dwarf_war_stonefoot_noble",
    ]},
    "04_headgear_armor.txt": {"headgear_armor": [
        "hobbit_war",
        "elven_war", "elven_war_silvan", "elven_war_silvan_king",
        "steel_dwarf_war_commoner", "steel_dwarf_war_noble", "dwarf_war_longbeard", "dwarf_war_longbead_royalty",
        "dwarf_war_eastern_gold", "dwarf_war_eastern_silver",
    ]},
}
# Not copied, RiE-only: elven_war_oropher (RiE's dynasty_oropher), hobbit_travel_cloak (a flag RiE's duel events set), dwarven_mining_no_cloak and
# dwarf_mining_headgear (RiE's activity_mining).

# Hand-written modifiers appended to a copied group: RiE group -> texts (one tab-indented block each).
EXTRA_ENTRIES = {
    "beards": [
        "\taov_hobbit_no_beard = { # RiE hobbits are beardless (its has_no_beard entry also covers other cases)\n"
        "\t\tdna_modifiers = {\n"
        "\t\t\taccessory = {\n"
        "\t\t\t\tmode = add\n"
        "\t\t\t\tgene = beards\n"
        "\t\t\t\ttemplate = no_beard\n"
        "\t\t\t\trange = { 0 1 } # For the randomness to work correctly\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t\tweight = {\n"
        "\t\t\tbase = 0\n"
        "\t\t\tmodifier = {\n"
        "\t\t\t\tadd = 1000\n"
        "\t\t\t\tportrait_aov_hobbit_clothing_trigger = yes\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n",
    ],
}
