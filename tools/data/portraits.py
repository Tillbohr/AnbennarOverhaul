"""Data for tools/build_portraits.py: which cultures wear which Realms in Exile look, and which RiE portrait
modifiers are copied (spec docs/superpowers/specs/2026-10-15-rie-portraits-design.md)."""

# Clothing groups: the clothing_gfx key prepended to the cultures' clothing_gfx lists (in data order, so a culture in
# two groups lists both keys, the earlier group's first), and either explicit culture keys or heritages. User choice:
# moon elves wear RiE's Noldor look, sun elves its Vanyar look (RiE's generic elves wear vanilla clothes); gnomes keep
# Anbennar's look (user choice after the first in-game test); halflings keep RiE's hobbit hair and beardlessness but
# wear Anbennar's clothes, headgear, legwear and armour (user choice: RiE's hobbit clothing reverted); every dwarf wears
# vanilla northern European clothes under RiE's dwarf hats, crowns, boots, armour, hair and beards, with no RiE southern
# dwarf style (user choice, round 4).
CLOTHING_GROUPS = {
    "hobbit": {"label": "Hobbit", "clothing_gfx": "aov_hobbit_clothing_gfx", "heritages": ("heritage_halfling",)},
    "vanyar": {"label": "Vanyarin Elven", "clothing_gfx": "aov_vanyar_clothing_gfx", "cultures": ("sun_elvish",)},
    "noldor": {"label": "Noldorin Elven", "clothing_gfx": "aov_noldor_clothing_gfx", "cultures": ("moon_elvish",)},
    "lasgalendrim": {"label": "Silvan Elven", "clothing_gfx": "aov_lasgalendrim_clothing_gfx",
                     "cultures": ("wood_elvish",)},
    # Copper, gold and marble dwarves look like the others, but their list continues differently (Anbennar's MENA
    # clothing keys), and every list starting with one key must continue the same way: so they lead with their own key.
    "southern_dwarf": {"label": "Dwarven (Southern)", "clothing_gfx": "aov_southern_dwarf_clothing_gfx",
                       "cultures": ("copper_dwarvish", "gold_dwarvish", "marble_dwarvish")},
    "dwarf": {"label": "Dwarven", "clothing_gfx": "aov_dwarf_clothing_gfx", "heritages": ("heritage_dwarven",)},
}

# CULTURE_INPUT values (and portrait_<input>_clothing_trigger names) of the copied entries: RiE key -> ours. Every
# other RiE clothing key becomes NONE_INPUT, whose triggers are always false. RiE's Vanyar culture has the generic
# elven key (its Vanyar entries add culture:vanyar), so "elven" is the sun elves.
INPUTS = {"hobbit": "aov_hobbit", "elven": "aov_vanyar", "noldor": "aov_noldor", "lasgalendrim": "aov_lasgalendrim",
          "dwarf": "aov_dwarf"}
NONE_INPUT = "aov_rie_none"
# Our inputs whose triggers test the culture's clothing_gfx key (through vanilla's
# portrait_shared_clothing_contents_trigger, flag = the input), and inputs made of others: input -> (input it needs,
# input it excludes). "aov_dwarf" counts every dwarf.
FLAG_INPUTS = ("aov_hobbit", "aov_vanyar", "aov_noldor", "aov_lasgalendrim", "aov_dwarf")
COMBINED_INPUTS = {}

# RiE dwarf heritages (culture scope) -> our culture triggers (generated with the portrait triggers): RiE's western
# clans (Durin's Folk, Firebeards, Broadbeams) are every dwarf of ours; its eastern and southern clans none.
HERITAGES = {
    "heritage_longbeard": "aov_rie_western_dwarf_culture_trigger",
    "heritage_firebeard": "aov_rie_western_dwarf_culture_trigger",
    "heritage_broadbeam": "aov_rie_western_dwarf_culture_trigger",
    "heritage_blacklock": "aov_rie_other_dwarf_culture_trigger",
    "heritage_stonefoot": "aov_rie_other_dwarf_culture_trigger",
    "heritage_ironfist": "aov_rie_other_dwarf_culture_trigger",
    "heritage_stiffbeard": "aov_rie_other_dwarf_culture_trigger",
}
CULTURE_TRIGGERS = {
    "aov_rie_western_dwarf_culture_trigger": "has_clothing_gfx = aov_dwarf_clothing_gfx",
    "aov_rie_other_dwarf_culture_trigger": "always = no",
}

# RiE game rules -> fixed values.
GAME_RULES = {"short_dwarven_beards": "no", "long_dwarven_beards": "no", "long_and_short_dwarven_beards": "no"}

# Literal replacements in every copied entry (after the renames above).
REPLACE = (
    ("scope:culture = culture:lasgalendrim", "scope:culture = { has_clothing_gfx = aov_lasgalendrim_clothing_gfx }"),
    ("scope:culture = culture:vanyar", "scope:culture = { has_clothing_gfx = aov_vanyar_clothing_gfx }"),
    ("is_elf = yes", "culture ?= { has_elvish_heritage = yes }"),  # RiE's race trigger; Anbennar's heritage one
    ("cannot_be_killed = yes", "always = no"),  # RiE's immortals (Maiar, Nazgul)
    ("dynasty = dynasty:dynasty_oropher", "always = no"),  # elven_war_silvan_king leaves Oropher's house to its entry
    ("this = character:lineofeonwe", "always = no"),  # RiE characters (elven_war_vanyar_legwear)
    ("this = character:lineofglorfindel", "always = no"),
    ("this = character:lineofeltariel", "always = no"),
)

# Anbennar's own northern European clothes for every dwarf ("source": take the entry from Anbennar's file of that name).
_NORTHERN = {"source": "anbennar", "inputs": {"northern": "aov_dwarf"}}
# The entry's high-noble clothing trigger also covers kings and emperors (RiE has no royal entry for the culture, so
# its kings would fall back to Anbennar's vanilla robes).
_UP_TO_EMPEROR = {"up_to_emperor": True}

# RiE portrait modifiers to copy: RiE file -> RiE group -> entries; an entry is a name (every block of that name, in
# file order; a repeated name gets _2, _3) or (name, options). Options: "inputs" overrides INPUTS for the entry,
# "up_to_emperor" (see above), "source": "anbennar" copies Anbennar's entry of that name from its file and group of
# the same name instead (the group's settings stay RiE's). Order matters: inside a group the first modifier weighing
# 100 or more wins, so a specific entry comes before the generic one it should beat.
ENTRIES = {
    "01_clothes_base.txt": {"clothes_base": [
        "vanyar_clothes_low", ("vanyar_clothes_high", _UP_TO_EMPEROR),
        "noldor_clothes_common", "noldor_clothes_low", ("noldor_clothes_high", _UP_TO_EMPEROR),
        "lasgalendrim_clothes_common", "lasgalendrim_clothes_low", "lasgalendrim_clothes_high",
        "lasgalendrim_clothes_royalty",
        ("northern_commoners", _NORTHERN), ("northern_low_nobles", _NORTHERN),
        ("northern_high_nobles", dict(_NORTHERN, **_UP_TO_EMPEROR)),
    ]},
    "01_headgear_base.txt": {"headgear": [
        "elven_commoners", "elven_counts", "elven_dukes", "elven_royalty_noldor", "elven_royalty_base",
        "silvan_commoner", "silvan_low", "silvan_high", "silvan_royalty",
        "dwarf_western_commoner", "dwarf_western_low", "dwarf_western_low_female", "dwarf_western_high",
        "dwarf_royalty",
    ]},
    "01_legwear_base.txt": {"legwear": [
        "elven_war_vanyar_legwear", "elven_war_legwear",
        "silvan_legwear_common", "silvan_nobility_legwear", "silvan_high_nobility_legwear",
        "elven_war_silvan_legwear", "elven_war_silvan_king_legwear",
        "dwarf_common_legwear", "dwarf_longbeard_legwear", "dwarf_longbeard_royalty_legwear",
    ]},
    "01_cloaks_base.txt": {"cloaks": ["dwarf_western_royalty"]},
    "01_hairstyles_base.txt": {"hairstyles": [
        "hobbit_hairstyles", "high_elven", "high_elven_no_dlc", "low_elven", "low_elven_no_dlc",
        "dwarven_straight", "dwarven_wavy", "dwarven_curly",
    ]},
    "01_beards_base.txt": {"beards": [
        "dwarven_males_vanilla", "dwarven_males_fp1", "dwarven_males_fp2",
    ]},
    "04_clothes_armor.txt": {"clothes_armor": [
        "elven_war_valinor", "elven_war", "elven_war_noldor_high", "elven_war_noldor",
        "elven_war_silvan", "elven_war_silvan_king",
        "dwarf_mercenary", "dwarf_war_steel", "dwarf_war_longbeard", "dwarf_war_longbeard_royalty",
    ]},
    "04_headgear_armor.txt": {"headgear_armor": [
        "elven_war_valinor", "elven_war_noldor", "elven_war", "elven_war_silvan", "elven_war_silvan_king",
        "steel_dwarf_war_commoner", "steel_dwarf_war_noble", "dwarf_war_longbeard", "dwarf_war_longbead_royalty",
    ]},
}
# Not copied: RiE's hobbit clothes, headgear, legwear and war armour (user choice: reverted), RiE's generic
# elven_clothes_* and elven_legwear (vanilla accessories; the sun elves wear the Vanyar entries), the female dwarf
# beards (user choice), RiE's western dwarf everyday clothes (vanilla HRE ones; dwarves wear Anbennar's northern ones)
# and its southern and eastern dwarf entries (user choice), and RiE-only content: elven_war_oropher (RiE's
# dynasty_oropher), the Noldor second-age, Gil-galad, Glorfindel, Feanorian, golden and high king armour (RiE dates,
# titles, houses, characters), elven_war_noldor_legwear (needs the generic elven key and culture:noldor at once, never
# true), hobbit_travel_cloak (a flag RiE's duel events set), dwarven_mining_no_cloak and dwarf_mining_headgear (RiE's
# activity_mining).


def _entry(name: str, comment: str, gene: str, template: str, conditions: list) -> str:
    lines = [f"\t{name} = {{ # {comment}", "\t\tdna_modifiers = {", "\t\t\taccessory = {", "\t\t\t\tmode = add",
             f"\t\t\t\tgene = {gene}", f"\t\t\t\ttemplate = {template}",
             "\t\t\t\trange = { 0 1 } # For the randomness to work correctly", "\t\t\t}", "\t\t}",
             "\t\tweight = {", "\t\t\tbase = 0", "\t\t\tmodifier = {", "\t\t\t\tadd = 1000"]
    lines += [f"\t\t\t\t{condition}" for condition in conditions]
    return "\n".join(lines + ["\t\t\t}", "\t\t}", "\t}"]) + "\n"


# Hand-written modifiers appended to a copied group: RiE group -> texts (one tab-indented block each).
EXTRA_ENTRIES = {
    "beards": [
        _entry("aov_hobbit_no_beard", "RiE hobbits are beardless (its has_no_beard entry also covers other cases)",
               "beards", "no_beard", ["portrait_aov_hobbit_clothing_trigger = yes"]),
    ],
    "cloaks": [
        # RiE gives its elves no vanilla cloaks (they are not in its proxy lists); war cloaks come from the armour
        # group, which applies later.
        _entry("aov_elf_no_cloak", "RiE's elves wear no vanilla cloaks", "cloaks", "no_cloak",
               ["OR = { portrait_aov_vanyar_clothing_trigger = yes portrait_aov_noldor_clothing_trigger = yes "
                "portrait_aov_lasgalendrim_clothing_trigger = yes }"]),
    ],
}
