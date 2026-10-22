"""Magic advancements, one per school: the single source of truth for tools/build_advancements.py.

Adapted from EU4 Anbennar's magical projects and Pursue Lichdom decision
(docs/superpowers/specs/2026-10-22-magic-advancements-design.md). Each level's effect is hand-written as
aov_adv_<key>_<n>_effect in common/scripted_effects/aov_advancement_level_effects.txt; the texts here only
describe it.

levels: three (name, desc) pairs; desc is the effect summary shown in the level tooltip.
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
        [level("Ward the Capital", "Capital county: +1 fort level, +25% garrison, enemy attrition, +10% development growth"),
         level("Ward the Domain", "Every county in our domain is warded; the capital gains defender advantage"),
         level("Unbreakable Wards", "Wards gain a further +1 fort level, more enemy attrition and +20% development growth")]),
    adv("summon_extraplanars", "conjuration", "Summon Extraplanars",
        "A host from beyond the planes answers our call and marches under our banner.",
        [level("Call the Host", "Choose a host - angels, eldritch beings or devils - and unlock its men-at-arms"),
         level("Bind the Host", "The host's kind of troops deal more damage"),
         level("Host Eternal", "The host's kind of troops are tougher and their regiments larger")]),
    adv("orb_of_omniscience", "divination", "Orb of Omniscience",
        "An orb of glass and starlight in which all things, past and coming, can be glimpsed.",
        [level("Grind the Orb", "Create the Orb of Omniscience: +Learning and lifestyle experience for its owner"),
         level("Clear Sight", "The Orb uncovers hostile schemes; our Scry reveals an extra secret"),
         level("All-Seeing", "The Orb grows stronger; our Foresight and Manipulated Fortune last longer")]),
    adv("enchanted_artifact", "enchantment", "Enchanted Artifact",
        "A single masterwork - weapon, armor, crown, regalia or trinket - that carries its maker's magic.",
        [level("Forge the Vessel", "Choose a weapon, armor, crown, regalia or trinket and craft it; one per mage"),
         level("Deepen the Enchantment", "Our enchanted artifact grows stronger"),
         level("Masterwork", "Our enchanted artifact reaches its full power")],
        requires={1: ["aov_adv_can_craft_enchanted_artifact"],
                  2: ["aov_adv_owns_enchanted_artifact"],
                  3: ["aov_adv_owns_enchanted_artifact"]}),
    adv("battlemage_academy", "evocation", "Battlemage Academy",
        "A school where mages learn to turn their spells on the battlefield.",
        [level("Found the Academy", "Unlocks the Battlemage Academy building and the Recruit Battlemage Commander decision"),
         level("Battle Drills", "Unlocks the academy's second tier and Battlemage men-at-arms"),
         level("Masters of War", "Unlocks the third tier: stronger Battlemages and commanders with advantage")]),
    adv("mirror_image", "illusion", "Mirror Image",
        "Doubles of the mage, cast in light and shadow, that act and fight as their maker would.",
        [level("Mirror Images", "+1 to all skills; extra prowess, and schemes against us are less likely to succeed"),
         level("Body Double", "+1 to all skills; when imprisoned, a double may be taken in our place"),
         level("Grand Simulacrum", "+1 to all skills; opinion, scheme power and cheaper Illusion spells")]),
    adv("lichdom", "necromancy", "Lichdom",
        "The dark road to undeath: a soul bound in a phylactery and a body that never dies.",
        [level("Begin the Crime", "+Learning; where magic is frowned upon, we may be found out"),
         level("Craft the Phylactery", "Create the phylactery that will hold our soul"),
         level("The Ritual", "Sacrifice a prisoner and become a Lich; needs the phylactery and a prisoner")],
        requires={3: ["aov_adv_owns_phylactery", "aov_adv_has_sacrifice", "aov_adv_can_become_lich"]}),
    adv("homunculus", "transmutation", "Homunculus",
        "Flesh shaped in the alembic: a servant that owes its maker everything.",
        [level("Vat-Born Servant", "Create a homunculus courtier"),
         level("Refined Homunculus", "Choose a skill for our homunculus to excel at"),
         level("Homunculus Labour", "Homunculi work our domain: faster development and construction")]),
]
