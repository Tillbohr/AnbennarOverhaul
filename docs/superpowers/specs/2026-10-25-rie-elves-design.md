# RiE elven holding and elf buildings (design)

Date: 2026-10-25. Status: implemented (branch rie-elves); system notes in `docs/systems/rie-elves.md`. Output files are named
`aov_elven_*` (not `aov_rie_elven_*`), since the dwarf generator owns `aov_rie_*`.

## Goal

Bring Realms in Exile's elf economy to Anbennar's elves:

1. **Holding:** RiE's `elven_holding` with its 7 `elven_settlement_01..07` levels, renamed **Elven Haven**.
2. **Buildings:** RiE's elf building lines, 19 standard lines and 5 duchy-capital lines, buildable only by elves.
3. **Conversion:** elf-held castles and tribal holdings become Elven Havens at game start; afterwards an elf ruler
   converts one by decision.
4. **Text:** every holding level and building level gets an Anbennar name and description; nothing Middle-earth is
   left in the player-facing text.

User choices: a new holding (not elven lines inside castles); conversion at game start plus a decision (no automatic
conversion later, no reversion); castles and tribal holdings convert, cities and temples do not; renamed and
re-described for Anbennar; elves only.

Elves are characters whose culture has `heritage_elven` (`is_elvish_culture = yes`): today `moon_elvish`,
`sun_elvish` and `wood_elvish` (`common/culture/cultures/anb_elven.txt`).

Sources (RiE, Workshop 2291024373): `common/buildings/lotr_buildings/lotr_elven_buildings.txt`,
`lotr_elven_settlement_holdings.txt`, `common/holdings/lotr_holdings.txt` (`elven_holding`),
`common/scripted_triggers/lotr_scripted_triggers/lotr_building_requirement_triggers.txt` (elven terrain triggers,
stronghold and city limits), `common/script_values` (the limits' values), the holding illustrations
`gfx/interface/illustrations/holding_types/refuge_*.dds`, the building type icons the blocks name, and
`localization/english/lotr_buildings_l_english.yml` (read only to find which keys need text).

## 1. Generator (`tools/build_rie_elves.py`)

Data in `tools/data/rie_elves.py`. Like `build_rie_dwarves.py`, the generator reads RiE at build time and copies
building blocks one by one through rewrite rules (shared helpers move from `tools/rie_dwarf_rewrite.py` into a common
module where both need them). Keys keep RiE's names, unprefixed (repo convention). The build stops if a key already
exists in Anbennar, the game or another overhaul file.

Outputs:

| File | Content |
|---|---|
| `common/buildings/aov_rie_elven_settlement.txt` | `elven_settlement_01..07` (Section 2) |
| `common/buildings/aov_rie_elven_buildings.txt` | the included lines (Section 3) |
| `common/scripted_triggers/aov_rie_elf_triggers.txt` | the copied terrain triggers, stronghold and city limit triggers, `aov_rie_elf_holder_trigger` |
| `common/script_values/aov_rie_elf_values.txt` | RiE's `elven_stronghold_limit` and `elven_city_limit` values |
| `common/scripted_effects/aov_elven_haven_effects.txt` | `aov_convert_to_elven_haven_effect` (Section 4), from the conversion data |
| `localization/english/aov_rie_elves_l_english.yml` | every name and description from the data (Section 5), the holding's keys, trigger tooltips |
| icons and pictures | the building type icons the blocks name and the refuge illustrations, at RiE's paths |

Rewrites:

| RiE | Becomes |
|---|---|
| `is_elf = yes` | `is_elvish_culture = yes` |
| `OR = { is_elf = yes is_valinor_maiar_character = yes }` | `is_elvish_culture = yes` |
| `building_requirement_elven = yes` (RiE: elven government flag) | `scope:holder = { is_elvish_culture = yes }` |
| `has_cultural_pillar = heritage_calaquendi` (AI weights) | culture is `moon_elvish` or `sun_elvish` |
| `building_elven_*_requirement_terrain` and the other terrain triggers the blocks name | copied as `aov_rie_elven_*_terrain_trigger`; terrains Anbennar lacks (`mallorn_forest`, `deep_forest`, `red_desert`, ...) dropped from the OR lists |
| `building_requirement_tribal = no` in `elven_settlement_*` | removed, so tribal elves (the Deepwoods) can raise their Havens |
| modifier blocks gated on a `parameter` | kept when the game or Anbennar defines it, else removed (RiE's `elven_holding_fort_level_in_*_bonus`, ...) |
| `has_cultural_parameter = next_level_*` lines | kept when defined, else removed |
| `province_dynasty_modifier` blocks with `lotr_*` perks | removed |
| Valinor assets (`middleearth_valinor`, `elven_tirion_mesh`) and Maiar branches | removed |
| `effect_desc` lines and blocks | removed (they describe activity and travel benefits wired to RiE activities or vanilla building keys) |

Every removed item goes in a build note. The build stops on any other identifier Anbennar and the game lack
(scripted trigger, building, modifier, men-at-arms type, cultural parameter, terrain), a missing icon, a key
collision, or a picture whose path Anbennar or the game already has with other content.

## 2. The holding (Elven Haven)

- **Holding:** `elven_holding`, `primary_building = elven_settlement_01`, added through
  `tools/build_holdings_override.py` (`NEW_HOLDINGS`, its list exported by the generator: the Section 3 lines and the
  15 RiE ore mines that `build_rie_dwarves.py` already defines). No vanilla castle building and no oath building is
  in the list, as in RiE.
- **Levels:** `elven_settlement_01..07` copied from RiE with the Section 1 rewrites: `levy`, `max_garrison`,
  `garrison_reinforcement_factor`, province and county modifiers, `building_slot_add`, construction time and costs.
  RiE's stronghold and city caps are commented out in RiE's own blocks, so there are none.
- **Who can raise it:** `can_construct` needs an elven holder (`aov_rie_elf_holder_trigger`). `is_enabled` is
  dropped from the level blocks: a non-elf who takes a Haven keeps its level effects, but cannot raise it and gets
  nothing from the elven buildings inside.
- **Models:** the meshes `build_holding_models.py` already imports. Moon and sun elves (`aov_high_elf_building_gfx`):
  `highelves_0N_01/02_mesh`; wood elves (`aov_wood_elf_building_gfx`): `sindarin_sanctuary_0N_mesh`; everyone else:
  the high-elf meshes. Levels 1-2 use tier 1, 3-4 tier 2, 5-6 tier 3, 7 tier 4 (`HAVEN_MESH_TIERS` in the data).
- **Pictures:** RiE's `refuge_calaquendi.dds` (high elves and default), `refuge_calaquendi2.dds` (levels 6-7),
  `refuge_sindarin.dds` (wood elves), imported at RiE's paths. RiE's Lothlórien picture is not used.
- **Governments:** `tools/build_governments_override.py` adds `elven_holding` wherever it adds
  `dwarven_hold_holding` (every government that accepts castles, tribal included).
- **Castle-level equivalence:** `zz_aov_building_requirement_triggers.txt` (the hand re-copy of Anbennar's
  `building_requirement_castle_city_church`) also accepts Haven levels 1/3/5/7 as castle levels 1-4, so vanilla
  duchy and special buildings that ask for a castle level work in a Haven.
- **Holding tab and county view:** the holding type icon and the county view's slot layout are checked in game; if
  the default castle layout does not fit, `build_county_view_override.py` gets a Haven case like the hold's.

## 3. The buildings

Included (every level RiE defines; RiE's own level counts):

| Line | Levels | Where |
|---|---|---|
| `elven_agriculture` | 7 | Haven, farm terrain |
| `elven_port` | 7 | Haven, coastal |
| `elven_mine` | 7 | Haven |
| `elven_forestry` | 7 | Haven, forest terrain |
| `elven_hunting_grounds` | 7 | Haven, hunting terrain |
| `elven_markets` | 7 | Haven |
| `elven_forges` | 7 | Haven |
| `elven_barracks` | 7 | Haven |
| `elven_fletchers` | 7 | Haven |
| `elven_stables` | 7 | Haven |
| `tree_flet` | 7 | Haven, forest or jungle |
| `elven_library` | 5 | Haven |
| `elven_guild` | 5 | Haven |
| `elven_embassy` | 5 | Haven |
| `elven_mustering_grounds` | 5 | Haven |
| `elven_sanctuary` | 5 | Haven |
| `elven_citadel` | 5 | Haven |
| `hall_of_lords` | 2 | Haven |
| `elven_armament` | 2 | Haven |
| `hall_of_music_and_tales` | 3 | duchy capital Haven |
| `crafting_enclaves` | 3 | duchy capital Haven |
| `sentinel_keeps` | 3 | duchy capital Haven |
| `warriors_enclave` | 3 | duchy capital Haven |
| `sanctuary_groves` | 3 | duchy capital Haven |

Left out: RiE's oath buildings, Valinor content, the blocks RiE has commented out. The 15 ore mines are listed in the
Haven but not redefined (they come from `build_rie_dwarves.py`).

**Elves only:** every included block asks for an elven holder in `can_construct_potential` or `can_construct` after
the rewrites (RiE's upper levels check in `can_construct`); the build stops if a block has neither. Requirements on Haven level (`has_building_or_higher =
elven_settlement_N`) stay as RiE has them.

## 4. Conversion

`aov_convert_to_elven_haven_effect` (barony province scope) sets `elven_holding`, then sets the Haven level and
swaps the buildings:

- **Level:** castle 1/2/3/4 become Haven 1/3/5/7; tribe 1/2 become Haven 1/2 (`LEVEL_MAP` in the data). The duchy and
  kingdom caps are not checked when converting.
- **Buildings:** each vanilla building with an elven counterpart (`BUILDING_MAP` in the data, for example
  `cereal_fields`, `farm_estates`, `pastures` and `hill_farms` to `elven_agriculture`, `hunting_grounds` to
  `elven_hunting_grounds`, `logging_camps` to `elven_forestry`, `quarries` to `elven_mine`, `common_tradeport` to `elven_port`,
  `barracks` and `military_camps` to `elven_barracks`, `regimental_grounds` to `elven_stables`) is removed and its
  counterpart added at the same level, capped at the line's top level and at the Haven level. Several vanilla
  buildings mapping to one line keep the highest level. Vanilla buildings with no counterpart are removed. Special
  and duchy buildings stay. The build stops on a map key that Anbennar, the game or Section 3 lacks.

**At game start** (`aov_elven_haven_game_start`, appended to `on_game_start`): every barony whose holding is
`castle_holding` or `tribal_holding`, whose holder `is_elvish_culture = yes` and whose county's culture is elven runs
the effect (user choice after the first in-game test: an elf ruling a county of another culture converts it by
decision). Cities and temples are untouched.

**Later, by decision:** `aov_raise_elven_haven_decision` (`common/decisions/aov_elven_haven_decisions.txt`):

- Shown to an elven ruler (`is_elvish_culture = yes`, at least count) who holds a castle or tribal barony in their
  domain.
- Opens picker event `aov_elven_haven.1` (namespace `aov_elven_haven`) offering up to three of the domain's eligible
  baronies, the capital first, then by Haven level; the chosen one runs the effect.
- Cost: `aov_elven_haven_conversion_cost` gold (100 x the Haven level it gets) and 100 prestige, paid in the picker
  option. Instant. Cooldown 5 years.
- AI: takes it when it has 2x the cost and an eligible barony, preferring its capital.

Nothing converts automatically after the start, and nothing reverts: a non-elf who takes a Haven keeps it as it is.

## 5. Names and descriptions

All text lives in `tools/data/rie_elves.py` (`NAMES`: key -> name, description) and is generated into the loc file;
the build stops on an included key without both. Each building level gets `building_<key>` and
`building_<key>_desc`; each line also gets `building_type_<line>_01` and its `_desc`; the holding gets
`elven_holding`, `local_holding_type_*` and its concept keys.

Style: one or two sentences in the voice of Anbennar's existing building descriptions. Elves in Anbennar are long-lived
exiles from fallen Aelantir who settled Cannor's havens; moon and sun elves keep courtly havens, the wood elves live in
the Deepwoods' groves among the fey. No Tolkien names (Yavanna, Oromë, Ulmo, Lórien, Valinor, Fëanor, telain, Sindarin
words). Names below; descriptions are written with the data.

**Elven Haven (holding):** 1 Haven Glade · 2 Flowering Haven · 3 Haven Hold · 4 Renowned Haven Hold ·
5 High Haven Hold · 6 Haven City · 7 Shining Haven City.

| Line (type name) | Levels 1 → top |
|---|---|
| `elven_agriculture` (Elven Gardens) | Foraging Bands · Homestead Gardens · Terraced Gardens · Silverleaf Orchards · Grand Gardens · Elven Vineyards · Gardens of Lost Aelantir |
| `elven_port` (Elven Harbour) | Fisher Flotillas · Stone Quays · Merchant Wharves · Elven Drydocks · Harbourmaster's Spire · Sea-Gates · Harbour of the Crossing |
| `elven_mine` (Elven Quarries) | Stone Cuttings · Shallow Ore Pits · Watermills · Great Quarries · Deep Mines · Vast Quarries · Songs of Stone |
| `elven_forestry` (Elven Woodwardens) | Careful Felling · Forester Bands · Wardens of the Wood · Speech of the Trees · Forest Reserves · Teachings of the Fey · Cultivated Wildwoods |
| `elven_hunting_grounds` (Elven Hunting Grounds) | Wildland Hunting · Hunting Bands · Hunt Masters · Trappers and Trackers · Keepers of the Herds · Hunters' Lodge · The Wild Hunt |
| `elven_markets` (Elven Markets) | Gathering Markets · Seasonal Fairs · Permanent Markets · Linked Markets · Great Storehouses · Regional Markets · Grand Markets of the Havens |
| `elven_forges` (Elven Forges) | Elven Smithies · Communal Forges · Apprentice Forges · Grand Forges · Starmetal Forges · Precursor Techniques · Hall of the Master Smiths |
| `elven_barracks` (Elven Barracks) | Militia Grounds · Militia Armouries · Warden Barracks · Warden Storehouses · Grand Barracks · Barracks Complex · Hall of the Host |
| `elven_fletchers` (Elven Fletchers) | Hearth Fletchers · Guard Fletchers · Spiral-Fletched Arrows · Song-Shaped Bows · Elf-Hair Bowstrings · Silvered Arrows · Great Arrow Stores |
| `elven_stables` (Elven Stables) | Local Riders · Regional Stables · War Stables · Armoured Riders · Farrier Smithies · Aelantiri Bloodlines · The Swift Host |
| `tree_flet` (Canopy Watchposts) | Canopy Lookout · Canopy Garrison · Canopy Armoury · Canopy Forge · Canopy Storehouses · Canopy Town · City in the Boughs |
| `elven_library` (Elven Library) | Private Collections · Ordered Library · Specialised Wings · Grand Library · Library of the Long Memory |
| `elven_guild` (Elven Guilds) | Hunters' Guild · Woodcarvers' Guild · Stonewrights' Guild · Glassmiths' Guild · Scribes' Guild |
| `elven_embassy` (Elven Gathering Halls) | Hearth Hall · Open-Air Forum · Hall of Debate · Festival Grounds · Elven Amphitheatre |
| `elven_mustering_grounds` (Elven Musters) | Sparse Summons · Regional Camps · Warden Musters · Free Companies · Call of the Havens |
| `elven_sanctuary` (Elven Sanctuary) | Secluded Groves · Healing Sanctuaries · Halls of Healing Dreams · Starlit Gardens · Gardens of Reverie |
| `elven_citadel` (Elven Citadel) | Grand Redoubts · High Citadel · Guarded Keep · Tall Bastion · Unbroken Fortress |
| `hall_of_lords` (Hall of Lords) | Audience Hall · Palace of Governance |
| `elven_armament` (Elven Armament) | Company of the Highborn · Hall of Banners |
| `hall_of_music_and_tales` (Hall of Song, duchy) | Hall of Song · The Echoing Vaults · Choir of the Long Years |
| `crafting_enclaves` (Masters' Enclave, duchy) | The Hundred Masters · Elven Masterworks · Secrets of Starfire |
| `sentinel_keeps` (Sentinel Keeps, duchy) | Remote Outpost · Fortified Watchtower · Vigilant Wardens |
| `warriors_enclave` (Warriors' Enclave, duchy) | Training Fields · Archery Ranges · Formation Drills |
| `sanctuary_groves` (Sanctuary Groves, duchy) | Great Forest Sanctuary · Fruit Groves · Groves of Meditation |

Level counts follow RiE's blocks (RiE's loc has unused names for `elven_barracks_08` and
`elven_mustering_grounds_06..07`); the generator stops when a name is missing or left over.

## Testing

- `tools/tests/test_build_rie_elves.py`: each rewrite rule on small RiE-shaped samples; the stop conditions (unknown
  identifier, collision, missing icon, block without an elf check, missing or extra name); `LEVEL_MAP` and
  `BUILDING_MAP` keys exist; `FreshnessTests` fail when the outputs are stale or orphaned.
- The holdings and governments tests: `elven_holding` is in the holdings file and in every castle government.
- `python -I tools/validate.py` clean; inherited reports from verbatim RiE code are baselined only after checking.
- **In game:**
  - moon and sun elf castles and the Deepwoods tribes start as Elven Havens at the mapped levels, with swapped
    buildings;
  - a human ruler's castle shows no elven building, and a human who takes a Haven cannot raise it or use its
    elven buildings;
  - the decision converts a chosen castle and charges the cost;
  - the models, pictures, holding tab icon and county view slots look right;
  - a tribal wood-elf ruler can raise a Haven and build in it.

## Docs

New system doc `docs/systems/rie-elves.md` (generated files, system notes), a Systems row in `CLAUDE.md`, and
`docs/systems/updating.md`: run `build_rie_elves.py` after `build_rie_dwarves.py` and before
`build_holdings_override.py` and `build_governments_override.py`, after an Anbennar or RiE update.

## Risks to confirm in game

1. Converting at start changes the balance of elven realms; the Deepwoods tribes gain RiE's settlement stats and
   buildings at once. Tune in data after playing.
2. Tribal realms with Haven capitals: tribal mechanics that look for `tribal_holding` (Anbennar or vanilla) may
   misbehave in the Deepwoods; check feudalization, tribal decisions and the holding counts in the realm view.
3. `set_holding_type` and `remove_building` on vanilla buildings in the swap: the order matters; confirm that no
   vanilla building is left in a Haven slot.
4. Some RiE blocks may lean on RiE identifiers not caught by name; the build's unknown-identifier stop is the guard,
   tiger the second.
