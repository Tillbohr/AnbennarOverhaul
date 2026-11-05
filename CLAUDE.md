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
| Run the tests for what you changed | `python -I tools/run_tests.py <name> [<name> ...]` (modules whose name contains a word; fast; prefer this) |
| Run all tool tests | `python -I tools/run_tests.py` (one process per module, `-j N` at a time; prints failures in full and a summary) |
| Run all tool tests one after another | `python -I -m unittest discover -s tools/tests` (the same tests, much slower; no `-v`: it prints a line per test) |

Tests share one trace of the carved regions through `tools/tests/shared_trace.py`, cached in the git-ignored
`tools/tests/.trace_cache/` and keyed by a hash of every input (Anbennar's and EU4's files, the tracer's code). A changed
input traces again by itself. Generators never use the cache, and tests still render every file from the trace.
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
For an outside (AI) upscaler, export PNGs into the git-ignored `art_work/` with `png <eu4 path> <png> [--painting]`
or `monument-pngs art_work/eu4_png/great_projects` (name plate lifted, frame cropped).

## Generated files

Files written by a `tools/build_*.py` script are never edited by hand: change the script's data in `tools/data/`
and rerun it. Each system's doc lists its generated files, generator and why. `FreshnessTests` in `tools/tests/`
fail when generated files are stale.

## Systems

Read only the doc for the system you are working on. Each holds the generated-file rows and the full system notes.

| System | Doc | Generators |
|---|---|---|
| Gnomish artificery: tradition, academy, handgunners, Artifice tab, 48 inventions, invention buildings and men-at-arms, research popup, artificer factions and influence | `docs/systems/artificery.md` | `build_inventions.py`, `build_hud_override.py` |
| Magic schools (mana, knowledge, 48 spells, Magic tab with Advancements and Spells tabs), 8 magic advancements (one per school), the magic lifestyle (3 trees, focuses, traits), Liches (portrait, clothes, backgrounds, raised-dead men-at-arms paid in mana), Anbennar's mage men-at-arms and Bladedancers retuned to vanilla power per gold | `docs/systems/magic.md` | `build_spells.py`, `build_advancements.py`, `build_lifestyle_override.py`, `build_lich_maa.py` |
| Great projects: EU4 monuments in Cannor, Middle Dwarovar, Bulwar, Salahad, Deepwoods; county view paintings | `docs/systems/great-projects.md` | `build_monuments.py`, `build_county_view_override.py` |
| Dwarven holds: `dwarven_hold_holding`, 10 levels, Delve Deeper digs, ruin and clear | `docs/systems/dwarven-holds.md` | `build_holds.py`, `build_holdings_override.py`, `build_governments_override.py` |
| Serpentreach: EU4's Serpentreach (67 counties, 124 baronies) carved Godherja-style into the Serpentspine block (province 2426), under a placeholder dwarven empire `e_serpentreach`; a kingdom per hold with the EU4 hold's flag and colour; its 6 holds join the dwarven holds; five EU4 hold cultures (cobalt, diamond, flint, garnet, basalt dwarves) with a Serpentreach Dwarven language | `docs/systems/serpentreach.md` | `build_serpentreach.py` (before `build_holds.py`, `build_holding_models.py` (its province terrain feeds the dwarf model) and `build_map_graphics.py`, which carves the heightmap from the same layout) |
| Segbandal: EU4's Middle Dwarovar completed around Anbennar's `e_middle_dwarovar` (37 counties, 71 provinces traced into the rock, Gor Vazumbrog's kingdom and hold, 31 caverns); EU4 areas as duchies, a kingdom per hold, linked by history de jure changes, elders in Seghdihr's and Verkal Gulan's new duchies | `docs/systems/segbandal.md` | `build_segbandal.py` (after `build_serpentreach.py`, which draws its provinces) |
| West Dwarovar: EU4's West Dwarovar (without the Krakdhum pocket) and Serpent's Vale traced into the Serpentspine block around Anbennar's Khugdihr (128 counties, 245 provinces) under a placeholder empire `e_west_dwarovar`; nine kingdoms (Khugdihr moved in by history, still kobold and unheld), EU4 hold flags, eight new holds; caves carved with Khugdihr, the Vale painted as surface land with gates at its cave mouths; crossings (adjacencies.csv) from Dwarovrod 24 into Segbandal and Gorrod 2 into Serpentreach | `docs/systems/west-dwarovar.md` | `build_west_dwarovar.py` (after `build_serpentreach.py`, which draws its provinces, and `build_segbandal.py`) |
| RiE dwarf buildings, ore deposits, mines and the Dwarven Expedition activity | `docs/systems/rie-dwarves.md` | `build_rie_dwarves.py` (run before `build_holds.py` and `build_holdings_override.py`) |
| Elven Haven: RiE's elven holding (7 levels) and 24 elf building lines, renamed for Anbennar, elves only; conversion at game start and by decision | `docs/systems/rie-elves.md` | `build_rie_elves.py` (after `build_rie_dwarves.py`, before `build_holdings_override.py`) |
| RiE holding models, walls and army models (elves, dwarves, Castanorians) | `docs/systems/holding-models.md` | `build_holding_models.py` |
| RiE portraits (halfling hair, elves, dwarves) | `docs/systems/rie-portraits.md` | `build_portraits.py` |
| RiE character backgrounds and royal courts | `docs/systems/rie-courts.md` | `build_rie_courts.py` |
| Deepwoods grove arms and EU4 names; Cyranvar arms for the Deepwoods kingdom and empire | `docs/systems/deepwoods-groves.md` | none (imported once; edit by hand) |
| Map graphics: RiE shaders and terrain, raised dwarven mountains, dwarven gates, Segbandal carved into its mountains like Serpentreach, the map-edge fog pulled back from the Serpentspine | `docs/systems/map-graphics.md` | `build_map_graphics.py` |
| Regional elven cultures: 9 Deepwoods grove cultures (from wood elves) and 4 moon elf realm cultures (Redglades, Ibevar, Celmaldor, Venáil), set on counties and characters at game start; structure for later regional traditions | `docs/systems/elven-cultures.md` | none (hand-written) |
| Racial traditions: 40 unique traditions for racial cultures that had none (moon and wood elves and their regional cultures, dwarf clans and the five Serpentreach hold cultures, marble's Whitestone Council, Sandfang and Fieldstalker gnolls, six halfling cultures) with 17 new RiE-art men-at-arms; clan units and the restored Sundancer Legions (no levy penalty) gated by tradition; extra traditions for Reverian, Shasoura and Taric | `docs/systems/racial-traditions.md` | `build_racial_traditions.py` |
| Racial armies: levies, domain limit, elf and dwarf MAA (moon, sun, wood elves; dwarf clans) with RiE icons and art, per-holding levy correction | `docs/systems/racial-armies.md` | `build_racial_levies.py` |
| Faith men-at-arms: Dercinges, Druids, Skalds and Knights of the Spear recruited by faith tenet or patron god instead of a culture tradition | `docs/systems/faith-maa.md` | none (hand-written overrides) |
| Holy sites for Devouring Path and Silk Turban (Anbennar ships them with none); real icons for the 31 faiths Anbennar ships with the `the_dame` placeholder, and EU4's New Sun Cult icon for Jaherian Cults; icons for the 28 doctrines and tenets Anbennar ships without one (patron deities, infernalist, Khetist, Dwarven Syncretism) | `docs/systems/holy-sites.md` | `build_holy_sites.py` |
| Dynasty names: EU4 Anbennar dynasty names for the 50 culture name lists Anbennar ships with vanilla English or Frisian placeholders (named at game start for 118 landed lowborn rulers, and for every later dynasty) | `docs/systems/dynasty-names.md` | `build_dynasty_names.py` |
| Race relations: monstrous races, Liches and exposed Vampires/Werewolves hostile to everyone else (EU4 monstrous opinions as marker traits, two conquest CBs, vampire/werewolf secrets, no marriage or alliance across the line; future racial marriage rules go in `aov_race_marriage_allowed_trigger`) | `docs/systems/race-relations.md` | `build_race_relations.py` |
| Isle of Adráil: Anbennar's test realm on province 524 (`e_test`, `k_test`, `d_test_1`, Emperor Testor) turned back into EU4's Isle of Adráil under Damesear | `docs/systems/adrail.md` | none (hand-written) |
| Base art fixes: Anbennar art copied to the file name the game looks up (Adeanic knight education icons, griffon rider icon); Warcraft mod pictures for griffon riders; nine men-at-arms switched to the unit icons Anbennar ships for them; icons for the avatar, racial purist, planetouched, vampire, lycanthrope, bladeshunned, Sun Reborn and Scion of the Sun Reborn traits; Sun Reborn text | `docs/systems/base-art-fixes.md` | none (copied once) |
| Race knight badges: EU4 tech group icons (gear removed) as the knight badge for elf, dwarf, gnome and kobold rulers; RiE levy and knight pictures in the military window for elf and dwarf rulers | `docs/systems/knight-icons.md` | `build_knight_icons.py` |
| Gnoll portraits: Victoria 3 Anbennar's hyena head (blend shape, spotted fur, gnoll eyes, no hair or beard) for every `race_gnoll` character, by portrait modifier | `docs/systems/gnoll-portraits.md` | `build_gnoll_portraits.py` |

## Updating and validation

- After an Anbennar update, a CK3 patch or a Realms in Exile update, follow `docs/systems/updating.md`
  (generator order, hand re-copies of overridden triggers and interactions, which generators to rerun).
- `tools/tiger_baseline.json` holds the accepted tiger reports; `docs/systems/validation-baseline.md` explains
  each group. Read it before re-baselining.
