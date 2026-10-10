"""Hand fixes for the Salahad monuments (North Salahad with Kheterata and Akasik, South Salahad), merged over
tools/data/monuments/salahad.py by tools/import_eu4_monuments.py on every import (`tiers` merges key by key; every
other field is replaced)."""

HAND = {
    "aur_kes_akasik": {"category": "palace"},
    "elikhet_pyramid": {"category": "tomb"},
    # Koroshesh is a one-barony county and holds two EU4 projects: the Grand Library (built in 1022) keeps
    # Koroshesh, the Grain Port goes to Kaashesh, the next coastal Korosheshi county of the duchy of Sopotremit.
    "koroshesh_grain_port": {
        "barony": "b_kaashesh",
        "notes": ["Placement: Koroshesh (c_koroshesh) has one barony, taken by the Grand Library; the Grain Port "
                  "is in b_kaashesh, a coastal county of the same duchy (d_sopotremit) and EU4 area."],
    },
    "water_dreams_oasis": {
        "category": "temple",
        "tiers": [{}, {}, {"county_modifier": {"tax_mult": 0.3, "hostile_raid_time": 0.5}}],
        "notes": ["gate atom religion:fangaulan_pantheon ignored (no CK3 equivalent)",
                  "gate atom religion:kvangahga ignored (no CK3 equivalent)",
                  "gate atom culture:dunesole_ogre ignored (no CK3 equivalent)",
                  "Balance cap: county tax_mult reduced from 0.5 to 0.3 and hostile_raid_time from 0.75 to 0.5 "
                  "(Theodosian Walls) at level 3."],
    },
}
