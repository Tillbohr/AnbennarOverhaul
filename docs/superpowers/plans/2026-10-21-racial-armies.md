# Racial Armies Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give elves, dwarves, gnomes and kobolds their own levy, MAA and domain-limit identity while an equal realm of
any race stays about as strong as a human one for the whole game.

**Architecture:** Hand-written single-object overrides (heritages, two traditions, 15 Anbennar MAA types) plus new
`aov_` MAA files gated by culture-lineage triggers. A Python generator (`tools/build_racial_levies.py`) reads every
`levy_size` source in the game, Anbennar and the overhaul and writes a per-holding script value, tiered correction
modifiers and a refresh effect; on_actions keep each racial holding's levy share fixed.

**Tech Stack:** CK3 1.19.0.6 script and localization; Python 3 (`python -I`), `unittest`; ck3-tiger via
`tools/validate.py`.

**Spec:** `docs/superpowers/specs/2026-10-21-racial-armies-design.md` (read it first; its tables are the source of
every number below).

## Global Constraints

- Never write to `../anbennar-ck3-dev-master`; all files go in this submod.
- Script and loc files: UTF-8 with BOM, LF line endings, tabs; loc files start with `l_english:`.
- New files use the `aov_` prefix; single-object overrides use `zz_aov_`; new keys are prefixed `aov_` (retuned
  Anbennar units keep their keys).
- Files written by `tools/build_*.py` are never edited by hand; the generator's data lives in `tools/data/`.
- File-local `@variables` used in a new file are redefined at the top of that file.
- Hook vanilla on_actions only by appending `on_actions = { aov_... }`.
- Run Python as `python -I`; run one test module with
  `python -I -m unittest discover -s tools/tests -p "test_<name>*.py"`.
- Validation: `python -I tools/validate.py` must report nothing new; baseline only reports inherited verbatim from
  Anbennar, recorded in `docs/systems/validation-baseline.md`.
- Commit after each task with a short imperative subject (repo style: `Racial armies: <what>`).

## Review Focus

1. **A county changes hands**: every barony of that county is refreshed, not just the capital. Pinned in Task 7
   (`test_title_gain_refreshes_every_county_province`).
2. **An owner stops being racial** (culture conversion, a human inherits): the old tier is removed and no new one is
   added. Pinned in Task 6 (`test_refresh_removes_before_adding_and_skips_non_racial`).
3. **A holding's bonus is outside the tier range**: it gets the end tier, never no modifier. Pinned in Task 6
   (`test_bonus_beyond_range_clamps_to_end_tier`).
4. **Wood elves descend from moon elves; hybrids have two parents**: wood elves never see moon units, sun lineage
   wins over moon. Pinned in Task 1 (`test_moon_trigger_excludes_wood_and_sun_lineage`).
5. **Negative levy sources** (governments, laws): the correction is positive, so an elf holding stays at
   0.25 × (1 + S), never zero. Pinned in Task 6 (`test_negative_bonus_gets_positive_correction`).

---

### Task 1: Heritages and lineage triggers

**Files:**
- Create: `common/culture/pillars/zz_aov_racial_heritages.txt`
- Create: `common/scripted_triggers/aov_racial_maa_triggers.txt`
- Test: `tools/tests/test_racial_armies.py`

**Interfaces:**
- Produces: heritage parameters `aov_racial_levy_elven`, `aov_racial_levy_dwarven`, `aov_racial_levy_gnomish`,
  `aov_racial_levy_kobold` (culture parameters, `= yes`).
- Produces (culture scope triggers): `aov_sun_elven_lineage_trigger`, `aov_wood_elven_lineage_trigger`,
  `aov_moon_elven_lineage_trigger`, and `aov_<clan>_dwarven_lineage_trigger` for clan in
  `ruby silver stone agate copper citrine gold pyrite titanium topaz marble`.
- Produces (test helpers in `test_racial_armies.py`, reused by later tasks): `SUBMOD`, `ANBENNAR`, `blocks(rel) ->
  dict` (wraps `pdx_script.parse_blocks` on a submod file), `base_blocks(rel) -> dict` (same on Anbennar),
  `field(body, key) -> str | None` (first `key = value` at depth 0 of a block body).

- [ ] **Step 1: Write the failing tests** in `tools/tests/test_racial_armies.py`, class `HeritageTests`:

```python
HERITAGES = {  # levy_size, levy_attack/levy_toughness, domain_limit, parameter
    "heritage_elven": ("-0.75", "30", "-1", "aov_racial_levy_elven"),
    "heritage_dwarven": ("-0.40", "7", "-2", "aov_racial_levy_dwarven"),
    "heritage_gnomish": ("-0.50", "10", "-1", "aov_racial_levy_gnomish"),
    "heritage_kobold": ("0.50", "-3", None, "aov_racial_levy_kobold"),
}

def test_heritages_carry_spec_values(self): ...      # each value above in character_modifier / parameters
def test_overrides_keep_anbennar_fields(self): ...   # type, is_shown, audio_parameter equal Anbennar's anb_heritage.txt
```

and class `LineageTriggerTests`:

```python
def test_every_lineage_trigger_exists(self): ...    # 3 elven + 11 dwarven names, exactly
def test_lineage_triggers_check_self_and_ancestors(self):
    # each body contains `this = culture:<root>` and `any_parent_culture_or_above = { this = culture:<root> }`
def test_moon_trigger_excludes_wood_and_sun_lineage(self):
    # aov_moon_elven_lineage_trigger body: has_cultural_pillar = heritage_elven,
    # aov_sun_elven_lineage_trigger = no, aov_wood_elven_lineage_trigger = no
```

- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p "test_racial_armies*.py"`. Expected: FAIL
  (files missing).
- [ ] **Step 3: Write the two script files.** Heritages: copy Anbennar's four blocks verbatim, add
  `parameters = { <param> = yes }` and a `character_modifier` with `levy_size`, `levy_attack`, `levy_toughness`
  and (not for kobolds) `domain_limit` from the table. Triggers: one block per name; sun/wood/clan roots are
  `sun_elvish`, `wood_elvish`, `<clan>_dwarvish`.
- [ ] **Step 4: Run the tests.** Expected: PASS.
- [ ] **Step 5: Commit** `Racial armies: heritage modifiers and lineage triggers`.

---

### Task 2: Remove Sundancer Legions and Dwarven Handgunners traditions

**Files:**
- Create: `common/culture/traditions/zz_aov_racial_traditions.txt`
- Create: `common/on_action/aov_racial_armies_on_actions.txt`
- Test: `tools/tests/test_racial_armies.py` (class `TraditionRemovalTests`)

**Interfaces:**
- Produces: on_action `aov_racial_armies_game_start` appended to `on_game_start` in
  `aov_racial_armies_on_actions.txt` (Task 7 adds the levy refresh to the same on_action's effect).

- [ ] **Step 1: Write the failing tests:**

```python
REMOVED = ("tradition_sundancer_legions", "tradition_test_maa_anb_dwarven_handgunners")

def test_removed_traditions_hidden_and_unpickable(self):
    # each override: is_shown = { always = no } and can_pick = { always = no }
def test_overrides_match_anbennar_elsewhere(self):
    # body with is_shown/can_pick blocks removed equals Anbennar's (anb_maa_traditions.txt) with the same removed
def test_game_start_removes_both(self):
    # aov_racial_armies_game_start effect: every_culture_global with limit has_cultural_tradition = X
    # and remove_culture_tradition = X, for both X; on_game_start appends aov_racial_armies_game_start
```

- [ ] **Step 2: Run the tests.** Expected: FAIL.
- [ ] **Step 3: Write the files**, following `aov_gnomish_ingenuity_game_start` in
  `common/on_action/aov_artificer_on_actions.txt` for the on_action shape.
- [ ] **Step 4: Run the tests.** Expected: PASS.
- [ ] **Step 5: Commit** `Racial armies: remove Sundancer Legions and Dwarven Handgunners traditions`.

---

### Task 3: Unit cost script values

**Files:**
- Create: `common/script_values/aov_racial_maa_values.txt`
- Test: `tools/tests/test_racial_armies.py` (class `PricingTests`)

**Interfaces:**
- Produces: for every unit key K in the spec's roster tables (14 retuned + 18 new):
  `aov_<K-without-aov_>_recruitment_cost`, `..._low_maint_cost`, `..._high_maint_cost` — e.g.
  `aov_staochri_recruitment_cost`, `aov_elven_knights_recruitment_cost`. Tasks 4–5 use these in `buy_cost` /
  `low_maintenance_cost` / `high_maintenance_cost`.
- Values are plain numbers from the spec's Buy and Upkeep columns; high = 3 × low. Silverforge Engineer Corps:
  `@[dwarven_bombards_recruitment_cost * 1.3]`-style references to Anbennar's `dwarven_bombards_*` values
  (`dwarven_bombard_low_maint_cost`, `dwarven_bombard_high_maint_cost` — note Anbennar's singular `bombard`).

- [ ] **Step 1: Write the failing tests:**

```python
VANILLA = {  # regiment damage, regiment toughness, buy, low upkeep (spec, Pricing)
    "skirmishers": (1000, 1600, 45, 0.15), "archers": (2500, 1000, 55, 0.2), "crossbow": (4200, 1800, 88, 0.3),
    "pikemen": (2200, 2400, 75, 0.3), "heavy_infantry": (3200, 2200, 90, 0.4),
    "light_cavalry": (2200, 1500, 85, 0.35), "heavy_cavalry": (5000, 1750, 200, 0.7),
}
# ROSTER: key -> (role, men, damage, toughness) for all 31 non-siege units, copied from the spec tables;
# role "crossbow" for armor_breakers, aov_giantbane_crossbows, aov_clockwork_bows.

def test_every_unit_priced_at_vanilla_power_per_gold(self):
    # factor = sqrt(men*dmg/vd * men*tough/vt); buy within 5% of vb*factor, low upkeep within 5% of vu*factor,
    # high upkeep == 3 * low upkeep
def test_engineer_corps_costs_scale_bombards(self): ...  # 1.3 × Anbennar's dwarven_bombard* values
```

- [ ] **Step 2: Run the tests.** Expected: FAIL.
- [ ] **Step 3: Write the values file** from the spec's Buy / Upkeep columns.
- [ ] **Step 4: Run the tests.** Expected: PASS.
- [ ] **Step 5: Commit** `Racial armies: unit cost values`.

---

### Task 4: Elven MAA (moon, sun, wood)

**Files:**
- Create: `common/men_at_arms_types/zz_aov_racial_maa_overrides.txt` (elven part: `aithchri`, `sheahrna`,
  `staochri`, `marcairna`, `sundancer_legions`, `jaherkadezim`, `ayethi`, `felwyr`, `glaifes`, `hyodeth`)
- Create: `common/men_at_arms_types/aov_elven_maa_types.txt` (`aov_elven_knights`, `aov_gladeguards`,
  `aov_sunspear_phalanx`, `aov_phoenix_bowmen`, `aov_sandwind_outriders`, `aov_duneblades`,
  `aov_greatoak_wardens`)
- Create: `localization/english/aov_racial_armies_l_english.yml`
- Test: `tools/tests/test_racial_armies.py` (class `MaaTests`, shared with Task 5)

**Interfaces:**
- Consumes: Task 1 lineage triggers; Task 3 cost values.
- Produces: `MaaTests` helpers `EXPECTED` (key -> type, stack, damage, toughness, pursuit, screen, gate) and
  `TERRAIN_SETS`, extended by Task 5.

- [ ] **Step 1: Write the failing tests:**

```python
# EXPECTED rows copied from the spec's Moon/Sun/Wood tables, e.g.
#   "staochri": ("heavy_infantry", 25, 300, 200, 10, 10, "aov_moon_elven_lineage_trigger"),
#   "aov_elven_knights": ("heavy_cavalry", 25, 450, 160, 40, 0, "aov_moon_elven_lineage_trigger"),
def test_units_have_spec_stats(self): ...            # type, stack, damage, toughness, pursuit, screen
def test_units_gated_by_their_lineage(self): ...     # can_recruit = { culture = { <gate> = yes } }, nothing else
def test_units_use_their_cost_values(self): ...      # buy/low/high reference aov_<k>_* from Task 3
def test_retuned_units_keep_unchanged_fields(self):
    # every field except stack, damage, toughness, pursuit, screen, terrain_bonus, can_recruit, buy_cost,
    # low_maintenance_cost, high_maintenance_cost, ai_quality equals Anbennar's block (type, icon, counters, ...)
def test_terrain_bonuses_follow_spec_percentages(self):
    # each listed terrain has damage == round(base_damage * pct) and toughness == round(base_toughness * pct)
    # moon: aithchri/aov_gladeguards +0.20 forest hills taiga, aov_gladeguards forest +0.50 total;
    # sun: +0.20 desert drylands floodplains plains, -0.20 jungle forest normal_winter harsh_winter (all six);
    # wood: +0.50 forest taiga jungle wetlands, -0.20 desert drylands plains (all five)
def test_every_unit_has_name_and_flavor(self): ...   # <key> and <key>_flavor in aov_racial_armies_l_english.yml
def test_ai_quality_uses_cultural_extra_score(self): ...  # ai_quality = { value = @cultural_maa_extra_ai_score }
```

- [ ] **Step 2: Run the tests.** Expected: FAIL.
- [ ] **Step 3: Write the overrides** by copying each Anbennar block (`anb_cultural_maa_generics.txt`,
  `anb_cultural_maa_types.txt`), then replacing stack, stats, pursuit/screen, `terrain_bonus`, `can_recruit` and
  costs. Define `@cultural_maa_extra_ai_score` (copy Anbennar's value) and the `@provisions_cost_*` variables the
  blocks use at the top of each file. Drop Hyodeth's duplicate `hills` entry.
- [ ] **Step 4: Write the new elven units** in the same shape; icons from the vanilla unit of the role
  (`bowmen`, `pikemen`, `heavy_infantry`, `light_cavalry`, `heavy_cavalry`, `skirmishers`).
- [ ] **Step 5: Write loc** for all 17 elven units: names from the spec; flavor one or two sentences of lore,
  `#F ... #!` as Anbennar does. Retuned units' flavor replaces Anbennar's placeholder text (later loc key wins).
- [ ] **Step 6: Run the tests.** Expected: PASS.
- [ ] **Step 7: Commit** `Racial armies: moon, sun and wood elf MAA`.

---

### Task 5: Dwarven MAA (shared, clan signatures, Handgunners disabled)

**Files:**
- Modify: `common/men_at_arms_types/zz_aov_racial_maa_overrides.txt` (add `dwarven_guardians`, `shieldwall`,
  `armor_breakers`, `ramriders`, and `dwarven_handgunners` with `can_recruit = { always = no }`)
- Create: `common/men_at_arms_types/aov_dwarven_maa_types.txt` (the 11 signature units from the spec)
- Modify: `localization/english/aov_racial_armies_l_english.yml`
- Test: `tools/tests/test_racial_armies.py` (`MaaTests`, rows added)

**Interfaces:**
- Consumes: Task 1 clan triggers; Task 3 costs; Task 4 `MaaTests` helpers.

- [ ] **Step 1: Add the failing test rows and tests:**

```python
# EXPECTED rows from the spec's dwarf tables; shared units gate "heritage_dwarven"
# (can_recruit = { culture = { has_cultural_pillar = heritage_dwarven } }), signatures gate their clan trigger, e.g.
#   "aov_golden_gate_guard": ("heavy_infantry", 50, 70, 160, 0, 0, "aov_gold_dwarven_lineage_trigger"),
def test_dwarven_terrain(self):
    # every dwarven unit except aov_silverforge_engineers: hills +0.30, mountains and desert_mountains +0.45,
    # dwarven_hold dwarven_hold_surface cavern dwarven_road +0.65, forest -0.15; row-specific extras from the
    # spec Special column replace the shared value for that terrain (e.g. golden gate dwarven_hold +1.00)
def test_signature_counters(self):
    # aov_giantbane_crossbows counters beasts = 1 elephant_cavalry = 1; aov_dauvek_veker beasts = 2
    # elephant_cavalry = 2; aov_brightbeard_hammers counters heavy_infantry = 1
def test_engineer_corps_siege(self): ...       # type siege_weapon, stack 20, toughness 40, siege_tier 4, siege_value 0.9
def test_handgunners_disabled(self): ...       # dwarven_handgunners can_recruit = { always = no }; rest == Anbennar's
def test_no_racial_unit_gated_by_tradition(self):
    # no can_recruit in either aov_ MAA file or the overrides contains has_cultural_parameter
```

- [ ] **Step 2: Run the tests.** Expected: FAIL.
- [ ] **Step 3: Write the overrides, new units and loc** as in Task 4 (Ramriders get pursuit 25 / screen 40;
  Seg Band pursuit 40; Copper Road Wardens pursuit 30 / screen 60).
- [ ] **Step 4: Run the tests.** Expected: PASS.
- [ ] **Step 5: Commit** `Racial armies: dwarven shared and clan MAA, disable Dwarven Handgunners`.

---

### Task 6: Levy correction generator

**Files:**
- Create: `tools/data/racial_levies.py`
- Create: `tools/build_racial_levies.py`
- Generated: `common/script_values/aov_racial_levy_values.txt`, `common/modifiers/aov_racial_levy_modifiers.txt`,
  `common/scripted_effects/aov_racial_levy_effects.txt`, `localization/english/aov_racial_levy_l_english.yml`
- Test: `tools/tests/test_build_racial_levies.py`

**Interfaces:**
- `tools/data/racial_levies.py`:
  - `RACES = {"elven": 0.75, "dwarven": 0.40, "gnomish": 0.50, "kobold": -0.50}` (f per spec; parameter
    `aov_racial_levy_<race>`).
  - `STEP = 0.05`, `S_MIN = -1.00`, `S_MAX = 3.00`.
  - `CLASSIFIED`: database folder (relative to `common/`) -> how its `levy_size` is conditioned: `buildings`,
    `culture/traditions`, `culture/innovations`, `culture/pillars`, `religion`, `governments`, `laws`.
  - `IGNORED`: `domiciles`, `council_positions`, `court_positions`, `house_aspirations`, `confederation_types`,
    `subject_contracts`, `modifiers`, `epidemics`, `scripted_effects`, `script_values`, `on_action`,
    `character_interactions`, `dynasty_perks`, `lifestyle_perks`, `important_actions` (each with a one-line reason
    comment).
  - `OWN_KEYS`: `heritage_elven`, `heritage_dwarven`, `heritage_gnomish`, `heritage_kobold` (the base cut, never
    corrected).
- `tools/build_racial_levies.py`:
  - `Roots` = `build_holding_models.Roots` (only `.anbennar` and `.game` are read; the overhaul is `SUBMOD`).
  - `collect_sources(roots) -> list[Source]`; `Source = (database: str, key: str, block: str, value: float,
    condition: dict)` — `block` is the modifier block name (`province_modifier`, `county_culture_modifier`, …),
    `condition` holds `parameter`, `terrain`, `is_coastal`, `is_riverside` when the block has them. Later roots
    replace earlier ones by relative path (game < Anbennar < overhaul). Raises `GeneratorError` on a `levy_size`
    in a folder neither in `CLASSIFIED` nor `IGNORED`.
  - `script_value(sources) -> str`: `aov_holding_levy_size_bonus = { value = 0 ... }` in province scope, one
    `if = { limit = { <condition> } add = <value> }` per source, conditions per the spec's Covered sources table
    (owner = `province_owner`; county culture = `county.culture`; county faith = `county.faith`).
  - `tier(s: float) -> int`: `round(clamp(s, S_MIN, S_MAX) / STEP)`.
  - `tier_key(race, n) -> str`: `aov_racial_levy_<race>_<n>` for n ≥ 0, `aov_racial_levy_<race>_m<-n>` for n < 0;
    no modifier for n == 0.
  - `modifiers_file() -> str`: one province modifier per race and non-zero tier with
    `levy_size = -f * STEP * n` (4 decimals, trailing zeros stripped).
  - `effects_file() -> str`: scripted effect `aov_refresh_holding_levy_correction` (province scope): if
    `has_variable = aov_racial_levy_tier`, remove the modifier named by `var:aov_racial_levy_tier` and
    `var:aov_racial_levy_race` (generated `if` chain), remove both variables; then if `province_owner.culture`
    has one of the four parameters, compute the tier from `aov_holding_levy_size_bonus` (`divide = 0.05`,
    `round = yes`, clamped with `min`/`max`), add that race's tier modifier (generated chain) unless 0, and set
    both variables (race as a flag value: `flag:elven` etc.).
  - `loc_file() -> bytes`: a name per tier modifier, `"<Race> Levy Share"` (e.g. `Elven Levy Share`), and a
    shared `_desc` explaining the share.
  - `build_all(roots, notes=None) -> dict[str, bytes]` (relative path -> BOM + LF content); `main() -> int`
    (writes files, prints notes, mirrors `build_rie_courts.main`).

- [ ] **Step 1: Write the failing tests** (`tools/tests/test_build_racial_levies.py`), using small fixture trees in
  a `tempfile.TemporaryDirectory` for the parser tests:

```python
def test_collects_each_block_kind(self):
    # a fixture building with province_modifier, county_culture_modifier { parameter = p }, province_terrain_modifier
    # { terrain = hills is_coastal = yes }, duchy_capital_county_modifier, character_modifier -> 5 sources, right blocks
def test_unclassified_folder_raises(self): ...         # levy_size in common/foo/x.txt -> GeneratorError
def test_ignored_folders_and_own_heritages_skipped(self): ...
def test_later_root_replaces_same_path(self): ...
def test_script_value_conditions(self):
    # province_modifier -> has_building = X; county_modifier -> county = { any_county_province = { has_building = X } }
    # tradition character_modifier -> province_owner.culture = { has_cultural_tradition = T }
    # doctrine -> province_owner.faith = { has_doctrine = D }; government -> province_owner = { has_government = G }
    # law -> province_owner = { has_realm_law = L }; innovation character_modifier -> province_owner.culture =
    # { has_innovation = I }, its county_modifier -> county.culture = { has_innovation = I }
    # building character_modifier -> province_owner = { any_directly_owned_province = { has_building = X } }
    # *_culture_modifier { parameter = P } -> also county.culture = { has_cultural_parameter = P }
def test_tier_math(self):
    for race, f in RACES.items():
        for s in (-0.5, 0.0, 0.3, 0.6, 2.0):
            final = 1 + base(race) + s - f * STEP * tier(s)   # base: -0.75/-0.40/-0.50/+0.50
            self.assertAlmostEqual(final, (1 + base(race)) * (1 + s), delta=f * STEP)
            self.assertGreaterEqual(final, 0)
def test_negative_bonus_gets_positive_correction(self):  # elven tier for s=-0.5 has levy_size = +0.375
def test_bonus_beyond_range_clamps_to_end_tier(self):    # tier(5.0) == tier(S_MAX); tier(-3) == tier(S_MIN)
def test_refresh_removes_before_adding_and_skips_non_racial(self):
    # in effects_file(): the remove chain precedes the add chain; the add chain sits inside a limit requiring
    # one of the four parameters
def test_every_tier_modifier_has_loc(self): ...
class FreshnessTests:  # same shape as test_build_rie_courts.FreshnessTests
    def test_generated_files_match_the_mod(self): ...
```

- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p "test_build_racial_levies*.py"`. Expected:
  FAIL (module missing).
- [ ] **Step 3: Write `tools/data/racial_levies.py` and `tools/build_racial_levies.py`** to the interfaces above.
- [ ] **Step 4: Run the tests except freshness.** Expected: PASS; `FreshnessTests` FAIL (files not generated).
- [ ] **Step 5: Run** `python -I tools/build_racial_levies.py`. Expected: `wrote 4 files`, plus notes listing
  source counts per database and any holding total the sources allow above `S_MAX` (if one is printed, raise
  `S_MAX` in the data file to cover it and rerun).
- [ ] **Step 6: Run all of `test_build_racial_levies`.** Expected: PASS.
- [ ] **Step 7: Commit** `Racial armies: generated per-holding levy correction`.

---

### Task 7: Refresh hooks

**Files:**
- Modify: `common/on_action/aov_racial_armies_on_actions.txt`
- Test: `tools/tests/test_racial_armies.py` (class `RefreshHookTests`)

**Interfaces:**
- Consumes: `aov_refresh_holding_levy_correction` (Task 6), `aov_racial_armies_game_start` (Task 2).
- Produces: on_actions `aov_racial_levy_building_completed`, `aov_racial_levy_title_gain`,
  `aov_racial_levy_holding_razed`, `aov_racial_levy_yearly` appended to `on_building_completed`, `on_title_gain`,
  `on_holding_razed`, `yearly_playable_pulse`.

- [ ] **Step 1: Write the failing tests:**

```python
def test_hooks_appended_to_vanilla_on_actions(self): ...  # the four appends, by name
def test_building_completed_refreshes_root(self): ...     # root is the province
def test_title_gain_refreshes_every_county_province(self):
    # scope:title tier county -> every_county_province; barony -> title_province; higher tiers: nothing
def test_holding_razed_refreshes_scope_province(self): ...
def test_yearly_refreshes_owned_provinces(self): ...       # every_directly_owned_province, racial owners only
def test_game_start_refreshes_racial_provinces(self): ...  # aov_racial_armies_game_start effect calls the refresh
```

- [ ] **Step 2: Run the tests.** Expected: FAIL.
- [ ] **Step 3: Write the on_actions.** Title tier checks: `scope:title = { tier = tier_county }` /
  `tier_barony`. Yearly: limit the root to a culture with one of the four parameters, then
  `every_directly_owned_province = { aov_refresh_holding_levy_correction = yes }`.
- [ ] **Step 4: Run the tests.** Expected: PASS.
- [ ] **Step 5: Commit** `Racial armies: levy correction refresh hooks`.

---

### Task 8: Debug battle event

**Files:**
- Create: `events/aov_racial_armies_debug_events.txt`
- Modify: `localization/english/aov_racial_armies_l_english.yml`

**Interfaces:**
- Produces: events `aov_racial_armies_debug.0001` (human vs moon elf) and `.0002` (human vs dwarf), fired from the
  console (`event aov_racial_armies_debug.0001`), `hidden = yes`, `trigger = { debug_only = yes }`.

- [ ] **Step 1: Write the events.** Root must be a playable ruler whose culture has none of the four
  `aov_racial_levy_*` parameters (the event does nothing otherwise). Each event picks
  `random_ruler = { limit = { is_landed = yes culture = { has_cultural_parameter = aov_racial_levy_elven } } }`
  (`.0002`: `aov_racial_levy_dwarven`) as `scope:foe`, has root `start_war` on it with `cb = county_conquest_cb`
  and `target_title = scope:foe.capital_county`, then `spawn_army` for each side at `root.capital_province`.
  Armies cost about 3 gold/month of MAA upkeep each: human 4,000 levies + `armored_footmen` 3, `bowmen` 5,
  `pikemen_unit` 3 stacks; elf 1,000 levies + `staochri` 1, `aithchri` 2, `sheahrna` 2; dwarf 2,400 levies +
  `dwarven_guardians` 2, `armor_breakers` 2, `shieldwall` 2. The tester watches the battle result (spec Testing
  item 5: within about ±15%).
- [ ] **Step 2: Validate** with `python -I tools/validate.py`. Expected: no new reports for the event file.
- [ ] **Step 3: Commit** `Racial armies: debug battle events`.

---

### Task 9: Validation, docs and handoff

**Files:**
- Create: `docs/systems/racial-armies.md`
- Modify: `CLAUDE.md` (Systems table row), `docs/systems/updating.md` (generator order and hand re-copies),
  `docs/systems/validation-baseline.md` (only if inherited reports are baselined)

- [ ] **Step 1: Run** `python -I tools/validate.py`. Expected: no new reports. Fix any that are ours; baseline only
  reports inherited verbatim from Anbennar copies, and record them in `validation-baseline.md`.
- [ ] **Step 2: Run all tool tests** `python -I -m unittest discover -s tools/tests`. Expected: OK.
- [ ] **Step 3: Write `docs/systems/racial-armies.md`**: the heritage table, the levy correction (formula, covered
  and not covered sources, refresh hooks), roster tables (link to the spec for stats), generated-file rows
  (`build_racial_levies.py`: the four generated files, why), hand-maintained overrides to re-check after an
  Anbennar update (4 heritages, 2 traditions, 15 MAA types), and the in-game checklist from the spec's Testing
  section with the debug event names.
- [ ] **Step 4: Add the CLAUDE.md row**: `| Racial armies: levies, domain limit, elf and dwarf MAA | docs/systems/racial-armies.md | build_racial_levies.py |`,
  and in `updating.md` add `python -I tools/build_racial_levies.py` to the generator list (after an Anbennar update
  or a CK3 patch, since both add levy sources) and the override re-check list.
- [ ] **Step 5: Commit** `Racial armies: docs and validation`.
- [ ] **Step 6: Report** to the user what still needs an in-game check (spec Testing items 1–6), naming
  `aov_racial_armies_debug.0001` / `.0002`.
