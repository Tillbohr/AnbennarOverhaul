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
| Run tool tests | `python -I -m unittest discover -s tools/tests -v` |
| Rebuild inventions | `python -I tools/build_inventions.py` (needs EU4 Anbennar installed for icons) |

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
| `common/modifiers/aov_invention_modifiers.txt`, `common/scripted_triggers/aov_invention_triggers.txt`, `common/script_values/aov_invention_values.txt`, `common/scripted_effects/aov_invention_effects.txt`, `common/scripted_guis/aov_invention_sgui.txt`, `common/customizable_localization/aov_invention_custom_loc.txt`, `gui/aov_inventions_generated.gui`, `localization/english/aov_inventions_l_english.yml`, `gfx/interface/icons/aov_inventions/` | `python -I tools/build_inventions.py` | One block per invention, generated from `tools/data/inventions.py` (edit the data, then rerun). |

## Updating to a new Anbennar version

1. Replace `../anbennar-ck3-dev-master` with the new Anbennar release.
2. Run `python -I tools/build_holdings_override.py` and `python -I tools/build_hud_override.py`.
3. Run tiger (below) and fix anything that references renamed Anbennar content.
4. Re-copy Anbennar's `title_revocation_standard_can_pick_title_trigger` (`common/scripted_triggers/00_interaction_triggers.txt`)
   into `common/scripted_triggers/zz_aov_interaction_triggers.txt`, keeping the `# Anbennar Overhaul` faction-title exclusion.
5. Test in game; check `database_conflicts.log` for overhaul keys now also defined by Anbennar.

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
