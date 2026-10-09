# Magic lifestyle: design

Date: 2026-10-08. Status: approved in chat (tree layout, perk role, focuses, capstone traits, art, perk list,
architecture); awaiting written-spec review.
Sub-project 2 of 3 of the magic system. Sub-project 1 (schools and spells,
`2026-10-08-magic-schools-design.md`) is built. Sub-project 3 is an optional balance and AI pass.

## Goal

Turn Anbennar's stub `magic_lifestyle` into a full lifestyle: three perk trees, three focuses and three
capstone traits. Its perks make a mage better at the school system (faster study, more mana, cheaper and
longer spells) and give ordinary character modifiers. The base mod stays untouched.

## Decisions taken

| Question | Decision |
|---|---|
| Tree layout | Three themed trees, each grouping schools, so the vanilla lifestyle window fits them |
| Perk role | Boosts only. Every school level stays reachable without perks; perks speed it up and strengthen spells |
| Focuses | Three, one per tree. Anbennar's `magic_duelist_focus` is reused as the Battle Mage focus (single-object override) |
| Capstones | Vanilla-sized trees (9 perks); the last perk grants a new lifestyle trait |
| Art | EU4 Anbennar magic art for the lifestyle, focuses and traits; a tinted vanilla node strip for the perks |
| Implementation | Approach A: content hand-written; generators only for the whole-file GUI override and the art |

## Starting point (Anbennar)

- `common/lifestyles/anb_magic_lifestyle.txt`: `magic_lifestyle`, valid with `has_trait = magical_affinity`
  (trait group), `xp_per_level = 1000`, `base_xp_gain = 25`.
- `common/focuses/anb_magic_focuses.txt`: `magic_duelist_focus` (+3 prowess).
- `common/lifestyle_perks/anb_magic_war_wizardry_perks.txt`: all perks commented out.
- `localization/english/anb_magic_lifestyle_l_english.yml`: lifestyle, focus and XP loc.
- Traits, an innovation and buildings grant `monthly_magic_lifestyle_xp_gain_mult`, which has no
  `modifier_definition_formats` entry.
- `gui/window_character_lifestyle.gui`: Anbennar's full override (widened lifestyle row), with no
  `magic_lifestyle` branches.
- `update_magic_mastery_stat` (never called) would set `magic_mastery` to the perk count;
  `magic_lifestyle_total_points` feeds the character-window tooltip. Sub-project 1 sets `magic_mastery` to the
  sum of school levels.

## Player-facing behaviour

### Trees

Vanilla layout: two branches of three (`position = { 0 0..2 }` and `{ 2 0..2 }`), a merge of two
(`{ 1 3 }` with both branch ends as parents, then `{ 1 4 }`), and the trait perk at `{ 1 5 }`.

Shorthand: **Study +25% X** = studying school X gains 25% more progress. **Cost −25% X** = X's spells cost 25%
less mana. **Lasts +50% X** = X's lasting spells last 50% longer; the cooldown equals the actual duration, so a
spell still cannot be stacked.

**Arcane Scholar** (`aov_arcane_scholar`): Divination | Abjuration → Transmutation

| Pos | Perk key | Name | Magic bonus | Other modifiers |
|---|---|---|---|---|
| 0,0 | `aov_diviners_eye_perk` | Diviner's Eye | Study +25% Divination | +1 Learning |
| 0,1 | `aov_read_the_stars_perk` | Read the Stars | Cost −25% Divination | +10% lifestyle XP |
| 0,2 | `aov_prescience_perk` | Prescience | Lasts +50% Divination | −5% enemy hostile scheme success |
| 2,0 | `aov_warding_glyphs_perk` | Warding Glyphs | Study +25% Abjuration | −5% enemy hostile scheme success |
| 2,1 | `aov_arcane_reservoir_perk` | Arcane Reservoir | +50 max mana | — |
| 2,2 | `aov_spellguard_perk` | Spellguard | Cost −25% Abjuration | +2 prowess |
| 1,3 | `aov_transmuters_craft_perk` | Transmuter's Craft | Study +25% Transmutation | +1 Stewardship |
| 1,4 | `aov_ley_lines_perk` | Ley Lines | +25% mana refill; Cost −25% Transmutation | — |
| 1,5 | `aov_arcane_scholar_perk` | Arcane Scholar | grants trait `arcane_scholar` | — |

**Battle Mage** (`aov_battle_mage`): Evocation | Conjuration → war magic

| Pos | Perk key | Name | Magic bonus | Other modifiers |
|---|---|---|---|---|
| 0,0 | `aov_spark_of_battle_perk` | Spark of Battle | Study +25% Evocation | +2 prowess |
| 0,1 | `aov_overchannel_perk` | Overchannel | Cost −25% Evocation | +1 Martial |
| 0,2 | `aov_firestorm_tactics_perk` | Firestorm Tactics | Lasts +50% Evocation | +2 advantage |
| 2,0 | `aov_summoners_circle_perk` | Summoner's Circle | Study +25% Conjuration | +1 Learning |
| 2,1 | `aov_conjured_provisions_perk` | Conjured Provisions | Cost −25% Conjuration | +10% supply limit |
| 2,2 | `aov_bound_elementals_perk` | Bound Elementals | Lasts +50% Conjuration | — |
| 1,3 | `aov_battle_meditation_perk` | Battle Meditation | +100% mana refill while at war | — |
| 1,4 | `aov_mage_knight_perk` | Mage-Knight | — | +4 prowess, +20% knight effectiveness |
| 1,5 | `aov_battle_mage_perk` | Battle Mage | grants trait `battle_mage` | — |

**Mindweaver** (`aov_mindweaver`): Enchantment | Illusion → Necromancy

| Pos | Perk key | Name | Magic bonus | Other modifiers |
|---|---|---|---|---|
| 0,0 | `aov_silver_tongue_perk` | Silver Tongue | Study +25% Enchantment | +1 Diplomacy |
| 0,1 | `aov_hearts_desire_perk` | Heart's Desire | Cost −25% Enchantment | +5 general opinion |
| 0,2 | `aov_lasting_charm_perk` | Lasting Charm | Lasts +50% Enchantment | +1 Diplomacy |
| 2,0 | `aov_veil_perk` | Veil | Study +25% Illusion | +1 Intrigue |
| 2,1 | `aov_mirror_image_perk` | Mirror Image | Cost −25% Illusion | own schemes harder to discover |
| 2,2 | `aov_grand_illusion_perk` | Grand Illusion | Lasts +50% Illusion | +10 dread |
| 1,3 | `aov_grave_whispers_perk` | Grave Whispers | Study +25% Necromancy; Forbidden Magic chance halved | — |
| 1,4 | `aov_deathless_will_perk` | Deathless Will | Cost −25% Necromancy | +10% stress loss |
| 1,5 | `aov_mindweaver_perk` | Mindweaver | grants trait `mindweaver` | — |

Modifier keys (enemy scheme success, scheme discovery, advantage, supply limit, knight effectiveness, stress loss,
dread) are checked against 1.19 with tiger while building; any substitute is recorded in this spec.

### Traits

Category `lifestyle`, no XP track, granted by the final perk (`add_trait_force_tooltip`).

| Trait | Magic bonus | Modifiers |
|---|---|---|
| `arcane_scholar` | +10% study in every school, +50 max mana | +3 Learning |
| `battle_mage` | War spells cost −25% | +2 Martial, +5 prowess |
| `mindweaver` | Targeted spells cost −25% | +2 Intrigue, +1 Diplomacy |

### Focuses

Each focus also gives Study +25% in its tree's schools.

| Focus | Tree | Modifiers |
|---|---|---|
| `magic_arcane_study_focus` (new) | Arcane Scholar | +2 Learning |
| `magic_duelist_focus` (override, renamed "Battle Mage") | Battle Mage | +3 prowess (kept), +1 Martial |
| `magic_mindweaving_focus` (new) | Mindweaver | +1 Intrigue, +1 Diplomacy |

### Stacking

- Study: the focus, perk and trait bonuses add together: `aov_study_mult_<school>` = 1 + 0.25 (focus) + 0.25 (perk)
  + 0.10 (trait), at most 1.6.
- Cost: the cuts add together, and the cost is at least half the base:
  `cost = round(base × max(0.5, 1 − school cut − type cut))`.
- Duration: `years = round(base years × aov_years_mult_<school>)`, so 1 → 2 (rounded up from 1.5), 2 → 3, 3 → 5 (4.5),
  5 → 8 (7.5). Rounding is half up.
- Mana max: `100 + 50 × affinity + aov_mana_max_bonus` (perk +50, trait +50).
- Mana refill: the monthly amount × `aov_mana_refill_mult` (1 + 0.25 Ley Lines + 1.0 Battle Meditation at war).
- Dark magic: the 25% / 10% chances × `aov_dark_magic_mult` (0.5 with Grave Whispers).

### Lifestyle XP

- The focus's base 25 XP per month (Anbennar's `base_xp_gain`).
- Casting a spell (window or interaction) gives magic lifestyle XP equal to the spell's base mana cost.
- `monthly_magic_lifestyle_xp_gain_mult` gets a display format, so Anbennar's existing sources show correctly.

### Magic mastery

`magic_mastery` = sum of school levels (0-24) + magic lifestyle perks (0-27). The sync also sets
`magic_lifestyle_total_points` to the perk count, so Anbennar's character-window tooltip shows both. Every magic
perk's `effect` runs the sync; the quarterly magic pulse keeps running it too.

### AI

- Perk `auto_selection_weight`: strongly prefers the tree containing the school the mage is studying, otherwise
  the tree matching their highest skill (Learning/Stewardship: Arcane Scholar; Martial/Prowess: Battle Mage;
  Diplomacy/Intrigue: Mindweaver). Vanilla's `can_start_new_lifestyle_tree_trigger` rule is kept.
- Focus `auto_selection_weight` follows the same preference; non-mages never see the focuses (lifestyle invalid).

## Architecture

### Bonus layer

`common/script_values/aov_magic_lifestyle_values.txt` (hand-written, character scope) is the only place that
reads perks, traits and focuses for magic purposes:

| Value | Meaning | Neutral |
|---|---|---|
| `aov_study_mult_<school>` (8) | study multiplier | 1 |
| `aov_cost_cut_<school>` (8) | cost reduction for the school's spells | 0 |
| `aov_cost_cut_war`, `aov_cost_cut_targeted` | cost reduction by spell type | 0 |
| `aov_years_mult_<school>` (8) | duration multiplier | 1 |
| `aov_mana_max_bonus` | added to max mana | 0 |
| `aov_mana_refill_mult` | multiplier on monthly refill | 1 |
| `aov_dark_magic_mult` | multiplier on Forbidden Magic chance | 1 |

### Changes to sub-project 1

| File | Change |
|---|---|
| `common/script_values/aov_magic_values.txt` | `aov_mana_max` adds `aov_mana_max_bonus`; `aov_mana_refill_month` multiplies by `aov_mana_refill_mult`; study gain per school multiplies by `aov_study_mult_<school>` |
| `common/scripted_effects/aov_magic_effects.txt` | study tick uses the per-school gain; dark-magic roll uses `aov_dark_magic_mult`; mastery sync adds perks and sets `magic_lifestyle_total_points`; casting adds `add_magic_lifestyle_xp`; the Summon Elementals army is removed after `aov_spell_summon_elementals_years` instead of a fixed 3 years, so Bound Elementals extends it |
| `tools/build_spells.py` | new generated `common/script_values/aov_spell_values.txt` with `aov_spell_<key>_cost` and `aov_spell_<key>_years` per spell; cast effects, castable triggers, generated interactions, AI casting, GUI cards and loc use them instead of fixed numbers; cost/duration tooltips become per-spell keys showing the live value; school progress from casting stays at the base cost |
| `common/character_interactions/zz_aov_spell_overrides.txt` | no change: Compel, Dominate and Enhance Ability call the generated `_castable`/`_cast` blocks, so they pick up the cost values |
| `tools/tests/test_build_spells.py` | expects the values file and no fixed costs in casts, triggers or interactions |

### New hand-written files

| File | Content |
|---|---|
| `common/lifestyle_perks/aov_magic_arcane_scholar_perks.txt` | 9 perks, tree `aov_arcane_scholar` |
| `common/lifestyle_perks/aov_magic_battle_mage_perks.txt` | 9 perks, tree `aov_battle_mage` |
| `common/lifestyle_perks/aov_magic_mindweaver_perks.txt` | 9 perks, tree `aov_mindweaver` |
| `common/focuses/zz_aov_magic_focuses.txt` | two new focuses and the `magic_duelist_focus` override (`zz_` loads after Anbennar's `anb_` file) |
| `common/traits/aov_magic_lifestyle_traits.txt` | `arcane_scholar`, `battle_mage`, `mindweaver` |
| `common/script_values/aov_magic_lifestyle_values.txt` | the bonus layer |
| `common/modifier_definition_formats/aov_magic_lifestyle_formats.txt` | `monthly_magic_lifestyle_xp_gain_mult` |
| `localization/english/aov_magic_lifestyle_l_english.yml` | tree names, perk names/descriptions, trait and new focus loc, bonus tooltips |
| `localization/replace/english/aov_magic_lifestyle_replace_l_english.yml` | renames `magic_duelist_focus` to "Battle Mage" and its description |
| `tools/tests/test_magic_lifestyle.py` | content checks (below) |

Each perk's description lists its magic bonus as a `custom_description_no_bullet` line (vanilla pattern), so the
perk tooltip shows what the bonus layer does.

### New generators

**`tools/build_lifestyle_override.py`** → `gui/window_character_lifestyle.gui`
- Source: Anbennar's `gui/window_character_lifestyle.gui`, else the game's.
- After each `wanderer_lifestyle` branch it inserts the matching `magic_lifestyle` branch (focus background,
  XP progress bar, unspent-points icon), marked `# Anbennar Overhaul`.
- Fails with a clear error if the number of `wanderer_lifestyle` anchors differs from the expected count, so an
  Anbennar or CK3 change is noticed rather than half-applied.
- Added to CLAUDE.md's generated-files table and the update steps (after Anbennar updates and CK3 patches).
- Tests: `tools/tests/test_build_lifestyle_override.py` (anchors found, one insert per anchor, idempotent output,
  error on a changed source).

**`tools/build_magic_lifestyle_art.py`** (pure Python; reads and writes uncompressed 32-bit BGRA DDS, reuses
`dx10_bgra_to_legacy` from `build_inventions.py`; bilinear resize, tint and alpha compositing)

| Output | Size | Source |
|---|---|---|
| `gfx/interface/icons/lifestyles/magic_lifestyle.dds` | as `learning_lifestyle.dds` (480×160, same frame layout) | EU4 `magic_center_graphic.dds` |
| `gfx/interface/icons/lifestyles_perks/node_magic.dds` | 180×60 | vanilla `node_learning.dds`, tinted teal |
| `gfx/interface/icons/focuses/magic_arcane_study_focus.dds` | 140×140 | Guidance (Divination slot 1) |
| `gfx/interface/icons/focuses/magic_duelist_focus.dds` | 140×140 | Fireball (Evocation slot 1) |
| `gfx/interface/icons/focuses/magic_mindweaving_focus.dds` | 140×140 | Enchanting Envoy (Enchantment slot 1) |
| `gfx/interface/icons/traits/arcane_scholar.dds` | 120×120 | Foresight (Divination slot 6) |
| `gfx/interface/icons/traits/battle_mage.dds` | 120×120 | Elemental Fury (Evocation slot 6) |
| `gfx/interface/icons/traits/mindweaver.dds` | 120×120 | Dominate to Surrender (Enchantment slot 6) |
| `gfx/interface/icons/lifestyles_perks/trait_{arcane_scholar,battle_mage,mindweaver}.dds` | 120×120 | same image as the trait icon (final perks use `icon = trait_<trait>`, like vanilla `trait_scholar.dds`) |
| `gfx/interface/icons/lifestyle_tree_backgrounds/{magic_lifestyle,aov_arcane_scholar,aov_battle_mage,aov_mindweaver}.dds` | 348×812 | EU4 `magic_bg.dds` |
| `gfx/interface/illustrations/lifestyles_background/magic_lifestyle.dds` | 608×1552 | EU4 `magic_bg.dds` |
| `gfx/interface/progressbars/aov_progress_magic.dds`, `aov_progress_magic_bg.dds` | 254×64 | vanilla `progress_purple(_bg).dds`, tinted teal |

Spell icons come from the 60×60 EU4 slot strips (`magic_spell_icons_slot_<n>_60x60.dds`, one frame per school in EU4
school order), placed on a vanilla-sized frame. Paths without the `aov_` prefix are fixed by CK3's key-derived
conventions; Anbennar ships none of them today. Tests check the dimensions and DDS headers of every output.

## Verification

- Tool tests:
  - `test_magic_lifestyle.py`: 27 perks in three trees of nine, positions match the vanilla layout, every
    parent exists and sits in the row above, the final perks add the right traits, every perk/trait/focus has
    loc, every bonus-layer value names only existing perks, traits and focuses, and every value the school code
    uses exists;
  - `test_build_lifestyle_override.py` and the art tests (above);
  - updated `test_build_spells.py`.
- `python -I tools/validate.py` clean.
- In game:
  - a mage sees the Magic lifestyle with its icon, three focuses, three trees, XP bar and backgrounds; a non-mage
    does not;
  - a perk changes the study rate, spell cost or duration shown in the Magic window;
  - the final perk grants the trait;
  - casting gives magic lifestyle XP;
  - the `magic_mastery` tooltip counts levels and perks;
  - the Duelist focus shows as "Battle Mage" with its new modifiers.

## Risks

- **Third whole-file GUI override.** Rerun `build_lifestyle_override.py` after every Anbennar update and CK3 patch.
- **Engine support to confirm with tiger:** `set_variable` with `years = <script value>`,
  `add_character_modifier` with `years = <script value>`, and the generated `add_magic_lifestyle_xp` effect.
  Fallbacks: a generated if-ladder over whole years; `add_lifestyle_xp`-style effects if the per-lifestyle one
  is missing.
- **Focus override:** the later definition of `magic_duelist_focus` must win; check `database_conflicts.log`.
- **Dynamic tooltips:** per-spell cost/duration loc must evaluate in both the window (player scope) and effect
  tooltips; if an effect tooltip cannot read the caster's value, it falls back to "base cost, reduced by perks".
- **Art quality:** upscaled 60 px spell icons may look soft at 140 px.

## Out of scope

- Perks that unlock spells or gate school levels.
- Lifestyle trait XP tracks, magic artifacts, EU4 patrons and magical traditions.
- Balance tuning beyond the numbers above (sub-project 3).
