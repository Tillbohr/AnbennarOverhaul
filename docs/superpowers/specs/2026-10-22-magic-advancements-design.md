# Magic advancements: design

Date: 2026-10-22. Status: approved in chat (rules, window, the eight advancements, files); awaiting written-spec review.
Extends the magic schools (`2026-10-08-magic-schools-design.md`) and the magic lifestyle
(`2026-10-08-magic-lifestyle-design.md`). Implements the master TODO item "Expand magic to include magical projects
from EU4".

## Goal

Give each of the eight schools one **advancement**: a three-level magical project adapted from EU4 Anbennar's
Magical Projects. The Magic window gains two tabs, **Advancements** and **Spells**, like the Artificery window's
Factions/Inventions tabs.

## Decisions taken

| Question | Decision |
|---|---|
| Source | EU4 Anbennar's standard magical projects and its Pursue Lichdom decision, remapped per the master TODO list |
| Who | Ruling mages: landed (`is_landed = yes`) characters with Magical Affinity (`has_magical_affinity = yes`). AI ruling mages too |
| Levels | Three per advancement. Level N needs knowledge level N in the advancement's school (as in EU4) |
| Cost | Gold and mana, paid when a level starts; then the level completes after a fixed time |
| Study vs. advancement | Exclusive: a mage either studies a school or is committed to one advancement, never both |
| Abandon | Allowed at any time, no refund |
| Ownership | Levels belong to the mage and die with them. Physical results (artifacts, homunculi, buildings, raised regiments) outlive the mage |
| Conjuration, Abjuration | EU4's Summon Extraplanars and Magical Fortress (the TODO list left them blank) |
| Window | Header, mana bar and school buttons on top; then Advancements / Spells tabs. Study progress stays inside the Spells tab (not at the top level) |
| Implementation | Data file `tools/data/advancements.py` + generator `tools/build_advancements.py` for the repetitive parts; each level's effect hand-written |

## The advancements

All numbers are placeholders held in `common/script_values/aov_advancement_tuning.txt` for the later balance pass
("Rebalance and rework all magical spells" in the TODO list covers magic as a whole).

### Abjuration: Magical Fortress

Wards are county modifiers on counties the mage holds in their domain, refreshed yearly and removed when the mage
dies, loses the county or loses the level.

| Level | Effect |
|---|---|
| 1 | Ward the capital county: +1 fort level, +25% garrison, +hostile county attrition, +10% development growth |
| 2 | Ward every domain county with the level-1 effects; the capital also gets +defender holding advantage |
| 3 | Wards strengthen: a further +1 fort level, more hostile attrition, development growth +20% |

### Conjuration: Summon Extraplanars

| Level | Effect |
|---|---|
| 1 | Event: choose a host. Unlocks its men-at-arms type: Host of the Shining City (heavy infantry), the Weird Ones (heavy cavalry) or Beings of Fire and Rage (archers) |
| 2 | Character modifier: + damage for the host's base type |
| 3 | Character modifier: + toughness for the host's base type, +1 regiment size for that base type |

CK3 has per-base-type modifiers (`heavy_infantry_damage_mult`, `archers_max_size_add`) but none per custom MaA type,
so the boosts apply to the base type. The modifiers fade with the mage; raised regiments stay but cannot be
recruited by a ruler without the level.

### Divination: Orb of Omniscience

| Level | Effect |
|---|---|
| 1 | Create the Orb of Omniscience (court artifact, non-decaying): +Learning, +lifestyle experience |
| 2 | `add_artifact_modifier` on the Orb: +hostile scheme discovery. The mage's Scry reveals an extra secret |
| 3 | Further Orb modifier. The mage's Foresight and Manipulated Fortune get stronger |

The Orb's own modifiers stay with the artifact; the spell boosts need a caster with the level.

### Enchantment: Enchanted Artifact

- Level 1: an event chooses the type (weapon, armor, crown, regalia or trinket) and crafts **one** non-decaying
  artifact (`decaying = no`) naming its maker. Stored on the mage as `aov_adv_enchanted_artifact`.
- Levels 2 and 3 add modifiers to that same artifact (`add_artifact_modifier`). They need the mage to own it.
- One artifact per mage per lifetime: if it is lost or destroyed, that mage cannot craft another. Another mage (for
  example the magical heir who inherits it) starts at level 0 and can craft their own.

Themes (placeholder totals at level 3; meant to be extremely strong):

| Type | Slot (vanilla type) | Theme |
|---|---|---|
| Weapon | primary armament (sword) | +15 prowess, +2 Martial, +3 advantage, +knight effectiveness |
| Armor | armor (armor_plate) | +12 prowess, +1 health, lower battle wound and death chance, +knight toughness |
| Crown | helmet | +4 Diplomacy, +3 monthly prestige, +15 vassal opinion, +10 general opinion |
| Regalia | regalia | +4 Stewardship, +1 domain limit, +20% domain tax, -20% building cost |
| Trinket | miscellaneous (ring) | +4 Learning, +50% mana, -25% spell cost, +study rate |

### Evocation: Battlemage Academy

- The levels unlock the three tiers of the building `battlemage_academy_01/02/03` (castle or city holding, one per
  domain, like `artificer_academy_01`). The building outlives the mage; later owners keep its effects.
- Any academy unlocks the decision **Recruit Battlemage Commander**: gold, 5-year cooldown; creates a courtier with
  Magical Affinity, Evocation knowledge, high Martial and Prowess and a commander trait. Recruit quality scales with
  the academy tier.
- Tier 2 unlocks the Battlemages men-at-arms (ranged evokers, needs a tier-2+ academy in the recruiter's domain).
- Tier 3 strengthens Battlemages and gives mage commanders +advantage.

### Illusion: Mirror Image

| Level | Effect |
|---|---|
| 1 | +1 to all six skills; illusory doubles: +prowess, hostile schemes against the mage less likely to succeed |
| 2 | Another +1 to all skills; body double: when imprisoned, a chance the double is taken instead and the mage is released |
| 3 | Another +1 to all skills; grand simulacrum: +general opinion, +personal scheme power, cheaper Illusion spells |

### Necromancy: Lichdom

| Level | Effect |
|---|---|
| 1 | Begin the Crime: +Learning; risks Forbidden Magic Practitioner like necromancy spells |
| 2 | Craft the Phylactery: a non-decaying artifact, stored on the mage as `aov_adv_phylactery` |
| 3 | The Ritual: needs the phylactery and a prisoner to start; on completion the prisoner is sacrificed and the mage gains Anbennar's `lich` trait |

- Starting and finishing level 3 need the phylactery in the mage's possession.
- If the phylactery is lost, stolen or destroyed before the ritual completes, Lichdom drops back to level 1 and a
  level-3 commitment is abandoned. Redoing level 2 crafts a new phylactery.
- Once a lich, losing the phylactery has no effect (a phylactery-hunting feature is left for later).

### Transmutation: Homunculus

| Level | Effect |
|---|---|
| 1 | Create a homunculus courtier with the new trait `aov_homunculus` (sterile, cannot inherit, +opinion of its maker) |
| 2 | Event: choose a skill focus; the homunculus's skills rise (a new one is made if the first has died) |
| 3 | Homunculus labour: character modifier with +development growth and +building speed in the domain |

## Rules

- **Starting a level** (`aov_adv_<key>_start_sgui`): needs a ruling mage, not committed to an advancement, the
  school level, the next level not yet done, enough gold and mana, and the per-advancement conditions above. Pays the
  gold and mana, clears `aov_studying`, sets `aov_adv_committed = flag:<key>` and `aov_adv_progress = 0`.
- **Progress**: the existing quarterly magic tick adds three months to `aov_adv_progress`; the level completes at
  its duration (placeholder 2 / 3 / 4 years), fires the completion event and calls `aov_adv_<key>_<n>_effect`, then
  sets `aov_adv_<key>_level` and clears the commitment.
- **Costs** (placeholders): 100 / 200 / 400 gold and 50 / 75 / 100 mana for levels 1 / 2 / 3.
- **Studying**: the Study buttons (`aov_study_<school>_sgui`) are invalid while committed; the quarterly study gain
  skips committed mages. Starting an advancement while studying shows "this ends your study of X".
- **Abandon** (`aov_adv_abandon_sgui`): clears the commitment and progress; nothing is refunded.
- **AI**: a yearly pulse lets an AI ruling mage who is not committed start an affordable level, weighted low.

## Window

`gui/aov_window_magic.gui` (hand-written) keeps header, mana bar and the eight school buttons. Below them two tab
buttons, **Advancements** and **Spells** (GUI variable `aov_magic_tab`, unset = Advancements).

- **Spells tab**: today's generated school pages from `build_spells.py`, unchanged (school level, study progress,
  Study button, spell cards).
- **Advancements tab**: generated page per school (`aov_advancement_<school>` in
  `gui/aov_advancements_generated.gui`): school level badge, the advancement's name, a three-step level track
  (tooltip per level with its effects), the cost, and either a Start button or, while committed, a progress bar with
  time left and an Abandon button. A line names the advancement in progress when it belongs to another school.

Art: EU4 has no per-project pictures. The school icons stand for each advancement; EU4's project button and project
progress bar (`gfx/interface/custom_gui/magic/project_button_*.dds`, `projects_progressbar_*`) are imported once with
`tools/eu4_import.py` into `gfx/interface/icons/aov_magic/`.

## Files

Generated by `python -I tools/build_advancements.py` from `tools/data/advancements.py`:

| File | Content |
|---|---|
| `common/scripted_guis/aov_advancement_sgui.txt` | Start per advancement, Abandon |
| `common/scripted_triggers/aov_advancement_triggers.txt` | can-start per advancement and level, committed checks |
| `common/script_values/aov_advancement_values.txt` | costs, durations, progress percent |
| `common/scripted_effects/aov_advancement_effects.txt` | start, abandon, quarterly progress, completion dispatch |
| `gui/aov_advancements_generated.gui` | Advancements pages |
| `localization/english/aov_advancements_l_english.yml` | names, level descriptions, tooltips |

Hand-written:

| File | Content |
|---|---|
| `common/scripted_effects/aov_advancement_level_effects.txt` | `aov_adv_<key>_<n>_effect` for all 24 levels |
| `events/aov_advancement_events.txt` | completion events, host / artifact type / skill / sacrifice choices |
| `common/modifiers/aov_advancement_modifiers.txt` | wards, host boosts, mirror image, homunculus labour |
| `common/script_values/aov_advancement_tuning.txt` | every balance number |
| `common/buildings/aov_battlemage_academy.txt` | three academy tiers |
| `common/decisions/aov_battlemage_decisions.txt` | Recruit Battlemage Commander |
| `common/men_at_arms_types/aov_advancement_maa_types.txt` | three extraplanar hosts, Battlemages |
| `common/traits/aov_homunculus_traits.txt` | `aov_homunculus` |
| `common/scripted_character_templates/aov_advancement_templates.txt` | homunculus, battlemage commander |
| `common/on_action/aov_advancement_on_actions.txt` | ward refresh, lost artifact/phylactery checks, body double on imprisonment, AI pick |
| `localization/english/aov_advancement_content_l_english.yml` | loc for the hand-written content |

Changed: `gui/aov_window_magic.gui` (tabs), `tools/build_spells.py` (study blocked while committed; rerun),
`docs/systems/magic.md`, `CLAUDE.md` (Systems row adds `build_advancements.py`), `docs/systems/updating.md`
(generator order).

## Testing

`tools/tests/test_advancements*.py`:

- Data: eight schools with one advancement each, three levels each, costs and durations rising by level.
- Freshness: generated files match the generator output (`FreshnessTests`).
- Every loc key the generated files use exists.
- Every `aov_adv_<key>_<n>_effect` the generator calls is defined in the hand-written effects file.
- Start triggers require a landed mage; the study scripted GUIs and the study tick check the commitment.
- Lichdom level 3 and Enchanted Artifact levels 2-3 check possession of the stored artifact.

Then `python -I tools/validate.py` (tiger) for new reports. Needs in-game testing: tab switching, artifact creation
and modifier upgrades, the imprisonment release, the Lichdom phylactery reset, the battlemage decision, and AI picks.

## Out of scope

- Phylactery hunting (killing a lich by destroying their phylactery).
- EU4 regional and country-unique projects.
- Balance numbers beyond placeholders.
