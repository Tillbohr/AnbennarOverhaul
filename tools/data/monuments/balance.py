"""Core effects of the great-project monuments by category (read by tools/build_monuments.py).

Every monument level gets its category's core package on top of its EU4 effects (tools/data/monuments/<region>.py),
so a full chain is worth about as much as a vanilla special building of the same cost:

- mine: Rammelsberg (00_special_mines.txt) levels 2-4
- temple: Notre Dame / Cologne Cathedral (00_special_buildings.txt)
- fortress: Citadel of Aleppo levels 1-2 (vanilla normal advantage and stationed MAA tiers 1-3)
- academy, library: House of Wisdom
- the rest scaled between those and vanilla's generic copper mines

CORE: package -> list of (block, modifier key, (tier 1, tier 2, tier 3)); a 0 leaves the key out of that tier.
CATEGORY_CORE: monument category -> package. CORE_OVERRIDES: eu4_key -> another package, or None for no core.
POI_FLAGS: category -> vanilla travel point-of-interest flag added to every level.

When a level already has the same key in the same block (its EU4 effect, or Anbennar's own line on an Anbennar
chain), the stronger of the two is kept, not the sum: the larger value for a positive core value, the smaller for a
negative one (travel_danger). An existing value of the opposite sign is a penalty and is summed with the core value.
"""

CORE = {
    "mine": [
        ("province_modifier", "monthly_income", (8, 11, 14)),
        ("county_modifier", "tax_mult", (0.25, 0.3, 0.35)),
        ("county_modifier", "development_growth_factor", (0.1, 0.15, 0.2)),
    ],
    "temple": [
        ("province_modifier", "monthly_income", (1.5, 2, 3)),
        ("county_modifier", "tax_mult", (0.1, 0.15, 0.2)),
        ("county_modifier", "development_growth_factor", (0.15, 0.2, 0.25)),
        ("county_modifier", "development_growth", (0.1, 0.2, 0.25)),
        ("county_modifier", "county_opinion_add", (3, 4, 5)),
        ("character_modifier", "monthly_piety", (0.5, 0.75, 1)),
        ("character_modifier", "monthly_dynasty_prestige_mult", (0.02, 0.03, 0.05)),
    ],
    "economic": [
        ("province_modifier", "monthly_income", (4, 6, 8)),
        ("county_modifier", "tax_mult", (0.15, 0.25, 0.3)),
        ("county_modifier", "development_growth_factor", (0.1, 0.15, 0.2)),
    ],
    "foundry": [
        ("province_modifier", "monthly_income", (3, 4.5, 6)),
        ("county_modifier", "tax_mult", (0.15, 0.2, 0.25)),
        ("character_modifier", "maa_toughness_mult", (0.05, 0.08, 0.1)),
    ],
    "palace": [
        ("province_modifier", "monthly_income", (1, 1.5, 2)),
        ("county_modifier", "development_growth_factor", (0.1, 0.15, 0.2)),
        ("character_modifier", "monthly_prestige", (0.5, 0.75, 1)),
        ("character_modifier", "vassal_opinion", (5, 8, 10)),
        ("character_modifier", "monthly_dynasty_prestige_mult", (0.02, 0.03, 0.05)),
    ],
    "fortress": [
        ("province_modifier", "defender_holding_advantage", (2, 4, 6)),
        ("province_modifier", "garrison_size", (0.2, 0.35, 0.5)),
        ("province_modifier", "stationed_maa_damage_mult", (0.15, 0.15, 0.2)),
        ("province_modifier", "stationed_maa_toughness_mult", (0.15, 0.15, 0.2)),
        ("province_modifier", "travel_danger", (-10, -15, -20)),
        ("character_modifier", "monthly_prestige", (0.1, 0.2, 0.3)),
    ],
    "academy": [
        ("county_modifier", "tax_mult", (0.1, 0.15, 0.2)),
        ("county_modifier", "development_growth_factor", (0.1, 0.2, 0.25)),
        ("county_modifier", "development_growth", (0.1, 0.2, 0.25)),
        ("character_modifier", "monthly_lifestyle_xp_gain_mult", (0.05, 0.1, 0.15)),
    ],
    "library": [
        ("county_modifier", "tax_mult", (0.1, 0.15, 0.2)),
        ("county_modifier", "development_growth_factor", (0.1, 0.2, 0.25)),
        ("county_modifier", "development_growth", (0.1, 0.2, 0.25)),
        ("character_modifier", "monthly_lifestyle_xp_gain_mult", (0.05, 0.1, 0.15)),
        ("character_modifier", "learning", (1, 1, 1)),
    ],
    "monument": [
        ("province_modifier", "monthly_income", (1, 2, 3)),
        ("county_modifier", "tax_mult", (0.1, 0.12, 0.15)),
        ("county_modifier", "development_growth_factor", (0.1, 0.15, 0.2)),
        ("character_modifier", "monthly_prestige", (0.5, 0.75, 1)),
    ],
}

CATEGORY_CORE = {
    "mine": "mine",
    "temple": "temple",
    "market": "economic", "guild": "economic", "port": "economic",
    "foundry": "foundry",
    "palace": "palace", "castle": "palace",
    "fortress": "fortress",
    "academy": "academy",
    "library": "library",
    "monument": "monument", "tomb": "monument", "theatre": "monument", "bath": "monument",
    "lighthouse": "monument", "forest": "monument",
}

CORE_OVERRIDES = {}

POI_FLAGS = {
    "temple": "travel_point_of_interest_religious", "tomb": "travel_point_of_interest_religious",
    "mine": "travel_point_of_interest_economic", "market": "travel_point_of_interest_economic",
    "guild": "travel_point_of_interest_economic", "port": "travel_point_of_interest_economic",
    "foundry": "travel_point_of_interest_economic",
    "fortress": "travel_point_of_interest_martial", "castle": "travel_point_of_interest_martial",
    "academy": "travel_point_of_interest_learning", "library": "travel_point_of_interest_learning",
    "palace": "travel_point_of_interest_diplomatic",
    "monument": "travel_point_of_interest_wonder", "lighthouse": "travel_point_of_interest_wonder",
    "theatre": "travel_point_of_interest_stress_relief", "bath": "travel_point_of_interest_stress_relief",
    "forest": "travel_point_of_interest_natural_feature",
}
