"""Spells of the eight schools of magic: the single source of truth for tools/build_spells.py.

Adapted from EU4 Anbennar (school, level, icon slot, theme); effects are CK3 terms
(docs/superpowers/specs/2026-10-08-magic-schools-design.md).

slot: EU4 icon slot within the school (1 = level 0, 2-3 = level 1, 4-5 = level 2, 6 = level 3).
type: self | realm | war (castable only at war) | targeted (a character interaction).
modifier: character modifier body on the caster for the duration ("" for one-off spells).
effect: one-off script run on cast, in the caster's scope; targeted spells have the target as scope:recipient.
scales_duration: the duration perks (aov_years_mult_<school>) apply; default = has a lasting modifier.
interaction: targeted spells only; Anbennar's own interaction for Compel and Dominate.
years_mult: an extra script value multiplying the duration (a magic advancement's bonus), or "".
needs_land: castable only by a landed ruler, because it works only on a domain, capital, levies or vassals (landless
adventurer mages, AI included, cannot cast it).
hostile: targeted only; the cast rolls aov_spell_land_chance (common/script_values/aov_spell_tuning.txt) and on a miss
runs aov_spell_missed instead of the modifier and effect. AI mages cast it on rivals and war enemies.
target_trigger: targeted only; a hand-written trigger (with scope:actor and scope:recipient) the interaction requires.
curse: the hand-written modifier this spell puts on its target; Purify removes it (aov_spell_remove_curses).
requires, requires_text: an extra hand-written caster trigger for casting, and the tooltip text for it.
"""


def spell(key, school, level, slot, type, name, desc, flavour, modifier="", effect="", interaction="", scales_duration=None,
          years_mult="", needs_land=False, hostile=False, target_trigger="", curse="", requires="", requires_text=""):
    if type == "targeted" and not interaction:
        interaction = f"aov_spell_{key}_interaction"
    return dict(key=key, school=school, level=level, slot=slot, type=type, name=name, desc=desc, flavour=flavour,
                modifier=modifier, effect=effect, interaction=interaction,
                scales_duration=bool(modifier.strip()) if scales_duration is None else scales_duration,
                years_mult=years_mult, needs_land=needs_land, hostile=hostile, target_trigger=target_trigger,
                curse=curse, requires=requires, requires_text=requires_text)


SPELLS = [
    # Abjuration: protection
    spell("combat_ward", "abjuration", 0, 1, "self", "Combat Ward", "+6 Prowess, +0.25 health",
          "A shimmer of force turns aside the blade that would have found its mark.",
          modifier="prowess = 6\nhealth = 0.25"),
    spell("ward", "abjuration", 1, 2, "targeted", "Ward",
          "Schemes against the target are far less likely to succeed; hostile spells against them often fail",
          "A ward woven about a person frays every plot and curse aimed at them.",
          effect="scope:recipient = { add_character_modifier = { modifier = aov_spell_ward_target years = 2 } }"),
    spell("purify", "abjuration", 1, 3, "self", "Purify", "Cures your wounds, illness and diseases, lifts curses, -20 stress",
          "What festers is burned clean; what was laid upon you is lifted.",
          effect="aov_purify = yes"),
    spell("mass_ward", "abjuration", 2, 4, "realm", "Mass Ward", "+50% garrisons, +6 defensive advantage",
          "Walls hum with layered wards that blunt rams and arrows alike.",
          modifier="garrison_size = 0.5\ndefender_advantage = 6", needs_land=True),
    spell("mage_armor", "abjuration", 2, 5, "war", "Mage Armor", "+25% men-at-arms toughness, tougher levies",
          "Every soldier marches beneath an unseen breastplate.",
          modifier="maa_toughness_mult = 0.25\nlevy_toughness = 2.5"),
    spell("field_of_forbiddance", "abjuration", 3, 6, "realm", "Field of Forbiddance",
          "-30% success for schemes against you; you cannot be targeted by spells; dispels your enemies' war spells",
          "Within the field, hostile magic and hostile intent alike find no purchase.",
          modifier="enemy_hostile_scheme_success_chance_add = -30", effect="aov_field_of_forbiddance = yes"),

    # Conjuration: summoned armies and minions
    spell("summon_familiars", "conjuration", 0, 1, "self", "Summon Familiar", "+3 Intrigue, +3 Learning",
          "A raven at the window, a cat beneath the desk: eyes and ears that answer only to you.",
          modifier="intrigue = 3\nlearning = 3"),
    spell("summon_beasts", "conjuration", 1, 2, "war", "Summon Beasts",
          "A pack of conjured wolves and bears appears at your capital (or where you are, if landless) for the spell's duration",
          "Wolves and bears answer the call and run before the host.",
          effect="aov_summon_beasts = yes", scales_duration=True),
    spell("bound_champion", "conjuration", 1, 3, "self", "Bound Champion",
          "An outsider champion of great prowess serves at your court as a knight, then fades when the spell ends",
          "Bound by name and circle, it fights for you until the binding frays.",
          effect="aov_bound_champion = yes", scales_duration=True),
    spell("summon_elementals", "conjuration", 2, 4, "war", "Summon Elementals",
          "A large army of conjured elementals appears at your capital (or where you are, if landless) for the spell's duration",
          "Stone and flame take shape and march at their summoner's word.",
          effect="aov_summon_elementals = yes", scales_duration=True),
    spell("aid_construction", "conjuration", 2, 5, "realm", "Unseen Servants", "Buildings 40% faster and 25% cheaper",
          "Unseen servants haul stone through the night.",
          modifier="build_speed = -0.4\nbuild_gold_cost = -0.25", needs_land=True),
    spell("planar_gate", "conjuration", 3, 6, "war", "Planar Gate",
          "A great extraplanar army (your bound host, if you have one) marches through a gate for the spell's duration; something else may slip through",
          "The gate opens on another plane, and an army marches out. Not everything that follows it is yours.",
          effect="aov_planar_gate = yes", scales_duration=True),

    # Divination: knowledge
    spell("guidance", "divination", 0, 1, "self", "Guidance", "+3 Learning, +10% lifestyle experience",
          "A whisper of insight at the moment of decision.",
          modifier="learning = 3\nmonthly_lifestyle_xp_gain_mult = 0.1"),
    spell("eye_for_talent", "divination", 1, 2, "self", "Eye for Talent", "A skilled character arrives at your court",
          "The diviner reads the threads of fate and finds the one worth pulling.",
          effect="aov_eye_for_talent = yes"),
    spell("deposit_divination", "divination", 1, 3, "realm", "Deposit Divination",
          "Gold from a newly found deposit, faster development in your capital",
          "Beneath the fields lies wealth no prospector suspected.",
          modifier="character_capital_county_monthly_development_growth_add = 0.2",
          effect="aov_deposit_divination = yes", needs_land=True),
    spell("scry", "divination", 2, 4, "targeted", "Scry", "Reveals one of the target's secrets",
          "In flame and water the diviner sees what was meant to stay hidden.",
          effect="aov_scry_reveal = yes"),
    spell("manipulated_fortune", "divination", 2, 5, "self", "Manipulated Fortune",
          "+10% hostile scheme success, +10% prestige gain",
          "Luck is merely probability the diviner has already read.",
          modifier="owned_hostile_scheme_success_chance_add = 10\nmonthly_prestige_gain_mult = 0.1",
          years_mult="aov_adv_orb_spell_years_mult"),
    spell("foresight", "divination", 3, 6, "self", "Foresight",
          "+8 advantage, schemes against you much easier to discover",
          "No ambush surprises one who has already seen the battle.",
          modifier="advantage = 8\nenemy_scheme_secrecy_add = -30", years_mult="aov_adv_orb_spell_years_mult"),

    # Enchantment: the mind
    spell("enchanting_envoy", "enchantment", 0, 1, "self", "Enchanting Envoy", "+3 Diplomacy",
          "Every word lands softly, every request sounds reasonable.",
          modifier="diplomacy = 3"),
    spell("heartstring", "enchantment", 1, 2, "targeted", "Heartstring", "The target gains +30 opinion of you",
          "The Charm spell makes its target broadly receptive to the caster.",
          effect="scope:recipient = { add_opinion = { target = root modifier = aov_charmed_opinion years = 2 } }"),
    spell("command_animals", "enchantment", 1, 3, "war", "Command Animals", "+15% army movement, +2 advantage",
          "Hounds scout the road and hawks watch the hills.",
          modifier="movement_speed = 0.15\nadvantage = 2"),
    spell("thoughtweave", "enchantment", 2, 4, "targeted", "Thoughtweave", "Compel the target to act as you wish",
          "Thoughts can be woven like thread, if one has the patience.",
          interaction="start_compel_interaction"),
    spell("enchanting_embassy", "enchantment", 2, 5, "realm", "Enchanting Embassy", "+15 vassal opinion, +5 general opinion",
          "A court perfumed with charm is a court at peace.",
          modifier="vassal_opinion = 15\ngeneral_opinion = 5", needs_land=True),
    spell("dominate_to_surrender", "enchantment", 3, 6, "targeted", "Dominate to Surrender",
          "Bend the target's will to yours",
          "The strongest enchantments leave the victim certain the choice was their own.",
          interaction="start_dominate_interaction"),

    # Evocation: war magic
    spell("fireball", "evocation", 0, 1, "self", "Fireball", "+6 Prowess",
          "The oldest argument of the battle-mage.",
          modifier="prowess = 6"),
    spell("shock_and_awe", "evocation", 1, 2, "war", "Shock and Awe", "+4 advantage",
          "Thunder and light break the enemy's nerve before the lines meet.",
          modifier="advantage = 4"),
    spell("flaming_munitions", "evocation", 1, 3, "war", "Flaming Munitions", "Sieges 25% faster",
          "Arrows and stones that burn on impact.",
          modifier="siege_phase_time = -0.25"),
    spell("meteor_swarm", "evocation", 2, 4, "war", "Meteor Swarm", "+20% men-at-arms damage",
          "The sky itself is turned against the foe.",
          modifier="maa_damage_mult = 0.2"),
    spell("tearfall", "evocation", 2, 5, "war", "Tearfall", "Sieges 50% faster, +20% supply limit",
          "Rain that eats stone and spares the besiegers.",
          modifier="siege_phase_time = -0.5\nsupply_limit_mult = 0.2"),
    spell("elemental_fury", "evocation", 3, 6, "war", "Elemental Fury",
          "+30% men-at-arms damage, +10 advantage, -0.5 health",
          "Overchannelled power that leaves both battlefield and caster scorched.",
          modifier="maa_damage_mult = 0.3\nadvantage = 10\nhealth = -0.5"),

    # Illusion: deception
    spell("invisibility", "illusion", 0, 1, "self", "Invisibility", "+3 Intrigue, your schemes harder to discover",
          "Unseen, unheard, unsuspected.",
          modifier="intrigue = 3\nowned_scheme_secrecy_add = 15"),
    spell("fear_and_loathing", "illusion", 1, 2, "realm", "Fear and Loathing", "+30 dread",
          "Shadows on the walls whisper what happens to the disloyal.",
          modifier="dread_baseline_add = 30"),
    spell("bread_and_circuses", "illusion", 1, 3, "realm", "Bread and Circuses", "+15 county opinion",
          "Grand spectacles, conjured from nothing, keep the people content.",
          modifier="county_opinion_add = 15", needs_land=True),
    spell("assimilation_program", "illusion", 2, 4, "realm", "Assimilation Program",
          "Your most developed county of another culture adopts yours; +15 opinion from other cultures",
          "Familiar faces and familiar songs, until the foreign feels like home.",
          modifier="different_culture_opinion = 15", effect="aov_assimilation_program = yes", needs_land=True),
    spell("shadows_in_the_night", "illusion", 2, 5, "self", "Shadows in the Night",
          "+20% hostile scheme success, your schemes much harder to discover",
          "The illusionist cultivates an environment rather than a person.",
          modifier="owned_hostile_scheme_success_chance_add = 20\nowned_scheme_secrecy_add = 30"),
    spell("lead_the_crowds", "illusion", 3, 6, "realm", "Lead the Crowds", "+25 county opinion, +15% levies",
          "The crowd sees a hero, and follows.",
          modifier="county_opinion_add = 25\nlevy_size = 0.15", needs_land=True),

    # Necromancy: dark magic
    spell("false_life", "necromancy", 0, 1, "self", "False Life", "+1 health, +10% stress gain",
          "Borrowed vigour, paid for in sleepless nights.",
          modifier="health = 1\nstress_gain_mult = 0.1"),
    spell("steal_vitality", "necromancy", 1, 2, "targeted", "Steal Vitality", "The target loses 1 health and you gain 1",
          "Life cannot be created, only transferred.",
          modifier="health = 1",
          effect="scope:recipient = { add_character_modifier = { modifier = aov_spell_steal_vitality_victim years = 2 } }"),
    spell("contagion", "necromancy", 1, 3, "targeted", "Contagion", "The target falls ill",
          "A touch, a cough, a fever by nightfall.",
          effect="scope:recipient = { if = { limit = { NOT = { has_trait = ill } } add_trait = ill } }"),
    spell("speak_with_dead", "necromancy", 2, 4, "self", "Speak With Dead",
          "Learning experience from your ancestors; may reveal a living relative's secret",
          "The dead keep the family's secrets, and share them for a price.",
          effect="aov_speak_with_dead = yes"),
    spell("remove_pain", "necromancy", 2, 5, "self", "Remove Pain", "Heals wounds and illness, -30 stress",
          "Pain is a message the necromancer can choose not to receive.",
          effect="aov_purify = yes"),
    spell("chronophage", "necromancy", 3, 6, "self", "Chronophage", "+2 health, +10 dread, +15% stress gain",
          "Years devoured, and the caster's own hourglass slows.",
          modifier="health = 2\ndread_baseline_add = 10\nstress_gain_mult = 0.15"),

    # Transmutation: change
    spell("longstrider", "transmutation", 0, 1, "self", "Longstrider", "+20% army movement, +25% travel speed",
          "Each stride covers a league.",
          modifier="movement_speed = 0.2\ncharacter_travel_speed_mult = 0.25"),
    spell("plant_growth", "transmutation", 1, 2, "realm", "Plant Growth", "Faster capital development, +20% supply limit",
          "Fields ripen twice in a season.",
          modifier="character_capital_county_monthly_development_growth_add = 0.3\nsupply_limit_mult = 0.2", needs_land=True),
    spell("mass_enlarge", "transmutation", 1, 3, "war", "Mass Enlarge", "+15% men-at-arms toughness and damage",
          "Soldiers grown a head taller and twice as broad.",
          modifier="maa_toughness_mult = 0.15\nmaa_damage_mult = 0.15"),
    spell("transmute_to_gold", "transmutation", 2, 4, "self", "Transmute to Gold", "Gold equal to Learning x 15, +20 stress",
          "Alchemy breaks things down and builds them anew, gold included.",
          effect="aov_transmute_to_gold = yes"),
    spell("reshape_terrain", "transmutation", 2, 5, "realm", "Reshape Terrain", "+4 defensive advantage",
          "Hills rise and rivers turn where the defender needs them.",
          modifier="defender_advantage = 4"),
    spell("rite_of_conception", "transmutation", 3, 6, "self", "Rite of Conception",
          "+50% fertility; a child born while it lasts may inherit Magical Affinity",
          "An old rite to bless a line with the gift.",
          modifier="fertility = 0.5"),
]
