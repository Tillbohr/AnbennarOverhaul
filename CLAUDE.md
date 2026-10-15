# Anbennar Overhaul — project notes

Submod for the Anbennar CK3 total conversion. **All new content goes here; the base Anbennar mod
(`../anbennar-ck3-dev-master`) stays an unmodified upstream copy** so the overhaul can be laid over any
new Anbennar version. Targets CK3 **1.19.0.6**. Base-mod conventions, paths and reference-mod notes
(imported below) apply here too, except that this repo is the one you edit.

@../anbennar-ck3-dev-master/CLAUDE.md

## Dev environment

- Start Claude Code **in this folder**. `.claude/settings.local.json` (machine-specific, git-ignored) grants
  access to the base mod, game install, Workshop mods, logs and ck3-tiger.
- Git repo on `main` → https://github.com/Tillbohr/AnbennarOverhaul (public), `core.autocrlf=false`;
  `.gitattributes` keeps `.txt`/`.yml`/`.mod` bytes exact (UTF-8 BOM + LF) and sends `.tga`/`.psd` to Git LFS.
- Base mod is read-only in practice: read it for reference, never write to it.

| Task | Command |
|---|---|
| Validate (new reports only) | `python -I tools/validate.py` |
| Validate (everything) | `python -I tools/validate.py --all` |
| Accept current reports as baseline | `python -I tools/validate.py --baseline` (only after confirming they are inherited from Anbennar or from a file copied verbatim from Realms in Exile) |
| Rebuild holdings override | `python -I tools/build_holdings_override.py` |
| Rebuild dwarven holds | `python -I tools/build_holds.py` (copies Anbennar's castle assets into the hold levels) |
| Rebuild governments override | `python -I tools/build_governments_override.py` |
| Rebuild HUD override | `python -I tools/build_hud_override.py` |
| Rebuild lifestyle window override | `python -I tools/build_lifestyle_override.py` |
| Rebuild county view override | `python -I tools/build_county_view_override.py` |
| Import EU4 monuments | `python -I tools/import_eu4_monuments.py --region <name>` (`cannor`, `dwarovar`, `bulwar`, `salahad`, `deepwoods`; needs the EU4 Anbennar, Cannorian and Dwarven Monuments mods installed; rewrites `tools/data/monuments/<region>.py`) |
| Rebuild monuments | `python -I tools/build_monuments.py` (every region; `--region <name>` for one, the shared illustration file is always rebuilt from all) |
| Run tool tests | `python -I -m unittest discover -s tools/tests -v` |
| Rebuild inventions | `python -I tools/build_inventions.py` (needs EU4 Anbennar installed for icons) |
| Rebuild spells | `python -I tools/build_spells.py` (needs EU4 Anbennar installed for magic art) |
| Rebuild magic lifestyle art | `python -I tools/build_magic_lifestyle_art.py` (needs EU4 Anbennar and CK3 installed) |
| Rebuild map graphics | `python -I tools/build_map_graphics.py` (needs Realms in Exile installed) |
| Rebuild holding models | `python -I tools/build_holding_models.py` (needs Realms in Exile installed) |

## Loading

| What | Where |
|---|---|
| Submod folder | this folder |
| Launcher descriptor | `../anbennar_overhaul.mod` (absolute `path=`); in-folder `descriptor.mod` mirrors it |
| Dependency | `dependencies = { "anbennar-ck3-dev" }`; in the playset, Anbennar Overhaul must load **after** Anbennar |

## Rules for keeping the base clean

- Never edit files in the base mod. Prefer, in order:
  1. **New files** with the `aov_` prefix (`common/buildings/aov_*.txt`, `localization/english/aov_*_l_english.yml`).
     The prefix keeps paths from colliding with future Anbennar files (a same-path file silently replaces the other).
  2. **Appended on_actions** (`on_actions = { aov_... }` inside a vanilla on_action name) and game-start effects
     instead of editing history or culture files. Example: gnomish cultures get their tradition in
     `aov_gnomish_ingenuity_game_start`, not in `anb_gnome.txt`.
  3. **Single-object overrides** in an `aov_`/`zz_aov_` file, for databases that support them.
  4. **Generated full-file overrides** only for whole-file-only databases. The file is rebuilt from the base
     by a script so it can be regenerated after every Anbennar update.
- Keys are not prefixed (`tradition_gnomish_ingenuity`, `artificer_academy_01`, `artificer_handgunners`). If Anbennar
  ever adds the same key, the later-loaded definition wins; check `database_conflicts.log` after updates.

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/holdings/00_holdings.txt` | `python -I tools/build_holdings_override.py` | Holdings are whole-file only. The script copies Anbennar's file, inserts the `ADDITIONS` (marked `# Anbennar Overhaul`) and appends the new `dwarven_hold_holding` (`NEW_HOLDINGS`: castle_holding's build list after `ADDITIONS` plus deep mine, runeforge and hall of the ancestors). Never edit the output by hand. |
| `common/governments/00_government_types.txt`, `common/governments/01_japan_government_types.txt` | `python -I tools/build_governments_override.py` | Governments are whole-file only. The script copies Anbennar's two files and adds `dwarven_hold_holding` to `valid_holdings` of every government whose `primary_holding` or `valid_holdings` has `castle_holding` (creating the line after `primary_holding` when absent; changed lines marked `# Anbennar Overhaul`). Never edit the output by hand. |
| `common/buildings/aov_dwarven_holds.txt`, `common/script_values/aov_hold_values.txt`, `common/scripted_effects/aov_hold_setup_effects.txt`, `common/modifiers/aov_hold_modifiers.txt`, `localization/english/aov_holds_l_english.yml` | `python -I tools/build_holds.py` | Dwarven hold data from `tools/data/holds.py` (edit the data, then rerun): the 10 `dwarven_hold_01..10` levels (castle assets copied from Anbennar) and the deep mine, runeforge and hall of the ancestors buildings; script values (dig cost and months per level, level numbers); the game-start setup effect (levels and ruin of the 9 holds); the level modifiers and the `aov_delving_02..10` dig markers; and their localization. |
| `gui/hud.gui` | `python -I tools/build_hud_override.py` | The main tab bar is whole-file only. The script copies Anbennar's `gui/hud.gui` if it has one, else the game's, and inserts the Artificery tab after `tab_situation` (marked `# Anbennar Overhaul`). Never edit the output by hand. |
| `gui/window_character_lifestyle.gui` | `python -I tools/build_lifestyle_override.py` | The lifestyle window is whole-file only. The script copies Anbennar's `gui/window_character_lifestyle.gui` if it has one, else the game's, and adds a `magic_lifestyle` copy after each of the three `wanderer_lifestyle` blocks (XP bar background, progress bar, unspent-points icon) using the magic art (marked `# Anbennar Overhaul: magic lifestyle`). Never edit the output by hand. |
| `gui/window_county_view.gui` | `python -I tools/build_county_view_override.py` | The county view is whole-file only. The script copies Anbennar's `gui/window_county_view.gui` if it has one, else the game's, and inserts one `background` per EU4 monument painting (`build_monuments.painting_backgrounds`) inline right after the vanilla holding-illustration `background`, covering the holding panel down to the garrison box (`margin_bottom = 63`, above the building slot row) top-aligned (`fittype = start`, so the top is never trimmed; marked `# Anbennar Overhaul: monument painting`); the vanilla holding illustration's `visible` also requires an empty `AovMonumentIllustration`. Never use a `using` template for these: template backgrounds draw beneath every inline background (the panel's dark background covered them). It also adds a dwarven hold's dig progress bar (`DIG_BLOCK`, marked `# Anbennar Overhaul: hold dig progress`) after vanilla's holding-construction bar, shown while the province has `aov_dig_target_level`; it reads `aov_dig_percent` and `aov_dig_years_left` (`common/script_values/aov_hold_view_values.txt`), text in `aov_hold_view_l_english.yml`. Rerun after `build_monuments.py` when monuments change. Never edit the output by hand. |
| `gfx/interface/illustrations/aov_monuments/*.dds`, `common/customizable_localization/aov_monument_illustration.txt`, `localization/english/aov_monument_illustration_l_english.yml`, `gfx/interface/window_county/aov_monument_painting_mask.dds` | `python -I tools/build_monuments.py` | EU4 monument paintings (uncompressed BGRA, 572x272: EU4's 300x150 with its baked-in dark name plate lifted (`lift_title_strip`), its 6 px frame and the bleed row next to it cropped (`crop_frame`) and a Lanczos-3 2x upscale (`upscale_2x`)), drawn at full alpha through a lighter generated mask (95% in the middle, short soft edges, drawn top-aligned (`fittype = start`, spires reach the frame); vanilla's holding mask peaks at ~67%); custom loc `AovMonumentIllustration` (province scope; the text of loc key `aov_monument_art_<eu4key>` for the province's monument, else empty; keys defined once in the shared loc file). `EXTRA_ART` adds non-monument pictures after the monument entries: ruined holds (`aov_hold_is_ruined`) show vanilla's ruined-holding picture, and a monument painting takes priority. The county view override draws each painting as a `background` with a fixed texture path, visible when `EqualTo_string(Custom('AovMonumentIllustration'), Localize('aov_monument_art_<eu4key>'))`. CK3 does not load a texture whose path comes from custom loc, so never bind `texture` to it. |
| `common/modifiers/aov_invention_modifiers.txt`, `common/scripted_triggers/aov_invention_triggers.txt`, `common/script_values/aov_invention_values.txt`, `common/scripted_effects/aov_invention_effects.txt`, `common/scripted_guis/aov_invention_sgui.txt`, `common/customizable_localization/aov_invention_custom_loc.txt`, `gui/aov_inventions_generated.gui`, `localization/english/aov_inventions_l_english.yml`, `gfx/interface/icons/aov_inventions/` | `python -I tools/build_inventions.py` | One block per invention, generated from `tools/data/inventions.py` (edit the data, then rerun). |
| `common/modifiers/aov_spell_modifiers.txt`, `common/scripted_triggers/aov_spell_triggers.txt`, `common/scripted_effects/aov_spell_effects.txt`, `common/scripted_guis/aov_spell_sgui.txt`, `common/character_interactions/aov_spell_interactions.txt`, `gui/aov_magic_generated.gui`, `localization/english/aov_spells_l_english.yml`, `gfx/interface/icons/aov_magic/`, `gfx/interface/skinned/hud_maintab/aov_maintab_magic.dds` | `python -I tools/build_spells.py` | One block per spell, generated from `tools/data/spells.py` (edit the data, then rerun). |
| `gfx/interface/icons/{lifestyles,focuses,traits,lifestyles_perks,lifestyle_tree_backgrounds}/` magic files, `gfx/interface/illustrations/lifestyles_background/magic_lifestyle.dds`, `gfx/interface/progressbars/aov_progress_magic*.dds` | `python -I tools/build_magic_lifestyle_art.py` | Magic lifestyle art (18 DDS files) composed from EU4 Anbennar magic art and uncompressed vanilla files; the output list is `OUTPUTS` in the script. |
| `common/buildings/zz_aov_monument_overrides_cannor.txt` (with `common/buildings/aov_monuments_cannor.txt`, `history/provinces/aov_monuments_cannor.txt`, `localization/english/aov_monuments_cannor_l_english.yml`) | `python -I tools/build_monuments.py` | Cannor great-project buildings from `tools/data/monuments/cannor.py`. The `zz_` file re-emits the 17 Anbennar monument levels (copied from Anbennar's current definitions) with the EU4 tier modifiers, `on_complete` and `next_building` inserted, marked `# Anbennar Overhaul: EU4 tier <n>`; Anbennar's own triggers are untouched. The new upper levels of those chains (in `aov_monuments_cannor.txt`) are copies of the chain's top Anbennar level with the EU4 tier merged the same way (EU4 culture gate in `can_construct` only), because a CK3 upgrade replaces the previous level's effects. The script validates the data first and stops on a placement, name, icon, modifier-key or empty-level problem. |
| `common/buildings/aov_monuments_dwarovar.txt`, `history/provinces/aov_monuments_dwarovar.txt`, `localization/english/aov_monuments_dwarovar_l_english.yml` | `python -I tools/build_monuments.py` | Middle Dwarovar great-project buildings from `tools/data/monuments/dwarovar.py` (no Anbennar levels, so no overrides file). |
| `common/buildings/aov_monuments_<region>.txt`, `history/provinces/aov_monuments_<region>.txt`, `localization/english/aov_monuments_<region>_l_english.yml` for `bulwar`, `salahad`, `deepwoods` | `python -I tools/build_monuments.py` | Great-project buildings of the rest of the map from `tools/data/monuments/<region>.py` (no Anbennar levels, so no overrides files). |
| `gfx/FX/` (16 shader files, plus `gfx/FX/court_scene.shader`: Anbennar's file with RiE's placeholder map-object effects appended so the gate mesh loads), `gfx/map/terrain/` (materials, textures), `gfx/map/environment/`, `gfx/map/water/`, `gfx/map/fog_of_war/`, `gfx/map/post_effects/`, `gfx/map/map_object_data/`, `gfx/models/mapitems/` (skybox), `common/defines/graphic/aov_map_graphics_defines.txt` (camera tilt), `map_data/heightmap.png`, `map_data/packed_heightmap.png`, `map_data/indirection_heightmap.png`, `map_data/heightmap.heightmap` (raised dwarven mountains, whole-file overrides of Anbennar's), `gfx/map/map_object_data/aov_dwarven_gates.txt`, `gfx/map/map_object_data/aov_dwarven_gate_overlays.txt`, `gfx/models/mapitems/aov_dwarven_gate/` (gate and composition assets, meshes, textures), `gfx/map/terrain/detail_index.tga`, `gfx/map/terrain/detail_intensity.tga` (Anbennar's terrain blend maps with unpainted pixels filled, whole-file overrides) | `python -I tools/build_map_graphics.py` | Realms in Exile's map look, 101 files (~547 MiB, `.dds`/`.mesh`/`.tga`/height `.png` via Git LFS) copied or rewritten from RiE and Anbennar by `tools/data/map_graphics.py`; the settings, `posteffect_volumes.txt` and the snow `Texture_Index` are rewritten, and the height files and gate objects are computed from Anbennar's heightmap, provinces and titles (`build_heightmap`, `tools/pngio.py`), so never edit the output by hand. Rerun after a RiE or Anbennar update, and after any Anbennar map change (provinces, terrain, heightmap, titles). |
| `common/culture/cultures/anb_elven.txt`, `anb_dwarf.txt`, `anb_escanni.txt` (the Anbennar files holding the 28 target cultures; derived from the data), `common/scripted_triggers/aov_holding_model_triggers.txt`, `common/buildings/zz_aov_holding_models.txt`, `common/buildings/aov_holding_walls.txt`, `common/buildings/zz_aov_holding_walls.txt`, `localization/english/aov_holding_models_l_english.yml`, `gfx/models/buildings/aov_rie_holdings/<group>/` (high_elf, wood_elf, dwarven, castanorian) | `python -I tools/build_holding_models.py` | RiE's holding models from `tools/data/holding_models.py` (edit the data, then rerun). The culture files are whole-file copies of Anbennar's with only the target cultures' `building_gfx` lines changed (a new `aov_*_building_gfx` key first; marked `# Anbennar Overhaul`). `zz_aov_holding_models.txt` re-emits Anbennar's castle/temple 01-04 and the game's city 01-04 and tribe_01/02 with RiE assets inserted before the first asset (illustration and sound copied from it; the source files' `@illustration` variables are redefined at the top, prefixed `castle_`/`city_`/`temple_` because the sources reuse names with different values). `aov_holding_walls.txt` defines the background building `aov_elven_walls`; `zz_aov_holding_walls.txt` re-emits Anbennar's `walls_01_tribal`, `walls_01..04` byte-exact with one line inserted at the start of each `is_enabled` (`NOT = { scope:holder ?= { culture = { OR = { has_building_gfx = <elf keys> } } } } # Anbennar Overhaul: elven walls`). There is no graphical region file any more. Asset, mesh and texture files (~17 MiB; `.mesh`/`.dds` via Git LFS) are copied from RiE; the build stops on a missing file, a name collision or a shader without its `_mapobject` effect. Never edit the output by hand; rerun after an Anbennar or RiE update. `tools/tests/test_build_holding_models.py` (`FreshnessTests`) fails when the files are stale. |

## Updating to a new Anbennar version

1. Replace `../anbennar-ck3-dev-master` with the new Anbennar release.
2. Run `python -I tools/build_holdings_override.py` and `python -I tools/build_holds.py` and `python -I tools/build_governments_override.py` and `python -I tools/build_hud_override.py` and `python -I tools/build_lifestyle_override.py` and `python -I tools/build_county_view_override.py`, and `python -I tools/build_map_graphics.py`, and `python -I tools/build_holding_models.py` (the culture files are whole-file overrides of Anbennar's) and `python -I tools/build_monuments.py` (the monument overrides copy Anbennar's current definitions; it errors naming any monument key Anbennar no longer defines). The `map_data/` height files are whole-file overrides of Anbennar's, regenerated from its new heightmap by `build_map_graphics.py`.
3. Run tiger and the tool tests (below) and fix anything that references renamed Anbennar content. The tests fail if
   Anbennar renames `anb_enhance_ability_interaction` or adds another way to start its Enhance Ability scheme (removed
   from the game; see `EnhanceAbilityRemovedTests`).
4. Re-copy Anbennar's `title_revocation_standard_can_pick_title_trigger` (`common/scripted_triggers/00_interaction_triggers.txt`)
   into `common/scripted_triggers/zz_aov_interaction_triggers.txt`, keeping the `# Anbennar Overhaul` faction-title exclusion.
5. Re-copy Anbennar's `building_requirement_castle_city_church` and
   `building_requirement_castle_city_church_temple_citadel_tribe` (`common/scripted_triggers/00_building_requirement_triggers.txt`)
   into `common/scripted_triggers/zz_aov_building_requirement_triggers.txt`, keeping the `# Anbennar Overhaul` dwarven
   hold branch (castle levels 01/02/03/04 = hold levels 1/3/5/8). `BuildingRequirementOverrideTests` fails until they match.
6. Re-copy Anbennar's `start_compel_interaction` and `start_dominate_interaction` into
   `common/character_interactions/zz_aov_spell_overrides.txt`, keeping the `# Anbennar Overhaul` lines. Its
   `anb_enhance_ability_interaction` is a never-shown stub and needs no re-copy.
7. Test in game; check `database_conflicts.log` for overhaul keys now also defined by Anbennar (notably `magic_duelist_focus`, which `zz_aov_magic_focuses.txt` must keep overriding).

After a CK3 patch, rerun `python -I tools/build_hud_override.py`, `python -I tools/build_lifestyle_override.py` and `python -I tools/build_county_view_override.py` too: their sources are the game's `hud.gui`, `window_character_lifestyle.gui` and `window_county_view.gui` (when Anbennar ships no copy).
Rerun `python -I tools/build_map_graphics.py` too once Realms in Exile has updated for the patch (its shaders are the source).
Rerun `python -I tools/build_holding_models.py` too after a CK3 patch (`city_01..04` are copied from the game) and after a Realms in Exile update (its holding models and shaders are the source).

## Validation

`python -I tools/validate.py` runs ck3-tiger with `--suppress tools/tiger_baseline.json`, so it prints only
reports that are not in the baseline (it ends `fatal: 0, error: 0, ...` when clean). `ck3-tiger.conf` loads the
base mod via its in-folder `descriptor.mod`; pointing it at the launcher's `../descriptor.mod` makes tiger load
the whole `mod/` folder instead. Current baseline: 4 `temple_citadel_holding` modifier-format warnings,
inherited from Anbennar's holdings file, and 1 `other_rulers` missing-item error in the generated `gui/hud.gui`
(vanilla HUD code referring to a dynastic-cycle group that Anbennar's `tgp_dynastic_cycle.txt` drops), and 5 missing `<government>_realm` localization warnings in the generated government files (celestial, steppe_admin, meritocratic, japan_administrative, japan_feudal; Anbennar and vanilla lack them too), and 2 warnings on
`relative_fog_color` in the copied RiE `gfx/map/environment/environment.txt` (RiE's value, kept so the lighting matches; vanilla's `environment.txt` has the identical line, so this is a tiger false positive on a vanilla value). 1 `duplicate-item` warning for `ZOOM_STEPS_MIN_TILT` in `common/defines/graphic/aov_map_graphics_defines.txt` (intended: it overrides Anbennar's and vanilla's value, the later-loaded mod wins; tiger flags every cross-mod define override). The baseline's `other_rulers` entry had its `linenr` refreshed from a stale 1722 to 1742 (same report, no new one).
75 reports in the generated `common/buildings/zz_aov_holding_models.txt`, all in code copied verbatim from Anbennar's
castle/temple and the game's city buildings (Anbennar drops these vanilla graphical faiths and entities): 8 errors for
`building_emishi_temple_01/02_entity`, 62 warnings for the graphical faiths `zoroastrian_gfx`, `shinto_gfx`,
`tengrism_gfx`, `kamuyism_gfx`, and 5 mandala-effect scope warnings. Regenerating that file can shift their line
numbers; re-baseline only after checking that the new reports are the same ones. 9 more, again verbatim copies: 2 errors for `building_emishi_tribal_01/02_mesh` and 1 warning each for the game's duplicate `next_building = tribe_02` and an `OR` tooltip complexity in `tribe_01/02` (all in `zz_aov_holding_models.txt`), and 5 errors for `building_emishi_wall_01..04_mesh` (`walls_01_tribal` and `walls_01` hold two) in `zz_aov_holding_walls.txt`.

## Systems

- **Gnomish artificery:** `tradition_gnomish_ingenuity` (gnomish heritage only; added to all gnomish cultures on
  game start; stripped from non-gnomes on culture creation/tradition add) → `artificer_academy_01` (regular
  castle/city building, university icon and modifiers, one per ruler's domain, all of a ruler's academies disabled
  if they hold 2+) → `artificer_handgunners` MaA (handgunner stats, needs the tradition and an enabled academy in
  the recruiter's domain).
- **Artificery tab:** HUD main tab below Situations (`gui/hud.gui`, generated) shown when the player passes
  `can_use_artificery_trigger` (gnome race, Gnomish Ingenuity culture, exactly one academy) via scripted GUI
  `aov_artificery_available`. Opens `gui/aov_window_artificery.gui` (scripted widget, variable
  `aov_artificery_window`) with Factions/Inventions tabs (variable `aov_artificery_tab`, unset = Factions).
- **Artificery inventions:** 60 inventions in `tools/data/inventions.py` (EU4 Anbennar mapping in
  `docs/research/2026-10-08-eu4-artificer-inventions.md`). Research sponsored by Brillites (5 y, random),
  Mechanists (10 y, chosen field) or Technomancers (15 y, chosen invention); cost and time set by that faction's
  influence (below); tiers gated by culture
  era; 3/4/5 slots with a 1-year cooldown; state in ruler variables, inherited by the heir; dormant while
  ineligible. Logic in `aov_artificery_research_*` files and `common/on_action/aov_inventions_on_actions.txt`.
- **Inventions tab UI:** EU4-style. Tier I/II/III tabs (variable `aov_inventions_tier`, unset = I), each with
  Society/Economic/Military sections of invention boxes (generated types `aov_inventions_tier_<n>`), drawn with EU4
  Anbennar's inventions-menu buttons (`aov_invention_button_<category>.dds`, frames: locked/undiscovered, discovered,
  active; converted from DX10 by the generator). Clicking a box
  runs `aov_inv_<key>_toggle_sgui` (activate, or deactivate with the slot cooldown); hovering shows
  `aov_invention_<key>_tooltip` (name, field/tier, description, effects, status).
- **Research popup:** `gui/aov_window_artificery_research.gui`, drawn like a character event (`bp2_university`
  background, `type_inspiration` icon). The three faction title holders stand on the right ("Vacant" plate when
  empty); each option shows that faction's price. Steps use GUI variable `aov_research_stage` (unset →
  `mechanists` / `technomancers` → `tech_<field>` proposals).
- **Artificer factions:** global landless duchies `d_brillites`, `d_mechanists`, `d_technomancers`
  (`common/landed_titles/aov_artificer_faction_titles.txt`), held for life, not revocable (revoke-trigger override).
  When a holder dies (`common/on_action/aov_artificer_faction_on_actions.txt`) the title is destroyed and
  `aov_election_open` (`common/scripted_effects/aov_artificer_election_effects.txt`) picks three gnome candidates;
  every artificer nation votes, weighted by influence level (players via event `aov_artificer_factions.1`), and
  the count after 30 days grants the title to the winner, who stays their liege's vassal. A gnome holds at most
  one faction title; a faction title gained any other way (Grant Titles, inheritance) is destroyed and re-elected
  (`on_title_gain`, title variable `aov_elected_holder`). Vacant titles are filled at game start and yearly. **Influence** per ruler and faction (`aov_influence_<f>`, 0-100, start 40): sponsoring
  +20 / rivals -10, +1/quarter while their research runs, -1/quarter above 40, ±1-2/quarter from the leader's
  opinion, Make Amends (100 gold, +10, up to 40). Levels Hostile/Displeased/Neutral/Favored/Exalted give modifiers
  `aov_<f>_<level>` and set research cost (100/75/50/38/25) and time (+25%/+25%/-/-/-25%). Values in
  `common/script_values/aov_artificer_faction_values.txt`; Factions tab cards in `gui/aov_artificer_factions.gui`.
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
  Anbennar's `magic_duelist_focus` is overridden as Battle Mage, name via `localization/replace/`). Perks feed magic only
  through `common/script_values/aov_magic_lifestyle_values.txt` (the bonus layer: study rate, spell cost and duration,
  mana, dark-magic risk), so tune balance there. Spell cost and duration are per-caster values
  `aov_spell_<k>_cost` / `_years` generated into `common/script_values/aov_spell_values.txt`; casting also grants
  magic lifestyle XP. `magic_mastery` = school levels + magic perks. Art and the lifestyle window override come from
  `tools/build_magic_lifestyle_art.py` and `tools/build_lifestyle_override.py`. Spec
  `docs/superpowers/specs/2026-10-08-magic-lifestyle-design.md`.
- **Great projects (Cannor):** the EU4 Anbennar great projects in Cannor (81 monuments, 3 levels each) as CK3 special
  buildings: new `aov_monument_<eu4key>_01/_02/_03` chains, 17 Anbennar levels re-emitted with EU4 tiers
  (`zz_aov_monument_overrides_cannor.txt`), and Castle Dameris (`castle_dameris_01/_02/_03`, generated into
  `aov_monuments_cannor.txt`). Effects come from EU4 through the table `tools/data/monuments/translation.py`; the
  importer writes `tools/data/monuments/cannor.py` and merges hand fixes from `tools/data/monuments/cannor_hand.py`
  (`HAND`, re-applied on every run; `tiers` merge key by key), so edit the hand file, never `cannor.py`. Rebuild:
  `import_eu4_monuments.py --region cannor`, then `build_monuments.py` (every region), then
  `build_county_view_override.py` (paintings in the county view). Dropped modifiers and one-offs are listed per tier
  (`dropped`); 10 gates stay open (EU4 gates on tags/flags/legacies); balance caps on the EU4 tiers: fort_level 4, county tax_mult 0.3; a summed fort_level stops at max(8, Anbennar's value), the rest goes to `defender_holding_advantage`; upgrades cost and take at least what the level they replace did; hand field `gate_mode: "or"` (Necropolis) makes the EU4 gate an alternative to Anbennar's `can_construct` on upper levels.
  Spec `docs/superpowers/specs/2026-10-09-great-projects-cannor-design.md`.
- **Great projects (Middle Dwarovar):** region `dwarovar` (EU4 west/east Serpentspine superregions) of the same
  framework: 5 Dwarven Monuments holds on the CK3 map (Seghdihr, Verkal Gulan, Hehodovar, Gor Ozumbrog, Khugdihr),
  data `tools/data/monuments/dwarovar.py` + `dwarovar_hand.py`, outputs `aov_monuments_dwarovar.*` (no overrides: no
  Anbennar buildings there). The other 48 Serpentspine projects are `EXCLUDED` with a reason: holds not on the CK3
  map, EU4 dungeons (left for the Dwarven Hold Digging system), Insyaa mission monuments on a placeholder province,
  tunnel canals. Dwarven Monuments gates expand its `dwarven_monuments_has_acceptable_culture_or_race` trigger
  (`translation.SCRIPTED_GATES`) to Dwarven/Kobold; its dig-level requirement waits for hold digging.
- **Great projects (rest of the map):** regions `bulwar` (12 built), `salahad` (10: North Salahad with Akasik and
  Kheterata, South Salahad's Krahgradir) and `deepwoods` (6) of the same framework, each with `<region>.py` +
  `<region>_hand.py`; all new monuments, no Anbennar chains. EU4 puts the Dragon Coast in western Cannor, so its 6
  projects were built with Cannor. Excluded with a reason: projects whose EU4 province has no CK3 title (5 of the 9
  Black Demesne Eternal Pillars, Djinnakah, Esuvrem), dungeons (Hero's Gate, Jorkad Dam, the Skewered Drake), canals
  (the Fey Portal, the Great Merfolk Canal) and EU4 event variants (`VARIANTS`: Befouled Aur-Kes-Akasik). Hand
  fixes: icon categories, balance caps (Ash Palace domain limit, Ebbusubtu piety, Oasis of Water Dreams, Anzarzax
  supply, Pillars' tax), the Grand Library keeps one-barony Koroshesh and the Grain Port goes to Kaashesh (same
  duchy), a written Pillar of Eternity description. The importer cleans EU4 text (Sarhal descriptions' dash rule
  and literal `\n`, typographic quotes and dashes) and reads Windows-1252 lines in EU4 loc files.
- **Dwarven holds:** the 9 EU4 dwarven holds on the CK3 map are baronies of the new `dwarven_hold_holding` (Khugdihr
  starts ruined), with 10 levels `dwarven_hold_01..10`. Levels are raised only by digs; the level effects need a
  dwarven holder and an unruined hold; each level gives a castle's flat levy, garrison and income (at least the castle
  of its art band) on top of its multipliers. Castle buildings can be built in a hold: an override of Anbennar's
  holding-level requirement triggers (`common/scripted_triggers/zz_aov_building_requirement_triggers.txt`) treats hold
  levels 1/3/5/8 as castle levels 1-4. Three dwarven buildings (deep mine from level 3, runeforge 5, hall of the
  ancestors 7), off under the same conditions as the levels. Dig with the **Delve Deeper** decision
  (`aov_delve_deeper_decision` -> picker event `aov_hold_delve.1`): it pays `aov_dig_cost` = 150 x target level gold
  up front and sets the hold province variables `aov_dig_target_level` and `aov_dig_progress` plus the marker modifier
  `aov_delving_02..10`; the dig needs `aov_dig_months` = 12 x (8 + 4 x (N - 1)) months. The quarterly tick
  `aov_hold_dig_quarterly` (`common/on_action/aov_hold_on_actions.txt`, on `quarterly_playable_pulse`) adds 3 months,
  pauses while the hold is occupied, ruined or under a non-dwarf, and on completion adds exactly one level and fires
  `aov_hold_dig.100`. Yearly (`aov_hold_dig_yearly`, `common/on_action/aov_hold_dig_on_actions.txt`,
  `yearly_playable_pulse`) each digging hold of a dwarven player has a 40% chance of an EU4-style event by progress
  share (under 25% events 1-3, 25-75% 4-8, 75% and over 9-11; `events/aov_hold_dig_events.txt`), whose options move
  progress by up to 18 months, floor 0. The hold's county view shows a running dig as a progress bar ("Delving to
  Level N: X / Y months", years left in the tooltip). The AI keeps 2x the cost in reserve. A non-dwarf conquering a
  dwarf-held hold ruins it (`on_title_gain`, `common/on_action/aov_hold_on_actions.txt`;
  `events/aov_hold_ruin_events.txt`); the *Clear the Ruins* decision (`aov_clear_ruins_decision`, 300 gold, 200
  prestige, 5 years; the AI takes it with 600 gold) restores it; ruined holds show vanilla's ruined picture in the
  county view (`EXTRA_ART` of `tools/build_monuments.py`). Data in `tools/data/holds.py`, generated by
  `tools/build_holds.py`; hand-written logic in the `aov_hold_*` files (decisions, on_actions, effects, triggers,
  `aov_hold_formats.txt`). Spec `docs/superpowers/specs/2026-10-10-dwarven-hold-digging-design.md`.
- **Holding models:** RiE's castles, cities and temples for four culture groups (spec `docs/superpowers/specs/2026-10-15-holding-models-design.md`). CK3 picks a holding asset by the province's graphical region first (the most important criterion, `_buildings.info`), then the holder culture's `building_gfx` keys. So every new asset lists the culture key(s) AND `graphical_regions` = every region with `graphical = yes` in Anbennar's `map_data/geographical_regions/*.txt` (read at build time; 7 today), as vanilla's DLC culture assets do; a bare culture asset would lose to the region-matched western ones. The 28 target cultures get a new key prepended: `aov_high_elf_building_gfx` (moon and sun elvish: `highelves_0N` pairs), `aov_wood_elf_building_gfx` (wood elvish: Sindarin sanctuaries), `aov_dwarven_building_gfx` (heritage_dwarven: `dwarven_holding_01..04`, castles and cities only) and `aov_castanorian_building_gfx` (heritage_escanni: Dunedain castles, Gondor cities, Dunedain temple pairs). CK3 needs every `building_gfx` list starting with a key to continue identically, so a group gets one key per distinct existing list: the group's key for its most common list, `aov_<group>_<second key's stem>_building_gfx` for the others (`aov_dwarven_mena_building_gfx`, "Dwarven (Southern)", for copper, gold and marble dwarvish, whose list ends in `mena_building_gfx`); an asset lists all keys of its group. `illustration`/`soundeffect` come from the first original asset without `requires_dlc_flag` that serves the key's fallback (the second key of its list, `western_building_gfx` or `mena_building_gfx`). **Dwarven provinces:** the graphical region `graphical_aov_dwarven_mountains` was rejected by CK3 (`error.log`: 450 "province lies in multiple graphical regions") and is gone; province lists replace it (`provinces` outranks the graphical region, as in vanilla's Constantinople castle). In each `castle_01..04` and `city_01..04` one dwarf asset comes first, with all regions: `provinces` = provinces of terrain `DWARF_TERRAIN_TERRAINS` (`dwarven_hold`, `dwarven_hold_surface`, `cavern`, `dwarven_road`) minus `DWARF_PROVINCE_EXCLUDE` (263, Old Passage; 118 provinces; `dwarf_model_provinces`, shared with `tools/build_holds.py`) and NO `graphical_cultures`, so any holder (kobold, human) shows the dwarf model there. There is no mountain asset (round 2: `provinces` outranks `graphical_cultures`, so it showed the dwarf model to every holder in ordinary mountains): dwarves outside dwarven terrain keep vanilla's models, because a province asset cannot be limited to a culture. No dwarf temples. **Temples:** CK3 scores assets (graphical faith +1, culture +2, region +4; ties go to the first asset), and Venail's faith has `graphical_faith = orthodox_gfx`, so vanilla's temple asset (faith + western + region = 7) beat ours (6). Every new temple asset therefore also lists `graphical_faiths` = every distinct `graphical_faith` of Anbennar's `common/religion/religion_types/*.txt` (read at build time: `catholic_gfx dharmic_gfx islamic_gfx orthodox_gfx pagan_gfx sinitic_gfx`), scoring 7 and winning on order; a non-target culture scores 5 with it and keeps vanilla's 7. **Walls:** vanilla walls around holdings are background buildings (`walls_00`, `walls_01_tribal`, `walls_01..04`, `is_graphical_background`), not part of the holding model; `aov_elven_walls` draws RiE's `highelves_fort_wall_mesh` (high elf keys) and `sindarin_hedge_wall_01_mesh` (wood elf keys) for elf-culture holders on a county capital or with `fort_level > 0` (not in dwarf-model provinces), and `walls_01_tribal`, `walls_01..04` stand down for them. All six re-emitted vanilla buildings (`zz_aov_holding_walls.txt`, `walls_00` included) also stand down in provinces that show the dwarf model (the fence and field around dwarf models), by the inserted first line `NOT = { aov_dwarven_model_province_trigger = yes }`; the trigger is generated into `common/scripted_triggers/aov_holding_model_triggers.txt` (province scope: `OR` of `terrain = <dwarven terrain>` minus `this = province:263`; `terrain = <key>` is a province trigger, as in vanilla's `00_artifact_triggers.txt` under `title_province`). Castanorian walls are unchanged. **Tribes:** wood elf holdings start tribal, so `tribe_01/02` (from the game's `00_tribal_buildings.txt`) get `sindarin_sanctuary_01/02_mesh` for the wood elf key; high elves get no tribal model. The dwarven hold levels (`tools/build_holds.py`) use `HOLD_DWARF_MESHES` (`dwarven_holding_01..05`, two levels per model) with all regions, the same dwarven-terrain `provinces` list (so a human-held hold such as Marrhold beats the copied western castle asset) and no `graphical_cultures`. **Risks, to confirm in game:** (1) whether `provinces` plus all `graphical_regions` in one asset picks the dwarf model over the regional western one (vanilla's Constantinople asset has the same shape). (2) RiE's assets reference `gravel_normal.dds` and `gravel_properties.dds`, which only vanilla ships (looked up by name, not copied); the wall decal textures shared by two groups are copied once. (3) The elven wall's `scope:holder ?= { culture = { ... has_building_gfx = ... } }` trigger shape is untested in a background building. Tiger reports 75 inherited items in `zz_aov_holding_models.txt` (undefined `building_emishi_temple_0N_entity`, `zoroastrian_gfx`/`shinto_gfx`/`tengrism_gfx`/`kamuyism_gfx`, mandala effect scopes): they come verbatim from vanilla's and Anbennar's own asset blocks, which tiger does not report while they sit in the base mod (baselined in `tools/tiger_baseline.json`, see Validation). Rerun the generator after a Realms in Exile update too.
- **Map graphics:** Realms in Exile's map look over Anbennar's map, generated by `tools/build_map_graphics.py` from
  `tools/data/map_graphics.py` (spec `docs/superpowers/specs/2026-10-13-map-graphics-design.md`). Terrain: 32 Anbennar
  mountain, hill and cliff materials (`TEXTURE_MAP`) get RiE's diffuse, normal and material textures in
  `materials.settings` (order and masks untouched), plus 4 drop-in files (`DROP_INS`). Shaders: 16 RiE files under
  `gfx/FX/` (12 roots plus `gh_snowfall`, `gh_utils`, `gh_vic3_fog_of_war`, `gh_vic3_fog_of_war_settings`); Anbennar
  keeps `bordercolor.fxh`, `gh_camera_utils.fxh` and `dynamic_masks.fxh`. Also RiE's environment, water, fog of war
  and the skybox (centred at (4096, 2048), RiE's z-scale 7000 kept); `aov_map_graphics_defines.txt` ports RiE's lowered
  `ZOOM_STEPS_MIN_TILT`, so at close zoom the camera can tilt nearly flat and show the skybox, as in RiE; the snow `Texture_Index` is rewritten to 56
  (Anbennar's `snow` material). Colour grading (`GRADING`, one box per de jure duchy of each graded kingdom from its
  baronies' building locators, margin 60, fade min(300, 25% of the box's short side); `GRADING_SKIP_PROVINCES` leaves
  out stray locators such as b_obadel's): 125 boxes, 20 boreal (Gerudia), 45 desert (Salahad, Kheterata), 60 arid
  (Bulwar, Harpylen); RiE's Middle-earth boxes are dropped, `k_the_reach` (no duchies) is reported as a note, and
  every pair of different-grade boxes overlapping by more than 25% is printed as a note (three pairs still exceed
  50%, see the spec). Tune the textures and
  grades in game. **Raised dwarven mountains and gates:** the 119 dwarven provinces (terrain `dwarven_hold_surface`,
  `dwarven_hold`, `cavern`, `dwarven_road`) form 9 ranges. Each range's highest point is lifted toward `LIFT_PEAK`
  50,000 from its ground (median of non-dwarven, non-water pixels within 24 px), factor capped at 1.8, never lowered;
  values above 60,000 ease toward 65,535 (soft ceiling) and changes fade out over 12 px. Rubyhold 40,982 -> 50,000
  (x1.37), Ovdal Tungr (526/2855/2856), Esmaria (263), the Harpylen cavern (655) and province 912 x1.8, the Serpentspine, Dragon Coast and Khugdihr ranges x1. Gate sites where dwarven terrain meets normal land: 12, of which `GATE_EXCLUDE_COUNTIES` (`c_oldpassage`, user choice; a listed county with no site stops the build) leaves 9
  (Dragon Coast and Harpylen excluded; sites closer than 16 merge, none today; Rubyhold's are Redgate -> Rewanfork and
  Rose Mines -> Rivergate) each get RiE's `erebor_gate_mesh` at scale `GATE_SCALE` 1.6, moved `GATE_INSET` 2 units along `inward` so it sits in the slope (local +Z points along `inward`, into the mountain, as in RiE's Erebor gate, so its front faces the normal land). `GATE_OVERRIDES` (`(dwarven county, normal county)` -> `scale`/`yaw`/`inset`/`dx`/`dy`, empty) tunes single gates and a key matching no gate stops the build; `SEA_GATES` (`c_ovdal_tungr`) replaces a hold county's land sites with one gate on the nearest shore pixel of its hold barony's province (`b_irovar`), facing the sea (`normal_county` `sea`). The gate mesh needs the `court_scene.shader` placeholders (`temp_layer`; `GATE_YAW_OFFSET` 0 is to be tuned in game).
  **Erebor transplant** (`tools/gate_transplant.py`, spec addendum item 5): RiE's Erebor gate stands in a small composition, extracted from RiE at build time (`extract_composition`; RiE's heightmap decode adds ~15 s, cached by `load_composition`) and stamped at every gate with scale `k = gate scale / EREBOR_GATE_SCALE` (0.703864): a steep **terrain cone** (RiE's height delta within `TRANSPLANT_RADIUS` 18 px; the pixel blends up from its own height by a cone weight = smoothstep(delta, 0.15..0.40 of the peak) x face weight (0 in front of the face, t < 0) x radius fade x water fade (6 px), so nothing in front of the gate, outside the cone or on water changes and rivers get no canyon walls; never lowered) and the **mountain pieces** (a piece stays only if its centre has t >= 0 and cone weight >= 0.3; of Erebor's 10, mountain_01/02/03/03/06 survive) in `gfx/map/map_object_data/aov_dwarven_gate_overlays.txt` (assets `aov_<piece>.asset` with their meshes and textures beside them). RiE's 3 flank objects are `waterfall` effect entities, not rocks, and are not used; Ravenhill and Rammas Echor are excluded. Per-site variation (all `TRANSPLANT_*` in `tools/data/map_graphics.py`; seed = SHA-256 of the site key; `TRANSPLANT_OVERRIDES` pins `mirror`/`turn`/`height`): mirror 50%, turn up to 25 degrees toward the uphill gradient, height factor 0.85-1.25 so the cone clears nearby high terrain, piece jitter (0.6 units, 15 degrees, x0.9-1.1), pieces on water or id 0 dropped. **Polish** (spec addendum item 6, after the cones): each gate in key order (reading what the last left) (a) **joins the range to its cone peak** (`_join_range`: dwarven or impassable land at t >= 0 within `RANGE_JOIN_RADIUS` 60 px, outside its cone core (weight < `RANGE_JOIN_CORE` 0.4), is scaled up from the gate's foot, `new = max(cur, soft_ceiling(g + (cur - g) * (1 + (s - 1) * w)))`, w = 1 within `RANGE_JOIN_FULL` 30 px then a cosine to 0, times the water fade; s is the smallest scale in [1, `RANGE_JOIN_MAX` 2] with which the highest scaled pixel reaches the cone's peak, so ridges keep their shape and are never lowered or flattened); (b) **levels the gate's footprint and front apron** to the foot (`_level_footprint`: gate frame, t from -`GATE_APRON` x size/1.6 to `GATE_MODEL_DEPTH` x size, |l| <= `GATE_MODEL_HALF_WIDTH` x size + 1, cosine blend over `GATE_APRON_FADE` 3 px, land only, never lowered); (c) **keeps pieces off the gate**: each piece's footprint (its mesh's `min`/`max` bounding box from the pdxmesh, `gt.mesh_bounds`, times the asset scale 1.5, `bmg.piece_bounds`) is tested against the gate's keep-out (`gt.keep_out`: only the zone in front of and at the face, t from the apron to `PIECE_FACE_CLEARANCE` 1 px behind it, |l| <= half width + 2 px; the body behind the face may be overlapped; the footprint is an oriented box); an overlapping piece is pushed back along the cone axis in 0.5 px steps by at most `PIECE_MAX_PUSH` 12 px, filtered again at the new position, else dropped. A note per gate reports mirrored, turn, factor, cone peak, range join (m before -> after, s), apron pixels raised and pieces kept/dropped/pushed (named). The generator repacks Anbennar's
  packed heightmap (32x32 blocks, tile 32/step+1, bottom-up): the 48 changed blocks are re-packed at level 0, the rest
  keep Anbennar's tiles; the packed image is 4059 rows (Anbennar's 4047) because each level band starts a new row.
  **Risk:** the game may reject our packed layout (its packer may differ); check the map loads in game before tuning,
  fallback is rebuilding the packed files with CK3's map editor. `credits.txt` credits RiE, Godherja (the `gh_` shaders, adapted by RiE) and Victoria 3 (fog of war
  is based on its shader) and RiE's Erebor gate model. Terrain gaps: Anbennar's blend maps leave some pixels with no material (drawn black: a ~395,000 px block in
  impassable province 2426 and ~2,100 small blocks over land, e.g. around Ovdal Tungr); `tools/terrain_fill.py` fills
  gaps under `TERRAIN_FILL_LARGE` (1000 px) from a painted neighbour and larger ones with `TERRAIN_FILL_MATERIAL`
  (`mountain_02`) at full weight; painted pixels never change. **Ask the RiE and Godherja teams for permission before the next Workshop upload.** The build stops if a copied asset's shader lacks its `_mapobject` effect in `court_scene.shader`. Spec addendum item 5.
