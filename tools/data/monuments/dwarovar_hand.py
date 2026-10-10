"""Hand fixes for the Middle Dwarovar monuments, merged over tools/data/monuments/dwarovar.py by
tools/import_eu4_monuments.py on every import (`tiers` merges key by key; every other field is replaced)."""

HAND = {
    # Icon categories: the importer's keyword guess gave these the generic "monument" icon
    "gor_ozumbrog_the_topaz_throne": {"category": "palace"},
    "khugdihr_bank": {"category": "market"},
    "seghdihr_home_of_the_seg_band": {"category": "fortress"},
    "verkal_gulan_golden_delve": {"category": "mine"},
}
