# RiE Dwarves Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import every Realms in Exile dwarf building line, its 15 ore deposits and mines, give the dwarven hold levels RiE's `dwarven_depths` effects and prerequisites, and add a hand-written Dwarven Expedition activity (Mining, Archaeology placeholder).

**Architecture:** A pure rewrite module (`tools/rie_dwarf_rewrite.py`) turns RiE building text into Anbennar-valid text by rules from `tools/data/rie_dwarves.py`; the generator `tools/build_rie_dwarves.py` reads RiE, applies the rules, checks every identifier, and writes the building, modifier, trigger, effect, value, loc, icon and background files. `build_holds.py` takes its level effects from the generator, `build_holdings_override.py` its building lists from the data. The activity, its events, on_actions and loc are hand-written script.

**Tech Stack:** Python 3 (stdlib only, `unittest`), CK3 1.19 script, ck3-tiger via `tools/validate.py`.

**Spec:** `docs/superpowers/specs/2026-10-17-rie-dwarves-design.md`

## Global Constraints

- Never write to `../anbennar-ck3-dev-master`, the game folder or the RiE Workshop folder; read only.
- Generated and hand-written `.txt`/`.yml`: UTF-8 with BOM, LF line endings, tabs (RiE files mix CRLF: normalise with `bp.lf`).
- New files carry the `aov_` prefix; RiE building, modifier and loc keys keep RiE's names unprefixed; new keys we invent start `aov_`.
- Run Python as `python -I`; tool modules add their folder to `sys.path` as `build_rie_courts.py` does.
- Generated files start with the two `HEADER` lines naming `tools/build_rie_dwarves.py`; never edit them by hand.
- Generator errors raise `GeneratorError` (from `build_hud_override`); `main()` prints `error: ...` and returns 1.
- Ore weights (spec): iron, copper, tin, lead 40; quartz, onyx, peridot, amethyst 12; silver 8; gold 6; sapphire, emerald, ruby 4; diamond 3; mithril 1.
- Start deposits (spec): `b_hul_az_amekh` ruby, `b_gulandhum` gold, `b_anvilwright` silver.
- Dig cost and time stay `150 x level` gold and `12 x (8 + 4 x (N - 1))` months.
- Expedition: 8-month phase, pulses at months 2/4/6, outcome at 7; success base 30, + stewardship/4 (max 10), crew +0/+10/+20, +10 in a hold, max 90; pulse steps 3/5/10; cooldown 4 years; `max_guests = 10`.

## Review Focus

- A rewrite that leaves an empty block (`OR = { }` after the orc branch goes, `culture = { }` after the innovation goes) must vanish, not stay: an empty `OR` is false in CK3 and would lock the building. Test in Task 1.
- `build_rie_courts.py`'s `test_no_orphan_files` scans `event_scenes`; our two copied pictures there would read as orphans. Test in Task 5.
- A province that already has a deposit must never get a second one (start setup on a prospected province, a Mining expedition there). Tests in Tasks 3 and 6.
- A non-dwarf holder of a hold or a dwarf-only building: no `is_dwarf` may survive the rewrite and every RiE `is_enabled` that tested `is_dwarf` must test `is_dwarvish_culture`. Test in Task 2.
- A running dig whose prerequisite building is later lost keeps going: the requirement triggers are used only when a dig starts. Test in Task 4.

---

## File Structure

| File | Responsibility |
|---|---|
| `tools/data/rie_dwarves.py` (create) | RiE source paths, rewrite tables, ores and weights, start deposits, holding lists, backgrounds, activity icons |
| `tools/rie_dwarf_rewrite.py` (create) | pure text rewrites of one RiE building block; no file access |
| `tools/build_rie_dwarves.py` (create) | read RiE, rewrite, check identifiers, render and write every generated file |
| `tools/tests/test_rie_dwarf_rewrite.py` (create) | rewrite rules on samples |
| `tools/tests/test_build_rie_dwarves.py` (create) | data checks, real build, freshness |
| `tools/build_holds.py`, `tools/data/holds.py` (modify) | level effects from RiE, remove the three dwarven buildings |
| `tools/build_holdings_override.py` (modify) | holding lists from the data |
| `common/scripted_triggers/aov_hold_triggers.txt`, `events/aov_hold_delve_events.txt`, `common/on_action/aov_hold_on_actions.txt` (modify) | dig prerequisites, start deposits hook |
| `common/activities/activity_types/aov_dwarven_expedition.txt`, `common/on_action/aov_dwarven_expedition_on_actions.txt`, `common/script_values/aov_expedition_values.txt`, `common/scripted_effects/aov_expedition_effects.txt`, `events/aov_dwarven_expedition_events.txt`, `localization/english/aov_dwarven_expedition_l_english.yml` (create) | the activity |
| `tools/tests/test_dwarven_expedition.py` (create) | static checks on the activity script |

---

### Task 1: Data module and rewrite engine

**Files:**
- Create: `tools/data/rie_dwarves.py`, `tools/rie_dwarf_rewrite.py`, `tools/tests/test_rie_dwarf_rewrite.py`

**Interfaces:**
- Produces (data): `RIE_BUILDING_FILES: tuple[str, ...]` (`common/buildings/lotr_buildings/lotr_dwarven_buildings.txt`, `.../lotr_mines_buildings.txt`); `DEPTHS_FILE = "common/buildings/lotr_buildings/lotr_dwarven_settlement_holdings.txt"`; `ORE_FILE = "common/modifiers/lotr_modifiers/lotr_ore_modifiers.txt"`; `ORES: tuple[str, ...]` (15, RiE order); `ORE_WEIGHTS: dict[str, int]`; `START_DEPOSITS: dict[str, str]` (barony -> ore); `MOUNTAIN_TERRAINS`, `HILL_TERRAINS`, `DWARVEN_TERRAINS: tuple[str, ...]`; `TOKEN_RENAMES: dict[str, str]` (`is_dwarf` and `lotr_subterranean_buildings` -> `is_dwarvish_culture`; the four `lotr_dwarven_*` triggers -> `aov_rie_hold_province_trigger`, `aov_rie_mountain_terrain_trigger`, `aov_rie_hill_terrain_trigger`, `aov_rie_surface_dwarf_trigger`; `lotr_dwarven_is_mountain_dwarf` -> `aov_rie_dwarven_holder_trigger`); `DROP_STATEMENTS: tuple[str, ...]` (regexes of whole statements to remove: `is_orc = yes`, `has_dynasty_perk = lotr_\w+`, `has_innovation = innovation_iron_hills_goat_domestication`, `has_building_or_higher = elven_settlement_\d+`); `DROP_BLOCKS: tuple[str, ...]` (`province_dynasty_modifier`); `UNGATED_PARAMETERS = ("unlock_full_delving",)`; `DROP_EFFECT_DESC = r"_artifact_crafting_buff$"`; `DEPTHS_RENAME = (r"\bdwarven_depths_(\d\d)\b", r"dwarven_hold_\1")`; `HOLD_BUILDINGS`, `SURFACE_BUILDINGS: list[str]` (level-01 keys; Task 3); `BACKGROUNDS: dict[str, tuple[str, str, str]]` (key -> (picture, environment, ambience), spec Section 4); `ACTIVITY_ICONS: dict[str, str]` (RiE path -> our path, Task 5).
- Produces (rewrite): `rewrite_block(body: str, known_parameters: set[str]) -> tuple[str, list[str]]` (rewritten block text, notes of what was removed); `prune_empty(text: str) -> str`.

- [ ] **Step 1: Write the failing tests** in `test_rie_dwarf_rewrite.py`, each on a small RiE-shaped block string:

```python
def test_is_dwarf_becomes_anbennar_trigger(self):
    out, _ = rw.rewrite_block("x_01 = {\n\tis_enabled = {\n\t\tscope:holder = { is_dwarf = yes }\n\t}\n}\n", set())
    self.assertIn("is_dwarvish_culture = yes", out); self.assertNotIn("is_dwarf ", out)
def test_orc_branch_leaves_no_empty_or(self):   # OR = { scope:holder = { is_dwarf = yes } scope:holder = { is_orc = yes } }
    self.assertNotIn("is_orc", out); self.assertEqual(out.count("OR = {"), 1)  # the dwarf branch stays
def test_only_orc_or_is_removed_whole(self):    # OR = { is_orc = yes }  ->  no "OR" left
def test_depths_become_hold_levels(self):       # has_building_or_higher = dwarven_depths_04 -> dwarven_hold_04
def test_dynasty_modifier_block_removed(self):  # province_dynasty_modifier = { county_holder_dynasty_perk = lotr_khazad_legacy_5 ... } gone, note names it
def test_dynasty_perk_tooltip_removed(self):    # custom_tooltip = { text = dwarven_forge_dynasty_requirement county.holder.dynasty ?= { has_dynasty_perk = lotr_crafting_legacy_3 } } gone whole
def test_goat_innovation_condition_removed(self):  # scope:holder = { culture = { has_innovation = innovation_iron_hills_goat_domestication } } gone whole
def test_unlock_full_delving_ungated(self):     # county_culture_modifier = { parameter = unlock_full_delving development_growth = 0.05 } -> county_modifier = { development_growth = 0.05 }
def test_known_parameter_kept(self):            # parameter = quarries_building_bonuses kept when in known_parameters
def test_unknown_parameter_block_removed(self): # parameter = rie_only_thing -> block gone, note names it
def test_crafting_effect_desc_removed(self):    # effect_desc = dwarven_forge_01_artifact_crafting_buff gone
def test_terrain_triggers_renamed(self):        # lotr_dwarven_hill_buildings_requirement_terrain = yes -> aov_rie_hill_terrain_trigger = yes
def test_four_space_indentation_handled(self):  # RiE mixes "    is_enabled = {" with tabs; same result as tabbed input
def test_data_ores_and_weights(self):           # set(data.ORE_WEIGHTS) == set(data.ORES), len 15, weights exactly as Global Constraints
```

- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p test_rie_dwarf_rewrite.py -v` — expect import failure.

- [ ] **Step 3: Write `tools/data/rie_dwarves.py`** with the constants above (module docstring naming the spec), then **`tools/rie_dwarf_rewrite.py`**: token renames by whole-word regex; statement drops by regex; block drops and `parameter` handling via `build_portraits.blocks(text, None, strict=False)` (innermost first, so offsets stay valid: process from the end of the text backwards); a statement drop removes its line, a dropped `custom_tooltip`/scope block is the smallest block whose remaining content became empty; then `prune_empty` removes blocks with no non-comment content, repeatedly until stable.

- [ ] **Step 4: Run the tests** — expect PASS.

- [ ] **Step 5: Commit** `git add tools/data/rie_dwarves.py tools/rie_dwarf_rewrite.py tools/tests/test_rie_dwarf_rewrite.py && git commit -m "RiE dwarves: data and building rewrite rules"`

---

### Task 2: Generator — buildings, mines, ore modifiers, values, loc, icons

**Files:**
- Create: `tools/build_rie_dwarves.py`, `tools/tests/test_build_rie_dwarves.py`
- Output: `common/buildings/aov_rie_dwarven_buildings.txt`, `common/buildings/aov_rie_mines.txt`, `common/modifiers/aov_rie_ore_modifiers.txt`, `common/script_values/aov_rie_dwarf_values.txt`, `localization/english/aov_rie_dwarves_l_english.yml`, icons under `gfx/interface/icons/building_types/`

**Interfaces:**
- Consumes: Task 1's `rewrite_block`, data constants; `build_portraits` (`Roots`, `blocks`, `code`, `read`, `lf`, `place_file`, `_exists_outside`, `effective_texts`, `BOM`, `MARKER`).
- Produces: `build_all(roots: Roots, notes: list | None = None) -> dict[str, bytes]` (every generated file, later tasks add to it); `rie_blocks(roots, rel) -> list[tuple[str, str]]` ((key, LF text) of top-level blocks); `depths_level_effects(roots) -> dict[int, str]` (Task 4); `main() -> int` with `--rie/--anbennar/--game` like `build_rie_courts.py`; paths `BUILDINGS_FILE`, `MINES_FILE`, `ORE_MODIFIERS_FILE`, `VALUES_FILE`, `LOC_FILE`.

- [ ] **Step 1: Write the failing tests** (`RealTests`, skipped without RiE/Anbennar/game, `build_all(REAL)` once in `setUpClass`):

```python
def test_every_rie_building_copied_once(self):      # keys in both outputs == every top-level key of RIE_BUILDING_FILES (344 today)
def test_no_rie_identifiers_left(self):             # no r"\blotr_|\bis_dwarf\b|\bis_orc\b|dwarven_depths_|elven_settlement_" in any output .txt
def test_dwarf_gates_survive(self):                 # every RiE block whose is_enabled has is_dwarf: our is_enabled has is_dwarvish_culture
def test_mines_need_their_deposit(self):            # for ore in ORES, n in 1..10: f"{ore}_mines_{n:02d}" can_construct_potential has f"has_province_modifier = mining_{ore}_province_modifier"
def test_ore_modifiers_verbatim(self):              # the 15 blocks equal RiE's (after lf)
def test_rie_only_script_values_copied(self):       # elven_building_garrison_reinforcement_factor_tier_1 defined in VALUES_FILE; every value name used in our buildings exists in VALUES_FILE, Anbennar or the game
def test_loc_for_every_building_and_tooltip(self):  # building_<key>, building_type_<key> for every key; every "text = X" and "effect_desc = X" key in our output has loc in LOC_FILE, Anbennar or the game
def test_type_icons_exist(self):                    # every type_icon file is in our output, Anbennar or the game
def test_files_have_bom_and_lf(self):
```

Plus unit tests without RiE: `test_unknown_trigger_stops_build` (a fake `roots` with a block using `lotr_made_up = yes` raises `GeneratorError` naming it) and `test_key_collision_stops_build` (a key Anbennar defines raises).

- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p test_build_rie_dwarves.py -v` — expect FAIL (no module).

- [ ] **Step 3: Implement** `build_all` for these files. Order: read and rewrite every block (notes collected); check identifiers: (a) `has_building(_or_higher)? = X` -> X copied or in Anbennar/game buildings; (b) `X = yes|no` where X is a scripted trigger name in RiE's `common/scripted_triggers` -> renamed in `TOKEN_RENAMES` or in Anbennar/game; (c) `parameter = X` kept -> defined `X = yes` in Anbennar's or the game's `common/culture`; (d) value identifiers on the right of `cost_gold`, `levy`, `max_garrison`, `garrison_reinforcement_factor`, `construction_time` and modifier lines -> Anbennar/game script value, else copied verbatim from RiE's `common/script_values` into `VALUES_FILE`, else error; (e) any key Anbennar or the game defines in `common/buildings` -> error. Loc: index RiE's `localization/english/**/*.yml` (key -> line) and copy the lines for the building keys, the `text =`/`effect_desc =` keys and the ore modifiers that Anbennar and the game lack. Icons: `type_icon` file names resolve under `gfx/interface/icons/building_types/`, copied with `place_file`. One note lists every removal grouped by rule with counts. Also `depths_level_effects`: read `DEPTHS_FILE`, rewrite each `dwarven_depths_<n>` block, return only its effect fields (Interfaces of Task 4); its `elven_building_garrison_reinforcement_factor_tier_1` goes into `VALUES_FILE` by rule (d).

- [ ] **Step 4: Run the build** `python -I tools/build_rie_dwarves.py` — expect `wrote N files` and notes; read the notes and confirm only the rule-listed removals occur.

- [ ] **Step 5: Run the tests** — expect PASS.

- [ ] **Step 6: Commit** generator, tests and output: `git commit -m "RiE dwarves: import dwarf buildings, mines and ore deposits"`

---

### Task 3: Triggers, deposit effects, holding lists

**Files:**
- Modify: `tools/build_rie_dwarves.py`, `tools/data/rie_dwarves.py`, `tools/build_holdings_override.py`, `tools/tests/test_build_rie_dwarves.py`, `tools/tests/test_build_holdings_override.py`
- Output: `common/scripted_triggers/aov_rie_dwarf_triggers.txt`, `common/scripted_effects/aov_rie_deposit_effects.txt`, `common/holdings/00_holdings.txt`

**Interfaces:**
- Produces triggers (all in `TRIGGERS_FILE`): province scope `aov_rie_hold_province_trigger` (`has_holding_type = dwarven_hold_holding`), `aov_rie_mountain_terrain_trigger` / `aov_rie_hill_terrain_trigger` (`OR` of `terrain = <t>`), `aov_rie_dwarven_holder_trigger` (`scope:holder = { is_dwarvish_culture = yes }`), `aov_rie_surface_dwarf_trigger` (custom tooltip `aov_rie_surface_dwarf_tt`: dwarven holder and `NOT = { has_holding_type = dwarven_hold_holding }`), `aov_rie_has_deposit_trigger` (`OR` of the 15 `has_province_modifier`).
- Produces effects (`DEPOSIT_EFFECTS_FILE`): `aov_expedition_roll_deposit_effect` (province scope; `random_list` with `ORE_WEIGHTS`, each branch adds `mining_<ore>_province_modifier` and `scope:activity ?= { set_variable = { name = aov_expedition_ore value = flag:<ore> } }`; whole effect inside `if = { limit = { NOT = { aov_rie_has_deposit_trigger = yes } } }`); `aov_rie_deposit_setup_effect` (no scope; per `START_DEPOSITS` entry `title:<barony>.title_province = { if = { limit = { NOT = { aov_rie_has_deposit_trigger = yes } } add_province_modifier = mining_<ore>_province_modifier } }`).
- Produces data: `HOLD_BUILDINGS` (RiE `dwarven_holding` list minus orc, oath and `breweries_01` entries), `SURFACE_BUILDINGS` (RiE `castle_holding` dwarf entries: `dwarven_terrace_farm_01 … goat_pastures_01`) and `MINE_BUILDINGS = [f"{ore}_mines_01" for ore in ORES]`.

- [ ] **Step 1: Write the failing tests:**

```python
def test_holding_lists_match_rie(self):          # RealTests: HOLD_BUILDINGS == RiE dwarven_holding list filtered; SURFACE_BUILDINGS + MINE_BUILDINGS == RiE castle_holding dwarf and mine entries, same order
def test_roll_weights(self):                     # parse the random_list: {ore: weight} == data.ORE_WEIGHTS
def test_roll_and_setup_skip_provinces_with_a_deposit(self):  # both effects contain "NOT = { aov_rie_has_deposit_trigger = yes }"
def test_start_deposits(self):                   # setup has title:b_hul_az_amekh ... ruby, b_gulandhum gold, b_anvilwright silver
def test_start_baronies_exist(self):             # RealTests: each barony in Anbennar's common/landed_titles
def test_unknown_start_ore_stops_build(self):    # mock START_DEPOSITS {"b_x": "adamant"} -> GeneratorError
def test_every_renamed_trigger_defined(self):    # every value of TOKEN_RENAMES ending _trigger is defined in TRIGGERS_FILE
```

In `test_build_holdings_override.py`: `test_hold_gets_rie_buildings_once` (hold list holds every `HOLD_BUILDINGS` key exactly once, no `deep_mine_01`/`runeforge_01`/`hall_of_the_ancestors_01`), `test_castle_and_city_get_surface_and_mines` (both lists hold every `SURFACE_BUILDINGS` + `MINE_BUILDINGS` key once).

- [ ] **Step 2: Run both test files** — expect FAIL.

- [ ] **Step 3: Implement:** generator renders `TRIGGERS_FILE` and `DEPOSIT_EFFECTS_FILE`; `check_holding_lists(roots)` raises when the data lists drift from RiE's `common/holdings/lotr_holdings.txt` / `00_holdings.txt`. In `build_holdings_override.py`: `ADDITIONS["castle_holding"]` and `["city_holding"]` append `SURFACE_BUILDINGS + MINE_BUILDINGS`; `NEW_HOLDINGS["dwarven_hold_holding"]["extra"] = HOLD_BUILDINGS`; `add_holding` drops duplicates keeping the first.

- [ ] **Step 4: Run both generators** (`build_rie_dwarves.py`, `build_holdings_override.py`) and both test files — expect PASS.

- [ ] **Step 5: Commit** `git commit -m "RiE dwarves: deposit effects, terrain triggers and holding lists"`

---

### Task 4: Hold levels from RiE's depths, dig prerequisites, start deposits

**Files:**
- Modify: `tools/build_holds.py`, `tools/data/holds.py`, `tools/build_rie_dwarves.py`, `tools/tests/test_build_holds.py`, `tools/tests/test_hold_data.py`, `common/scripted_triggers/aov_hold_triggers.txt`, `events/aov_hold_delve_events.txt`, `common/on_action/aov_hold_on_actions.txt`
- Output: `common/buildings/aov_dwarven_holds.txt`, `localization/english/aov_holds_l_english.yml` (regenerated), `aov_rie_dwarf_triggers.txt` (dig requirements)

**Interfaces:**
- Consumes: Task 2 `depths_level_effects(roots) -> dict[int, str]`: for n in 1..10 the rewritten lines of `dwarven_depths_<n>`'s `levy`, `max_garrison`, `garrison_reinforcement_factor`, `province_modifier`, `province_terrain_modifier`, `county_modifier`/`county_culture_modifier` blocks (tab-indented one level, ready to paste).
- Produces: province-scope `aov_hold_dig_requirements_<N>_trigger` for N in 2..10 (RiE `can_construct` of depths N, rewritten, without `has_building_or_higher = dwarven_hold_<N-1>`) and `aov_hold_dig_requirements_met_trigger` (`trigger_if = { limit = { aov_hold_level = <N-1> } aov_hold_dig_requirements_<N>_trigger = yes }` for each N); `render_level(n, assets, gfx, effects: str)`; `render_all(root, roots: bp.Roots)`.

- [ ] **Step 1: Write the failing tests** in `test_build_holds.py` (replace `test_level_effects_match_data`, `FlatValueTests`, every dwarven-building test and `BUILDING_KEYS`):

```python
def test_level_effects_come_from_rie(self):        # RealTests: each dwarven_hold_<n> contains depths_level_effects(REAL)[n] verbatim
def test_level_ten_matches_rie(self):              # dwarven_hold_10 province_modifier has fort_level = 20 and building_slot_add = 9
def test_levels_still_not_buildable(self):         # can_construct_potential always = no, is_enabled unchanged (dwarven holder, not ruined)
def test_old_dwarven_buildings_gone(self):         # no deep_mine/runeforge/hall_of_the_ancestors in buildings, loc, holds.py
def test_dig_requirements_for_levels_2_to_10(self):# triggers 2..10 exist; level 5 needs dwarven_quarry_03 and has_mines_04_or_higher tooltip; none names dwarven_hold_<N-1>
def test_dig_start_checks_requirements(self):      # aov_can_dig_at contains aov_hold_dig_requirements_met_trigger = yes
def test_running_dig_ignores_requirements(self):   # aov_hold_on_actions.txt and aov_hold_dig_on_actions.txt never name aov_hold_dig_requirements
def test_picker_shows_blocked_holds(self):         # every hold option in aov_hold_delve.1 has show_as_unavailable = { title:<barony> = { holder = root } }
def test_game_start_sets_deposits(self):           # aov_hold_game_start effect calls aov_rie_deposit_setup_effect = yes after aov_hold_setup_effect = yes
```

In `test_hold_data.py`: drop `test_levels_rise` and the `DWARVEN_BUILDINGS` part of `test_buildings_and_constants`.

- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p "test_*hold*.py" -v` — expect FAIL.

- [ ] **Step 3: Implement:** remove `_LEVEL_ROWS`, `FLAT_VALUES`, `_FLAT_TIERS`, `LEVELS`, `DWARVEN_BUILDINGS` from `holds.py` and the building code, names and AI table from `build_holds.py`; `render_level` pastes the RiE effects; `build_holds.py` gains `--rie/--anbennar/--game` (default `bp.Roots.default()`). Generator adds the requirement triggers to `TRIGGERS_FILE` with their RiE tooltip loc keys (`has_mines_0N_or_higher`, `has_specialization_0N_or_higher`, copied in Task 2's loc). Hand edits: `aov_can_dig_at` gets `aov_hold_dig_requirements_met_trigger = yes`; each option of `aov_hold_delve.1` gets `show_as_unavailable = { title:<barony> = { holder = root } }`; `aov_hold_game_start` gets `aov_rie_deposit_setup_effect = yes`.

- [ ] **Step 4: Rerun** `build_rie_dwarves.py`, `build_holds.py`, `build_holdings_override.py`; run the hold tests — expect PASS.

- [ ] **Step 5: Commit** `git commit -m "Dwarven holds: RiE depths effects and dig prerequisites; remove the three hold buildings"`

---

### Task 5: Expedition art and event backgrounds

**Files:**
- Modify: `tools/build_rie_dwarves.py`, `tools/data/rie_dwarves.py`, `tools/tests/test_build_rie_dwarves.py`, `tools/tests/test_build_rie_courts.py`
- Output: `common/event_backgrounds/aov_dwarven_expedition_backgrounds.txt`; pictures at RiE's paths (`gfx/interface/illustrations/activity_backgrounds/lotr_cave_interior.dds`, `.../event_scenes/lotr_halls.dds`, `.../event_scenes/lotr_dwarven_gate.dds`); icons per `ACTIVITY_ICONS`

**Interfaces:**
- Produces: event backgrounds `aov_expedition_cave`, `aov_expedition_halls`, `aov_expedition_gate` (each `background = { reference = "<picture>" environment = "<env>" ambience = "<amb>" }`); `ACTIVITY_ICONS` = `activities/activity_mining.dds` -> `activities/activity_dwarven_expedition.dds`, `activity_mining_header.dds` -> `activity_dwarven_expedition_header.dds`, `activity_phases/mining_phase.dds` -> `activity_phases/aov_expedition_phase.dds`, `activity_option_categories/mining_option_surveyors.dds` -> `aov_expedition_crew.dds`, `mining_option_party_size.dds` -> `aov_expedition_type.dds`, `activity_types/mining_type_prospecting_icon.dds` -> `aov_expedition_mining_icon.dds`, `mining_type_standard_icon.dds` -> `aov_expedition_archaeology_icon.dds` (all under `gfx/interface/icons/`; names follow the game's convention `activities/<key>.dds`, `<key>_header.dds`, `activity_phases/<phase>.dds`, `activity_option_categories/<category>.dds`, `activity_types/<option>_icon.dds`).

- [ ] **Step 1: Write the failing tests:** `test_backgrounds_defined_with_copied_pictures` (three keys in the backgrounds file, each picture in the output or Anbennar/game, environments `environment_event_alley`/`environment_travel_mountain_settlement` exist in the game's `gfx/portraits/environments`), `test_activity_icons_copied` (every `ACTIVITY_ICONS` target in the output, byte-equal to RiE's source), `test_background_clash_stops_build` (a picture Anbennar has with other bytes raises). In `test_build_rie_courts.py` `FreshnessTests.test_no_orphan_files`: files produced by `build_rie_dwarves.build_all(REAL)` are not orphans (add them to `produced`).

- [ ] **Step 2: Run** both test files — expect FAIL.

- [ ] **Step 3: Implement** the copies with `bp.place_file` (error when it returns a renamed path for a picture: the spec forbids clashes) and the backgrounds file.

- [ ] **Step 4: Rerun** `build_rie_dwarves.py`; run both test files — expect PASS.

- [ ] **Step 5: Commit** `git commit -m "RiE dwarves: expedition icons and event backgrounds from RiE"`

---

### Task 6: The activity definition

**Files:**
- Create: `common/activities/activity_types/aov_dwarven_expedition.txt`, `common/on_action/aov_dwarven_expedition_on_actions.txt`, `common/script_values/aov_expedition_values.txt`, `common/scripted_effects/aov_expedition_effects.txt`, `localization/english/aov_dwarven_expedition_l_english.yml`, `tools/tests/test_dwarven_expedition.py`

**Interfaces:**
- Consumes: `aov_rie_mountain_terrain_trigger`, `aov_rie_hold_province_trigger`, `aov_rie_has_deposit_trigger`, `aov_expedition_roll_deposit_effect` (Task 3); backgrounds and icon names (Task 5).
- Produces: activity `activity_dwarven_expedition`; special category `aov_expedition_type` with options `aov_expedition_mining`, `aov_expedition_archaeology`; category `aov_expedition_crew` with `aov_expedition_crew_local`, `_skilled`, `_master`; phase `aov_expedition_phase`; activity variable `aov_expedition_success_chance`; on_actions `aov_expedition_start_events`, `aov_expedition_random_pulse`, `aov_expedition_outcome`; values `aov_expedition_success_chance_value`, `aov_expedition_success_minor_value` 3, `_medium_value` 5, `_major_value` 10, `aov_expedition_cooldown_years` 4, `aov_expedition_crew_skilled_cost`, `_master_cost` (RiE's 10 and 35 x `activity_cost_scale_by_tier` x `activity_cost_scale_by_era`); effects `aov_expedition_change_success_effect = { AMOUNT = }` (clamps 0..90), `aov_expedition_archaeology_outcome_effect` (prestige + log entry `aov_expedition_archaeology_log`, comment: placeholder for the user's archaeology design).

- [ ] **Step 1: Write the failing tests** (`test_dwarven_expedition.py`, static text checks like `test_hold_dig_events.py`):

```python
def test_host_must_be_dwarf_ruler(self):            # is_shown has is_dwarvish_culture = yes and highest_held_title_tier > tier_barony
def test_location_is_mountain_or_dwarven(self):     # is_location_valid has aov_rie_mountain_terrain_trigger = yes; province_filter = domicile_realm
def test_mining_needs_province_without_deposit(self):  # aov_expedition_mining is_valid has NOT = { aov_rie_has_deposit_trigger = yes }
def test_archaeology_needs_dwarven_terrain(self):   # its is_valid names exactly data.DWARVEN_TERRAINS
def test_phase_schedule(self):                      # progress_activity_phase_after = { months = 8 }; pulses months = 2, 4, 6; outcome months = 7
def test_success_chance_formula(self):              # value block: base 30, stewardship divide 4 max 10, crew +10/+20, +10 with aov_rie_hold_province_trigger, max = 90
def test_every_option_category_and_phase_has_loc_and_icon(self):  # loc keys and Task 5 icon files exist for every category, option, phase, the activity
def test_no_rie_branches(self):                     # no lotr_, is_dwarf, overseer_of_the_mines, stone_singer, murder, struggle
```

- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p test_dwarven_expedition.py -v` — expect FAIL.

- [ ] **Step 3: Write the activity** from RiE's `common/activities/activity_types/lotr_mining.txt` as the structural template: keep its top-level keys (`is_shown`, `can_start`, `can_start_showing_failures_only`, `is_valid`, `on_invalidated`, `cooldown`, `cost`, `is_single_location`, `province_filter`, `ai_province_filter`, `is_location_valid`, `province_score`, `province_description`, `special_option_category`, `options`, `max_guest_arrival_delay_time`, `phases`, `ai_check_interval`, `ai_will_select_province`, `ai_will_do`, `guest_invite_rules`, `max_guests`, `host_intents`, `guest_intents`, `guest_join_chance`, `allow_zero_guest_invites`, `on_start`, `on_complete`, `map_entity`, `background`, `window_characters`, `activity_window_widgets` limited to `"activity_plugin_widgets_summary"`), with values from the spec and Global Constraints (cost `standard_activity_base_cost` x `activity_cost_scale_by_era` as RiE's `cost` block, Mining option x0.5 as RiE's prospecting option, crew option costs added); drop the landless-adventurer, overseer/stone-singer, murder, struggle, crafting and RiE region branches. Backgrounds: `aov_expedition_halls` picture when the location passes `aov_rie_hold_province_trigger` or terrain `cavern`/`dwarven_road`, `lotr_dwarven_gate` when travelling from dwarf-owned mountains or hills, `lotr_cave_interior` otherwise. AI: `ai_will_do` 100 for Mining when a realm province passes the location rules without a deposit, 0 for Archaeology. Loc in `aov_dwarven_expedition_l_english.yml` for every activity, option, category, phase, tooltip and log key.

- [ ] **Step 4: Run the tests** — expect PASS.

- [ ] **Step 5: Commit** `git commit -m "Dwarven Expedition activity: definition, values, on_actions"`

---

### Task 7: Expedition events

**Files:**
- Create: `events/aov_dwarven_expedition_events.txt`; Modify: `localization/english/aov_dwarven_expedition_l_english.yml`, `common/on_action/aov_dwarven_expedition_on_actions.txt`, `tools/tests/test_dwarven_expedition.py`

**Interfaces:**
- Consumes: Task 6 values, effects, on_actions; Task 3 `aov_expedition_roll_deposit_effect`.
- Produces: namespace `aov_expedition`; `aov_expedition.1` setting out (background `aov_expedition_gate`); pulse events `.101` rich vein, `.102` cave-in, `.103` flooded shaft, `.104` old dwarven carvings, `.105` a lost miner, `.106` a quarrel among the delvers (backgrounds `aov_expedition_cave`, or `aov_expedition_halls` in a hold/cavern/road location); outcomes `.900` Mining success, `.901` Mining failure, `.902` Archaeology.

- [ ] **Step 1: Write the failing tests:**

```python
def test_every_event_has_loc_and_options(self):     # t, desc and every option name in loc
def test_pulse_on_action_lists_the_six_pulses(self):# random_events of aov_expedition_random_pulse == {101..106}
def test_pulses_change_success_by_spec_steps(self): # every aov_expedition_change_success_effect AMOUNT is ±minor/medium/major value
def test_costly_options_check_gold(self):           # every option with remove_short_term_gold has a gold trigger
def test_outcome_rolls_against_success(self):       # aov_expedition_outcome picks .900/.901 by var:aov_expedition_success_chance for Mining, .902 for Archaeology
def test_success_rolls_a_deposit(self):             # .900 calls aov_expedition_roll_deposit_effect on scope:activity.activity_location and names var:aov_expedition_ore in loc
def test_backgrounds_are_ours(self):                # every override_background reference is one of data.BACKGROUNDS
```

- [ ] **Step 2: Run** — expect FAIL.

- [ ] **Step 3: Write the events and loc.** Ore name in `.900`'s desc via a `first_valid` `triggered_desc` per ore flag (`scope:activity.var:aov_expedition_ore = flag:<ore>`), using RiE's modifier names from `aov_rie_dwarves_l_english.yml`.

- [ ] **Step 4: Run the tests** — expect PASS.

- [ ] **Step 5: Commit** `git commit -m "Dwarven Expedition: events"`

---

### Task 8: Validation and docs

**Files:**
- Modify: `tools/tiger_baseline.json` (only after checking), `CLAUDE.md`

- [ ] **Step 1: Run** `python -I -m unittest discover -s tools/tests -v` — expect all PASS (or skips only where RiE is absent).

- [ ] **Step 2: Run** `python -I tools/validate.py` — expect `fatal: 0, error: 0`. Fix every report in our hand-written files and our generated lines. Reports inside verbatim-copied RiE code (unchanged by our rewrites) may be baselined with `--baseline` only after listing them; record count and kind in `CLAUDE.md`'s Validation paragraph.

- [ ] **Step 3: Update `CLAUDE.md`:** task-table row `Rebuild RiE dwarves | python -I tools/build_rie_dwarves.py (needs Realms in Exile installed; run before build_holds.py and build_holdings_override.py)`; generated-files row listing Task 2-5 outputs; Updating steps (Anbennar and RiE updates); Dwarven holds Systems entry (RiE depths effects, dig prerequisites, removed buildings, holding lists from `tools/data/rie_dwarves.py`); new Systems entry "RiE dwarf buildings and the Dwarven Expedition" (deposits, weights, start deposits, mines, activity, Archaeology placeholder, risks to confirm in game from the spec).

- [ ] **Step 4: Commit** `git commit -m "RiE dwarves: validation baseline and docs"`

- [ ] **Step 5: In-game checklist** (hand to the user; not automatable): planner shows the expedition for a dwarf ruler and not for a human; a Mining expedition can end with a deposit and the mine can be built in a castle, city and hold; Rubyhold, Verkal Gulan and Anvilwright start with ruby, gold and silver; Delve Deeper shows level-N requirements greyed with tooltips; surface buildings in a dwarf-held mountain castle, not a human-held one; the three backgrounds and the icons load.
