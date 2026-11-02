# Artificery Rework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 60 EU4-era inventions with 48 period-appropriate ones, make discovered inventions permanently unlock buildings and men-at-arms, gate tiers on discoveries, and raise slots to 4/5/6.

**Architecture:** The roster lives in `tools/data/inventions.py` and `tools/build_inventions.py` generates every per-invention script file. The generator gains an `unlock` field, a per-invention `_unlock_ready` trigger, tier-gated `_unlocked` triggers and discovered-count values. Men-at-arms, buildings, slot values and loc are hand-written files that call those generated triggers. `tools/build_holdings_override.py` adds the buildings to castle and city build lists.

**Tech Stack:** CK3 1.19 script (UTF-8 BOM, LF, tabs), Python 3 generators, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-01-artificery-rework-design.md`

## Global Constraints

- Script and loc files: UTF-8 with BOM, LF line endings, tabs. Loc files keep the `l_english:` header.
- Never hand-edit generated files (`aov_invention_*` outputs, `common/holdings/00_holdings.txt`): change data or the generator, then rerun.
- Never write to `../anbennar-ck3-dev-master`.
- Every modifier line, stat and cost comes from the spec's tables, value for value.
- Character modifiers must not use `travel_speed` or `cultural_acceptance_gain_mult` (existing test).
- Descriptions are in period (1022–1453 AA): no engines, rails, radio, or flight beyond tethered balloons. No double quotes in names or descriptions.
- Run tests with `python -I -m unittest discover -s tools/tests -p "<file>"`; whole suite without `-v`.
- Work on branch `artificery-rework` (created in Task 1); commit per task.

## Review Focus

1. A ruler goes dormant (loses the academy, or the culture loses Gnomish Ingenuity) after discovering War Golems: recruitment and the three buildings must switch off, then come back when dormancy ends. Pinned by Task 2's `_unlock_ready` test (contains the dormant check) and Tasks 3–4's tests that every gate calls `_unlock_ready`.
2. An heir inherits the predecessor's sixth slot cooldown: the heir must not get a free extra slot. Pinned by Task 2's `test_inherit_copies_six_cooldowns`.
3. A county held by a vassal who has not discovered the invention: the vassal cannot build there, even though their liege can in their own domain. Pinned by Task 4's test that the potential checks `scope:holder`, not `root` or the liege.
4. Faith-locked Tier I inventions (Ancestral Golems, Sunblessed Armaments, Fey Spray) count toward the Tier II gate, and research cannot offer a Tier II invention before the gate opens. Pinned by Task 2's count test, which lists every Tier I key, and by the existing `_discoverable` → `_available` → `_unlocked` chain, which Task 2's gate test reads.
5. An old save that has removed invention keys logs missing-modifier errors. This can't be tested; Task 5 documents "start a new campaign" in `docs/systems/artificery.md`.

---

### Task 1: New roster and the `unlock` field

**Files:**
- Modify: `tools/data/inventions.py` (rewrite `INVENTIONS`)
- Modify: `tools/build_inventions.py:36` (`MAA_KEYS` → unlock sets), `validate()`
- Test: `tools/tests/test_build_inventions.py`
- Regenerated: all `build_inventions.py` outputs

**Interfaces:**
- Produces: each invention dict has fields `key, category, tier, faith, gnome_only, icon, modifier, unlock, name, desc` (no `maa`). `bi.MAA_UNLOCKS = {"aov_clockwork_repeaters", "aov_war_golems", "aov_gnomish_bombards", "armored_artificers"}`, `bi.BUILDING_UNLOCKS = {"aov_clockwork_mill_01", "aov_alchemical_distillery_01", "aov_damestear_foundry_01"}`.

- [ ] **Step 0: Branch**

```bash
git switch -c artificery-rework
```

- [ ] **Step 1: Rewrite `DataTests` and the key-specific asserts**

Replace `test_sixty_unique_inventions`, `test_category_counts_match_research_doc`, `test_maa_unlocks`, `test_locks` with:

```python
REMOVED = {"arcane_battery_capital_complex", "automated_translator", "market_mender", "plane_of_water_teleporter",
           "gene_food_cultivation", "vendorless_stall", "elemental_locomotives", "prefabricated_city_constructors",
           "t_wave_transceivers", "artificer_exo_arms", "commercial_sky_galleons", "magic_missile_deployer",
           "portable_turrets", "sparkdrive_rifles", "arcane_blaster", "balloonboost_packs", "coddorran_powered_exosuit",
           "gu_boats", "prototype_tanks", "artillery_autoloader", "bioartificed_ascension", "damestear_reactor_megacannon",
           "military_sky_galleons", "naval_mageshields", "personal_mageshields", "apparitional_communicator", "viewcatcher",
           "empire_engine", "think_thought_transmitters", "bureaucratizer", "crierless_crier_device", "negotiation_nexus",
           "runethought_network"}

def test_forty_eight_unique_inventions(self):
    self.assertEqual(len(INVENTIONS), 48)
    self.assertEqual(len(set(KEYS)), 48)

def test_category_tier_counts(self):
    counts = collections.Counter((i["category"], i["tier"]) for i in INVENTIONS)
    self.assertEqual(counts, {("economic", 1): 5, ("economic", 2): 4, ("economic", 3): 4,
                              ("military", 1): 6, ("military", 2): 7, ("military", 3): 6,
                              ("society", 1): 6, ("society", 2): 6, ("society", 3): 4})

def test_removed_keys_are_gone(self):
    self.assertFalse(REMOVED & set(KEYS))

def test_unlocks(self):
    self.assertEqual({i["key"]: i["unlock"] for i in INVENTIONS if i["unlock"]}, {
        "clockwork_waterwheels": "aov_clockwork_mill_01", "alchemical_distilleries": "aov_alchemical_distillery_01",
        "damestear_foundries": "aov_damestear_foundry_01", "clockwork_repeaters": "aov_clockwork_repeaters",
        "war_golems": "aov_war_golems", "gnomish_bombards": "aov_gnomish_bombards",
        "clockwork_plate_harness": "armored_artificers"})
    self.assertTrue(all("maa" not in i for i in INVENTIONS))

def test_locks(self):
    self.assertEqual(sum(1 for i in INVENTIONS if i["faith"]), 8)
    self.assertEqual({i["key"] for i in INVENTIONS if i["gnome_only"]}, {"conversation_calibrator", "automaton_labourers"})

def test_icon_matches_category_and_tier(self):
    code = {"economic": "Ec", "military": "Mi", "society": "So"}
    for i in INVENTIONS:
        with self.subTest(i["key"]):
            self.assertRegex(i["icon"], rf"^Artf_(Br|Ma|Te){code[i['category']]}{i['tier']}\.dds$")

def test_spot_check_modifiers(self):
    by = {i["key"]: i["modifier"] for i in INVENTIONS}
    self.assertEqual(by["damestear_powder"], "gunpowder_damage_mult = 0.25")
    self.assertEqual(by["gnomish_spectacles"].split("\n"),
                     ["diplomacy = 1", "martial = 1", "stewardship = 1", "intrigue = 1", "learning = 1", "prowess = 1"])
    self.assertEqual(by["universal_grammarye"], "different_culture_opinion = 25\ndiplomacy = 2")
    self.assertEqual(by["clerk_automatons"], "domain_limit = 1\nvassal_limit = 20")
```

In `ValidateTests` add:

```python
def test_rejects_unknown_unlock(self):
    with self.assertRaises(bi.GeneratorError):
        bi.validate([dict(INVENTIONS[0], unlock="aov_made_up")])

def test_rejects_duplicate_unlock(self):
    a = dict(INVENTIONS[0], key="a", unlock="aov_war_golems")
    b = dict(INVENTIONS[0], key="b", unlock="aov_war_golems")
    with self.assertRaises(bi.GeneratorError):
        bi.validate([a, b])
```

Switch the `sparkdrive_rifles` asserts to `damestear_powder`. Expected modifier block: `"aov_invention_damestear_powder = {\n\ticon = martial_positive\n\tgunpowder_damage_mult = 0.25\n}"`. Subtitle: `$AOV_CATEGORY_MILITARY$, $AOV_TIER_1$`. In `test_deactivate_newest_is_a_single_chain` the `else_if` count becomes 47; in `test_nine_sguis_per_invention` the total becomes `9 * 48`.

- [ ] **Step 2: Run, expect failures**

Run: `python -I -m unittest discover -s tools/tests -p "test_build_inventions.py"`
Expected: FAIL. The counts, unlocks and removed keys fail, and the unlock tests error with `KeyError: 'unlock'` or fail to raise.

- [ ] **Step 3: Generator validation**

In `build_inventions.py`, replace `MAA_KEYS` with `MAA_UNLOCKS` and `BUILDING_UNLOCKS` (values above). In `validate()`, replace the `maa` check: `unlock` must be `None` or in `MAA_UNLOCKS | BUILDING_UNLOCKS`, and no unlock may appear twice (`GeneratorError`, as the other checks do).

- [ ] **Step 4: Rewrite the roster**

Write `INVENTIONS` from the spec's Economic, Military and Society tables: key, category, tier, faith (existing allow-listed strings), `gnome_only`, `modifier` (spec lines joined by `\n`), `unlock`, and `name`. Sort the list by (category, tier, key), which the existing `test_sorted_by_category_tier_key` checks.
- **Kept and moved inventions:** keep their `desc`. Keep their icon unless the category or tier changed; then pick an existing icon of the same faction prefix that matches.
- **New and renamed inventions:** write a new one- or two-sentence `desc` in the existing voice (Global Constraints). Pick any committed `Artf_*` icon that matches category and tier. The only Tier III Society icon is `Artf_TeSo3.dds`.
- Update the module docstring: content is the overhaul's own roster, and the EU4 mapping is history.

- [ ] **Step 5: Run tests, expect pass**

Run: `python -I -m unittest discover -s tools/tests -p "test_build_inventions.py"`
Expected: OK.

- [ ] **Step 6: Regenerate**

Run: `python -I tools/build_inventions.py`
Expected: `wrote 8 files for 48 inventions`

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/2026-11-01-artificery-rework-design.md docs/superpowers/plans/2026-11-01-artificery-rework.md
git add tools/data/inventions.py tools/build_inventions.py tools/tests/test_build_inventions.py common gui localization
git commit -m "Artificery: 48 period inventions with unlock field"
```

(`test_artificery_research.test_maa_gated_on_active_invention` fails until Task 3.)

---

### Task 2: Unlock triggers, tier gate, slots

**Files:**
- Modify: `tools/build_inventions.py`: `triggers()`, `values()`, `tooltip_type()`, `loc()`
- Modify: `common/script_values/aov_artificery_values.txt`
- Modify: `common/scripted_effects/aov_artificery_research_effects.txt` (`aov_artificery_start_slot_cooldown` at line 101; inherit lines 296–300)
- Modify: `localization/english/aov_artificery_l_english.yml:48-49`
- Test: `tools/tests/test_build_inventions.py`, `tools/tests/test_artificery_research.py`

**Interfaces:**
- Consumes: `unlock` field, `MAA_UNLOCKS`, `BUILDING_UNLOCKS` (Task 1).
- Produces: trigger `aov_invention_<key>_unlock_ready` (character scope, every invention). Script values `aov_inventions_t1_discovered_count`, `aov_inventions_t2_discovered_count` (generated) and `aov_invention_tier_gate_count` (hand-written, 6). Loc key `aov_invention_<key>_unlock_tt` (only for inventions with an unlock).

- [ ] **Step 1: Write failing generator tests** (in `ScriptOutputTests` / `GuiOutputTests`)

```python
def test_unlock_ready_per_invention(self):
    text = bi.triggers(INVENTIONS)
    for k in KEYS:
        block = re.search(rf"^aov_invention_{k}_unlock_ready = \{{\n(.*?)\n\}}", text, re.M | re.S).group(1)
        self.assertEqual(block, f"\taov_invention_{k}_discovered = yes\n\taov_invention_{k}_visible = yes\n"
                                "\tNOT = { has_variable = aov_artificery_dormant }")

def test_unlocked_gates_on_lower_tier_discoveries(self):
    text = bi.triggers(INVENTIONS)
    for i in INVENTIONS:
        block = re.search(rf"^aov_invention_{i['key']}_unlocked = \{{\n(.*?)\n\}}", text, re.M | re.S).group(1)
        if i["tier"] == 1:
            self.assertNotIn("discovered_count", block)
        else:
            self.assertIn(f"aov_inventions_t{i['tier'] - 1}_discovered_count >= aov_invention_tier_gate_count", block)

def test_discovered_counts_list_their_tier(self):
    text = bi.values(INVENTIONS)
    self.assertEqual(top_level_blocks(text), ["aov_invention_active_count", "aov_invention_newest_order",
                                              "aov_inventions_t1_discovered_count", "aov_inventions_t2_discovered_count"])
    for t in (1, 2):
        block = re.search(rf"^aov_inventions_t{t}_discovered_count = \{{\n(.*?)\n\}}", text, re.M | re.S).group(1)
        self.assertEqual(set(re.findall(r"aov_invention_([a-z0-9_]+)_discovered = yes", block)),
                         {i["key"] for i in INVENTIONS if i["tier"] == t})

def test_unlock_tooltip_and_loc(self):
    gui, lc = bi.gui(INVENTIONS), bi.loc(INVENTIONS)
    for i in INVENTIONS:
        k = i["key"]
        tt = gui.split(f"type aov_invention_{k}_tooltip = object_tooltip_pop_out {{")[1].split("\n\t}\n")[0]
        if i["unlock"]:
            name = f"building_{i['unlock']}" if i["unlock"] in bi.BUILDING_UNLOCKS else i["unlock"]
            self.assertIn(f'text = "aov_invention_{k}_unlock_tt"', tt)
            self.assertIn(f' aov_invention_{k}_unlock_tt: "#P Unlocks#! ${name}$ #weak (permanent once discovered)#!"', lc)
        else:
            self.assertNotIn("_unlock_tt", tt)
```

Also add `"unlock_ready"` to the suffix list in `test_triggers_per_invention`.

In `test_artificery_research.py`, replace `test_cooldowns_cover_five_slots` and add tests:

```python
def test_cooldowns_cover_six_slots(self):
    b = block(read("common/scripted_effects/aov_artificery_research_effects.txt"), "aov_artificery_start_slot_cooldown")
    for n in range(1, 7):
        self.assertIn(f"set_variable = {{ name = aov_slot_cd_{n} years = 1 }}", b)

def test_inherit_copies_six_cooldowns(self):
    text = read("common/scripted_effects/aov_artificery_research_effects.txt")
    for n in range(1, 7):
        self.assertIn(f"scope:aov_predecessor = {{ has_variable = aov_slot_cd_{n} }}", text)

def test_slots_and_tier_gate_values(self):
    text = read("common/script_values/aov_artificery_values.txt")
    slots = block(text, "aov_invention_slots_max")
    self.assertRegex(slots, r"^\tvalue = 4\n")
    self.assertIn("value = 5", slots)
    self.assertIn("value = 6", slots)
    self.assertIn("has_variable = aov_slot_cd_6", block(text, "aov_invention_slots_cooling"))
    self.assertRegex(text, r"(?m)^aov_invention_tier_gate_count = 6$")

def test_tier_lock_loc_shows_progress(self):
    text = read("localization/english/aov_artificery_l_english.yml")
    for t, prev in ((2, 1), (3, 2)):
        line = next(l for l in text.splitlines() if l.startswith(f" AOV_INV_LOCKED_TIER_{t}_TT:"))
        self.assertIn("ScriptValue('aov_invention_tier_gate_count')", line)
        self.assertIn(f"ScriptValue('aov_inventions_t{prev}_discovered_count')", line)
```

- [ ] **Step 2: Run, expect failures**

Run: `python -I -m unittest discover -s tools/tests -p "test_build_inventions.py"` and the same with `-p "test_artificery_research.py"`
Expected: the new tests FAIL.

- [ ] **Step 3: Generator**

- `triggers()`: emit `aov_invention_<k>_unlock_ready` (body exactly as the test). For tier 2 and 3, `_unlocked` adds the line `aov_inventions_t<tier-1>_discovered_count >= aov_invention_tier_gate_count` after the era check.
- `values()`: append the two count values: `value = 0` plus one `if = { limit = { aov_invention_<k>_discovered = yes } add = 1 }` per invention of that tier, in the style of `aov_invention_active_count`.
- `tooltip_type()`: for an invention with `unlock`, add an unconditional paragraph `aov_invention_<k>_unlock_tt` after the effects paragraph.
- `loc()`: for those inventions, emit `aov_invention_<k>_unlock_tt` with the exact text in the test. A building's name key is `building_<unlock>`; an MaA's is the MaA key.

- [ ] **Step 4: Hand-written files**

- `aov_artificery_values.txt`: slots 4 / 5 (High Medieval) / 6 (Late Medieval), with the comment updated. Add `has_variable = aov_slot_cd_6` to the cooling value. Add the line `aov_invention_tier_gate_count = 6` with the comment `# Tier II/III need this many discoveries of the tier below (with the era)`.
- `aov_artificery_research_effects.txt`: a sixth `else_if` for `aov_slot_cd_6` in `aov_artificery_start_slot_cooldown`, and a sixth inherit line after line 300.
- Loc, replacing lines 48–49:
  ` AOV_INV_LOCKED_TIER_2_TT: "#N Locked:#! requires the High Medieval era and [GetPlayer.MakeScope.ScriptValue('aov_invention_tier_gate_count')|0] Tier I inventions discovered ([GetPlayer.MakeScope.ScriptValue('aov_inventions_t1_discovered_count')|0] so far)."`
  Tier 3 is the same with "Late Medieval", "Tier II" and `t2`.

- [ ] **Step 5: Run tests, expect pass**

Run both test files as in Step 2. Expected: OK, except `test_maa_gated_on_active_invention` (Task 3).

- [ ] **Step 6: Regenerate and commit**

```bash
python -I tools/build_inventions.py
git add tools common gui localization
git commit -m "Artificery: permanent unlocks, tier gate on discoveries, 4/5/6 slots"
```

---

### Task 3: Men-at-arms

**Files:**
- Modify: `common/men_at_arms_types/aov_invention_maa_types.txt` (rewrite)
- Modify: `common/men_at_arms_types/zz_aov_gnome_maa_overrides.txt` (`armored_artificers` block, header comment)
- Modify: `localization/english/aov_artificery_l_english.yml:102-107`
- Create: `localization/english/replace/aov_artificery_replace_l_english.yml`
- Test: `tools/tests/test_artificery_research.py`

**Interfaces:**
- Consumes: `aov_invention_<key>_unlock_ready` (Task 2); `has_enabled_artificer_academy_trigger` (existing).

- [ ] **Step 1: Write failing tests** (replace `test_maa_gated_on_active_invention`)

```python
MAA = {"aov_clockwork_repeaters": ("clockwork_repeaters", 55, 23), "aov_war_golems": ("war_golems", 45, 31)}

def test_invention_maa_file_and_gates(self):
    text = read("common/men_at_arms_types/aov_invention_maa_types.txt")
    self.assertEqual(re.findall(r"^([a-z_]+) = \{", text, re.M),
                     ["aov_clockwork_repeaters", "aov_war_golems", "aov_gnomish_bombards"])
    for maa, inv in (("aov_clockwork_repeaters", "clockwork_repeaters"), ("aov_war_golems", "war_golems"),
                     ("aov_gnomish_bombards", "gnomish_bombards")):
        b = block(text, maa)
        self.assertIn(f"aov_invention_{inv}_unlock_ready = yes", b)
        self.assertIn("has_enabled_artificer_academy_trigger = yes", b)
    for maa, (_, dmg, tough) in MAA.items():
        b = block(text, maa)
        self.assertIn(f"\tdamage = {dmg}\n", b)
        self.assertIn(f"\ttoughness = {tough}\n", b)
    bomb = block(text, "aov_gnomish_bombards")
    for line in ("type = siege_weapon", "siege_tier = 4", "siege_value = 0.75", "toughness = 12", "stack = 10"):
        self.assertIn(line, bomb)

def test_armored_artificers_reenabled(self):
    text = read("common/men_at_arms_types/zz_aov_gnome_maa_overrides.txt")
    b = block(text, "armored_artificers")
    for line in ("type = gunpowder", "damage = 45", "toughness = 30", "stack = 75",
                 "aov_invention_clockwork_plate_harness_unlock_ready = yes", "has_enabled_artificer_academy_trigger = yes"):
        self.assertIn(line, b)
    self.assertNotIn("always = no", b)
    self.assertIn("can_recruit = { always = no }", block(text, "artificers"))

def test_maa_loc(self):
    text = read("localization/english/aov_artificery_l_english.yml")
    self.assertNotIn("aov_prototype_tanks", text)
    self.assertNotIn("megacannon", text)
    for k in ("aov_clockwork_repeaters", "aov_gnomish_bombards", "aov_war_golems"):
        self.assertIn(f" {k}:", text)
        self.assertIn(f" {k}_flavor:", text)
    self.assertIn(" armored_artificers_flavor:", read("localization/english/replace/aov_artificery_replace_l_english.yml"))
```

- [ ] **Step 2: Run, expect failure**

Run: `python -I -m unittest discover -s tools/tests -p "test_artificery_research.py"`. Expected: the three new tests FAIL.

- [ ] **Step 3: Rewrite `aov_invention_maa_types.txt`**

Delete the tanks and megacannon blocks. Keep the `@` variables the remaining blocks use: `@cultural_maa_extra_ai_score`, `@provisions_cost_infantry_moderate`, `@provisions_cost_special_expensive`. Header: "recruitable once their invention is discovered (permanent; off while artificery is dormant)", with the stat derivations from the spec.
- `aov_clockwork_repeaters`: vanilla `crossbowmen` shape (counters `heavy_infantry = 1 heavy_cavalry = 1 archer_cavalry = 0.5`, crossbow terrain bonuses), damage 55, toughness 23, stack 100, `crossbowmen_*` costs, `icon = crossbowmen`.
- `aov_war_golems`: damage 45, toughness 31.
- `aov_gnomish_bombards`: vanilla `bombard` shape, `siege_value = 0.75`, `bombard_*` costs, `provision_cost = @provisions_cost_special_expensive`, `allowed_in_hired_troops = no`, `icon = bombard`.

Each `can_recruit` is `aov_invention_<inv>_unlock_ready = yes` plus `has_enabled_artificer_academy_trigger = yes`.

- [ ] **Step 4: `armored_artificers` override**

`type = gunpowder`, damage 45, toughness 30, stack 75, and `can_recruit` as above with `clockwork_plate_harness`. Keep the rest of Anbennar's block. Update the file header: Armored Artificers come back with Clockwork Plate Harness.

- [ ] **Step 5: Loc**

Remove lines 102–103 and 106–107. Change the War Golems flavor's help line to `Recruitable once [GetModifier('aov_invention_war_golems').GetName] is discovered.` Add name and flavor for Clockwork Repeaters and Gnomish Bombards in the same form. Create the replace file (BOM, `l_english:`) with `armored_artificers_flavor`: a period flavor line plus the same help line for `aov_invention_clockwork_plate_harness`.

- [ ] **Step 6: Run tests, expect pass**

Run: `python -I -m unittest discover -s tools/tests -p "test_artificery_research.py"`. Expected: OK.

- [ ] **Step 7: Commit**

```bash
git add common/men_at_arms_types localization tools/tests/test_artificery_research.py
git commit -m "Artificery: repeaters, bombards, stronger golems and armored artificers unlocked by inventions"
```

---

### Task 4: Invention buildings

**Files:**
- Create: `common/buildings/aov_invention_buildings.txt`
- Modify: `tools/build_holdings_override.py:22-23` (`ADDITIONS`)
- Regenerated: `common/holdings/00_holdings.txt`
- Modify: `localization/english/aov_artificery_l_english.yml` (building loc)
- Test: `tools/tests/test_build_holdings_override.py:105`, `tools/tests/test_artificery_research.py`

**Interfaces:**
- Consumes: `aov_invention_<key>_unlock_ready` (Task 2).
- Produces: buildings `aov_clockwork_mill_01`, `aov_alchemical_distillery_01`, `aov_damestear_foundry_01`; loc `building_type_<b>`, `building_type_<b>_desc`, `building_<b>`, `building_<b>_desc`, `<b>_effect_desc`.

- [ ] **Step 1: Write failing tests**

In `test_artificery_research.py`:

```python
BUILDINGS = {
    "aov_clockwork_mill_01": ("clockwork_waterwheels", 150, "icon_building_watermills.dds",
                              ["tax_mult = 0.15", "development_growth_factor = 0.1"]),
    "aov_alchemical_distillery_01": ("alchemical_distilleries", 250, "icon_building_breweries.dds",
                                     ["tax_mult = 0.2", "county_opinion_add = 5"]),
    "aov_damestear_foundry_01": ("damestear_foundries", 400, "icon_building_wind_furnaces.dds",
                                 ["tax_mult = 0.25", "development_growth_factor = 0.15", "levy_size = 0.15"]),
}

def test_invention_buildings(self):
    text = read("common/buildings/aov_invention_buildings.txt")
    self.assertEqual(re.findall(r"^([a-z0-9_]+) = \{", text, re.M), list(BUILDINGS))
    for b, (inv, cost, icon, mods) in BUILDINGS.items():
        body = block(text, b)
        gate = f"scope:holder = {{ aov_invention_{inv}_unlock_ready = yes }}"
        self.assertIn(gate, body.split("can_construct_potential = {")[1].split("\n\t}")[0])
        self.assertIn(gate, body.split("is_enabled = {")[1].split("\n\t}")[0])
        self.assertIn("show_disabled = yes", body)
        self.assertIn(f"cost_gold = {cost}", body)
        self.assertIn(f'type_icon = "{icon}"', body)
        county = body.split("county_modifier = {")[1].split("}")[0]
        for m in mods:
            self.assertIn(m, county)

def test_invention_building_loc(self):
    text = read("localization/english/aov_artificery_l_english.yml")
    for b in BUILDINGS:
        for key in (f"building_type_{b}", f"building_type_{b}_desc", f"building_{b}", f"building_{b}_desc", f"{b}_effect_desc"):
            self.assertIn(f" {key}:", text)
```

In `test_build_holdings_override.py:105`, the expected list becomes `["artificer_academy_01", "battlemage_academy_01", "aov_clockwork_mill_01", "aov_alchemical_distillery_01", "aov_damestear_foundry_01"] + rie.SURFACE_BUILDINGS + rie.MINE_BUILDINGS`. In `test_generated_holdings`, assert all three are in `out["castle_holding"]` and `out["city_holding"]`.

- [ ] **Step 2: Run, expect failure**

Run each file with `-p`. Expected: the new tests FAIL.

- [ ] **Step 3: Building file**

Copy the shape of `artificer_academy_01` (`common/buildings/aov_artificer_buildings.txt`), minus the academy triggers, character modifier and `flag`. For each building:
- `construction_time`: `standard_construction_time` for the mill, `slow_construction_time` for the others.
- `can_construct_potential`: `building_requirement_tribal = no`, `building_requirement_castle_city_church = { LEVEL = 01 }`, plus the holder gate. `is_enabled` holds the holder gate alone.
- `show_disabled = yes`, `cost_gold`, `type_icon`, and `county_modifier` lines from the spec.
- `effect_desc = { desc = <b>_effect_desc }`.
- `ai_value = { base = 20 ai_general_building_modifier = yes }`.

Header comment: unlocked permanently by the named invention and off while the holder's artificery is dormant (see `docs/systems/artificery.md`).

- [ ] **Step 4: Holdings and loc**

Insert the three keys after `"battlemage_academy_01"` in both `ADDITIONS` lists. Run `python -I tools/build_holdings_override.py`. Expected: it writes `common/holdings/00_holdings.txt` with no error. Add the five loc keys per building in the academy's pattern (lines 10–14). The effect description reads `#low Unlocked by#! [GetModifier('aov_invention_<inv>').GetName]#low , permanently once discovered.#!`.

- [ ] **Step 5: Run tests, expect pass**

Run: `python -I -m unittest discover -s tools/tests -p "test_artificery_research.py"` and `-p "test_build_holdings_override.py"`. Expected: OK.

- [ ] **Step 6: Commit**

```bash
git add common/buildings/aov_invention_buildings.txt common/holdings tools/build_holdings_override.py tools/tests localization
git commit -m "Artificery: Clockwork Mill, Alchemical Distillery and Damestear Foundry unlocked by inventions"
```

---

### Task 5: Docs and validation

**Files:**
- Modify: `docs/systems/artificery.md` (Artificery inventions bullet, Inventions tab UI bullet, new Unlocks bullet)
- Modify: `CLAUDE.md` (systems table, artificery row: "60 inventions" → "48 inventions, invention buildings and men-at-arms")
- Modify: `docs/systems/updating.md` only if it lists the holdings additions by name (check with grep)

- [ ] **Step 1: Docs**

`artificery.md`:
- 48 inventions from `tools/data/inventions.py`, the overhaul's own roster (the EU4 mapping doc is history).
- Hybrid: unlocks are permanent once discovered and off while dormant (`_unlock_ready`); modifiers need a slot.
- Slots are 4/5/6.
- Tier II/III need the era plus `aov_invention_tier_gate_count` (6) discoveries of the tier below.
- Three buildings in `aov_invention_buildings.txt`, added by `build_holdings_override.py`.
- Men-at-arms: Repeaters, War Golems, Bombards, and Armored Artificers re-enabled as `gunpowder`.
- Saves from before this change: start a new campaign.

- [ ] **Step 2: Full test suite**

Run: `python -I -m unittest discover -s tools/tests`
Expected: `OK` (skips allowed).

- [ ] **Step 3: Validation**

Run: `python -I tools/validate.py`
Expected: no new reports. If tiger reports a key in the new files, fix it at the source and rerun; never baseline new-file reports.

- [ ] **Step 4: Commit**

```bash
git add docs CLAUDE.md
git commit -m "Docs: artificery rework"
```

- [ ] **Step 5: In-game checklist for the user** (not run by the implementer)

- At game start, a gnomish artificer ruler has 4 slots.
- The Tier II tab is locked, showing "(N so far)".
- After discovering Clockwork Waterwheels, the Clockwork Mill can be built without the invention active.
- Clockwork Plate Harness makes Armored Artificers recruitable.
- Removing the academy disables the mill, and the Repeaters can no longer be recruited.
- `error.log` has no new lines for the `aov_invention_*` files, the buildings or the men-at-arms.
