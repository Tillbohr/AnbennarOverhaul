# Magic Schools and Spells Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eight schools of magic with per-mage mana and knowledge, 49 castable spells adapted from EU4 Anbennar, and a Magic window like the Artificery window.

**Architecture:** One data table (`tools/data/spells.py`) and a generator (`tools/build_spells.py`) produce the per-spell script, GUI, loc and art, as `tools/build_inventions.py` does for inventions. Hand-written files hold the shared system (mana, study, levels, casting rules, AI), the window, the HUD tab, and overrides of Anbennar's three spell interactions.

**Tech Stack:** CK3 1.19.0.6 script, PdxGui, ck3-tiger (`python -I tools/validate.py`), Python `unittest` in `tools/tests/`.

**Spec:** `docs/superpowers/specs/2026-10-08-magic-schools-design.md` (spell effects, mechanics and window are defined there; this plan does not repeat the spell tables).

## Global Constraints

- Script/loc/gui files: UTF-8 with BOM, LF, tabs. Python and Markdown: LF (write with `write_bytes`, never `write_text` on Windows).
- New files `aov_`-prefixed; base Anbennar is never edited. Generated files carry the "generated ... do not edit by hand" header.
- Schools, in this order everywhere (EU4 frame order 1-8): `abjuration`, `conjuration`, `divination`, `enchantment`, `evocation`, `illusion`, `necromancy`, `transmutation`.
- A mage is `has_magical_affinity = yes` (Anbennar trigger); affinity level = 1/2/3 from `magical_affinity_1/2/3`.
- Mana max = 100 + 50 x affinity. Refill per month = 5 + Learning / 2 + 2 x affinity. Costs 25/50/100/200 by spell level.
- Study per month = Learning + 5 x affinity; level thresholds 300/800/2000 (cumulative). Casting adds progress = mana cost.
- **Pulse:** CK3 has no monthly character pulse; mana and study tick in `quarterly_playable_pulse` at 3x the monthly amounts (same rate). The window and tooltips show the monthly rate.
- Durations and cooldowns by spell level: 1/2/3/5 years.
- Dark magic: Necromancy cast with faith `has_doctrine_parameter = witchcraft_illegal` 25%, `witchcraft_shunned` 10% chance of `forbidden_magic_practitioner`.
- Spell keys: `aov_spell_<key>`; per-spell cooldown timed variable `aov_spell_<key>_cd`.
- Summon Elementals: `spawn_army` at the caster's capital with men-at-arms type `aov_conjured_elementals` (never recruitable), bound to the caster's war, removed after 3 years with `deplete_army_by_percent = 1`.

## Review Focus

1. Casting with exactly the mana cost leaves 0, never negative; refills cap at the maximum. *(Task 2 test `test_mana_change_clamps`.)*
2. A mage who loses Magical Affinity: no refill, no study, no window, spells uncastable; state kept. *(Task 2 test `test_pulse_only_for_mages`; Task 3 test `test_castable_requires_mage`.)*
3. The caster dies or the war ends before Summon Elementals expires: the depletion event must not error on a missing army. *(Task 4 test `test_elementals_depletion_guarded`.)*
4. Targeted spell on a target protected by Field of Forbiddance: every spell interaction refuses it. *(Task 5 test `test_interactions_respect_forbiddance`.)*
5. Switching the studied school keeps each school's progress; a school at level 3 cannot be studied further. *(Task 2 test `test_study_switch_keeps_progress`.)*

---

### Task 1: Spell data, validation and art

**Files:**
- Create: `tools/data/spells.py`, `tools/build_spells.py`, `tools/tests/test_build_spells.py`
- Generated: `gfx/interface/icons/aov_magic/*`

**Interfaces:**
- Produces: `SPELLS` (list of dicts) with keys `key`, `school`, `level` (0-3), `slot` (1-6, or 0 for Enhance Ability), `type` (`self`|`realm`|`war`|`targeted`), `modifier` (str, `""` if none), `effect` (str, `""` if none), `interaction` (str key for targeted spells; existing Anbennar key for compel/dominate/enhance, else `aov_spell_<key>_interaction`), `name`, `desc`, `flavour`.
- Produces in `build_spells.py`: `SCHOOLS` tuple (order above), `COSTS = (25, 50, 100, 200)`, `YEARS = (1, 2, 3, 5)`, `GeneratorError`, `load_spells()`, `validate(spells)`, `copy_art(eu4: Path, root: Path)`, `downscale(px, w, h, size) -> bytes`, and re-uses `dx10_bgra_to_legacy` by importing it from `build_inventions`.
- Art written to `gfx/interface/icons/aov_magic/`: `spell_slot_<1-6>.dds` (EU4 `magic_spell_icons_slot_<n>_60x60.dds`, 8 frames of 60x60), `school_<school>.dds` (EU4 `magic_<school>_icon.dds`, 34x34), `levels_strip.dds` (EU4 `levels_strip_glow_1_7.dds`, frames 42x41), `spell_frames.dds` (EU4 `magic_ui_spell_frames_64x76.dds`, 4 frames 64x76), `spell_plate.dds` (EU4 `magic_cast_spell_button.dds`, 290x64), `magic_bg.dds`; and `gfx/interface/skinned/hud_maintab/aov_maintab_magic.dds` = EU4 `magic_center_graphic.dds` (181x182, uncompressed A8R8G8B8) area-averaged down to 95x95.

- [ ] **Step 1: Write the failing tests** (`tools/tests/test_build_spells.py`: load `SPELLS` from `tools/data/spells.py` and import `build_spells as bs` the way `test_build_inventions.py` loads `INVENTIONS` and `build_inventions as bi`; reuse its `balanced()` and `top_level_blocks()` helpers, and add `block(text, name)` from `test_artificer_factions.py`):

```python
class DataTests(unittest.TestCase):
    def test_forty_nine_spells_in_eight_schools(self):
        self.assertEqual(len(SPELLS), 49)
        counts = collections.Counter(s["school"] for s in SPELLS)
        self.assertEqual(set(counts), set(bs.SCHOOLS))
        self.assertEqual(counts["transmutation"], 7)
        self.assertTrue(all(counts[c] == 6 for c in bs.SCHOOLS if c != "transmutation"))

    def test_slots_match_levels(self):
        level_of_slot = {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3}
        for s in SPELLS:
            if s["slot"]:
                self.assertEqual(level_of_slot[s["slot"]], s["level"], s["key"])
        for c in bs.SCHOOLS:
            slots = [s["slot"] for s in SPELLS if s["school"] == c and s["slot"]]
            self.assertEqual(sorted(slots), [1, 2, 3, 4, 5, 6], c)

    def test_existing_anbennar_spells(self):
        by = {s["key"]: s for s in SPELLS}
        self.assertEqual(by["thoughtweave"]["interaction"], "start_compel_interaction")
        self.assertEqual(by["dominate_to_surrender"]["interaction"], "start_dominate_interaction")
        self.assertEqual(by["enhance_ability"]["interaction"], "anb_enhance_ability_interaction")
        self.assertEqual((by["enhance_ability"]["school"], by["enhance_ability"]["level"]), ("transmutation", 1))

    def test_types(self):
        targeted = {s["key"] for s in SPELLS if s["type"] == "targeted"}
        self.assertEqual(targeted, {"ward", "heartstring", "thoughtweave", "dominate_to_surrender", "scry",
                                    "steal_vitality", "contagion", "enhance_ability"})
        for s in SPELLS:
            if s["type"] in ("self", "realm", "war"):
                self.assertTrue(s["modifier"].strip() or s["effect"].strip(), s["key"])

class ValidateTests(unittest.TestCase):
    def test_real_data_valid(self):
        bs.validate(SPELLS)
    def test_rejects_unknown_school(self):
        with self.assertRaises(bs.GeneratorError):
            bs.validate([dict(SPELLS[0], school="evokation")])
    def test_rejects_duplicate(self):
        with self.assertRaises(bs.GeneratorError):
            bs.validate(SPELLS + [dict(SPELLS[0])])

class ArtTests(unittest.TestCase):
    def test_downscale_averages(self):
        px = bytes([255, 0, 0, 255] * 4)          # 2x2 red BGRA
        self.assertEqual(bs.downscale(px, 2, 2, 1), bytes([255, 0, 0, 255]))
    def test_copy_art_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(bs.GeneratorError):
                bs.copy_art(Path(tmp, "nope"), Path(tmp, "mod"))
```

- [ ] **Step 2: Run `python -I -m unittest discover -s tools/tests -p "test_build_spells.py"`.** Expected: errors (module missing).
- [ ] **Step 3: Write `tools/data/spells.py`** with all 49 spells from the spec tables: names, school, level, slot (EU4 position within the school: slot 1 = the level-0 spell, 2-3 = level 1 in the spec's order, 4-5 = level 2, 6 = level 3; Enhance Ability slot 0), type, modifier bodies with the spec's values, one-off `effect` script for one-off spells (Eye for Talent, Deposit Divination's gold, Scry, Contagion, Speak With Dead, Remove Pain, Transmute to Gold, Extraplanar Contact `trigger_event`, Summon Elementals `aov_summon_elementals = yes`). `desc` = the spec's effect line; `flavour` = a short line in the spirit of EU4's `<spell>_spell_desc` (written fresh, not copied).
- [ ] **Step 4: Write `tools/build_spells.py`** with the Interfaces above; `main()` validates, copies art, and (from Task 3 on) writes the generated files. Art: classic-header DDS copied as is; DX10 converted; the tab icon decoded (uncompressed A8R8G8B8), downscaled, written as a classic A8R8G8B8 DDS.
- [ ] **Step 5: Run the tests and `python -I tools/build_spells.py`.** Expected: tests OK; art files present.
- [ ] **Step 6: Commit** `Add spell data table and magic art`.

---

### Task 2: Mana, study and school levels

**Files:**
- Create: `common/scripted_triggers/aov_magic_triggers.txt`, `common/script_values/aov_magic_values.txt`, `common/scripted_effects/aov_magic_effects.txt`, `common/on_action/aov_magic_on_actions.txt`, `events/aov_magic_events.txt`, `localization/english/aov_magic_l_english.yml`, `tools/tests/test_magic_system.py`

**Interfaces:**
- Triggers (character): `aov_is_mage`, `aov_school_level_at_least = { SCHOOL = <s> LEVEL = <n> }`, `aov_is_studying = { SCHOOL = <s> }`, `aov_dark_magic_risky`.
- Values: `aov_affinity_level` (0-3), `aov_mana` (variable or 0), `aov_mana_max`, `aov_mana_refill_month`, `aov_study_gain_month`, `aov_school_<s>_progress`, `aov_school_<s>_level` (0-3), `aov_school_<s>_next` (threshold of next level), `aov_magic_mastery_value` (sum of levels).
- Effects: `aov_magic_init` (full mana, all progress 0), `aov_mana_change = { AMOUNT = <v> }` (clamped 0..max), `aov_study_set = { SCHOOL = <s> }`, `aov_school_add_progress = { SCHOOL = <s> AMOUNT = <v> }` (fires `aov_magic.1` level-up when a threshold is crossed), `aov_magic_quarterly` (refill x3, study x3, mastery sync), `aov_magic_sync_mastery` (sets Anbennar's `magic_mastery`).
- Event `aov_magic.1` (level up; `scope:aov_school` flag, `scope:aov_new_level`).

- [ ] **Step 1: Write the failing tests** (`tools/tests/test_magic_system.py`, `read`/`block` helpers as in `test_artificer_factions.py`):

```python
def test_mana_values(self):
    v = read("common/script_values/aov_magic_values.txt")
    self.assertIn("value = 100", block(v, "aov_mana_max"))
    self.assertIn("multiply = 50", block(v, "aov_mana_max"))
    self.assertIn("value = 5", block(v, "aov_mana_refill_month"))
def test_mana_change_clamps(self):
    b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_mana_change")
    self.assertIn("min = 0", b); self.assertIn("max = aov_mana_max", b)
def test_thresholds(self):
    b = block(read("common/script_values/aov_magic_values.txt"), "aov_school_divination_level")
    for n in ("300", "800", "2000"): self.assertIn(f">= {n}", b)
def test_quarterly_ticks_three_months(self):
    b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_magic_quarterly")
    self.assertIn("multiply = 3", b)
def test_pulse_only_for_mages(self):
    text = read("common/on_action/aov_magic_on_actions.txt")
    self.assertIn("quarterly_playable_pulse = {\n\ton_actions = { aov_magic_quarterly_pulse }", text)
    self.assertIn("aov_is_mage = yes", block(text, "aov_magic_quarterly_pulse"))
def test_study_switch_keeps_progress(self):
    b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_study_set")
    self.assertIn("set_variable = { name = aov_studying value = flag:$SCHOOL$ }", b)
    self.assertNotIn("progress", b)
    q = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_magic_quarterly")
    self.assertIn("< 3", q)   # no study gain at level 3
def test_mastery_synced(self):
    self.assertIn("name = magic_mastery", block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_magic_sync_mastery"))
```

- [ ] **Step 2: Run; expect errors (files missing).**
- [ ] **Step 3: Implement** the Interfaces. `aov_magic_quarterly` per school is written out for all eight (no generator needed). `aov_magic_init` runs from the pulse when `aov_mana` is unset. Level-up event: notification with the school icon (`gfx/interface/icons/aov_magic/school_<s>.dds` via loc text icon not required; plain text is fine).
- [ ] **Step 4: Run tests + `python -I tools/validate.py`.** Expected: OK; tiger clean.
- [ ] **Step 5: Commit** `Add mana, study and school levels`.

---

### Task 3: Generated spell layer (lasting and one-off spells)

**Files:**
- Modify: `tools/build_spells.py`, `tools/tests/test_build_spells.py`
- Generated: `common/modifiers/aov_spell_modifiers.txt`, `common/scripted_triggers/aov_spell_triggers.txt`, `common/scripted_effects/aov_spell_effects.txt`, `common/scripted_guis/aov_spell_sgui.txt`, `localization/english/aov_spells_l_english.yml`

**Interfaces:**
- Consumes: Task 2 triggers/values/effects.
- Produces per spell `k`: modifier `aov_spell_<k>` (if `modifier`); triggers `aov_spell_<k>_known`, `aov_spell_<k>_ready` (no cooldown var), `aov_spell_<k>_castable` (mage, known, ready, mana >= cost, war spells `is_at_war = yes`, each under a `custom_tooltip` with shared loc keys `AOV_SPELL_REQ_*`); effect `aov_spell_<k>_cast` (pay mana, add progress, cooldown `set_variable = { name = aov_spell_<k>_cd years = Y }`, modifier with `years = Y`, one-off `effect`, dark-magic roll for necromancy); sGUI `aov_spell_<k>_sgui` for self/realm/war (is_valid = castable, effect = cast) and `aov_study_<s>_sgui` per school.
- Loc: `aov_spell_<k>` (name), `aov_spell_<k>_desc`, `aov_spell_<k>_flavour`, `aov_spell_<k>` modifier name/desc keys.

- [ ] **Step 1: Write the failing tests**:

```python
def test_cast_effect_pays_progresses_and_cools_down(self):
    t = bs.effects(SPELLS)
    b = block(t, "aov_spell_guidance_cast")
    self.assertIn("aov_mana_change = { AMOUNT = -25 }", b)
    self.assertIn("aov_school_add_progress = { SCHOOL = divination AMOUNT = 25 }", b)
    self.assertIn("set_variable = { name = aov_spell_guidance_cd years = 1 }", b)
    self.assertIn("add_character_modifier = { modifier = aov_spell_guidance years = 1 }", b)
def test_necromancy_rolls_dark_magic(self):
    t = bs.effects(SPELLS)
    self.assertIn("aov_dark_magic_roll = yes", block(t, "aov_spell_false_life_cast"))
    self.assertNotIn("aov_dark_magic_roll", block(t, "aov_spell_guidance_cast"))
def test_castable_requires_mage(self):
    b = block(bs.triggers(SPELLS), "aov_spell_fireball_castable")
    for s in ("aov_is_mage = yes", "aov_spell_fireball_known = yes", "aov_spell_fireball_ready = yes", "aov_mana >= 25"):
        self.assertIn(s, b)
def test_war_spells_need_war(self):
    self.assertIn("is_at_war = yes", block(bs.triggers(SPELLS), "aov_spell_meteor_swarm_castable"))
def test_sgui_only_for_window_spells(self):
    names = set(top_level_blocks(bs.sguis(SPELLS)))
    self.assertIn("aov_spell_guidance_sgui", names)
    self.assertNotIn("aov_spell_heartstring_sgui", names)
    for c in bs.SCHOOLS: self.assertIn(f"aov_study_{c}_sgui", names)
def test_modifier_per_lasting_spell(self):
    names = set(top_level_blocks(bs.modifiers(SPELLS)))
    self.assertIn("aov_spell_combat_ward", names)
    self.assertNotIn("aov_spell_transmute_to_gold", names)   # one-off
```

- [ ] **Step 2: Run; expect failures (functions missing).**
- [ ] **Step 3: Implement** `modifiers()`, `triggers()`, `effects()`, `sguis()`, `loc()`, `render_all()`, `write_all()` mirroring `build_inventions.py`. Shared loc keys (`AOV_SPELL_REQ_*`, type names, "Cast") go in hand-written `aov_magic_l_english.yml`. Add `aov_dark_magic_roll` (hand-written, `aov_magic_effects.txt`): `random = { chance = 25 ... }` / `10` by doctrine, gives `forbidden_magic_practitioner` if missing.
- [ ] **Step 4: Run the generator, tests and tiger.** Fix any modifier key tiger rejects with the closest valid character modifier and add a line to the spec's Risks section naming the substitution.
- [ ] **Step 5: Commit** `Generate spell modifiers, casting and loc`.

---

### Task 4: Special spells (events, Summon Elementals, Rite of Conception)

**Files:**
- Create: `common/men_at_arms_types/aov_magic_maa_types.txt`
- Modify: `common/scripted_effects/aov_magic_effects.txt`, `events/aov_magic_events.txt`, `common/on_action/aov_magic_on_actions.txt`, `localization/english/aov_magic_l_english.yml`, `tools/tests/test_magic_system.py`

**Interfaces:**
- Effects: `aov_summon_elementals` (spawn, save army in `aov_elemental_army`, schedule `aov_magic.10` in 3 years), `aov_eye_for_talent` (`create_character` with one skill 14-18, two good traits, culture/faith of the caster, then `add_courtier`), `aov_speak_with_dead`, `aov_scry_reveal` (target scope).
- Events: `aov_magic.10` (hidden: deplete elementals), `aov_magic.20` (Extraplanar Contact: three options + demonic price roll), `aov_magic.30` (Eye for Talent arrival notification).
- MaA `aov_conjured_elementals`: heavy-infantry stats, `can_recruit = { always = no }`.
- On birth (`on_birth_child` appended): mother or father with `aov_spell_rite_of_conception` modifier, 50% `add_trait = magical_affinity_1`.

- [ ] **Step 1: Write the failing tests**:

```python
def test_elementals_spawn_bound_to_war(self):
    b = block(read("common/scripted_effects/aov_magic_effects.txt"), "aov_summon_elementals")
    for s in ("spawn_army", "type = aov_conjured_elementals", "inheritable = no", "save_scope_as = aov_new_elementals",
              "name = aov_elemental_army", "id = aov_magic.10"):
        self.assertIn(s, b)
def test_elementals_depletion_guarded(self):
    b = block(read("events/aov_magic_events.txt"), "aov_magic.10")
    self.assertIn("exists = var:aov_elemental_army", b)
    self.assertIn("deplete_army_by_percent = 1", b)
def test_elementals_never_recruitable(self):
    self.assertIn("always = no", block(read("common/men_at_arms_types/aov_magic_maa_types.txt"), "aov_conjured_elementals"))
def test_rite_of_conception_on_birth(self):
    text = read("common/on_action/aov_magic_on_actions.txt")
    self.assertIn("on_birth_child = {\n\ton_actions = { aov_magic_on_birth }", text)
    self.assertIn("magical_affinity_1", block(text, "aov_magic_on_birth"))
```

- [ ] **Step 2: Run; expect failures.**
- [ ] **Step 3: Implement.** Check vanilla `on_birth_child` scopes (`root` = child, `scope:mother`, `scope:father`) in `common/on_action/birth_on_actions.txt` before writing the trigger.
- [ ] **Step 4: Tests + tiger.** In-game check deferred to Task 8: `deplete_army_by_percent` on a spawned army.
- [ ] **Step 5: Commit** `Add special spells: elementals, contact, talent, conception`.

---

### Task 5: Targeted spells (interactions and overrides)

**Files:**
- Modify: `tools/build_spells.py` (adds `interactions()`), tests
- Generated: `common/character_interactions/aov_spell_interactions.txt`
- Create: `common/character_interactions/zz_aov_spell_overrides.txt`, `tools/tests/test_magic_system.py` additions

**Interfaces:**
- Generated interactions `aov_spell_<k>_interaction` for ward, heartstring, scry, steal_vitality, contagion: `category = interaction_category_spells`, `is_shown` = actor `aov_is_mage`, `is_valid_showing_failures_only` = actor `aov_spell_<k>_castable` and recipient `aov_spell_target_allowed`, `on_accept` = actor `aov_spell_<k>_cast` (with `scope:recipient` as target) plus the spell's target effect; `auto_accept = yes` except Heartstring (accept logic: base 0, +opinion, AI accepts the charm attempt like a gift); AI: `ai_potential` = `is_ai = yes` mages, `ai_will_do` low (10) for hostile spells, 0 for Ward on non-family.
- Trigger `aov_spell_target_allowed` (recipient): `NOT = { has_character_modifier = aov_spell_field_of_forbiddance }`.
- Overrides: copies of Anbennar's `start_compel_interaction`, `start_dominate_interaction` (`anb_spellcasting_infin_spells.txt`) and `anb_enhance_ability_interaction` (`anb_spellcasting_interactions_enchantment.txt`), each with `# Anbennar Overhaul` additions: `is_valid_showing_failures_only` gains actor `aov_spell_<k>_castable = yes` and recipient `aov_spell_target_allowed = yes`; `on_accept` gains actor `aov_spell_<k>_cast = yes` (k = thoughtweave / dominate_to_surrender / enhance_ability).

- [ ] **Step 1: Write the failing tests**:

```python
def test_generated_interactions(self):
    names = set(top_level_blocks(bs.interactions(SPELLS)))
    self.assertEqual(names, {f"aov_spell_{k}_interaction" for k in ("ward", "heartstring", "scry", "steal_vitality", "contagion")})
def test_interactions_respect_forbiddance(self):
    gen = bs.interactions(SPELLS)
    over = read("common/character_interactions/zz_aov_spell_overrides.txt")
    for name in top_level_blocks(gen):
        self.assertIn("aov_spell_target_allowed = yes", block(gen, name))
    for name in ("start_compel_interaction", "start_dominate_interaction", "anb_enhance_ability_interaction"):
        self.assertIn("aov_spell_target_allowed = yes", block(over, name))
def test_overrides_keep_anbennar_bodies(self):
    over = read("common/character_interactions/zz_aov_spell_overrides.txt")
    base = (MOD.parent / "anbennar-ck3-dev-master/common/character_interactions/anb_spellcasting_infin_spells.txt").read_text(encoding="utf-8-sig")
    for line in block(base, "start_compel_interaction").splitlines():
        if line.strip() and not line.strip().startswith("#"):
            self.assertIn(line, block(over, "start_compel_interaction"))
    self.assertIn("aov_spell_thoughtweave_cast = yes", block(over, "start_compel_interaction"))
```

- [ ] **Step 2: Run; expect failures.**
- [ ] **Step 3: Implement.** Copy the three Anbennar interactions with a small script (byte-exact), then insert the additions at the start of the matching blocks.
- [ ] **Step 4: Tests + tiger.**
- [ ] **Step 5: Commit** `Add targeted spell interactions and gate Anbennar's spells`.

---

### Task 6: AI

**Files:** Modify `common/scripted_effects/aov_magic_effects.txt`, `common/on_action/aov_magic_on_actions.txt`, `tools/build_spells.py` (generates `aov_magic_ai_cast_random`), tests.

**Interfaces:** `aov_magic_ai_quarterly` (AI mages only): choose study school if none (highest skill mapping from the spec, else random), then `aov_magic_ai_cast_random` = `random_list` over S/R/W spells with `trigger = { aov_spell_<k>_castable = yes }`, weight 10 (war spells 30 at war).

- [ ] **Step 1: Tests**: `aov_magic_ai_quarterly` has `is_ai = yes` and `aov_study_set`; the generated random list lists every S/R/W spell and no targeted spell.
- [ ] **Step 2: Run; expect failures.** **Step 3: Implement.** **Step 4: Tests + tiger.** **Step 5: Commit** `Add AI study and casting`.

---

### Task 7: HUD tab and Magic window

**Files:**
- Modify: `tools/build_hud_override.py` (+ rerun → `gui/hud.gui`), `tools/tests/test_build_hud_override.py`, `tools/build_spells.py` (adds `gui()`), `gui/scripted_widgets/aov_scripted_widgets.txt`
- Create: `gui/aov_window_magic.gui`, `common/scripted_guis/aov_magic_sgui.txt`
- Generated: `gui/aov_magic_generated.gui`

**Interfaces:**
- HUD: a second inserted tab `tab_aov_magic` directly after `tab_aov_artificery` (same block markers style), texture `gfx/interface/skinned/hud_maintab/aov_maintab_magic.dds`, visible on sGUI `aov_magic_available` (`aov_is_mage = yes`), onclick toggles `aov_magic_window` and clears `aov_artificery_window`; the Artificery tab's onclick also clears `aov_magic_window`.
- Window `aov_magic_window`: same frame/position pattern as `gui/aov_window_artificery.gui`; mana bar (`progressbar_standard`, value `aov_mana` / `aov_mana_max` x 100); study line; eight `button_tab`s with `school_<s>.dds` icons (variable `aov_magic_school`, unset = abjuration); scrollbox with generated type `aov_magic_school_<s>`.
- Generated types `aov_magic_school_<s>`: header (icon, name, `levels_strip.dds` frame = level, progress bar to `aov_school_<s>_next`, Study button = `aov_study_<s>_sgui`, down while studied) and one card per spell: `spell_plate.dds` background (290x64 scaled to the card width), icon `spell_slot_<slot>.dds` frame = school index (1-8), framesize 60x60, inside `spell_frames.dds` frame = level + 1; name, "Level N - M mana - Type - Y years"; Cast `button_standard` bound to the spell sGUI (S/R/W) or the text `AOV_SPELL_CAST_FROM_PORTRAIT` (T); cooldown text when `aov_spell_<k>_ready` fails; tooltip = desc + flavour + `[GetModifier(...).GetDescWithEffects]` for lasting spells.
- Card widths fit 480 px (see `test_card_rows_fit_the_factions_tab` in the factions tests).

- [ ] **Step 1: Tests**: HUD test asserts both tabs inserted, magic after artificery, each onclick clears the other window; generated gui has eight school types, 49 cards, targeted cards have no Cast button, every Cast binds its own sGUI; window file registers and has eight tab buttons; card row widths <= 480.
- [ ] **Step 2: Run; expect failures.** **Step 3: Implement**, rerun `python -I tools/build_hud_override.py` and `python -I tools/build_spells.py`. **Step 4: Tests + tiger.** **Step 5: Commit** `Add Magic tab and window`.

---

### Task 8: Documentation and verification

**Files:** Modify `CLAUDE.md` (Systems: Magic schools; Generated files: `build_spells.py` outputs; Updating Anbennar: re-copy the three spell interactions).

- [ ] **Step 1:** Update docs.
- [ ] **Step 2:** `python -I -m unittest discover -s tools/tests -v` and `python -I tools/validate.py`: all OK, tiger clean.
- [ ] **Step 3: In-game checklist (user):** Magic tab for a mage only; mana fills; Study raises a school and fires the level-up event; casting Guidance spends 25 mana, applies the modifier, starts a 1-year cooldown; Meteor Swarm only at war; Summon Elementals spawns an army at the capital and removes it after 3 years or at peace; Heartstring/Scry/Steal Vitality/Contagion/Ward in a character's Spells menu charge mana; Compel/Dominate/Enhance Ability need school level and mana; Necromancy in a witchcraft-illegal faith can give Forbidden Magic Practitioner; Field of Forbiddance blocks spells on you; `magic_mastery` icon tracks levels; error.log / gui_warnings.log clean of `aov_`.
- [ ] **Step 4: Commit** `Document magic schools`.
