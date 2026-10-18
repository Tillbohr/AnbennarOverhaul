# RiE dwarf buildings, deposits and the Dwarven Expedition (design)

Date: 2026-10-17. Status: design approved, not implemented.

## Goal

Bring Realms in Exile's dwarf economy to Anbennar's dwarves:

1. **Buildings:** every RiE dwarf building line, underground ones in the 9 Anbennar dwarven holds, surface ones in
   dwarf-held castles and cities on mountain, hill or dwarven-surface terrain.
2. **Hold levels:** `dwarven_hold_01..10` keep being raised only by Delve Deeper digs, but take the effects and the
   building prerequisites of RiE's `dwarven_depths_01..10`.
3. **Deposits and mines:** RiE's 15 ore deposits (province modifiers) and their 10-level mines.
4. **Dwarven Expedition:** a new activity with two types, Mining (finds a deposit, like RiE's prospecting) and
   Archaeology (a placeholder the user develops later).

Starting deposits: Rubyhold ruby, Verkal Gulan gold, Anvilwright (the hold of `d_silverforge`) silver.

User choices: all RiE dwarf lines, surface ones included; RiE's 15 ores unchanged; one ore rarity for the whole map;
prospecting in any mountain or dwarven-terrain province of the realm; mines in castles, cities and holds; hold levels
stay dig-based with RiE's stats and prerequisites; buildings imported by a generator, the activity hand-written;
Archaeology only as an option for now; event backgrounds imported from RiE. Only the 9 Anbennar holds use the hold
holding: no province is converted.

Sources (RiE, Workshop 2291024373): `common/buildings/lotr_buildings/lotr_dwarven_buildings.txt`,
`lotr_mines_buildings.txt`, `lotr_dwarven_settlement_holdings.txt` (`dwarven_depths_*`, read for Section 2 only),
`common/holdings/lotr_holdings.txt` and `00_holdings.txt` (holding lists), `common/modifiers/lotr_modifiers/lotr_ore_modifiers.txt`,
`common/activities/activity_types/lotr_mining.txt` (structure reference), `common/event_backgrounds/lotr_event_backgrounds.txt`,
their localization and icons.

## 1. Building import (`tools/build_rie_dwarves.py`)

Data in `tools/data/rie_dwarves.py`. The generator reads RiE at build time and copies building blocks one by one,
rewriting them. Keys keep RiE's names, unprefixed (repo convention): `dwarven_forge_01`, `ruby_mines_01`. RiE's dwarf
and mine files define 344 building keys; none exists in Anbennar or the game today, and the build stops if one ever does.

Outputs:

| File | Content |
|---|---|
| `common/buildings/aov_rie_dwarven_buildings.txt` | every block of `lotr_dwarven_buildings.txt` (underground and surface lines, specializations, bank, king's armory, grand library) |
| `common/buildings/aov_rie_mines.txt` | `<ore>_mines_01..10` for the 15 ores |
| `common/modifiers/aov_rie_ore_modifiers.txt` | the 15 `mining_<ore>_province_modifier` deposits, verbatim |
| `common/scripted_triggers/aov_rie_dwarf_triggers.txt` | the replacement triggers below, the dig prerequisites (Section 2) |
| `common/scripted_effects/aov_rie_deposit_effects.txt` | `aov_expedition_roll_deposit_effect`, `aov_rie_deposit_setup_effect` (Section 3) |
| `localization/english/aov_rie_dwarves_l_english.yml` | RiE's names and descriptions of the copied buildings and modifiers, plus our trigger tooltips |
| icons and pictures | building type icons the blocks name, the activity art (Section 4), at RiE's paths |

Rewrites:

| RiE | Becomes |
|---|---|
| `is_dwarf = yes` | `is_dwarvish_culture = yes` (Anbennar, character scope) |
| `is_orc = yes` and branches that only serve orcs | removed |
| `has_building_or_higher = dwarven_depths_N` | `has_building_or_higher = dwarven_hold_N` |
| `lotr_dwarven_underground_buildings_requirement_terrain` (`terrain = halls`) | `aov_rie_hold_province_trigger` (`has_holding_type = dwarven_hold_holding`) |
| `lotr_dwarven_mountain_buildings_requirement_terrain` | `aov_rie_mountain_terrain_trigger`: `mountains`, `desert_mountains`, `dwarven_hold`, `dwarven_hold_surface`, `cavern`, `dwarven_road` |
| `lotr_dwarven_hill_buildings_requirement_terrain` | `aov_rie_hill_terrain_trigger`: the mountain list plus `hills` |
| `lotr_dwarven_is_surface_dwarf` | `aov_rie_surface_dwarf_trigger`: dwarven holder and the holding is not `dwarven_hold_holding` (Anbennar has no surface-dweller tradition) |
| `lotr_dwarven_is_mountain_dwarf`, `lotr_subterranean_buildings` | dwarven holder |
| `province_dynasty_modifier` blocks with `lotr_*_legacy_*` perks | removed |
| modifier blocks gated on `parameter = unlock_full_delving` | ungated: the `parameter` line is removed and `county_culture_modifier` becomes `county_modifier` (RiE gives the parameter to every dwarven heritage; our blocks are already limited to dwarven holders) |
| modifier blocks gated on another `parameter` | kept when the game or Anbennar defines the parameter (`quarries_building_bonuses`, `strength_in_numbers_maa_limit_bonus` today), else removed |
| `elven_settlement_N` alternatives in `can_construct` | removed |

Every removed item is listed in a build note. The build stops on any other identifier Anbennar and the game lack
(scripted trigger, building, modifier, men-at-arms type, cultural parameter), a missing icon, a key collision, or a
picture whose path Anbennar or the game already has with other content.

Holding lists, through `tools/build_holdings_override.py`:

- `dwarven_hold_holding` keeps the castle build list (castle buildings in holds via the castle-level equivalence) and
  gains RiE's `dwarven_holding` list (its mines and dwarven buildings), without the orc and oath buildings and without
  `dwarven_depths_01`. `deep_mine_01`, `runeforge_01` and `hall_of_the_ancestors_01` leave `NEW_HOLDINGS` (Section 2).
- `castle_holding` and `city_holding` gain RiE's castle-list dwarf entries (surface buildings, `dwarven_terrace_farm_01`,
  `dwarven_outpost_01`, `dwarven_mustering_grounds_01`) and the 15 mines. The generator exports these lists; the
  holdings script imports them, so both stay in step.

## 2. Hold levels

`dwarven_hold_01..10` (`tools/build_holds.py`) take their effects from RiE's `dwarven_depths_01..10`, copied with the
Section 1 rewrites: `levy`, `max_garrison`, `garrison_reinforcement_factor`, `province_modifier` (income 0.5 to 3.5,
`fort_level` 2 to 20, defender advantage, stationed men-at-arms damage and toughness, `building_slot_add` 0 to 9,
travel danger) and the formerly delving-gated terrain and county blocks. This replaces the hand-set `LEVELS` and
`_FLAT_TIERS` in `tools/data/holds.py`; `build_holds.py` gets the level effects from `build_rie_dwarves.py`
(`depths_level_effects`). Kept ours: assets (dwarf models), `is_enabled` (dwarven holder, hold not ruined), no
construction (digs only), `next_building`, the castle-level equivalence (hold levels 1/3/5/8 = castle 1-4,
`zz_aov_building_requirement_triggers.txt`).

Prerequisites: each RiE level's `can_construct`, rewritten and without its "previous level" line (a dig to level N
starts from level N-1), becomes `aov_hold_dig_requirements_<N>_trigger` (province scope) in
`aov_rie_dwarf_triggers.txt`. Delve Deeper's picker event `aov_hold_delve.1` shows the option for level N disabled,
with the trigger's tooltip, until the hold has those buildings. Today's RiE requirements:

| Level | Needs |
|---|---|
| 2 | quarry 1 |
| 3 | quarry 2 |
| 4 | quarry 3, any mine 3 |
| 5 | quarry 3, any mine 4 |
| 6 | quarry 3, roads 4, a level-1 specialization, any mine 5 |
| 7 | quarry 4, toolmaker guild 3, any mine 6 |
| 8 | quarry 5, roads 7, a level-2 specialization, any mine 7 |
| 9 | quarry 6, any mine 8 |
| 10 | quarry 8, roads 8, toolmaker guild 6, a level-3 specialization, any mine 9 |

(The generator copies whatever RiE's file says; the table only documents it.) A running dig is not cancelled when a
requirement is lost later. Consequence: a hold needs a deposit (and its mine) to dig past level 3. Rubyhold, Verkal
Gulan and Anvilwright start with one; the other six must find one with a Mining expedition in the hold province.

Dig cost and time stay ours (150 gold x target level; 12 x (8 + 4 x (N - 1)) months); RiE's `cost_gold` is not used.
Holds that start above level 1 keep their start levels whether or not they meet the requirements.

Removed: `deep_mine_01..`, `runeforge_01..`, `hall_of_the_ancestors_01..` (`DWARVEN_BUILDINGS` in `tools/data/holds.py`,
their loc and modifiers); RiE's quarry, forge and vault lines cover them. Unchanged: Khugdihr's ruin, Clear the Ruins,
dig events, the county-view dig bar, the AI's dig reserve.

## 3. Deposits and mines

Deposits are RiE's 15 province modifiers, verbatim: `mining_<ore>_province_modifier`, `monthly_income` +0.1 (iron,
copper, tin, lead) to +0.5 (mithril). They are permanent. A province holds at most one: Mining expeditions need a
location without one (RiE's rule, `aov_rie_has_deposit_trigger` = OR of the 15 modifiers).

Rarity is the same everywhere: `ORE_WEIGHTS` in `tools/data/rie_dwarves.py`, generated into one `random_list` in
`aov_expedition_roll_deposit_effect` (activity location scope; adds the modifier and sets activity variable
`aov_expedition_ore = flag:<ore>`):

| Ores | Weight each | Share of finds |
|---|---|---|
| iron, copper, tin, lead | 40 | 67% together |
| quartz, onyx, peridot, amethyst | 12 | 20% together |
| silver | 8 | 3.4% |
| gold | 6 | 2.5% |
| sapphire, emerald, ruby | 4 | 1.7% each |
| diamond | 3 | 1.3% |
| mithril | 1 | 0.4% |

RiE's mineral regions, legend seeds and perk and legacy multipliers are not copied.

Mines: `<ore>_mines_01..10` as RiE has them (`can_construct_potential` = the matching deposit). Each level needs RiE's
holding level: `building_requirement_castle_city_church = { LEVEL = .. }` in castles and cities, `dwarven_hold_N` in
holds (the elven-settlement alternative is removed). No race requirement, as in RiE: a conqueror can work a deposit;
deposits only appear through dwarven expeditions and the start setup.

Starting deposits: `START_DEPOSITS` in the data (`b_hul_az_amekh`: ruby, Rubyhold; `b_gulandhum`: gold, Verkal Gulan;
`b_anvilwright`: silver, Anvilwright), generated into `aov_rie_deposit_setup_effect`
(`title:<barony>.title_province = { add_province_modifier = mining_<ore>_province_modifier }`), called from the
existing hold game-start on_action. The build stops on an unknown barony or ore. No mines are pre-built.

## 4. The Dwarven Expedition (hand-written)

`common/activities/activity_types/aov_dwarven_expedition.txt`, key `activity_dwarven_expedition`, on RiE's mining
skeleton without its murder, abduction, court-position, crafting and struggle branches.

- **Host:** playable, `highest_held_title_tier > tier_barony`, `is_dwarvish_culture = yes`, available adult. AI: not at
  war, `short_term_gold >=` the cost.
- **Location:** `is_single_location = yes`, `province_filter = domicile_realm`, `ai_province_filter = domicile_domain`;
  valid on `aov_rie_mountain_terrain_trigger` (mountain or dwarven terrain). `can_start` needs one valid province for at
  least one type.
- **Expedition type** (special option category, RiE's prospecting and standard icons):
  - `expedition_mining`: the location has no deposit. Cost x0.5 (RiE's prospecting rate).
  - `expedition_archaeology`: the location is on dwarven terrain (`dwarven_hold`, `dwarven_hold_surface`, `cavern`,
    `dwarven_road`). Placeholder outcome only: prestige and a log entry saying nothing was catalogued yet, through
    `aov_expedition_archaeology_outcome_effect` (the hook the user fills later).
- **Crew** (option category): local miners / skilled delvers / master delvers; RiE's three option costs (0, 10, 35,
  scaled by tier and era); +0 / +10 / +20 success.
- **Cost and cooldown:** `standard_activity_base_cost` scaled by era (RiE's formula); cooldown 4 years.
- **Phase:** one predefined phase. `on_phase_active` (host): `progress_activity_phase_after = { months = 8 }`; every
  player attendee gets `aov_expedition_random_pulse` at months 2, 4 and 6; the host gets `aov_expedition_outcome` at
  month 7.
- **Success chance:** activity variable `aov_expedition_success_chance`, set on start from
  `aov_expedition_success_chance_value`: base 30, + stewardship / 4 (at most 10), + crew, + 10 when the location is a
  hold, at most 90. Pulse events change it by `aov_expedition_success_minor/medium/major` = 3 / 5 / 10 (RiE's values).
- **Guests:** optional (`allow_zero_guest_invites = yes`), RiE's invite rules, `max_guests = 10`; AI guests get no pulse
  events. The activity ends early if the host dies, is imprisoned, becomes incapable or loses the location's realm.
- **Events** (`events/aov_dwarven_expedition_events.txt`, namespace `aov_expedition`): a setting-out event; six pulse
  events (rich vein, cave-in, flooded shaft, old dwarven carvings, a lost miner, a quarrel among the delvers) whose
  options cost gold or risk and move the success chance; outcomes: Mining success (roll against the chance) runs
  `aov_expedition_roll_deposit_effect`, names the ore and gives prestige; Mining failure returns some gold; Archaeology
  runs the placeholder. Values in `common/script_values/aov_expedition_values.txt`.
- **AI:** `ai_check_interval = 60`, `ai_will_do` higher with free gold and a valid location without a deposit; the AI
  picks Mining.
- **Backgrounds** (imported from RiE by the generator, at RiE's paths):
  - `gfx/interface/illustrations/activity_backgrounds/lotr_cave_interior.dds`: RiE's mining background (39 of its 48
    mining events); the activity's location and fallback background and event background `aov_expedition_cave`.
  - `gfx/interface/illustrations/event_scenes/lotr_halls.dds`: event background `aov_expedition_halls`, for events in a
    hold or on `cavern` / `dwarven_road` terrain.
  - `gfx/interface/illustrations/event_scenes/lotr_dwarven_gate.dds`: the travel background when the host sets out
    from dwarf-settled mountains or hills, and event background `aov_expedition_gate` (setting-out event).
  - Definitions in `common/event_backgrounds/aov_dwarven_expedition_backgrounds.txt` with RiE's (vanilla) environments
    and ambiences (`environment_event_alley`, `environment_travel_mountain_settlement`).
- **Other art:** RiE's activity icon and header, phase icon, option-category icons and the two type icons, copied as
  `aov_expedition_*`; map entity `building_special_mines_entity` (the game's). Loc hand-written in
  `localization/english/aov_dwarven_expedition_l_english.yml`.

## Testing

- `tools/tests/test_build_rie_dwarves.py`: each rewrite rule on small RiE-shaped samples; the stop conditions (unknown
  identifier, collision, missing icon); `ORE_WEIGHTS` covers exactly RiE's 15 deposits; `START_DEPOSITS` baronies exist
  in Anbennar's landed titles; `FreshnessTests` fail when the outputs are stale or orphaned.
- `tools/tests` for holds: the level effects come from RiE, the three removed buildings appear nowhere, the dig
  prerequisites exist for levels 2-10.
- `python -I tools/validate.py` clean; new inherited reports (verbatim RiE code) are baselined only after checking.
- **In game:** the expedition shows in the planner for a dwarf ruler; a Mining expedition can end with a deposit and the
  matching mine can be built in a castle, city and hold; Rubyhold, Verkal Gulan and Anvilwright start with ruby, gold
  and silver; Delve Deeper shows the level-N requirements; surface buildings appear in a dwarf-held mountain castle and
  not in a human-held one; the backgrounds load.

## Docs

`CLAUDE.md`: a generated-files row for `build_rie_dwarves.py`, the Dwarven holds Systems entry updated (RiE level
stats, prerequisites, removed buildings), a new Systems entry (RiE dwarf buildings, deposits, Dwarven Expedition), the
command in the task table, and the generator in the update steps (after an Anbennar or RiE update, before
`build_holds.py` and `build_holdings_override.py`).

## Risks to confirm in game

1. RiE's buildings were balanced for RiE; with every line in, holds get much stronger (fort level 20, up to 9 extra
   slots). Tune in data after playing.
2. Some RiE blocks may lean on RiE men-at-arms or modifiers not caught by name; the build's unknown-identifier stop is
   the guard, tiger the second.
3. Activities need the planner's art and loc keys to be complete or the planner shows blanks; check every option and
   phase in game.
4. Removing the three old hold buildings changes existing saves' holds (they lose those buildings).
