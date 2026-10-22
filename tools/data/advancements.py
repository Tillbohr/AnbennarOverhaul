"""Magic advancements, one per school: the single source of truth for tools/build_advancements.py.

Adapted from EU4 Anbennar's magical projects and Pursue Lichdom decision
(docs/superpowers/specs/2026-10-22-magic-advancements-design.md). Each level's effect is hand-written as
aov_adv_<key>_<n>_effect in common/scripted_effects/aov_advancement_level_effects.txt; the texts here only
describe it.

levels: three (name, desc) pairs; desc is the effect summary shown under the level on the Advancements tab. Its
numbers mirror the modifiers and common/script_values/aov_advancement_tuning.txt: update both together.
requires: {level: [trigger, ...]} hand-written triggers (common/scripted_triggers/aov_advancement_conditions.txt)
that must hold to start that level.
"""


def level(name, desc):
    return dict(name=name, desc=desc)


def adv(key, school, name, desc, levels, requires=None):
    return dict(key=key, school=school, name=name, desc=desc, levels=levels, requires=requires or {})


ADVANCEMENTS = [
    adv("magical_fortress", "abjuration", "Magical Fortress",
        "Wards woven into the stones of our holdings turn back besiegers and shelter the land within.",
        [level("Ward the Capital", "Ward the capital county: +1 fort level, +25% garrison, raiders 25% slower, +10% development growth"),
         level("Ward the Domain", "Ward every county in our domain the same way; the capital also gains +5 defender advantage"),
         level("Unbreakable Wards", "Wards grow to +2 fort level, +50% garrison, raiders 50% slower and +20% development growth")]),
    adv("summon_extraplanars", "conjuration", "Summon Extraplanars",
        "A host from beyond the planes answers our call and marches under our banner.",
        [level("Call the Host", "Choose a host and unlock its men-at-arms, free to recruit, upgrade and maintain: Host of the Shining City (heavy infantry), The Weird Ones (heavy cavalry) or Beings of Fire and Rage (archers)"),
         level("Bind the Host", "+15% damage for all men-at-arms of the host's troop type"),
         level("Host Eternal", "+15% toughness and +1 regiment size for all men-at-arms of the host's troop type")]),
    adv("orb_of_omniscience", "divination", "Orb of Omniscience",
        "An orb of glass and starlight in which all things, past and coming, can be glimpsed.",
        [level("Grind the Orb", "Create the Orb of Omniscience, a court artifact: +2 Learning, +10% lifestyle experience"),
         level("Clear Sight", "The Orb: schemes against its owner lose 20 secrecy. Our Scry reveals a second secret"),
         level("All-Seeing", "The Orb: +2 Learning, +1 monthly prestige. Our Foresight and Manipulated Fortune last 50% longer")],
        requires={2: ["aov_adv_owns_orb"], 3: ["aov_adv_owns_orb"]}),
    adv("enchanted_artifact", "enchantment", "Enchanted Artifact",
        "A single masterwork - weapon, armor, crown, regalia or trinket - that carries its maker's magic.",
        [level("Forge the Vessel", "Craft one artifact, once in our life: Blade +6 prowess; Armor +5 prowess, health; Crown +2 Diplomacy, prestige; Regalia +2 Stewardship, tax; Ring +2 Learning, +20% mana, cheaper spells"),
         level("Deepen the Enchantment", "Strengthen it: Blade +4 prowess, +1 Martial, +1 advantage; Armor +3 prowess, health, army toughness; Crown +1 Diplomacy, prestige, +10 vassal opinion; Regalia +1 Stewardship, +1 domain limit, -10% building cost; Ring +1 Learning, +35% mana"),
         level("Masterwork", "Master it: Blade +5 prowess, +1 Martial, +2 advantage; Armor +4 prowess, health, army toughness; Crown +1 Diplomacy, prestige, +10 general opinion; Regalia +1 Stewardship, tax, -10% building cost; Ring +1 Learning, +50% mana, 25% cheaper spells")],
        requires={1: ["aov_adv_can_craft_enchanted_artifact"],
                  2: ["aov_adv_owns_enchanted_artifact"],
                  3: ["aov_adv_owns_enchanted_artifact"]}),
    adv("battlemage_academy", "evocation", "Battlemage Academy",
        "A school where mages learn to turn their spells on the battlefield.",
        [level("Found the Academy", "Build the Battlemage Academy (one per domain): +10% knight effectiveness, +1 prowess; unlocks the Recruit Battlemage Commander decision"),
         level("Battle Drills", "Upgrade to the Battlemage College: Battlemages men-at-arms and more skilled commanders"),
         level("Masters of War", "Upgrade to the Grand Battlemage Academy: Grand Battlemages, and new commanders gain +5 advantage")]),
    adv("mirror_image", "illusion", "Mirror Image",
        "Doubles of the mage, cast in light and shadow, that act and fight as their maker would.",
        [level("Mirror Images", "+1 to all skills, +2 more prowess; hostile schemes against us 10% less likely to succeed"),
         level("Body Double", "+1 to all skills; when imprisoned, a 50% chance a body double takes our place"),
         level("Grand Simulacrum", "+1 to all skills, +10 general opinion, +10% personal scheme success, Illusion spells 20% cheaper")]),
    adv("lichdom", "necromancy", "Lichdom",
        "The dark road to undeath: a soul bound in a phylactery and a body that never dies.",
        [level("Begin the Crime", "+2 Learning, +5 dread; where magic is frowned upon, we may be revealed as a Forbidden Magic Practitioner"),
         level("Craft the Phylactery", "Craft the Phylactery that will hold our soul (+1 Learning). If it is lost before the ritual, Lichdom falls back to level 1"),
         level("The Ritual", "Sacrifice a prisoner and become a Lich: immortal, +5 to all skills, +10 prowess, +50 dread, -20 general opinion")],
        requires={3: ["aov_adv_owns_phylactery", "aov_adv_has_sacrifice", "aov_adv_can_become_lich"]}),
    adv("homunculus", "transmutation", "Homunculus",
        "Flesh shaped in the alembic: a servant that owes its maker everything.",
        [level("Vat-Born Servant", "Create a Homunculus courtier: +2 Stewardship, sterile, cannot inherit, +75 opinion of us"),
         level("Refined Homunculus", "Refine it: +8 to a skill of our choice (a new homunculus if the first has died)"),
         level("Homunculus Labour", "Homunculi work our domain: +15% development growth, 20% faster construction")]),
]
