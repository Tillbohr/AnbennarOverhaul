# Anbennar Overhaul — project notes

Submod for the Anbennar CK3 total conversion. **All new content goes here; the base Anbennar mod
(`../anbennar-ck3-dev-master`) stays an unmodified upstream copy** so the overhaul can be laid over any
new Anbennar version. Targets CK3 **1.19.0.6**. Base-mod conventions, paths and reference-mod notes
(imported below) apply here too, except that this repo is the one you edit.

@../anbennar-ck3-dev-master/CLAUDE.md

## Dev environment

- Start Claude Code **in this folder**. `.claude/settings.local.json` (machine-specific, git-ignored) grants
  access to the base mod, game install, Workshop mods, logs and ck3-tiger.
- Local git repo on `main`, `core.autocrlf=false`; `.gitattributes` keeps `.txt`/`.yml`/`.mod` bytes exact
  (UTF-8 BOM + LF) and sends `.tga`/`.psd` to Git LFS. No remote yet.
- Base mod is read-only in practice: read it for reference, never write to it.

| Task | Command |
|---|---|
| Validate (new reports only) | `python -I tools/validate.py` |
| Validate (everything) | `python -I tools/validate.py --all` |
| Accept current reports as baseline | `python -I tools/validate.py --baseline` (only after confirming they are inherited from Anbennar) |
| Rebuild holdings override | `python -I tools/build_holdings_override.py` |
| Rebuild HUD override | `python -I tools/build_hud_override.py` |
| Run tool tests | `python -I -m unittest discover -s tools/tests -v` |

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

## Updating to a new Anbennar version

1. Replace `../anbennar-ck3-dev-master` with the new Anbennar release.
2. Run `python -I tools/build_holdings_override.py` and `python -I tools/build_hud_override.py`.
3. Run tiger (below) and fix anything that references renamed Anbennar content.
4. Test in game; check `database_conflicts.log` for overhaul keys now also defined by Anbennar.

After a CK3 patch, rerun `python -I tools/build_hud_override.py` too: its source is the game's `hud.gui`.

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
  `aov_artificery_window`) with Factions/Inventions tabs (variable `aov_artificery_tab`, unset = Factions);
  both tab bodies are placeholders until the factions and inventions systems are built.
