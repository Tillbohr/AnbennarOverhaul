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

## Model choice

The default model is **Sonnet 5.5 on medium effort**, for speed and lower token use. Routine work stays on it:
rerunning generators, data edits, loc, small script fixes, tests, validation, commits, docs.

When a task needs deeper thought, **stop before the hard part and ask the user to switch to the most capable
model in the model menu, on high effort**. Say in one line why, then wait. A session cannot change its own model;
the user switches it from the model menu. Deeper thought means any of:

- designing a new system or a new generator, or changing how an existing generator works;
- debugging engine behavior the files do not explain (asset scoring, scopes, GUI layout, why a trigger fails in game);
- a change across several systems or generators, or one that touches generator order (`docs/systems/updating.md`);
- a fix that already failed once on this model.

After the hard part is done, say so, so the user can switch back to Sonnet 5.5 medium for the rest.

| Task | Command |
|---|---|
| Validate (new reports only) | `python -I tools/validate.py` |
| Validate (everything) | `python -I tools/validate.py --all` |
| Accept current reports as baseline | `python -I tools/validate.py --baseline` (only after confirming they are inherited from Anbennar or from a file copied verbatim from Realms in Exile; record them in `docs/systems/validation-baseline.md`) |
| Run the tests for what you changed | `python -I -m unittest discover -s tools/tests -p "test_<name>*.py"` (fast; prefer this) |
| Run all tool tests | `python -I -m unittest discover -s tools/tests` (no `-v`: it prints a line per test, ~900 lines) |
| Rebuild anything | see the system's doc below; every command and its prerequisites are in `docs/systems/updating.md` |

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

## EU4 imports

Nothing is rebuilt from EU4 Anbennar: EU4 art and data are imported once, committed, then edited here.
`tools/eu4_import.py` holds the import helpers (EU4 paths, loc, map regions and province names, DDS/TGA
readers, DX10 header fix, Lanczos 2x upscale, mip chains). Convert one EU4 picture with
`python -I tools/eu4_import.py convert <eu4 path> <mod path> [--upscale2x] [--resize WxH] [--mips]`.

## Generated files

Files written by a `tools/build_*.py` script are never edited by hand: change the script's data in `tools/data/`
and rerun it. Each system's doc lists its generated files, generator and why. `FreshnessTests` in `tools/tests/`
fail when generated files are stale.

## Systems

Read only the doc for the system you are working on. Each holds the generated-file rows and the full system notes.

| System | Doc | Generators |
|---|---|---|
| Gnomish artificery: tradition, academy, handgunners, Artificery tab, 60 inventions, research popup, artificer factions and influence | `docs/systems/artificery.md` | `build_inventions.py`, `build_hud_override.py` |
| Magic schools (mana, knowledge, 48 spells, Magic tab with Advancements and Spells tabs), 8 magic advancements (one per school) and the magic lifestyle (3 trees, focuses, traits) | `docs/systems/magic.md` | `build_spells.py`, `build_advancements.py`, `build_lifestyle_override.py` |
| Great projects: EU4 monuments in Cannor, Middle Dwarovar, Bulwar, Salahad, Deepwoods; county view paintings | `docs/systems/great-projects.md` | `build_monuments.py`, `build_county_view_override.py` |
| Dwarven holds: `dwarven_hold_holding`, 10 levels, Delve Deeper digs, ruin and clear | `docs/systems/dwarven-holds.md` | `build_holds.py`, `build_holdings_override.py`, `build_governments_override.py` |
| RiE dwarf buildings, ore deposits, mines and the Dwarven Expedition activity | `docs/systems/rie-dwarves.md` | `build_rie_dwarves.py` (run before `build_holds.py` and `build_holdings_override.py`) |
| RiE holding models, walls and army models (elves, dwarves, Castanorians) | `docs/systems/holding-models.md` | `build_holding_models.py` |
| RiE portraits (halfling hair, elves, dwarves) | `docs/systems/rie-portraits.md` | `build_portraits.py` |
| RiE character backgrounds and royal courts | `docs/systems/rie-courts.md` | `build_rie_courts.py` |
| Deepwoods grove arms and EU4 names | `docs/systems/deepwoods-groves.md` | none (imported once; edit by hand) |
| Map graphics: RiE shaders and terrain, raised dwarven mountains, dwarven gates | `docs/systems/map-graphics.md` | `build_map_graphics.py` |
| Racial armies: levies, domain limit, elf and dwarf MAA (moon, sun, wood elves; dwarf clans) with RiE icons and art, per-holding levy correction | `docs/systems/racial-armies.md` | `build_racial_levies.py` |
| Faith men-at-arms: Dercinges, Druids, Skalds and Knights of the Spear recruited by faith tenet or patron god instead of a culture tradition | `docs/systems/faith-maa.md` | none (hand-written overrides) |
| Holy sites for Devouring Path and Silk Turban (Anbennar ships them with none) | `docs/systems/holy-sites.md` | `build_holy_sites.py` |
| Race knight badges: EU4 tech group icons (gear removed) as the knight badge for elf, dwarf, gnome and kobold rulers; RiE levy and knight pictures in the military window for elf and dwarf rulers | `docs/systems/knight-icons.md` | `build_knight_icons.py` |

## Updating and validation

- After an Anbennar update, a CK3 patch or a Realms in Exile update, follow `docs/systems/updating.md`
  (generator order, hand re-copies of overridden triggers and interactions, which generators to rerun).
- `tools/tiger_baseline.json` holds the accepted tiger reports; `docs/systems/validation-baseline.md` explains
  each group. Read it before re-baselining.
