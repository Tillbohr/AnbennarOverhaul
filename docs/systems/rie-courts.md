# RiE backgrounds and courts

## Generated files

| File | Generator | Why |
|---|---|---|
| `gfx/interface/illustrations/scripted_illustrations/ingame.txt` (also the Lich backgrounds), `gfx/court_scene/scene_cultures/00_default_cultures.txt` (whole-file overrides of Anbennar's), `gfx/court_scene/scene_settings/grandeur_levels/grandeur_levels.txt` (override of the game's), `common/scripted_triggers/aov_rie_court_triggers.txt`, `gfx/portraits/environments/aov_rie_environments.txt`, `gfx/court_scene/scene_settings/scene_settings_{Dwarven_1_g3,rie_elf_1,ek_yespest_*}.txt`, `gfx/court_scene/scene_environment/court_scene_environment_rie_elf.txt`, `gfx/interface/illustrations/{character_view,event_scenes}/` (RiE pictures), `gfx/models/court/**`, `gfx/models/artifacts/thrones/` | `python -I tools/build_rie_courts.py` | RiE's character-window backgrounds and royal courts for dwarves (in dwarven hold, road or cavern terrain), wood elves and moon elves from `tools/data/rie_courts.py` (see Systems, RiE backgrounds and courts). The illustration override is Anbennar's file plus our entries between `# Anbennar Overhaul: Realms in Exile backgrounds` and its end marker; the culture-set override is Anbennar's file with our sets first and a marked `NOT = { aov_rie_court_scene_trigger = yes }` line in every other set; the grandeur override is the game's file plus RiE's three entries between markers. 95 files (~241 MiB; the pictures and `.dds`/`.mesh` via Git LFS). Never edit the output by hand; rerun after an Anbennar, RiE or CK3 update. `tools/tests/test_build_rie_courts.py` (`FreshnessTests`) fails when the files are stale or orphaned. |

## System

- **RiE backgrounds and courts:** the character window's background (by realm level) and the royal court come from
  RiE for dwarves whose capital is on `dwarven_hold`, `dwarven_hold_surface`, `dwarven_road` or `cavern` terrain (dwarf
  thronerooms highest/high/mid/low for empire/kingdom/duchy/county-and-below; RiE's `dwarven` Durin's Folk court), wood
  elves (Thranduil's halls for kingdom and above, RiE's Forest Avari forest hall with mountain windows below, user
  choice; RiE's `moriquendi` Lasgalen tree-hall
  court) and moon elves (RiE's Noldor thronerooms high/mid/low, which RiE gives the Falathrim of Lindon; RiE's `noldor`
  Lindon court, 2 layouts x 3 grandeur levels). User choices; spec `docs/superpowers/specs/2026-10-16-rie-courts-design.md`,
  generator `tools/build_rie_courts.py`, data `tools/data/rie_courts.py`. Groups are found by the portrait clothing keys
  (`aov_dwarf_`, `aov_lasgalendrim_`, `aov_noldor_clothing_gfx`). Backgrounds: `character_view_bg` returns its first
  valid entry, so ours go right before Anbennar's first throneroom (`fp1_throneroom_nontribal`), below death, prison,
  activity, travel and camp entries; each tests `aov_rie_court_view_<group>_<tier>_trigger` (the character, else a
  non-ruling spouse, the betrothed or the host, RiE's and vanilla's pattern). Courts: culture sets are made exclusive
  (vanilla's style) since their test order is not documented: ours first, every Anbennar set excludes them. Copied: RiE
  pictures, 7 portrait environments (Noldor, dwarf), 8 scene files verbatim, the elf court environment, 48 court model
  entities (block by block via `build_portraits.build_models`; vanilla props and `roco_*` effects stay vanilla's).
  **Liches** (`LICH_BACKGROUNDS`, user choice) come first, before the race courts: an unlanded Lich (`has_trait = lich`,
  `is_landed = no`: courtiers, guests, adventurers) stands in RiE's Nazgul crypt (`event_scenes/lotr_throneroom_evil.dds`,
  RiE's `environment_evil_throneroom`), shown for the Lich only; a landed Lich holds court in Godherja's lichdom hall
  (`gfx/interface/illustrations/aov_lich/lichdom_court.dds`, imported once and saved uncompressed since it is 1539x849,
  not generated; vanilla's `environment_cw_india_main`, as Godherja pairs it), also shown for a non-ruling spouse, the
  betrothed and the host like the courts. Triggers `aov_lich_court_[view_]{landed,unlanded}_trigger` in the generated
  trigger file. Death, prison, activity and travel backgrounds still win. Royal court scenes are unchanged.
  **To confirm in game:** the court choice, the Noldor grandeur levels, and RiE's odd-sized DDS pictures loading.
