"""Data for tools/build_racial_traditions.py: unique traditions for racial cultures, their men-at-arms, and the extra
traditions given to thin cultures at game start (docs/systems/racial-traditions.md).

Each tradition is written from EU4 Anbennar's ideas for the realm or culture group named in its `eu4` field.
"""

# Gates. ("lineage", trigger): a scripted trigger in the culture scope (aov_racial_maa_triggers.txt).
# ("culture", key): the culture itself or any culture descended from it.
MOON = ("lineage", "aov_moon_elven_lineage_trigger")
WOOD = ("lineage", "aov_wood_elven_lineage_trigger")


def culture(key):
    return ("culture", key)


# Terrain sets: terrain -> fraction of base damage and toughness (the racial armies convention).
WOOD_TERRAIN = {"forest": 0.5, "taiga": 0.5, "jungle": 0.5, "wetlands": 0.5, "desert": -0.2, "drylands": -0.2,
                "plains": -0.2}
DESERT_TERRAIN = {"desert": 0.3, "drylands": 0.3, "desert_mountains": 0.2, "oasis": 0.2, "jungle": -0.2,
                  "forest": -0.2}

# key: name, description, heritage (is_shown), gate (can_pick), category, layers (background, pattern, icon),
# character, culture and county modifiers, parameters, eu4 source. `units` lists the new units it unlocks.
TRADITIONS = {
    # --- Elves -----------------------------------------------------------------------------------------------------
    "tradition_elven_high_culture": dict(
        name="Elven High Culture", heritage="heritage_elven", gate=MOON, category="societal",
        layers=("diplo", "western", "crown.dds"), eu4="moon elf ideas: Elven High Culture, Mercenaries of Men",
        character={"monthly_prestige_gain_mult": 0.15, "diplomacy": 1, "mercenary_hire_cost_mult": -0.15},
        desc="The moon elves remember the courts of Aelantir and hold to their manners still. Human kings seek their "
             "counsel, and human sellswords take their silver gladly."),
    "tradition_ranger_art": dict(
        name="The Ranger Art", heritage="heritage_elven", gate=WOOD, category="combat",
        layers=("martial", "western", "forest.dds"), eu4="wood elf ideas: One With Nature, The Ranger Art",
        character={"movement_speed": 0.1, "supply_duration": 0.25, "forest_advantage": 4, "taiga_advantage": 4},
        desc="Since the retreat into the Deepwoods every wood elf learns to walk the forest unseen, live off what it "
             "gives and strike from where the enemy least expects."),
    "tradition_iorels_accords": dict(
        name="Ioriel's Accords", heritage="heritage_elven", gate=culture("redglader"), category="realm",
        layers=("diplo", "western", "diplomat.dds"), eu4="Redglades ideas: Ioriel's Accords, Voice of the Rose Throne",
        character={"different_culture_opinion": 10}, culture={"cultural_acceptance_gain_mult": 0.25},
        units=("aov_erhetana_sentinels",),
        desc="In 1001 Ioriel Redrose made peace with Lorent, and the Redglades have lived by treaty ever since. Its "
             "Érhetana Sentinels keep the thorned glades for those who forget it."),
    "tradition_forlorn_vale": dict(
        name="Defense of the Forlorn Vale", heritage="heritage_elven", gate=culture("ibevari"), category="combat",
        layers=("martial", "western", "shield.dds"),
        eu4="Ibevar ideas: Defense of the Forlorn Vale, The Blaiddscal, Elven-Eyed Archers",
        character={"defender_advantage": 4, "knight_effectiveness_mult": 0.15, "archers_damage_mult": 0.1},
        units=("aov_blaiddscal_blademasters",),
        desc="Ibevar was carved out of a vale no one else wanted and has been defended ever since. The Blaiddscal "
             "academy trains its blademasters, and every Ibevari learns the bow."),
    "tradition_elves_of_the_reach": dict(
        name="Elves of the Reach", heritage="heritage_elven", gate=culture("celmaldorian"), category="societal",
        layers=("steward", "western", "ship.dds"),
        eu4="Celmaldor ideas: Maldorian the Navigator, Elves of the Reach, Escorts of the Trade Princes",
        character={"diplomacy": 1, "embarkation_cost_mult": -0.3, "naval_movement_speed_mult": 0.15},
        units=("aov_trade_prince_escorts",),
        desc="Maldorian the Navigator led his people to the cold coasts of the Reach, where they trade with every "
             "port and hire out their spears to escort the merchant princes."),
    "tradition_remnant_fleet": dict(
        name="Lessons of the Remnant Fleet", heritage="heritage_elven", gate=culture("venaili"), category="societal",
        layers=("steward", "western", "boat.dds"),
        eu4="Venáil ideas: Lessons of the Remnant Fleet, Venáili Arks, Elves Around the Globe",
        character={"embarkation_cost_mult": -0.4, "naval_movement_speed_mult": 0.2, "diplomatic_range_mult": 0.2},
        units=("aov_remnant_fleet_marines",),
        desc="The Venáili never forgot the fleet that carried the elves across the sea. Their arks are the finest "
             "afloat, and their marines fight as well on a heaving deck as on a beach."),
    "tradition_verdant_pact": dict(
        name="The Verdant Pact", heritage="heritage_elven", gate=culture("lake_elvish"), category="realm",
        layers=("diplo", "western", "council.dds"), eu4="Lake Grove ideas: The Verdant Pact, Elynáile the Eternal City",
        character={"vassal_limit": 5, "vassal_levy_contribution_mult": 0.1, "vassal_tax_contribution_mult": 0.1},
        units=("aov_oak_oath_guard",),
        desc="Salla Elyn rules from Elynáile, the Eternal City, by the Verdant Pact: the lesser clans keep their "
             "groves, and in return they answer the conclave's call."),
    "tradition_never_to_fall": dict(
        name="Never to Fall", heritage="heritage_elven", gate=culture("mountain_elvish"), category="combat",
        layers=("martial", "western", "mountain.dds"), eu4="Mountain Grove ideas: Never to Fall, Legacy of the Speardancer",
        character={"garrison_size": 0.3, "hills_advantage": 4, "mountains_advantage": 4},
        units=("aov_speardancers",),
        desc="Ciranmyna has never fallen, and Salla Myna means to keep it so. Its warriors still dance with the spear "
             "as the Speardancer taught them."),
    "tradition_closest_to_the_fey": dict(
        name="Closest to the Fey", heritage="heritage_elven", gate=culture("thorn_elvish"), category="ritual",
        layers=("learning", "western", "temple.dds"), eu4="Thorn Grove ideas: Closest to the Fey, First Grove of Druids",
        character={"monthly_piety_gain_mult": 0.15, "learning": 1, "defender_advantage": 2},
        parameters=("aov_unlock_maa_thorn_druids",),
        desc="Salla Drennen lives nearest the fey and raised the first druids of the Deepwoods. Its druids still "
             "march with its warriors, and the thorns rise against its enemies."),
    "tradition_bone_struggle": dict(
        name="The Bone Struggle", heritage="heritage_elven", gate=culture("bone_elvish"), category="combat",
        layers=("intrigue", "western", "hunter.dds"),
        eu4="Bone Grove ideas: The Bone Struggle, Horrors of the Bone Grove, Bonecoated Infiltrators",
        character={"owned_hostile_scheme_success_chance_add": 10, "siege_phase_time": -0.1,
                   "hostile_county_attrition": 0.1},
        units=("aov_bonecoated_infiltrators",),
        desc="Salla Cenág survived the Bone Struggle by learning to fight unseen. Its scouts wear the bones of what "
             "they have killed and slip past any wall."),
    "tradition_great_beast_hunters": dict(
        name="Great Beast Hunters", heritage="heritage_elven", gate=culture("hunter_elvish"), category="combat",
        layers=("martial", "western", "rider.dds"), eu4="Hunter Grove ideas: Great Beast Hunters, One With The Stag",
        character={"light_cavalry_damage_mult": 0.15, "light_cavalry_toughness_mult": 0.15,
                   "light_cavalry_maintenance_mult": -0.2, "monthly_prestige_gain_mult": 0.1},
        desc="Salla Fealgarn hunts the great beasts of the Deepwoods from the backs of its stags. Its Hyodeth riders "
             "are the best mounted, best fed and most feared in the forest."),
    "tradition_every_elf_a_botanist": dict(
        name="Every Elf a Botanist", heritage="heritage_elven", gate=culture("flower_elvish"), category="societal",
        layers=("steward", "western", "garden_architects.dds"),
        eu4="Flower Grove ideas: Every Elf a Botanist, And Every Botanist a Merchant, Poisons and Potions",
        character={"domain_tax_mult": 0.1, "health": 0.25, "owned_hostile_scheme_success_chance_add": 5},
        units=("aov_scotha_poison_archers",),
        desc="Salla Scotha knows every herb of the Deepwoods: which heals, which sells, and which kills. Its archers "
             "dip their arrows in the last kind."),
    "tradition_peace_and_abundance": dict(
        name="A Grove of Peace and Abundance", heritage="heritage_elven", gate=culture("river_elvish"),
        category="societal", layers=("steward", "western", "food.dds"),
        eu4="River Grove ideas: A Grove of Peace and Abundance, Satyr Communities, First Friends of the Fey",
        character={"stress_gain_mult": -0.15}, county={"development_growth_factor": 0.15, "county_opinion_add": 5},
        desc="Salla Ahain shares its springs with satyrs and fey, and its people want for nothing. Few wood elves "
             "are as content, and few groves as rich."),
    "tradition_greatest_archers": dict(
        name="Clan of the Greatest Archers", heritage="heritage_elven", gate=culture("arrow_elvish"), category="combat",
        layers=("martial", "western", "bow.dds"),
        eu4="Arrow Grove ideas: Clan of the Greatest Archers, Acrobats by Necessity, Finest Carpenters",
        character={"archers_damage_mult": 0.15, "archers_toughness_mult": 0.1, "build_gold_cost": -0.1},
        desc="Salla Ayeth gave the Ayethi their name. Its archers loose from the high branches, and its carpenters "
             "build in living wood."),
    "tradition_shadow_grove": dict(
        name="The Shadow Grove", heritage="heritage_elven", gate=culture("shadow_elvish"), category="societal",
        layers=("intrigue", "western", "palace_politics.dds"),
        eu4="Shadow Grove ideas: The Shadow Grove, Home of the Ashentree Fey, The Witch of the East",
        character={"enemy_hostile_scheme_success_chance_add": -10, "intrigue": 1, "dread_gain_mult": 0.15},
        units=("aov_witchwood_stalkers",),
        desc="Salla Ghúl lives in the shade of the Ashentree fey and the Witch of the East. Those who come to spy on "
             "it are rarely seen again."),
    # --- Dwarves ---------------------------------------------------------------------------------------------------
    "tradition_our_rubies": dict(
        name="Our Rubies", heritage="heritage_dwarven", gate=culture("ruby_dwarvish"), category="societal",
        layers=("steward", "western", "crown.dds"), eu4="Rubyhold ideas: Our Rubies, Rose Party Siege Engineers",
        character={"monthly_prestige_gain_mult": 0.1, "domain_tax_mult": 0.1, "siege_phase_time": -0.1},
        parameters=("aov_unlock_maa_grudgebearers",),
        desc="The rubies of Rubyhold buy friends in Lencenor and pay the engineers who take the walls of those who "
             "will not be friends. Its Grudgebearers remember the rest."),
    "tradition_silverforge": dict(
        name="Silver Army Engineers", heritage="heritage_dwarven", gate=culture("silver_dwarvish"), category="combat",
        layers=("martial", "western", "tools.dds"),
        eu4="Silverforge ideas: Silver Army Engineer Corps, Imperial Center of Balgar Worship",
        character={"siege_phase_time": -0.15, "stewardship": 1, "siege_weapon_maintenance_mult": -0.2},
        parameters=("aov_unlock_maa_silverforge_engineers",),
        desc="Silverforge's engineers cut the greatest mines in Escann and turn the same skill to war. Their siege "
             "engines go up faster and cost less than anyone else's."),
    "tradition_solid_as_stone": dict(
        name="Solid as Stone", heritage="heritage_dwarven", gate=culture("stone_dwarvish"), category="combat",
        layers=("martial", "western", "wall.dds"), eu4="dwarven ideas: Solid as Stone, Masters of Defense",
        character={"hard_casualty_modifier": -0.1, "defender_advantage": 3, "pikemen_toughness_mult": 0.1},
        parameters=("aov_unlock_maa_tortoise_formation",),
        desc="The stone dwarves count every life and spend none lightly. Behind their tortoise of shields they "
             "outlast foes who outnumber them ten to one."),
    "tradition_giantbane": dict(
        name="Giantbane", heritage="heritage_dwarven", gate=culture("agate_dwarvish"), category="combat",
        layers=("martial", "western", "fight.dds"), eu4="Khugdihr: the Giantbane crossbows",
        character={"archers_damage_mult": 0.1, "knight_effectiveness_mult": 0.1, "prowess": 2},
        parameters=("aov_unlock_maa_giantbane_crossbows",),
        desc="Khugdihr has fallen to orcs, dragons and giants, and risen each time. The agate dwarves train to kill "
             "the largest thing on the field first."),
    "tradition_uthojdihr_seafarers": dict(
        name="Uthojdihr Seafarers", heritage="heritage_dwarven", gate=culture("copper_dwarvish"), category="societal",
        layers=("steward", "western", "ship.dds"), eu4="Ovdal Tûngr: the Uthojdihr clan",
        character={"embarkation_cost_mult": -0.4, "naval_movement_speed_mult": 0.15, "wetlands_advantage": 4},
        parameters=("aov_unlock_maa_uthojdihr_marines",),
        desc="Unlike other dwarves, the copper dwarves of Ovdal Tûngr took to the sea. They sail the Bahar coast and "
             "fight as well in its marshes as in their halls."),
    "tradition_citrine_code": dict(
        name="The Citrine Code", heritage="heritage_dwarven", gate=culture("citrine_dwarvish"), category="realm",
        layers=("diplo", "mena", "diplomacy.dds"),
        eu4="Seghdihr ideas: The Citrine Code, Bulwari-Dwarf Treaty of Cooperation, Origin of the Seg Band",
        character={"different_culture_opinion": 10, "diplomacy": 1, "skirmishers_damage_mult": 0.15},
        parameters=("aov_unlock_maa_seg_band_gnollhunters",),
        desc="Seghdihr keeps its word to the Bulwari, and the Seg Band keeps the gnolls from both. Its code binds "
             "every citrine dwarf to honest dealing."),
    "tradition_three_golden_gates": dict(
        name="The Three Golden Gates", heritage="heritage_dwarven", gate=culture("gold_dwarvish"), category="realm",
        layers=("steward", "western", "city.dds"),
        eu4="Verkal Gulan ideas: The Three Golden Gates, Vault Magistrates, Companies of Arm",
        character={"domain_tax_mult": 0.1, "garrison_size": 0.25, "mercenary_hire_cost_mult": -0.15},
        parameters=("aov_unlock_maa_golden_gate_guard",),
        desc="Verkal Gulan guards its vaults behind three golden gates and pays well to keep them shut. No enemy "
             "has passed the Hero's Gate while its guard stood."),
    "tradition_thirteen_stages": dict(
        name="The Thirteen Stages of Enlightenment", heritage="heritage_dwarven", gate=culture("pyrite_dwarvish"),
        category="societal", layers=("learning", "western", "philosopher.dds"),
        eu4="Hehodovar ideas: The Thirteen Stages of Enlightenment, The Work Curse, The Thinkers' Party",
        character={"cultural_head_fascination_mult": 0.15, "build_speed": -0.15, "learning": 1},
        parameters=("aov_unlock_maa_clockwork_bows",),
        desc="Hehodovar's Builders Guild still keeps the learning of Aul-Dwarov alive. Its thinkers invent, its "
             "builders cannot stop working, and its bows tension their own strings."),
    "tradition_dauvek_veker": dict(
        name="The Titanium Orders", heritage="heritage_dwarven", gate=culture("titanium_dwarvish"), category="combat",
        layers=("martial", "western", "warrior_monk.dds"), eu4="Gor Vazumbrog: the Dauvek Veker",
        character={"heavy_infantry_toughness_mult": 0.15, "prowess": 2},
        parameters=("aov_unlock_maa_dauvek_veker",),
        desc="The titanium dwarves join holy orders sworn to hunt what crawls up from the deep. Their penitents "
             "wear the heaviest armour any dwarf can carry."),
    "tradition_copper_road_pact": dict(
        name="The Copper Road Pact", heritage="heritage_dwarven", gate=culture("topaz_dwarvish"), category="combat",
        layers=("martial", "western", "marching_soldiers.dds"),
        eu4="Gor Ozumbrog ideas: The Copper Road Pact, Eastguard of the Middle Dwarovar, When Surrounded All Must Serve",
        character={"movement_speed": 0.15, "garrison_size": 0.2, "defender_advantage": 2},
        parameters=("aov_unlock_maa_copper_road_wardens",),
        desc="By the Copper Road Pact, Gor Ozumbrog keeps the dwarven road open to the east. Its wardens ride every "
             "tunnel of it, and every topaz dwarf stands to defend the hold."),
    "tradition_masons_of_the_deep": dict(
        name="Masons of the Deep", heritage="heritage_dwarven", gate=culture("marble_dwarvish"), category="societal",
        layers=("steward", "western", "artisan.dds"), eu4="dwarven ideas: Master Builders, Dwarven Craftsmanship",
        character={"build_gold_cost": -0.15}, county={"development_growth_factor": 0.1},
        parameters=("aov_unlock_maa_brightbeard_hammers",),
        desc="The marble dwarves carve the finest halls under the mountains. They honour Mhoki Brightbeard, whose "
             "hammer ended a siege of 47 years with one blow."),
    # --- Gnolls ----------------------------------------------------------------------------------------------------
    "tradition_scavengers_and_raiders": dict(
        name="Scavengers and Raiders", heritage="heritage_gnollish", gate=culture("sandfang_gnoll"), category="combat",
        layers=("martial", "mena", "desert.dds"),
        eu4="gnollish ideas: A Race of Scavengers and Raiders, Flesh Eaters",
        character={"raid_speed": 0.25, "max_loot_mult": 0.25, "supply_duration": 0.2},
        units=("aov_hyena_riders",),
        desc="The Sandfang gnolls take what they need from those too weak to keep it. Their hyena riders strike "
             "far from the desert and are gone with the loot before an army can gather."),
    "tradition_tight_leash": dict(
        name="A Tight Leash", heritage="heritage_gnollish", gate=culture("fieldstalker_gnoll"), category="realm",
        layers=("intrigue", "mena", "hostages.dds"), eu4="gnollish ideas: A Tight Leash, Gnollish Slave-Lords, Pack Loyalty",
        character={"dread_gain_mult": 0.2, "monthly_county_control_growth_factor": 0.15,
                   "hostile_county_attrition": 0.1},
        units=("aov_fieldstalker_packs",),
        desc="The Fieldstalkers rule their fields as slave-lords and keep their packs, of hyenas and of subjects, "
             "on a tight leash."),
    # --- Halflings -------------------------------------------------------------------------------------------------
    "tradition_apple_lords": dict(
        name="Apple Lords", heritage="heritage_halfling", gate=culture("ciderfoot_halfling"), category="societal",
        layers=("steward", "western", "farmland.dds"),
        eu4="Appleton ideas: Apple Lords of Appleton, An Apple a Day; Pearview ideas: Wine Poached Pears",
        character={"health": 0.2, "stress_gain_mult": -0.1, "domain_tax_mult": 0.1},
        units=("aov_orchard_bowmen",),
        desc="The ciderfoot halflings grow the best apples and pears in Cannor and drink the best cider. They live "
             "long, worry little and guard their orchards with the bow."),
    "tradition_beggas_two_hands": dict(
        name="Begga's Two Hands", heritage="heritage_halfling", gate=culture("beefoot_halfling"), category="realm",
        layers=("diplo", "western", "greeting.dds"),
        eu4="Beepeck ideas: Begga's Right Hand Gives, Begga's Left Hand Takes, Cathedral of the Last Crust",
        character={"diplomacy": 1, "domain_tax_mult": 0.1, "different_faith_opinion": 10},
        units=("aov_seedoud_marines",),
        desc="Beepeck's right hand gives and its left hand takes, and its merchants welcome any faith that pays. "
             "Its marines keep the harbour open."),
    "tradition_mound_forts": dict(
        name="Mound Forts", heritage="heritage_halfling", gate=culture("bluefoot_halfling"), category="combat",
        layers=("martial", "western", "wall.dds"), eu4="Pearview ideas: A Bluefoot Heart, Mound Forts",
        character={"garrison_size": 0.25, "defender_advantage": 3, "hard_casualty_modifier": -0.1},
        units=("aov_mound_wardens",),
        desc="The bluefoot halflings dig their forts into the hills and hold them with stubborn hearts. Whoever "
             "comes for them has to dig them out."),
    "tradition_small_country_envoys": dict(
        name="Small Country Envoys", heritage="heritage_halfling", gate=culture("visfoot_halfling"),
        category="realm", layers=("diplo", "western", "conversation.dds"), eu4="halfling city keepers and diplomats",
        character={"diplomacy": 1, "different_culture_opinion": 10},
        units=("aov_moot_keepers",),
        desc="The visfoot halflings talk their way out of more wars than they fight. Their moots are guarded by "
             "keepers in good armour, just in case."),
    "tradition_charter_rights": dict(
        name="Charter Rights", heritage="heritage_halfling", gate=culture("imperial_halfling"), category="realm",
        layers=("steward", "western", "quill.dds"), eu4="halfling legalists and republicans",
        character={"stewardship": 1}, county={"county_opinion_add": 5},
        units=("aov_charter_rangers",),
        desc="Every imperial halfling town keeps its charter, and every charter names its rights. Its rangers "
             "patrol the bounds the charters draw."),
    "tradition_hearth_and_harvest": dict(
        name="Hearth and Harvest", heritage="heritage_halfling", gate=culture("moonfoot_halfling"),
        category="societal", layers=("steward", "western", "food.dds"), eu4="halfling farmers",
        character={"levy_reinforcement_rate": 0.15}, county={"development_growth_factor": 0.1},
        units=("aov_hearth_muster",),
        desc="The moonfoot halflings tend their fields and their hearths. When trouble comes the whole village "
             "musters, and goes home to the harvest after."),
}

# Units: the unlocking parameter is aov_unlock_maa_<key without aov_>. Regiment `stack` men with `damage` and
# `toughness` each; costs follow the racial armies pricing (VANILLA_ROLES). Art is RiE's, copied once as aov_rie_<art>.
UNITS = {
    "aov_erhetana_sentinels": dict(
        name="Érhetana Sentinels", type="skirmishers", stack=50, damage=50, toughness=70, pursuit=30, screen=60,
        counters={"heavy_infantry": 1}, terrain={"forest": 0.5, "hills": 0.2}, art="thorn_guard",
        flavor="The sentinels of the Redglades keep its thorned glades. They let pass whoever comes in peace and turn "
               "the thorns themselves against whoever does not."),
    "aov_blaiddscal_blademasters": dict(
        name="Blaiddscal Blademasters", type="heavy_infantry", stack=25, damage=320, toughness=190, pursuit=10,
        screen=10, counters={"pikemen": 1, "skirmishers": 1}, terrain={"hills": 0.2, "forest": 0.2, "mountains": 0.2},
        art="noldor_glaivesmen",
        flavor="Graduates of the Blaiddscal, Ibevar's academy of arms. Each has spent a human lifetime with the "
               "glaive before taking the field."),
    "aov_trade_prince_escorts": dict(
        name="Escorts of the Trade Princes", type="pikemen", stack=50, damage=85, toughness=120,
        counters={"light_cavalry": 1, "heavy_cavalry": 1}, terrain={"wetlands": 0.2, "floodplains": 0.2},
        art="seaward_spearmen",
        flavor="Celmaldor's spearmen guard the merchant princes of the Reach on every road and quay. Their wall of "
               "spears has turned back raiders from the sea and the steppe alike."),
    "aov_remnant_fleet_marines": dict(
        name="Remnant Fleet Marines", type="skirmishers", stack=50, damage=55, toughness=65, pursuit=40, screen=40,
        counters={"heavy_infantry": 1}, terrain={"wetlands": 0.3, "floodplains": 0.3}, art="falathrim_haven_guard",
        flavor="Venáil's marines descend from the warriors of the fleet that carried the elves to Cannor. They land "
               "anywhere a ship can reach and fight before the enemy has formed up."),
    "aov_oak_oath_guard": dict(
        name="Oak Oath Guard", type="heavy_infantry", stack=25, damage=270, toughness=230, pursuit=10, screen=10,
        counters={"pikemen": 1}, terrain=WOOD_TERRAIN, art="galadhrim_sentinels",
        flavor="Sworn by the Oak Oath to Elynáile and its conclave, these guards stand before the Eternal City in "
               "living-wood armour."),
    "aov_speardancers": dict(
        name="Speardancers", type="heavy_infantry", stack=25, damage=300, toughness=200, pursuit=20, screen=20,
        counters={"pikemen": 1, "heavy_cavalry": 1}, terrain={"forest": 0.5, "hills": 0.3, "mountains": 0.3},
        art="galadhrim_warriors",
        flavor="Salla Myna's warriors fight in the style of the Speardancer, whirling through the enemy line where "
               "no shield can follow the point."),
    "aov_bonecoated_infiltrators": dict(
        name="Bonecoated Infiltrators", type="skirmishers", stack=50, damage=55, toughness=65, pursuit=40, screen=60,
        counters={"heavy_infantry": 1, "siege_weapon": 1}, terrain=WOOD_TERRAIN, art="silent_stingers",
        flavor="Salla Cenág's scouts wear the bones of what they have hunted. They slip into camps and over walls "
               "and leave nothing behind but the bones."),
    "aov_scotha_poison_archers": dict(
        name="Scotha Poison Archers", type="archers", stack=50, damage=120, toughness=35, terrain=WOOD_TERRAIN,
        art="druedain_poison_archers",
        flavor="Salla Scotha's archers know which herbs kill and how fast. A graze from one of their arrows is "
               "enough."),
    "aov_witchwood_stalkers": dict(
        name="Witchwood Stalkers", type="archers", stack=50, damage=115, toughness=40, pursuit=20,
        terrain=WOOD_TERRAIN, art="marksmen_of_the_matron",
        flavor="The archers of the Shadow Grove serve the Witch of the East. They are seldom seen, and those who see "
               "them rarely report it."),
    "aov_hyena_riders": dict(
        name="Hyena Riders", type="light_cavalry", stack=100, damage=30, toughness=18, pursuit=40, screen=25,
        counters={"archers": 1}, terrain=DESERT_TERRAIN, art="hunter_orcs_on_fell_wargs",
        flavor="Sandfang gnolls on great hyenas, who range far ahead of the pack and fall on anything that strays "
               "from the column."),
    "aov_fieldstalker_packs": dict(
        name="Fieldstalker Packs", type="skirmishers", stack=100, damage=16, toughness=22, pursuit=20, screen=20,
        counters={"heavy_infantry": 1}, terrain={"plains": 0.2, "farmlands": 0.2, "drylands": 0.2},
        art="caragor_pack",
        flavor="Gnoll packmasters with their hyenas, who stalk the fields of their slaves and run down anyone who "
               "tries to flee them."),
    "aov_orchard_bowmen": dict(
        name="Orchard Bowmen", type="archers", stack=100, damage=24, toughness=10,
        terrain={"farmlands": 0.3, "forest": 0.2}, art="vineyard_bowmen",
        flavor="Ciderfoot halflings who learned the bow guarding their orchards from thieves, and now guard the "
               "rest of the realm the same way."),
    "aov_seedoud_marines": dict(
        name="Seedoud Marines", type="skirmishers", stack=100, damage=12, toughness=18, pursuit=10, screen=15,
        counters={"heavy_infantry": 1}, terrain={"wetlands": 0.3, "floodplains": 0.3}, art="quayside_crossbowmen",
        flavor="Beepeck's harbour watch, armed with crossbows. They guard the quays and sail with its merchant "
               "fleet."),
    "aov_mound_wardens": dict(
        name="Mound Wardens", type="pikemen", stack=100, damage=18, toughness=30,
        counters={"light_cavalry": 1, "heavy_cavalry": 1}, terrain={"hills": 0.3, "farmlands": 0.2},
        art="hobbit_bounders",
        flavor="Bluefoot halflings who hold the mound forts. Behind their earthworks and their spears they will "
               "not be moved."),
    "aov_moot_keepers": dict(
        name="Moot Keepers", type="heavy_infantry", stack=100, damage=28, toughness=22,
        counters={"pikemen": 1}, terrain={"farmlands": 0.2, "plains": 0.2}, art="moot_keepers",
        flavor="The armoured guard of the visfoot moots, who keep order while the talking goes on and settle it "
               "when the talking stops."),
    "aov_charter_rangers": dict(
        name="Charter Rangers", type="archers", stack=100, damage=22, toughness=12,
        terrain={"forest": 0.3, "hills": 0.2}, art="hobbit_hunters",
        flavor="Imperial halfling rangers who walk the bounds of their towns' charters with bow in hand."),
    "aov_hearth_muster": dict(
        name="Hearth Muster", type="skirmishers", stack=100, damage=10, toughness=18, pursuit=5, screen=20,
        counters={"heavy_infantry": 1}, terrain={"farmlands": 0.3, "hills": 0.2}, art="hobbit_muster",
        flavor="The whole moonfoot village, called up with whatever is to hand. Hard to catch and harder to drive "
               "off their own fields."),
}

# Vanilla role per unit type: regiment damage, regiment toughness, buy cost, low upkeep (racial armies pricing).
VANILLA_ROLES = {
    "skirmishers": (1000, 1600, 45, 0.15), "archers": (2500, 1000, 55, 0.2), "pikemen": (2200, 2400, 75, 0.3),
    "heavy_infantry": (3200, 2200, 90, 0.4), "light_cavalry": (2200, 1500, 85, 0.35),
    "heavy_cavalry": (5000, 1750, 200, 0.7),
}

# Culture -> traditions given at game start (if it does not have them yet).
GRANTS = {
    "moon_elvish": ("tradition_elven_high_culture",),
    "wood_elvish": ("tradition_ranger_art",),
    "redglader": ("tradition_elven_high_culture", "tradition_iorels_accords"),
    "ibevari": ("tradition_elven_high_culture", "tradition_forlorn_vale"),
    "celmaldorian": ("tradition_elven_high_culture", "tradition_elves_of_the_reach"),
    "venaili": ("tradition_elven_high_culture", "tradition_remnant_fleet"),
    "lake_elvish": ("tradition_ranger_art", "tradition_verdant_pact"),
    "mountain_elvish": ("tradition_ranger_art", "tradition_never_to_fall"),
    "thorn_elvish": ("tradition_ranger_art", "tradition_closest_to_the_fey"),
    "bone_elvish": ("tradition_ranger_art", "tradition_bone_struggle"),
    "hunter_elvish": ("tradition_ranger_art", "tradition_great_beast_hunters"),
    "flower_elvish": ("tradition_ranger_art", "tradition_every_elf_a_botanist"),
    "river_elvish": ("tradition_ranger_art", "tradition_peace_and_abundance"),
    "arrow_elvish": ("tradition_ranger_art", "tradition_greatest_archers"),
    "shadow_elvish": ("tradition_ranger_art", "tradition_shadow_grove"),
    "ruby_dwarvish": ("tradition_our_rubies",),
    "silver_dwarvish": ("tradition_silverforge",),
    "stone_dwarvish": ("tradition_solid_as_stone",),
    "agate_dwarvish": ("tradition_giantbane",),
    "copper_dwarvish": ("tradition_uthojdihr_seafarers",),
    "citrine_dwarvish": ("tradition_citrine_code",),
    "gold_dwarvish": ("tradition_three_golden_gates",),
    "pyrite_dwarvish": ("tradition_thirteen_stages",),
    "titanium_dwarvish": ("tradition_dauvek_veker",),
    "topaz_dwarvish": ("tradition_copper_road_pact",),
    "marble_dwarvish": ("tradition_masons_of_the_deep",),
    "sandfang_gnoll": ("tradition_scavengers_and_raiders",),
    "fieldstalker_gnoll": ("tradition_tight_leash",),
    "ciderfoot_halfling": ("tradition_apple_lords",),
    "beefoot_halfling": ("tradition_beggas_two_hands",),
    "bluefoot_halfling": ("tradition_mound_forts",),
    "visfoot_halfling": ("tradition_small_country_envoys",),
    "imperial_halfling": ("tradition_charter_rights",),
    "moonfoot_halfling": ("tradition_hearth_and_harvest",),
    # Human cultures with two traditions or fewer: existing traditions that fit them.
    "reverian": ("tradition_seafaring",),
    "shasoura": ("tradition_caravaneers",),
    "taric": ("tradition_winter_warriors",),
}

# Words from Realms in Exile's setting that must not reach our text (the art keeps RiE's file names).
FORBIDDEN_LORE = ("Galadhrim", "Noldor", "Falathrim", "Druedain", "Drúedain", "Hobbit", "Shire", "Gondor", "Mordor",
                  "Middle-earth", "Lothlórien", "Lorien", "Matron", "Caragor", "Warg")
