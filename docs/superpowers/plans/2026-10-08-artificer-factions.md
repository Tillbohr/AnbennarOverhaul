# Artificer Factions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three elected, life-held landless faction titles (Brillites, Mechanists, Technomancers) with per-realm influence that drives modifiers, research cost and time, shown in the Artificery window's Factions tab.

**Architecture:** Plain CK3 script in new `aov_` files: titles and coats of arms, influence stored as ruler variables with parameterised scripted effects (`FACTION = brillites|mechanists|technomancers`), elections run through global lists/variables and a vote event, and GUI built from one reusable faction-card type. Existing research effects are changed to read per-faction cost and duration.

**Tech Stack:** CK3 1.19.0.6 script, PdxGui, ck3-tiger (`python -I tools/validate.py`), Python `unittest` static tests in `tools/tests/`.

**Spec:** `docs/superpowers/specs/2026-10-08-artificer-factions-design.md`

## Global Constraints

- All script/loc files: UTF-8 **with BOM**, **LF** line endings, tabs; loc files start with `l_english:`.
- New files use the `aov_`/`zz_aov_` prefix; never edit `../anbennar-ck3-dev-master`.
- Faction keys everywhere: `brillites`, `mechanists`, `technomancers` (order: Brillites, Mechanists, Technomancers).
- Titles: `d_brillites`, `d_mechanists`, `d_technomancers`; duchy tier, `landless = yes`, `capital = c_nimscodd`.
- Influence: ruler variables `aov_influence_<faction>`, 0–100, start 40.
- Levels: Hostile 0–14, Displeased 15–29, Neutral 30–59, Favored 60–84, Exalted 85–100 (level index 0–4).
- Research cost by level: 100 / 75 / 50 / 38 / 25. Time: Hostile/Displeased ×1.25, Neutral/Favored ×1, Exalted ×0.75.
- Sponsoring: +20 to the sponsor, −10 to each other faction. Running research: +1/quarter to the sponsor.
  Fade: −1/quarter above 40. Leader opinion: ≥50 → +2, 20–49 → +1, −19–19 → 0, −49–−20 → −1, ≤−50 → −2 per quarter.
- Make Amends: 100 gold, +10, only below 40, capped at 40.
- Vote weight = level index + 1 (Hostile 1 … Exalted 5). Election lasts 30 days. Exactly three candidates.
- Candidate score = Learning × 2 + Diplomacy (Brillites) / Stewardship (Mechanists) / Martial (Technomancers).
- Active inventions never change influence.

## Review Focus

1. A candidate dies or loses eligibility during the 30-day vote → the count ignores them; if all three are gone, a new election opens. *(Task 5 test: `test_resolve_skips_dead_candidates`.)*
2. Two leaders die close together and the same gnome wins both → at the count, a candidate already holding a faction title is skipped. *(Task 5 test: `test_resolve_skips_current_holders`.)*
3. Influence near the bounds: sponsoring a rival at 5 gives 0, not −5; Make Amends at 35 gives 40, not 45. *(Task 2 test: `test_change_influence_clamps`; Task 6 test: `test_make_amends_caps_at_forty`.)*
4. Influence level changes while research runs → the refund returns what was actually paid, not today's price. *(Task 3 test: `test_refund_uses_paid_amount`.)*
5. A voter loses their academy or dies before the count → their pending vote is not cast for them. *(Task 5 test: `test_auto_votes_only_for_living_eligible_voters`.)*

---

## File Structure

| File | Responsibility |
|---|---|
| `common/landed_titles/aov_artificer_faction_titles.txt` | the three titles |
| `common/coat_of_arms/coat_of_arms/aov_artificer_factions.txt` | their coats of arms |
| `common/flavorization/aov_artificer_faction_flavorization.txt` | holder titles |
| `common/scripted_triggers/aov_artificer_faction_triggers.txt` | title, level, candidate, voter triggers |
| `common/scripted_triggers/zz_aov_interaction_triggers.txt` | revoke-trigger override |
| `common/script_values/aov_artificer_faction_values.txt` | level, cost, quarters, score, opinion drift, vote weight |
| `common/modifiers/aov_artificer_faction_modifiers.txt` | 12 level modifiers |
| `common/scripted_effects/aov_artificer_faction_effects.txt` | influence change/refresh/quarterly/inherit/AI |
| `common/scripted_effects/aov_artificer_election_effects.txt` | election open/vote/resolve/grant |
| `common/scripted_guis/aov_artificer_faction_sgui.txt` | Make Amends, holder/vacancy/election visibility |
| `common/on_action/aov_artificer_faction_on_actions.txt` | game start, quarterly, on_death, yearly |
| `common/event_themes/aov_artificery_event_themes.txt` | `aov_artificery` theme |
| `events/aov_artificer_faction_events.txt` | vote panel `.1`, result `.2` |
| `gui/aov_artificer_factions.gui` | `aov_faction_card` and `aov_influence_bar` types |
| `localization/english/aov_artificer_factions_l_english.yml` | all new loc |
| `tools/tests/test_artificer_factions.py` | static tests for all of the above |

Changed: `common/scripted_effects/aov_artificery_research_effects.txt`, `common/scripted_triggers/aov_artificery_research_triggers.txt`, `common/scripted_guis/aov_artificery_research_sgui.txt`, `common/script_values/aov_artificery_values.txt`, `tools/build_inventions.py` (+ regenerated output), `gui/aov_window_artificery.gui`, `gui/aov_window_artificery_research.gui`, `localization/english/aov_artificery_l_english.yml`, `CLAUDE.md`.

Test helpers: every task's tests go in `tools/tests/test_artificer_factions.py`, which starts with the same `MOD`, `read(rel)` and `block(text, name)` helpers as `tools/tests/test_artificery_research.py`, plus `FACTIONS = ("brillites", "mechanists", "technomancers")` and `LEVELS = ("hostile", "displeased", "favored", "exalted")`.

Run all tool tests with: `python -I -m unittest discover -s tools/tests -v` (expected: all `ok`). Validate with: `python -I tools/validate.py` (expected last line: `fatal: 0, error: 0, warning: 0, untidy: 0, tips: 0`).

---

### Task 1: Titles, coats of arms, flavorization, revoke protection

**Files:**
- Create: `common/landed_titles/aov_artificer_faction_titles.txt`, `common/coat_of_arms/coat_of_arms/aov_artificer_factions.txt`, `common/flavorization/aov_artificer_faction_flavorization.txt`, `common/scripted_triggers/aov_artificer_faction_triggers.txt`, `common/scripted_triggers/zz_aov_interaction_triggers.txt`, `localization/english/aov_artificer_factions_l_english.yml`
- Test: `tools/tests/test_artificer_factions.py`

**Interfaces:**
- Produces: title scope trigger `aov_is_artificer_faction_title` (yes for the three titles); titles `title:d_<faction>`.

- [ ] **Step 1: Write the failing tests**

```python
class TitleTests(unittest.TestCase):
    def test_three_landless_duchies(self):
        text = read("common/landed_titles/aov_artificer_faction_titles.txt")
        for f in FACTIONS:
            b = block(text, f"d_{f}")
            for line in ("landless = yes", "definite_form = yes", "ruler_uses_title_name = no",
                         "no_automatic_claims = yes", "can_use_nomadic_naming = no", "capital = c_nimscodd"):
                self.assertIn(line, b)
            self.assertNotIn("always_follows_primary_heir", b)

    def test_coats_of_arms_use_cogs(self):
        text = read("common/coat_of_arms/coat_of_arms/aov_artificer_factions.txt")
        self.assertIn("ce_anb_cog", block(text, "d_brillites"))
        self.assertIn("ce_anb_crystal_magic", block(text, "d_brillites"))
        self.assertIn("pattern_checkers_01", block(text, "d_mechanists"))
        self.assertEqual(block(text, "d_mechanists").count("ce_anb_cog.dds"), 2)
        self.assertIn("ce_anb_cog_02", block(text, "d_technomancers"))

    def test_revoke_override_keeps_anbennar_and_excludes_faction_titles(self):
        ours = block(read("common/scripted_triggers/zz_aov_interaction_triggers.txt"), "title_revocation_standard_can_pick_title_trigger")
        base = (MOD.parent / "anbennar-ck3-dev-master/common/scripted_triggers/00_interaction_triggers.txt").read_text(encoding="utf-8-sig")
        for line in block(base, "title_revocation_standard_can_pick_title_trigger").splitlines():
            self.assertIn(line, ours)
        self.assertIn("aov_is_artificer_faction_title = no", ours)

    def test_faction_title_trigger(self):
        b = block(read("common/scripted_triggers/aov_artificer_faction_triggers.txt"), "aov_is_artificer_faction_title")
        for f in FACTIONS:
            self.assertIn(f"this = title:d_{f}", b)
```

- [ ] **Step 2: Run tests, expect FAIL** (`FileNotFoundError`).
- [ ] **Step 3: Write the titles** as Anbennar's `d_minar_temple` format with the Global Constraints flags (no `always_follows_primary_heir`, no `destroy_if_invalid_heir`) and colors Brillites `{ 120 40 160 }`, Mechanists `{ 110 110 120 }`, Technomancers `{ 30 50 150 }`.
- [ ] **Step 4: Write the coats of arms** (CoA format as Anbennar's `common/coat_of_arms/coat_of_arms/` files):
  - Brillites: `pattern_solid.dds`, purple field; `ce_anb_cog.dds` gold, scale 0.8; `ce_anb_crystal_magic.dds` white, scale 0.35, centred.
  - Mechanists: `pattern_checkers_01.dds` grey/black; two `ce_anb_cog.dds` bronze (`rgb { 176 120 60 }`), scale 0.55, at positions `{ 0.38 0.42 }` and `{ 0.62 0.60 }`.
  - Technomancers: `pattern_solid.dds` deep blue; `ce_anb_cog_02.dds` colors blue / magenta / teal, scale 0.85.
- [ ] **Step 5: Write the flavorization** so the holders of `d_brillites`, `d_mechanists` and `d_technomancers` are titled *Spark-Primarch*, *Guildmaster Mechanist* and *Arch-Technomancer* (follow Anbennar's `common/flavorization/00_anb_title_holders.txt` block for `d_skaldskola`: `type = character`, `gender = male`, `special = holder`, `titles = { d_x }`, `priority`; add female versions with the same names).
- [ ] **Step 6: Write `aov_is_artificer_faction_title`** (`OR = { this = title:d_brillites this = title:d_mechanists this = title:d_technomancers }`) and the override: copy Anbennar's `title_revocation_standard_can_pick_title_trigger` verbatim into the `zz_aov_` file, add `aov_is_artificer_faction_title = no` inside a `custom_description = { text = "aov_revoke_not_artificer_faction_title" ... }` with the comment `# Anbennar Overhaul`.
- [ ] **Step 7: Loc**: title names (`d_brillites: "The Brillite Circle"`, `d_brillites_adj`, and the same for `d_mechanists` "The Mechanist Guild" and `d_technomancers` "The Technomancer Conclave"), the flavour keys, and `aov_revoke_not_artificer_faction_title: "Is not the leadership of an artificer faction"`.
- [ ] **Step 8: Run tests and validate, expect PASS / clean.**
- [ ] **Step 9: Commit** `git add` the new files and the test; message `Add artificer faction titles`.

---

### Task 2: Influence core (values, levels, modifiers, change effect)

**Files:**
- Create: `common/script_values/aov_artificer_faction_values.txt`, `common/modifiers/aov_artificer_faction_modifiers.txt`, `common/scripted_effects/aov_artificer_faction_effects.txt`
- Modify: `common/scripted_triggers/aov_artificer_faction_triggers.txt`, `localization/english/aov_artificer_factions_l_english.yml`
- Test: `tools/tests/test_artificer_factions.py`

**Interfaces:**
- Produces (character scope):
  - values `aov_influence_<f>` (the variable, 40 if unset), `aov_influence_level_<f>` (0–4), `aov_vote_weight_<f>` (level + 1), `aov_research_cost_<f>`, `aov_research_quarters_<f>`;
  - triggers `aov_influence_is_<level>_<f>` for the five levels;
  - effects `aov_faction_init = yes` (sets missing variables to 40), `aov_faction_change_influence = { FACTION = <f> AMOUNT = <int> }` (clamps 0–100 then refreshes), `aov_faction_refresh_modifiers = yes` (exactly one level modifier per faction, none at Neutral, none while `aov_artificery_dormant`), `aov_faction_remove_modifiers = yes`.
  - modifiers `aov_<f>_<level>` for level in hostile/displeased/favored/exalted.

- [ ] **Step 1: Write the failing tests**

```python
class InfluenceTests(unittest.TestCase):
    def test_twelve_modifiers(self):
        text = read("common/modifiers/aov_artificer_faction_modifiers.txt")
        for f in FACTIONS:
            for lv in LEVELS:
                block(text, f"aov_{f}_{lv}")
        self.assertIn("domain_tax_mult = 0.1", block(text, "aov_mechanists_exalted"))
        self.assertIn("domain_tax_mult = -0.1", block(text, "aov_mechanists_hostile"))
        self.assertIn("learning = 2", block(text, "aov_brillites_exalted"))
        self.assertIn("advantage = -5", block(text, "aov_technomancers_hostile"))

    def test_level_thresholds(self):
        b = block(read("common/script_values/aov_artificer_faction_values.txt"), "aov_influence_level_brillites")
        for n in ("15", "30", "60", "85"):
            self.assertIn(f">= {n}", b)

    def test_costs_and_quarters(self):
        text = read("common/script_values/aov_artificer_faction_values.txt")
        cost = block(text, "aov_research_cost_mechanists")
        for v in ("100", "75", "50", "38", "25"):
            self.assertIn(f"value = {v}", cost)
        q = block(text, "aov_research_quarters_technomancers")
        for v in ("75", "60", "45"):
            self.assertIn(f"value = {v}", q)

    def test_change_influence_clamps(self):
        b = block(read("common/scripted_effects/aov_artificer_faction_effects.txt"), "aov_faction_change_influence")
        self.assertIn("min = 0", b)
        self.assertIn("max = 100", b)
        self.assertIn("aov_faction_refresh_modifiers = yes", b)
```

- [ ] **Step 2: Run tests, expect FAIL.**
- [ ] **Step 3: Write the values.** Level, cost and quarters are `if/else_if` chains on `var:aov_influence_<f>` with the Global Constraints thresholds; quarters base Brillites 20, Mechanists 40, Technomancers 60 → ×1.25 = 25/50/75, ×0.75 = 15/30/45 (written as literal values).
- [ ] **Step 4: Write the 12 modifiers** with the spec table's values. Keys: `learning`, `martial`, `monthly_prestige_gain_mult`, `stress_gain_mult`, `monthly_lifestyle_xp_gain_mult`, `domain_tax_mult`, `build_speed` (positive = slower; "build time −15%" = `build_speed = -0.15`), `character_capital_county_monthly_development_growth_add`, `advantage`, `knight_effectiveness_mult`. Icons: Brillites `learning_positive`/`learning_negative`, Mechanists `stewardship_positive`/`stewardship_negative`, Technomancers `martial_positive`/`martial_negative`.
- [ ] **Step 5: Write the effects and level triggers** listed under Interfaces. `aov_faction_change_influence` uses `change_variable` then `clamp_variable = { name = aov_influence_$FACTION$ min = 0 max = 100 }`.
- [ ] **Step 6: Loc**: modifier names/descs (`aov_brillites_favored: "Favored by the Brillites"`, etc.), level names `AOV_LEVEL_HOSTILE` … `AOV_LEVEL_EXALTED`.
- [ ] **Step 7: Run tests + validate, expect PASS / clean.**
- [ ] **Step 8: Commit** `Add artificer faction influence and level modifiers`.

---

### Task 3: Research cost, duration and influence from sponsoring

**Files:**
- Modify: `common/scripted_effects/aov_artificery_research_effects.txt`, `common/scripted_triggers/aov_artificery_research_triggers.txt`, `common/scripted_guis/aov_artificery_research_sgui.txt`, `common/script_values/aov_artificery_values.txt`, `tools/build_inventions.py` (+ rerun), `localization/english/aov_artificery_l_english.yml`, `tools/tests/test_artificery_research.py`
- Test: `tools/tests/test_artificer_factions.py`

**Interfaces:**
- Consumes: Task 2 values and `aov_faction_change_influence`.
- Produces: trigger `aov_artificery_can_sponsor = { FACTION = <f> }` (= `aov_artificery_can_start_research` minus its gold check, plus `gold >= aov_research_cost_$FACTION$` under `aov_artificery_research_gold_tt`); variable `aov_research_paid`.

- [ ] **Step 1: Write the failing tests**

```python
class ResearchCostTests(unittest.TestCase):
    def test_common_start_pays_scaled_cost_and_shifts_influence(self):
        b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_start_research_common")
        self.assertIn("set_variable = { name = aov_research_paid value = aov_research_cost_$SPONSOR$ }", b)
        self.assertIn("value = aov_research_quarters_$SPONSOR$", b)
        self.assertIn("aov_faction_change_influence = { FACTION = $SPONSOR$ AMOUNT = 20 }", b)
        self.assertEqual(b.count("AMOUNT = -10"), 2)
        self.assertIn("custom_tooltip = aov_sponsor_influence_$SPONSOR$_tt", b)

    def test_refund_uses_paid_amount(self):
        b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_complete_research")
        self.assertIn("add_gold = var:aov_research_paid", b)
        self.assertNotIn("add_gold = aov_research_cost", b)

    def test_sponsor_sguis_check_their_faction(self):
        text = read("common/scripted_guis/aov_artificery_research_sgui.txt")
        self.assertIn("aov_artificery_can_sponsor = { FACTION = brillites }", block(text, "aov_research_brillites_sgui"))
        for c in ("economic", "military", "society"):
            self.assertIn("FACTION = mechanists", block(text, f"aov_research_mechanists_{c}_sgui"))
            self.assertIn("FACTION = technomancers", block(text, f"aov_research_technomancers_{c}_sgui"))
        gen = read("common/scripted_guis/aov_invention_sgui.txt")
        self.assertIn("aov_artificery_can_sponsor = { FACTION = technomancers }", block(gen, "aov_inv_sparkdrive_rifles_research_sgui"))
```

- [ ] **Step 2: Run tests, expect FAIL.**
- [ ] **Step 3: Change `aov_artificery_start_research_common`**: drop the `QUARTERS` parameter (callers pass only `SPONSOR`), pay `aov_research_cost_$SPONSOR$`, store `aov_research_paid`, set `aov_research_quarters_left` from `aov_research_quarters_$SPONSOR$`, +20 to the sponsor and −10 to each other faction (a three-way `if` on `flag:$SPONSOR$`), shown in the sGUI tooltip with `custom_tooltip = aov_sponsor_influence_$SPONSOR$_tt` and the changes themselves inside `hidden_effect`. Refund `var:aov_research_paid`; remove `aov_research_paid` in `aov_artificery_clear_research`.
- [ ] **Step 4: Triggers/sGUIs**: add `aov_artificery_can_sponsor`; remove the gold check from `aov_artificery_can_start_research` (it now gates opening the popup only); point every sponsor sGUI and the generator's `research_sgui` (`tools/build_inventions.py`, `sguis()`) at it; rerun `python -I tools/build_inventions.py`. Replace `aov_research_cost = 50` in `aov_artificery_values.txt` by nothing (the per-faction values replace it). Update `test_sponsor_durations` in `tools/tests/test_artificery_research.py` to assert `SPONSOR = brillites` / `mechanists` / `technomancers` calls instead of `QUARTERS =`.
- [ ] **Step 5: Loc**: replace `aov_artificery_research_gold_tt` by three keys `aov_artificery_research_gold_<f>_tt` = `"Has at least @gold_icon! [ROOT.Char.MakeScope.ScriptValue('aov_research_cost_<f>')|0] gold"`, used as `text = aov_artificery_research_gold_$FACTION$_tt`; add `aov_sponsor_influence_<f>_tt` = `"#P +20#! influence with the <Faction>, #N -10#! with the other two factions"`.
- [ ] **Step 6: Run tests + validate, expect PASS / clean.**
- [ ] **Step 7: Commit** `Scale research cost and time by faction influence`.

---

### Task 4: Quarterly drift, dormancy, inheritance, AI

**Files:**
- Create: `common/on_action/aov_artificer_faction_on_actions.txt`
- Modify: `common/scripted_effects/aov_artificer_faction_effects.txt`, `common/script_values/aov_artificer_faction_values.txt`, `common/scripted_effects/aov_artificery_research_effects.txt` (dormancy + inherit + AI hooks)
- Test: `tools/tests/test_artificer_factions.py`

**Interfaces:**
- Consumes: Task 2 effects.
- Produces: value `aov_opinion_drift_<f>` (−2…+2: `if = { limit = { exists = title:d_<f>.holder title:d_<f>.holder = { opinion = { target = root value >= 50 } } } value = 2 }` and so on for the bands, 0 if vacant); effect `aov_factions_quarterly = yes`; `aov_factions_inherit = yes` (heir scope, `scope:aov_predecessor`).

- [ ] **Step 1: Write the failing tests**

```python
class DriftTests(unittest.TestCase):
    def test_quarterly_applies_running_fade_and_opinion(self):
        b = block(read("common/scripted_effects/aov_artificer_faction_effects.txt"), "aov_factions_quarterly")
        for f in FACTIONS:
            self.assertIn(f"var:aov_research_sponsor = flag:{f}", b)
            self.assertIn(f"var:aov_influence_{f} > 40", b)
            self.assertIn(f"AMOUNT = aov_opinion_drift_{f}", b)

    def test_opinion_drift_bands(self):
        b = block(read("common/script_values/aov_artificer_faction_values.txt"), "aov_opinion_drift_brillites")
        self.assertIn("exists = title:d_brillites.holder", b)
        for cond in ("value >= 50", "value >= 20", "value <= -20", "value <= -50"):
            self.assertIn(f"opinion = {{ target = root {cond} }}", b)

    def test_dormancy_and_inheritance_hooked(self):
        eff = read("common/scripted_effects/aov_artificery_research_effects.txt")
        self.assertIn("aov_faction_remove_modifiers = yes", block(eff, "aov_artificery_update_dormancy"))
        self.assertIn("aov_faction_refresh_modifiers = yes", block(eff, "aov_artificery_update_dormancy"))
        self.assertIn("aov_factions_inherit = yes", block(eff, "aov_artificery_inherit"))

    def test_quarterly_on_action(self):
        text = read("common/on_action/aov_artificer_faction_on_actions.txt")
        self.assertIn("quarterly_playable_pulse = {\n\ton_actions = { aov_artificer_factions_quarterly }", text)
```

- [ ] **Step 2: Run tests, expect FAIL.**
- [ ] **Step 3: Implement** `aov_opinion_drift_<f>` and `aov_factions_quarterly` (per faction: +1 if sponsoring, −1 if above 40, then opinion drift, all through `aov_faction_change_influence`), the on_action `aov_artificer_factions_quarterly` (trigger `can_use_artificery_trigger = yes`; effect `aov_faction_init = yes` then `aov_factions_quarterly = yes`), dormancy hooks (suspend → `aov_faction_remove_modifiers`, resume → `aov_faction_refresh_modifiers`), `aov_factions_inherit` (copy each `aov_influence_<f>` from the predecessor when the heir lacks it, then refresh), called from `aov_artificery_inherit`; `aov_artificery_has_state` also true when `has_variable = aov_influence_brillites`.
- [ ] **Step 4: AI** in `aov_artificery_ai_research`: before the existing random list, if a faction is at level ≤ 1 and `aov_artificery_can_sponsor = { FACTION = <f> }`, sponsor that faction (Brillites → random invention, Mechanists → random discoverable field, Technomancers → roll offers + `aov_inventions_ai_start_technomancers_<field>`). In `aov_artificery_ai_quarterly`: for each faction at level 0 with `gold > 300`, run the Make Amends effect from Task 6 (`aov_faction_make_amends = { FACTION = <f> }`; define it here, Task 6 adds the sGUI).
- [ ] **Step 5: Run tests + validate, expect PASS / clean.**
- [ ] **Step 6: Commit** `Add quarterly faction influence drift, dormancy and inheritance`.

---

### Task 5: Elections

**Files:**
- Create: `common/scripted_effects/aov_artificer_election_effects.txt`, `common/event_themes/aov_artificery_event_themes.txt`, `events/aov_artificer_faction_events.txt`
- Modify: `common/scripted_triggers/aov_artificer_faction_triggers.txt`, `common/script_values/aov_artificer_faction_values.txt`, `common/on_action/aov_artificer_faction_on_actions.txt`, `localization/english/aov_artificer_factions_l_english.yml`
- Test: `tools/tests/test_artificer_factions.py`

**Interfaces:**
- Consumes: `aov_vote_weight_<f>` (Task 2), `aov_is_artificer_faction_title` (Task 1).
- Produces:
  - triggers `aov_faction_candidate_trigger` (character: gnome, adult, alive, not imprisoned, `is_ruler = no`, holds no faction title), `aov_artificer_nation_trigger` (= `can_use_artificery_trigger = yes`);
  - values `aov_candidate_score_<f>`;
  - effects `aov_election_open = { FACTION = <f> }`, `aov_election_cast_vote = { FACTION = <f> CANDIDATE = <scope> }` (root = voter), `aov_election_ai_vote = { FACTION = <f> }` (root = voter), `aov_election_resolve = { FACTION = <f> }`, `aov_faction_grant_title = { FACTION = <f> WINNER = <scope> }`;
  - global state: list `aov_candidates_<f>`, variable `aov_election_open_<f>`, timed variable `aov_election_running_<f>` (`days = 30`), candidate variable `aov_votes_<f>`, voter variable `aov_voted_<f>`;
  - events `aov_artificer_factions.1` (vote, one per faction via `scope:aov_election_faction` = `flag:<f>`), `.2` (result).

- [ ] **Step 1: Write the failing tests**

```python
class ElectionTests(unittest.TestCase):
    def eff(self, name):
        return block(read("common/scripted_effects/aov_artificer_election_effects.txt"), name)

    def test_open_picks_exactly_three_with_world_fallback(self):
        b = self.eff("aov_election_open")
        self.assertIn("clear_global_variable_list = aov_candidates_$FACTION$", b)
        self.assertIn("max = 3", b)
        self.assertIn("order_by = aov_candidate_score_$FACTION$", b)
        self.assertIn("every_living_character", b)          # top-up from anywhere
        self.assertIn("name = aov_election_running_$FACTION$ days = 30", b)
        self.assertIn("trigger_event = aov_artificer_factions.1", b)

    def test_vote_adds_weight_and_marks_voter(self):
        b = self.eff("aov_election_cast_vote")
        self.assertIn("save_temporary_scope_value_as = { name = aov_vote_weight value = aov_vote_weight_$FACTION$ }", b)
        self.assertIn("add = scope:aov_vote_weight", b)
        self.assertIn("set_variable = aov_voted_$FACTION$", b)

    def test_resolve_skips_dead_candidates(self):
        self.assertIn("is_alive = yes", self.eff("aov_election_resolve"))

    def test_resolve_skips_current_holders(self):
        self.assertIn("aov_faction_candidate_trigger = yes", self.eff("aov_election_resolve"))

    def test_auto_votes_only_for_living_eligible_voters(self):
        b = self.eff("aov_election_resolve")
        self.assertRegex(b, r"every_ruler = \{\s*limit = \{\s*aov_artificer_nation_trigger = yes\s*NOT = \{ has_variable = aov_voted_\$FACTION\$ \}")

    def test_vote_event_shows_three_candidates_and_highlights(self):
        ev = read("events/aov_artificer_faction_events.txt")
        b = block(ev, "aov_artificer_factions.1")
        for slot in ("lower_left_portrait", "lower_center_portrait", "lower_right_portrait"):
            self.assertIn(slot, b)
        for n in (1, 2, 3):
            self.assertIn(f"highlight_portrait = scope:aov_candidate_{n}", b)
        self.assertIn("theme = aov_artificery", b)

    def test_on_death_and_game_start(self):
        text = read("common/on_action/aov_artificer_faction_on_actions.txt")
        self.assertIn("on_death = {\n\ton_actions = { aov_artificer_factions_on_death }", text)
        self.assertIn("on_game_start_after_lobby = {\n\ton_actions = { aov_artificer_factions_game_start }", text)
        self.assertIn("yearly_global_pulse = {\n\ton_actions = { aov_artificer_factions_yearly }", text)
```

- [ ] **Step 2: Run tests, expect FAIL.**
- [ ] **Step 3: Event theme** `aov_artificery`: icon `gfx/interface/icons/event_types/type_inspiration.dds`, header `gfx/interface/window_event/event_header_yellow.dds`, sound `event:/SFX/Events/Themes/sfx_event_theme_type_learning`, background reference `bp2_university` (format of vanilla `learning` in `common/event_themes/00_event_themes.txt`).
- [ ] **Step 4: Candidates and open.** `aov_election_open`: clear the list and every old `aov_votes_$FACTION$` / `aov_voted_$FACTION$`; add the top 3 `aov_faction_candidate_trigger` courtiers of `aov_artificer_nation_trigger` rulers by `aov_candidate_score_$FACTION$`; while the list has fewer than 3, add the best remaining from `every_living_character` (gnome, adult, `aov_faction_candidate_trigger`, unlanded ordered first via a second pass). Empty list → `set_global_variable = aov_election_retry_$FACTION$` and stop. No nations → `aov_faction_grant_title` with the best candidate at once. Otherwise set `aov_election_open_$FACTION$`, the 30-day timed variable, and `trigger_event = aov_artificer_factions.1` on every nation (saving `scope:aov_election_faction = flag:$FACTION$` first), and `trigger_event = { id = aov_artificer_factions.3 days = 30 }` on the highest-weight nation (`.3` is a hidden event that calls `aov_election_resolve` for the faction in `scope:aov_election_faction`).
- [ ] **Step 5: Vote event `.1`** (`type = character_event`, `theme = aov_artificery`): `immediate` saves `scope:aov_candidate_1..3` from `ordered_in_global_list` of the faction's list (`position = 0/1/2`, order by score) and `scope:aov_late_leader` from `global_var:aov_late_leader_<f>` if set; portraits `left_portrait = root`, `right_portrait = scope:aov_late_leader`, lower left/center/right = candidates 1–3; options per candidate (`trigger = { exists = scope:aov_candidate_N }`, `highlight_portrait`, effect `aov_election_cast_vote`, `ai_chance` 100 if the candidate is root's courtier else `aov_candidate_score`); the effect switch on `scope:aov_election_faction` picks the `FACTION` value. Result event `.2`: `type = character_event`, same theme, `left_portrait` = winner, desc names faction and winner, one option.
- [ ] **Step 6: Resolve and grant.** `aov_election_resolve`: return if `aov_election_open_$FACTION$` is not set; `aov_election_ai_vote` for every nation that has not voted; pick the living `aov_faction_candidate_trigger` candidate with the most `aov_votes_$FACTION$` (ties → score); none valid → `aov_election_open` again; else `aov_faction_grant_title` and `.2` to every nation; clear state. `aov_faction_grant_title`: `create_title_and_vassal_change = { type = created save_scope_as = change add_claim_on_loss = no }`, `title:d_$FACTION$ = { change_title_holder = { holder = $WINNER$ change = scope:change } }`, `resolve_title_and_vassal_change = scope:change` (vanilla `introduce_court_fashion_events.txt` k_fashion pattern).
- [ ] **Step 7: Hooks.** `aov_artificer_factions_on_death` (trigger: holds a faction title): for each held faction title, `set_global_variable = { name = aov_late_leader_<f> value = root }`, `destroy_title = title:d_<f>` (vanilla `death.txt` e_mongol_empire precedent), `aov_election_open = { FACTION = <f> }`. Also: if the dying character is the scheduled resolver, the quarterly pulse covers it — add to `aov_artificer_factions_quarterly`: for each faction, if `aov_election_open_<f>` exists and `aov_election_running_<f>` does not, `aov_election_resolve`. `aov_artificer_factions_game_start` and `aov_artificer_factions_yearly`: for each faction with no holder and no open election, `aov_election_open`.
- [ ] **Step 8: Loc** for `.1` (title "The [faction] Elects a Leader", desc with the three candidates via `[aov_candidate_1.GetName]` and their liege), options `"Vote for [aov_candidate_1.GetShortUIName]"`, `.2`, and option tooltip `AOV_VOTE_WEIGHT_TT` showing `[ROOT.Char.MakeScope.ScriptValue('aov_vote_weight_brillites')]` per faction (three keys).
- [ ] **Step 9: Run tests + validate, expect PASS / clean.**
- [ ] **Step 10: In-game check (user):** console `kill <Brillite leader id>`; within a day the vote panel appears with three portraits; hovering an option highlights its candidate; after 30 days the result event fires and the winner holds `d_brillites` and is still their liege's vassal. If `destroy_title` + regrant fails (title missing or not given), switch Step 7 to the spec's fallback: skip `destroy_title`, set `aov_interim_holder` on the heir after inheritance (`on_title_gain` is not needed: read `title:d_<f>.holder` in `aov_election_resolve`) and transfer at the count.
- [ ] **Step 11: Commit** `Add artificer faction elections`.

---

### Task 6: Factions tab and Make Amends

**Files:**
- Create: `gui/aov_artificer_factions.gui`, `common/scripted_guis/aov_artificer_faction_sgui.txt`
- Modify: `gui/aov_window_artificery.gui` (Factions body), `localization/english/aov_artificer_factions_l_english.yml`, `localization/english/aov_artificery_l_english.yml` (drop `AOV_ARTIFICERY_FACTIONS_PLACEHOLDER`)
- Test: `tools/tests/test_artificer_factions.py`, `tools/tests/test_artificery_window.py`

**Interfaces:**
- Consumes: Task 2 values, Task 4 `aov_faction_make_amends`, Task 5 election variables.
- Produces: sGUIs `aov_make_amends_<f>_sgui` (`is_valid`: `var:aov_influence_<f> < 40` under `aov_make_amends_below_40_tt`, `gold >= 100` under `aov_make_amends_gold_tt`; effect `aov_faction_make_amends`), `aov_faction_<f>_has_holder_sgui`, `aov_faction_<f>_election_sgui`; GUI types `aov_faction_card` (blocks `title_key`, `faction`, `description`) and `aov_influence_bar` (block `value`).

- [ ] **Step 1: Write the failing tests**

```python
class FactionsTabTests(unittest.TestCase):
    def test_make_amends_caps_at_forty(self):
        b = block(read("common/scripted_effects/aov_artificer_faction_effects.txt"), "aov_faction_make_amends")
        self.assertIn("add_gold = -100", b)
        self.assertIn("max = 40", b)

    def test_tab_has_three_cards(self):
        win = read("gui/aov_window_artificery.gui")
        self.assertNotIn("AOV_ARTIFICERY_FACTIONS_PLACEHOLDER", win)
        self.assertEqual(win.count("aov_faction_card = {"), 3)
        for f in FACTIONS:
            self.assertIn(f"GetTitleByKey('d_{f}')", win)
            self.assertIn(f"aov_make_amends_{f}_sgui", win)

    def test_bar_markers_at_thresholds(self):
        gui = read("gui/aov_artificer_factions.gui")
        self.assertIn("type aov_influence_bar", gui)
        self.assertEqual(gui.count("widget_level_marker = {"), 4)
        for x in ("15%", "30%", "60%", "85%"):
            self.assertIn(x, gui)
```

- [ ] **Step 2: Run tests, expect FAIL.**
- [ ] **Step 3: `aov_influence_bar`**: a `widget` 0×15 expanding with a `progressbar_standard` (`min = 0`, `max = 100`, `value = "[FixedPointToFloat( <block value> )]"`) and four `widget_level_marker` children placed by `position` at 15/30/60/85 % of the bar width (use a `hbox` of proportional spacer widgets with `layoutstretchfactor_horizontal` 15/15/30/25/15 so the markers sit between them), each with `blockoverride "visible_active"` = current level matches, `"visible_inactive"` its negation, `"marker_text"` the level's Roman numeral, `"marker_tooltip"` = level tooltip key `AOV_LEVEL_<LEVEL>_<F>_TT` (modifier via `[GetModifier('aov_<f>_<level>').GetDescWithEffects]`, cost, time). Bar tooltip `AOV_INFLUENCE_<F>_TT`: value, level, leader opinion (`[GetTitleByKey('d_<f>').GetHolder.GetOpinionOf( GetPlayer )]`), drift per quarter (`aov_opinion_drift_<f>`).
- [ ] **Step 4: `aov_faction_card`**: vbox with `Background_Area_With_Header`; hbox of `coa_title_medium` (`datacontext` = the title), `portrait_head` (`datacontext = "[Title.GetHolder]"`, visible when `Title.HasHolder`), name + holder title text, or "Vacant — election under way" (`aov_faction_<f>_election_sgui`) / "Vacant"; faction name and one-line description; `aov_influence_bar`; a line with level name and current cost; `button_standard` Make Amends (enabled/tooltip/onclick from its sGUI).
- [ ] **Step 5: Factions body** in `gui/aov_window_artificery.gui`: replace the placeholder text with a scrollbox containing the three cards in faction order.
- [ ] **Step 6: Loc** for all keys referenced.
- [ ] **Step 7: Run tests + validate, expect PASS / clean.** Update `tools/tests/test_artificery_window.py` if it asserts on the placeholder.
- [ ] **Step 8: Commit** `Add Factions tab with influence bars and Make Amends`.

---

### Task 7: Research popup shows real leaders and costs

**Files:**
- Modify: `gui/aov_window_artificery_research.gui`, `localization/english/aov_artificery_l_english.yml`, `tools/tests/test_artificery_window.py`

**Interfaces:**
- Consumes: Task 2 `aov_research_cost_<f>`, Task 1 titles.

- [ ] **Step 1: Write the failing test** in `test_artificery_window.py`:

```python
    def test_research_popup_uses_title_holders_and_faction_costs(self):
        popup = (WINDOW.parent / "aov_window_artificery_research.gui").read_text(encoding="utf-8-sig")
        self.assertNotIn('datacontext = "[GetPlayer]"', popup)
        for f in ("brillites", "mechanists", "technomancers"):
            self.assertIn(f"GetTitleByKey('d_{f}').GetHolder", popup)
            self.assertIn(f"AOV_RESEARCH_COST_{f.upper()}", popup)
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement**: each `aov_research_leader` gets `datacontext = "[GetTitleByKey('d_<f>').GetHolder]"` and `visible` on `GetTitleByKey('d_<f>').HasHolder`; a sibling nameplate "Vacant" shows otherwise. Sponsor options use `AOV_RESEARCH_COST_<F>` (`"@gold_icon! [GetPlayer.MakeScope.ScriptValue('aov_research_cost_<f>')|0]"`) for the Brillites option, the Mechanist field options and Technomancer offers (the generated offers in `tools/build_inventions.py` `offer_option()` switch from `AOV_RESEARCH_COST` to `AOV_RESEARCH_COST_TECHNOMANCERS`; rerun the generator). Remove the placeholder comment.
- [ ] **Step 4: Run tests + validate, expect PASS / clean.**
- [ ] **Step 5: Commit** `Show faction leaders and costs in the research popup`.

---

### Task 8: Documentation and full verification

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md**: Systems → add **Artificer factions** (titles, elections, influence, Factions tab, file names); Updating to a new Anbennar version → add "re-copy `title_revocation_standard_can_pick_title_trigger` into `common/scripted_triggers/zz_aov_interaction_triggers.txt`"; replace the research popup's placeholder-leaders note.
- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -v` and `python -I tools/validate.py`; expect all `ok` and a clean tiger line.
- [ ] **Step 3: In-game checklist (user)**, new campaign with a gnomish Artificer Academy ruler:
  1. The three titles have holders after the game start election (30 days); Revoke Title does not list them.
  2. Factions tab: CoA, portrait, bar at 40 (Neutral marker glowing), cost 50.
  3. Sponsor the Brillites → Brillites 60 (Favored, modifier present, cost 38), others 30.
  4. Make Amends on a faction below 40 → +10, never above 40; disabled at 40.
  5. `add_opinion` from a leader to you of +60 → that faction +2 next quarter.
  6. Kill a leader → vote panel with three candidates → result after 30 days.
  7. `error.log` / `gui_warnings.log` have no new `aov_` lines.
- [ ] **Step 4: Commit** `Document artificer factions`.
