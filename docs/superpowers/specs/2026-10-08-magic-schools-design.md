# Magic schools and spells: design

Date: 2026-10-08. Status: approved in chat (decomposition, mechanics, window, spell list); awaiting written-spec review.
Sub-project 1 of 3 of the magic system. Sub-project 2 is the magic lifestyle (three trees, perks, focuses, art, loc),
which will feed school knowledge. Sub-project 3 is an optional balance and AI pass.

## Goal

Give Anbennar's mages eight schools of magic to study and 49 spells to cast. Spells are adapted from EU4 Anbennar
to CK3 terms. The Magic window works like the Artificery window: a mana bar, a study project, and one tab per school
listing its spells with Cast buttons. Anbennar's existing Compel, Dominate and Enhance Ability spells become part of
the system.

## Decisions taken

| Question | Decision |
|---|---|
| Schools | Eight: Abjuration, Conjuration, Divination, Enchantment, Evocation, Illusion, Necromancy, Transmutation (EU4 order) |
| Who can use magic | Any character with Magical Affinity (`magical_affinity_1/2/3`, Anbennar) |
| Spell cost | Mana pool, refilled monthly; 25/50/100/200 mana for spell levels 0/1/2/3 |
| Knowledge | Per school, levels 0-3. Raised by studying one chosen school at a time; casting also adds progress |
| Targeting | Approach A: the window casts self/realm/war spells; character-targeted spells are character interactions in Anbennar's `interaction_category_spells` |
| Magic law | Necromancy is dark: casting it where the faith makes magic illegal or shunned risks Forbidden Magic Practitioner. Other schools are always legal |
| Existing spells | Compel = Thoughtweave (Enchantment 2), Dominate = Dominate to Surrender (Enchantment 3), Enhance Ability joins Transmutation at level 1 |
| Summon Elementals | A ready-made army, not a mercenary company: CK3 cannot create, price or restrict mercenary companies from script (user's choice of substitute) |
| Content source | EU4 Anbennar spells (names, school, level, theme, icons, flavour), adapted to CK3 effects |
| Implementation | Data-driven: `tools/data/spells.py` + generator `tools/build_spells.py`, like the inventions |

## Player-facing behaviour

### Eligibility

A **mage** is a character with any Magical Affinity trait (`has_magical_affinity = yes`, Anbennar's scripted trigger).
Only mages have mana, knowledge, the Magic tab and the spell interactions. Magic state is personal: it is not
inherited.
Mana refill, study and AI casting run for **playable** mages (rulers and landless adventurers, via
`quarterly_playable_pulse`). A courtier mage keeps their state frozen until they
become playable; they can still be the target of spells.

### Mana

- Maximum: 100 + 50 per affinity level (150 / 200 / 250).
- Monthly refill: 5 + Learning / 2 + 2 per affinity level, capped at the maximum.
- CK3 has no monthly character pulse, so mana and study are applied each quarter (`quarterly_playable_pulse`)
  at three times the monthly amounts; the rate is the same, and the window shows the monthly figure.
- A new mage starts full.

### Knowledge and study

- Each school has a level 0-3 and a progress value. Every mage starts at level 0 in every school, so all level-0
  spells are castable from the start.
- Thresholds: level 1 at 300 progress, level 2 at 800, level 3 at 2000 (cumulative, per school).
- **Study:** the mage picks one school in the window. Each month it gains Learning + 5 x affinity level progress.
  Switching school keeps the progress already made in each school. Studying is optional; no school is studied
  until one is picked.
- **Casting:** each cast adds progress equal to its mana cost in that spell's school.
- A level-up fires a short notification event.
- Anbennar's `magic_mastery` variable is set to the sum of school levels (0-24), so its existing character-window
  icon shows real progress.

### Casting

- A spell can be cast when: the caster is a mage; the school level is at least the spell's level; the caster has
  enough mana; the spell is not on cooldown; and war spells need the caster at war.
- Cost: the mana is spent and the school gains progress.
- Duration by spell level: 1 / 2 / 3 / 5 years. Each spell's cooldown equals its duration, so a spell cannot be
  stacked or refreshed early.
- Effect types:
  - **Self (S):** a character modifier on the caster.
  - **Realm (R):** a character modifier on the caster whose effects apply to their domain.
  - **War (W):** a character modifier on the caster affecting their armies. Castable only while at war; it stays
    for its duration even if the war ends.
  - **Targeted (T):** a character interaction from the target's portrait (Spells category). The window lists it
    with "Cast on a character from their portrait". The interaction checks the same requirements and spends the
    same mana. Spells with acceptance or schemes (Heartstring, Compel, Dominate, Enhance Ability) keep that logic.
- **Dark magic:** casting a Necromancy spell where the caster's faith has `witchcraft_illegal` gives a 25% chance
  of `forbidden_magic_practitioner`; with `witchcraft_shunned`, 10%.

### Spells

S = self, R = realm, W = war (castable only while at war), T = targeted from a character's portrait.
Durations by level: 0 = 1 year, 1 = 2 years, 2 = 3 years, 3 = 5 years. Modifier keys are verified with tiger at
implementation; where a key does not exist for characters, the closest character modifier is used and the
deviation recorded.

**Abjuration: protection**

| Lvl | Spell | Type | Effect |
|---|---|---|---|
| 0 | Combat Ward | S | +4 prowess |
| 1 | Ward | T | Target: schemes against them are harder (hostile scheme resistance) |
| 1 | Protected Journey | S | Safer travel, +10% travel speed |
| 2 | Mass Ward | R | +25% garrison size, +3 defensive advantage |
| 2 | Mage Armor | W | +15% men-at-arms toughness |
| 3 | Field of Forbiddance | R | -20% success for schemes against the caster; the caster cannot be targeted by spells |

**Conjuration: summoning**

| Lvl | Spell | Type | Effect |
|---|---|---|---|
| 0 | Summon Familiars | S | +2 intrigue, +2 learning |
| 1 | Summon Animals | W | +10% levy size |
| 1 | Conjure Supplies | W | +25% supply limit, -10% army maintenance |
| 2 | Summon Elementals | W | A free army of conjured elementals appears at the caster's capital, under the caster's control only; it vanishes after 3 years or when that war ends |
| 2 | Aid Construction | R | Buildings 30% faster and 20% cheaper |
| 3 | Extraplanar Contact | S | Event: choose great learning XP, an artifact, or gold; chance of a demonic price (stress or a scar) |

**Divination: knowledge**

| Lvl | Spell | Type | Effect |
|---|---|---|---|
| 0 | Guidance | S | +3 learning, +10% lifestyle XP |
| 1 | Eye for Talent | S | A skilled character (one high skill, good traits) arrives at court (one-off) |
| 1 | Deposit Divination | R | One-off gold scaled by capital development, plus faster capital development |
| 2 | Scry | T | Reveals one of the target's secrets; if none, intrigue lifestyle XP (one-off) |
| 2 | Manipulated Fortune | S | +10% scheme success, +10% prestige gain |
| 3 | Foresight | S | +8 advantage as commander; hostile schemes against the caster much easier to discover |

**Enchantment: the mind**

| Lvl | Spell | Type | Effect |
|---|---|---|---|
| 0 | Enchanting Envoy | S | +3 diplomacy |
| 1 | Heartstring | T | Charm: target gains +30 opinion of the caster |
| 1 | Command Animals | W | +15% army movement speed, +2 advantage |
| 2 | Thoughtweave | T | Anbennar's Compel scheme |
| 2 | Enchanting Embassy | R | +15 vassal opinion, +5 general opinion |
| 3 | Dominate to Surrender | T | Anbennar's Dominate scheme |

**Evocation: war magic**

| Lvl | Spell | Type | Effect |
|---|---|---|---|
| 0 | Fireball | S | +6 prowess |
| 1 | Shock and Awe | W | +4 advantage |
| 1 | Flaming Munitions | W | Sieges 25% faster |
| 2 | Meteor Swarm | W | +20% men-at-arms damage |
| 2 | Tearfall | W | Sieges 50% faster, less attrition |
| 3 | Elemental Fury | W | +30% men-at-arms damage, +10 advantage, -0.5 health while active |

**Illusion: deception**

| Lvl | Spell | Type | Effect |
|---|---|---|---|
| 0 | Invisibility | S | +3 intrigue, own schemes harder to discover |
| 1 | Fear and Loathing | R | +30 dread |
| 1 | Bread and Circuses | R | +15 county opinion in the domain |
| 2 | Assimilation Program | R | Much faster culture conversion in the domain |
| 2 | Shadows in the Night | S | +20% hostile scheme success, own schemes much harder to discover |
| 3 | Lead the Crowds | R | +25 county opinion, +15% levies |

**Necromancy: dark magic**

| Lvl | Spell | Type | Effect |
|---|---|---|---|
| 0 | False Life | S | +1 health, +10% stress gain |
| 1 | Steal Vitality | T | Target -1 health, caster +1 health (both for the duration) |
| 1 | Contagion | T | Target falls ill (one-off) |
| 2 | Speak With Dead | S | Large XP in the caster's current lifestyle; 33% chance to discover a living relative's secret (one-off) |
| 2 | Remove Pain | S | Removes wounded and ill traits, -30 stress (one-off) |
| 3 | Chronophage | S | +2 health, +10 dread, +15% stress gain |

**Transmutation: change**

| Lvl | Spell | Type | Effect |
|---|---|---|---|
| 0 | Longstrider | S | +20% army movement, +25% travel speed |
| 1 | Plant Growth | R | Faster capital development, +20% supply limit |
| 1 | Mass Enlarge | W | +15% men-at-arms toughness and damage |
| 1 | Enhance Ability | T | Anbennar's Enhance Ability scheme |
| 2 | Transmute to Gold | S | Gold = Learning x 15, +20 stress (one-off) |
| 2 | Reshape Terrain | R | +4 defensive advantage |
| 3 | Rite of Conception | S | +50% fertility; a child born to the caster while it lasts gains Magical Affinity 1 with 50% chance |

One-off spells apply their effect at once; their cooldown is still the level duration.

### Magic window

- **HUD tab:** a main tab below Artificery (`gui/hud.gui`, generated), shown to players who are mages, opening
  `gui/aov_window_magic.gui` (scripted widget, GUI variable `aov_magic_window`). Opening it closes the Artificery
  window and vice versa.
- **Top:** mana bar (current / maximum, refill per month in the tooltip); study status ("Studying Divination:
  420 / 800" or "Not studying").
- **School tabs:** eight tabs with EU4 school icons (GUI variable `aov_magic_school`, unset = Abjuration).
- **School page:**
  - Header: school icon and name, level (EU4 level strip), progress bar to the next level, and a
    "Study this school" button (pressed while it is the studied school).
  - Spell cards (six; seven for Transmutation): EU4 spell icon, name, level, mana cost, type, duration.
    - S/R/W cards: a Cast button. Disabled with the reason (school level, mana, cooldown, not at war).
    - T cards: the line "Cast on a character from their portrait".
    - Tooltip: effects, duration, cooldown, flavour.
    - On cooldown: "Ready in N months".
- **Art:** EU4 Anbennar magic assets copied by the generator. Classic-header files are copied as they are; DX10
  files are converted with the existing `dx10_bgra_to_legacy`.

### AI

AI mages:
- With no study target, study the school matching their highest skill (Diplomacy: Enchantment;
  Martial: Evocation; Stewardship: Transmutation; Intrigue: Illusion; Learning: Divination); a random school
  otherwise.
- Each quarter, cast one affordable self or realm spell (random among castable ones; war spells only at war).
- Targeted spells: the AI uses the interactions through their `ai_potential`/`ai_will_do`, kept conservative.

## Architecture

### Data and generator

`tools/data/spells.py` is the single source of truth: one entry per spell with `key`, `school`, `level`, `slot`
(1-6, the EU4 icon slot), `type` (self/realm/war/targeted), `modifier` (character modifier body, empty for
one-offs and targeted), `effect` (script for one-off effects, optional), `name`, `desc` (effect summary),
`flavour`, and for targeted spells `interaction` (the existing interaction key for Compel, Dominate, Enhance
Ability; else generated).

`tools/build_spells.py` validates the data and writes (header "generated ... do not edit by hand"):

| File | Content |
|---|---|
| `common/modifiers/aov_spell_modifiers.txt` | one modifier per lasting spell |
| `common/scripted_triggers/aov_spell_triggers.txt` | per spell: known (school level), ready (cooldown), castable |
| `common/scripted_effects/aov_spell_effects.txt` | per spell: cast (pay, progress, apply, cooldown, dark-magic roll) |
| `common/scripted_guis/aov_spell_sgui.txt` | per S/R/W spell: cast sGUI; per school: study sGUI |
| `common/character_interactions/aov_spell_interactions.txt` | generated targeted spells (Ward, Heartstring, Scry, Steal Vitality, Contagion) |
| `gui/aov_magic_generated.gui` | spell cards and school pages as types |
| `localization/english/aov_spells_l_english.yml` | names, descriptions, flavour, tooltips |
| `gfx/interface/icons/aov_magic/` | EU4 spell slot strips, school icons, level strip, background, buttons |

### Hand-written files

| File | Content |
|---|---|
| `common/scripted_effects/aov_magic_effects.txt` | mana refill/cap, study tick, level-up, mastery sync, AI |
| `common/scripted_triggers/aov_magic_triggers.txt` | `aov_is_mage`, school level triggers, dark-magic law |
| `common/script_values/aov_magic_values.txt` | mana max/refill, study gain, thresholds, school levels |
| `common/scripted_guis/aov_magic_sgui.txt` | window availability, study state |
| `common/on_action/aov_magic_on_actions.txt` | quarterly mana, study and AI (`quarterly_playable_pulse`, mages only), birth (Rite of Conception) |
| `common/character_interactions/zz_aov_spell_overrides.txt` | single-object overrides of `start_compel_interaction`, `start_dominate_interaction`, `anb_enhance_ability_interaction`: Anbennar's definitions plus school level, mana cost and cooldown (marked `# Anbennar Overhaul`) |
| `events/aov_magic_events.txt` | level-up, Extraplanar Contact, Eye for Talent arrival |
| `gui/aov_window_magic.gui` | window |
| `gui/scripted_widgets/aov_scripted_widgets.txt` | registers the window |
| `tools/build_hud_override.py` | adds the Magic tab after the Artificery tab |
| `localization/english/aov_magic_l_english.yml` | window and system loc |

### State (character variables on the mage)

- `aov_mana` (0..max).
- `aov_school_<school>_progress` (cumulative); level derived by value `aov_school_<school>_level`.
- `aov_studying` = `flag:<school>`.
- Per spell cooldown: timed variable `aov_spell_<key>_cd` (years = duration).
- `magic_mastery` = sum of levels (Anbennar variable).
- Rite of Conception: the modifier's presence is checked on birth.

## Out of scope

- The magic lifestyle (sub-project 2) and its perks feeding knowledge.
- EU4 patrons, magical traditions, infamy, magic projects and spell discounts.
- Mana or knowledge for non-mages; magic artifacts.

## Verification

- Tool tests: data validation (49 spells, 8 schools, 6 per school plus Enhance Ability, unique slots per school,
  levels match slots), generated-output structure, overrides contain Anbennar's interaction bodies plus the added
  requirements.
- `python -I tools/validate.py` clean.
- In game: the Magic tab appears for a mage and not for others; mana refills monthly; studying raises a school
  and fires the level-up event; casting a self spell spends mana, applies the modifier and starts the cooldown;
  war spells only at war; Summon Elementals spawns and disbands its army; targeted spells appear in a character's
  Spells menu and charge mana; Necromancy in a witchcraft-illegal faith can give Forbidden Magic Practitioner;
  `magic_mastery` icon reflects levels.

## Risks

- **Interaction overrides** copy three Anbennar interactions; re-copy after Anbennar updates (CLAUDE.md step).
- **Modifier keys** for travel safety, hostile scheme resistance, culture conversion and siege speed must be checked
  against 1.19; substitutes are recorded.
- **Summon Elementals** uses `spawn_army` (`men_at_arms = { type = aov_conjured_elementals stacks = 4 }`,
  `location = capital_province`, `war` = the caster's current war, `inheritable = no`, `uses_supply = no`), saved in
  variable `aov_elemental_army`. A scheduled event 3 years later runs `deplete_army_by_percent = 1` on it (an engine
  effect tiger knows; vanilla never uses it, so it needs an in-game check). Binding it to the war also removes it
  when the war ends. `aov_conjured_elementals` is a new men-at-arms type that can never be recruited.
- **HUD space:** a second extra main tab; check the tab column still fits at 1080p.
