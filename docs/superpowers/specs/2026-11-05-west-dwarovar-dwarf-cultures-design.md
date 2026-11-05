# West Dwarovar dwarf cultures: design

Status: design approved 2026-11-05; written spec awaiting review. Nothing is implemented.
Visual draft with the art: https://claude.ai/artifact/6WZokbtUZKcw33g3z9ypsh

## Goal

West Dwarovar's eight dwarven kingdoms use `silver_dwarvish` as a stand-in (`docs/systems/west-dwarovar.md`). This
work replaces it with their eight EU4 Anbennar hold cultures, so each hold plays differently. It follows the
Serpentreach cultures (`docs/superpowers/specs/2026-11-03-serpentreach-dwarf-cultures-draft.md`,
`docs/systems/serpentreach.md`).

Each culture gets:

- an ethos and base traditions from its hold's EU4 ideas;
- one new tradition of its own, granted at game start;
- a clan men-at-arms unit gated by that tradition, except Sapphire.

Success means all of this:

1. Every county and character of the eight kingdoms has its hold's culture at both bookmarks.
2. Each culture shows its base traditions, its own tradition and its language.
3. Each unit can be recruited by its culture only, with the art listed here.
4. The tool tests pass, tiger reports nothing new, and the in-game list below is ready for the user to run.

## Out of scope

- Khugdihr stays `darkscale`/`nimrithani`, so EU4's Agate culture is not placed there.
- Quartz dwarves: the Krakdhum pocket is not on the map.
- `silver_dwarvish` itself, and any other dwarf culture, is unchanged.
- Events, decisions, buildings, faiths, new titles and map changes.
- Numbers are starting values at the level of the existing clans. Balance beyond that needs play.

## The eight cultures

All are founding cultures with no `parents` or `created`, as in Serpentreach. Colours are the hold's EU4 country
colour, which its kingdom already uses on the map. Display names follow the existing dwarf style: "Kronium Dwarven",
"Kronium Dwarf", "Kronium Dwarves".

| Culture key | Kingdom | Colour | Ethos | Base traditions (file order) | `dlc_tradition` |
|---|---|---|---|---|---|
| `kronium_dwarvish` | `k_amldihr` | 60 40 80 | bureaucratic | mountain_homes, legalistic, agrarian | none |
| `platinum_dwarvish` | `k_haraz_orldhum` | 74 80 97 | courtly | mountain_homes, ruling_caste, castle_keepers | artisans (`royal_court`) |
| `mithril_dwarvish` | `k_mithradhum` | 81 231 213 | stoic | mountain_homes, loyal_soldiers, storytellers | none |
| `dagrite_dwarvish` | `k_er_natvir` | 147 191 155 | egalitarian | mountain_homes, caravaneers, swords_for_hire | none |
| `opal_dwarvish` | `k_verkal_kozenad` | 255 228 216 | spiritual | mountain_homes, battlefield_looters, life_is_just_a_joke | none |
| `lead_dwarvish` | `k_hul_jorkad` | 160 114 158 | communal | mountain_homes, city_keepers, sorcerous_metallurgy | none |
| `ramsteel_dwarvish` | `k_orlazam_az_dihr` | 74 111 121 | bellicose | mountain_homes, horse_breeder, culinary_art | none |
| `sapphire_dwarvish` | `k_dur_vazhatun` | 0 25 119 | bureaucratic | mountain_homes, philosopher_culture, astute_diplomats | none |

EU4 sources for the base traditions:

| Culture | Source ideas |
|---|---|
| Kronium | Rule with a Kronium Glove (legalistic), Serpent's Vale Terraced Farming (agrarian) |
| Platinum | Vainglorious Nobility and the Hold of Platinum Chains (ruling caste), Turrets of Orldhûm (castle keepers), Platinum Jewellers (artisans) |
| Mithril | High King's Favorite (loyal soldiers), the folklorists of The Warchanters (storytellers) |
| Dagrite | Dwarovstapola (caravaneers), Mercenary Guards (swords for hire) |
| Opal | Opal Railway Robbers (looters), Bad Luck! (life is just a joke) |
| Lead | The Junction's facilities (city keepers), A Tale of Lead and Gold (sorcerous metallurgy) |
| Ramsteel | Originator of Ram Cavalry (horse breeder), Slow-roasted Orlazam Lamb (culinary art) |
| Sapphire | Scholars of the Dwarovar (philosopher culture), Sapphire Wit (astute diplomats) |

Every other field is `stone_dwarvish`'s from the overhaul's generated `anb_dwarf.txt`: heritage, martial custom, head
determination, name list and the coat of arms, building, clothing and unit gfx keys, plus `ethnicities`. As in
Serpentreach, a test keeps them equal, because `build_holding_models.py` and `build_portraits.py` never see this file.

## Language

New `language_west_dwarovar_dwarven`, spoken by all eight, defined like `language_serpentreach_dwarven`:
`language_is_shown_trigger`, the same `ai_will_do`, colour 96 72 128 (Amldihr's purple, lightened). Its loc name is
"West Dwarovar Dwarven".

## Placement

`tools/data/west_dwarovar.py` replaces the stand-in with an explicit `KINGDOM_CULTURES` map, using the table above and
keeping `"k_khugdihr": "darkscale"`. The existing generator already reads this map for counties and characters, so
no generator code changes and no game-start effect is needed. The Vale's terrace counties are in `k_amldihr`, so they
are Kronium. `RELIGION` stays `ancestor_worship`.

## Own traditions

These go in `tools/data/racial_traditions.py`, with one culture gate and heritage `heritage_dwarven`, and in its
game-start grants. Each costs the base prestige with no ethos penalty, like the other clan traditions.

| Key | Name | Category | Layers | Character | County / culture | Parameter |
|---|---|---|---|---|---|---|
| `tradition_high_assembly` | The High Assembly | realm | diplo, western, council | `vassal_limit` 5, `vassal_opinion` 5, `monthly_county_control_growth_factor` 0.15 | | `aov_unlock_maa_amldavhad_guard` |
| `tradition_reign_of_the_highlord` | Reign of the Highlord | realm | steward, western, crown | `monthly_prestige_gain_mult` 0.1, `hostile_county_attrition` 0.15, `heavy_infantry_toughness_mult` 0.1 | | `aov_unlock_maa_platinum_warsuits` |
| `tradition_vow_of_honesty` | The Vow of Honesty | societal | martial, western, warrior_monk | `enemy_hostile_scheme_success_chance_add` -10, `monthly_piety_gain_mult` 0.1, `heavy_infantry_damage_mult` 0.1 | | `aov_unlock_maa_mithril_warchanters` |
| `tradition_all_roads_lead_to_er_natvir` | All Roads Lead to Er-Natvir | realm | steward, western, city | `domain_tax_mult` 0.1, `supply_duration` 0.25 | culture: `cultural_acceptance_gain_mult` 0.25 | `aov_unlock_maa_mercenary_guards` |
| `tradition_spymasters_of_aul_dwarov` | Spymasters of Aul-Dwarov | societal | intrigue, western, palace_politics | `owned_hostile_scheme_success_chance_add` 10, `intrigue` 1, `max_loot_mult` 0.25 | | `aov_unlock_maa_railway_robbers` |
| `tradition_dwarven_plumbing` | Dwarven Plumbing | realm | steward, western, garden_architects | `health` 0.25, `garrison_size` 0.2 | county: `development_growth_factor` 0.1 | `aov_unlock_maa_sewer_wardens` |
| `tradition_stewards_of_the_vale` | Stewards of the Vale | combat | martial, western, rider | `heavy_cavalry_damage_mult` 0.15, `movement_speed` 0.15, `plains_advantage` 3, `farmlands_advantage` 3 | | `aov_unlock_maa_fourfoot_chargers` |
| `tradition_setzunkhupa` | The Setzunkhûpa | societal | learning, western, philosopher | `cultural_head_fascination_mult` 0.2, `learning` 1, `monthly_learning_lifestyle_xp_gain_mult` 0.15 | | none |

The `eu4` source lines:

| Tradition | EU4 ideas |
|---|---|
| The High Assembly | The High Assembly of Aul-Dwarov, Birthplace of the Old Empire, Rule with a Kronium Glove |
| Reign of the Highlord | Reign of the Highlord, Turrets of Orldhûm, Vainglorious Nobility |
| The Vow of Honesty | Vow of Honesty, The Warchanters of Mithradhum, Goblinslayer Academy |
| All Roads Lead to Er-Natvir | All Roads Lead to Er-Natvir, Melting Pot, Immaculate Supply Lines |
| Spymasters of Aul-Dwarov | Spymasters of Aul-Dwarov, Opal Railway Robbers, Ladies of the Opal Calling |
| Dwarven Plumbing | Dwarven Plumbing, Lead Lined Lives, Life-bearing Lake |
| Stewards of the Vale | Originator of Ram Cavalry, Stewards of Vale and Beyond, The Charge of Tednur Fourfoot |
| The Setzunkhûpa | The Setzunkhûpa, Skygazers, Students of Mind and Sky |

Descriptions are in our own words and carry no Realms in Exile terms; the generator checks that.

## Men-at-arms

Units are hand-written in `common/men_at_arms_types/aov_dwarven_maa_types.txt`, gated by
`valid_for_maa_trigger = { PARAMETER = aov_unlock_maa_<unit> }`, with `allowed_in_hired_troops = no` and
`ai_quality = { value = @cultural_maa_extra_ai_score }`, like the Serpentreach clan units.

| Unit key | Name | Culture | Type | Men | Damage | Toughness | Pursuit | Screen | Extra terrain |
|---|---|---|---|---|---|---|---|---|---|
| `aov_amldavhad_guard` | Amldavhad Guard | Kronium | heavy_infantry | 50 | 90 | 130 | 0 | 0 | none |
| `aov_platinum_warsuits` | Platinum Warsuits | Platinum | heavy_infantry | 25 | 180 | 320 | 0 | 0 | none |
| `aov_mithril_warchanters` | Warchanters of Mithradhûm | Mithril | heavy_infantry | 50 | 105 | 105 | 0 | 0 | none |
| `aov_mercenary_guards` | Er-Natvir Mercenary Guards | Dagrite | heavy_infantry | 50 | 90 | 95 | 0 | 0 | `dwarven_road` 1.0 |
| `aov_railway_robbers` | Opal Railway Robbers | Opal | skirmishers | 80 | 38 | 38 | 40 | 0 | `dwarven_road` 1.0 |
| `aov_sewer_wardens` | Hul-Jorkad Sewer Wardens | Lead | skirmishers | 80 | 30 | 52 | 0 | 0 | `dwarven_hold` 1.0, `cavern` 1.0 |
| `aov_fourfoot_chargers` | Fourfoot Chargers | Ramsteel | heavy_cavalry | 50 | 150 | 90 | 40 | 0 | `plains` 0.5, `farmlands` 0.5 |

**Terrain.** Each unit takes the dwarf set (hills 0.3, mountains and desert mountains 0.45, holds, caverns and roads
0.65, forest −0.15), overridden by the extras. Bonuses are the multiplier × the stat, rounded, as in `DWARF_TERRAIN`
in `test_racial_armies.py`.

**Counters.** These are role defaults. Heavy infantry counters `pikemen` 1, as Lightflare Guard does, without its
militia bonus. Skirmishers counter `heavy_infantry` 1, as Flint Forest Rangers do. Heavy cavalry counters `archers` 1
and `gunpowder` 1, as Elven Knights do.

**Costs.** These use the racial armies formula, with the role's vanilla regiment values from `VANILLA` in
`test_racial_armies.py`. Values are rounded like the existing units and sit within that test's 5% tolerance. High
upkeep is 3× low.

| Unit | Buy | Low upkeep | High upkeep |
|---|---|---|---|
| Amldavhad Guard | 185 | 0.82 | 2.46 |
| Platinum Warsuits | 205 | 0.90 | 2.70 |
| Warchanters of Mithradhûm | 180 | 0.79 | 2.37 |
| Er-Natvir Mercenary Guards | 155 | 0.70 | 2.10 |
| Opal Railway Robbers | 110 | 0.36 | 1.08 |
| Hul-Jorkad Sewer Wardens | 110 | 0.37 | 1.11 |
| Fourfoot Chargers | 395 | 1.37 | 4.11 |

### Art

The game finds a unit's big and small pictures by its icon name, so all three files share one name. A unit that mixes
sources gets files under its own name, as `aov_lens_crossbows` does. Files go in `gfx/interface/icons/regimenttypes/`,
`gfx/interface/illustrations/men_at_arms_big/` and `men_at_arms_small/`.

| Unit | `icon` value | Icon source | Pictures source (RiE) | Note |
|---|---|---|---|---|
| Amldavhad Guard | `aov_amldavhad_guard` | RiE `house_guard_dwarf` | `blacklock_heavy_infantry` | The icon has no pictures of its own |
| Platinum Warsuits | `aov_rie_undying_of_khazad_dum` | RiE, same name | same name | |
| Warchanters of Mithradhûm | `aov_mithril_warchanters` | Anbennar `paladins` | `stiffbeard_heavy_infantry` | No Anbennar unit uses this icon |
| Er-Natvir Mercenary Guards | `aov_rie_blacklock_mercenaries` | RiE, same name | same name | Icon is 121×131: resize |
| Opal Railway Robbers | `aov_railway_robbers` | Anbennar `rogues` | `blacklock_skirmishers` | No Anbennar unit uses this icon |
| Hul-Jorkad Sewer Wardens | `aov_rie_blacklock_engineers` | RiE `Blacklock_engineers` | `Blacklock_engineers` | Icon is 112×119: resize; lower-case the copies |
| Fourfoot Chargers | `aov_rie_longbeard_cavalry` | already copied | already copied | Shared with Ramriders, the only ram-mounted art |

Icons are normalised to 120×120 with `python -I tools/eu4_import.py convert <src> <dst> --resize 120x120`. Art is
copied once, not generated.

## Dynasty names

`DYNASTY_NAMES` in `tools/data/west_dwarovar.py` renames ten of the generated per-duchy dynasties. As in Serpentreach,
they carry no `az` prefix and the dynasty keys stay the same. Every other duchy, including all of Kronium and
Platinum, keeps `az-<duchy>`.

| Duchy | Dynasty | EU4 source |
|---|---|---|
| `d_mithradhum` | Strongbellow | Mithril ideas: Belgar Strongbellow's clan |
| `d_riftway` | Goldbeard | Mithril ideas: Kramdur Goldbeard |
| `d_dwarovrod_7_9` | Goblinslayer | Mithril ideas: Thorin Goblinslayer |
| `d_the_railyard` | Ironhelm | Dagrite ideas: Bardur Ironhelm |
| `d_stunad_kozenad` | Forktongue | `opal_dwarf` dynasty list |
| `d_zokkorna_caverns` | Ringbeard | Opal ideas: Morzad Ringbeard |
| `d_westnest` | Kezdori | Opal ideas: Bozan Kezdori |
| `d_jorkad_junction` | Leadpipe | `lead_dwarf` dynasty list |
| `d_orlazam` | Fourfoot | Ramsteel ideas: Tednur Fourfoot |
| `d_vazhatun` | Melmarn | Sapphire ideas: Beddugr Melmarn |

## Files

| Action | File |
|---|---|
| New | `common/culture/cultures/aov_west_dwarovar_cultures.txt` |
| New | `common/culture/pillars/aov_west_dwarovar_language.txt` |
| New | `localization/english/aov_west_dwarovar_cultures_l_english.yml` (culture name, prefix, collective noun; language name) |
| New | `tools/tests/test_west_dwarovar_cultures.py`, modelled on `test_serpentreach_cultures.py` |
| New | Art files listed above |
| Edit data | `tools/data/west_dwarovar.py`: `KINGDOM_CULTURES`, `DYNASTY_NAMES`, and the stand-in comment |
| Edit data | `tools/data/racial_traditions.py`: eight traditions and grants |
| Edit by hand | `common/men_at_arms_types/aov_dwarven_maa_types.txt`, `common/script_values/aov_racial_maa_values.txt`, `localization/english/aov_racial_armies_l_english.yml` (name and `_flavor`) |
| Regenerate | `python -I tools/build_west_dwarovar.py`, `python -I tools/build_racial_traditions.py` |
| Edit tests | `test_west_dwarovar.py` (the `culture = silver_dwarvish` check at line 343 and a culture map check), `test_racial_armies.py` (`ROSTER`, `EXPECTED`, `DWARF_EXTRA`, the art test), `test_build_racial_traditions.py` (`GATED_ELSEWHERE`, grants) |
| Edit docs | `docs/systems/west-dwarovar.md`, `racial-traditions.md`, `racial-armies.md`, `CLAUDE.md` (the West Dwarovar and Racial traditions rows) |

`build_racial_levies.py` needs no rerun, because no new tradition has a levy modifier; its `FreshnessTests` confirm
that. No West Dwarovar title, province or map data changes, so `build_serpentreach.py`, `build_holds.py`,
`build_holding_models.py` and `build_map_graphics.py` need no rerun either. The full test run confirms this too.

## Tests and validation

`test_west_dwarovar_cultures.py` checks:

- BOM and LF on the three new text files;
- the language pillar matches `language_segbandalic_dwarven`'s `ai_will_do`, with the key replaced;
- each culture's colour, ethos, traditions in order, language and artisans `dlc_tradition`, with no `parents` or
  `created`;
- the copied fields equal `stone_dwarvish`'s;
- colours differ from each other and from every other dwarf culture;
- loc is complete;
- `KINGDOM_CULTURES` matches this spec and leaves Khugdihr `darkscale`.

Existing suites then check pricing, gates, terrain, art files, unit unlocks, game-start grants and generator
freshness. The final run is `python -I -m unittest discover -s tools/tests`, then `python -I tools/validate.py`.

## Checked already

- All eight culture keys and all eight tradition keys are free in the game, Anbennar and the overhaul.
- All picked base traditions exist. None depends on a DLC to work once it is set in the culture file. `artisans` is
  granted through `dlc_tradition` because its `is_shown` needs Royal Court.
- Legalistic (`is_shown` on faith doctrines), Caravaneers (`always = no`), Culinary Art (`can_pick` needs farmlands)
  and Sorcerous Metallurgy (`can_pick` on witchcraft doctrines) only limit later picking. The closest precedents are
  Diamond's culture file, which lists the hidden Ancient Miners, and Shasoura, which gets Caravaneers through the
  game-start grant. Whether Diamond's works in game is still an open Serpentreach check.
- Four modifier keys are new to `racial_traditions.py`: `heavy_cavalry_damage_mult`, `plains_advantage`,
  `farmlands_advantage` and `monthly_learning_lifestyle_xp_gain_mult`. All four appear in vanilla script.

## Risks

- **Colour close to Moorman.** Platinum (74 80 97) is nearly Moorman's (71 84 102) in the culture map mode. Moorman is
  a human culture, so the test does not catch it. Platinum keeps EU4's colour; change it if it confuses in play.
- **Sapphire and Cobalt.** Both are dark blue, so check them together in the culture map mode.
- **Icon style.** `paladins` and `rogues` are Anbennar's painted style, while the other dwarf units use RiE's icons.
  They may need a second look beside the others in the recruit list.
- **Sorcerous Metallurgy** carries nomad and yurt parameters that do nothing for settled dwarves. It stays for its
  weapon inspiration and barracks bonuses.

## To confirm in game

The game is the only proof for these; tiger cannot show them.

1. Each of the eight kingdoms' counties and characters shows its culture at both bookmarks; Khugdihr is still kobold.
2. The culture window shows West Dwarovar Dwarven, the listed base traditions and the own tradition. Platinum shows
   Artisans with Royal Court.
3. Legalistic, Caravaneers, Culinary Art and Sorcerous Metallurgy show and apply on their cultures.
4. Each of the seven units is in its own culture's recruit list only, with its icon and pictures. Sapphire has none.
5. The two mixed-art units show the right pictures: Warchanters in silver armour, Railway Robbers with spears and
   shields.
6. Dynasty names read as listed, with no "az-". Other duchies keep it.
7. Every modifier shows in its tradition tooltip, with no blank lines. This matters most for the four new keys.
8. The holdings, clothes and armies use the RiE dwarf assets, like other dwarf cultures.
