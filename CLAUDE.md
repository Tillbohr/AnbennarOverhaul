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
| Accept current reports as baseline | `python -I tools/validate.py --baseline` (only after confirming they are inherited from Anbennar) |
| Rebuild holdings override | `python -I tools/build_holdings_override.py` |
| Rebuild HUD override | `python -I tools/build_hud_override.py` |
| Rebuild lifestyle window override | `python -I tools/build_lifestyle_override.py` |
| Rebuild county view override | `python -I tools/build_county_view_override.py` |
| Import EU4 monuments | `python -I tools/import_eu4_monuments.py --region <name>` (`cannor`, `dwarovar`, `bulwar`, `salahad`, `deepwoods`; needs the EU4 Anbennar, Cannorian and Dwarven Monuments mods installed; rewrites `tools/data/monuments/<region>.py`) |
| Rebuild monuments | `python -I tools/build_monuments.py` (every region; `--region <name>` for one, the shared illustration file is always rebuilt from all) |
| Run tool tests | `python -I -m unittest discover -s tools/tests -v` |
| Rebuild inventions | `python -I tools/build_inventions.py` (needs EU4 Anbennar installed for icons) |
| Rebuild spells | `python -I tools/build_spells.py` (needs EU4 Anbennar installed for magic art) |
| Rebuild magic lifestyle art | `python -I tools/build_magic_lifestyle_art.py` (needs EU4 Anbennar and CK3 installed) |

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
| `common/holdings/00_holdings.txt` | `python -I tools/build_holdings_override.py` | Holdings are whole-file only. The script copies Anbennar's file and inserts the `ADDITIONS` (marked `# Anbennar Overhaul`). Never edit the output by hand. |
| `gui/hud.gui` | `python -I tools/build_hud_override.py` | The main tab bar is whole-file only. The script copies Anbennar's `gui/hud.gui` if it has one, else the game's, and inserts the Artificery tab after `tab_situation` (marked `# Anbennar Overhaul`). Never edit the output by hand. |
| `gui/window_character_lifestyle.gui` | `python -I tools/build_lifestyle_override.py` | The lifestyle window is whole-file only. The script copies Anbennar's `gui/window_character_lifestyle.gui` if it has one, else the game's, and adds a `magic_lifestyle` copy after each of the three `wanderer_lifestyle` blocks (XP bar background, progress bar, unspent-points icon) using the magic art (marked `# Anbennar Overhaul: magic lifestyle`). Never edit the output by hand. |
| `gui/window_county_view.gui` | `python -I tools/build_county_view_override.py` | The county view is whole-file only. The script copies Anbennar's `gui/window_county_view.gui` if it has one, else the game's, and inserts one `background` per EU4 monument painting (`build_monuments.painting_backgrounds`) inline right after the vanilla holding-illustration `background`, covering the holding panel down to the garrison box (`margin_bottom = 63`, above the building slot row) top-aligned (`fittype = start`, so the top is never trimmed; marked `# Anbennar Overhaul: monument painting`); the vanilla holding illustration's `visible` also requires an empty `AovMonumentIllustration`. Never use a `using` template for these: template backgrounds draw beneath every inline background (the panel's dark background covered them). Rerun after `build_monuments.py` when monuments change. Never edit the output by hand. |
| `gfx/interface/illustrations/aov_monuments/*.dds`, `common/customizable_localization/aov_monument_illustration.txt`, `localization/english/aov_monument_illustration_l_english.yml`, `gfx/interface/window_county/aov_monument_painting_mask.dds` | `python -I tools/build_monuments.py` | EU4 monument paintings (uncompressed BGRA, 572x272: EU4's 300x150 with its baked-in dark name plate lifted (`lift_title_strip`), its 6 px frame and the bleed row next to it cropped (`crop_frame`) and a Lanczos-3 2x upscale (`upscale_2x`)), drawn at full alpha through a lighter generated mask (95% in the middle, short soft edges, drawn top-aligned (`fittype = start`, spires reach the frame); vanilla's holding mask peaks at ~67%); custom loc `AovMonumentIllustration` (province scope; the text of loc key `aov_monument_art_<eu4key>` for the province's monument, else empty; keys defined once in the shared loc file). The county view override draws each painting as a `background` with a fixed texture path, visible when `EqualTo_string(Custom('AovMonumentIllustration'), Localize('aov_monument_art_<eu4key>'))`. CK3 does not load a texture whose path comes from custom loc, so never bind `texture` to it. |
| `common/modifiers/aov_invention_modifiers.txt`, `common/scripted_triggers/aov_invention_triggers.txt`, `common/script_values/aov_invention_values.txt`, `common/scripted_effects/aov_invention_effects.txt`, `common/scripted_guis/aov_invention_sgui.txt`, `common/customizable_localization/aov_invention_custom_loc.txt`, `gui/aov_inventions_generated.gui`, `localization/english/aov_inventions_l_english.yml`, `gfx/interface/icons/aov_inventions/` | `python -I tools/build_inventions.py` | One block per invention, generated from `tools/data/inventions.py` (edit the data, then rerun). |
| `common/modifiers/aov_spell_modifiers.txt`, `common/scripted_triggers/aov_spell_triggers.txt`, `common/scripted_effects/aov_spell_effects.txt`, `common/scripted_guis/aov_spell_sgui.txt`, `common/character_interactions/aov_spell_interactions.txt`, `gui/aov_magic_generated.gui`, `localization/english/aov_spells_l_english.yml`, `gfx/interface/icons/aov_magic/`, `gfx/interface/skinned/hud_maintab/aov_maintab_magic.dds` | `python -I tools/build_spells.py` | One block per spell, generated from `tools/data/spells.py` (edit the data, then rerun). |
| `gfx/interface/icons/{lifestyles,focuses,traits,lifestyles_perks,lifestyle_tree_backgrounds}/` magic files, `gfx/interface/illustrations/lifestyles_background/magic_lifestyle.dds`, `gfx/interface/progressbars/aov_progress_magic*.dds` | `python -I tools/build_magic_lifestyle_art.py` | Magic lifestyle art (18 DDS files) composed from EU4 Anbennar magic art and uncompressed vanilla files; the output list is `OUTPUTS` in the script. |
| `common/buildings/zz_aov_monument_overrides_cannor.txt` (with `common/buildings/aov_monuments_cannor.txt`, `history/provinces/aov_monuments_cannor.txt`, `localization/english/aov_monuments_cannor_l_english.yml`) | `python -I tools/build_monuments.py` | Cannor great-project buildings from `tools/data/monuments/cannor.py`. The `zz_` file re-emits the 17 Anbennar monument levels (copied from Anbennar's current definitions) with the EU4 tier modifiers, `on_complete` and `next_building` inserted, marked `# Anbennar Overhaul: EU4 tier <n>`; Anbennar's own triggers are untouched. The new upper levels of those chains (in `aov_monuments_cannor.txt`) are copies of the chain's top Anbennar level with the EU4 tier merged the same way (EU4 culture gate in `can_construct` only), because a CK3 upgrade replaces the previous level's effects. The script validates the data first and stops on a placement, name, icon, modifier-key or empty-level problem. |
| `common/buildings/aov_monuments_dwarovar.txt`, `history/provinces/aov_monuments_dwarovar.txt`, `localization/english/aov_monuments_dwarovar_l_english.yml` | `python -I tools/build_monuments.py` | Middle Dwarovar great-project buildings from `tools/data/monuments/dwarovar.py` (no Anbennar levels, so no overrides file). |
| `common/buildings/aov_monuments_<region>.txt`, `history/provinces/aov_monuments_<region>.txt`, `localization/english/aov_monuments_<region>_l_english.yml` for `bulwar`, `salahad`, `deepwoods` | `python -I tools/build_monuments.py` | Great-project buildings of the rest of the map from `tools/data/monuments/<region>.py` (no Anbennar levels, so no overrides files). |

## Updating to a new Anbennar version

1. Replace `../anbennar-ck3-dev-master` with the new Anbennar release.
2. Run `python -I tools/build_holdings_override.py` and `python -I tools/build_hud_override.py` and `python -I tools/build_lifestyle_override.py` and `python -I tools/build_county_view_override.py`, and `python -I tools/build_monuments.py` (the monument overrides copy Anbennar's current definitions; it errors naming any monument key Anbennar no longer defines).
3. Run tiger and the tool tests (below) and fix anything that references renamed Anbennar content. The tests fail if
   Anbennar renames `anb_enhance_ability_interaction` or adds another way to start its Enhance Ability scheme (removed
   from the game; see `EnhanceAbilityRemovedTests`).
4. Re-copy Anbennar's `title_revocation_standard_can_pick_title_trigger` (`common/scripted_triggers/00_interaction_triggers.txt`)
   into `common/scripted_triggers/zz_aov_interaction_triggers.txt`, keeping the `# Anbennar Overhaul` faction-title exclusion.
5. Re-copy Anbennar's `start_compel_interaction` and `start_dominate_interaction` into
   `common/character_interactions/zz_aov_spell_overrides.txt`, keeping the `# Anbennar Overhaul` lines. Its
   `anb_enhance_ability_interaction` is a never-shown stub and needs no re-copy.
6. Test in game; check `database_conflicts.log` for overhaul keys now also defined by Anbennar (notably `magic_duelist_focus`, which `zz_aov_magic_focuses.txt` must keep overriding).

After a CK3 patch, rerun `python -I tools/build_hud_override.py`, `python -I tools/build_lifestyle_override.py` and `python -I tools/build_county_view_override.py` too: their sources are the game's `hud.gui`, `window_character_lifestyle.gui` and `window_county_view.gui` (when Anbennar ships no copy).

## Validation

`python -I tools/validate.py` runs ck3-tiger with `--suppress tools/tiger_baseline.json`, so it prints only
reports that are not in the baseline (it ends `fatal: 0, error: 0, ...` when clean). `ck3-tiger.conf` loads the
base mod via its in-folder `descriptor.mod`; pointing it at the launcher's `../descriptor.mod` makes tiger load
the whole `mod/` folder instead. Current baseline: 4 `temple_citadel_holding` modifier-format warnings,
inherited from Anbennar's holdings file, and 1 `other_rulers` missing-item error in the generated `gui/hud.gui`
(vanilla HUD code referring to a dynastic-cycle group that Anbennar's `tgp_dynastic_cycle.txt` drops).

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
