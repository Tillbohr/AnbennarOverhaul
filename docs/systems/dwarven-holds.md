# Dwarven holds

The dig progress bar is part of the county view override in great-projects.md; the RiE buildings, deposits and dig prerequisites are in rie-dwarves.md.

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/holdings/00_holdings.txt` | `python -I tools/build_holdings_override.py` | Holdings are whole-file only. The script copies Anbennar's file, inserts the `ADDITIONS` (marked `# Anbennar Overhaul`) and appends the new `dwarven_hold_holding` (`NEW_HOLDINGS`: castle_holding's build list after `ADDITIONS` plus RiE's `dwarven_holding` list; `ADDITIONS` also gives `castle_holding` and `city_holding` RiE's surface dwarf buildings and the 15 mines, all from `tools/data/rie_dwarves.py`). Never edit the output by hand; run `build_rie_dwarves.py` first. |
| `common/governments/00_government_types.txt`, `common/governments/01_japan_government_types.txt` | `python -I tools/build_governments_override.py` | Governments are whole-file only. The script copies Anbennar's two files and adds `dwarven_hold_holding` to `valid_holdings` of every government whose `primary_holding` or `valid_holdings` has `castle_holding` (creating the line after `primary_holding` when absent; changed lines marked `# Anbennar Overhaul`). Never edit the output by hand. |
| `common/buildings/aov_dwarven_holds.txt`, `common/script_values/aov_hold_values.txt`, `common/scripted_effects/aov_hold_setup_effects.txt`, `common/modifiers/aov_hold_modifiers.txt`, `localization/english/aov_holds_l_english.yml` | `python -I tools/build_holds.py` | Dwarven hold data from `tools/data/holds.py` (edit the data, then rerun): the 10 `dwarven_hold_01..10` levels (castle assets copied from Anbennar; level effects from RiE's `dwarven_depths_01..10` via `build_rie_dwarves.depths_level_effects`, so run that first); script values (dig cost and months per level, level numbers); the game-start setup effect (levels and ruin of the 9 holds); the level modifiers and the `aov_delving_02..10` dig markers; and their localization. |

## System

- **Dwarven holds:** the 9 EU4 dwarven holds on the CK3 map are baronies of the new `dwarven_hold_holding` (Khugdihr
  starts ruined), with 10 levels `dwarven_hold_01..10`. Levels are raised only by digs; the level effects need a
  dwarven holder and an unruined hold; each level takes RiE's `dwarven_depths_01..10` stats (`levy`, `max_garrison`, `garrison_reinforcement_factor`, province modifiers: income 0.5 to 3.5, `fort_level` 2 to 20, `building_slot_add` 0 to 9, the formerly delving-gated terrain and county blocks, ungated), copied by `build_rie_dwarves.depths_level_effects`. Castle buildings can be built in a hold: an override of Anbennar's
  holding-level requirement triggers (`common/scripted_triggers/zz_aov_building_requirement_triggers.txt`) treats hold
  levels 1/3/5/8 as castle levels 1-4. The old deep mine, runeforge and hall of the ancestors buildings are gone (RiE's quarry, forge and vault lines cover them). **Dig prerequisites:** level N needs the buildings RiE's level N asks for, as `aov_hold_dig_requirements_<N>_trigger` (province scope, `aov_rie_dwarf_triggers.txt`; quarries, roads, toolmaker guild, specializations, and from level 4 any mine of a given level); `aov_hold_dig_requirements_met_trigger` picks the trigger for the hold's next level. `aov_can_start_dig_base` (`aov_hold_triggers.txt`: working hold, below level 10, not digging, not occupied, dwarven holder) is the check without prerequisites; `aov_can_dig_at` adds them. The decision needs the base check, and picker event `aov_hold_delve.1` shows a hold that still lacks buildings greyed out with the prerequisite tooltip (`show_as_unavailable`). A running dig is not cancelled when a requirement is lost. A hold needs an ore deposit and its mine to dig past level 3; Rubyhold, Verkal Gulan and Anvilwright start with one, the others need a Mining expedition. Holds that start above level 1 keep their start levels. Dig with the **Delve Deeper** decision
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
  county view, and built holdings on dwarven terrain show Anbennar's EU4 terrain picture instead of vanilla's castle
  art (`tools/data/holding_art.py`, via `EXTRA_ART` of `tools/build_monuments.py`). Data in `tools/data/holds.py` (assets, names, `next_building`) and `tools/data/rie_dwarves.py` (level effects, holding lists, prerequisites), generated by
  `tools/build_holds.py` and `tools/build_rie_dwarves.py`; hand-written logic in the `aov_hold_*` files (decisions, on_actions, effects, triggers,
  `aov_hold_formats.txt`). Specs `docs/superpowers/specs/2026-10-10-dwarven-hold-digging-design.md` and `2026-10-17-rie-dwarves-design.md`.
