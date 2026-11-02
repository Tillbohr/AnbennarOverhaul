# Artificery rework: design

Date: 2026-11-01. Status: roster and the hybrid model approved in chat; awaiting written-spec review.
Revises the 60 inventions of `docs/superpowers/specs/2026-10-08-artificery-inventions-design.md`. Research, the
three factions, influence, the research popup, the Inventions tab layout, dormancy and inheritance are unchanged
except where this spec says so.

## Goal

1. **Fit the period.** Anbennar CK3 runs 1022–1453 AA; EU4 Anbennar starts in 1444. Most current inventions are
   EU4's later tech (rifles, rail, radio, tanks, airships, submarines, cameras, exosuits). Gnomes should be a century
   or two ahead of Cannor, not four: clockwork, alchemy, damestear powder, golems, lenses, printing, bombards, and
   tethered balloons late in the game.
2. **Make inventions the main driver of gnomish military and economic progress:** stronger effects, permanent
   unlocks (buildings and men-at-arms), and a tier ladder that needs research, not only the culture era.

## Decisions taken

| Question | Decision |
|---|---|
| Model | **Hybrid** (user's choice): a discovered invention's building or men-at-arms unlock is permanent; its modifier still needs a slot |
| Slots | 4 / 5 / 6 (Early / High / Late Medieval), up from 3 / 4 / 5; one-year cooldown unchanged |
| Tier gate | Tier II: High Medieval era **and** 6 Tier I inventions discovered. Tier III: Late Medieval **and** 6 Tier II discovered. Faith- and gnome-locked inventions count. The 6 is a hand-written script value |
| Roster | 48 inventions (13 Economic, 19 Military, 16 Society; 8 faith-locked, 2 gnome-only), listed below |
| Keys | An invention that keeps its name, or a near version of it (Lullaby Cannon → Lullaby Horns), keeps its key. Replacements get new keys. Removed keys leave dead variables in old saves; a new campaign is advised |
| "Artificers" in effects | All `gunpowder` regiments: `artificer_handgunners`, and `armored_artificers` once re-enabled (it becomes `gunpowder`, below). Keys `gunpowder_damage_mult` / `gunpowder_toughness_mult` |
| Removed men-at-arms | `aov_prototype_tanks`, `aov_damestear_megacannon` (deleted with their loc) |
| Gnomish innovation penalty | Not done (not proposed) |
| Icons | No new art. Each new invention reuses a committed `Artf_*.dds` of its category and tier; new buildings use vanilla building icons |

## Roster

Effects are the exact modifier lines (all keys checked against vanilla 1.19 usage). **Unlock** is permanent once
discovered (see Hybrid unlocks). Status: *kept* (same key and name), *renamed* (same key), *moved* (category or
tier change, same key), *new* (new key).

### Economic (13)

| T | Key | Name | Status | Modifier | Unlock |
|---|---|---|---|---|---|
| I | `clockwork_waterwheels` | Clockwork Waterwheels | new | `domain_tax_mult = 0.10` | building `aov_clockwork_mill_01` |
| I | `growth_beans` | Growth Beans | moved II→I | `development_growth_factor = 0.25` `supply_limit_mult = 0.15` | |
| I | `self_cleaning_parchment` | Self Cleaning Parchment | kept | `monthly_county_control_growth_add = 0.5` `stewardship = 1` | |
| I | `box_of_holding` | Box of Holding | moved Military→Economic | `monthly_income_mult = 0.10` `supply_duration = 0.5` | |
| I | `clockwork_abacus` | Clockwork Abacus | new | `stewardship = 2` `vassal_tax_mult = 0.10` | |
| II | `arithmatons` | Arithmatons | moved Society→Economic | `domain_tax_mult = 0.20` `vassal_tax_mult = 0.15` | |
| II | `alchemical_distilleries` | Alchemical Distilleries | new | `monthly_income_mult = 0.10` | building `aov_alchemical_distillery_01` |
| II | `subterrenes` | Clockwork Excavators | renamed | `build_gold_cost = -0.25` `build_speed = -0.25` | |
| II | `damestear_lamps` | Damestear Lamps | new | `development_growth_factor = 0.25` `character_capital_county_monthly_development_growth_add = 0.3` | |
| III | `damestear_foundries` | Damestear Foundries | new | `monthly_income_mult = 0.15` | building `aov_damestear_foundry_01` |
| III | `automaton_labourers` | Automaton Labourers *(gnome)* | new | `domain_limit = 1` `holding_build_gold_cost = -0.30` `development_growth_factor = 0.25` | |
| III | `pathway_transmutation` | Transmutation Crucibles | renamed | `monthly_income_mult = 0.25` | |
| III | `pneumatic_post` | Pneumatic Post | new | `monthly_county_control_growth_add = 0.5` `character_travel_speed_mult = 0.20` | |

### Military (19)

| T | Key | Name | Status | Modifier | Unlock |
|---|---|---|---|---|---|
| I | `damestear_powder` | Damestear Powder | new | `gunpowder_damage_mult = 0.25` | |
| I | `brass_cuirasses` | Brass Cuirasses | new | `gunpowder_toughness_mult = 0.25` | |
| I | `clockwork_repeaters` | Clockwork Repeaters | new | `archers_damage_mult = 0.10` | MaA `aov_clockwork_repeaters` |
| I | `clockwork_ballistae` | Clockwork Ballistae | new | `siege_phase_time = -0.20` `archers_damage_mult = 0.15` | |
| I | `ancestral_golems` | Ancestral Guardian Golems *(ancestor worship)* | kept | `fort_level = 2` `defender_holding_advantage = 6` | |
| I | `sunbeam_armaments` | Sunblessed Armaments *(Bulwari sun cults)* | kept | `siege_phase_time = -0.30` | |
| II | `war_golems` | War Golems | kept | `heavy_infantry_damage_mult = 0.10` | MaA `aov_war_golems` |
| II | `gnomish_bombards` | Gnomish Bombards | new | `siege_phase_time = -0.10` | MaA `aov_gnomish_bombards` |
| II | `brass_prosthesis` | Brass Prosthesis | moved Economic→Military | `levy_reinforcement_rate = 0.40` `gunpowder_toughness_mult = 0.10` | |
| II | `vorpal_bullets` | Vorpal Bullets | moved I→II | `maa_damage_mult = 0.10` `gunpowder_damage_mult = 0.15` | |
| II | `chi_cultivation` | Chi Extraction Charms *(Devouring Path)* | moved Economic→Military | `gunpowder_damage_mult = 0.30` | |
| II | `avatar_supersoldier_serum` | Avatar's Draught *(Cannorian pantheon)* | renamed | `knight_effectiveness_mult = 0.25` `gunpowder_toughness_mult = 0.15` | |
| II | `lullaby_cannon` | Lullaby Horns *(Skaldhyrric)* | renamed | `advantage = 5` | |
| III | `wandlocks` | Wandlocks | moved II→III | `gunpowder_damage_mult = 0.30` `gunpowder_toughness_mult = 0.15` | |
| III | `clockwork_plate_harness` | Clockwork Plate Harness | new | `gunpowder_toughness_mult = 0.10` | MaA `armored_artificers` |
| III | `observation_balloons` | Observation Balloons | new | `advantage = 6` | |
| III | `black_damestear_bullets` | Black Damestear Shot | renamed | `maa_damage_mult = 0.15` `maa_toughness_mult = 0.15` | |
| III | `damestear_mortars` | Damestear Mortars | new | `siege_phase_time = -0.30` `siege_weapon_max_size_add = 1` | |
| III | `demonflame_flamethrowers` | Demonflame Siphons *(Xhazobkult)* | renamed | `gunpowder_damage_mult = 0.35` `dread_decay_mult = -0.25` | |

### Society (16)

| T | Key | Name | Status | Modifier |
|---|---|---|---|---|
| I | `sending_stones` | Sending Stones | kept | `diplomacy = 2` `councillor_opinion = 15` |
| I | `mystic_ciphers` | Mystic Ciphers | kept | `enemy_hostile_scheme_success_chance_add = -20` `owned_hostile_scheme_success_chance_add = 10` |
| I | `spell_in_a_box` | Spell-In-A-Box | moved Economic→Society | `monthly_prestige_gain_mult = 0.20` |
| I | `centipedal_chests` | Centipedal Chests | kept | `character_travel_speed_mult = 0.30` `travel_danger = -10` |
| I | `conversation_calibrator` | Conversation Calibrator *(gnome)* | kept | `different_culture_opinion = 15` `general_opinion = 5` |
| I | `fey_spray` | Fey Spray *(fey)* | kept | `county_opinion_add = 10` |
| II | `printing_press` | Gnomish Printing Press | new | `monthly_lifestyle_xp_gain_mult = 0.25` `learning = 1` |
| II | `clockwork_orrery` | Clockwork Orrery | new | `learning = 2` `cultural_head_fascination_mult = 0.25` |
| II | `remedial_tinctures` | Remedial Tinctures | kept | `health = 0.5` `hard_casualty_modifier = -0.20` |
| II | `living_mirrors` | Living Mirrors | moved I→II | `county_opinion_add = 10` `different_culture_opinion = 15` |
| II | `mirage_detector_3000` | Miracle Detector 3000 | kept | `monthly_piety_gain_mult = 0.20` `faith_conversion_piety_cost_mult = -0.25` |
| II | `game_of_khet` | Game of the Khet *(Khetism)* | kept | `vassal_opinion = 10` `county_opinion_add = 10` |
| III | `clerk_automatons` | Clerk-Automatons | new | `domain_limit = 1` `vassal_limit = 20` |
| III | `gnomish_spectacles` | Gnomish Spectacles | new | `diplomacy = 1` `martial = 1` `stewardship = 1` `intrigue = 1` `learning = 1` `prowess = 1` |
| III | `clockwork_heralds` | Clockwork Heralds | new | `monthly_county_control_growth_add = 0.5` `county_opinion_add = 10` |
| III | `universal_grammarye` | Universal Grammarye | new | `different_culture_opinion = 25` `diplomacy = 2` (`cultural_acceptance_gain_mult` is a culture modifier, not allowed on a character) |

Faith triggers are the existing allow-listed ones; `gnome_only` is unchanged in meaning.

### Removed (33 keys; 27 kept, 21 new)

`arcane_battery_capital_complex`, `automated_translator`, `market_mender`, `plane_of_water_teleporter`,
`gene_food_cultivation`, `vendorless_stall`, `elemental_locomotives`, `prefabricated_city_constructors`,
`t_wave_transceivers`, `artificer_exo_arms`, `commercial_sky_galleons`, `magic_missile_deployer`, `portable_turrets`,
`sparkdrive_rifles`, `arcane_blaster`, `balloonboost_packs`, `coddorran_powered_exosuit`, `gu_boats`,
`prototype_tanks`, `artillery_autoloader`, `bioartificed_ascension`, `damestear_reactor_megacannon`,
`military_sky_galleons`, `naval_mageshields`, `personal_mageshields`, `apparitional_communicator`, `viewcatcher`,
`empire_engine`, `think_thought_transmitters`, `bureaucratizer`, `crierless_crier_device`, `negotiation_nexus`,
`runethought_network`.

### Descriptions

Each new or renamed invention gets a one- or two-sentence description in the existing voice, in period: no
engines, rails, radio or flight beyond tethered balloons. Kept and moved inventions keep their text.

## Hybrid unlocks

A new generated trigger per invention, character scope:

```
aov_invention_<key>_unlock_ready = {
	aov_invention_<key>_discovered = yes
	aov_invention_<key>_visible = yes
	NOT = { has_variable = aov_artificery_dormant }
}
```

Discovery is inherited (union of predecessor's discoveries, already in `aov_inventions_inherit`), so unlocks pass to
the heir. Dormancy (no academy, not a gnome, culture lost the tradition) switches unlocks off until it ends, as it
already does for modifiers.

### Men-at-arms

| MaA | Unlocked by | Type | Stats |
|---|---|---|---|
| `aov_clockwork_repeaters` (new) | Clockwork Repeaters | `archers` | vanilla `crossbowmen` (42/18) +30 %: damage 55, toughness 23; same counters and terrain, stack 100 |
| `aov_war_golems` (kept) | War Golems | `heavy_infantry` | vanilla `armored_footmen` (32/22) +40 % (was +25 %): damage 45, toughness 31 |
| `aov_gnomish_bombards` (new) | Gnomish Bombards | `siege_weapon` | vanilla `bombard` (tier 4, siege value 0.6, toughness 12): siege value 0.75; stack 10 |
| `armored_artificers` (Anbennar's, re-enabled) | Clockwork Plate Harness | `gunpowder` (was `heavy_infantry`) | damage 45, toughness 30, stack 75; Anbennar's culture-era upgrades keep applying |

`can_recruit` is `aov_invention_<key>_unlock_ready = yes` (each MaA also keeps `has_enabled_artificer_academy_trigger`
for parity with `artificer_handgunners`). `armored_artificers` stays a single-object override in
`zz_aov_gnome_maa_overrides.txt`; `artificers` stays disabled. The flavor loc says "Recruitable once
[invention] is discovered"; Anbennar's own `armored_artificers_flavor` is replaced from
`localization/english/replace/`.

### Buildings

Three regular buildings in `common/buildings/aov_invention_buildings.txt` (hand-written), each a single level,
in castles and cities. They take a normal building slot.

| Building | Unlocked by | Cost | Time | County modifier |
|---|---|---|---|---|
| `aov_clockwork_mill_01` | Clockwork Waterwheels | 150 gold | standard | `tax_mult = 0.15` `development_growth_factor = 0.10` |
| `aov_alchemical_distillery_01` | Alchemical Distilleries | 250 gold | slow | `tax_mult = 0.20` `county_opinion_add = 5` |
| `aov_damestear_foundry_01` | Damestear Foundries | 400 gold | slow | `tax_mult = 0.25` `development_growth_factor = 0.15` `levy_size = 0.15` |

- `can_construct_potential`: `building_requirement_tribal = no`, castle/city, and
  `scope:holder = { aov_invention_<key>_unlock_ready = yes }`.
- `is_enabled`: the same holder check, so a dormant or changed holder's buildings switch off (`show_disabled = yes`).
- Added to `castle_holding` and `city_holding` in `tools/build_holdings_override.py` (as the academy is); rerun it.
- `ai_value` base 20 with `ai_general_building_modifier = yes`. Loc: name, description, effect description in `aov_artificery_l_english.yml`.
- `tax_mult`, `levy_size` and `county_opinion_add` are all `county_modifier` keys in vanilla buildings (checked).
  Icons: `icon_building_watermills.dds`, `icon_building_breweries.dds`, `icon_building_wind_furnaces.dds` (vanilla).

## Tier gate

- Hand-written `aov_invention_tier_gate_count = 6` in `common/script_values/aov_artificery_values.txt`.
- Generated values `aov_inventions_t1_discovered_count`, `aov_inventions_t2_discovered_count` (character scope).
- Generated `aov_invention_<key>_unlocked`: tier I unchanged; tier II adds
  `aov_inventions_t1_discovered_count >= aov_invention_tier_gate_count`; tier III likewise with tier II.
- Loc: `AOV_INV_LOCKED_TIER_2_TT` / `_3_TT` become "requires the High (Late) Medieval era and
  [count] Tier I (II) inventions discovered ([current]/[count])".

## Slots

`aov_invention_slots_max` becomes 4 / 5 / 6. The cooldown machinery (`aov_slot_cd_<n>`, `aov_invention_slots_cooling`,
`aov_artificery_start_slot_cooldown`) gains a sixth slot. The AI activation order is unchanged (highest tier
first; Military at war, Economic at peace).

## Generator changes (`tools/build_inventions.py`)

- Data field `maa` is replaced by `unlock`: `None`, or the key of an unlocked MaA or building. Validation checks it
  against `MAA_UNLOCKS = {aov_clockwork_repeaters, aov_war_golems, aov_gnomish_bombards, armored_artificers}` and
  `BUILDING_UNLOCKS = {aov_clockwork_mill_01, aov_alchemical_distillery_01, aov_damestear_foundry_01}`, and that each
  unlock is used once.
- Emits `_unlock_ready` triggers, the two discovered-count values and the tier-gated `_unlocked` triggers.
- Tooltip: a paragraph for inventions with an unlock, "Unlocks [name] permanently once discovered"
  (`aov_invention_<key>_unlock_tt`, generated loc; MaA via `$<maa>$`, buildings via `$building_<key>$`).
- Section rows stay 5 wide; the largest visible section is 5 boxes plus at most one faith box.

## Files

| File | Change |
|---|---|
| `tools/data/inventions.py` | Roster above |
| `tools/build_inventions.py` | Above; rerun |
| `common/men_at_arms_types/aov_invention_maa_types.txt` | Remove tanks and megacannon; add repeaters and bombards; War Golems stats and trigger |
| `common/men_at_arms_types/zz_aov_gnome_maa_overrides.txt` | `armored_artificers` re-enabled as `gunpowder` |
| `common/buildings/aov_invention_buildings.txt` | New |
| `tools/build_holdings_override.py` + its outputs | Three buildings added; rerun |
| `common/script_values/aov_artificery_values.txt` | Slots 4/5/6, sixth cooldown, tier gate count |
| `common/scripted_effects/aov_artificery_research_effects.txt` | Sixth cooldown slot |
| `localization/english/aov_artificery_l_english.yml` | MaA, buildings, tier-lock text |
| `docs/systems/artificery.md`, `CLAUDE.md` systems row | 48 inventions, hybrid unlocks, buildings, tier gate, slots |
| `tools/tests/test_build_inventions.py`, `test_artificery_research.py` | Roster counts, unlock validation, unlock triggers in MaA/buildings, tier gate, slots |

`docs/research/2026-10-08-eu4-artificer-inventions.md` stays as the record of the EU4 import.

## Testing

- Unit tests (TDD): validation rejects an unknown or duplicate unlock; every unlock-bearing invention emits
  `_unlock_ready`; tier II/III `_unlocked` contain the count check; every MaA and building `can_recruit` /
  `can_construct_potential` uses its invention's `_unlock_ready`; slots value reads 4/5/6; freshness tests pass.
- `python -I tools/validate.py` shows no new reports.
- In game (user): Inventions tab shows 48 boxes in the right tiers; Tier II is locked with the count until 6 Tier I
  are discovered; discovering Clockwork Waterwheels allows building the Clockwork Mill without the invention
  active; Clockwork Plate Harness makes Armored Artificers recruitable; slots read 4 at game start.

## Out of scope

Tying inventions to a specific faction, a gnomish innovation penalty, new art, EU4 imports, and changes to research
cost or time.
