# Magic schools and magic lifestyle

The Magic HUD tab sits in the generated `gui/hud.gui` (see artificery.md).

## Generated files

| File | Generator | Why |
|---|---|---|
| `gui/window_character_lifestyle.gui` | `python -I tools/build_lifestyle_override.py` | The lifestyle window is whole-file only. The script copies Anbennar's `gui/window_character_lifestyle.gui` if it has one, else the game's, and adds a `magic_lifestyle` copy after each of the three `wanderer_lifestyle` blocks (XP bar background, progress bar, unspent-points icon) using the magic art (marked `# Anbennar Overhaul: magic lifestyle`). Never edit the output by hand. |
| `common/modifiers/aov_spell_modifiers.txt`, `common/scripted_triggers/aov_spell_triggers.txt`, `common/scripted_effects/aov_spell_effects.txt`, `common/scripted_guis/aov_spell_sgui.txt`, `common/character_interactions/aov_spell_interactions.txt`, `gui/aov_magic_generated.gui`, `localization/english/aov_spells_l_english.yml`, `gfx/interface/icons/aov_magic/`, `gfx/interface/skinned/hud_maintab/aov_maintab_magic.dds` | `python -I tools/build_spells.py` | One block per spell, generated from `tools/data/spells.py` (edit the data, then rerun). |
| `gfx/interface/icons/{lifestyles,focuses,traits,lifestyles_perks,lifestyle_tree_backgrounds}/` magic files, `gfx/interface/illustrations/lifestyles_background/magic_lifestyle.dds`, `gfx/interface/progressbars/aov_progress_magic*.dds` | `python -I tools/build_magic_lifestyle_art.py` | Magic lifestyle art (18 DDS files) composed from EU4 Anbennar magic art and uncompressed vanilla files; the output list is `OUTPUTS` in the script. |

## System

- **Magic schools:** eight schools (Abjuration, Conjuration, Divination, Enchantment, Evocation, Illusion, Necromancy,
  Transmutation) for mages (`has_magical_affinity`, Anbennar). Mana (100 + 50 per affinity level, refilled quarterly at
  3x the monthly rate), per-school knowledge levels 0-3 (300/800/2000 progress) from studying one chosen school and
  from casting (choosing a new school with the Study button opens event `aov_magic.2`, the mage reading in a study;
  AI mages skip it); `magic_mastery` = sum of levels. 48 spells in `tools/data/spells.py` (spec
  `docs/superpowers/specs/2026-10-08-magic-schools-design.md`): self/realm/war spells cast from the Magic window
  (`gui/aov_window_magic.gui`, HUD tab below Artificery, generated pages `gui/aov_magic_generated.gui`), targeted
  spells as interactions in Anbennar's Spells category (Compel, Dominate overridden to need mana and knowledge;
  Anbennar's Enhance Ability is removed from the game by a hidden stub override). Necromancy risks Forbidden Magic Practitioner under witchcraft-illegal/shunned faiths. Hand-written
  logic in `aov_magic_*` files; Summon Elementals spawns an army removed after the spell's duration (`aov_spell_summon_elementals_years`, extended by Bound Elementals).
- **Magic lifestyle:** fills the "Known gaps" magic-lifestyle skeleton listed in the base mod's CLAUDE.md (which cannot be edited). Anbennar's stub `magic_lifestyle` made full: three trees of 9 perks (Arcane Scholar, Battle Mage,
  Mindweaver; `common/lifestyle_perks/aov_magic_*_perks.txt`), each ending in a trait
  (`common/traits/aov_magic_lifestyle_traits.txt`), and three focuses (`common/focuses/zz_aov_magic_focuses.txt`;
  Anbennar's `magic_duelist_focus` is overridden as Battle Mage, name via `localization/replace/`). Mages only: every
  magic focus has `is_shown`/`is_valid` and every magic perk `can_be_picked` = `has_trait = magical_affinity`, because
  the engine picks game-start focuses and perks by `auto_selection_weight` without checking the lifestyle's `is_valid`
  (`MagesOnlyTests`). Perks feed magic only
  through `common/script_values/aov_magic_lifestyle_values.txt` (the bonus layer: study rate, spell cost and duration,
  mana, dark-magic risk), so tune balance there. Spell cost and duration are per-caster values
  `aov_spell_<k>_cost` / `_years` generated into `common/script_values/aov_spell_values.txt`; casting also grants
  magic lifestyle XP. `magic_mastery` = school levels + magic perks. Art and the lifestyle window override come from
  `tools/build_magic_lifestyle_art.py` and `tools/build_lifestyle_override.py`. Spec
  `docs/superpowers/specs/2026-10-08-magic-lifestyle-design.md`.
