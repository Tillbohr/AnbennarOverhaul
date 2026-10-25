# Racial armies

Levies, men-at-arms and domain limit by race, from the Gameplay section of `docs/Anbennar-Overhaul-Master-TODO List.md`.
Spec: `docs/superpowers/specs/2026-10-21-racial-armies-design.md` (every stat and cost lives in its tables). Plan:
`docs/superpowers/plans/2026-10-21-racial-armies.md`.

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/script_values/aov_racial_levy_values.txt`, `common/modifiers/aov_racial_levy_modifiers.txt`, `common/scripted_effects/aov_racial_levy_effects.txt`, `localization/english/aov_racial_levy_l_english.yml` | `python -I tools/build_racial_levies.py` | The per-holding levy correction (below), from every `levy_size` and `<terrain>_levy_size` in the game, Anbennar and this submod; data in `tools/data/racial_levies.py`. The game's files in folders Anbennar's `descriptor.mod` replaces (`replace_path`) are skipped. It stops on a `levy_size` in a folder the data file neither classifies nor ignores, and on a value that is not a number, a file `@variable` or a constant script value. Rerun after an Anbennar update or a CK3 patch. `tools/tests/test_build_racial_levies.py` (`FreshnessTests`) fails when the files are stale. |

## System

- **Heritages** (`common/culture/pillars/zz_aov_racial_heritages.txt`, single-object overrides of Anbennar's four bare
  heritages; `type`, `is_shown`, `audio_parameter` copied). By the ruler's culture (`character_modifier`), so levy
  count and levy quality always come from one culture:

  | Heritage | `levy_size` | Levy damage / toughness | `domain_limit` | Levies vs a human holding |
  |---|---|---|---|---|
  | Elven | −0.75 | +30 / +30 (40 per man) | −1 | 25% |
  | Dwarven | −0.40 | +7 / +7 (17) | −2 | 60% |
  | Gnomish | −0.50 | +10 / +10 (20) | −1 | 50% |
  | Kobold | +0.50 | −3 / −3 (7) | 0 | 150% |

  Count × quality equals a human's, so levy power is unchanged; races differ in how many men they field. Each also
  sets the parameter `aov_racial_levy_<race>`.
- **Levy correction.** CK3 adds every `levy_size` into one total, so a flat −75% would let elven levies grow about
  twice as fast as human ones as buildings add bonuses. For a holding whose owner has a racial heritage, with S the
  holding's summed covered levy bonus, the province modifier `aov_racial_levy_<race>_<n>` (n = S / 0.05 rounded,
  S clamped to −1..+3) adds `levy_size = −f × 0.05 × n` (f: elven 0.75, dwarven 0.40, gnomish 0.50, kobold −0.50), so
  the holding ends at share × (1 + S) and never below its share. Negative sources (administrative governments, some
  traits and laws) get a positive correction.
  - Covered (`aov_holding_levy_size_bonus`, province scope): buildings in the province (`province_modifier`, culture,
    faith and terrain variants), buildings in the county (`county_modifier` and variants, counted per building, since they stack),
    duchy capital buildings (`duchy_capital_county_modifier`, every de jure county of the duchy), the owner's buildings (`character_modifier`), traditions, innovations and pillars
    (the owner's culture for `character_modifier`, the county's for `county_modifier`/`province_modifier`), doctrines
    and tenets (owner's faith), holy sites (owner's faith controls it), governments, realm laws and traits (owner).
    `<terrain>_levy_size` counts only in a holding of that terrain. A building's `is_enabled` is copied into its
    condition (`scope:holder` as `province_owner`, `scope:county` as `county`), and an object defined in several
    files counts once, from the file loaded last.
  - Not covered (`IGNORED` in the data file): event, activity and festival modifiers, epidemics, estate (domicile)
    buildings, council and court positions, house aspirations, confederations, special subject contracts. They are
    temporary or narrow. Development and county control multiply levies and need no correction.
  - Refresh (`common/on_action/aov_racial_armies_on_actions.txt`): `aov_refresh_holding_levy_correction` (province
    scope; removes the tier recorded in `var:aov_racial_levy_tier`/`var:aov_racial_levy_race`, then adds the owner's)
    runs at game start for every racial ruler's holdings, on `on_building_completed` (every holding of the building's
    de jure duchy), `on_title_gain` (every province of a county, the province of a barony), `on_holding_razed`, and
    yearly (`yearly_playable_pulse`) for every holding of the counties of rulers who are racial or have a corrected
    holding there (this reaches vassal barons' temples and cities).
- **Removed traditions** (`common/culture/traditions/zz_aov_racial_traditions.txt`, hidden and unpickable; removed
  from every culture by `aov_racial_armies_game_start`): `tradition_sundancer_legions` (its units belong to every sun
  elf culture), `tradition_test_maa_anb_dwarven_handgunners` (`dwarven_handgunners` is overridden with
  `can_recruit = { always = no }`; the key stays for saves and Anbennar's debug `tradition_test_maa`) and
  `tradition_test_maa_anb_dwarven_bombard` (it unlocked nothing: Anbennar comments out its `dwarven_bombard` unit, and
  every late-medieval dwarven culture already has the generic `dwarven_bombards`).
- **Men-at-arms.** Elves: few men per regiment with very high stats; dwarves: 80-man tough regiments strong in holds,
  mountains, caverns and on dwarven roads. Every unit costs its role's vanilla buy cost and upkeep times
  √(regiment damage ratio × regiment toughness ratio), so the same gold buys the same power
  (`common/script_values/aov_racial_maa_values.txt`). Gates are culture lineage (the culture or any ancestor;
  `common/scripted_triggers/aov_racial_maa_triggers.txt`), never a tradition; shared dwarf units keep
  `has_cultural_pillar = heritage_dwarven`. Wood elves descend from moon elves, so the moon trigger excludes the wood and
  sun lineages.

  | Culture | Units |
  |---|---|
  | Moon elves | Aithchri, Sheáhrna, Stáochri, Marcairna (retuned), Elven Knights, Gladeguards |
  | Sun elves | Sundancer Legionaries, Jaherkadezim (retuned), Sunspear Phalanx, Phoenix Bowmen, Sandwind Outriders, Duneblades |
  | Wood elves | Ayethi, Felwyr, Glaifes, Hyodeth (retuned), Greatoak Wardens |
  | Every dwarf | Guardians, Shieldwall, Armor Breakers, Ramriders (retuned), Dwarven Bombards (Anbennar's) |
  | Dwarf clans | Ruby Grudgebearers, Silver Silverforge Engineer Corps, Stone Tortoise Formation, Agate Giantbane Crossbows, Copper Uthojdihr Marines, Citrine Seg Band Gnollhunters, Gold Golden Gate Guard, Pyrite Massed Clockwork Bows, Titanium Dauvek Veker, Topaz Copper Road Wardens, Marble Brightbeard Hammers |

  Retuned units are single-object overrides in `common/men_at_arms_types/zz_aov_racial_maa_overrides.txt` (only stack,
  stats, terrain and winter bonuses, gate, costs and `ai_quality` change); new units are in
  `aov_elven_maa_types.txt` and `aov_dwarven_maa_types.txt`. Names and flavor: new units in
  `localization/english/aov_racial_armies_l_english.yml`, retuned units in
  `localization/replace/english/aov_racial_armies_replace_l_english.yml`.
- **Art.** Icons and pictures come from Realms in Exile's men-at-arms, copied once (not generated; edit by hand) under
  an `aov_rie_` prefix into `gfx/interface/icons/regimenttypes/`, `gfx/interface/illustrations/men_at_arms_big/` and
  `men_at_arms_small/`; each unit's `icon` names the file. Sun elves use RiE's Calaquendi (`high_elven_*`) set and
  `noldor_heavy_infantry`, moon elves its Lomiquendi (`grey_elven_*`) set, wood elves its Moriquendi (`green_elven_*`,
  Avarin) set, and every dwarf unit the Longbeard set, chosen by unit role:

  | RiE picture | Units |
  |---|---|
  | `noldor_heavy_infantry`, `high_elven_heavy_cavalry`, `_pikemen`, `_archers`, `_light_cavalry`, `_skirmishers` | Sundancer Legionaries, Jaherkadezim, Sunspear Phalanx, Phoenix Bowmen, Sandwind Outriders, Duneblades |
  | `grey_elven_archers`, `_pikemen`, `_heavy_infantry`, `_light_cavalry`, `_heavy_cavalry`, `_skirmishers` | Aithchri, Sheáhrna, Stáochri, Marcairna, Elven Knights, Gladeguards |
  | `green_elven_archers`, `_skirmishers`, `_pikemen`, `_heavy_infantry` | Ayethi, Felwyr, Glaifes, Greatoak Wardens |
  | `royal_elk_riders` (Lasgalen's stag riders) | Hyodeth |
  | `longbeard_heavy_infantry` | Guardians, Golden Gate Guard, Dauvek Veker, Brightbeard Hammers |
  | `longbeard_pikemen` | Shieldwall, Grudgebearers, Tortoise Formation |
  | `longbeard_crossbowmen` | Armor Breakers, Giantbane Crossbows, Massed Clockwork Bows |
  | `longbeard_cavalry` (ram riders) | Ramriders |
  | `longbeard_horse_archers` (ram chariots) | Copper Road Wardens |
  | `longbeard_skirmishers` | Uthojdihr Marines, Seg Band Gnollhunters |

  The two light cavalry icons were 130×130 DXT5 in RiE and are resized to 120×120 (`eu4_import.py convert --resize`).
  Siege units (Silverforge Engineer Corps, Dwarven Bombards) keep the vanilla bombard art. The military window's levy
  and knight pictures for elf and dwarf rulers (RiE's `levies_elven`, `levies_longbeard`, `knights_elven`,
  `knights_falathrim`, `knights_silvan`, `knights_longbeard`, copied the same way) are wired up by
  `build_knight_icons.py`; see `knight-icons.md`.

## Hand-maintained overrides to re-check after an Anbennar update

`tools/tests/test_racial_armies.py` fails when Anbennar changes any field the overhaul copies:
the four heritages (`HeritageTests`), the three traditions (`TraditionRemovalTests`) and the 15 men-at-arms types
(`MaaTests.test_retuned_units_keep_unchanged_fields`, `test_handgunners_disabled`; `icon` is one of the overhaul's changed fields). Re-copy the changed fields by hand.

## In-game checks

A clean tiger pass does not prove the engine accepts this. Still to confirm:

1. An elven holding's levy tooltip shows the heritage −75%, its building bonuses and the matching `Elven Levy Share`
   modifier, and its levies are a quarter of an identical human holding's (assumes holding, county and owner
   `levy_size` add into one total, and that county modifiers from several building instances stack).
2. Whether an elven ruler's +30/+30 levy damage and toughness also applies to a human vassal's levies in their army.
3. The correction updates when a levy building finishes and when a holding changes hands.
4. Each culture's recruit list shows exactly its roster, with the RiE icon and picture on every elf and dwarf unit; no culture has the Sundancer Legions or Dwarven Handgunners
   traditions, and no one can recruit Dwarven Handgunners.
5. Debug battles (console, playing a human-culture ruler): `event aov_racial_armies_debug.0001` (vs a random elven
   ruler) and `event aov_racial_armies_debug.0002` (vs a random dwarven ruler) declare war and spawn equal-cost
   armies at root's capital (`events/aov_racial_armies_debug_events.txt`); the result should be within about 15%.
6. `database_conflicts.log` lists only the intended overrides.

## Known limits

- The Silverforge Engineer Corps (siege tier 4, value 0.9) has no era gate, unlike Anbennar's bombards (late
  medieval).
- Rich late-game elf realms reach the regiment cap later than human realms (`REGIMENT_MAA_EXTRA_BY_CAP`) and so gain a
  small edge.
- Kobold MAA terrain bonuses and traps, and gnome MAA, are separate work.
