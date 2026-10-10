"""Hand fixes for the Deepwoods monuments, merged over tools/data/monuments/deepwoods.py by
tools/import_eu4_monuments.py on every import (`tiers` merges key by key; every other field is replaced)."""

# EU4 has no description for the Black Demesne's nine Pillars of Eternity (mission monuments; the four whose EU4
# province has a CK3 title are built). Text written from their EU4 data: Black Demesne gate, damestear at tier 3.
_PILLAR = {
    "name": "Pillar of Eternity",
    "desc": "One of the nine Pillars of Eternity that the sorcerers of the Black Demesne raise across the Deepwoods. "
            "Each pillar draws the wealth of the forest towards it, and at its full height turns the earth around "
            "it to damestear, but the folk of the woods resent the black stone and those who serve it.",
    "tiers": [{}, {}, {"county_modifier": {"tax_mult": 0.3}}],
    "notes": ["Gate decision: left open. EU4 requires a Black Demesne government reform (has_reform), which has "
              "no CK3 equivalent.",
              "Balance cap: county tax_mult reduced from 0.399 to 0.3 at level 3.",
              "mission-spawned in EU4 (start province read from a commented start)"],
}

HAND = {
    "ciranmyna_the_shimmering_city": {"category": "fortress"},
    **{f"eternal_pillar_{n}": _PILLAR for n in (1, 2, 5, 6)},
}
