# Serpentreach design

EU4 Anbennar's `serpentreach_region` (19 areas, 70 provinces of the West Serpentspine Dwarovar) added to the CK3 map as
playable provinces carved into the existing Serpentspine block, Godherja-style, under a placeholder empire.

## Intent

- **User asked:** implement EU4's Serpentreach in the overhaul; the beings there live in the mountain, so the mountain
  stays and the provinces are carved terrain like Godherja's; a placeholder empire holds them for now.
- **User chose:** each EU4 province becomes a county, each EU4 area (state) a duchy, kingdoms improvised, the whole
  region one empire; baronies by type; a dwarven realm of generated placeholder characters; surface gates only (no
  link to Middle Dwarovar); traced EU4 shapes; a new generator run before `build_map_graphics.py`.
- **Recommended defaults taken (user pre-approved):** no gate meshes at the openings in v1; one dwarven culture
  (`stone_dwarvish`, `ancestor_worship`); placeholder dynasties named after duchies; the 6 Serpentreach holds join the
  dwarven-hold system.
- **Success:** the game loads; ~124 new provinces sit in carved, flat-floored trenches inside the Serpentspine with
  steep walls; the rest of the block stays impassable mountain; four openings reach the surface; every title has a
  holder in both bookmarks (867 and 1022); the generators rebuild everything after an Anbennar update.

## Where it goes

The CK3 map already has the mountain: a ~1000 x 230 px block (x 2230-3200, rows 1900-2130) inside impassable
province 2426 "Big Waste", Deepwoods to the north, the Bulwar/Dostanor lands to the south. An affine transform fitted
on the 98 provinces both maps share near Serpentreach (scale ~3.5, median error 23 px) puts 99% of the EU4 region's
pixels on province 2426; the remaining 59 px fall on Basilan and are clipped.

## §1 Map geometry (`tools/build_serpentreach.py`, data `tools/data/serpentreach.py`)

- **Trace:** read EU4's `provinces.bmp`; fit the affine transform EU4 -> CK3 by least squares on matched province
  centroids (same id, same first five letters of the name, within `FIT_BOX` around the region). Each CK3 pixel in the
  region's transformed bounding box takes the EU4 province under the inverse-mapped pixel centre.
- **Clip and wall:** a pixel becomes floor only if it is on province 2426 and at least `WALL_MARGIN` (4) px from any
  pixel of another province. Rock always separates Serpentreach from the surface except at the openings.
- **Counties -> baronies:** each EU4 province is a county; its floor is split into `BARONIES[type]` baronies (holds
  and surface holds 4, caverns 2, roads 1; `BARONY_OVERRIDES` per county) by seeded k-means (Lloyd, fixed iterations,
  seeds from the pixel order), so rebuilds are byte-identical. The capital barony is the piece holding the pixel
  nearest the county's centroid.
- **Openings:** each EU4 entrance (a Serpentreach province bordering a non-Serpentreach EU4 land province) gets a
  corridor `OPENING_WIDTH` (6) px wide from the county's floor straight to the nearest pixel of its CK3 neighbour; the
  corridor pixels (on 2426 only) belong to the county's capital barony. The neighbour is the same id when CK3 has it
  with the same name (Bazibar 534, Grenwoud 511, Azkasad 650), otherwise the nearest non-2426 land province to the
  transformed contact point (Verkal Skomdihr -> a Deepwoods province); `OPENING_TARGETS` overrides.
- **Ids and colours:** new provinces are appended after Anbennar's last id (6943) in county order (EU4 area order,
  then EU4 province order), capital barony first. Colours are generated deterministically and checked against every
  existing colour.
- **Outputs:** `map_data/provinces.png`, `map_data/definition.csv` (generated full-file overrides). Province 2426
  keeps its other pixels and stays impassable, so `default.map` and `adjacencies.csv` are unchanged.
- **Build stops on:** a county with fewer floor pixels than `MIN_BARONY_PX` x its barony count; a barony that is not
  4-connected; a county whose floor is not connected to the rest of Serpentreach; an opening that touches a province
  other than its target or 2426; any changed pixel that was not province 2426.

## §2 Carving and look (in `tools/build_map_graphics.py`)

`build_map_graphics.py` imports `build_serpentreach.layout(roots)` (the same deterministic function that draws the
provinces) instead of reading the generated `provinces.png`, so the two generators always agree. Its existing raise,
gate and cone steps keep running on Anbennar's map unchanged; carving is a final heightmap step:

- **Base:** the median height of non-2426 land pixels within `CARVE_GROUND_RADIUS` (40) px of the floor.
- **Floors:** every floor pixel is flat at `base + TERRACE[type]` (roads 0, caverns -`TERRACE_STEP`, holds and surface
  holds +`TERRACE_STEP`; `TERRACE_STEP` 600 in 16-bit height units), giving Godherja's stepped halls. Opening
  corridors ramp linearly from the county floor to the outside land height at their mouth.
- **Walls:** for 2426 pixels at Euclidean distance d from the nearest floor pixel, with `rim = floor + MIN_WALL`
  (6000): d <= `WALL_WIDTH` (4): `floor + (max(orig, rim) - floor) * smoothstep(d / WALL_WIDTH)` (a steep slope, so
  rock within 4 px of the floor may come down); up to `WALL_WIDTH + WALL_FADE` (8): `max(orig, lerp(rim, orig, t))`;
  beyond, unchanged.
- **Packed heightmap:** changed blocks are repacked by the existing code.
- **Terrain:** floor pixels get their county type's `FLOOR_MATERIALS` entry at full weight; wall pixels (d <=
  `WALL_WIDTH`) blend it into `WALL_MATERIAL` by smoothstep(d / WALL_WIDTH). The materials are Godherja's
  `imperial_road` (roads), `canyon_rough_rock` (caverns), `mayik_tiles_01` (holds) and `mayik_cliff_01` (walls),
  appended to the end of `materials.settings` with blank masks.
- **Smoothing** (addendum after the first in-game look, which showed 3-4 px stair steps): the traced labels go through
  a majority filter (radius 3, 3 passes) before the wall margin and the county split.
- **Gates** (addendum, user request): every opening gets RiE's Erebor gate through the existing gate pipeline, cone turn 0; the carve runs after the cones and re-cuts the corridor; pieces near the floor are dropped. Verkal Skomdihr's corridor cuts through Deepwoods Wasteland (1782) to reach the Deepwoods.

## §3 Titles, history and people (`tools/build_serpentreach.py`)

- `common/landed_titles/aov_serpentreach.txt`: `e_serpentreach` > 3 kingdoms (`KINGDOMS` in data:
  `k_arg_ordstun` west, `k_ovdal_lodhum` centre, `k_gor_burad` east) > 19 duchies (`d_<area>`) > 70 counties
  (`c_<slug of EU4 name>`, e.g. `c_argrod_3`, `c_ovdal_lodhum`) > baronies (`b_<county slug>`, then `_2`.. `_4`).
  Deterministic colours; capitals are the first county of each duchy and the hold county where there is one. A key
  that already exists in Anbennar stops the build.
- `history/provinces/aov_serpentreach.txt`: every barony gets `culture`/`religion` (`CULTURE`, `RELIGION`); holdings:
  capital `castle_holding`; holds' 2nd `city_holding`, 3rd `church_holding`, 4th none; caverns' 2nd none.
- `history/characters/aov_serpentreach.txt` and `common/dynasties/aov_serpentreach_dynasties.txt`: per duchy and for
  the empire, an elder (born 830-845, dies 1000-1010) and his son (born 975-990) of one dynasty (`az-<Duchy>`),
  `trait = race_dwarf`, names from `name_list_dwarven`, deterministic.
- `history/titles/aov_serpentreach.txt`: at 860.1.1 the elders hold the empire / their duchy and every county of it,
  dukes are vassals of the emperor (`liege`); at each elder's death date the son takes the same titles.
- `common/province_terrain/aov_serpentreach_terrain.txt`: EU4 type -> Anbennar terrain (`dwarven_road`, `cavern`,
  `dwarven_hold`, `dwarven_hold_surface`).
- `map_data/geographical_regions/aov_serpentreach_regions.txt`: `world_serpentreach` with the 19 duchies.
- `localization/english/aov_serpentreach_l_english.yml`: titles and adjectives (EU4 names; road names `Argrod | 3 |`
  -> `Argrod 3`; extra baronies `<County> Halls`, `Deeps`, `Vaults`), dynasty names.
- `tools/data/holds.py`: the 6 holds (Arg-Ördstun, Ovdal Lodhum, Gor Búrad level 2; Shazstundihr, Verkal Skomdihr,
  Orlghelovar level 1) are added to `HOLDS`; rerun `build_holds.py`.
- **Locators:** whole-file overrides of Anbennar's `building_locators`, `special_building_locators`,
  `combat_locators`, `player_stack_locators`, `siege_locators`, `other_stack_locators`, `stack_locators`, `activities`
  with one instance per new province at the barony's interior point (the floor pixel farthest from its edge),
  `position = { x 0 4096-row }`.

## §4 Order, tests, risks

- **Order:** `build_serpentreach.py`, then `build_holds.py` (holds data), then `build_map_graphics.py`. Rerun all
  three after an Anbennar map, title or locator change. Recorded in `docs/systems/updating.md` and a new
  `docs/systems/serpentreach.md`.
- **Tests** (`tools/tests/test_serpentreach.py`): affine fit on synthetic points; k-means split deterministic and
  connected; slugging; carve profile on a synthetic grid (floor flat, walls monotone, nothing lowered off-floor);
  locator text; FreshnessTests entry for the generated files.
- **Validation:** `python -I tools/validate.py`; grep tiger for the new files.
- **Risks (test in game):** the province map loads with the new ids; the game accepts locator overrides; provinces in
  `common/province_terrain` from a second file are read; floor and wall textures look right; Anbennar's
  `rivers.png` has no river pixels on the floor (the generator reports any).
