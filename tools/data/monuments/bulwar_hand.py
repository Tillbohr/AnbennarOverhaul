"""Hand fixes for the Bulwar monuments, merged over tools/data/monuments/bulwar.py by
tools/import_eu4_monuments.py on every import (`tiers` merges key by key; every other field is replaced)."""

HAND = {
    "anzarzax_palace": {
        "tiers": [{}, {}, {"county_modifier": {"supply_limit_mult": 0.5}}],
        "notes": ["gate atom tag:F74 ignored (no CK3 equivalent)",
                  "mission-spawned in EU4 (start province read from a commented start)",
                  "Balance cap: EU4 tier 3 adds a flat supply_limit of 40 (county supply_limit_mult 10.25 through "
                  "the table); level 3 gets supply_limit_mult 0.5."],
    },
    "ash_palace": {
        "tiers": [{"character_modifier": {"domain_limit": 1}}, {"character_modifier": {"domain_limit": 2}},
                  {"character_modifier": {"domain_limit": 2}}],
        "notes": ["gate atom flag:ash_palace_enabled ignored (no CK3 equivalent)",
                  "gate atom tag:F52 ignored (no CK3 equivalent)",
                  "gate atom religion:yudunyovi ignored (no CK3 equivalent)",
                  "Balance cap: EU4 governing capacity +100/175/250 is domain_limit 4/7/10 through the table; "
                  "capped at 1/2/2 (Cannor's largest is 2)."],
    },
    "dasmati_halls_of_reverence": {"category": "tomb"},
    "ebbusubtu": {
        "category": "temple",
        "tiers": [{}, {"character_modifier": {"monthly_piety": 0.75}}, {"character_modifier": {"monthly_piety": 1}}],
        "notes": ["gate atom religion:the_jadd ignored (no CK3 equivalent)",
                  "Gate decision: left open. EU4 gates it on the Jadd, which arises centuries after 1022; any "
                  "holder may use it.",
                  "Balance cap: EU4 fervor +1/+2 and tolerance give monthly_piety 0.5/1/2; capped at 0.5/0.75/1."],
    },
    "eduz_ginakku": {"category": "library"},
    "eka_idulnazzar": {"category": "academy"},
    "ger_bexamurr": {"category": "temple"},
    "mount_lazzaward": {"category": "temple"},
    "quartz_cothon": {"category": "port"},
    "queens_throne": {"category": "palace"},
    "suhuskar": {"category": "palace"},
}
