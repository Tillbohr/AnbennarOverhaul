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
  heritages; `type`, `is_shown`, `audio_parameter` copied). By the ruler's culture (`character_modifier`). Every
  ruler's whole levy pool follows their own race: their own holdings (`levy_size`) and what their vassals send them,
  whatever the vassals' race (`vassal_levy_contribution_mult`), all at the ruler's levy quality. A vassal raising
  their own army uses their own race.

  | Heritage | `levy_size` and `vassal_levy_contribution_mult` | Levy damage / toughness | `domain_limit` | Levies vs a human ruler |
  |---|---|---|---|---|
  | Elven | −0.75 | +30 / +30 (40 per man) | −1 | 25% |
  | Dwarven | −0.40 | +7 / +7 (17) | −2 | 60% |
  | Gnomish | −0.50 | +10 / +10 (20) | −1 | 50% |
  | Kobold | +0.50 | −3 / −3 (7) | 0 | 150% |

  Count × quality equals a human's, so levy power is unchanged; races differ in how many men they field. Each also
  sets the parameter `aov_racial_levy_<race>`. A racial vassal's own levies are already at their share, so what it
  sends a racial liege is cut again (an elf vassal sends an elf liege a quarter of its quarter).
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
- **Vassal contribution correction.** The same drift applies to `vassal_levy_contribution_mult` (crown authority
  laws, the large-levies perk, a tradition, three monuments add to it), so each racial ruler gets the character
  modifier `aov_racial_contribution_<race>_<n>` taking back the race's share of those bonuses
  (`aov_ruler_contribution_bonus`, character scope; same tiers and range). `aov_refresh_ruler_contribution_correction`
  runs at game start for every racial ruler, on `on_title_gain` for the new holder, and in the same yearly pulse.
- **Removed traditions** (`common/culture/traditions/zz_aov_racial_traditions.txt`, hidden and unpickable; removed
  from every culture by `aov_racial_armies_game_start`): `tradition_sundancer_legions` (its units belong to every sun
  elf culture) and `tradition_test_maa_anb_dwarven_handgunners` (`dwarven_handgunners` is overridden with
  `can_recruit = { always = no }`; the key stays for saves and Anbennar's debug `tradition_test_maa`).
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

## Hand-maintained overrides to re-check after an Anbennar update

`tools/tests/test_racial_armies.py` fails when Anbennar changes any field the overhaul copies:
the four heritages (`HeritageTests`), the two traditions (`TraditionRemovalTests`) and the 15 men-at-arms types
(`MaaTests.test_retuned_units_keep_unchanged_fields`, `test_handgunners_disabled`). Re-copy the changed fields by hand.

## In-game checks

A clean tiger pass does not prove the engine accepts this. Still to confirm:

1. An elven holding's levy tooltip shows the heritage −75%, its building bonuses and the matching `Elven Levy Share`
   modifier, and its levies are a quarter of an identical human holding's (assumes holding, county and owner
   `levy_size` add into one total, and that county modifiers from several building instances stack).
2. Whether an elven ruler's +30/+30 levy damage and toughness also applies to a human vassal's levies in their army.
3. The correction updates when a levy building finishes and when a holding changes hands.
4. Each culture's recruit list shows exactly its roster; no culture has the Sundancer Legions or Dwarven Handgunners
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
