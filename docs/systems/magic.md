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

The HUD alert for unspent magic perks, `gfx/interface/icons/alerts/aov_action_lifestyle_magic.dds` (3 frames of 144,
like vanilla's `action_lifestyle_*.dds`), was composed once: the flame of `magic_lifestyle.dds` on the game's
`_frame_purple.dds`. Its alert `aov_action_lifestyle_magic` is in `common/important_actions/aov_magic_lifestyle_actions.txt`;
vanilla's generic `action_can_spend_perk_point` is overridden in `zz_aov_lifestyle_actions.txt` to skip magic focuses
(`aov_has_focus_magic`), so a mage sees the magic alert instead of the generic arrows.

The Lich portrait (Godherja's skeleton, art from Elder Kings) was imported once with a scratch script and is edited by
hand: meshes and textures in `gfx/models/portraits/aov_lich/` (`aov_lich.asset`), accessories
`gfx/portraits/accessories/aov_lich.txt`, rune and gem-eye variations `gfx/portraits/accessory_variations/aov_lich.txt`
(textures in `textures/aov_lich/`); every name is prefixed `aov_`. The genes `common/genes/aov_lich_genes.txt`
(`aov_lich_flesh` hides the living head and body with vanilla's `bs_no_portrait` blend shapes; `aov_lich_head`,
`aov_lich_body`, `aov_lich_eyes`; index 0 of each is nothing) are applied by
`gfx/portraits/portrait_modifiers/aov_lich.txt` to anyone with the `lich` trait, which also removes eyes, lashes,
teeth, hair and beard. Clothes and headgear are untouched. The RiE portrait generator's orphan check skips this folder.

## System

- **Magic schools:** eight schools (Abjuration, Conjuration, Divination, Enchantment, Evocation, Illusion, Necromancy,
  Transmutation) for mages (`has_magical_affinity`, Anbennar). Mana (100 + 50 per affinity level, refilled quarterly at
  3x the monthly rate), per-school knowledge levels 0-3 (300/800/2000 progress) from studying one chosen school and
  from casting; reaching a level stops the study of that school until the mage presses Study again (AI mages re-pick) (choosing a new school with the Study button opens event `aov_magic.2`, the mage reading in a study;
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
  `battlemage_academy_01-03`, Recruit Battlemage Commander decision (the recruit is a gender your faith and culture let lead armies, vanilla's `root_soldier_female_chance`), Battlemages men-at-arms), Mirror Image (+1 all
  skills per level, body double on imprisonment), Lichdom (EU4's Pursue Lichdom: The Phylactery, The Transformation
  Potion, The Dark Ritual, three choice-event steps each in `events/aov_lichdom_events.txt`; the mage drinks the potion,
  dies and rises with Anbennar's `lich` trait and Forbidden Magic Practitioner whatever the faith, no prisoner needed;
  losing the phylactery before then starts Lichdom over), Homunculus (`aov_homunculus` courtier, domain labour). Ruling mages only (`aov_adv_eligible`: landed + Magical Affinity). Level N needs school level N; a level
  costs gold and mana up front and completes on the quarterly tick. A mage either studies or works on one advancement
  (starting clears `aov_studying`; the Study buttons are invalid while `aov_adv_committed` is set); Abandon refunds
  nothing. A level that fires its own event instead of the success one saves scope:aov_adv_own_event: a lost Orb or
  enchanted artifact ends the work (event 44); the Dark Ritual ends in Consumption (`aov_lichdom.10`). Lichdom's steps:
  the generated start effect calls the data's `on_start` hook (`aov_adv_lichdom_on_start`, the first step); the
  quarterly pulse fires the next one at a third and two thirds of the level's months (`aov_adv_lichdom_steps`,
  `var:aov_lichdom_step`); faster choices add progress capped by `aov_lichdom_progress_cap` so every step still fires. A mage who stops being a ruling mage abandons the commitment (quarterly tick; `on_title_lost`). State: `aov_adv_committed`, `aov_adv_working_level`, `aov_adv_progress`, `aov_adv_<key>_lvl`, plus
  `aov_adv_orb`, `aov_adv_enchanted_*`, `aov_adv_phylactery`, `aov_lichdom_vessel`, `aov_lichdom_step`, `aov_adv_host`, `aov_adv_homunculus`; all die with the
  mage, while artifacts, homunculi, buildings and regiments remain. Hand-written: level effects
  `common/scripted_effects/aov_advancement_level_effects.txt`, start conditions
  `common/scripted_triggers/aov_advancement_conditions.txt`, events `events/aov_advancement_events.txt`, modifiers,
  men-at-arms, building, decision, trait, templates, on_actions (`aov_advancement_*`). Every balance number is in
  `common/script_values/aov_advancement_tuning.txt`. The Magic window (`gui/aov_window_magic.gui`) has Advancements and
  Spells tabs under the school buttons (GUI variable `aov_magic_tab`, unset = Advancements); study progress shows on
  the Spells tab's school header.
- **Mage men-at-arms:** Anbennar's Battlemages (`battlemages`, shown as War Mages so they differ from the academy's
  own Battlemages) are recruited from a Battlemage Academy of tier 2 or more instead of the Magic Schools innovation;
  the academy also recruits `aov_battlemages` (tier 2) and `aov_battlemages_3` (tier 3). Storm Sorcerers are disabled
  (`can_recruit = { always = no }`; gnomes field artificers instead), their tradition
  `tradition_test_maa_anb_storm_sorcerers` hidden, unpickable and removed from every culture at game start
  (`common/on_action/aov_mage_maa_on_actions.txt`). Both units are Anbennar's blocks with only `can_recruit` changed
  (`common/men_at_arms_types/zz_aov_mage_maa_overrides.txt`, tradition in
  `common/culture/traditions/zz_aov_mage_traditions.txt`); `common/culture/innovations/zz_aov_mage_innovations.txt`
  drops the unit line from Magic Schools, which keeps its +10% magic lifestyle experience. Druids, Wren Hedge Witches,
  Bladedancers and Skalds are unchanged. `tools/tests/test_cultural_maa.py` fails when Anbennar changes a copied block
  or adds a cultural mage unit.
