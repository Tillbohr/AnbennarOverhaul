# Great projects (EU4 monuments)

The county view override also draws the dwarven hold dig bar (see dwarven-holds.md).

## Generated files

| File | Generator | Why |
|---|---|---|
| `gui/window_county_view.gui` | `python -I tools/build_county_view_override.py` | The county view is whole-file only. The script copies Anbennar's `gui/window_county_view.gui` if it has one, else the game's, and inserts one `background` per EU4 monument painting (`build_monuments.painting_backgrounds`) inline right after the vanilla holding-illustration `background`, covering the holding panel down to the garrison box (`margin_bottom = 63`, above the building slot row) top-aligned (`fittype = start`, so the top is never trimmed; marked `# Anbennar Overhaul: monument painting`); the vanilla holding illustration's `visible` also requires an empty `AovMonumentIllustration`. Never use a `using` template for these: template backgrounds draw beneath every inline background (the panel's dark background covered them). It also adds a dwarven hold's dig progress bar (`DIG_BLOCK`, marked `# Anbennar Overhaul: hold dig progress`) after vanilla's holding-construction bar, shown while the province has `aov_dig_target_level`; it reads `aov_dig_percent` and `aov_dig_years_left` (`common/script_values/aov_hold_view_values.txt`), text in `aov_hold_view_l_english.yml`. Rerun after `build_monuments.py` when monuments change. Never edit the output by hand. |
| `gfx/interface/illustrations/aov_monuments/*.dds`, `common/customizable_localization/aov_monument_illustration.txt`, `localization/english/aov_monument_illustration_l_english.yml`, `gfx/interface/window_county/aov_monument_painting_mask.dds` | `python -I tools/build_monuments.py` | EU4 monument paintings (uncompressed BGRA, 572x272: EU4's 300x150 with its baked-in dark name plate lifted (`lift_title_strip`), its 6 px frame and the bleed row next to it cropped (`crop_frame`) and a Lanczos-3 2x upscale (`upscale_2x`)), drawn at full alpha through a lighter generated mask (95% in the middle, short soft edges, drawn top-aligned (`fittype = start`, spires reach the frame); vanilla's holding mask peaks at ~67%); custom loc `AovMonumentIllustration` (province scope; the text of loc key `aov_monument_art_<eu4key>` for the province's monument, else empty; keys defined once in the shared loc file). `EXTRA_ART` (data `tools/data/holding_art.py`, `HOLDING_ART`: key, province trigger, texture, style) adds non-monument pictures after the monument entries, first match wins and a monument painting takes priority: ruined holds (`aov_hold_is_ruined`) show vanilla's ruined-holding picture (style `painting`), then a built holding (`has_holding = yes`) on a dwarven terrain (`TERRAIN_ART`: `dwarven_hold`, `dwarven_hold_surface`, `cavern`, `dwarven_road`) shows Anbennar's EU4 terrain picture `gfx/interface/illustrations/terrain_types/<terrain>.dds`, the one an empty holding there shows (style `illustration`: drawn with the vanilla holding illustration's alpha, centercrop and mask). New groups (e.g. wood elves) are one more entry; the build stops on a duplicate key, unknown style, empty trigger or a texture missing from the mod, Anbennar and the game. The county view override draws each painting as a `background` with a fixed texture path, visible when `EqualTo_string(Custom('AovMonumentIllustration'), Localize('aov_monument_art_<eu4key>'))`. CK3 does not load a texture whose path comes from custom loc, so never bind `texture` to it. |
| `common/buildings/zz_aov_monument_overrides_cannor.txt` (with `common/buildings/aov_monuments_cannor.txt`, `history/provinces/aov_monuments_cannor.txt`, `localization/english/aov_monuments_cannor_l_english.yml`) | `python -I tools/build_monuments.py` | Cannor great-project buildings from `tools/data/monuments/cannor.py`. The `zz_` file re-emits the 17 Anbennar monument levels (copied from Anbennar's current definitions) with the EU4 tier modifiers, `on_complete` and `next_building` inserted, marked `# Anbennar Overhaul: EU4 tier <n>`; Anbennar's own triggers are untouched. The new upper levels of those chains (in `aov_monuments_cannor.txt`) are copies of the chain's top Anbennar level with the EU4 tier merged the same way (EU4 culture gate in `can_construct` only), because a CK3 upgrade replaces the previous level's effects. The script validates the data first and stops on a placement, name, icon, modifier-key or empty-level problem. |
| `common/buildings/aov_monuments_dwarovar.txt`, `history/provinces/aov_monuments_dwarovar.txt`, `localization/english/aov_monuments_dwarovar_l_english.yml` | `python -I tools/build_monuments.py` | Middle Dwarovar great-project buildings from `tools/data/monuments/dwarovar.py` (no Anbennar levels, so no overrides file). |
| `common/buildings/aov_monuments_<region>.txt`, `history/provinces/aov_monuments_<region>.txt`, `localization/english/aov_monuments_<region>_l_english.yml` for `bulwar`, `salahad`, `deepwoods` | `python -I tools/build_monuments.py` | Great-project buildings of the rest of the map from `tools/data/monuments/<region>.py` (no Anbennar levels, so no overrides files). |

## System

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
