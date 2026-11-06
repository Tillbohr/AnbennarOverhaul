# Dwarovar tribes

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/governments/aov_dwarovar_governments.txt`, `common/landed_titles/aov_dwarovar_tribes.txt`, `common/landed_titles/zz_aov_dwarovar_tribes_overrides.txt`, `common/scripted_effects/aov_tribes_pool_effects.txt`, `common/scripted_triggers/aov_tribes_pool_triggers.txt`, `common/script_values/aov_tribes_values.txt`, `common/decisions/zz_aov_dwarovar_tribes_overrides.txt`, `common/modifiers/aov_tribes_modifiers.txt`, `history/titles/aov_dwarovar_tribes.txt`, `history/characters/aov_dwarovar_tribes.txt`, `common/dynasties/aov_dwarovar_tribes.txt`, `common/coat_of_arms/coat_of_arms/aov_dwarovar_tribes.txt`, `localization/english/aov_dwarovar_tribes_l_english.yml` | `python -I tools/build_dwarovar_tribes.py` | Everything that follows from `tools/data/dwarovar_tribes.py`, or is a copy of a tribal government, a vanilla decision or Anbennar's Segbandal titles, so an update carries through. Run after `build_governments_override.py` and `build_west_dwarovar.py`. |
| Culture, faith and holding of tribe counties in `history/provinces/aov_serpentreach.txt`, `aov_segbandal.txt`, `aov_west_dwarovar.txt` | the three region generators, through `build_serpentreach.county_people` | Tribe counties are region counties. The region generators also add `can_create` and drift settings to every title they write. |

Imported once (no generator): `gfx/coat_of_arms/textured_emblems/aov_tribe_<slug>.dds`, the flags of EU4 H81, H87, M05, H86, H90, H75, H85, H89, H73 and H82 (`python -I tools/eu4_import.py convert gfx/flags/<tag>.tga <dds> --upscale2x --mips`; M05's source is large, so `--resize 256x256 --mips`).

Hand-written: `common/decisions/aov_tribes_decisions.txt`, `common/character_interactions/aov_tribes_interactions.txt`, `common/scripted_effects/aov_tribes_effects.txt`, `common/scripted_triggers/aov_tribes_triggers.txt`, `common/on_action/aov_tribes_on_actions.txt`, `events/aov_tribes_duel_events.txt`, `aov_tribal_war_cb` in `common/casus_belli_types/aov_race_relations_wars.txt`, and the placeholder `common/culture/{pillars,cultures,name_lists}/aov_tribes*`, `history/cultures/heritage_{orcish,goblinoid}.txt` and `common/religion/{religion_family_types,religion_types,holy_site_types}/aov_tribes*`, with their `localization/english/aov_tribes_*` files.

## System

- Spec `docs/superpowers/specs/2026-11-05-dwarovar-tribes-design.md`, plan `docs/superpowers/plans/2026-11-05-dwarovar-tribes.md`.
- **Placement:** 27 tribes hold 215 of the 256 carved counties in 1022 (`TRIBES`). Dwarves keep six holds (`DWARF_REALMS`), kobolds keep Khugdihr's 10 counties. `tribe_of(eu4_id, area)` answers for any county; `check_tribes` stops the build if an Anbennar or EU4 change leaves a tribe's area or seat with no county.
- **Governments:** `orcish_warband_government` and `goblin_chiefdom_government` are generated copies of `tribal_government` (so about 200 game files reading `government_is_tribal` treat them as tribal), adding `government_ignores_rightful_liege_penalties`, `sticky_government`, `use_as_base_on_landed`, `use_as_base_on_rank_up` and `dynasty_named_realms`, the flags `government_is_dwarovar_tribe` and `government_is_orcish_warband` or `government_is_goblin_chiefdom`, and `can_get_government` by race trait. `on_title_gain` (`aov_tribe_title_gain`) moves an orc or goblin to their race's government when they gain a pool title or anything inside a tribal realm.
- **Vanilla decisions blocked for tribes:** a generated override adds one `is_shown` line to the two whole-realm feudalism decisions, `tribal_challenge_ruler_decision` and the three `found_*` decisions. The seventh in the spec, `convert_whole_realm_to_feudalism_west_african_pagan_decision`, is only in the game's `80_major_decisions.txt`, which Anbennar's file replaces, so it never loads; a test says so.
- **Title pool:** blank top-level titles (40/20/6 orc, 40/15/4 goblin, `POOL`), modelled on vanilla's `k_danelaw`, with `de_jure_drift_disabled`, `no_automatic_claims`, `ignore_titularity_for_title_weighting`, `definite_form` and `can_create = { always = no }`. A title with no holder is free. `aov_tribe_take_free_title_effect = { TIER = duchy }`, run in the future holder's scope, saves a free title of their race as `scope:aov_new_title` with its capital at theirs; the caller transfers it. A pool title reaching someone neither orc nor goblin is destroyed, which frees it. `create_dynamic_title` is not used, because no effect sets drift during play.
- **Name and arms follow the dynasty:** a pool title's loc reads `[GetTitleByKey('x').GetHolder.GetDynasty.GetName] Warband` (Warhost, Horde; Chiefdom, High Chiefdom, Swarm); the map reads the dynasty through `dynasty_named_realms` and `house_based_map_names` on the name lists. A primary kingdom shows the game's tier word first: "The Skewered Drake Kingdom (Skewered Drake Warhost)". `aov_tribe_title_sync_effect` sets `set_coa = holder.dynasty`; dynasty arms are keyed by the dynasty key.
- **People:** each chief holds a pool duchy and every county of the seat's EU4 area; each other area has a sub-chief holding its counties as a vassal. Every chief and sub-chief has their own dynasty, so a vassal who wins a duel brings a new name and new arms. Ten chiefs carry EU4 flags; the rest take EU4's orc and goblin dynasty names in list order, and a generated charge on a field from the key. A tribe never holds a dwarven title. Dates are the tribes' own (`TRIBE_START` 980), not the regions' 860.
- **Forming and raising:** `aov_form_tribal_{duchy,kingdom,empire}_decision` for a count, duke or king with enough counties in the realm and prestige (`FORM`); `aov_raise_tribal_vassal_interaction` lifts a tribal vassal two or more tiers below the ruler to a free title one tier below the ruler, for 200 prestige. Dukes make count vassals with vanilla's grant interaction.
- **Keeping dwarven titles dwarven:** generated titles refuse `government_is_dwarovar_tribe` in `can_create`, and kingdoms and empires take `de_jure_drift_disabled`. Anbennar's `e_middle_dwarovar`, its four kingdoms and their duchies get the same through `zz_aov_dwarovar_tribes_overrides.txt`, nested as Anbennar has them, with each title's own fields copied (see below). `k_khugdihr` is Anbennar's under another empire and moves by history, so it is not covered: a tribe holding its de jure land can create it.
- **Duels (orcs only):** `aov_challenge_warlord_decision`, for a landed orc vassal of an independent warband, 5-year cooldown. The ruler gets `aov_tribe_duel.1`, which rechecks that both can still fight. Accepting runs vanilla's `configure_start_single_combat_effect` with `FATALITY = no`, then `.2` moves every title and vassal to a winning challenger and kills the ruler in that order, so the realm does not partition; a winning ruler kills the challenger. Refusing costs `add_prestige_level = -5` and the permanent `aov_refused_challenge` (`general_opinion = -50`).
- **Wars:** `aov_tribal_war_cb` lets a tribal ruler take a neighbouring county of another; it is the monster war with both gates swapped, and shares its cost. `aov_ai_tribe_may_not_target_trigger` stops AI tribes starting it or the monster war outside `world_serpentreach`, `world_west_dwarovar` and `world_segbandal`.
- **Reviving a hold's culture:** `aov_revive_<hold>_decision` in `build_holds.py`, from `culture` and `kingdom` on each hold. A dwarf personally holding exactly one hold, this one, with its de jure kingdom unheld, can spend 500 prestige so that they, their spouse, their children and the hold's county take the culture. A decision only, with no prompt on creating a kingdom.
- **Placeholders:** `black_orc` and `cave_goblin` are humans with western graphics (`ethnicities = { 100 = arab }`), as gnolls shipped; EU4's names; Old Dookan and Goblinic Shamanism in one new family. Vic3 Anbennar has `orc_head_bs` and `goblin_head_bs` for a later portraits job.

### What the first in-game test found

Four rounds on a throwaway branch; the spec's "First test results" has them all. What later work should know:

- **Redefining a title clears its own fields and moves it to where it is nested.** At the top level, `k_hehodovar` left its empire. Nested in the empire, the empire lost its colour and cultural name. Children left out of the redefinition keep theirs. So `render_title_override` copies each title's own fields.
- **Drift never appeared,** on a drift-off title or on a control without the setting, even with rulers holding the duchies. Why the control does not drift is unknown, so the setting stays and the observer run checks again.
- **`error.log` shows 12 "Could not find the preregistered modifier type" lines per new government,** which entries in `common/modifier_definition_formats` do not silence. RiE ships no entries for its orc government either. The government worked anyway.

## Wars a tribal AI can still reach the surface with

The surface rule covers only the two wars above. These are not touched; the observer run decides whether any needs an override:

| War | File | Who can use it | Reach |
|---|---|---|---|
| `county_conquest_cb` | Anbennar's `00_conquest.txt` | Anyone not landless | A neighbouring county |
| `tribal_subjugation_cb` | Anbennar's `00_subjugation.txt` | `government_is_tribal`, by prestige level | A tribal ruler, which the surface also has |
| `vassalization_cb` | Anbennar's `00_vassalization.txt` | Anyone not landless | A neighbour |
| `invasion_war` | Anbennar's `00_invasion_war.txt` | `government_is_tribal`, once a lifetime | A kingdom |

Raiding stays allowed by design.

## Needs an in-game test

1. The game starts cleanly with all pool titles and tribes.
2. Tribes, characters, cultures and faiths show as in the spec's tables; six holds are dwarven; a chief's capital is sensible and their realm shows its dynasty's name and arms.
3. The de jure kingdom map mode is unchanged at the start and after a long observer run. `e_middle_dwarovar` reads "Segbandal" to a dwarven ruler, with colour 36 96 143; all five of its kingdoms and their duchies are in place.
4. What the game does with counties left unheld, such as Khugdihr's. This was not checked during design.
5. Cultures with no followers survive and are not stuck far behind on innovations when revived. If they are, the revival decision catches them up.
6. Duels: all three outcomes. On a win, the winner is independent, the realm does not partition, and name and arms change. On a refusal, prestige falls to the lowest level from any starting level, and the modifier shows -50 in other rulers' opinion breakdowns and stays after years pass. A goblin vassal is never offered the challenge.
7. Forming duchy, kingdom and empire titles; the raise-a-vassal interaction; a duke granting a county to a courtier creates a count vassal; pool titles are reused once free; a pool running out shows the tooltip; a dwarf inheriting a pool title sees it destroyed without trouble. Holds behave as before apart from ruin: conquest does not change them, and digging still works under a dwarf.
8. Tribal law and military windows work with the new governments, and tribes cannot feudalise.
9. Revival appears and hides as specified, with Arg-Ôrdstun conquering Orlghelovar as the negative case.
10. AI behaviour over several decades: tribes fight each other, do not start surface conquests, and do not overrun the Segbandal's 26 counties in the first decade. Check the wars listed above.
