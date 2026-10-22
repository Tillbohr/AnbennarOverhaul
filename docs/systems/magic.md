# Magic schools and magic lifestyle

The Magic HUD tab sits in the generated `gui/hud.gui` (see artificery.md).

## Generated files

| File | Generator | Why |
|---|---|---|
| `gui/window_character_lifestyle.gui` | `python -I tools/build_lifestyle_override.py` | The lifestyle window is whole-file only. The script copies Anbennar's `gui/window_character_lifestyle.gui` if it has one, else the game's, and adds a `magic_lifestyle` copy after each of the three `wanderer_lifestyle` blocks (XP bar background, progress bar, unspent-points icon) using the magic art (marked `# Anbennar Overhaul: magic lifestyle`). Never edit the output by hand. |
| `common/modifiers/aov_spell_modifiers.txt`, `common/scripted_triggers/aov_spell_triggers.txt`, `common/scripted_effects/aov_spell_effects.txt`, `common/scripted_guis/aov_spell_sgui.txt`, `common/character_interactions/aov_spell_interactions.txt`, `gui/aov_magic_generated.gui`, `localization/english/aov_spells_l_english.yml`, `gfx/interface/icons/aov_magic/`, `gfx/interface/skinned/hud_maintab/aov_maintab_magic.dds` | `python -I tools/build_spells.py` | One block per spell, generated from `tools/data/spells.py` (edit the data, then rerun). The magic art (`gfx/interface/icons/aov_magic/`, the Magic tab icon) was imported once from EU4 Anbennar and is committed (not rebuilt); the build stops when a file the GUI names is missing. |
| `common/scripted_triggers/aov_advancement_triggers.txt`, `common/script_values/aov_advancement_values.txt`, `common/scripted_effects/aov_advancement_effects.txt`, `common/scripted_guis/aov_advancement_sgui.txt`, `gui/aov_advancements_generated.gui`, `localization/english/aov_advancements_l_english.yml` | `python -I tools/build_advancements.py` | One block per advancement (start, can-start, costs, completion dispatch, AI pick, Advancements page), generated from `tools/data/advancements.py`. Costs and durations are the generator's `GOLD`/`MANA`/`YEARS`. EU4's project plate and progress bar (`gfx/interface/icons/aov_magic/project_*.dds`) were imported once and are committed. |

## Imported files (no generator)

The magic lifestyle art (18 DDS files: `gfx/interface/icons/{lifestyles,focuses,traits,lifestyles_perks,lifestyle_tree_backgrounds}/`
magic files, `gfx/interface/illustrations/lifestyles_background/magic_lifestyle.dds`,
`gfx/interface/progressbars/aov_progress_magic*.dds`) was composed once from EU4 Anbennar magic art and vanilla files.
Its generator `tools/build_magic_lifestyle_art.py` was removed; replace the files directly to change them.

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
  magic lifestyle XP. `magic_mastery` = school levels + magic perks. The art is imported (above); the lifestyle window override comes from
  `tools/build_lifestyle_override.py`. Spec
  `docs/superpowers/specs/2026-10-08-magic-lifestyle-design.md`.
- **Magic advancements:** one three-level advancement per school, adapted from EU4 Anbennar's magical projects
  (spec `docs/superpowers/specs/2026-10-22-magic-advancements-design.md`): Magical Fortress (wards: county modifiers
  re-laid yearly), Summon Extraplanars (a host's men-at-arms and base-type boosts), Orb of Omniscience (court artifact;
  boosts Scry, Foresight, Manipulated Fortune), Enchanted Artifact (one weapon/armor/crown/regalia/trinket per mage,
  strengthened each level; the trinket feeds mana and spell cost), Battlemage Academy (building tiers
  `battlemage_academy_01-03`, Recruit Battlemage Commander decision, Battlemages men-at-arms), Mirror Image (+1 all
  skills per level, body double on imprisonment), Lichdom (phylactery artifact, prisoner sacrifice, Anbennar's `lich`
  trait; losing the phylactery before the ritual drops it to level 1), Homunculus (`aov_homunculus` courtier, domain
  labour). Ruling mages only (`aov_adv_eligible`: landed + Magical Affinity). Level N needs school level N; a level
  costs gold and mana up front and completes on the quarterly tick. A mage either studies or works on one advancement
  (starting clears `aov_studying`; the Study buttons are invalid while `aov_adv_committed` is set); Abandon refunds
  nothing. State: `aov_adv_committed`, `aov_adv_working_level`, `aov_adv_progress`, `aov_adv_<key>_lvl`, plus
  `aov_adv_orb`, `aov_adv_enchanted_*`, `aov_adv_phylactery`, `aov_adv_host`, `aov_adv_homunculus`; all die with the
  mage, while artifacts, homunculi, buildings and regiments remain. Hand-written: level effects
  `common/scripted_effects/aov_advancement_level_effects.txt`, start conditions
  `common/scripted_triggers/aov_advancement_conditions.txt`, events `events/aov_advancement_events.txt`, modifiers,
  men-at-arms, building, decision, trait, templates, on_actions (`aov_advancement_*`). Every balance number is in
  `common/script_values/aov_advancement_tuning.txt`. The Magic window (`gui/aov_window_magic.gui`) has Advancements and
  Spells tabs under the school buttons (GUI variable `aov_magic_tab`, unset = Advancements); study progress shows on
  the Spells tab's school header.
