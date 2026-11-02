# Spell Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 48 spells with the revised, school-themed list: 28 kept or strengthened, 20 new, 20 removed.

**Architecture:** First the generator (`tools/build_spells.py`) learns hostile spells (a land roll, a miss path, AI
weights), curse and dispel lists, per-spell target triggers and extra cast requirements. A shared spawned-army helper
replaces the elementals-only code. Then each school is one task: its block in `tools/data/spells.py` plus the
hand-written effects, events, modifiers and loc behind it, regenerated and tested.

**Tech Stack:** CK3 1.19.0.6 script (Jomini), Python 3 generator and `unittest` static tests.

**Spec:** `docs/superpowers/specs/2026-11-01-spell-revision-design.md`

## Global Constraints

- Script and loc files: UTF-8 with BOM, LF, tabs. New hand-written content goes in existing `aov_magic_*` files (or
  new `aov_`-prefixed files); never edit `../anbennar-ck3-dev-master`.
- Generated files (`aov_spell_*`, `gui/aov_magic_generated.gui`, `aov_spells_l_english.yml`) are never edited by hand:
  edit `tools/data/spells.py` or `tools/build_spells.py`, then run `python -I tools/build_spells.py`.
- Six spells per school at levels 0/1/1/2/2/3 (slots 1-6); costs 25/50/100/200 mana, durations 1/2/3/5 years
  (`COSTS`, `YEARS`): unchanged.
- Every chance and amount that is not a modifier line lives in `common/script_values/aov_spell_tuning.txt` (new).
- Verify every engine identifier not already used in this repo against vanilla usage in
  `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game` (no script_docs dump).
- Tests: `python -I -m unittest discover -s tools/tests -p "<file>"`; the full run has no `-v`.
- Commit only with the user's go-ahead for this branch of work; messages end with the session's attribution lines.

## Review Focus

- A summoned army whose war ends, or whose caster dies, before the spell runs out must still vanish: the removal
  event is scheduled on the caster and guards a missing army (Task 1 test `test_spell_army_removal_guarded`); Bound
  Champion's vanish event runs on the champion, not the caster (Task 3 `test_champion_vanishes_on_their_own`).
- A caster with no capital and no location: army spells refund mana and clear the cooldown (Task 1
  `test_spell_army_fizzle_refunds`).
- Perfect Form never offers a trait the caster has, never upgrades past tier 3, never offers a good trait while the bad
  one of that group is held, and is uncastable with an empty pool (Task 9 `test_perfect_form_pool_guards`).
- Targets that cannot take the effect are not valid: Plague Cloud and Earthquake need a capital province, Grand
  Deception a held county, Dominate's surrender only when caster and target are the war's two primary participants
  (Tasks 6, 7, 8, 5 `test_*_target_trigger`).
- Hostile spells on a Field of Forbiddance target stay blocked, including the two hand-written Enchantment
  interactions (Task 5 `test_enchantment_interactions_respect_forbiddance`).

---

## File map

| File | Responsibility | Tasks |
|---|---|---|
| `tools/build_spells.py` | New data fields, hostile roll, miss path, curse/dispel lists, target triggers, cast requirements, AI weights | 1 |
| `tools/data/spells.py` | The spell list; one school block per task | 2-9 |
| `common/script_values/aov_spell_tuning.txt` (new) | Land chance and every per-spell number | 1-9 |
| `common/scripted_effects/aov_magic_effects.txt` | Hand-written spell effects; shared army helper | 1-9 |
| `common/scripted_triggers/aov_magic_triggers.txt` | Target triggers, cast requirements, AI target trigger | 1-9 |
| `events/aov_magic_events.txt` | Removal, miss, choice and result events | 1-9 |
| `common/modifiers/aov_magic_modifiers.txt` | Curse modifiers on targets, choice-event modifiers, county modifiers | 2-9 |
| `common/opinion_modifiers/aov_magic_opinion_modifiers.txt` | `aov_attempted_hostile_magic` | 1 |
| `common/character_interactions/aov_magic_interactions.txt` (new) | Thoughtweave and Dominate (secondary recipient, send options) | 5 |
| `common/character_interactions/zz_aov_spell_overrides.txt` | Stubs hiding Anbennar's Compel and Dominate | 5 |
| `common/men_at_arms_types/aov_magic_maa_types.txt` | `aov_conjured_beasts` | 3 |
| `common/scripted_character_templates/aov_magic_templates.txt` | `aov_bound_champion_template` | 3 |
| `localization/english/aov_magic_l_english.yml` | Loc for everything hand-written | 1-9 |
| `tools/data/advancements.py`, `tools/tests/test_advancements.py` | Orb texts and Augury | 4 |
| `tools/tests/test_build_spells.py` | Generator tests | 1-9 |
| `tools/tests/test_spell_schools.py` (new) | One class per school for hand-written behaviour | 2-9 |
| `tools/tests/test_magic_system.py` | Tests of removed spells and the Compel/Dominate overrides move or go | 1, 5, 9 |
| `docs/systems/magic.md` | Spell summary | 10 |

---

### Task 1: Generator support for hostile spells, curses, dispel, target triggers and summoned armies

**Files:**
- Modify: `tools/build_spells.py`, `tools/data/spells.py` (the `spell()` helper and its docstring only)
- Modify: `common/scripted_effects/aov_magic_effects.txt` (`aov_summon_elementals`), `events/aov_magic_events.txt` (`aov_magic.10`, new `aov_magic.50`)
- Modify: `common/scripted_triggers/aov_magic_triggers.txt`, `common/opinion_modifiers/aov_magic_opinion_modifiers.txt`, `localization/english/aov_magic_l_english.yml`
- Create: `common/script_values/aov_spell_tuning.txt`
- Test: `tools/tests/test_build_spells.py`, `tools/tests/test_magic_system.py` (`SpecialSpellTests`)

**Interfaces:**
- Produces, `spell()` gains keyword fields (all default empty/False):
  - `hostile: bool`: targeted only; the cast runs the land roll.
  - `target_trigger: str`: a hand-written trigger evaluated at the interaction's top level, with scope:actor and
    scope:recipient; generated interactions add `{target_trigger} = yes` to `is_valid_showing_failures_only`.
  - `curse: str`: the key of the modifier this spell puts on its target (hand-written in `aov_magic_modifiers.txt`).
  - `requires: str` and `requires_text: str`: an extra caster trigger in `aov_spell_<k>_castable` inside
    `custom_tooltip = { text = aov_spell_<k>_req <requires> = yes }`; the loc line `aov_spell_<k>_req` is
    `requires_text`.
- Produces, generated effects (character scope):
  - `aov_spell_<k>_cast` for a hostile spell: cost, progress, XP and cooldown as now, then
    `random_list = { aov_spell_land_chance = { <modifier and effect lines> } aov_spell_miss_chance = { aov_spell_missed = yes } }`.
    The necromancy dark-magic roll stays outside the `random_list`.
  - `aov_spell_remove_curses`: `remove_character_modifier` for every spell's `curse`, each guarded by `has_character_modifier`.
  - `aov_spell_dispel_war_spells`: the same for every lasting `war` spell's `aov_spell_<k>`.
- Produces, hand-written:
  - `aov_spell_land_chance` and `aov_spell_miss_chance` (script values, caster scope, need scope:recipient), in `aov_spell_tuning.txt`.
  - `aov_spell_missed` (effect, caster scope): the target gets opinion `aov_attempted_hostile_magic` toward the caster (−30, 5 years) and event `aov_magic.50` (the target is told who tried).
  - `aov_spawn_spell_army = { SPELL TYPE STACKS }` (effect, caster scope, assumes `aov_spell_army_possible = yes`): spawn at the capital province, else the location, bound to a random war of the caster, `inheritable = no`, `uses_supply = no`, saved as `scope:aov_spell_army`, then `trigger_event = { id = aov_magic.10 years = aov_spell_$SPELL$_years }`.
  - `aov_spell_army_possible` (trigger): a capital province or a location, and a war.
  - `aov_spell_army_fizzle = { SPELL }` (effect): refund `aov_spell_$SPELL$_cost` and remove `aov_spell_$SPELL$_cd`.
  - `aov_spell_ai_hostile_target` (trigger, interaction scopes): the recipient is the actor's rival, or at war with the actor.

- [ ] **Step 1: Write failing generator tests** in `tools/tests/test_build_spells.py`, a new class `HostileSpellTests` that builds a small in-memory list with `bs_data.spell(...)` (import `tools/data/spells.py` as the test file already does) rather than relying on the real data:
  - `test_hostile_cast_rolls_to_land`: for a hostile spell `x` with modifier `prowess = 1` and effect `foo = yes`, `block(bs.effects(L), "aov_spell_x_cast")` contains `random_list = {`, `aov_spell_land_chance = {`, `aov_spell_miss_chance = {`, `aov_spell_missed = yes`, and both `add_character_modifier = { modifier = aov_spell_x` and `foo = yes` appear after `aov_spell_land_chance = {`.
  - `test_friendly_cast_does_not_roll`: a non-hostile targeted spell's cast has no `random_list`.
  - `test_necromancy_roll_outside_land_roll`: for a hostile necromancy spell, `aov_dark_magic_roll = yes` appears after the closing of the `random_list`.
  - `test_validate_rejects_hostile_window_spell` and `test_validate_rejects_target_trigger_on_window_spell`: `GeneratorError`.
  - `test_target_trigger_in_interaction`: `foo_target = yes` inside `is_valid_showing_failures_only` of `aov_spell_x_interaction`.
  - `test_requires_in_castable`: `requires="foo_possible"` yields `text = aov_spell_x_req` and `foo_possible = yes` in `aov_spell_x_castable`, and loc has `aov_spell_x_req: "<requires_text>"`.
  - `test_remove_curses_and_dispel_lists`: `aov_spell_remove_curses` names every `curse`; `aov_spell_dispel_war_spells` names `aov_spell_<k>` for every lasting war spell and no other type.
  - `test_hostile_ai_weights`: a hostile generated interaction's `ai_will_do` contains `aov_spell_ai_hostile_target = yes`, and it has `ai_targets` and `ai_frequency`; a friendly one keeps `base = 0` only.
  - `test_scales_duration_with_effect_only`: `validate` accepts `scales_duration=True` with an effect and no modifier (the `summon_elementals` exception goes).
- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p "test_build_spells.py"`. Expected: the new tests FAIL (unknown keyword `hostile`).
- [ ] **Step 3: Implement the fields in `spell()`** (`tools/data/spells.py`) and document them in its docstring.
- [ ] **Step 4: Implement them in `tools/build_spells.py`**: `validate` (hostile/target_trigger only on targeted; `requires_text` required with `requires`; the scales_duration rule), `effects` (roll, lists), `triggers` (requires), `interactions` (target trigger, AI), `loc` (`_req`). AI block for hostile spells: `ai_targets` with the vanilla values for rivals and war enemies (copy the exact `ai_recipients` keys from a vanilla hostile interaction such as murder), `ai_frequency = 12`, `ai_will_do = { base = 0 modifier = { add = 60 aov_spell_ai_hostile_target = yes } modifier = { factor = 0 scope:actor = { aov_spell_land_chance < 40 } } }`.
- [ ] **Step 5: Write failing hand-written tests** in `tools/tests/test_magic_system.py` `SpecialSpellTests`, replacing the elementals tests:
  - `test_spell_army_helper`: block `aov_spawn_spell_army` contains `spawn_army`, `type = $TYPE$`, `stacks = $STACKS$`, `inheritable = no`, `uses_supply = no`, `save_scope_as = aov_spell_army`, `id = aov_magic.10`, `years = aov_spell_$SPELL$_years`.
  - `test_spell_army_removal_guarded`: `aov_magic.10` contains `exists = scope:aov_spell_army` and `scope:aov_spell_army = { deplete_army_by_percentage = 1 }`.
  - `test_spell_army_fizzle_refunds`: `aov_spell_army_fizzle` contains `aov_mana_change = { AMOUNT = aov_spell_$SPELL$_cost }` and `remove_variable = aov_spell_$SPELL$_cd`.
  - `test_land_chance_terms`: `aov_spell_land_chance` in `aov_spell_tuning.txt` contains `value = 75`, `multiply = 3`, `scope:recipient`, `multiply = 10`, `aov_spell_ward_target`, `subtract = 30`, `min = 10`, `max = 95`.
  - `test_missed_spell_tells_target`: `aov_spell_missed` contains `modifier = aov_attempted_hostile_magic`, `years = 5`, `id = aov_magic.50`; the opinion modifier has `opinion = -30`.
- [ ] **Step 6: Implement them.** `aov_summon_elementals` becomes: `if = { limit = { aov_spell_army_possible = yes } aov_spawn_spell_army = { SPELL = summon_elementals TYPE = aov_conjured_elementals STACKS = 4 } } else = { aov_spell_army_fizzle = { SPELL = summon_elementals } }` (Task 3 raises it to 6). Drop the `aov_elemental_army` variable. Add the `aov_magic.50` event (character event, the caster as right portrait, one option) and its loc, and the opinion modifier loc.
- [ ] **Step 7: Regenerate and run** `python -I tools/build_spells.py`, then `python -I -m unittest discover -s tools/tests -p "test_build_spells.py"` and `-p "test_magic_system.py"`. Expected: PASS (no spell is hostile yet, so generated output changes only by the new empty lists).
- [ ] **Step 8: Commit** `feat(magic): hostile spell roll, curses, dispel and a shared summoned-army helper`.

### Task 2: Abjuration

**Files:** `tools/data/spells.py` (Abjuration block), `aov_magic_effects.txt`, `aov_magic_modifiers.txt`, loc, `tools/tests/test_spell_schools.py` (create, with `read`/`block` helpers copied from `test_magic_system.py`), `tools/tests/test_build_spells.py`.

**Interfaces:**
- Consumes: `aov_spell_remove_curses`, `aov_spell_dispel_war_spells` (Task 1).
- Produces: `aov_purify` (effect, caster scope); modifier `aov_spell_ward_target` keeps its key (read by the land chance).

- [ ] **Step 1: Write failing tests**, class `AbjurationTests`:
  - data: keys in slot order `combat_ward, ward, purify, mass_ward, mage_armor, field_of_forbiddance`; `combat_ward` modifier has `prowess = 6` and `health = 0.25`; `mass_ward` has `garrison_size = 0.5`, `defender_advantage = 6`; `mage_armor` has `maa_toughness_mult = 0.25` and a levy toughness line; `field_of_forbiddance` modifier has `enemy_hostile_scheme_success_chance_add = -30` and its effect is `aov_spell_dispel_war_spells = yes`.
  - `aov_spell_ward_target` modifier has `enemy_hostile_scheme_success_chance_add = -30`.
  - `aov_purify` contains `aov_spell_remove_curses = yes`, `add_stress = -20`, and the old `aov_remove_pain` cure lines (copy its assertions); `aov_remove_pain` no longer exists.
- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p "test_spell_schools.py"`. Expected: FAIL.
- [ ] **Step 3: Implement** the data block (spec Abjuration table; Purify is `self`, slot 3, effect `aov_purify = yes`); rename `aov_remove_pain` to `aov_purify` and extend it; strengthen `aov_spell_ward_target`. Levy toughness: use the vanilla modifier `levy_toughness` (check its scale in vanilla before choosing the amount; aim for the same weight as +25% on men-at-arms).
- [ ] **Step 4: Regenerate and run** the build, then `test_spell_schools.py` and `test_build_spells.py`. Expected: PASS after updating `test_build_spells.py` asserts that named `protected_journey` (`test_land_spells_need_land` uses another non-land spell instead, e.g. `combat_ward`).
- [ ] **Step 5: Commit** `feat(magic): Abjuration revised`.

### Task 3: Conjuration

**Files:** data block, `aov_magic_effects.txt`, `aov_magic_events.txt`, `aov_magic_maa_types.txt`, `aov_magic_templates.txt`, loc, `test_spell_schools.py`.

**Interfaces:**
- Consumes: `aov_spawn_spell_army`, `aov_spell_army_possible`, `aov_spell_army_fizzle` (Task 1); `var:aov_adv_host` with `flag:angels|eldritch|devils` and types `aov_host_angels|eldritch|devils` (Summon Extraplanars advancement); event `aov_magic.20` (Extraplanar bargain).
- Produces: effects `aov_summon_beasts`, `aov_bound_champion`, `aov_planar_gate`; event `aov_magic.11` (champion vanishes, hidden, champion scope); men-at-arms `aov_conjured_beasts`; template `aov_bound_champion_template`.

- [ ] **Step 1: Write failing tests**, class `ConjurationTests`:
  - data keys `summon_familiars, summon_beasts, bound_champion, summon_elementals, aid_construction, planar_gate`; `aid_construction` name `Unseen Servants`, `build_speed = -0.4`, `build_gold_cost = -0.25`; `summon_familiars` `intrigue = 3`, `learning = 3`; `summon_beasts`, `summon_elementals`, `planar_gate` are `war`, `scales_duration=True`.
  - `aov_summon_beasts` calls the helper with `TYPE = aov_conjured_beasts STACKS = 2`; `aov_summon_elementals` with `STACKS = 6`; each has the fizzle branch.
  - `aov_planar_gate` picks `aov_host_angels`/`aov_host_eldritch`/`aov_host_devils` by `var:aov_adv_host`, else `aov_conjured_elementals`, `STACKS = 10`, and holds a `random = { chance = aov_planar_gate_demon_chance` that fires `aov_magic.20`; tuning has `aov_planar_gate_demon_chance = 10`.
  - `aov_conjured_beasts` has `can_recruit = { always = no }` and is a light cavalry type.
  - `test_champion_vanishes_on_their_own`: `aov_bound_champion` contains `create_character`, `template = aov_bound_champion_template`, `add_courtier`, `set_knight_status`, and a `trigger_event = { id = aov_magic.11` inside the champion's scope; `aov_magic.11` contains `death = { death_reason = death_vanished }`. The template has `prowess = { 23 27 }`.
  - `test_extraplanar_contact_event` stays (the event is kept); no data key `extraplanar_contact`, `summon_animals` or `conjure_supplies`.
- [ ] **Step 2: Run** `test_spell_schools.py`. Expected: FAIL.
- [ ] **Step 3: Implement** per spec Conjuration table. The champion's duration is the caster's `aov_spell_bound_champion_years`: save it with `save_scope_value_as` before entering the champion's scope. Give the champion a combat lifestyle trait that exists in vanilla (check `blademaster_*`), the caster's culture and faith, and a `aov_bound_outsider` character flag. `aov_conjured_beasts`: copy `aov_conjured_elementals`' shape with light cavalry stats and its icon.
- [ ] **Step 4: Regenerate and run** the build, `test_spell_schools.py`, `test_build_spells.py`, `test_magic_system.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(magic): Conjuration summons armies and a bound champion`.

### Task 4: Divination

**Files:** data block, `aov_magic_effects.txt` (`aov_scry_reveal`, new `aov_detect_plots`, `aov_augury`, delete `aov_deposit_divination`), `aov_magic_events.txt` (`aov_magic.45`), loc, `tools/data/advancements.py`, `tools/tests/test_advancements.py`, rerun `python -I tools/build_advancements.py`.

**Interfaces:**
- Consumes: `aov_adv_orb_spell_years_mult`, `aov_adv_orb_of_omniscience_level`.
- Produces: `aov_detect_plots`, `aov_augury` (fires `aov_magic.45`).

- [ ] **Step 1: Write failing tests**, class `DivinationTests`, and edit `test_advancements.py`:
  - data keys `guidance, detect_plots, eye_for_talent, scry, augury, foresight`; `guidance` `learning = 4`, `monthly_lifestyle_xp_gain_mult = 0.15`; `foresight` `advantage = 12`, `enemy_scheme_secrecy_add = -50`, `owned_hostile_scheme_success_chance_add = 10`; `augury` has the old Manipulated Fortune modifier lines and `years_mult = "aov_adv_orb_spell_years_mult"`.
  - `aov_detect_plots` uses `every_targeting_scheme`, `expose_scheme` and `expose_scheme_agent`.
  - `aov_scry_reveal` contains `every_secret` and `reveal_to = root`, and under `aov_adv_orb_of_omniscience_level >= 2` an `every_known_secret` (verify the iterator name in vanilla) that also reveals.
  - `aov_magic.45` has four `triggered_desc` blocks keyed on `scope:aov_augury_claimant`, `scope:aov_augury_faction`, `scope:aov_augury_dying`, `scope:aov_augury_plotter`.
  - `test_advancements.py::test_foresight_and_fortune_last_longer` checks `foresight` and `augury`; the Orb level 2 and 3 descs in `advancements.py` read as in the spec.
- [ ] **Step 2: Run** `test_spell_schools.py` and `test_advancements.py`. Expected: FAIL.
- [ ] **Step 3: Implement.** Augury saves at most one character per threat: a holder of a claim on one of the caster's held titles whose `max_military_strength` exceeds the caster's; the leader of the faction targeting the caster with the highest discontent; a close family member in poor health; the owner of a hostile scheme targeting the caster. Detect Plots exposes only hostile schemes.
- [ ] **Step 4: Regenerate** spells and advancements; **run** `test_spell_schools.py`, `test_build_spells.py`, `test_advancements.py`, `test_build_advancements.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(magic): Divination reveals plots, secrets and the coming years`.

### Task 5: Enchantment

**Files:** data block, create `common/character_interactions/aov_magic_interactions.txt`, `zz_aov_spell_overrides.txt`, `aov_magic_effects.txt`, `aov_magic_modifiers.txt`, loc, `test_spell_schools.py`, `test_magic_system.py` (`SpellOverrideTests`).

**Interfaces:**
- Consumes: Task 1's hostile roll (Thoughtweave and Dominate are `hostile=True`, `interaction="aov_thoughtweave_interaction"` / `"aov_dominate_interaction"`), `aov_spell_target_allowed`.
- Produces: interactions `aov_thoughtweave_interaction`, `aov_dominate_interaction`; effects `aov_thoughtweave_apply`, `aov_dominate_apply`, `aov_enchant_trinket`; triggers `aov_dominate_surrender_possible`.

- [ ] **Step 1: Write failing tests**, class `EnchantmentTests`, and rewrite `SpellOverrideTests` the way `EnhanceAbilityRemovedTests` works:
  - data keys `enchanting_envoy, heartstring, enchant_trinket, thoughtweave, enchanting_embassy, dominate_to_surrender`; `dominate_to_surrender` name `Dominate`; `enchanting_envoy` `diplomacy = 4`, `general_opinion = 5`; `enchanting_embassy` `vassal_opinion = 25`, `general_opinion = 10`; Heartstring's effect has `years = 3` and opinion modifier `aov_charmed_opinion` is +50.
  - `test_enchantment_interactions_respect_forbiddance`: both interactions contain `scope:recipient = { aov_spell_target_allowed = yes }`, `scope:actor = { aov_spell_<k>_castable = yes }` and `scope:actor = { aov_spell_<k>_cast = yes }`.
  - Thoughtweave has `populate_recipient_list` (courtiers of actor and recipient), four `send_option` flags (`aov_tw_friend`, `aov_tw_lover`, `aov_tw_rival`, `aov_tw_hook`), and lover/rival require `exists = scope:secondary_recipient`; `aov_thoughtweave_apply` uses `set_relation_friend`, `set_relation_lover`, `set_relation_rival`, `add_hook`.
  - Dominate has send options `aov_dom_hook`, `aov_dom_surrender` (shown only when `aov_dominate_surrender_possible = yes`), `aov_dom_free` (needs a secondary recipient from `scope:recipient`'s prisoners); `aov_dominate_apply` uses `add_hook`, `end_war`, `release_from_prison`.
  - `test_dominate_surrender_target_trigger`: `aov_dominate_surrender_possible` requires a war where actor and recipient are the primary attacker and defender.
  - Overrides: `start_compel_interaction` and `start_dominate_interaction` are stubs with `is_shown = { always = no }` and no `start_scheme`; base-mod scan finds no other way into `anb_compel_spell` or `anb_dominate_spell` (copy `test_base_mod_has_no_other_way_in`, parameterised).
  - `aov_enchant_trinket` contains `create_artifact` with a trinket type and one of six modifiers `aov_spell_trinket_<diplomacy|martial|stewardship|intrigue|learning|prowess>`.
- [ ] **Step 2: Run** `test_spell_schools.py`, `test_magic_system.py`. Expected: FAIL.
- [ ] **Step 3: Implement.** Use vanilla `00_education_interactions.txt` (the guardian interaction) as the pattern for an optional `secondary_recipient` and `00_alliance.txt` for `send_option`. Both interactions copy the generated hostile `ai_targets`, `ai_frequency` and `ai_will_do` block (Task 1); the AI always picks the hook option (`send_options_exclusive = yes`, hook as the default). Hook types: the ones Anbennar's `anb_compel_spell` (weak) and `anb_dominate_spell` (strong) schemes grant. Relation reasons: new loc keys `aov_thoughtweave_reason`. Enchant Trinket mirrors the trinket branch of the Enchanted Artifact level 1 effect in `aov_advancement_level_effects.txt`, with low durability so it decays in about ten years. Delete the Compel/Dominate copy note at the file top.
- [ ] **Step 4: Regenerate and run** `test_spell_schools.py`, `test_build_spells.py` (update `test_existing_anbennar_spells` and `test_types`), `test_magic_system.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(magic): Enchantment: forced relations, domination, enchanted trinkets`.

### Task 6: Evocation

**Files:** data block, `aov_magic_effects.txt`, `aov_magic_modifiers.txt`, `aov_magic_triggers.txt`, `aov_spell_tuning.txt`, loc, `test_spell_schools.py`, `test_build_spells.py`.

**Interfaces:**
- Produces: triggers `aov_spell_target_war_foe` (recipient at war with actor, or a knight or army commander of a ruler at war with the actor), `aov_spell_target_war_capital` (at war with actor and has a capital province); effects `aov_fireball`, `aov_earthquake`, `aov_meteor_swarm`; curse `aov_spell_winters_grip_target`; county modifiers `aov_earthquake_damage`, `aov_meteor_scorched`.

- [ ] **Step 1: Write failing tests**, class `EvocationTests`:
  - data keys `fireball, shock_and_awe, flaming_munitions, winters_grip, earthquake, meteor_swarm`; `fireball`, `winters_grip`, `earthquake` targeted and hostile; `meteor_swarm` level 3 slot 6 `war`; `shock_and_awe` name `Thunderclap`, `advantage = 6`, `maa_damage_mult = 0.1`; `flaming_munitions` `siege_phase_time = -0.4`.
  - `test_evocation_target_trigger`: Fireball uses `aov_spell_target_war_foe`; Winter's Grip and Earthquake use `aov_spell_target_war_capital`.
  - `aov_fireball` wounds (vanilla `increase_wounds_effect`) and wounds again inside `random = { chance = aov_fireball_severe_chance` (tuning 20).
  - `aov_spell_winters_grip_target` has `movement_speed = -0.4`, `maa_damage_mult = -0.15`, `supply_limit_mult = -0.2`; `winters_grip` has `curse = "aov_spell_winters_grip_target"`.
  - `aov_earthquake`: `change_development_level = -2`, `change_county_control = -40`, `add_county_modifier = { modifier = aov_earthquake_damage years = 3 }`, a `random` with `aov_earthquake_extra_chance` (tuning 25) and another `change_development_level = -1`; `aov_earthquake_damage` has `fort_level = -1`, `garrison_size = -0.5`.
  - `aov_meteor_swarm` finds the other primary participant of a war of the caster (`is_attacker`), uses `ordered_held_county` with `order_by = development_level` and `max = 3`, and applies `change_development_level = -1`, `change_county_control = -30`, `aov_meteor_scorched` for 5 years; the spell's modifier has `maa_damage_mult = 0.3`, `advantage = 10`, `health = -0.5`.
  - `tearfall` and `elemental_fury` are gone.
- [ ] **Step 2: Run** `test_spell_schools.py`. Expected: FAIL.
- [ ] **Step 3: Implement** per spec Evocation table. `aov_meteor_scorched`: −50% levies and −50% tax (county modifier keys checked in vanilla).
- [ ] **Step 4: Regenerate and run** `test_spell_schools.py`, `test_build_spells.py` (asserts that used `meteor_swarm` at level 2 or `elemental_fury` move to current keys). Expected: PASS.
- [ ] **Step 5: Commit** `feat(magic): Evocation: fireball, frost, earthquake, meteors`.

### Task 7: Illusion

**Files:** data block, `aov_magic_effects.txt` (new `aov_phantasmal_rumour`, `aov_implant_scandal`, `aov_grand_deception`; delete `aov_assimilation_program`), `aov_magic_modifiers.txt`, `aov_magic_triggers.txt`, loc, tests.

**Interfaces:**
- Produces: trigger `aov_spell_target_has_county` (recipient holds a county); curse `aov_spell_phantasmal_rumour_target`.

- [ ] **Step 1: Write failing tests**, class `IllusionTests`:
  - data keys `invisibility, fear_and_loathing, phantasmal_rumour, shadows_in_the_night, implant_scandal, grand_deception`; `invisibility` `intrigue = 4`, `owned_scheme_secrecy_add = 25`; `fear_and_loathing` `dread_baseline_add = 40`; `shadows_in_the_night` `= 25` and `= 40`; the three new ones hostile.
  - `aov_phantasmal_rumour`: `add_prestige = -150` on the recipient and `aov_spell_phantasmal_rumour_target` for 3 years (`vassal_opinion = -20`); the spell's `curse` is that modifier.
  - `aov_implant_scandal`: `add_secret` among `secret_deviant`, `secret_witch`, `secret_non_believer`, each guarded by that secret's validity (vanilla `_is_valid_trigger`) and `NOT = { any_secret = { secret_type = <it> } }`, then `reveal_to = root`.
  - `test_illusion_target_trigger`: Grand Deception uses `aov_spell_target_has_county`; `aov_grand_deception` prefers a county with `any_neighboring_county` held within the caster's realm, else `capital_county`, then `add_pressed_claim`.
  - `bread_and_circuses`, `assimilation_program`, `lead_the_crowds` gone; `aov_assimilation_program` deleted.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** per spec Illusion table.
- [ ] **Step 4: Regenerate and run** `test_spell_schools.py`, `test_build_spells.py` (replace `lead_the_crowds` in `test_land_spells_need_land` with a current land spell). Expected: PASS.
- [ ] **Step 5: Commit** `feat(magic): Illusion: rumours, scandals and forged claims`.

### Task 8: Necromancy

**Files:** data block, `aov_magic_effects.txt` (new `aov_contagion`, `aov_plague_cloud`, `aov_raise_dead`, `aov_finger_of_death`; delete `aov_speak_with_dead`), `aov_magic_modifiers.txt`, `aov_magic_triggers.txt`, `aov_spell_tuning.txt`, loc, tests.

**Interfaces:**
- Consumes: Task 1 army helper; `aov_lich_skeletons`, `aov_lich_skeleton_archers`; `contract_disease_effect = { DISEASE TREATMENT_EVENT }` and `can_contract_disease_trigger` (vanilla).
- Produces: trigger `aov_spell_target_has_capital`; curses `aov_spell_ray_of_sickness_victim`, `aov_spell_steal_vitality_victim` (kept key).

- [ ] **Step 1: Write failing tests**, class `NecromancyTests`:
  - data keys `ray_of_sickness, contagion, steal_vitality, plague_cloud, raise_dead, finger_of_death`; all targeted ones hostile; `steal_vitality` name `Life Drain`, modifier `health = 2`; victim modifier `health = -2`; `ray_of_sickness` curse `health = -1`; `ray_of_sickness` and `steal_vitality` set `curse` to their victim modifiers.
  - `aov_contagion`: `contract_disease_effect` for `consumption`, `typhus`, `smallpox` under `can_contract_disease_trigger`, falling back to `add_trait = ill`.
  - `test_plague_cloud_target_trigger` uses `aov_spell_target_has_capital`. `aov_plague_cloud`: `create_epidemic_outbreak` inside `capital_province`, types `smallpox, bubonic_plague, typhus, consumption, measles, dysentery`, intensity `random_list` with `aov_plague_cloud_major_chance` (tuning 20) for `major` and the rest `minor`, and no `apocalyptic`.
  - `aov_raise_dead`: two helper calls `TYPE = aov_lich_skeletons` and `TYPE = aov_lich_skeleton_archers`, stacks 2 and 1, doubled (4 and 2) under `has_trait = lich`; fizzle branch.
  - `aov_finger_of_death`: `random_list` weights `aov_finger_death_chance` (15), `aov_finger_injury_chance` (45), `aov_finger_disease_chance` (40); `death = { death_reason = death_mysterious }`; injury picks a maiming trait the target lacks or wounds twice; disease uses `contract_disease_effect`; `add_dread = 20` outside the list.
  - `false_life`, `speak_with_dead`, `remove_pain`, `chronophage` gone; `aov_speak_with_dead` deleted. Every necromancy cast still rolls dark magic.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** per spec Necromancy table. Spec "3 stacks, a Lich 6" = 2 skeleton + 1 archer stacks, doubled for a Lich.
- [ ] **Step 4: Regenerate and run** `test_spell_schools.py`, `test_build_spells.py` (`test_necromancy_rolls_dark_magic` uses `ray_of_sickness_cast` instead of `false_life`). Expected: PASS.
- [ ] **Step 5: Commit** `feat(magic): Necromancy: plague, raised dead and Finger of Death`.

### Task 9: Transmutation

**Files:** data block, `aov_magic_effects.txt` (new `aov_perfect_form`; delete `aov_transmute_to_gold`), `aov_magic_events.txt` (`aov_magic.40` Enhance Ability, `.41` Living Steel, `.42` Shapechange), `aov_magic_modifiers.txt`, `aov_magic_triggers.txt` (`aov_perfect_form_possible`), `common/on_action/aov_magic_on_actions.txt` (drop the Rite of Conception birth hook), loc, tests.

**Interfaces:**
- Consumes: `requires`/`requires_text` (Task 1).
- Produces: modifiers `aov_spell_enhance_<skill>` (5), `aov_spell_living_steel_<heavy_infantry|skirmishers|pikemen|archers|light_cavalry|heavy_cavalry>` (6), `aov_spell_shape_<bear|wolf|hawk>` (3); `aov_perfect_form`, `aov_perfect_form_possible`.

- [ ] **Step 1: Write failing tests**, class `TransmutationTests`; remove `test_rite_of_conception_on_birth` from `test_magic_system.py`:
  - data keys `enhance_ability, longstrider, mass_enlarge, living_steel, shapechange, perfect_form`; `longstrider` level 1 slot 2, `movement_speed = 0.3`, `character_travel_speed_mult = 0.4`; `mass_enlarge` `0.2` and `0.2`; `enhance_ability`, `living_steel`, `shapechange` effects `trigger_event = aov_magic.40/.41/.42` with `scales_duration=True`; `living_steel` is `war`.
  - Each choice event has one option per modifier, each with `ai_chance`, and applies `years = aov_spell_<k>_years`; every option of `.42` also has `dread` +20 in its modifier; living steel modifiers carry `<type>_damage_mult = 0.3` and `<type>_toughness_mult = 0.3`.
  - `test_perfect_form_pool_guards`: for each of beauty/intellect/physique, the gain branches are `trigger`-limited so that none → good_1, good_1 → good_2, good_2 → good_3, never while `<group>_bad_1/2/3` is held, never at good_3; `fecund` only when lacking; one removal branch per defect in the spec's list, each limited by `has_trait`; `albino` and `magical_affinity` absent; `aov_perfect_form_possible` is the OR of all branch triggers; `perfect_form` has `requires = "aov_perfect_form_possible"`; the effect adds `add_stress = 50` and a `random` with `aov_perfect_form_health_risk` (tuning 10).
  - `plant_growth`, `transmute_to_gold`, `reshape_terrain`, `rite_of_conception` gone; `aov_magic_on_birth` and its `on_birth_child` hook gone.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** per spec Transmutation table. Perfect Form: a `random_list` of equal weights, one entry per branch with its `trigger`; an upgrade removes the old tier before adding the new one.
- [ ] **Step 4: Regenerate and run** `test_spell_schools.py`, `test_build_spells.py` (`test_land_spells_need_land` loses `plant_growth`; the one-off check uses a current one-off spell), `test_magic_system.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(magic): Transmutation changes the caster and their army`.

### Task 10: Docs and validation

**Files:** `docs/systems/magic.md`, `CLAUDE.md` (Systems row, if wording changes), `docs/systems/validation-baseline.md` only if a report is accepted.

- [ ] **Step 1: Update `docs/systems/magic.md`**: the System bullet's spell summary (themes, hostile roll, Field of Forbiddance immunity, Summon Elementals now one of four spawned-army spells via `aov_spawn_spell_army`, Compel and Dominate hidden, the removed spells), and point at the new spec.
- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests`. Expected: OK (freshness tests included).
- [ ] **Step 3: Run** `python -I tools/validate.py`. Expected: no new reports for files touched by this plan; fix any that appear.
- [ ] **Step 4: Grep** the repo for every removed key (spec list) outside `docs/superpowers/` and `.claude/worktrees/`. Expected: no hits.
- [ ] **Step 5: Commit** `docs(magic): spell revision`.
- [ ] **Step 6: Report** the in-game checks from the spec's Testing section as not yet done.
