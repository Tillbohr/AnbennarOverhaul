# Magic Lifestyle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Anbennar's stub `magic_lifestyle` into a full lifestyle (3 trees × 9 perks, 3 focuses, 3 traits, art, GUI)
whose perks boost the magic-school system through one script-value layer.

**Architecture:** Hand-written perks, traits, focuses and a bonus layer (`aov_magic_lifestyle_values.txt`) that is the
only place reading perks for magic. The school code (hand-written values/effects and the `build_spells.py` generator)
reads that layer: per-spell cost and duration become generated script values. Two new generators produce the
whole-file lifestyle window override and the art.

**Tech Stack:** CK3 1.19.0.6 script, PdxGui, ck3-tiger (`python -I tools/validate.py`), Python `unittest` in `tools/tests/`.

**Spec:** `docs/superpowers/specs/2026-10-08-magic-lifestyle-design.md` (perk tables, numbers and art sources are there;
this plan does not repeat the perk tables).

## Global Constraints

- Script/loc/gui files: UTF-8 with BOM, LF, tabs. Python/Markdown: LF, written with `write_bytes`.
- Base Anbennar is never edited. New files `aov_`/`zz_aov_`-prefixed except art paths CK3 derives from keys.
- Generated files carry the "generated ... do not edit by hand" header; never hand-edit them.
- Schools in this order everywhere: `abjuration, conjuration, divination, enchantment, evocation, illusion, necromancy, transmutation`.
- School → tree/focus: divination, abjuration, transmutation → `aov_arcane_scholar` / `magic_arcane_study_focus`;
  evocation, conjuration → `aov_battle_mage` / `magic_duelist_focus`; enchantment, illusion, necromancy →
  `aov_mindweaver` / `magic_mindweaving_focus`.
- Bonus amounts: focus study +0.25, perk study +0.25, trait study +0.10 (Arcane Scholar, all schools); perk cost cut 0.25;
  trait cost cut 0.25 (Battle Mage: war; Mindweaver: targeted); cost floor 0.5; perk duration ×1.5; mana +50 (Arcane
  Reservoir) +50 (Arcane Scholar trait); refill +0.25 (Ley Lines), +1.0 at war (Battle Meditation); dark magic ×0.5
  (Grave Whispers).
- Rounding is half up: `add = 0.5` then `floor = yes`.
- School progress from a cast stays at the spell's **base** cost; magic lifestyle XP from a cast = base cost.
- Lifestyle XP effect `add_magic_lifestyle_xp` (engine-generated; Anbennar has effect loc for it).

## Review Focus

1. A mage with every cost perk and trait casts a war Evocation spell: cost is exactly half base (floor), never lower,
   never negative mana. *(Task 3 test `test_cost_value_has_floor`.)*
2. A mage loses a perk's prerequisites (affinity removed, lifestyle invalid): bonus values fall back to neutral
   because they only read `has_perk`/`has_trait`/`has_focus`; nothing reads a stale variable. *(Task 2 test
   `test_bonus_layer_reads_only_perks_traits_focuses`.)*
3. Duration rounding at the boundaries (1→2, 5→8) and the cooldown always equals the modifier duration, so a
   spell cannot be recast while active. *(Task 3 test `test_cooldown_and_modifier_share_years_value`.)*
4. Summon Elementals with Bound Elementals: the army lasts as long as the spell's cooldown, not a fixed 3 years.
   *(Task 3 test `test_elementals_follow_spell_years`.)*
5. An Anbennar update changes the lifestyle window: the GUI generator must stop with an error rather than ship a
   half-patched window. *(Task 4 test `test_errors_when_anchor_count_changes`.)*

---

### Task 1: Perks, traits, focuses and loc

**Files:**
- Create: `common/lifestyle_perks/aov_magic_arcane_scholar_perks.txt`, `common/lifestyle_perks/aov_magic_battle_mage_perks.txt`,
  `common/lifestyle_perks/aov_magic_mindweaver_perks.txt`, `common/traits/aov_magic_lifestyle_traits.txt`,
  `common/focuses/zz_aov_magic_focuses.txt`, `common/modifier_definition_formats/aov_magic_lifestyle_formats.txt`,
  `localization/english/aov_magic_lifestyle_l_english.yml`,
  `localization/replace/english/aov_magic_lifestyle_replace_l_english.yml`
- Modify: `common/scripted_effects/aov_magic_effects.txt` (`aov_magic_sync_mastery`), `common/script_values/aov_magic_values.txt` (`aov_magic_mastery_value`)
- Test: `tools/tests/test_magic_lifestyle.py`

**Interfaces:**
- Produces: perk keys exactly as in the spec tables (27, `aov_*_perk`), tree keys `aov_arcane_scholar`, `aov_battle_mage`,
  `aov_mindweaver`; trait keys `arcane_scholar`, `battle_mage`, `mindweaver`; focus keys `magic_arcane_study_focus`,
  `magic_duelist_focus`, `magic_mindweaving_focus`.
- Every perk has `effect = { custom_description_no_bullet = { text = <perk>_effect } aov_magic_sync_mastery = yes }`
  (final perks: `add_trait_force_tooltip = <trait>` instead of the description, plus the sync and `trait = <trait>`).
- `aov_magic_sync_mastery` also sets `magic_lifestyle_total_points = magic_lifestyle_perks`;
  `aov_magic_mastery_value` adds `magic_lifestyle_perks`.

- [ ] **Step 1: Write the failing tests** in `tools/tests/test_magic_lifestyle.py`. Reuse `read`/`block` from
  `test_magic_system.py` (copy the two helpers); parse perks with
  `re.finditer(r"^(\w+_perk) = \{\n(.*?)\n^\}", text, re.M | re.S)`. Keep a module constant `TREES` mapping each tree key
  to its 9 perk keys in the spec's table order, `TRAIT_OF = {"aov_arcane_scholar": "arcane_scholar", ...}`,
  `FINAL_PERKS = {keys[8] for keys in TREES.values()}`, `SCHOOLS` (as in `test_magic_system.py`), `FOCUS_OF`
  (school → focus, Global Constraints) and `all_perks()` (perk key → body, from the three perk files).

```python
LAYOUT = [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2), (1, 3), (1, 4), (1, 5)]
PARENTS = [[], [0], [1], [], [3], [4], [2, 5], [6], [7]]   # indices into the tree's perk list

class PerkTests(unittest.TestCase):
    def test_three_trees_of_nine(self):
        perks = all_perks()                              # {key: body} from the three files
        self.assertEqual(len(perks), 27)
        for tree, keys in TREES.items():
            for k in keys:
                self.assertIn(f"tree = {tree}", perks[k])
                self.assertIn("lifestyle = magic_lifestyle", perks[k])

    def test_vanilla_layout_and_parents(self):
        for tree, keys in TREES.items():
            for i, k in enumerate(keys):
                body = all_perks()[k]
                x, y = LAYOUT[i]
                self.assertIn(f"position = {{ {x} {y} }}", body)
                self.assertEqual(sorted(re.findall(r"parent = (\w+)", body)), sorted(keys[p] for p in PARENTS[i]))

    def test_final_perk_grants_trait(self):
        for tree, keys in TREES.items():
            body = all_perks()[keys[8]]
            self.assertIn(f"trait = {TRAIT_OF[tree]}", body)
            self.assertIn(f"add_trait_force_tooltip = {TRAIT_OF[tree]}", body)
            self.assertIn(f"icon = trait_{TRAIT_OF[tree]}", body)

    def test_every_perk_syncs_mastery(self):
        for k, body in all_perks().items():
            self.assertIn("aov_magic_sync_mastery = yes", body, k)

    def test_root_perks_respect_new_tree_rule(self):
        for keys in TREES.values():
            for root in (keys[0], keys[3]):
                self.assertIn("can_start_new_lifestyle_tree_trigger = no", all_perks()[root])

class TraitFocusTests(unittest.TestCase):
    def test_traits_are_lifestyle(self):
        t = read("common/traits/aov_magic_lifestyle_traits.txt")
        for k in ("arcane_scholar", "battle_mage", "mindweaver"):
            self.assertIn("category = lifestyle", block(t, k))

    def test_focuses(self):
        f = read("common/focuses/zz_aov_magic_focuses.txt")
        for k in ("magic_arcane_study_focus", "magic_duelist_focus", "magic_mindweaving_focus"):
            self.assertIn("lifestyle = magic_lifestyle", block(f, k))
        self.assertIn("prowess = 3", block(f, "magic_duelist_focus"))
        self.assertIn("martial = 1", block(f, "magic_duelist_focus"))

class LocTests(unittest.TestCase):
    def test_every_key_has_loc(self):
        loc = read("localization/english/aov_magic_lifestyle_l_english.yml")
        keys = [f"{p}_name" for p in all_perks()] + [f"{p}_effect" for p in all_perks() if not p in FINAL_PERKS]
        keys += [f"{t}_name" for t in TREES]                                  # tree names
        keys += [f"trait_{t}" for t in TRAIT_OF.values()] + [f"trait_{t}_desc" for t in TRAIT_OF.values()]
        for f in ("magic_arcane_study_focus", "magic_mindweaving_focus"):
            keys += [f, f"{f}_desc", f"{f}_modifier"]
        keys += ["monthly_magic_lifestyle_xp_gain_mult"]
        for k in keys:
            self.assertRegex(loc, rf"(?m)^ {re.escape(k)}:", k)
        rep = read("localization/replace/english/aov_magic_lifestyle_replace_l_english.yml")
        self.assertIn(' magic_duelist_focus: "Battle Mage Focus"', rep)

class MasteryTests(unittest.TestCase):
    def test_mastery_counts_perks(self):
        self.assertIn("add = magic_lifestyle_perks", block(read("common/script_values/aov_magic_values.txt"), "aov_magic_mastery_value"))
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_magic_sync_mastery")
        self.assertIn("name = magic_lifestyle_total_points", b)
```

- [ ] **Step 2: Run** `python -I -m unittest tools.tests.test_magic_lifestyle -v` from `tools/..`
  (or `discover -s tools/tests -p test_magic_lifestyle.py`). Expected: FAIL (files missing).

- [ ] **Step 3: Write the content.**
  - Perks: shape of vanilla `game/common/lifestyle_perks/00_learning_2_scholarship_tree_perks.txt` (`icon = node_magic`;
    final perk `icon = trait_<trait>`). `character_modifier` holds each perk's "Other modifiers" column from the spec.
    `auto_selection_weight`: `value = 11`; `add = 1989` if the mage studies a school of this tree
    (`aov_is_studying = { SCHOOL = <s> }`, OR over the tree's schools); `multiply = 5` if `has_focus = <tree focus>`;
    roots `multiply = 0` under `can_start_new_lifestyle_tree_trigger = no` unless the sibling root is taken (vanilla pattern).
    Battle Meditation, Arcane Reservoir, Bound Elementals and Grave Whispers have no `character_modifier` (magic-only).
  - Traits: copy the shape of vanilla `scholar` (`game/common/traits/00_traits.txt`): `category = lifestyle`, the spec's
    modifiers, `desc = trait_<key>_desc`, `icon = <key>.dds` resolved by default path.
  - Focuses: `magic_duelist_focus` keeps Anbennar's `desc` block and weight shape, adds `martial = 1`; the two new
    focuses mirror it. All three `auto_selection_weight`s add 1989 when the mage studies a school of their tree.
  - Formats: `monthly_magic_lifestyle_xp_gain_mult = { percent = yes }` (copy the shape of vanilla
    `monthly_learning_lifestyle_xp_gain_mult` from `game/common/modifier_definition_formats/00_modifier_definition_formats.txt`).
  - Loc: perk `_name`, perk `_effect` lines stating the magic bonus (e.g. `aov_diviners_eye_perk_effect: "Study of
    $AOV_SCHOOL_DIVINATION$ is #P 25%#! faster"`), tree `_name`s ("Arcane Scholar", "Battle Mage", "Mindweaver"),
    trait name/desc, new focus name/desc/`_modifier`/`_effect_desc`, the XP modifier name; replace file renames
    `magic_duelist_focus` to "Battle Mage Focus" and `magic_duelist_focus_desc` to "Spells and steel, side by side.".
  - Mastery: `aov_magic_mastery_value` gains `add = magic_lifestyle_perks`; `aov_magic_sync_mastery` adds
    `set_variable = { name = magic_lifestyle_total_points value = magic_lifestyle_perks }`.

- [ ] **Step 4: Run the tests.** Expected: PASS. Then `python -I tools/validate.py`. Expected: ends
  `fatal: 0, error: 0` (lifestyle icons are missing until Task 5; tiger does not report DDS by default — if it does,
  note the reports and expect Task 5 to clear them). Any modifier key tiger rejects: replace with the closest valid
  key and record it in the spec's perk table.

- [ ] **Step 5: Commit** `git add` the files above; message `Add magic lifestyle perks, traits and focuses`.

---

### Task 2: Bonus layer and school wiring

**Files:**
- Create: `common/script_values/aov_magic_lifestyle_values.txt`
- Modify: `common/script_values/aov_magic_values.txt` (`aov_mana_max`, `aov_mana_refill_month`, new per-school study values),
  `common/scripted_effects/aov_magic_effects.txt` (`aov_magic_quarterly`, `aov_dark_magic_roll`, new `aov_mana_spend`),
  `localization/english/aov_magic_l_english.yml` (`AOV_MAGIC_MANA_TT`, `AOV_MAGIC_STUDYING`)
- Test: `tools/tests/test_magic_lifestyle.py`, `tools/tests/test_magic_system.py`

**Interfaces:**
- Consumes: Task 1 perk/trait/focus keys.
- Produces (character scope): `aov_study_mult_<s>`, `aov_cost_cut_<s>`, `aov_years_mult_<s>` (8 each),
  `aov_cost_cut_war`, `aov_cost_cut_targeted`, `aov_mana_max_bonus`, `aov_mana_refill_mult`, `aov_dark_magic_mult`;
  `aov_study_gain_<s>_month` (8) and `aov_study_gain_current_month` (the studied school's rate, 0 if none);
  scripted effect `aov_mana_spend = { AMOUNT = <value> }` (subtracts, clamps 0..max).

- [ ] **Step 1: Write the failing tests** (add to `test_magic_lifestyle.py`; `MAPS` = the spec's school → perk maps for
  study, cost and duration, built from the perk tables).

```python
class BonusLayerTests(unittest.TestCase):
    def v(self):
        return read("common/script_values/aov_magic_lifestyle_values.txt")

    def test_school_values_name_their_perks(self):
        for s in SCHOOLS:
            self.assertIn(f"has_perk = {STUDY_PERK[s]}", block(self.v(), f"aov_study_mult_{s}"))
            self.assertIn(f"has_focus = {FOCUS_OF[s]}", block(self.v(), f"aov_study_mult_{s}"))
            self.assertIn("has_trait = arcane_scholar", block(self.v(), f"aov_study_mult_{s}"))
            self.assertIn(f"has_perk = {COST_PERK[s]}", block(self.v(), f"aov_cost_cut_{s}"))
            if s in YEARS_PERK:
                self.assertIn(f"has_perk = {YEARS_PERK[s]}", block(self.v(), f"aov_years_mult_{s}"))
            else:
                self.assertEqual(block(self.v(), f"aov_years_mult_{s}").strip(), "value = 1")

    def test_bonus_layer_reads_only_perks_traits_focuses(self):
        refs = set(re.findall(r"has_(?:perk|trait|focus) = (\w+)", self.v()))
        self.assertTrue(refs <= set(all_perks()) | set(TRAIT_OF.values()) | set(FOCUS_OF.values()))
        self.assertNotIn("var:", self.v())

    def test_mana_and_dark_magic(self):
        self.assertIn("has_perk = aov_arcane_reservoir_perk", block(self.v(), "aov_mana_max_bonus"))
        self.assertIn("has_trait = arcane_scholar", block(self.v(), "aov_mana_max_bonus"))
        b = block(self.v(), "aov_mana_refill_mult")
        self.assertIn("has_perk = aov_ley_lines_perk", b)
        self.assertIn("is_at_war = yes", b)
        self.assertIn("has_perk = aov_grave_whispers_perk", block(self.v(), "aov_dark_magic_mult"))
        self.assertIn("has_trait = battle_mage", block(self.v(), "aov_cost_cut_war"))
        self.assertIn("has_trait = mindweaver", block(self.v(), "aov_cost_cut_targeted"))

class WiringTests(unittest.TestCase):
    def test_values_use_layer(self):
        v = read("common/script_values/aov_magic_values.txt")
        self.assertIn("add = aov_mana_max_bonus", block(v, "aov_mana_max"))
        self.assertIn("multiply = aov_mana_refill_mult", block(v, "aov_mana_refill_month"))
        for s in SCHOOLS:
            self.assertIn(f"multiply = aov_study_mult_{s}", block(v, f"aov_study_gain_{s}_month"))

    def test_quarterly_uses_per_school_gain(self):
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_magic_quarterly")
        for s in SCHOOLS:
            self.assertIn(f"aov_study_gain_{s}_month", b)

    def test_dark_magic_scaled(self):
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_dark_magic_roll")
        self.assertEqual(b.count("multiply = aov_dark_magic_mult"), 2)

    def test_mana_spend_clamps(self):
        b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_mana_spend")
        self.assertIn("subtract = $AMOUNT$", b)
        self.assertIn("min = 0", b)
```

  In `test_magic_system.py`, update `test_quarterly_ticks_three_months` if it asserts `aov_study_gain_month` inside
  the quarterly block (it now uses the per-school values).

- [ ] **Step 2: Run** both test files. Expected: the new tests FAIL.

- [ ] **Step 3: Implement.**
  - Layer values: `value = 1` (mults) or `value = 0` (cuts/bonus) plus one `if = { limit = { has_perk = … } add = … }`
    per source; `aov_mana_refill_mult` Battle Meditation limit is `has_perk = aov_battle_meditation_perk is_at_war = yes`;
    `aov_dark_magic_mult` = 1, `multiply = 0.5` with Grave Whispers. Schools with no duration perk: `value = 1` only.
  - `aov_mana_max`: `add = aov_mana_max_bonus`. `aov_mana_refill_month`: trailing `multiply = aov_mana_refill_mult`.
  - `aov_study_gain_<s>_month = { value = aov_study_gain_month multiply = aov_study_mult_<s> }`;
    `aov_study_gain_current_month`: 0, then one `if` per school on `aov_is_studying = { SCHOOL = <s> }`.
  - `aov_magic_quarterly`: drop the shared `aov_study_quarter`; each school's branch passes
    `AMOUNT = { value = aov_study_gain_<s>_month multiply = 3 }` (save as a temporary scope value per branch if the
    inline block is rejected by tiger).
  - `aov_dark_magic_roll`: `chance = { value = 25 multiply = aov_dark_magic_mult }` and the same for 10.
  - `aov_mana_spend`: like `aov_mana_change` but `change_variable = { name = aov_mana subtract = $AMOUNT$ }`.
  - Loc: `AOV_MAGIC_STUDYING` shows `aov_study_gain_current_month`; `AOV_MAGIC_MANA_TT` appends "Magic lifestyle perks
    raise these." and changes "Spells cost 25, 50, 100 or 200 mana by level" to "… by level, before perks".

- [ ] **Step 4: Run** all tool tests and `python -I tools/validate.py`. Expected: PASS; `fatal: 0, error: 0`.

- [ ] **Step 5: Commit** `Add magic lifestyle bonus layer and wire it into mana and study`.

---

### Task 3: Per-spell cost and duration values in `build_spells.py`

**Files:**
- Modify: `tools/build_spells.py` (`triggers`, `effects`, `card`, `loc`, `render_all`; new `values`), `tools/data/spells.py`
  (Summon Elementals `desc`), `common/scripted_effects/aov_magic_effects.txt` (`aov_summon_elementals`)
- Generated (rerun): `common/script_values/aov_spell_values.txt` (new) and the existing generated spell files
- Test: `tools/tests/test_build_spells.py`

**Interfaces:**
- Consumes: Task 2 `aov_cost_cut_<s>`, `aov_cost_cut_war`, `aov_cost_cut_targeted`, `aov_years_mult_<s>`, `aov_mana_spend`.
- Produces: `values(spells) -> str`; per spell `aov_spell_<k>_cost`, `aov_spell_<k>_years`; loc keys
  `aov_spell_<k>_facts`, `aov_spell_<k>_req_mana`, `aov_spell_<k>_cost_tt` (replacing `AOV_SPELL_FACTS_*`,
  `AOV_SPELL_REQ_MANA_*`, `AOV_SPELL_COST_*`).

- [ ] **Step 1: Write the failing tests** (in `test_build_spells.py`, replacing the fixed-number assertions at
  lines ~120-124):

```python
class ValueTests(unittest.TestCase):
    def setUp(self):
        self.files = bs.render_all(SPELLS)
        self.v = self.files["common/script_values/aov_spell_values.txt"]

    def test_cost_value_has_floor(self):
        b = block(self.v, "aov_spell_meteor_swarm_cost")
        self.assertIn("subtract = aov_cost_cut_evocation", b)
        self.assertIn("subtract = aov_cost_cut_war", b)
        self.assertIn("min = 0.5", b)
        self.assertIn("multiply = 100", b)
        self.assertIn("floor = yes", b)
        self.assertNotIn("aov_cost_cut_war", block(self.v, "aov_spell_guidance_cost"))
        self.assertIn("subtract = aov_cost_cut_targeted", block(self.v, "aov_spell_scry_cost"))

    def test_years_value(self):
        b = block(self.v, "aov_spell_elemental_fury_years")
        self.assertIn("value = 5", b)
        self.assertIn("multiply = aov_years_mult_evocation", b)
        self.assertIn("floor = yes", b)

    def test_cooldown_and_modifier_share_years_value(self):
        b = block(self.files["common/scripted_effects/aov_spell_effects.txt"], "aov_spell_guidance_cast")
        self.assertIn("set_variable = { name = aov_spell_guidance_cd years = aov_spell_guidance_years }", b)
        self.assertIn("add_character_modifier = { modifier = aov_spell_guidance years = aov_spell_guidance_years }", b)
        self.assertIn("aov_mana_spend = { AMOUNT = aov_spell_guidance_cost }", b)
        self.assertIn("aov_school_add_progress = { SCHOOL = divination AMOUNT = 25 }", b)
        self.assertIn("add_magic_lifestyle_xp = 25", b)

    def test_no_fixed_costs_left(self):
        for rel in ("common/scripted_triggers/aov_spell_triggers.txt", "common/scripted_effects/aov_spell_effects.txt",
                    "localization/english/aov_spells_l_english.yml", "gui/aov_magic_generated.gui"):
            self.assertNotRegex(self.files[rel], r"AOV_SPELL_(COST|REQ_MANA|FACTS)_\d", rel)
            self.assertNotRegex(self.files[rel], r"aov_mana >= \d", rel)

    def test_dynamic_loc(self):
        loc = self.files["localization/english/aov_spells_l_english.yml"]
        self.assertIn("ScriptValue('aov_spell_fireball_cost')", loc)
        self.assertIn("ScriptValue('aov_spell_fireball_years')", loc)

    def test_elementals_follow_spell_years(self):
        eff = (MOD / "common/scripted_effects/aov_magic_effects.txt").read_text(encoding="utf-8-sig")
        self.assertIn("trigger_event = { id = aov_magic.10 years = aov_spell_summon_elementals_years }", eff)
        self.assertNotIn("years = 3", block(eff, "aov_summon_elementals"))
```

- [ ] **Step 2: Run** `test_build_spells.py`. Expected: FAIL.

- [ ] **Step 3: Implement.**
  - `values(spells)`: per spell, cost = `{ value = 1  subtract = aov_cost_cut_<s>  [subtract = aov_cost_cut_war|targeted]
    min = 0.5  multiply = <base>  add = 0.5  floor = yes }`; years = `{ value = <base years>  multiply = aov_years_mult_<s>
    add = 0.5  floor = yes }`. Add it to `render_all` as `common/script_values/aov_spell_values.txt`.
  - `triggers`: mana check `aov_mana >= aov_spell_<k>_cost` with tooltip `aov_spell_<k>_req_mana`.
  - `effects`: `custom_tooltip = aov_spell_<k>_cost_tt`; `aov_mana_spend = { AMOUNT = aov_spell_<k>_cost }`; progress stays
    `AMOUNT = <base>`; cooldown and modifier `years = aov_spell_<k>_years`; add `add_magic_lifestyle_xp = <base>`
    (inside `hidden_effect`).
  - `card` and the `_tt` loc use `aov_spell_<k>_facts`.
  - `loc`: per spell `aov_spell_<k>_facts: "Level N · #V [GetPlayer.MakeScope.ScriptValue('aov_spell_<k>_cost')|0]#! mana ·
    <Type> · #V [GetPlayer.MakeScope.ScriptValue('aov_spell_<k>_years')|0]#! years"`, `_req_mana: "Has at least …"`,
    `_cost_tt: "Costs …"`; drop the per-level `AOV_SPELL_FACTS_*`, `AOV_SPELL_REQ_MANA_*`, `AOV_SPELL_COST_*` keys.
  - `aov_summon_elementals`: `years = aov_spell_summon_elementals_years`; fix its comment. Spell desc in `spells.py`:
    "A free army of conjured elementals appears at your capital for the spell's duration".

- [ ] **Step 4: Regenerate and verify.** `python -I tools/build_spells.py`, all tool tests, `python -I tools/validate.py`.
  Expected: PASS; `fatal: 0, error: 0`. If tiger rejects `years = <value>` in `set_variable`, `add_character_modifier` or
  `trigger_event`, generate an `if`/`else_if` ladder over the possible whole years (base and ×1.5 rounded: 1,2,3,5,8)
  and record the deviation in the spec's Risks.

- [ ] **Step 5: Commit** `Make spell cost and duration per-caster values`.

---

### Task 4: Lifestyle window override generator

**Files:**
- Create: `tools/build_lifestyle_override.py`, `tools/tests/test_build_lifestyle_override.py`
- Generated: `gui/window_character_lifestyle.gui`
- Modify: `CLAUDE.md` (generated-files table, task table, update steps 2 and the CK3-patch line)

**Interfaces:**
- Consumes: `brace_delta` and `GeneratorError` from `build_hud_override` (import them).
- Produces: `ANCHOR = "EqualTo_string( Lifestyle.GetKey, 'wanderer_lifestyle' )"`, `EXPECTED_ANCHORS = 3`,
  `TEXTURES = {"gfx/interface/progressbars/progress_brown.dds": "gfx/interface/progressbars/aov_progress_magic.dds",
  "gfx/interface/progressbars/progress_brown_bg.dds": "gfx/interface/progressbars/aov_progress_magic_bg.dds",
  "gfx/interface/icons/lifestyles_perks/node_wanderer.dds": "gfx/interface/icons/lifestyles_perks/node_magic.dds"}`,
  `insert_magic(text: str) -> str`, `build(raw: bytes) -> bytes`, `find_source(anbennar, game) -> Path`, `main()`.
  Same CLI and header style as `build_hud_override.py`.

- [ ] **Step 1: Write the failing tests** with a small fixture holding three `wanderer_lifestyle` blocks
  (a `background`, a `progressbar_lifestyle_xp`, an `icon_lifestyle_unspent_points`, each shaped like vanilla lines 685-689,
  852-856, 895-898 of `game/gui/window_character_lifestyle.gui`):

```python
def test_inserts_a_magic_copy_after_each_anchor(self):
    out = blo.insert_magic(FIXTURE)
    self.assertEqual(out.count("'magic_lifestyle'"), 3)
    for i in range(3):   # each copy follows its wanderer block
        self.assertLess(nth(out, "'wanderer_lifestyle'", i), nth(out, "'magic_lifestyle'", i))
    for chunk in out.split(blo.MARKER)[1:]:   # the marked copies carry no wanderer art
        copy = chunk.split("\n\n", 1)[0]
        self.assertNotIn("progress_brown", copy)
        self.assertNotIn("node_wanderer", copy)

def test_textures_mapped(self):
    out = blo.insert_magic(FIXTURE)
    for new in blo.TEXTURES.values():
        self.assertIn(new, out)

def test_errors_when_anchor_count_changes(self):
    with self.assertRaises(blo.GeneratorError):
        blo.insert_magic(FIXTURE.replace("'wanderer_lifestyle'", "'other'", 1))

def test_errors_on_unmapped_texture(self):
    with self.assertRaises(blo.GeneratorError):
        blo.insert_magic(FIXTURE.replace("progress_brown_bg.dds", "progress_new.dds"))

def test_refuses_generated_input(self):
    with self.assertRaises(blo.GeneratorError):
        blo.insert_magic(blo.insert_magic(FIXTURE))

def test_build_keeps_bom_and_adds_header(self):
    out = blo.build(b"\xef\xbb\xbf" + FIXTURE.encode())
    self.assertTrue(out.startswith(b"\xef\xbb\xbf# Anbennar Overhaul: generated by tools/build_lifestyle_override.py"))
```

- [ ] **Step 2: Run** the test file. Expected: FAIL (module missing).

- [ ] **Step 3: Implement.** For each anchor line: the enclosing block starts on the nearest preceding line ending in
  `= {`; find its end with `brace_delta`; copy it, replace `'wanderer_lifestyle'` with `'magic_lifestyle'`, map every
  `texture`/`progresstexture`/`noprogresstexture` path through `TEXTURES` (unmapped path → `GeneratorError`), prefix
  `# Anbennar Overhaul: magic lifestyle` at the block's indent, insert after the original. Insert from the last anchor
  backwards so indices stay valid. Source: Anbennar's file, else the game's.

- [ ] **Step 4: Generate and verify.** `python -I tools/build_lifestyle_override.py`; diff the output against Anbennar's
  file (only the header and three marked blocks differ); all tool tests; `python -I tools/validate.py`
  (`fatal: 0, error: 0`). Update CLAUDE.md: generated-files row, task-table row, update step 2 runs the new script,
  CK3-patch line names it too.

- [ ] **Step 5: Commit** `Generate the lifestyle window override with magic branches`.

---

### Task 5: Art generator

**Files:**
- Create: `tools/build_magic_lifestyle_art.py`, `tools/tests/test_build_magic_lifestyle_art.py`
- Generated: every output in the spec's art table, plus `gfx/interface/icons/lifestyles_perks/trait_<trait>.dds` (×3,
  120×120, same image as the trait icon: final perks use `icon = trait_<trait>`, as vanilla `trait_scholar.dds`)
- Modify: `CLAUDE.md` (generated-files table, task table)

**Interfaces:**
- Consumes: `read_bgra`, `write_bgra` from `build_spells`; `GeneratorError`, `dx10_bgra_to_legacy` from `build_inventions`.
- Produces: `resize(px: bytes, w: int, h: int, nw: int, nh: int) -> bytes` (bilinear, premultiplied alpha),
  `tint(px: bytes, bgr: tuple) -> bytes` (luminance × colour, alpha kept), `crop(px, w, x, y, cw, ch) -> bytes`,
  `over(dst: bytearray, dw: int, src: bytes, sw: int, sh: int, x: int, y: int) -> None` (alpha-over),
  `OUTPUTS: dict[str, tuple[int, int]]` (path → size), `build_all(eu4: Path, game: Path) -> dict[str, bytes]`, `main()`
  with `--eu4` and `--game`. Teal = BGR `(200, 190, 40)`.
- Composition: lifestyle icon = 3 frames of 160×160, the center graphic resized to 150 and centred, frames 2 and 3
  brightened ×1.15 and ×1.3 (vanilla's frames are DXT5, which this script does not decode, so only frame count and size
  are matched); focus icons = spell frame (60×60 crop at
  `(school_index × 60, 0)` of the slot strip) resized to 120 and centred on a 140×140 transparent canvas; trait icons =
  the same crop resized to 112 centred on 120×120; tree backgrounds and illustration = `magic_bg.dds` resized to size.

- [ ] **Step 1: Write the failing tests:**

```python
def test_resize_keeps_flat_colour(self):
    px = bytes([10, 20, 30, 255]) * 4
    out = art.resize(px, 2, 2, 5, 3)
    self.assertEqual(len(out), 5 * 3 * 4)
    self.assertEqual(set(out[i:i + 4] for i in range(0, len(out), 4)), {bytes([10, 20, 30, 255])})

def test_tint_keeps_alpha(self):
    out = art.tint(bytes([255, 255, 255, 77]), (200, 190, 40))
    self.assertEqual(out, bytes([200, 190, 40, 77]))

def test_over_respects_alpha(self):
    dst = bytearray(bytes([0, 0, 0, 255]))
    art.over(dst, 1, bytes([255, 255, 255, 0]), 1, 1, 0, 0)
    self.assertEqual(bytes(dst), bytes([0, 0, 0, 255]))

@unittest.skipUnless(EU4.is_dir() and GAME.is_dir(), "needs EU4 Anbennar and CK3 installed")
def test_outputs_have_declared_sizes(self):
    files = art.build_all(EU4, GAME)
    self.assertEqual(set(files), set(art.OUTPUTS))
    for path, data in files.items():
        w, h, px = bs.read_bgra(data)
        self.assertEqual((w, h), art.OUTPUTS[path], path)
        self.assertEqual(len(px), w * h * 4)
```

- [ ] **Step 2: Run.** Expected: FAIL (module missing).

- [ ] **Step 3: Implement** the helpers and `build_all` per the spec's art table and the composition above; `main()`
  writes each file under the submod and prints the count.

- [ ] **Step 4: Generate and verify.** `python -I tools/build_magic_lifestyle_art.py`; all tool tests; open two outputs
  (the lifestyle icon and one trait icon) with the Read tool to eyeball them; `python -I tools/validate.py`
  (`fatal: 0, error: 0`). Add the generator to CLAUDE.md's tables.

- [ ] **Step 5: Commit** `Generate magic lifestyle art`.

---

### Task 6: Documentation and in-game check

**Files:**
- Modify: `CLAUDE.md` (Systems: replace "Sub-project 2 (the magic lifestyle) is not built yet." with a paragraph on the
  lifestyle: trees, bonus layer file, per-spell values, generators), the spec's Status line ("built"),
  `docs/superpowers/specs/2026-10-08-magic-lifestyle-design.md` (record any substitutes from Tasks 1 and 3)

- [ ] **Step 1: Full verification.** `python -I -m unittest discover -s tools/tests -v` (all pass) and
  `python -I tools/validate.py --all` reviewed for any report touching `aov_magic_lifestyle`, `zz_aov_magic_focuses`,
  `aov_spell_values` or `window_character_lifestyle` (none expected beyond the baseline).
- [ ] **Step 2: Write the docs** above.
- [ ] **Step 3: Hand the in-game checklist to the user** (not runnable here): the spec's Verification "In game" list,
  plus `database_conflicts.log` shows `magic_duelist_focus` overridden by `zz_aov_magic_focuses.txt` and the tooltip
  of a spell card shows the reduced cost after taking a cost perk (debug: `add_perk`/console `lifestyle_perks`).
- [ ] **Step 4: Commit** `Document the magic lifestyle`.
