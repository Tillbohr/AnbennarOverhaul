# Dwarovar Tribes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put 27 orc and goblin tribes on 215 of the 256 carved Serpentspine counties in 1022, under two tribal-style governments that ignore de jure, with dwarves down to six holds and the dwarven kingdoms whole as titles to reclaim.

**Architecture:** One data file (`tools/data/dwarovar_tribes.py`) says which tribe holds which EU4 area. The three region generators read it for each county's culture, faith, holding and holder; a new generator writes the governments, the pool of blank titles, tribe people and vanilla decision overrides. Decisions, the duel, wars and effects are hand-written script.

**Tech Stack:** CK3 1.19.0.6 script and localization, Python 3 generators (`tools/`, stdlib only), `unittest` through `tools/run_tests.py`, ck3-tiger through `tools/validate.py`.

**Spec:** `docs/superpowers/specs/2026-11-05-dwarovar-tribes-design.md`. Read it first: it holds the placement tables, the lore basis and the culture table, which this plan does not repeat.

## Global Constraints

- Base mod `../anbennar-ck3-dev-master` is never edited. New files take the `aov_` prefix; last-wins overrides `zz_aov_`.
- Script and localization files: UTF-8 with BOM, LF, tabs. English localization only, with the `l_english:` header.
- Files written by a `tools/build_*.py` script are never edited by hand: change `tools/data/` and rerun.
- Generators stop with `GeneratorError` (or `SystemExit`) on missing inputs rather than guessing.
- Identifiers come from local evidence (game, Anbennar, RiE). A tiger pass is not proof; each task says what stays for the in-game list.
- Run Python with `python -I`. Work on branch `dwarovar-tribes`, not `main`.
- Every value the spec calls a starting value lives in `tools/data/dwarovar_tribes.py`: `form_duchy` 3 counties and 250 prestige; `form_kingdom` 15 and 500; `form_empire` 40 and 1000; raise a vassal 200 prestige; refused-challenge opinion -50; duel cooldown 5 years; revival 500 prestige (revival lives in `holds.py`).
- Pool sizes: orc duchy 40, kingdom 20, empire 6; goblin duchy 40, kingdom 15, empire 4.

## Review Focus

Spec-implied conditions no feature test would otherwise reach. Each has its test in the owning task.

1. A pool title reaching a holder who is neither orc nor goblin (inheritance, a player's odd marriage) is destroyed and freed, not left showing a dwarf's dynasty. Task 5.
2. A reused pool title carries the last owner's capital and arms unless taking it resets both. Task 5.
3. A challenged ruler can die, be imprisoned or go to war before the challenge event resolves, and then no duel or refusal penalty should apply. Task 9.
4. An Anbennar update removing or renaming a tribe's area or a tribe's seat county must stop the generator, not silently drop counties. Task 7.
5. AI tribes reaching the surface through a vanilla war the surface rule does not cover (subjugation, invasion, county conquest). No static test can show this: Task 8 lists the candidates and in-game item 10 decides.

---

### Task 1: In-game naming and engine test

This is a throwaway spike that needs the user at the game. Its answers pick branches in Tasks 5 and 7, so nothing else starts until they are recorded.

**Files:**
- Create (on branch `spike/tribes-naming`, never merged): `common/landed_titles/aov_spike.txt`, `common/governments/aov_spike_government.txt`, `history/titles/aov_spike.txt`, `history/characters/aov_spike.txt`, `common/dynasties/aov_spike.txt`, `common/coat_of_arms/coat_of_arms/aov_spike.txt`, `common/landed_titles/zz_aov_spike_override.txt`, `common/on_action/aov_spike.txt`, `localization/english/aov_spike_l_english.yml`
- Modify: the spec, a new section "First test results"

**Interfaces:**
- Produces: the five answers below, in the spec. Task 5 reads answers 1-2 for the naming route; Task 7 reads answer 5 for Anbennar's titles.

- [ ] **Step 1: Branch and write the spike.** One blank `d_aov_warband_01` per the spec's field list, with `government_ignores_rightful_liege_penalties` on a copy of `tribal_government`, `dynasty_named_realms = yes`, one orc chief and one orc count vassal in `c_gor_vazumbrog` and `c_dwarovrod27` (use the keys in `aov_segbandal.txt`), a dynasty with arms, and `house_based_map_names = yes` on a copy of a name list. Loc: `d_aov_warband_01:0 "[GetTitleByKey('d_aov_warband_01').GetHolder.GetDynasty.GetName] Warband"`. `on_game_start` runs `title:d_aov_warband_01 = { set_coa = holder.dynasty set_capital_county = title:c_gor_vazumbrog }`. The override file holds `k_hehodovar = { can_create = { always = no } }`.
- [ ] **Step 2: Hand the user the checklist and wait.** They load the game and report:
  1. Does the title window show "<Dynasty> Warband"? On the map?
  2. Does the title carry the dynasty's arms? Does the script error log complain?
  3. Is the vassal's opinion, tax and levy free of the "not de jure liege" penalties?
  4. After console-forcing `de_jure_drift` progress on `d_vazumbrog`, does it stay out of the pool title?
  5. Does `k_hehodovar` keep its de jure counties with the override loaded (`database_conflicts.log`, de jure map mode), and is creation refused?
- [ ] **Step 3: Record the answers in the spec, delete the spike branch.** For each failed answer, write which fallback the spec names. If answer 5 fails, stop and ask the user the question the spec reserves for them before Task 7.

### Task 2: Remove ruined holds

**Files:**
- Delete: `events/aov_hold_ruin_events.txt`, `localization/english/aov_hold_ruin_l_english.yml`, `tools/tests/test_hold_ruin.py`
- Modify: `common/decisions/aov_hold_decisions.txt`, `common/on_action/aov_hold_on_actions.txt`, `common/on_action/aov_hold_dig_on_actions.txt`, `common/scripted_effects/aov_hold_effects.txt`, `common/scripted_triggers/aov_hold_triggers.txt`, `events/aov_hold_delve_events.txt`, `tools/build_holds.py`, `tools/data/holds.py`, `tools/data/holding_art.py`, `tools/build_monuments.py`, `tools/tests/test_build_holds.py`, `tools/tests/test_build_monuments.py`, `tools/tests/test_hold_data.py`, `tools/tests/test_hold_dig.py`, `docs/systems/dwarven-holds.md`, `docs/systems/segbandal.md`, `docs/systems/great-projects.md`, `CLAUDE.md`
- Regenerate: `common/modifiers/aov_hold_modifiers.txt`, `common/scripted_effects/aov_hold_setup_effects.txt`, `common/buildings/aov_dwarven_holds.txt`, `localization/english/aov_holds_l_english.yml`, `common/customizable_localization/aov_monument_illustration.txt`, `gui/window_county_view.gui`

**Interfaces:**
- Produces: `aov_hold_is_working` no longer exists; its three callers use `aov_is_hold = yes` (also `NOT = { has_province_modifier = ... }` goes with the modifier). `_hold(name, eu4_province, title, barony, start_level)` has no `ruined`.

- [ ] **Step 1: Write the failing test** in `tools/tests/test_hold_data.py`:

```python
RUIN_NAMES = ("aov_hold_ruined", "aov_hold_is_ruined", "aov_hold_is_working", "aov_clear_ruins_decision",
              "aov_hold_ruin", "aov_ruined_hold", "aov_restoring_hold", "aov_restore_pending",
              "aov_hold_begin_restoration_effect")

def test_no_ruin_names_left(self):
    # every .txt, .gui and .yml under common, events, gui, localization, and every .py in tools/ except this test
    self.assertEqual(files_naming(RUIN_NAMES), [])
```

- [ ] **Step 2: Run** `python -I tools/run_tests.py hold_data`. Expected: FAIL, listing the files above.
- [ ] **Step 3: Remove the mechanic from the hand-written script.** Delete `aov_clear_ruins_decision`, `aov_hold_on_title_gain`, `aov_hold_restoration_handover` (and their `on_actions` entries), `aov_hold_ruin_effect`, `aov_hold_begin_restoration_effect`, `aov_hold_is_ruined`, `aov_hold_is_working`. Fix the "ruined" comments in the delve picker. Keep `aov_hold_end_dig_effect` if anything else calls it; delete it if not.
- [ ] **Step 4: Remove it from the data and generators.** In `build_holds.py`: `IS_ENABLED` keeps only the dwarven-holder check; setup and the two modifiers and their loc go. In `holds.py`: `ruined`, `RUINED_MODIFIER`, `RUINED_ART`. In `holding_art.py`: the `ruined_hold` entry.
- [ ] **Step 5: Update the tests.** `test_hold_data.py:14-27` becomes `test_twenty_four_holds`; the ruin and restore assertions in `test_build_holds.py:43,64,225-254,347-364`, `test_hold_dig.py:105-106,154-159` and `test_build_monuments.py:853-858,878-884,903-906` are removed. `test_build_monuments.py:317` (`test_ruins_stage_untouched`) is about monuments and stays.
- [ ] **Step 6: Regenerate.** `python -I tools/build_holds.py`, then `python -I tools/build_monuments.py`, then `python -I tools/build_county_view_override.py`.
- [ ] **Step 7: Run** `python -I tools/run_tests.py hold monument county`. Expected: all pass, including `test_no_ruin_names_left`.
- [ ] **Step 8: Update the docs** listed above, including `CLAUDE.md`'s table row ("Delve Deeper digs" only).
- [ ] **Step 9: Run** `python -I tools/validate.py`. Expected: no new reports.
- [ ] **Step 10: Commit** with message `Remove the ruined holds mechanic`, staging the files above.

### Task 3: The tribe data

**Files:**
- Create: `tools/data/dwarovar_tribes.py`, `tools/tests/test_dwarovar_tribes.py`

**Interfaces:**
- Produces, in `tools/data/dwarovar_tribes.py`:
  - `Tribe = namedtuple("Tribe", "name race seat areas extra removed tag")`, with `race` `"orc"` or `"goblin"`, `seat` an EU4 province id, `tag` an EU4 tag or `None`.
  - `TRIBES: dict[str, Tribe]`, the 27 tribes from the spec's tables. Key is a slug (`masked_butcher`).
  - `DWARF_REALMS: dict[str, tuple]`, kingdom key -> EU4 areas the dwarves keep (`k_arg_ordstun: ()`, with `c_arg_ordstun` the hold county only).
  - `tribe_of(eu4_id: int, area: str) -> Tribe | None`.
  - `POOL = {"orc": {"duchy": 40, "kingdom": 20, "empire": 6}, "goblin": {"duchy": 40, "kingdom": 15, "empire": 4}}`.
  - `FORM = {"duchy": (3, 250), "kingdom": (15, 500), "empire": (40, 1000)}`; `RAISE_PRESTIGE = 200`; `REFUSAL_OPINION = -50`; `CHALLENGE_COOLDOWN_YEARS = 5`.
  - `CULTURE = {"orc": "black_orc", "goblin": "cave_goblin"}`; `FAITH = {"orc": "old_dookan", "goblin": "goblinic_shamanism"}`.
  - EU4 ids for the spec's single-county entries: Lavawater 4040, Bûrad Depths 4042, Molten Core 4041, Bûradforge 2949, hold 4093 removed from `arg_ordstun_area`.

- [ ] **Step 1: Write the failing tests** in `tools/tests/test_dwarovar_tribes.py`, reading `shared_trace.layouts()`:

```python
def test_totals(self):                      # orc 148, goblin 67 over all counties
def test_region_totals(self):               # serpentreach orc 38 goblin 24; west orc 97 goblin 25; segbandal orc 13 goblin 18
def test_tribe_counts(self):                # each tribe's county count equals the spec table, e.g. amldihr_orcs 18
def test_every_county_at_most_once(self):   # no county in two tribes; dwarves + kobolds + tribes == 256
def test_each_tribe_is_one_piece(self):     # adjacency from map_data/provinces.png and the two CROSSINGS
def test_segbandal_holds_connected(self):   # Seghdihr, Hehodovar, Verkal Gulan, Gor Ozumbrog in one piece of dwarven land
def test_no_tribe_on_anbennars_counties(self):  # no tribe county in segbandal.EXISTING or west_dwarovar.EXISTING
def test_seat_inside_tribe(self):           # tribe_of(t.seat, area) is t
def test_unknown_area_stops(self):          # every area in TRIBES exists in eu4i.province_areas(); else named in the failure
```

Adjacency: use `dwarven_mountains.load_province_map`; the scan in the scratch script took about a minute in pure Python, so cache it at class level.

- [ ] **Step 2: Run** `python -I tools/run_tests.py dwarovar_tribes`. Expected: FAIL, no module `data.dwarovar_tribes`.
- [ ] **Step 3: Write the data file** from the spec's tables. Copy the area keys exactly.
- [ ] **Step 4: Run the tests.** Expected: PASS.
- [ ] **Step 5: Commit** `Dwarovar tribes: the placement data`.

### Task 4: Placeholder cultures and faiths

**Files:**
- Create: `common/culture/pillars/aov_tribes_heritage.txt`, `common/culture/pillars/aov_tribes_language.txt`, `common/culture/cultures/aov_tribes_cultures.txt`, `common/culture/name_lists/aov_tribes.txt`, `history/cultures/heritage_orcish.txt`, `history/cultures/heritage_goblinoid.txt`, `common/religion/religion_family_types/aov_tribes.txt`, `common/religion/religion_types/aov_tribes_religions.txt`, `common/religion/holy_site_types/aov_tribes_holy_sites.txt`, `localization/english/aov_tribes_cultures_l_english.yml`, `tools/tests/test_dwarovar_tribes_cultures.py`

**Interfaces:**
- Produces: cultures `black_orc`, `cave_goblin`; heritages `heritage_orcish`, `heritage_goblinoid`; languages `language_orcish`, `language_goblin`; name lists `name_list_black_orc`, `name_list_cave_goblin`; family `rf_aov_serpentspine_tribes`, religions `aov_dookan_religion` and `aov_goblin_shamanism_religion`, faiths `old_dookan` and `goblinic_shamanism`.

- [ ] **Step 1: Write the failing tests:**

```python
def test_cultures_have_fields(self):      # heritage, language, ethos, martial_custom, traditions, name_list, *_gfx, ethnicities
def test_traditions_exist(self):          # every tradition key is defined in the game, Anbennar or the overhaul
def test_name_lists(self):                # house_based_map_names = yes; dynasty_names, male_names, female_names not empty
def test_collective_nouns(self):          # loc: black_orc_collective_noun "Orcs", cave_goblin_collective_noun "Goblins"
def test_every_pillar_and_faith_has_loc(self)
def test_holy_sites_are_tribe_counties(self):  # each site county exists in a layout and belongs to a tribe of that race
```

- [ ] **Step 2: Run** `python -I tools/run_tests.py dwarovar_tribes_cultures`. Expected: FAIL, files missing.
- [ ] **Step 3: Write the pillars and cultures.** Heritage blocks follow `heritage_kobold`, language blocks follow `language_serpentreach_dwarven`. Cultures follow `darkscale`: `ethnicities = { 10 = arab }` (human placeholder, as gnolls shipped), western `_gfx` keys, `martial_custom_equal`, `head_determination_domain`. Traditions: orc `tradition_mountain_homes`, `tradition_warrior_culture`, `tradition_ancient_miners`; goblin `tradition_mountain_homes`, `tradition_ancient_miners`, `tradition_stalwart_defenders`. `tradition_warrior_culture` is from memory, so test `test_traditions_exist` must pass or it gets replaced from what the file offers.
- [ ] **Step 4: Write the name lists.** Dynasty names from `eu4_import.culture_dynasty_names()` for `black_orc` and `cave_goblin`, committed as text. Male and female names from EU4's culture file. Add `house_based_map_names = yes`.
- [ ] **Step 5: Write `history/cultures`.** Copy `heritage_gnollish.txt`'s innovation list. The file name must match the heritage.
- [ ] **Step 6: Write the faiths** after `anb_harpy_hunts.txt`, in one new family, with doctrines kept vanilla-valid. Holy sites, 5 each: Old Dookan `c_hul_jorkad`, `c_amldihr`, `c_gor_burad`, `c_orlghelovar`, `c_mithradhum`; Goblinic Shamanism `c_shazstundihr`, `c_verkal_skomdihr`, `c_dur_vazhatun`, `c_weballey`, `c_old_coinvault` (check the keys in the generated titles).
- [ ] **Step 7: Run the tests.** Expected: PASS.
- [ ] **Step 8: Run** `python -I tools/validate.py`. Expected: new reports only for things no county uses yet; none about parsing.
- [ ] **Step 9: Commit** `Dwarovar tribes: placeholder orc and goblin cultures and faiths`.

### Task 5: Governments, pool titles and the sync effect

**Files:**
- Create: `tools/build_dwarovar_tribes.py`, `tools/tests/test_build_dwarovar_tribes.py`, `common/scripted_effects/aov_tribes_effects.txt`, `common/on_action/aov_tribes_on_actions.txt`
- Generated by this task: `common/governments/aov_dwarovar_governments.txt`, `common/landed_titles/aov_dwarovar_tribes.txt`, `common/scripted_effects/aov_tribes_pool_effects.txt`, `common/scripted_triggers/aov_tribes_pool_triggers.txt`, `common/script_values/aov_tribes_values.txt`, `common/decisions/zz_aov_dwarovar_tribes_overrides.txt`, `common/modifiers/aov_tribes_modifiers.txt`, `localization/english/aov_dwarovar_tribes_l_english.yml`

**Interfaces:**
- Consumes: `data.dwarovar_tribes` (Task 3); Task 1's naming answers.
- Produces:
  - `build_all(anbennar: Path = ANBENNAR) -> dict[str, bytes]`, `main() -> int`, `FreshnessTests`.
  - Governments `orcish_warband_government`, `goblin_chiefdom_government`; flags `government_is_dwarovar_tribe`, `government_is_orcish_warband`, `government_is_goblin_chiefdom`.
  - Pool keys `d_aov_warband_NN`, `k_aov_warband_NN`, `e_aov_warband_NN`, `d_aov_chiefdom_NN`, `k_aov_chiefdom_NN`, `e_aov_chiefdom_NN` (zero-padded from 01).
  - Scripted trigger `aov_tribe_has_free_title_trigger = { TIER = duchy }` and effect `aov_tribe_take_free_title_effect = { TIER = duchy }`, both run in the future holder's scope. They read that character's race trait and call a generated per-race, per-tier chain (`aov_tribe_free_orc_$TIER$_effect`). The effect saves `scope:aov_new_title` and sets its capital to the character's capital county; the caller transfers the title.
  - `aov_is_pool_title_trigger` (title scope, generated `OR` over the pool keys).
  - `aov_tribe_title_sync_effect` (title scope, reads `holder`).
  - Script values `aov_form_duchy_counties`, `aov_form_duchy_prestige`, and the same for kingdom and empire; `aov_raise_prestige`.
  - Modifier `aov_refused_challenge` with `general_opinion = -50`.

- [ ] **Step 1: Write the failing tests** in `tools/tests/test_build_dwarovar_tribes.py`:

```python
def test_governments_copy_tribal(self):
    # for both: primary_holding = tribal_holding, vassal_contract_group = tribal_vassal,
    # flags government_is_tribal, use_prestige_to_buy_maa, government_can_raid_rule
def test_governments_add_rules(self):
    # government_ignores_rightful_liege_penalties, sticky_government, use_as_base_on_landed, use_as_base_on_rank_up,
    # dynasty_named_realms = yes; can_get_government names race_orc / race_goblin only
def test_valid_holdings_include_holds(self):      # dwarven_hold_holding, elven_holding, as the source block has them
def test_pool_counts(self):                       # 40/20/6 and 40/15/4
def test_pool_fields(self):
    # every title: de_jure_drift_disabled, no_automatic_claims, ignore_titularity_for_title_weighting, definite_form,
    # can_create = { always = no }, a colour; no child title
def test_pool_colours_differ(self):               # no two pool titles share a colour
def test_overrides_copy_and_block(self):
    # 7 decision keys, each with the NOT government_has_flag = government_is_dwarovar_tribe line in is_shown
def test_missing_override_key_stops(self):        # GeneratorError naming the key when a decision is gone
def test_reused_title_resets_capital_and_arms(self):
    # Review Focus 2: the take effect calls set_capital_county; on_title_gain runs the sync on every pool title
def test_non_tribal_holder_destroys_title(self):  # Review Focus 1: on_action destroys a pool title when holder has neither race trait
def test_sync_guards_missing_dynasty(self):       # effect text: limit exists = holder.dynasty before set_coa
def test_gov_changes_on_title_gain(self):
    # holder with the race trait, and the title is a pool title or the holder's top liege has government_is_dwarovar_tribe:
    # race_orc gets orcish_warband_government, race_goblin goblin_chiefdom_government
class FreshnessTests: ...
```

- [ ] **Step 2: Run** `python -I tools/run_tests.py build_dwarovar_tribes`. Expected: FAIL, no module.
- [ ] **Step 3: Implement `render_governments(source: str) -> str`.** Find `tribal_government` in the overhaul's generated `common/governments/00_government_types.txt`, copy it twice under the new keys, add the rules, `can_get_government` and flags. Stop if the source block is missing. Run after `build_governments_override.py`.
- [ ] **Step 4: Implement `render_pool_titles() -> str`.** Top-level titles with the fields above. Hue spread over the pool at fixed saturation and value; give each a placeholder `capital` from a county in the Serpentreach layout, as `set_capital_county` overwrites it.
- [ ] **Step 5: Implement `render_pool_loc(route: str) -> str`.** From Task 1: route `"dynamic"` writes the `GetTitleByKey` name; route `"table"` writes the plain name and adds a per-dynasty `set_title_name` table in the sync effect. Words: Warband, Warhost, Horde; Chiefdom, High Chiefdom, Swarm.
- [ ] **Step 6: Implement `render_pool_effects() -> str`, `render_values() -> str`, `render_modifiers() -> str`.** The take effect is an if/else-if chain over the pool in order: first title with `NOT = { exists = holder }`.
- [ ] **Step 7: Implement `render_decision_overrides(anbennar: Path, game: Path) -> str`.** Find each of the spec's seven keys in Anbennar's `common/decisions/`, else the game's, adding the block line at the top of `is_shown`, following `build_race_relations.py`'s copy and stop.
- [ ] **Step 8: Write `aov_tribes_effects.txt` and `aov_tribes_on_actions.txt` by hand.** `on_title_gain` -> `aov_tribe_title_gain`, per the two tests above: on a pool title, destroy or sync; then the government change. `on_game_start` -> sync every held pool title and set its capital.
- [ ] **Step 9: Write and run the generator.** `python -I tools/build_dwarovar_tribes.py`.
- [ ] **Step 10: Run** `python -I tools/run_tests.py build_dwarovar_tribes`. Expected: PASS.
- [ ] **Step 11: Run** `python -I tools/validate.py`. Expected: no new parse errors; note anything about a key tiger does not know (`government_ignores_rightful_liege_penalties`).
- [ ] **Step 12: Commit** `Dwarovar tribes: governments, title pool and name and arms sync`.

### Task 6: Forming titles and raising vassals

**Files:**
- Create: `common/decisions/aov_tribes_decisions.txt`, `common/character_interactions/aov_tribes_interactions.txt`, `localization/english/aov_tribes_decisions_l_english.yml`, `tools/tests/test_dwarovar_tribes_script.py`

**Interfaces:**
- Consumes: `aov_tribe_has_free_title_trigger`, `aov_tribe_take_free_title_effect`, `aov_tribe_title_sync_effect`, script values (Task 5).
- Produces: decisions `aov_form_tribal_duchy_decision`, `aov_form_tribal_kingdom_decision`, `aov_form_tribal_empire_decision`; interaction `aov_raise_tribal_vassal_interaction`.

- [ ] **Step 1: Write the failing tests** in `tools/tests/test_dwarovar_tribes_script.py`, on the script text with `pdx_script.parse_blocks`:

```python
def test_form_decisions_tier_gates(self):    # duchy: highest_held_title_tier = tier_county; kingdom: tier_duchy; empire: tier_kingdom
def test_form_decisions_use_values(self):    # any_sub_realm_county count >= aov_form_<tier>_counties; cost prestige = aov_form_<tier>_prestige
def test_form_decisions_gate_on_government(self):   # is_shown has government_is_dwarovar_tribe
def test_form_decisions_need_a_free_title(self):    # is_valid has aov_tribe_has_free_title_trigger with a tooltip
def test_raise_tier_rules(self):
    # recipient tier at least two below actor; recipient is_vassal of actor; recipient government_is_dwarovar_tribe
    # grants one tier below actor: king gives duchy, emperor gives kingdom
def test_duke_cannot_raise(self):            # is_shown needs actor highest_held_title_tier >= tier_kingdom
def test_loc_complete(self):                 # title, desc, tooltip, confirm keys each exist
```

- [ ] **Step 2: Run** `python -I tools/run_tests.py dwarovar_tribes_script`. Expected: FAIL.
- [ ] **Step 3: Write the three decisions.** `is_shown` tier and government; `is_valid` county count and free title; `effect`: `aov_tribe_take_free_title_effect`, then `create_title_and_vassal_change = { type = created ... }`, `change_title_holder`, `resolve_title_and_vassal_change`. AI: `ai_check_interval` 60 months, `ai_will_do` scaling with prestige margin, so Amldihr and Orldhûm do not both go in the first year.
- [ ] **Step 4: Write the interaction,** following a vanilla vassal interaction in `00_vassal_interactions.txt`. `auto_accept = yes`, cost `aov_raise_prestige`. The take effect runs in `scope:recipient`, with `TIER` one below the actor's.
- [ ] **Step 5: Run the tests and** `python -I tools/validate.py`. Expected: PASS; no new reports.
- [ ] **Step 6: Commit** `Dwarovar tribes: decisions to form titles and raising a vassal`.

### Task 7: Tribes on the map, and dwarven rulers

**Files:**
- Modify: `tools/build_serpentreach.py`, `tools/build_west_dwarovar.py`, `tools/build_segbandal.py`, `tools/data/serpentreach.py`, `tools/data/west_dwarovar.py`, `tools/data/segbandal.py`, `tools/build_dwarovar_tribes.py`, `tools/tests/test_serpentreach.py`, `tools/tests/test_west_dwarovar.py`, `tools/tests/test_segbandal.py`, `tools/tests/test_build_dwarovar_tribes.py`
- Regenerate: each region's history, titles, characters and dynasties
- Generated by this task: `history/titles/aov_dwarovar_tribes.txt`, `history/characters/aov_dwarovar_tribes.txt`, `common/dynasties/aov_dwarovar_tribes.txt`, `common/coat_of_arms/coat_of_arms/aov_dwarovar_tribes.txt`
- Imported once: `gfx/coat_of_arms/textured_emblems/aov_tribe_<slug>.dds` for H81, H87, M05, H86, H90, H75, H85, H89, H73, H82, with `python -I tools/eu4_import.py convert gfx/flags/<tag>.tga <dds> --upscale2x --mips`

**Interfaces:**
- Consumes: `tribe_of`, `TRIBES`, `DWARF_REALMS` (Task 3); pool keys (Task 5); cultures and faiths (Task 4).
- Produces:
  - `build_serpentreach.county_people(county, culture: str, religion: str, holdings: list) -> tuple[str, str, list]`: the given values for a dwarven county; the tribe's culture, faith and holdings for a tribe county. All three builders call it, as Segbandal has no `Realm`.
  - `build_dwarovar_tribes.check_tribes(lays) -> None`: raises `GeneratorError` naming any tribe area with no county, or a seat in no layout.
  - `People` has lines only for dwarven duchies; `render_title_history` writes nothing for tribe counties.
  - `build_dwarovar_tribes.TribePeople`: `{tribe_slug: {"pool_title", "dynasty", "chief", "sub_chiefs": {area: id}}}`.
  - Character ids `aov_tr_<slug>_chief_1`, `_2`, `aov_tr_<slug>_<area>_1`, `_2`; dynasties `aov_tr_dynasty_<slug>`, arms key equal to the dynasty key.

- [ ] **Step 1: Write the failing tests:**

```python
# test_build_dwarovar_tribes.py
def test_tribe_counties_take_tribe_people(self):
    # in province history: Bloodied Altar culture black_orc, religion old_dookan, first barony tribal_holding, others none
def test_hold_barony_stays_castle_in_history(self):  # aov_hold_setup_effect converts it; culture is the tribe's
def test_chief_holds_pool_title_and_seat(self):      # pool title holder = chief; government = orcish_warband_government
def test_sub_chiefs_are_vassals(self):               # each other area's counties: holder sub-chief, liege = pool title
def test_no_tribe_holds_a_dwarven_title(self):       # no d_/k_/e_ from the regions in tribe title history
def test_ten_dynasties_have_flags(self):             # Masked Butcher arms texture aov_tribe_masked_butcher.dds, and 9 more
def test_race_traits(self):                          # every orc tribe character race_orc; goblin race_goblin
def test_missing_area_stops(self):                   # Review Focus 4: check_tribes raises on a layout lacking a tribe's area or seat
# test_west_dwarovar.py
def test_no_dwarven_rulers(self):       # no aov_wd_* character; e_west_dwarovar, all kingdoms and duchies have no holder
def test_de_jure_moves_stay(self):      # k_khugdihr etc still move by history
# test_serpentreach.py
def test_only_two_dwarven_kingdoms(self):
    # holders only on k_arg_ordstun (with d_arg_ordstun, c_arg_ordstun) and k_ovdal_lodhum (with d_ovdal_lodhum and its 4 counties)
    # neither has a liege; e_serpentreach has no holder
# test_segbandal.py
def test_elders_left(self):             # only d_steamsource keeps an elder among the new duchies
def test_new_kings(self):               # k_hehodovar and k_gor_ozumbrog have holders, cultures pyrite and topaz, liege e_middle_dwarovar from 921.9.24
def test_dwarven_counties_all_held(self):   # every county of DWARF_REALMS has a holder in Anbennar's or our history
# each region's titles file
def test_generated_titles_refuse_tribes(self):   # can_create NOT government_is_dwarovar_tribe on every d_/k_/e_
def test_generated_kingdoms_no_drift(self):      # de_jure_drift_disabled = yes on every k_/e_
```

Replace the now wrong assertions at `test_west_dwarovar.py:285-300,350`, `test_serpentreach.py:547-552,582` and `test_segbandal.py:302-313`.

- [ ] **Step 2: Run** `python -I tools/run_tests.py serpentreach west_dwarovar segbandal build_dwarovar_tribes`. Expected: FAIL on the new tests.
- [ ] **Step 3: Implement `county_people` and use it in all three province histories.** Tribe county: the tribe's culture and faith; first barony `tribal_holding`, unless the county is a hold (`county.eu4_id` in `holds.HOLDS`), whose first barony stays `castle_holding` for `aov_hold_setup_effect` to convert; other baronies `none`. West's `KOBOLD_KINGDOMS` check stays first.
- [ ] **Step 4: Change the rulers.**
  - `People`: drop duchies with no dwarven county. West ends with none.
  - `render_title_history`: empire block only when the region has an emperor; a living kingdom's king holds his kingdom, hold duchy and dwarven counties, with no liege. `cfg.LIVING_KINGDOMS`: Serpentreach `("k_arg_ordstun", "k_ovdal_lodhum")`, West `()`.
  - Serpentreach keeps the `aov_sr_emperor_*` ids for Arg-Ôrdstun's line, now a king's.
  - `EMPIRE_CAPITAL` stays as the empire title's capital; nothing may read `people.lines[realm.emperor_duchy]` without checking it exists.
- [ ] **Step 5: Add Segbandal's kings.** `KING_LINES` in `tools/data/segbandal.py`: `k_hehodovar` (`pyrite_dwarvish`), `k_gor_ozumbrog` (`topaz_dwarvish`, dynasty name "az-Fiobmhor"). Write `holder` for each dwarven county with none in Anbennar's history (reuse `title_holder`), and `921.9.24 = { liege = e_middle_dwarovar }` on the kingdoms. Drop `check` paths that assumed these kingdoms have no holder.
- [ ] **Step 6: Add `can_create` and drift to `_duchy_title_lines` and the kingdom and empire lines** in `build_serpentreach.py` and `build_segbandal.py`. For Anbennar's own titles, do what Task 1's answer 5 chose.
- [ ] **Step 7: Implement tribe people in `build_dwarovar_tribes.py`:** `check_tribes`, `TribePeople`, `render_dynasties`, `render_characters`, `render_title_history`, `render_arms`. Assign pool titles in `TRIBES` order per race. Chief holds the pool duchy and the seat's county; each other area's counties go to its sub-chief, `liege = <pool title>`, in line with `aov_sb_*`. Holder dates as the region's `START`, deaths and sons as `ELDER_DEATH`. `government = <gov>` on the title entries, RiE's pattern. `culture_of` a character: `CULTURE[race]`.
- [ ] **Step 8: Convert the ten flags** with the command above.
- [ ] **Step 9: Regenerate in the documented order:** `build_serpentreach.py`, `build_segbandal.py`, `build_west_dwarovar.py`, `build_dwarovar_tribes.py`, then whatever `docs/systems/updating.md` lists after those.
- [ ] **Step 10: Run** `python -I tools/run_tests.py`. Expected: all pass. Fix any `FreshnessTests` by rerunning the listed generator.
- [ ] **Step 11: Run** `python -I tools/validate.py`. Expected: no new reports. Read each one; do not baseline.
- [ ] **Step 12: Commit** `Dwarovar tribes: tribes on the map, dwarven rulers cut back to the lore`.

### Task 8: Wars and the AI surface rule

**Files:**
- Modify: `common/casus_belli_types/aov_race_relations_wars.txt`, `tools/tests/test_build_race_relations.py`, `docs/systems/race-relations.md`
- Create: `common/scripted_triggers/aov_tribes_triggers.txt`, localization lines in `localization/english/aov_tribes_decisions_l_english.yml`

**Interfaces:**
- Produces: `aov_tribal_war_cb`; trigger `aov_title_in_serpentspine_trigger` (title scope); `aov_ai_tribe_may_not_target_trigger` (scope:attacker, scope:target).

- [ ] **Step 1: Write the failing tests:**

```python
def test_tribal_war_both_sides_tribes(self):
    # allowed_for_character government_is_dwarovar_tribe; allowed_against_character defender government_is_dwarovar_tribe
def test_tribal_war_neighbouring_county(self):    # target_title_tier = county; valid_to_start is_neighbor_to_realm = scope:attacker
def test_monster_conquest_keeps_non_monstrous_target(self):   # unchanged
def test_ai_surface_rule_on_both_wars(self):      # both CBs' valid_to_start call aov_ai_tribe_may_not_target_trigger
def test_surface_rule_regions(self):              # world_serpentreach, world_west_dwarovar, world_segbandal
def test_surface_rule_is_ai_only(self):           # the trigger text limits on is_ai = yes
```

- [ ] **Step 2: Run** `python -I tools/run_tests.py race_relations`. Expected: FAIL.
- [ ] **Step 3: Write `aov_tribal_war_cb`** by copying `aov_monster_conquest_cb`, swapping both character gates. Same prestige cost. Add its loc.
- [ ] **Step 4: Write the two triggers and add the surface rule** to `aov_monster_conquest_cb`'s and the new war's `valid_to_start`.
- [ ] **Step 5: Run the tests.** Expected: PASS.
- [ ] **Step 6: List other wars a tribal AI can use.** Read `allowed_for_character` in `county_conquest_cb` (Anbennar's `00_conquest.txt`), `00_subjugation.txt`, `00_vassalization.txt`, `00_invasion_war.txt`, `01_fp1_wars.txt`, `07_ep3_wars.txt`. Write the findings in `docs/systems/dwarovar-tribes.md`. Do not override any now: the in-game observer run (Task 11, item 10) decides, and a follow-up adds a generated override only if tribes reach the surface that way.
- [ ] **Step 7: Commit** `Dwarovar tribes: tribal wars and no early AI surface conquest`.

### Task 9: Duels

**Files:**
- Create: `events/aov_tribes_duel_events.txt`, `localization/english/aov_tribes_duel_l_english.yml`
- Modify: `common/decisions/aov_tribes_decisions.txt`, `common/scripted_effects/aov_tribes_effects.txt`, `tools/tests/test_dwarovar_tribes_script.py`

**Interfaces:**
- Consumes: `aov_refused_challenge`, `aov_tribe_title_sync_effect` (Task 5).
- Produces: `aov_challenge_warlord_decision`; events `aov_tribe_duel.1` (received), `.2` (outcome), `.3` (invalidated); `aov_tribe_duel_winner_takes_all_effect`.

- [ ] **Step 1: Write the failing tests:**

```python
def test_challenger_must_be_orc(self):        # is_shown has has_trait = race_orc on root; a goblin fails
def test_liege_must_be_top_warband(self):     # liege is independent, government_is_orcish_warband
def test_limits(self):                        # adult, not imprisoned, not at war on either side, cooldown years = 5
def test_accept_uses_vanilla_combat(self):
    # configure_start_single_combat_effect with FATALITY = no, OUTPUT_EVENT = aov_tribe_duel.2, INVALIDATION_EVENT = aov_tribe_duel.3
def test_refuse_penalties(self):              # add_prestige_level = -5; add_character_modifier aov_refused_challenge with no duration
def test_event_revalidates(self):             # Review Focus 3: .1 trigger checks ruler alive, not imprisoned, not at war, still liege
def test_outcome_order(self):
    # in .2: winner_takes_all effect before the death effect; death_reason = death_duel; sync runs after the transfer
def test_ruler_win_kills_challenger(self)
def test_vanilla_challenge_blocked(self):     # the override blocks tribal_challenge_ruler_decision (Task 5's file)
def test_no_goblin_ruler_can_be_challenged(self)  # liege government check rejects government_is_goblin_chiefdom
```

- [ ] **Step 2: Run** `python -I tools/run_tests.py dwarovar_tribes_script`. Expected: FAIL.
- [ ] **Step 3: Write the decision,** following `tribal_challenge_ruler_decision`, without the claim requirement, and without its champion path. AI: `ai_potential` adult and `has_trait = ambitious`, or prowess above the ruler's by 6; `ai_will_do` scales with prowess gap; 0 when weaker.
- [ ] **Step 4: Write `aov_tribe_duel.1`.** Trigger per the test. Option accept per the test, `ai_chance` high. Option refuse with the two penalties; `ai_chance` low unless the ruler's prowess is far lower. Both options tell the challenger.
- [ ] **Step 5: Write `aov_tribe_duel_winner_takes_all_effect`.** `create_title_and_vassal_change = { type = usurped add_claim_on_loss = no }`, `every_held_title` of the loser to the winner, resolve; then every vassal follows the winner's realm. Vanilla's `tribal_transfer_liege_title_effect` is the base, for all titles rather than the primary.
- [ ] **Step 6: Write `aov_tribe_duel.2` and `.3`.** `.2` reads `scope:sc_victor` (vanilla's name, `tribal_events.txt:1058`) and the other as loser. Challenger won: take all, then `death = { death_reason = death_duel killer = scope:sc_victor }`. Ruler won: challenger dies the same way. `.3` is a toast only: no effects.
- [ ] **Step 7: Run the tests and** `python -I tools/validate.py`. Expected: PASS; no new reports.
- [ ] **Step 8: Commit** `Dwarovar tribes: orc duels for the throne`.

### Task 10: Culture revival

**Files:**
- Modify: `tools/data/holds.py`, `tools/build_holds.py`, `tools/tests/test_build_holds.py`, `tools/tests/test_hold_data.py`
- Generated by `build_holds.py`: `common/decisions/aov_hold_revival_decisions.txt`, `localization/english/aov_hold_revival_l_english.yml`
- Modify generated: `common/script_values/aov_hold_values.txt` (`aov_revival_prestige = 500`)

**Interfaces:**
- Consumes: `aov_is_hold` (existing); the table in the spec.
- Produces: `_hold(name, eu4_province, title, barony, start_level, culture=None, kingdom=None)`; one decision per hold with a culture, `aov_revive_<title without c_>_decision`. A ruler with exactly one hold sees at most one, so no picker is needed.

- [ ] **Step 1: Write the failing tests:**

```python
def test_twenty_holds_have_cultures(self):     # the spec's 20; Marrhold, Anvilwright, Ovdal Tûngr, Rubyhold have None
def test_cultures_exist(self):                 # each key in the culture files
def test_kingdoms_exist(self)
def test_one_decision_per_hold(self):          # 20 decisions
def test_requires_only_one_hold(self):
    # is_shown has any_held_title = { count = 1 tier = tier_barony title_province = { aov_is_hold = yes } } and has_title of this hold's barony
def test_requires_dwarf_and_unformed(self):    # is_dwarvish_culture; title:<kingdom> NOT exists = holder; culture != hold's
def test_no_prompt_on_creation(self):          # no on_title_gain or flag:created mention of revival anywhere
def test_effect_converts_family_and_county(self):
    # set_culture on root, every_spouse, every_child; hold county set_county_culture; nothing on other counties
def test_ai_only_at_capital(self):             # ai_potential: capital_province = the hold's province
```

- [ ] **Step 2: Run** `python -I tools/run_tests.py hold`. Expected: FAIL on the new tests.
- [ ] **Step 3: Add `culture` and `kingdom` to `_hold`** for the 20 holds, from the spec's table and the kingdom keys `k_<slug>` in the region data.
- [ ] **Step 4: Implement `render_revival_decisions() -> str` and `render_revival_loc() -> str`** in `build_holds.py`.
- [ ] **Step 5: Regenerate** with `python -I tools/build_holds.py`.
- [ ] **Step 6: Run the tests and** `python -I tools/validate.py`. Expected: PASS; no new reports.
- [ ] **Step 7: Commit** `Dwarven holds: reviving a lost hold's culture`.

### Task 11: Docs and the full in-game list

**Files:**
- Create: `docs/systems/dwarovar-tribes.md`
- Modify: `CLAUDE.md`, `docs/systems/updating.md`, `docs/systems/serpentreach.md`, `docs/systems/segbandal.md`, `docs/systems/west-dwarovar.md`, `docs/systems/dwarven-holds.md`, `docs/systems/race-relations.md`, `docs/systems/validation-baseline.md` if any report is accepted

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Write `docs/systems/dwarovar-tribes.md`** in the shape of `west-dwarovar.md`: generated-files table, system notes, Task 1's answers, the spec's in-game list as "Needs an in-game test".
- [ ] **Step 2: Update the other docs.** `CLAUDE.md` gets a systems row and a generator-order note; `updating.md` gets `build_dwarovar_tribes.py` after `build_governments_override.py` and `build_west_dwarovar.py`, before `build_holds.py`, and the CK3-patch rerun line. The three region docs lose "elders" and "emperor" where they no longer apply.
- [ ] **Step 3: Run everything.** `python -I tools/run_tests.py` and `python -I tools/validate.py --all`. Expected: all pass; any new report read and either fixed or, if inherited, recorded before `--baseline`.
- [ ] **Step 4: Commit** `Dwarovar tribes: system docs`.
- [ ] **Step 5: Hand the user the spec's in-game list and wait.** Items 1-10 under Testing. Fix what they report; a fix that fails once goes to the most capable model under the project's rule. Add a Review Focus 5 override only if item 10 shows it.
