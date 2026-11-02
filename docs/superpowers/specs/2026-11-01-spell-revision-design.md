# Spell revision: design

Date: 2026-11-01. Status: spell list approved in chat; awaiting written-spec review.
Revises the 48 spells of `docs/superpowers/specs/2026-10-08-magic-schools-design.md`. Mana, knowledge, the Magic window,
costs and durations are unchanged. New advancements are out of scope (see the end).

## Goal

Make spells stronger and give each school one clear theme:

| School | Theme |
|---|---|
| Abjuration | Defence: wards, cures, dispelling |
| Conjuration | Summoned armies and minions |
| Divination | Hidden information and the future |
| Enchantment | Minds: opinion, forced relations, domination; enchanted objects |
| Evocation | Offensive war magic: fire, frost, earthquakes |
| Illusion | Deception and intrigue |
| Necromancy | Disease, plague, death, the dead |
| Transmutation | Changing what you have: yourself and your army |

## Decisions taken

| Question | Decision |
|---|---|
| Spell layout | Unchanged: six per school, levels 0/1/1/2/2/3, costs 25/50/100/200 mana, durations 1/2/3/5 years |
| Keys | A spell that keeps its theme keeps its key (cooldowns and modifiers carry on); renamed spells keep their key and change only their name |
| Removed spells | 20 removed (list below). Saves made before the change may log missing-modifier errors for them; a new campaign is advised |
| Thoughtweave | Keeps its name; becomes the forced-interaction spell (user's choice) |
| Finger of Death | Instant death is the least likely outcome; injury and disease are more likely (user's choice) |
| Plague Cloud | Starts an outbreak of random scale; major outbreaks are rare, apocalyptic never (user's choice) |
| Perfect Form | Random: gives a beneficial genetic trait the caster lacks, or removes a genetic defect they have (user's choice) |
| Raise Dead | Stays in Necromancy (approved as proposed) |
| Anbennar's Compel and Dominate | Thoughtweave and Dominate become our own interactions; Anbennar's `start_compel_interaction` and `start_dominate_interaction` are hidden by never-shown stub overrides, as Enhance Ability already is |
| Tuning | Every chance and amount that is not a modifier line lives in a new hand-written `common/script_values/aov_spell_tuning.txt` |

## Shared rules

### Hostile spells and spell resistance

These targeted spells are **hostile**: Fireball, Winter's Grip, Earthquake, Ray of Sickness, Contagion, Life Drain,
Plague Cloud, Finger of Death, Phantasmal Rumour, Implant Scandal, Grand Deception, Thoughtweave, Dominate.

Each rolls to land (`aov_spell_land_chance`, caster scope, target `scope:recipient`):

- base 75;
- +3 per point of the caster's Learning above the target's (or −3 per point below);
- −10 per level of the target's Abjuration knowledge;
- −30 if the target has the Ward modifier;
- clamped to 10..95.

A target under Field of Forbiddance cannot be chosen at all (the existing `aov_spell_target_allowed`). The interaction
shows the chance: the roll is a `random_list` in the cast effect, whose tooltip prints both percentages. On a miss the mana is spent, the cooldown starts, and the target learns who cast
it: opinion `aov_attempted_hostile_magic` (−30, 5 years) and a notification. On a hit, war spells (Fireball, Winter's
Grip, Earthquake) are open: the target knows. Curses (all the others) stay anonymous unless the spell's own text says
otherwise. Necromancy keeps its Forbidden Magic Practitioner risk.

### Choice events

Window spells that make the caster choose (Enhance Ability, Living Steel, Shapechange) open an event after casting;
each option has an `ai_chance`, so AI mages pick too. Thoughtweave and Dominate take their choice in the interaction
window instead (send options, and a second character picked like vanilla's guardian interaction), so the choice is
made before the land roll.

### AI

Window spells keep the existing quarterly AI casting. Hostile targeted spells get `ai_will_do`: AI mages cast them on
rivals and on rulers at war with them, more readily when the chance to land is high.

## Spell list

Kept = same key. Numbers in brackets are the old values.

### Abjuration

| Lvl | Key | Name | Type | Effect |
|---|---|---|---|---|
| 0 | combat_ward | Combat Ward | self | +6 prowess (4), +0.25 health |
| 1 | ward | Ward | targeted | Target: −30% hostile scheme success against them, −30 to hostile spells' chance to land |
| 1 | **purify** | Purify | self | Cures illness, diseases and wounds (old Remove Pain's `aov_remove_pain`), removes hostile spell modifiers, −20 stress |
| 2 | mass_ward | Mass Ward | realm | +50% garrison (25%), +6 defender advantage (3) |
| 2 | mage_armor | Mage Armor | war | +25% men-at-arms toughness (15%), + levy toughness |
| 3 | field_of_forbiddance | Field of Forbiddance | realm | −30% hostile scheme success (20), immune to hostile spells; on cast, removes every war-spell modifier from rulers at war with the caster |

### Conjuration

| Lvl | Key | Name | Type | Effect |
|---|---|---|---|---|
| 0 | summon_familiars | Summon Familiar | self | +3 Intrigue, +3 Learning (2/2) |
| 1 | **summon_beasts** | Summon Beasts | war | Spawns 2 stacks of a new men-at-arms type `aov_conjured_beasts` (light cavalry: wolves and bears) where the elementals would appear; removed when the spell ends |
| 1 | **bound_champion** | Bound Champion | self | Creates an outsider knight (prowess about 25, a combat trait), forced as a knight of the caster's court; vanishes when the spell ends |
| 2 | summon_elementals | Summon Elementals | war | 6 stacks (4) |
| 2 | aid_construction | Unseen Servants | realm | Buildings 40% faster (30%), 25% cheaper (20%) |
| 3 | **planar_gate** | Planar Gate | war | 10-stack army for 5 years: the Summon Extraplanars host's men-at-arms type if the caster has one, else `aov_conjured_elementals`. 10% chance a demon slips through: fires the old Extraplanar Contact bargain event `aov_magic.20` |

### Divination

| Lvl | Key | Name | Type | Effect |
|---|---|---|---|---|
| 0 | guidance | Guidance | self | +4 Learning (3), +15% lifestyle experience (10%) |
| 1 | **detect_plots** | Detect Plots | self | Exposes every hostile scheme targeting the caster and its agents (`expose_scheme`, `expose_scheme_agent`) |
| 1 | eye_for_talent | Eye for Talent | self | Unchanged |
| 2 | scry | Scry | targeted | Reveals all of the target's secrets (1), including disputed parentage; not hostile |
| 2 | **augury** | Augury | self | Event listing the threats of the coming years: rulers with claims on the caster's titles who outmatch them, vassals in factions against them, close relatives in poor health, rivals with schemes against them. Modifier +10% hostile scheme success, +10% prestige gain (old Manipulated Fortune) |
| 3 | foresight | Foresight | self | +12 advantage (8), −50 secrecy for schemes against the caster (−30), +10% hostile scheme success |

The Orb of Omniscience's level 3 bonus moves from Manipulated Fortune to Augury (`years_mult`). Its level 2 Scry bonus
(a second secret) means nothing once Scry reveals them all, so it becomes: Scry also reveals every secret the target
knows about others.

### Enchantment

| Lvl | Key | Name | Type | Effect |
|---|---|---|---|---|
| 0 | enchanting_envoy | Enchanting Envoy | self | +4 Diplomacy (3), +5 general opinion |
| 1 | heartstring | Heartstring | targeted | +50 opinion (30) for 3 years (2) |
| 1 | **enchant_trinket** | Enchant Trinket | self | Creates a minor trinket artifact: +2 to a random skill or +4 prowess; low durability, so it decays in about ten years |
| 2 | thoughtweave | Thoughtweave | targeted | Hostile. Caster chooses: the target becomes their friend; becomes the lover of a character the caster names; becomes the rival of a character the caster names; or the caster gains a weak hook |
| 2 | enchanting_embassy | Enchanting Embassy | realm | +25 vassal opinion (15), +10 general opinion (5) |
| 3 | dominate_to_surrender | Dominate | targeted | Hostile. Caster chooses: a strong hook; or, when caster and target are the two primary participants of a war, the target surrenders (the caster's side wins); or the target frees a prisoner the caster names |

### Evocation

| Lvl | Key | Name | Type | Effect |
|---|---|---|---|---|
| 0 | fireball | Fireball | targeted (was self) | Hostile. Target: a ruler at war with the caster, or a knight or commander of one. Wounded; 20% chance severely wounded |
| 1 | shock_and_awe | Thunderclap | war | +6 advantage (4), +10% men-at-arms damage |
| 1 | flaming_munitions | Flaming Munitions | war | Sieges 40% faster (25%) |
| 2 | **winters_grip** | Winter's Grip | targeted | Hostile, at war only. Target's armies: −40% movement, −15% men-at-arms damage, −20% supply limit, 3 years |
| 2 | **earthquake** | Earthquake | targeted | Hostile, at war only. Target's capital county: −2 development, −40 control, county modifier −1 fort level and −50% garrison for 3 years; 25% chance of a further −1 development (CK3 script cannot pick an existing building to destroy) |
| 3 | meteor_swarm | Meteor Swarm | war (was level 2) | The enemy war leader's 3 most developed counties: −1 development, −30 control, county modifier −50% levies and tax for 5 years. Caster's armies +30% men-at-arms damage, +10 advantage; caster −0.5 health (old Elemental Fury). Target: the other primary participant of the caster's war |

### Illusion

| Lvl | Key | Name | Type | Effect |
|---|---|---|---|---|
| 0 | invisibility | Invisibility | self | +4 Intrigue (3), +25 scheme secrecy (15) |
| 1 | fear_and_loathing | Fear and Loathing | realm | +40 dread (30) |
| 1 | **phantasmal_rumour** | Phantasmal Rumour | targeted | Hostile. Target −150 prestige, −20 vassal opinion for 3 years |
| 2 | shadows_in_the_night | Shadows in the Night | self | +25% hostile scheme success (20), +40 secrecy (30) |
| 2 | **implant_scandal** | Implant Scandal | targeted | Hostile. Target gains a false secret fitting them (deviancy, witchcraft or heresy; exact secret types checked in implementation), known only to the caster |
| 3 | **grand_deception** | Grand Deception | targeted | Hostile. Caster gains a pressed claim on one of the target's counties: one bordering the caster's realm, else the target's capital county |

### Necromancy

| Lvl | Key | Name | Type | Effect |
|---|---|---|---|---|
| 0 | **ray_of_sickness** | Ray of Sickness | targeted | Hostile. Target −1 health for 1 year |
| 1 | contagion | Contagion | targeted | Hostile. Target contracts a random disease they can catch (`contract_disease_effect`: consumption, typhus or smallpox) instead of `ill` |
| 1 | steal_vitality | Life Drain | targeted | Hostile. Target −2 health (1), caster +2 health (1) |
| 2 | **plague_cloud** | Plague Cloud | targeted | Hostile. An epidemic breaks out in the target's capital province (`create_epidemic_outbreak`): type random among the contagious ones (smallpox, bubonic plague, typhus, consumption, measles, dysentery); intensity minor 80%, major 20%, never apocalyptic. It spreads normally, possibly to the caster |
| 2 | **raise_dead** | Raise Dead | war | Spawns 3 stacks of `aov_lich_skeletons` and skeleton archers where the caster's elementals would appear; a Lich raises 6. Removed when the spell ends |
| 3 | **finger_of_death** | Finger of Death | targeted | Hostile. If it lands: death 15%, severe injury 45% (a severe wound or a maiming trait), deadly disease 40% (`contract_disease_effect`). +20 dread whatever the outcome |

### Transmutation

| Lvl | Key | Name | Type | Effect |
|---|---|---|---|---|
| 0 | **enhance_ability** | Enhance Ability | self | Caster chooses a skill: +4 for 1 year |
| 1 | longstrider | Longstrider | self (was level 0) | +30% army movement (20%), +40% travel speed (25%) |
| 1 | mass_enlarge | Mass Enlarge | war | +20% men-at-arms toughness and damage (15%) |
| 2 | **living_steel** | Living Steel | war | Caster chooses a troop type (heavy infantry, light infantry/skirmishers, pikes, archers, light cavalry, heavy cavalry): +30% damage and toughness for it |
| 2 | **shapechange** | Shapechange | self | Caster chooses a form: Bear (+10 prowess, +0.5 health), Wolf (+3 Martial, +4 advantage), Hawk (+3 Intrigue, +40% travel speed, +20 secrecy). Each +20 dread |
| 3 | **perfect_form** | Perfect Form | self | One random outcome from a pool (below). +50 stress; 10% chance of −1 health for 5 years |

**Perfect Form pool.** Every option that applies to the caster has equal weight:

- *Gain:* a beauty, intellect or physique trait one step above what they have (none → good 1, good 1 → good 2,
  good 2 → good 3; not offered while they have the bad trait of that group); `fecund` if they lack it.
- *Remove:* each genetic defect they have: `beauty_bad_*`, `intellect_bad_*`, `physique_bad_*`, `clubfooted`,
  `hunchbacked`, `lisping`, `stuttering`, `dwarf`, `giant`, `spindly`, `scaly`, `wheezing`, `bleeder`, `infertile`,
  `depressed_genetic`, `lunatic_genetic`, `possessed_genetic`.
- `albino` is neutral and left alone. Magical Affinity is not in the pool.
- With an empty pool the spell cannot be cast (shown in its tooltip).

## Removed spells (20)

protected_journey, summon_animals, conjure_supplies, extraplanar_contact (its event lives on in Planar Gate),
deposit_divination, manipulated_fortune, command_animals, tearfall, elemental_fury, false_life, speak_with_dead,
remove_pain (its effect lives on in Purify), chronophage, bread_and_circuses, assimilation_program, lead_the_crowds,
plant_growth, transmute_to_gold, reshape_terrain, rite_of_conception.

Their hand-written effects (`aov_deposit_divination`, `aov_speak_with_dead`, `aov_transmute_to_gold`,
`aov_assimilation_program`) and any loc and modifiers only they used are deleted.

## What changes where

| Area | Change |
|---|---|
| `tools/data/spells.py` | New list; a `hostile` flag for the resistance roll |
| `tools/build_spells.py` | Emits the land-chance check for hostile spells and the list of war-spell modifiers that Field of Forbiddance dispels; Meteor Swarm moves to slot 6 |
| Hand-written `aov_magic_*` files | New effects and events for the new spells; resistance, miss and dispel effects; spawned-army removal reused from Summon Elementals |
| `common/script_values/aov_spell_tuning.txt` | New: chances and amounts (land chance terms, Finger of Death odds, Plague Cloud odds, Perfect Form risk) |
| Men-at-arms | New `aov_conjured_beasts` type (never recruitable, like the elementals) |
| `common/character_interactions/zz_aov_spell_overrides.txt` | Compel and Dominate hidden by stubs |
| `tools/data/advancements.py` | Orb level 3 text and `years_mult` move to Augury |
| `docs/systems/magic.md` | Spell summary updated |
| Tests | Spell data tests updated; freshness tests after regenerating |

## Testing

- `python -I -m unittest discover -s tools/tests -p "test_build_spells.py"`, then `test_magic_system.py`,
  `test_advancements.py` and `test_build_advancements.py`.
- `python -I tools/validate.py`: no new reports for the changed files.
- **To confirm in game:** each choice event opens and its AI chances fire; spawned armies (beasts, raised dead, gate)
  appear and vanish; Plague Cloud outbreaks start at the target's capital at the expected scales; Dominate's surrender
  ends the war in the caster's favour; Grand Deception's claim is pressed; Perfect Form's pool never offers a trait the
  caster already has.

## Out of scope

The new advancement ideas (one more per school, and Alchemical Forge for Transmutation) wait for a separate decision.
The Advancements page shows one advancement per school, so a second needs a GUI change.
