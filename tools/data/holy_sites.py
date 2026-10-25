"""Data for tools/build_holy_sites.py: holy sites for Anbennar faiths that have none.

Each entry is one new holy site: its key, the county and barony it sits in, the name shown in game, the character
modifier it grants, and the faiths that hold it. The generator writes the holy site definitions and their loc, and
adds a holy_site line to each faith in a whole-file copy of the Anbennar religion file that defines it.

Devouring Path (Beikling) and Silk Turban (Raghamidesh) are emigrant faiths from Haless and Rahen, which lie off the
CK3 map; each starts with a single county in Salahad. Their holy sites are that county and the lands next to it.
"""

HOLY_SITES = [
    # Devouring Path: the Beikling enclave at Benoné in Siadanlen and the harpy mountains around it.
    {
        "key": "benone",
        "county": "c_benone",
        "barony": "b_benone",
        "name": "Benoné",
        "modifier": {"health": "0.15"},  # eternal life is the meaning of enlightenment
        "faiths": ["devouring_path"],
    },
    {
        "key": "ianvireri",
        "county": "c_ianvireri",
        "barony": "b_ianvireri",
        "name": "Ianviréri",
        "modifier": {"mountains_advantage": "3"},  # the Path's cthonic redoubts
        "faiths": ["devouring_path"],
    },
    {
        "key": "mohira",
        "county": "c_mermigan",
        "barony": "b_mohira",
        "name": "Mohíra",
        "modifier": {"dread_gain_mult": "0.1"},
        "faiths": ["devouring_path"],
    },
    {
        "key": "phiomusti",
        "county": "c_kotidurnor",
        "barony": "b_phiomusti",
        "name": "Phiomústi",
        "modifier": {"intrigue_per_piety_level": "1"},
        "faiths": ["devouring_path"],
    },
    # Silk Turban: the Raghamidesh merchant colony at Davharral and the Masnsih trade towns around it.
    {
        "key": "davharral",
        "county": "c_davharral",
        "barony": "b_davharral",
        "name": "Davharral",
        "modifier": {"domain_tax_mult": "0.1"},
        "faiths": ["silk_turban"],
    },
    {
        "key": "rahensah",
        "county": "c_sahkuz",
        "barony": "b_rahensah",
        "name": "Rahenšah",
        "modifier": {"build_gold_cost": "-0.1"},
        "faiths": ["silk_turban"],
    },
    {
        "key": "nabasah",
        "county": "c_sahnuses",
        "barony": "b_nabasah",
        "name": "Nabašah",
        "modifier": {"development_growth_factor": "0.1"},
        "faiths": ["silk_turban"],
    },
    {
        "key": "edenlil",
        "county": "c_edenlil",
        "barony": "b_edenlil",
        "name": "Edenlil",
        "modifier": {"diplomacy_per_piety_level": "1"},  # ritual hospitality
        "faiths": ["silk_turban"],
    },
]
