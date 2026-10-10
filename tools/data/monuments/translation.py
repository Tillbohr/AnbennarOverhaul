"""EU4 Anbennar great project -> CK3 special building translation table (hand-written; tune balance here).

Read by tools/import_eu4_monuments.py. How the importer applies it:

- MODIFIERS: each EU4 modifier of a tier becomes `ck3 = value * mult`. EU4 `province_modifiers` land in the
  building's `province_modifier` or `county_modifier` (the row's `scope`); `area_modifier` also lands in
  `county_modifier` (CK3's `duchy_capital_county_modifier` works only on `type = duchy_capital` buildings), and
  `country_modifiers` in `character_modifier`, whatever the scope. Rows that hit the same CK3 key in one block
  add up. Keys in INTEGER are rounded half away from zero and never round a
  nonzero value to 0 (+-1 minimum). Drop rows are listed in the tier's `dropped` notes.
- Balance target: a fully upgraded monument is about a strong vanilla special building (Hagia Sophia, Notre Dame:
  tax_mult 0.2-0.3, development_growth_factor 0.2-0.3, monthly_income 2, a skill +2, monthly_piety 1), never a
  duchy wonder (Theodosian Walls: fort_level 5, monthly_income 10).
- CK3 keys are the ones vanilla/Anbennar use in the matching block (checked by tools/tests).
- ONE_OFF: EU4 `on_upgraded` is split into top-level statements; each statement takes the effect of the first
  pattern that `re.search`es it (None = dropped and listed). Effects are CK3 `on_complete` text in province scope.
- CULTURES: EU4 gate atoms (eu4_monuments.gate_atoms) -> CK3 trigger in the holder's scope; None = ignored.
  A gate whose atoms all map to None stays open.
"""

from collections import namedtuple

Row = namedtuple("Row", "ck3 mult scope")
Drop = namedtuple("Drop", "reason")

P, C = "province", "county"
H = C  # country_modifiers always go to the holder's character_modifier; scope is unused for them

COST = 0.4  # EU4 cost factor 1000/2500/5000 -> 400/1000/2000 gold
DAYS_PER_MONTH = 15  # EU4 120/240/480 months -> 5/10/20 years

INTEGER = {
    "fort_level", "defender_holding_advantage", "building_slot_add", "county_opinion_add", "diplomacy", "martial",
    "general_opinion", "domain_limit", "knight_limit", "advantage", "defender_advantage", "heavy_cavalry_max_size_add",
    "levy_toughness",
}

_ESTATES = "EU4 estate system; CK3 has no estates"
_ABSOLUTISM = "EU4 absolutism/revolution; no CK3 equivalent"
_ADVISORS = "EU4 advisors; CK3 councillors are not hired"
_CULTURE_CONVERSION = "CK3 has no county culture-conversion modifier"
_TRADE = "EU4 trade nodes/merchants/colonies; no CK3 equivalent"
_SHIPS = "EU4 ship design/flagships; CK3 has no navies"
_GOVERNMENT = "government-specific twin of legitimacy (translated); EU4 gives only the one that applies"

MODIFIERS = {
    # --- Province/area: defence. EU4 +10% fort defence ~ one CK3 fort level; an EU4 fort level is a big step (x2).
    "local_defensiveness": Row("fort_level", 6, P),
    "fort_level": Row("fort_level", 2, P),
    "local_garrison_size": Row("garrison_size", 1, P),
    # EU4 +1 defender dice / coastal landing defences -> CK3 defender advantage (vanilla building tiers give 2-9).
    "local_defender_dice_roll_bonus": Row("defender_holding_advantage", 4, P),
    "hostile_disembark_speed": Row("defender_holding_advantage", 2, P),
    "landing_penalty": Row("defender_holding_advantage", -1, P),
    # Hostile attrition/slowing and fleet attrition -> enemies raid the holding slower (Theodosian Walls: 0.5).
    "local_hostile_attrition": Row("hostile_raid_time", 0.25, P),
    "local_hostile_movement_speed": Row("hostile_raid_time", -2, P),
    "hostile_fleet_attrition": Row("hostile_raid_time", 0.05, P),

    # --- Province/area: development and economy. Cheaper development -> faster growth (1:1, -0.15 -> +0.15).
    "local_development_cost": Row("development_growth_factor", -1, C),
    "local_prosperity_growth": Row("development_growth_factor", 1, C),
    # Tax/production/goods -> county tax at about half the EU4 percentage (EU4 +50% tax -> CK3 +25%).
    "local_tax_modifier": Row("tax_mult", 0.5, C),
    "local_production_efficiency": Row("tax_mult", 0.3, C),
    "trade_goods_size_modifier": Row("tax_mult", 0.5, C),
    "province_trade_power_modifier": Row("tax_mult", 0.3, C),
    "trade_goods_size": Row("tax_mult", 0.1, C),  # flat goods (0.25-3) also appear in area blocks: county tax
    # Flat trade power (2.5-50) -> flat province income, 15 -> 1.5 gold (Notre Dame 2, Theodosian Walls 10).
    "province_trade_power_value": Row("monthly_income", 0.1, P),
    # Extra building slots stay slots; ship costs/speed -> cheaper/faster construction there.
    "allowed_num_of_buildings": Row("building_slot_add", 1, P),
    "local_ship_cost": Row("build_gold_cost", 0.5, C),
    "ship_recruit_speed": Row("build_speed", 0.5, P),

    # --- Province/area: manpower and supply. EU4 manpower % -> levies at half; sailors are a smaller pool.
    "local_manpower_modifier": Row("levy_size", 0.5, C),
    "local_sailors_modifier": Row("levy_size", 0.25, C),
    "local_ship_repair": Row("levy_reinforcement_rate", 0.25, C),  # refitting fleets ~ reinforcing troops
    "supply_limit": Row("supply_limit_mult", 0.25, C),  # flat +2 of a ~8 base -> +50%
    "supply_limit_modifier": Row("supply_limit_mult", 1, C),

    # --- Province/area: control. EU4 -5 unrest -> +10 county opinion; autonomy/governing cost -> control growth.
    "local_unrest": Row("county_opinion_add", -2, C),
    "local_autonomy": Row("monthly_county_control_growth_add", -10, C),
    "local_governing_cost": Row("monthly_county_control_growth_add", -0.5, C),

    # --- Province: EU4-only systems.
    "allowed_num_of_manufactories": Drop("EU4 manufactories; no CK3 equivalent"),
    "blockade_force_required": Drop("EU4 naval blockades; no CK3 equivalent"),
    "gold_depletion_chance_modifier": Drop("EU4 gold mine depletion; no CK3 equivalent"),
    "local_institution_spread": Drop("EU4 institutions; no CK3 equivalent"),
    "local_state_maintenance_modifier": Drop("EU4 states; no CK3 equivalent"),
    "statewide_governing_cost": Drop("EU4 states/governing capacity; no CK3 equivalent"),

    # --- Country: prestige, legitimacy, piety. EU4 yearly prestige 0.5 -> 0.5/month; splendor at half.
    "prestige": Row("monthly_prestige", 1, H),
    "monthly_splendor": Row("monthly_prestige", 0.5, H),
    "prestige_from_land": Row("monthly_prestige_gain_mult", 0.2, H),
    "power_projection_from_insults": Row("monthly_prestige_gain_mult", 0.1, H),
    "legitimacy": Row("monthly_legitimacy_add", 0.25, H),  # EU4 +2/year -> +0.5/month (vanilla 0.1-0.5)
    "devotion": Drop(_GOVERNMENT),
    "republican_tradition": Drop(_GOVERNMENT),
    "horde_unity": Drop(_GOVERNMENT),
    "monarch_lifespan": Row("life_expectancy", 20, H),  # +15% lifespan -> +3 years

    # --- Country: faith and culture. Tolerance of own faith -> piety; of others -> less different-faith malus.
    "tolerance_own": Row("monthly_piety", 0.5, H),
    "religious_unity": Row("different_faith_county_opinion_mult", -1, H),
    "tolerance_heretic": Row("different_faith_county_opinion_mult", -0.1, H),
    "tolerance_heathen": Row("different_faith_county_opinion_mult", -0.1, H),
    "tolerance_of_heretics_capacity": Row("different_faith_county_opinion_mult", -0.05, H),
    "tolerance_of_heathens_capacity": Row("different_faith_county_opinion_mult", -0.05, H),
    "global_missionary_strength": Row("faith_conversion_piety_cost_mult", -5, H),  # +3% -> -15% conversion cost
    "missionaries": Row("faith_conversion_piety_cost_mult", -0.1, H),
    "culture_conversion_cost": Drop(_CULTURE_CONVERSION),
    "culture_conversion_time": Drop(_CULTURE_CONVERSION),
    "promote_culture_cost": Drop(_CULTURE_CONVERSION),

    # --- Country: diplomacy and intrigue. Reputation -> diplomacy skill; relations/AE -> opinion (+0.3 -> +6).
    "diplomatic_reputation": Row("diplomacy", 1, H),
    "improve_relation_modifier": Row("general_opinion", 20, H),
    "ae_impact": Row("general_opinion", -20, H),
    "accept_vassalization_reasons": Drop("EU4 diplomatic vassalization; no CK3 equivalent"),
    "diplomatic_upkeep": Drop("EU4 relation slots; no CK3 equivalent"),
    "spy_offence": Row("owned_hostile_scheme_success_chance_add", 20, H),  # +50% -> +10 success chance
    "global_spy_defence": Row("enemy_hostile_scheme_success_chance_add", -25, H),
    "spy_action_cost_modifier": Row("owned_scheme_secrecy_add", -20, H),

    # --- Country: rule. Autonomy -> vassal taxes; governing capacity -> domain limit; unrest-like keys -> opinion.
    "global_autonomy": Row("vassal_tax_contribution_mult", -1, H),
    "governing_capacity": Row("domain_limit", 0.04, H),
    "governing_capacity_modifier": Row("domain_limit", 10, H),
    "harsh_treatment_cost": Row("tyranny_gain_mult", 1, H),
    "stability_cost_modifier": Row("county_opinion_add", -20, H),
    "war_exhaustion": Row("county_opinion_add", -100, H),
    "years_of_nationalism": Row("monthly_county_control_growth_add", -0.1, H),
    # Keys of EU4 event modifiers that a project's on_upgraded adds (read by hand into cannor_hand.py, e.g. Castle
    # Dameris): imperial authority -> prestige (+0.25 -> +0.5/month), favours -> vassal opinion (+0.1 -> +4).
    "free_city_imperial_authority": Row("monthly_prestige", 2, H),
    "monthly_favor_modifier": Row("vassal_opinion", 40, H),
    "max_absolutism": Drop(_ABSOLUTISM),
    "yearly_absolutism": Drop(_ABSOLUTISM),
    "max_revolutionary_zeal": Drop(_ABSOLUTISM),
    "possible_policy": Drop("EU4 policies; no CK3 equivalent"),
    "state_maintenance_modifier": Drop("EU4 states; no CK3 equivalent"),

    # --- Country: estates. Loyalty of a CK3-like group -> that group's opinion (+0.1 -> +5); magic estate -> magic.
    "all_estate_loyalty_equilibrium": Row("vassal_opinion", 50, H),
    "nobles_loyalty_modifier": Row("vassal_opinion", 25, H),
    "castonath_patricians_loyalty_modifier": Row("vassal_opinion", 25, H),  # Castonath's patrician houses
    "church_loyalty_modifier": Row("clergy_opinion", 50, H),
    "mages_loyalty_modifier": Row("monthly_learning_lifestyle_xp_gain_mult", 1, H),
    "mages_influence_modifier": Row("monthly_magic_lifestyle_xp_gain_mult", 2, H),
    "mages_ruler_experience_mod": Row("monthly_magic_lifestyle_xp_gain_mult", 0.5, H),
    "adventurers_loyalty_modifier": Row("knight_effectiveness_mult", 1, H),  # adventurers ~ knights-errant
    "adventurers_influence_modifier": Row("knight_effectiveness_mult", 1, H),
    "burghers_loyalty_modifier": Row("monthly_income_mult", 0.5, H),
    "burghers_influence_modifier": Row("monthly_income_mult", 0.5, H),
    "artificers_loyalty_modifier": Row("monthly_learning_lifestyle_xp_gain_mult", 0.5, H),  # artificers ~ scholars
    "artificers_influence_modifier": Row("monthly_learning_lifestyle_xp_gain_mult", 0.5, H),
    "artificers_capacity": Drop(_ESTATES),
    "vampires_loyalty_modifier": Drop(_ESTATES),
    "all_estate_possible_privileges": Drop(_ESTATES),
    "estate_interaction_cooldown_modifier": Drop(_ESTATES),

    # --- Country: monarch power, ideas, technology -> lifestyle XP (cultural_head_* keys only work for the
    # cultural head, so not used). One-category tech cost -10% -> +10% learning XP; all-tech cost -5% -> +10%.
    "monarch_military_power": Row("martial", 1, H),
    "all_power_cost": Row("monthly_lifestyle_xp_gain_mult", -2, H),
    "idea_cost": Row("monthly_lifestyle_xp_gain_mult", -1, H),
    "technology_cost": Row("monthly_learning_lifestyle_xp_gain_mult", -2, H),
    "adm_tech_cost_modifier": Row("monthly_learning_lifestyle_xp_gain_mult", -1, H),
    "dip_tech_cost_modifier": Row("monthly_learning_lifestyle_xp_gain_mult", -1, H),
    "mil_tech_cost_modifier": Row("monthly_learning_lifestyle_xp_gain_mult", -1, H),
    "innovativeness_gain": Row("monthly_learning_lifestyle_xp_gain_mult", 0.5, H),
    "advisor_cost": Drop(_ADVISORS),
    "adm_advisor_cost": Drop(_ADVISORS),
    "dip_advisor_cost": Drop(_ADVISORS),
    "mil_advisor_cost": Drop(_ADVISORS),
    "advisor_pool": Drop(_ADVISORS),

    # --- Country: economy. National tax 1:1 on the domain; trade efficiency/power -> income at half or less.
    "global_tax_modifier": Row("domain_tax_mult", 1, H),
    "global_trade_goods_size_modifier": Row("domain_tax_mult", 0.5, H),
    "trade_efficiency": Row("monthly_income_mult", 0.5, H),
    "global_trade_power": Row("monthly_income_mult", 0.5, H),
    "global_foreign_trade_power": Row("monthly_income_mult", 0.25, H),
    "global_ship_trade_power": Row("monthly_income_mult", 0.25, H),
    "caravan_power": Row("monthly_income_mult", 0.2, H),
    "build_cost": Row("build_gold_cost", 1, H),
    "build_time": Row("build_speed", 1, H),
    "center_of_trade_upgrade_cost": Drop(_TRADE),
    "embargo_efficiency": Drop(_TRADE),
    "merchants": Drop(_TRADE),
    "placed_merchant_power": Drop(_TRADE),
    "range": Drop(_TRADE),
    "global_colonial_growth": Drop(_TRADE),
    "global_tariffs": Drop(_TRADE),
    "treasure_fleet_income": Drop(_TRADE),
    "reduced_liberty_desire_on_other_continent": Drop(_TRADE),
    "interest": Drop("EU4 loans; CK3 has no interest"),
    "monthly_gold_inflation_modifier": Drop("EU4 inflation; no CK3 equivalent"),
    # Middle Dwarovar (Dwarven Monuments): inflation and corruption have no CK3 system; upgrade cost -> build cost
    "inflation_reduction": Drop("EU4 inflation; no CK3 equivalent"),
    "inflation_action_cost": Drop("EU4 inflation; no CK3 equivalent"),
    "yearly_corruption": Drop("EU4 corruption; no CK3 equivalent"),
    "great_project_upgrade_cost": Row("build_gold_cost", 1, H),  # -10% monument upgrades -> -10% building cost
    "meritocracy": Drop(_GOVERNMENT),
    # Subjects: +50%..150% vassal force limit -> +5..15% vassal levies; -10..30% subject liberty -> +5..15 opinion
    "vassal_forcelimit_bonus": Row("vassal_levy_contribution_mult", 0.1, H),
    "liberty_desire_from_subject_development": Row("vassal_opinion", -50, H),

    # --- Country: army size and upkeep. Force limit/manpower -> levies; regiment costs -> MaA upkeep (1:1).
    "land_forcelimit_modifier": Row("levy_size", 1, H),
    "manpower_in_accepted_culture_provinces": Row("levy_size", 0.5, H),
    "manpower_recovery_speed": Row("levy_reinforcement_rate", 1, H),
    "recover_army_morale_speed": Row("levy_reinforcement_rate", 1, H),
    "reserves_organisation": Row("levy_toughness", 30, H),  # +10% -> +3 (vanilla uses +-2..5)
    "global_regiment_cost": Row("men_at_arms_maintenance", 1, H),
    "infantry_cost": Row("heavy_infantry_maintenance_mult", 1, H),
    "mercenary_cost": Row("mercenary_hire_cost_mult", 1, H),
    "fort_maintenance_modifier": Row("army_maintenance_mult", 0.25, H),
    "garrison_size": Row("garrison_size", 1, H),
    "global_supply_limit_modifier": Row("supply_limit_mult", 1, H),
    "land_attrition": Row("provisions_use_mult", 1, H),
    "hostile_attrition": Row("defender_advantage", 2, H),
    "merc_leader_army_tradition": Drop("EU4 mercenary leaders; no CK3 equivalent"),
    "allowed_marine_fraction": Drop("EU4 marines; no CK3 equivalent"),
    "allowed_rajput_fraction": Drop("EU4 special regiments; no CK3 equivalent"),
    "province_warscore_cost": Drop("EU4 peace deals; no CK3 equivalent"),

    # --- Country: army quality. Drill/professionalism -> MaA stats; tradition -> martial XP; leaders -> knights.
    "drill_gain_modifier": Row("maa_toughness_mult", 0.2, H),
    "yearly_army_professionalism": Row("maa_damage_mult", 20, H),
    "fire_damage_received": Row("maa_toughness_mult", -1, H),
    "shock_damage_received": Row("maa_toughness_mult", -1, H),
    "army_tradition": Row("monthly_martial_lifestyle_xp_gain_mult", 0.1, H),
    "army_tradition_decay": Row("monthly_martial_lifestyle_xp_gain_mult", -5, H),
    "army_tradition_from_battle": Row("accolade_glory_gain_mult", 0.2, H),
    "free_land_leader_pool": Row("knight_limit", 1, H),
    "free_leader_pool": Row("knight_limit", 1, H),
    "leader_land_manuever": Row("advantage", 2, H),
    "max_general_maneuver": Row("advantage", 1, H),
    "movement_speed": Row("movement_speed", 1, H),
    "siege_blockade_progress": Row("siege_phase_time", -0.1, H),
    "loot_amount": Row("max_loot_mult", 0.25, H),
    "privateer_efficiency": Row("raid_speed", 1, H),
    # Unit types: EU4 cavalry -> heavy cavalry, fire -> archers, shock -> heavy infantry (1:1 percentages).
    "cavalry_power": Row("heavy_cavalry_damage_mult", 1, H),
    "cavalry_shock": Row("heavy_cavalry_damage_mult", 1, H),
    "cavalry_flanking": Row("light_cavalry_pursuit_mult", 0.4, H),
    "cav_to_inf_ratio": Row("heavy_cavalry_max_size_add", 4, H),
    "infantry_fire": Row("archers_damage_mult", 1, H),
    "infantry_shock": Row("heavy_infantry_damage_mult", 1, H),
    "admiral_cost": Drop("EU4 admirals; CK3 has no navies"),
    "admiral_skill_gain_modifier": Drop("EU4 admirals; CK3 has no navies"),

    # --- Country: navy. CK3 has only embarkation and sea movement: fleet size/cost -> embarkation, power -> speed.
    "naval_forcelimit_modifier": Row("embarkation_cost_mult", -1, H),
    "global_sailors_modifier": Row("embarkation_cost_mult", -1, H),
    "sailors_recovery_speed": Row("embarkation_cost_mult", -1, H),
    "heavy_ship_cost": Row("embarkation_cost_mult", 1, H),
    "naval_morale": Row("naval_movement_speed_mult", 1, H),
    "galley_power": Row("naval_movement_speed_mult", 1, H),
    "heavy_ship_power": Row("naval_movement_speed_mult", 1, H),
    "light_ship_power": Row("naval_movement_speed_mult", 1, H),
    "naval_attrition": Row("naval_movement_speed_mult", -0.5, H),
    "transport_attrition": Row("naval_movement_speed_mult", -0.5, H),
    "heavy_ship_hull_size_modifier": Drop(_SHIPS),
    "ship_durability": Drop(_SHIPS),
    "capture_ship_chance": Drop(_SHIPS),
    "flagship_morale": Drop(_SHIPS),
    "max_flagships": Drop(_SHIPS),
    "number_of_cannons_flagship_modifier": Drop(_SHIPS),
}


# One-offs reward the barony holder, who also gets the building's character_modifier (vanilla building
# on_complete uses `barony.holder`, e.g. 00_castle_buildings.txt).
def _courtier(skill, education, *, extra_trait=None, female_chance="50"):
    """create_character of a skilled courtier at the court of the holder (root = the monument's province)."""
    extra = f" trait = {extra_trait}" if extra_trait else ""
    return (
        "barony.holder = { save_scope_as = aov_monument_patron "
        "create_character = { employer = scope:aov_monument_patron "
        "culture = scope:aov_monument_patron.culture faith = scope:aov_monument_patron.faith "
        f"age = {{ 30 50 }} gender_female_chance = {female_chance} dynasty = none "
        f"trait = education_{education}_3{extra} {skill} = {{ 14 18 }} random_traits = yes }} }}"
    )


def _gain(currency, amount):
    return f"barony.holder = {{ add_{currency} = {amount} }}"


_LOYALTY = r"add_estate_loyalty\s*=\s*\{{\s*estate\s*=\s*{estate}\s+loyalty\s*=\s*{n}\b"
_ADVISOR = r"define_advisor\s*=\s*\{{[^}}]*type\s*=\s*(?:{types})\b"

ONE_OFF = [
    # Court mage -> a learned mage courtier (Anbennar magical affinity). EU4 skill 3 ~ CK3 skill 14-18.
    (_ADVISOR.format(types="court_mage"),
     _courtier("learning", "learning", extra_trait="magical_affinity_2", female_chance=50)),
    # Other EU4 advisors -> a courtier skilled in the matching CK3 skill.
    (_ADVISOR.format(types="philosopher|natural_scientist"), _courtier("learning", "learning")),
    (_ADVISOR.format(types="trader|treasurer"), _courtier("stewardship", "stewardship")),
    (_ADVISOR.format(types="spymaster"), _courtier("intrigue", "intrigue")),
    (_ADVISOR.format(types="commandant|army_organiser|army_reformer|grand_captain|navigator"),
     _courtier("martial", "martial")),
    # A named EU4 general -> a martial courtier (a commander for the holder).
    (r"define_general\s*=", _courtier("martial", "martial")),
    # Estate loyalty -> prestige (church: piety) = 50 x loyalty / 5.
    *[(_LOYALTY.format(estate="estate_church", n=n), _gain("piety", 10 * n)) for n in (5, 10, 15, 20, 30)],
    *[(_LOYALTY.format(estate=r"\w+", n=n), _gain("prestige", 10 * n)) for n in (5, 10, 15, 20, 30)],
    # EU4 prestige (0-100 scale) x10; splendor at half as prestige; treasury x COST as gold.
    *[(rf"add_prestige\s*=\s*{n}\b", _gain("prestige", 10 * n)) for n in (10, 15, 25)],
    *[(rf"add_splendor\s*=\s*{n}\b", _gain("prestige", n // 2)) for n in (150, 300, 450)],
    *[(rf"add_treasury\s*=\s*{n}\b", _gain("gold", round(n * COST))) for n in (100, 500)],
    # Dropped: free EU4 buildings, base development, timed country modifiers, trade/mercantilism changes.
    (r"add_building_construction\s*=", None),
    (r"add_base_(?:production|tax|manpower)\s*=", None),
    (r"add_country_modifier\s*=", None),
]

# EU4 scripted triggers used in gates: regex -> the gate atoms the trigger checks (each mapped through CULTURES),
# or None = a requirement with no CK3 equivalent, kept as a note. From Dwarven Monuments'
# common/scripted_triggers/dwarven_monuments_scripted_triggers.txt (its province-modifier branches are dropped).
SCRIPTED_GATES = {
    r"\bdwarven_monuments_has_acceptable_culture_or_race\s*=\s*yes": (
        "culture_group:dwarven", "culture_group:goblin", "culture_group:kobold", "culture_group:orcish",
        "culture:mossmouth_ogre"),
    r"\bdwarven_monuments_has_dig_level_\d+_or_higher\s*=\s*yes": None,  # hold dig level: no CK3 hold digging yet
}

CULTURES = {
    # Cultures Anbennar CK3 also has under the same key.
    "culture:castanorian": "culture = culture:castanorian",
    "culture:black_castanorian": "culture = culture:black_castanorian",
    "culture:white_reachman": "culture = culture:white_reachman",
    "culture:blue_reachman": "culture = culture:blue_reachman",
    "culture:vertesker": "culture = culture:vertesker",
    "culture:roilsardi": "culture = culture:roilsardi",
    "culture:wexonard": "culture = culture:wexonard",
    "culture:gawedi": "culture = culture:gawedi",
    "culture:marrodic": "culture = culture:marrodic",
    "culture:esmari": "culture = culture:esmari",
    "culture:reverian": "culture = culture:reverian",
    "culture:ourdi": "culture = culture:ourdi",
    "culture:dostanorian": "culture = culture:dostanorian",
    "culture:imperial_halfling": "culture = culture:imperial_halfling",
    "culture:visfoot_halfling": "culture = culture:visfoot_halfling",
    "culture:hapremiti": "culture = culture:hapremiti",
    # Same culture, CK3 spelling (EU4 race nouns -> CK3 adjectives; EU4's later "_r" reachman split).
    "culture:moon_elf": "culture = culture:moon_elvish",
    "culture:silver_dwarf": "culture = culture:silver_dwarvish",
    "culture:stone_dwarf": "culture = culture:stone_dwarvish",
    "culture:imperial_gnome": "culture = culture:imperial_gnomish",
    "culture:creek_gnome": "culture = culture:creek_gnomish",
    "culture:jarnklo_harpy": "culture = culture:jarnklo",
    "culture:white_reachman_r": "culture = culture:white_reachman",
    "culture:blue_reachman_r": "culture = culture:blue_reachman",
    "culture:black_demesner": "culture = culture:black_castanorian",  # the Black Demesne's Castanorian heirs
    # EU4 cultures that do not exist yet in 1022 -> their CK3 heritage (EU4 culture group).
    "culture:creekfoot_halfling": "culture = { has_cultural_pillar = heritage_halfling }",
    "culture:newfoot_halfling": "culture = { has_cultural_pillar = heritage_halfling }",
    "culture:eclipse_elf": "culture = { has_cultural_pillar = heritage_elven }",
    "culture:iron_dwarf": "culture = { has_cultural_pillar = heritage_dwarven }",
    "culture:elikhander": "culture = { has_cultural_pillar = heritage_escanni }",
    "culture:gerudian_reachman": "culture = { has_cultural_pillar = heritage_gerudian }",
    "culture:skamvin": "culture = { has_cultural_pillar = heritage_gerudian }",
    "culture:itrahuresi": "culture = { has_cultural_pillar = heritage_bulwari }",
    "culture:flamemarked_gnoll": "culture = { has_cultural_pillar = heritage_gnollish }",
    "culture:hill_gnoll": "culture = { has_cultural_pillar = heritage_gnollish }",
    # No goblins, orcs, half-orcs or trolls in Anbennar CK3's Cannor: ignored.
    "culture:city_goblin": None,
    "culture:common_goblin": None,
    "culture:forest_goblin": None,
    "culture:orvitzyen_goblin": None,
    "culture:gray_orc": None,
    "culture:grombar_orc": None,
    "culture:grombar_half_orc": None,
    "culture:fjord_troll": None,
    # Culture groups -> heritages (EU4 "anbennarian" is CK3's Damesheader heritage).
    "culture_group:anbennarian": "culture = { has_cultural_pillar = heritage_damesheader }",
    "culture_group:alenic": "culture = { has_cultural_pillar = heritage_alenic }",
    "culture_group:businori": "culture = { has_cultural_pillar = heritage_businori }",
    "culture_group:dostanorian_g": "culture = { has_cultural_pillar = heritage_dostanorian }",
    "culture_group:dwarven": "culture = { has_cultural_pillar = heritage_dwarven }",
    "culture_group:escanni": "culture = { has_cultural_pillar = heritage_escanni }",
    "culture_group:gerudian": "culture = { has_cultural_pillar = heritage_gerudian }",
    "culture_group:gnomish": "culture = { has_cultural_pillar = heritage_gnomish }",
    "culture_group:halfling": "culture = { has_cultural_pillar = heritage_halfling }",
    "culture_group:kheteratan": "culture = { has_cultural_pillar = heritage_kheteratan }",
    "culture_group:kobold": "culture = { has_cultural_pillar = heritage_kobold }",
    "culture_group:lencori": "culture = { has_cultural_pillar = heritage_lencori }",
    # EU4's reachman group (blue/white reachmen, moormen) is split over two CK3 heritages: name the cultures.
    "culture_group:reachman": (
        "OR = { culture = culture:blue_reachman culture = culture:white_reachman culture = culture:moorman }"),
    "culture_group:goblin": None,  # no goblin cultures in CK3
    "culture_group:orcish": None,  # no orc cultures in CK3
    "culture:mossmouth_ogre": None,  # no ogre cultures in CK3
    "culture_group:centaur": None,  # no centaur cultures in CK3
    # Religions -> CK3 religion, or the CK3 faith where EU4's religion is a single faith.
    "religion_group:cannorian": "faith.religion = religion:cannorian_pantheon_religion",
    "religion_group:khetist": "faith.religion = religion:khetism_religion",
    "religion:the_thought": "faith.religion = religion:the_thought_religion",
    "religion:skaldhyrric_faith": "faith = faith:skaldhyrric_faith",
    "religion:elven_forebears": "faith = faith:elven_forebears",
    "religion:dalcabba": "faith = faith:elikhetist",  # Khetism revering Castellos ~ CK3's Elikhetism
    # EU4 tags and country flags name EU4 countries/events: ignored.
    "tag:A19": None,
    "tag:A24": None,
    "tag:A25": None,
    "tag:A30": None,
    "tag:A40": None,
    "tag:A46": None,
    "tag:A49": None,
    "tag:A62": None,
    "tag:A80": None,
    "tag:B33": None,
    "tag:B54": None,
    "tag:U16": None,
    "tag:Z01": None,
    "tag:Z07": None,
    "tag:Z36": None,
    "tag:Z88": None,
    "tag:Z97": None,
    "flag:bladeskeep_monument_is_worthy": None,
    "flag:has_dismantled_the_hre": None,
    "flag:no_longer_monstrous": None,
    "flag:semi_monstrous": None,
}

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
