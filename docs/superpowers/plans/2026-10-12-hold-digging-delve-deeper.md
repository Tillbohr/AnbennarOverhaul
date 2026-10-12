# Hold Digging: Delve Deeper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the *Delving Campaign* activity with *Delve Deeper*: a ruler pays for a hold's next level, the dig runs for years as a scripted construction stored on the hold, and EU4-style events add or remove months of progress.

**Architecture:** Dig state lives on the hold province (`aov_dig_target_level`, `aov_dig_progress`, modifier `aov_delving_NN`). A quarterly on_action advances each playable ruler's running digs; a yearly on_action rolls the dig events for dwarven players. The decision *Delve Deeper* starts a dig through a hold-picker event. Costs, lengths and chances are data in `tools/data/holds.py`, emitted by `tools/build_holds.py`. The activity, its art, loc and tests are removed.

**Tech Stack:** CK3 1.19.0.6 script, ck3-tiger (`python -I tools/validate.py`), Python `unittest` in `tools/tests/` (run with `python -I -m unittest discover -s tools/tests -p <file>`).

**Spec:** `docs/superpowers/specs/2026-10-10-dwarven-hold-digging-design.md` (section "Digging: Delve Deeper (revised 2026-10-12)").

## Global Constraints

- Branch `hold-digging` (PR #8). Base Anbennar is never edited. Script/loc: UTF-8 BOM + LF + tabs; Python: no BOM, LF. Never hand-edit generated files; change `tools/data/holds.py` / `tools/build_holds.py` and regenerate.
- No attribution lines in commit messages.
- Dwarf test: `is_dwarvish_culture = yes`. Hold test: `aov_is_hold`; working: `aov_hold_is_working` (existing triggers).
- Cost: `aov_dig_cost` = 150 × target level gold, paid up front. Length: `aov_dig_months` = 12 × (8 + 4 × (target − 1)) months (144 for level 2 … 528 for level 10).
- Events: 40% chance per hold per year, dwarven player holders only; stages by progress share: Survey under 25% (events 1-3), Excavation 25% to under 75% (4-8), Shoring 75% and over (9-11); equal weights; options change progress by at most ±18 months, never below 0.
- A dig cannot be cancelled. Ruin by conquest ends it (progress and gold lost). It pauses while the hold is occupied or its holder is not a dwarf.
- **Ruling (deviation from the spec's "monthly tick"):** CK3 has no monthly or per-province pulse (the finest global pulse is `quarterly_playable_pulse`, root = each playable ruler). The tick runs quarterly and adds **3 months**, for the holds the ruler holds. A hold held by a non-playable baron does not advance (it pauses). Task 5 updates the spec's wording.

## Review Focus

1. A gain event or tick that overshoots the target: the level rises exactly once, and the dig ends with the surplus discarded (a new dig starts at 0). *(Task 2 `test_completion_levels_once_and_ends_dig`.)*
2. A ruler holding two holds, one digging: the decision offers only the other, events target the digging hold, and the progress tooltip lists only running digs. *(Task 3 `test_picker_excludes_running_digs`, Task 4 `test_events_act_on_scope_hold`.)*
3. A hold ruined mid-dig, then restored: the dig is gone and a new dig starts from 0 at full price. *(Task 2 `test_ruin_ends_dig`.)*
4. Level 10: no decision option, no tick, and no event for that hold. *(Task 2 `test_can_dig_needs_level_below_ten`, Task 4 `test_roll_skips_holds_without_dig`.)*
5. The AI never digs without a 2 × cost reserve, and picks its cheapest hold. *(Task 3 `test_ai_reserve_and_cheapest_hold`.)*

---

### Task 1: Dig data and generated values

**Files:**
- Modify: `tools/data/holds.py`, `tools/build_holds.py`, `tools/tests/test_build_holds.py`, `tools/tests/test_hold_data.py`
- Regenerate: `common/script_values/aov_hold_values.txt`, `common/modifiers/aov_hold_modifiers.txt`, `localization/english/aov_holds_l_english.yml`

**Interfaces:**
- Produces in `tools/data/holds.py`:
  - `DIG_COST_PER_LEVEL = 150`;
  - `dig_months(target: int) -> int` returning `12 * (8 + 4 * (target - 1))`;
  - `EVENT_CHANCE = 40`, `STAGE_SHARES = (0.25, 0.75)`, `TICK_MONTHS = 3`.

  Remove `DIG_TARGET_PER_LEVEL`, `CAMPAIGN_COST_PER_LEVEL`, `CAMPAIGN_BASE`, `TRAIT_BONUS`, `PACE`, `INVESTMENT`, `PHASE_MONTHS`.
- Produces script values (generated):
  - `aov_hold_level` (unchanged).
  - `aov_dig_target_value` (province): `var:aov_dig_target_level` if set, else `aov_hold_level + 1`.
  - `aov_dig_cost` (province): `DIG_COST_PER_LEVEL × aov_dig_target_value`.
  - `aov_dig_months` (province): `12 × (8 + 4 × (aov_dig_target_value − 1))`.

  Remove `aov_dig_target`, `aov_dig_campaign_cost`, `aov_dig_campaign_base`.
- Produces modifiers `aov_delving_02` … `aov_delving_10` (province, `icon = economy_positive`, no effects). Loc: "Delving to Level N" and desc "Dwarves are digging this hold deeper."

- [ ] **Step 1: Write the failing tests** (`test_build_holds.py`; drop tests of the removed values and constants):

```python
def test_dig_months_and_cost(self):
    self.assertEqual([holds.dig_months(n) for n in (2, 10)], [144, 528])
    self.assertEqual(holds.DIG_COST_PER_LEVEL, 150)
    v = bh.render_values()
    for name in ("aov_dig_target_value", "aov_dig_cost", "aov_dig_months"):
        self.assertIn(f"{name} = {{", v)
    for gone in ("aov_dig_campaign_cost", "aov_dig_campaign_base", "aov_dig_target ="):
        self.assertNotIn(gone, v)

def test_delving_modifiers(self):
    m = bh.render_modifiers()
    for n in range(2, 11):
        self.assertIn(f"aov_delving_{n:02d} = {{", m)
    self.assertNotIn("aov_delving_01", m)

def test_removed_constants(self):
    for name in ("PACE", "INVESTMENT", "PHASE_MONTHS", "CAMPAIGN_BASE", "CAMPAIGN_COST_PER_LEVEL", "TRAIT_BONUS"):
        self.assertFalse(hasattr(holds, name), name)
```

- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p test_build_holds.py` → FAIL.
- [ ] **Step 3: Implement** the data and generator changes. Regenerate with `python -I tools/build_holds.py`.
- [ ] **Step 4: Run** the focused tests → PASS. Other test modules may fail until Task 2; note which.
- [ ] **Step 5: Commit** `git commit -m "Dig data: cost and months per level, delving modifiers"`.

---

### Task 2: Remove the activity; dig core (start, tick, complete, end)

**Files:**
- Delete: `common/activities/activity_types/aov_hold_dig.txt`; `common/on_action/aov_hold_dig_on_actions.txt` (recreated in Task 4); `localization/english/aov_hold_dig_l_english.yml` (keep event 100 loc by moving it into `localization/english/aov_hold_dig_events_l_english.yml`); the 9 DDS files under `gfx/interface/icons/activities/activity_hold_dig*.dds`, `gfx/interface/icons/activity_option_categories/aov_dig_*.dds`, `gfx/interface/icons/activity_phases/aov_dig_*.dds`, `gfx/interface/illustrations/activity_header_backgrounds/activity_hold_dig.dds`; `tools/tests/test_hold_dig_activity.py`.
- Modify: `common/scripted_effects/aov_hold_effects.txt`, `common/scripted_effects/aov_hold_dig_event_effects.txt`, `common/scripted_triggers/aov_hold_triggers.txt`, `common/on_action/aov_hold_on_actions.txt`, `events/aov_hold_dig_events.txt` (event 101 removed; 100 keeps its discovery, now `scope:hold`-based), `tools/tests/test_hold_ruin.py`
- Create: `tools/tests/test_hold_dig.py`

**Interfaces:**
- Consumes: Task 1 values and modifiers.
- Produces (province scope unless noted):
  - Trigger `aov_hold_dig_running`: `has_variable = aov_dig_target_level`.
  - Trigger `aov_can_dig_at` (uses `scope:digger`), updated: working, `aov_hold_level < 10`, `NOT = { aov_hold_dig_running = yes }`, `barony.holder = scope:digger`, digger `is_dwarvish_culture = yes`.
  - Effect `aov_hold_start_dig_effect`: sets `aov_dig_target_level` = level + 1 and `aov_dig_progress` = 0, and adds the matching `aov_delving_NN` modifier. Gold is paid by the caller (Task 3).
  - Effect `aov_hold_add_dig_progress_effect`: takes `$MONTHS$` (may be negative), clamps at 0, then calls `aov_hold_check_dig_complete_effect`.
  - Effect `aov_hold_check_dig_complete_effect`: if `var:aov_dig_progress >= aov_dig_months`, then:
    - one guarded `add_building = dwarven_hold_0N` for the target level;
    - `aov_hold_end_dig_effect`;
    - `barony.holder = { save_scope_as … trigger_event = aov_hold_dig.100 }` with `scope:hold` saved.
  - Effect `aov_hold_end_dig_effect`: replaces `aov_hold_end_campaign_effect`. It removes `aov_dig_target_level`, `aov_dig_progress` and every `aov_delving_NN` modifier. `aov_hold_ruin_effect` calls it.
  - On_action `aov_hold_dig_quarterly`, appended to `quarterly_playable_pulse`: root = the ruler; for every held barony whose province is a hold with a running dig, `aov_hold_add_dig_progress_effect = { MONTHS = 3 }` unless the province `is_occupied` or root is not `is_dwarvish_culture`.
  - Remove `aov_hold_apply_campaign_effect` and the activity-scope `aov_dig_floor_progress`.
  - Events 1-11 converted mechanically so nothing references the activity:
    - `trigger` becomes `exists = scope:hold` and `scope:hold = { aov_hold_dig_running = yes }`;
    - the `immediate` activity scopes are removed;
    - each `change_variable` on `aov_campaign_progress` becomes `scope:hold = { aov_hold_add_dig_progress_effect = { MONTHS = <same n> } }`;
    - the following `aov_dig_floor_progress` calls are dropped.

    Loc and the yearly roll are Task 4.

- [ ] **Step 1: Write the failing tests** (`tools/tests/test_hold_dig.py`, text checks in the style of `test_hold_ruin.py`):

```python
def test_activity_is_gone(self):
    self.assertFalse((ROOT / "common/activities/activity_types/aov_hold_dig.txt").exists())
    for path in list((ROOT / "common").rglob("*.txt")) + list((ROOT / "events").rglob("*.txt")):
        self.assertNotIn("activity_hold_dig", path.read_text("utf-8-sig", errors="ignore"), path)

def test_can_dig_needs_level_below_ten(self):
    t = trigger_block("aov_can_dig_at")
    self.assertIn("aov_hold_level < 10", t)
    self.assertIn("aov_hold_dig_running = yes", t)   # inside NOT

def test_completion_levels_once_and_ends_dig(self):
    e = effect_block("aov_hold_check_dig_complete_effect")
    self.assertEqual(e.count("add_building = dwarven_hold_"), 9)   # targets 02..10, if/else_if chain
    self.assertIn("aov_hold_end_dig_effect = yes", e)
    self.assertIn("aov_hold_dig.100", e)

def test_progress_floor(self):
    self.assertIn("aov_dig_progress < 0", effect_block("aov_hold_add_dig_progress_effect"))

def test_ruin_ends_dig(self):
    self.assertIn("aov_hold_end_dig_effect = yes", effect_block("aov_hold_ruin_effect"))
    self.assertIn("remove_variable = aov_dig_progress", effect_block("aov_hold_end_dig_effect"))

def test_quarterly_tick(self):
    oa = read("common/on_action/aov_hold_on_actions.txt")
    self.assertRegex(oa, r"quarterly_playable_pulse\s*=\s*\{\s*on_actions\s*=\s*\{[^}]*aov_hold_dig_quarterly")
    tick = on_action_block("aov_hold_dig_quarterly")
    for s in ("MONTHS = 3", "is_occupied", "is_dwarvish_culture"):
        self.assertIn(s, tick)
```

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.** Delete the files with `git rm`, then write the effects, triggers and on_action. Update the old tests: `test_hold_ruin.py` references to `aov_hold_end_campaign_effect` become `aov_hold_end_dig_effect`.
- [ ] **Step 4: Run** the hold test modules and `python -I tools/validate.py` → PASS / `fatal: 0, error: 0, warning: 0`. `test_hold_dig_events.py` is rewritten in Task 4; at this step update only its assertions that name the activity or `aov_campaign_progress`.
- [ ] **Step 5: Commit** `git commit -m "Replace the dig activity with a scripted dig on the hold"`.

---

### Task 3: Delve Deeper decision and progress display

**Files:**
- Modify: `common/decisions/aov_hold_decisions.txt`, `events/aov_hold_ruin_events.txt` or a new `events/aov_hold_delve_events.txt` (picker event; your choice, namespace `aov_hold_delve`), loc in `localization/english/aov_hold_ruin_l_english.yml` or a new `aov_hold_delve_l_english.yml`
- Test: `tools/tests/test_hold_dig.py`

**Interfaces:**
- Consumes: `aov_can_dig_at`, `aov_dig_cost`, `aov_dig_months`, `aov_hold_start_dig_effect`, `aov_hold_dig_running`.
- Produces:
  - Decision `aov_delve_deeper_decision`. `is_shown`: `is_dwarvish_culture = yes` and holds any hold barony. `is_valid`: some held hold passes `aov_can_dig_at` (scope:digger = root) with `gold >= that hold's aov_dig_cost`. Its effect opens the picker event.
  - Picker event `aov_hold_delve.1`: one option per hold in `holds.HOLDS` (9 options, each limited to that barony: held by root, `aov_can_dig_at`, `gold >= aov_dig_cost`). The option calls `remove_short_term_gold = <that province's aov_dig_cost>` and `aov_hold_start_dig_effect`, plus a cancel option.
  - Progress display: the decision's `desc` has one `triggered_desc` per hold (9) shown when root holds that barony and it has a running dig. Its loc reads "[hold name]: [progress] of [months] months" through data functions (`GetTitleByKey('<barony>').GetProvince.MakeScope.Var('aov_dig_progress').GetValue|0` and `.ScriptValue('aov_dig_months')|0`). If tiger rejects a form, use the nearest one tiger accepts and record it in the report.
  - AI:
    - `ai_check_interval = 12`.
    - `ai_will_do` is 0 unless root's gold ≥ 2 × the cheapest diggable hold's `aov_dig_cost`.
    - The picker option weights favour the cheapest hold (`ai_chance` higher for lower `aov_dig_cost`).

- [ ] **Step 1: Write the failing tests:**

```python
def test_decision_gating_and_cost(self):
    d = decision_block("aov_delve_deeper_decision")
    self.assertIn("is_dwarvish_culture = yes", d)
    self.assertIn("aov_can_dig_at", d)
    self.assertIn("aov_dig_cost", d)

def test_picker_excludes_running_digs(self):
    ev = event_block("aov_hold_delve.1")
    for h in holds.HOLDS:
        self.assertIn(f"title:{h['barony']}", ev)
    self.assertGreaterEqual(ev.count("aov_can_dig_at = yes"), 9)   # each option re-checks, so a running dig is excluded
    self.assertGreaterEqual(ev.count("aov_hold_start_dig_effect = yes"), 9)

def test_progress_desc_per_hold(self):
    d = decision_block("aov_delve_deeper_decision")
    self.assertGreaterEqual(d.count("triggered_desc"), 9)
    self.assertIn("aov_hold_dig_running = yes", d)

def test_ai_reserve_and_cheapest_hold(self):
    d = decision_block("aov_delve_deeper_decision")
    self.assertIn("ai_check_interval = 12", d)
    self.assertRegex(d, r"multiply = 2|2 \*|value = 2")   # the 2 x cost reserve
```

- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** tests and `validate.py` → PASS / clean.
- [ ] **Step 5: Commit** `git commit -m "Add the Delve Deeper decision"`.

---

### Task 4: Dig events on the hold

**Files:**
- Modify: `events/aov_hold_dig_events.txt` (events 1-11 and 100), `localization/english/aov_hold_dig_events_l_english.yml`, `common/scripted_effects/aov_hold_dig_event_effects.txt` (delete if now empty), `tools/tests/test_hold_dig_events.py`
- Create: `common/on_action/aov_hold_dig_on_actions.txt`

**Interfaces:**
- Consumes: `aov_hold_add_dig_progress_effect`, `aov_hold_dig_running`, `aov_dig_months`.
- Produces:
  - On_action `aov_hold_dig_yearly`, appended to `yearly_playable_pulse`. Root is the ruler; it does nothing unless `is_ai = no` and `is_dwarvish_culture = yes`. For every held hold with a running dig:
    - `random = { chance = 40 ... }`;
    - save `scope:hold`;
    - pick the stage by `var:aov_dig_progress` against `aov_dig_months` × 0.25 / 0.75;
    - `random_list` with equal weights over that stage's events (1-3 / 4-8 / 9-11);
    - `trigger_event`.
  - Events 1-11 (already on `scope:hold` from Task 2): loc reworded from "campaign" to "the delving at [hold.GetName]", with months in place of progress. Gold, prestige and duel parts stay.
  - Event 100 (Breakthrough): loc only.

- [ ] **Step 1: Write the failing tests** (rewrite `test_hold_dig_events.py`):

```python
def test_roll_skips_holds_without_dig(self):
    oa = on_action_block("aov_hold_dig_yearly")
    self.assertIn("aov_hold_dig_running = yes", oa)
    self.assertIn("chance = 40", oa)
    self.assertIn("is_ai = no", oa)

def test_stage_selection(self):
    oa = on_action_block("aov_hold_dig_yearly")
    self.assertIn("0.25", oa); self.assertIn("0.75", oa)
    for n in range(1, 12):
        self.assertIn(f"trigger_event = aov_hold_dig.{n}", oa)

def test_events_act_on_scope_hold(self):
    for n in range(1, 12):
        ev = event_block(f"aov_hold_dig.{n}")
        self.assertIn("scope:hold", ev)
        self.assertNotIn("involved_activity", ev)
        self.assertNotIn("aov_campaign_progress", ev)

def test_month_changes_bounded(self):
    for m in re.finditer(r"MONTHS = (-?\d+)", EVENTS):
        self.assertLessEqual(abs(int(m.group(1))), 18)

def test_no_campaign_wording(self):
    self.assertNotRegex(LOC.lower(), r"campaign")
```

- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** tests, the full suite and `validate.py` → PASS / clean.
- [ ] **Step 5: Commit** `git commit -m "Dig events act on the hold's progress"`.

---

### Task 5: Docs and verification

**Files:**
- Modify: `CLAUDE.md`
  - The Dwarven holds entry: Delve Deeper replaces the activity; cost, months, the quarterly tick of 3 months, the yearly 40% events and stages.
  - Generated-files row: the new values and the `aov_delving_NN` modifiers.
- Modify: `docs/superpowers/specs/2026-10-10-dwarven-hold-digging-design.md`
  - "Monthly tick" becomes "quarterly tick of 3 months (`quarterly_playable_pulse`; a hold held by a non-playable baron pauses)", per the plan's ruling.

- [ ] **Step 1:** Update both documents.
- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests` → OK; `python -I tools/validate.py` → `fatal: 0, error: 0, warning: 0`; `git grep -n "activity_hold_dig\|aov_campaign"` → no hits outside `docs/`.
- [ ] **Step 3: In-game checklist** (for the PR, unticked):
  - [ ] *Delve Deeper* is shown to a dwarven ruler holding a hold.
    - Picking a hold charges 150 × target level gold.
    - It adds *Delving to Level N*.
    - The decision tooltip shows "[Hold]: X of Y months".
  - [ ] Progress rises by 3 each quarter, and stops while the hold is occupied.
  - [ ] A dig event appears within a few years for a player, and its option moves the shown progress.
  - [ ] Console-boosted progress raises the level once and fires *Breakthrough*.
  - [ ] Conquest by a non-dwarf removes the dig.
- [ ] **Step 4: Commit** `git commit -m "Document Delve Deeper"`.
