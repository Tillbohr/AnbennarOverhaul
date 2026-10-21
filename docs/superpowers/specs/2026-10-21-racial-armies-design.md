# Racial armies — design

Date: 2026-10-21. Status: approved in chat (roster, stats, levy balance, event-driven levy correction), awaiting
written-spec review.
Source: the Gameplay section of `docs/Anbennar-Overhaul-Master-TODO List.md` (levy, MAA and domain limit items for
Humans, Elves, Dwarves, Gnomes, Kobolds). Inspiration: Realms in Exile's elven and dwarven heritages and regiments.

## Goal

Give each race its own army shape while keeping an elven, dwarven, gnomish or kobold realm about as strong as a
human realm with the same counties and tier, at game start and for the rest of the game:

- **Elves**: very few levies, each one elite; full rosters of small, very strong MAA regiments, different for moon,
  sun and wood elves.
- **Dwarves**: fewer, tougher levies; tough 80-man MAA strong in holds and mountains, a shared dwarven set plus one
  signature unit per clan.
- **Gnomes**: fewer, better levies (their strength stays the artificer MAA).
- **Kobolds**: many weak levies.
- **Humans** (and halflings, harpies, gnolls): unchanged.

## Decisions taken

| Question | Decision |
|---|---|
| MAA strength | New and retuned MAA units, no percentage bonuses to MAA stats |
| Unit pricing | Every racial unit costs the same per point of power as the vanilla unit of its role (see *Pricing*) |
| Levy and quality basis | The ruler's culture (heritage `character_modifier`), so count and quality always come from one culture |
| Levy balance | Levy count is a fixed share of a human's for the whole game, levy quality is fixed; total levy power equals a human's |
| Keeping the share fixed | Generated per-holding correction, refreshed on building completion, title change and a yearly backstop |
| Sun elf units | `tradition_sundancer_legions` removed from every culture and hidden; its units belong to all sun elf cultures |
| Dwarven Handgunners | Removed entirely: the unit can no longer be recruited and its tradition is removed from every culture and hidden |
| Unit gating | Culture lineage (the culture or any ancestor), never a tradition another culture could adopt |
| Dwarf signatures | One per clan, from that hold's EU4 Anbennar national ideas |
| Domain limit | Elves −1, dwarves −2, gnomes −1, kobolds and humans unchanged |
| Anbennar's existing elf/dwarf units | Retuned in place (same keys), with real flavor text replacing placeholder jokes |

## Levies and domain limit

### Heritage modifiers

`heritage_elven`, `heritage_dwarven`, `heritage_gnomish` and `heritage_kobold` are overridden in
`common/culture/pillars/zz_aov_racial_heritages.txt`. Anbennar's versions carry only `type`, `is_shown` and
`audio_parameter`; the overrides keep those three unchanged and add a `character_modifier` and a `parameters` flag.

| Heritage | `levy_size` | `levy_attack` / `levy_toughness` | Levy damage/toughness per man | `domain_limit` | Parameter |
|---|---|---|---|---|---|
| Elven | −0.75 | +30 / +30 | 40 / 40 | −1 | `aov_racial_levy_elven` |
| Dwarven | −0.40 | +7 / +7 | 17 / 17 | −2 | `aov_racial_levy_dwarven` |
| Gnomish | −0.50 | +10 / +10 | 20 / 20 | −1 | `aov_racial_levy_gnomish` |
| Kobold | +0.50 | −3 / −3 | 7 / 7 | 0 | `aov_racial_levy_kobold` |

Levy count × levy quality equals a human's (0.25 × 4, 0.6 × 1.7, 0.5 × 2, 1.5 × 0.7), so total levy power is unchanged
and the races differ in how many men they field, not how strong their levies are.

### Why a correction is needed

CK3 adds every `levy_size` modifier into one total. A human holding with +0.6 from buildings has 1.6; an elven
holding with the flat −0.75 would have 0.85, not a quarter of 1.6, so elven levies would grow about twice as fast
as human ones (modelled: elves 0.96 at start, 1.8 mid game, 2.3 late game versus an equal human realm). To keep the
share fixed, each racial holding must receive only its share of every bonus (elves 25%, dwarves 60%, gnomes 50%,
kobolds 150%).

### Per-holding correction

For a holding whose owner has a racial heritage, with S = that holding's summed `levy_size` from the covered
sources:

- correction = −f × S, with f = 0.75 elven, 0.40 dwarven, 0.50 gnomish, −0.50 kobold;
- final levy size = 1 + base + S − f × S = share × (1 + S): elves 0.25 (1 + S), dwarves 0.6 (1 + S), and so on.

The correction can never exceed the bonus it cancels, so a holding never falls below its share and levies never
reach zero. Negative sources (governments, laws) are scaled the same way, so a −0.5 government leaves an elf
holding at 0.25 × 0.5, not at zero.

**Generated files** (`tools/build_racial_levies.py`, data in `tools/data/racial_levies.py`):

- `common/script_values/aov_racial_levy_values.txt`: `aov_holding_levy_size_bonus`, province scope, the sum of
  covered `levy_size` sources for that holding, written as one `if` per source.
- `common/modifiers/aov_racial_levy_modifiers.txt`: tier modifiers `aov_racial_levy_<race>_<n>` (province
  modifiers), one per 0.05 of S, `levy_size = −f × 0.05 × n`, for S from −1.00 to the largest reachable total
  (negative tiers for negative S). Each race gets its own set.
- `common/scripted_effects/aov_racial_levy_effects.txt`: `aov_refresh_holding_levy_correction` (province scope):
  removes the holding's current tier (tracked with a province variable holding the tier index, so only one
  `has_province_modifier` check runs per refresh), then adds the tier for the owner's heritage and rounded S.

**Covered sources** (read from game, Anbennar and overhaul files, later files winning by relative path):

| Source | Block | Condition written into the script value |
|---|---|---|
| Buildings in this province | `province_modifier` | `has_building = X` |
| | `province_culture_modifier` | building + `county.culture = { has_cultural_parameter = P }` |
| | `province_faith_modifier` | building + `county.faith = { has_doctrine_parameter = P }` |
| | `province_terrain_modifier` | building + terrain / `is_coastal` / `is_riverside` / culture parameter as listed |
| Buildings anywhere in the county | `county_modifier`, `county_culture_modifier`, `county_faith_modifier` | `county = { any_county_province = { has_building = X } }` + parameter |
| Duchy capital buildings | `duchy_capital_county_modifier` | the county is its duchy's capital and holds the building |
| Owner's buildings, culture, faith, government | building `character_modifier`; traditions, innovations, pillars (`character_modifier`, `county_modifier`, `province_modifier`); doctrines and tenets; government `character_modifier`; realm laws | `province_owner` has the building / tradition / innovation / doctrine / government / law |

**Not covered** (logged by the generator, listed in the system doc): event and festival modifiers, epidemics,
council and court positions, house aspirations, confederations, subject contracts, domicile buildings. These are
temporary or narrow; they cause short swings, not drift. Development and county control are multipliers, not
`levy_size`, and need no correction.

The generator fails if it meets a `levy_size` in a database it does not classify, so a new source after an update
is caught. `FreshnessTests` fails when the generated files are stale.

**Refresh triggers** (`common/on_action/aov_racial_armies_on_actions.txt`, appended `on_actions`):

- `on_building_completed`: the province where the building finished.
- `on_title_gain`: every province of the gained title (one for a barony, all of a county's).
- `on_holding_razed`: the razed province.
- yearly backstop: for each playable ruler with a racial heritage, every province they own (catches culture
  conversion, faith conversion, new traditions or innovations); each refresh also clears a leftover tier on a
  province whose owner is no longer racial.
- game start: every province with a racial owner.

Cost: a refresh is one script-value evaluation (a few hundred `has_building`-style checks) and one modifier swap.

### Domain limit

A plain `domain_limit` in the heritage `character_modifier` (table above). It is the one deliberate handicap; CK3
already costs a ruler 20% of levies and taxes per holding over the limit (`ABOVE_LIMIT_LEVY_PENALTY`).

## Removed traditions and units

Two Anbennar traditions are removed the same way:

- `aov_racial_armies_game_start` (appended to `on_game_start`) runs `remove_culture_tradition` on every culture
  that has them.
- `zz_aov_racial_traditions.txt` overrides each with `is_shown = { always = no }` and `can_pick = { always = no }`
  so neither can be re-adopted; the rest of each definition is copied from Anbennar.

**`tradition_sundancer_legions`** (sun elves). Its effects go away: −35% levies (replaced by the elven heritage),
−25% MAA cost, −35% MAA upkeep, +1 MAA cap, −15% casualties. Its units (`sundancer_legions`, `jaherkadezim`) move
to the sun elf roster.

**`tradition_test_maa_anb_dwarven_handgunners`** (Ruby and Silver at start; any dwarven culture from the High
Medieval era). Ruby and Silver keep their other three traditions and gain a free slot. The unit
`dwarven_handgunners` is overridden in `zz_aov_racial_maa_overrides.txt` with `can_recruit = { always = no }`; the
key stays defined so saves and Anbennar's debug `tradition_test_maa` (which lists every unlock parameter) still
load. The gnomish `artificer_handgunners` are a separate unit and are unaffected.

## Men-at-arms

### Shared rules

- **Gating.** Culture lineage triggers in `common/scripted_triggers/aov_racial_maa_triggers.txt` (culture scope):
  `aov_sun_elven_lineage_trigger` (sun_elvish or any ancestor is), `aov_wood_elven_lineage_trigger`
  (wood_elvish …), `aov_moon_elven_lineage_trigger` (elven heritage and neither sun nor wood lineage; wood elves
  descend from moon elves, so they are excluded explicitly), and `aov_<clan>_dwarven_lineage_trigger` for each of
  the eleven clans. Shared dwarf units keep Anbennar's `has_cultural_pillar = heritage_dwarven`. Each `can_recruit`
  is `culture = { <trigger> = yes }`.
- **Pricing.** Each unit is priced at vanilla power per gold. Factor = √(regiment damage ratio × regiment toughness
  ratio) against the vanilla unit of its role; buy cost and upkeep are the vanilla unit's × factor. Vanilla
  references (per regiment, damage / toughness, buy / upkeep): light footmen 1,000 / 1,600, 45 / 0.15; bowmen
  2,500 / 1,000, 55 / 0.2; crossbowmen 4,200 / 1,800, 88 / 0.3; pikemen 2,200 / 2,400, 75 / 0.3; armored footmen
  3,200 / 2,200, 90 / 0.4; light horsemen 2,200 / 1,500, 85 / 0.35; armored horsemen 5,000 / 1,750, 200 / 0.7.
  High upkeep is 3× low upkeep, as in vanilla. Costs are script values in
  `common/script_values/aov_racial_maa_values.txt` (this also replaces Anbennar's broken `stáochri_*` cost keys).
- **Terrain.** Percentages below become flat per-man `terrain_bonus` damage and toughness (rounded) of the unit's
  base stats.
- **AI.** `ai_quality = { value = @cultural_maa_extra_ai_score }` as Anbennar's racial units do, so the AI recruits
  them.
- **Icons.** Existing vanilla or Anbennar regiment icons for the unit's role in this pass.
- **Flavor text.** Every unit gets `<key>` and `<key>_flavor` in `localization/english/aov_racial_armies_l_english.yml`;
  retuned Anbennar units get new flavor text there (the later loc key wins), replacing the placeholder jokes.

Retuned Anbennar units are single-object overrides in `common/men_at_arms_types/zz_aov_racial_maa_overrides.txt`;
new units are in `aov_elven_maa_types.txt` and `aov_dwarven_maa_types.txt`.

### Units per culture

| Culture | Units | Retuned Anbennar | New |
|---|---|---|---|
| Moon elves | 6 | 4 | 2 |
| Sun elves | 6 | 2 | 4 |
| Wood elves | 5 | 4 | 1 |
| Each dwarf clan | 6 (5 shared + 1 signature) | 4 shared (Bombards unchanged) | 1 signature each (11 total) |

Totals: 18 new units, 14 retuned, 1 disabled (Dwarven Handgunners). Dwarven Bombards stay exactly as Anbennar
defines them.

### Moon elves (Moonhaven, the Lencenor vales)

Terrain: Aithchri and Gladeguards +20% in forest, hills, taiga; Gladeguards a further +30% in forest.

| Unit | Key | Role | Men | Dmg | Tough | Pursuit / Screen | Regiment dmg / tough | Buy | Upkeep |
|---|---|---|---|---|---|---|---|---|---|
| Aithchri | `aithchri` (retuned) | Archers | 50 | 120 | 35 | 0 / 0 | 6,000 / 1,750 | 115 | 0.41 |
| Sheáhrna | `sheahrna` (retuned) | Pikemen | 50 | 90 | 110 | 0 / 0 | 4,500 / 5,500 | 160 | 0.65 |
| Stáochri | `staochri` (retuned) | Heavy infantry | 25 | 300 | 200 | 10 / 10 | 7,500 / 5,000 | 210 | 0.92 |
| Marcairna | `marcairna` (retuned) | Light cavalry | 50 | 90 | 60 | 90 / 90 | 4,500 / 3,000 | 170 | 0.71 |
| Elven Knights | `aov_elven_knights` | Heavy cavalry | 25 | 450 | 160 | 40 / 0 | 11,250 / 4,000 | 455 | 1.59 |
| Gladeguards | `aov_gladeguards` | Skirmishers | 50 | 45 | 70 | 30 / 60 | 2,250 / 3,500 | 100 | 0.33 |

Lore: Elven Knights and Gladeguards are EU4 Anbennar's `elven_1_elven_knights` and `elven_5_gladeguards`.

### Sun elves (Jaher's Phoenix Empire)

Terrain: +20% in desert, drylands, floodplains, plains; −20% in jungle, forest and winter.

| Unit | Key | Role | Men | Dmg | Tough | Pursuit / Screen | Regiment dmg / tough | Buy | Upkeep |
|---|---|---|---|---|---|---|---|---|---|
| Sundancer Legionaries | `sundancer_legions` (retuned) | Heavy infantry | 25 | 280 | 240 | 20 / 20 | 7,000 / 6,000 | 220 | 0.98 |
| Jaherkadezim | `jaherkadezim` (retuned) | Heavy cavalry | 25 | 480 | 150 | 40 / 0 | 12,000 / 3,750 | 455 | 1.59 |
| Sunspear Phalanx | `aov_sunspear_phalanx` | Pikemen | 50 | 80 | 130 | 0 / 0 | 4,000 / 6,500 | 165 | 0.67 |
| Phoenix Bowmen | `aov_phoenix_bowmen` | Archers | 50 | 110 | 40 | 0 / 0 | 5,500 / 2,000 | 115 | 0.42 |
| Sandwind Outriders | `aov_sandwind_outriders` | Light cavalry | 50 | 80 | 55 | 100 / 80 | 4,000 / 2,750 | 155 | 0.64 |
| Duneblades | `aov_duneblades` | Skirmishers | 50 | 50 | 60 | 40 / 50 | 2,500 / 3,000 | 95 | 0.32 |

### Wood elves (Deepwoods)

Terrain: +50% in forest, taiga, jungle, wetlands; −20% in desert, drylands, plains. Hyodeth's duplicate `hills`
entry in Anbennar's version is dropped.

| Unit | Key | Role | Men | Dmg | Tough | Pursuit / Screen | Regiment dmg / tough | Buy | Upkeep |
|---|---|---|---|---|---|---|---|---|---|
| Ayethi | `ayethi` (retuned) | Archers | 50 | 110 | 35 | 0 / 0 | 5,500 / 1,750 | 110 | 0.39 |
| Felwyr | `felwyr` (retuned) | Skirmishers | 50 | 50 | 70 | 20 / 60 | 2,500 / 3,500 | 105 | 0.35 |
| Glaifes | `glaifes` (retuned) | Pikemen | 50 | 80 | 110 | 0 / 0 | 4,000 / 5,500 | 155 | 0.61 |
| Hyodeth | `hyodeth` (retuned) | Light cavalry (stag riders) | 50 | 90 | 60 | 90 / 90 | 4,500 / 3,000 | 170 | 0.71 |
| Greatoak Wardens | `aov_greatoak_wardens` | Heavy infantry | 25 | 260 | 220 | 10 / 10 | 6,500 / 5,500 | 205 | 0.90 |

### Dwarves: shared units (every dwarven culture)

Terrain: +30% hills; +45% mountains and desert mountains; +65% `dwarven_hold`, `dwarven_hold_surface`, `cavern`,
`dwarven_road`; −15% forest.

| Unit | Key | Role | Men | Dmg | Tough | Pursuit / Screen | Regiment dmg / tough | Buy | Upkeep |
|---|---|---|---|---|---|---|---|---|---|
| Guardians | `dwarven_guardians` (retuned) | Heavy infantry | 80 | 48 | 60 | 0 / 15 | 3,840 / 4,800 | 145 | 0.65 |
| Shieldwall | `shieldwall` (retuned) | Pikemen | 80 | 30 | 70 | 0 / 0 | 2,400 / 5,600 | 120 | 0.48 |
| Armor Breakers | `armor_breakers` (retuned) | Archers (crossbows) | 80 | 55 | 35 | 0 / 0 | 4,400 / 2,800 | 110 | 0.38 |
| Ramriders | `ramriders` (retuned) | Light cavalry | 50 | 50 | 45 | 25 / 40 | 2,500 / 2,250 | 110 | 0.46 |
| Dwarven Bombards | `dwarven_bombards` (unchanged) | Siege | 10 | — | 30 | siege 0.7 | — | Anbennar's | Anbennar's |

### Dwarves: clan signature units

Each also gets the shared dwarven terrain bonuses unless its row says otherwise.

| Clan (hold) | Unit | Key | Role | Men | Dmg | Tough | Regiment dmg / tough | Special | Buy | Upkeep | Lore source (EU4 national idea) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ruby (Rubyhold) | Grudgebearers | `aov_grudgebearers` | Pikemen | 80 | 40 | 60 | 3,200 / 4,800 | +20% plains, farmlands | 130 | 0.51 | Thorgrim "the Grudgebearer"; Struggle against Elvenisation |
| Silver (Silverforge) | Silverforge Engineer Corps | `aov_silverforge_engineers` | Siege | 20 | — | 40 | — | siege tier 4, siege value 0.9 | 1.3× Dwarven Bombards | 1.3× | Silver Army Engineer Corps |
| Stone (Escann) | Tortoise Formation | `aov_tortoise_formation` | Pikemen | 80 | 26 | 110 | 2,080 / 8,800 | highest toughness | 140 | 0.56 | EU4 unit `dwarven_5_tortoise_formation` |
| Agate (Khugdihr) | Giantbane Crossbows | `aov_giantbane_crossbows` | Archers | 80 | 65 | 35 | 5,200 / 2,800 | counters beasts, elephant cavalry | 120 | 0.42 | The Many Falls of Khugdihr |
| Copper (Ovdal Tûngr) | Uthojdihr Marines | `aov_uthojdihr_marines` | Skirmishers | 80 | 30 | 50 | 2,400 / 4,000 | +50% wetlands, floodplains, oasis | 110 | 0.37 | Ancient Trade Routes (the Uthojdihr) |
| Citrine (Seghdihr) | Seg Band Gnollhunters | `aov_seg_band_gnollhunters` | Skirmishers | 80 | 35 | 40 | 2,800 / 3,200 | pursuit 40; +50% desert, drylands, desert mountains | 105 | 0.35 | Origin of the Seg Band |
| Gold (Verkal Gulan) | Golden Gate Guard | `aov_golden_gate_guard` | Heavy infantry | 50 | 70 | 160 | 3,500 / 8,000 | +100% `dwarven_hold` | 180 | 0.80 | The Three Golden Gates |
| Pyrite (Hehodovar) | Massed Clockwork Bows | `aov_clockwork_bows` | Archers | 80 | 80 | 30 | 6,400 / 2,400 | highest dwarven damage | 125 | 0.43 | Builders Guild; EU4 unit `dwarven_5_massed_clockwork_bows` |
| Titanium (Gor Vazumbrog) | Dauvek Veker | `aov_dauvek_veker` | Heavy infantry | 50 | 110 | 90 | 5,500 / 4,500 | counters beasts, elephant cavalry ×2 | 170 | 0.75 | Dauvek Veker (monster hunters) |
| Topaz (Gor Ozumbrog) | Copper Road Wardens | `aov_copper_road_wardens` | Light cavalry | 50 | 55 | 55 | 2,750 / 2,750 | pursuit 30, screen 60; +100% `dwarven_road` | 130 | 0.53 | The Copper Road Pact |
| Marble (Shazstundihr) | Brightbeard Hammers | `aov_brightbeard_hammers` | Heavy infantry | 50 | 100 | 70 | 5,000 / 3,500 | counters heavy infantry | 140 | 0.63 | Brightbeard's Glory |

Titanium and Marble hold no counties in 1022; their units matter for landless and later rulers. Stone's tie is the
weakest (EU4 places the Tortoise Formation in the Dwarovar, not Escann).

## Files

| File | Kind |
|---|---|
| `common/culture/pillars/zz_aov_racial_heritages.txt` | Hand-written single-object overrides (4 heritages) |
| `common/culture/traditions/zz_aov_racial_traditions.txt` | Hand-written overrides of `tradition_sundancer_legions` and `tradition_test_maa_anb_dwarven_handgunners` |
| `common/men_at_arms_types/zz_aov_racial_maa_overrides.txt` | Hand-written overrides of 14 retuned Anbennar units and the disabled `dwarven_handgunners` |
| `common/men_at_arms_types/aov_elven_maa_types.txt`, `aov_dwarven_maa_types.txt` | New units |
| `common/script_values/aov_racial_maa_values.txt` | Unit costs |
| `common/scripted_triggers/aov_racial_maa_triggers.txt` | Lineage triggers |
| `common/script_values/aov_racial_levy_values.txt` | Generated |
| `common/modifiers/aov_racial_levy_modifiers.txt` | Generated |
| `common/scripted_effects/aov_racial_levy_effects.txt` | Generated |
| `common/on_action/aov_racial_armies_on_actions.txt` | Game start (tradition removal, first refresh) and refresh hooks |
| `localization/english/aov_racial_armies_l_english.yml` | Unit names and flavor, tier modifier names |
| `tools/build_racial_levies.py`, `tools/data/racial_levies.py` | Generator and its data |
| `tools/tests/test_racial_levies.py`, `tools/tests/test_racial_armies.py` | Tests |
| `docs/systems/racial-armies.md` | System doc; rows added to `CLAUDE.md` and `docs/systems/updating.md` |

## Testing

- **Unit tests** (`tools/tests`):
  - generator: classifies every `levy_size` it finds, fails on an unclassified database, writes the right
    condition per block kind, tier math (share × (1 + S) for sample S, never negative);
  - overrides: each overridden heritage, tradition and MAA type still matches Anbennar's definition in every field
    the overhaul does not change, so an Anbennar update that changes them fails a test;
  - pricing: every racial unit's buy and upkeep script value equals its role's vanilla value × factor (±5%);
  - gating: every unit's `can_recruit` names one of the lineage triggers or `heritage_dwarven`, no racial unit
    is gated by a tradition parameter, and `dwarven_handgunners` has `can_recruit = { always = no }`;
  - `FreshnessTests` covers the generated files.
- **ck3-tiger**: `python -I tools/validate.py` reports nothing new.
- **In game** (a clean tiger pass is not proof):
  1. An elven holding's levy tooltip shows the heritage −75%, its building bonuses and the matching correction, and
     its levies equal a quarter of an identical human holding's.
  2. Whether an elven ruler's +30/+30 applies to a human vassal's levies raised in the ruler's army.
  3. The correction updates when a levy building finishes and when a holding changes hands.
  4. Each culture's recruit list shows exactly its roster; no culture has the Sundancer Legions or Dwarven
     Handgunners traditions, and no one can recruit Dwarven Handgunners.
  5. A debug event spawns equal-cost human and elven armies (same gold, same county count) and lets them fight;
     result within about ±15%.
  6. `database_conflicts.log` lists the intended overrides only.

## Out of scope

- Kobold MAA terrain bonuses and kobold traps (TODO items; separate work).
- Gnome MAA (the artificer system already covers them).
- Moving mage MAA into the magic system (separate TODO item).
- RiE regiment icons.
- Correcting temporary levy modifiers (events, festivals, epidemics) and the narrow sources listed above.
- The regiment-cap edge: rich late-game elf realms reach `REGIMENT_MAA_EXTRA_BY_CAP` later than human realms and
  so gain a small edge; revisit only if in-game testing shows it is large.

## Risks

- **Modifier stacking.** The correction assumes holding, county and owner `levy_size` all add into one total for a
  holding's levies. CK3 does not document this; in-game check 1 confirms it before balance values are trusted.
- **Vassal levy quality.** If the army owner's `levy_attack` applies to vassal levies, an elf liege with human
  vassals fields human-sized vassal levies at elite quality. In-game check 2 decides whether vassal levies need
  handling.
- **Balance model.** Strength was estimated as total damage × total toughness. It ignores counters, terrain,
  knights (dwarves +3 prowess, elves no prowess loss with age), commanders, pursuit and screen.
