# Serpentreach

## Generated files

| File | Generator | Why |
|---|---|---|
| `map_data/provinces.png`, `map_data/definition.csv`, `gfx/map/map_object_data/{building,special_building,combat,player_stack,siege,other_stack,stack}_locators.txt`, `gfx/map/map_object_data/activities.txt` (whole-file overrides of Anbennar's), `common/landed_titles/aov_serpentreach.txt`, `history/provinces/aov_serpentreach.txt`, `history/titles/aov_serpentreach.txt`, `history/characters/aov_serpentreach.txt`, `common/dynasties/aov_serpentreach_dynasties.txt`, `common/province_terrain/aov_serpentreach_terrain.txt`, `map_data/geographical_regions/aov_serpentreach_regions.txt`, `localization/english/aov_serpentreach_l_english.yml`, `common/coat_of_arms/coat_of_arms/aov_serpentreach.txt` | `python -I tools/build_serpentreach.py` | EU4 Anbennar's `serpentreach_region` traced onto CK3 province 2426 by `tools/serpentreach_layout.py` with `tools/data/serpentreach.py`. Rerun after any Anbennar map, title or locator change, then `build_holds.py` and `build_map_graphics.py`. |

Imported once (no generator): `gfx/coat_of_arms/textured_emblems/aov_{orlghelovar,shazstundihr,arg_ordstun,verkal_skomdihr,ovdal_lodhum,gor_burad}.dds`,
the EU4 flags of the six holds (`KINGDOM_ARMS` names the tag) converted with
`python -I tools/eu4_import.py convert gfx/flags/<tag>.tga gfx/coat_of_arms/textured_emblems/aov_<kingdom>.dds --upscale2x --mips`.
The generator stops when one is missing.

## System

- Spec `docs/superpowers/specs/2026-11-02-serpentreach-design.md`, plan `docs/superpowers/plans/2026-11-02-serpentreach.md`.
- **Layout:** an affine fit (111 shared provinces, median error ~21 px) maps EU4's 67 Serpentreach provinces onto
  the Serpentspine block inside impassable province 2426; floors keep 4 px of rock from every other province.
  67 counties (EU4 provinces), 19 duchies (EU4 areas), 6 kingdoms (`KINGDOMS`), `e_serpentreach`; 124 baronies (holds
  4, caverns 2, roads 1), new ids from 6944, numbered in `AREA_ORDER` (fixed, so regrouping kingdoms keeps the ids,
  the province map and the locators).
- **Kingdoms:** one per dwarven hold, each a contiguous run of areas from the hold's out (west to east):
  Orlghelovar (+ Argrod Origin, North Altar), Shazstundihr (+ South Altar), Arg-Ôrdstun (+ King's Caverns),
  Verkal Skomdihr (Stunad Skomdihr + Argrod 6-8, Thievesbane), Ovdal Lodhum (+ Argrod 9-11, Shroomfissure, Still
  Caverns), Gor Bûrad (+ Buradforge, Zarn, Argrod 14-16, Argrod Junction). The hold county is the kingdom's capital.
  `world_serpentreach` lists the six kingdoms (geographical regions take no `empires`).
- **Arms:** each kingdom, its hold's duchy (named like the kingdom, except Verkal Skomdihr's Stunad Skomdihr) and its
  hold county carry the EU4 hold's flag (`KINGDOM_ARMS`: Orlghelovar I12, Shazstundihr I11, Arg-Ôrdstun H76, Verkal
  Skomdihr I13, Ovdal Lodhum H77, Gor Bûrad I16) as a textured emblem over the whole shield, like the Deepwoods groves;
  `color1` is the flag's most common colour. EU4 has no country in the other 13 areas, so their duchies get composed
  dwarven arms (`DUCHY_CHARGES`, one per area: hammer, fire altars, crown, axe, crossed keys, lamp, flaming jewel, gem,
  cog, fire, runestone, a flame over an anvil for Buradforge) on a field of the duchy's map colour divided by a
  `DUCHY_PATTERNS` pattern picked by key hash; charges are gold on dark fields and black on pale ones. Only generic
  game and Anbennar emblems, never another hold's own (`ce_anb_seghdihr`, ...); the build stops on a missing emblem.
  EU4 has no Serpentreach tag, so the empire and the other counties keep generated arms.
- **Map colours:** each kingdom takes its EU4 country colour, except Arg-Ôrdstun's grey (200 200 200), darkened to
  steel (120 124 132) so it does not merge with Shazstundihr's off-white beside it. Duchies are HLS lightness shades
  of it (`DUCHY_SHADES`, slid together to stay within 0.12-0.92 so none repeats); counties vary
  +/- `COUNTY_JITTER` around their duchy's; `e_serpentreach` is bronze (`EMPIRE_COLOUR`).
- **Rulers:** the emperor holds Arg-Ôrdstun's kingdom and duchy; each other kingdom is held by the lord of its hold's
  duchy, a vassal of the emperor, and the other dukes of a kingdom are the king's vassals (King's Caverns is the
  emperor's). The realm map mode shows the empire's colour; the kingdom colours show in the de jure kingdom map mode.
- **Openings:** corridors `OPENING_WIDTH` 10 px wide, at most `OPENING_REACH` 160 px long: Shazstundihr -> Basilan
  (county Bazibar; Bazibar itself is not reachable at that width), Orlghelovar -> Grenwoud, Glogund Cave -> Rianelen
  (Azkasad is boxed in by its own county), Verkal Skomdihr -> Deepwoods85, cut through Deepwoods Wasteland (1782,
  `OPENING_CUT_THROUGH`: its corridor pixels become the barony's and its rock gets walls like 2426's).
- **Gates:** `build_map_graphics.py` puts RiE's Erebor gate at every opening, like the 9 dwarven-range gates
  (`gate_sites_for_openings`: at the corridor pixel nearest the mouth, facing out of the corridor). Their cones
  keep turn 0 (`transplant_overrides`), so they stay on the corridor's axis; mountain pieces within
  `PIECE_FLOOR_CLEARANCE` 3 px of the floor are dropped (`drop_pieces_on_floor`); the carve runs after the cones,
  so the corridor and floor are cut back through them.
- **Smooth outlines:** before the wall margin and the county split, a majority filter (`SMOOTH_RADIUS` 3,
  `SMOOTH_PASSES` 3, `smooth_labels`) removes the ~3.5 px stair steps of the upscaled EU4 shapes from the floor
  outline and the province borders.
- **Carving** (`build_map_graphics.py`, after the gate cones): floors flat at the surrounding ground (~27,350)
  +/- `TERRACE_STEP` by type; within `WALL_WIDTH` 4 px (Euclidean, nearest floor pixel carried outward) a
  smoothstep slope from the floor up to the rock, or to the rim (floor + `MIN_WALL`) where the rock is lower; beyond
  it low rock fades from the rim to its own height over `WALL_FADE` and is never lowered.
- **Terrain, by region from EU4 lore** (`sl.province_materials`; plan previewed in the git-ignored
  `art_work/serpentreach_terrain_plan.html`): each EU4 area has a style (`AREA_STYLES`, default otherwise) giving the
  floor per county type and the wall the slope blends into (`TERRAIN_STYLES`); `COUNTY_FLOORS` and `BARONY_FLOORS`
  override single floors.
  - default: roads and holds `mayik_tiles_01` (stone tiles), caves `mountain_02_d_granitegrey`, walls `rock_13_05_10`;
  - volcanic (Gor Bûrad, Bûradforge, Zarn, Argrod 14-16): caves `hardened_lava`, walls `rock_14_05_05`; Gor Bûrad's
    hold `hardened_lava_b` (the Basalt Hold) with `lava` in `b_gor_burad_2`, the barony facing Lavawater and Molten
    Core, which are `lava` too (a test checks the barony index still faces them after a layout change);
  - marble (Shazstundihr, South Altar): roads `desert_cracked_white`, holds `mayik_tiles_02`, caves `rock_white`,
    walls `mountains_white`;
  - diamond (Arg-Ôrdstun): caves `mountain_02_dark` (kimberlite); garnet (Ovdal Lodhum): caves
    `red_canyon_surface_stone_2`; mushroom (Shroomfissure): caves `moss_ground_01`.
  Every used material Anbennar lacks is appended to the end of `materials.settings` (existing indices unchanged) from
  Godherja's list, else Realms in Exile's (`build_map_graphics.appended_materials`, 14 today: 10 Godherja, 4 RiE),
  its textures copied as `aov_<file name>` (mods reuse vanilla names, e.g. Godherja's
  `mountain_02_d_desert_normal.dds`; spaces become `_`), a texture only the game has used as it is, with blank masks
  `masks/aov_<id>_mask.png`. Ask the Godherja team before a Workshop upload, as for the shaders.
- **Cultures** (hand-written; spec `docs/superpowers/specs/2026-11-03-serpentreach-dwarf-cultures-draft.md`, plan
  `docs/superpowers/plans/2026-11-03-serpentreach-dwarf-cultures.md`): one EU4 culture per hold, `cobalt_dwarvish`
  (Orlghelovar), `diamond_dwarvish` (Arg-Ôrdstun), `flint_dwarvish` (Verkal Skomdihr), `garnet_dwarvish` (Ovdal Lodhum)
  and `basalt_dwarvish` (Gor Bûrad) in `common/culture/cultures/aov_serpentreach_cultures.txt`, speaking
  `language_serpentreach_dwarven` (`common/culture/pillars/aov_serpentreach_language.txt`); loc in
  `aov_serpentreach_cultures_l_english.yml`. Shazstundihr keeps Anbennar's `marble_dwarvish` (Segbandalic, unchanged).
  Ethos and three traditions come from each hold's EU4 ideas. Every other field is `stone_dwarvish`'s from the
  overhaul's generated `anb_dwarf.txt`, including the RiE gfx keys, which the generators only add to Anbennar's
  files. `test_serpentreach_cultures.py` keeps the two equal, so copy any change by hand.
- **People:** placeholder `stone_dwarvish` dwarves; per duchy an elder (holds from 860.1.1, dies 1000-1010) and his
  son; the emperor holds `d_arg_ordstun` himself. The 6 holds are in `tools/data/holds.py`.
- **Needs an in-game test:** the map loads with the new ids; locators, province terrain and region files are read;
  textures and wall heights look right (tune in `tools/data/serpentreach.py`).
