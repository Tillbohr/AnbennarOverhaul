"""Allowed modifier keys and building icons of the great-project monuments (read by tools/build_monuments.py).

The monument data in tools/data/monuments/<region>.py was imported once from EU4 Anbennar; edit it there.
build_monuments.py stops on a modifier key that is not in MODIFIER_KEYS (add a new key here first) and on a
category without an icon in ICONS.
"""

MODIFIER_KEYS = frozenset({
    "accolade_glory_gain_mult", "advantage", "archers_damage_mult", "army_maintenance_mult", "build_gold_cost",
    "build_speed", "building_slot_add", "clergy_opinion", "county_opinion_add", "defender_advantage",
    "defender_holding_advantage", "development_growth_factor", "different_culture_opinion",
    "different_faith_county_opinion_mult", "diplomacy", "domain_limit", "domain_tax_mult",
    "embarkation_cost_mult", "enemy_hostile_scheme_success_chance_add", "faith_conversion_piety_cost_mult",
    "fort_level", "garrison_size", "general_opinion", "heavy_cavalry_damage_mult", "heavy_cavalry_max_size_add",
    "heavy_infantry_damage_mult", "heavy_infantry_maintenance_mult", "hostile_raid_time",
    "knight_effectiveness_mult", "knight_limit", "levy_reinforcement_rate", "levy_size", "levy_toughness",
    "life_expectancy", "light_cavalry_pursuit_mult", "maa_damage_mult", "maa_toughness_mult", "martial",
    "max_loot_mult", "men_at_arms_maintenance", "mercenary_hire_cost_mult", "monthly_county_control_growth_add",
    "monthly_income", "monthly_income_mult", "monthly_learning_lifestyle_xp_gain_mult",
    "monthly_legitimacy_add", "monthly_lifestyle_xp_gain_mult", "monthly_magic_lifestyle_xp_gain_mult",
    "monthly_martial_lifestyle_xp_gain_mult", "monthly_piety", "monthly_prestige", "monthly_prestige_gain_mult",
    "movement_speed", "naval_movement_speed_mult", "owned_hostile_scheme_success_chance_add",
    "owned_scheme_secrecy_add", "provisions_use_mult", "raid_speed", "siege_phase_time",
    "siege_weapon_maintenance_mult", "supply_limit_mult", "tax_mult", "tyranny_gain_mult",
    "vassal_levy_contribution_mult", "vassal_opinion", "vassal_tax_contribution_mult",
})

ICONS = {
    "fortress": "icon_structure_the_citadel_of_aleppo.dds",
    "castle": "icon_structure_visegrad_castle.dds",
    "palace": "icon_structure_doges_palace.dds",
    "temple": "icon_structure_notre_dame.dds",
    "academy": "icon_structure_university_of_siena.dds",
    "library": "icon_structure_grand_library_of_baghdad.dds",
    "port": "icon_structure_quanzhou_seaport.dds",
    "market": "icon_structure_special_silk_road_market.dds",
    "guild": "icon_building_guild_halls.dds",
    "foundry": "icon_building_royal_armory.dds",
    "mine": "icon_structure_mines.dds",
    "tomb": "icon_structure_tomb_of_cyrus.dds",
    "monument": "icon_building_legendary_statue.dds",
    "theatre": "icon_structure_colosseum.dds",
    "lighthouse": "icon_building_legendary_watchtower.dds",
    "bath": "icon_building_bath_house.dds",
    "forest": "icon_building_royal_forest.dds",
}
