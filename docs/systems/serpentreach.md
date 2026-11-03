# Serpentreach

## Generated files

| File | Generator | Why |
|---|---|---|
| `map_data/provinces.png`, `map_data/definition.csv`, `gfx/map/map_object_data/{building,special_building,combat,player_stack,siege,other_stack,stack}_locators.txt`, `gfx/map/map_object_data/activities.txt` (whole-file overrides of Anbennar's), `common/landed_titles/aov_serpentreach.txt`, `history/provinces/aov_serpentreach.txt`, `history/titles/aov_serpentreach.txt`, `history/characters/aov_serpentreach.txt`, `common/dynasties/aov_serpentreach_dynasties.txt`, `common/province_terrain/aov_serpentreach_terrain.txt`, `map_data/geographical_regions/aov_serpentreach_regions.txt`, `localization/english/aov_serpentreach_l_english.yml` | `python -I tools/build_serpentreach.py` | EU4 Anbennar's `serpentreach_region` traced onto CK3 province 2426 by `tools/serpentreach_layout.py` with `tools/data/serpentreach.py`. Rerun after any Anbennar map, title or locator change, then `build_holds.py` and `build_map_graphics.py`. |

## System

- Spec `docs/superpowers/specs/2026-11-02-serpentreach-design.md`, plan `docs/superpowers/plans/2026-11-02-serpentreach.md`.
- **Layout:** an affine fit (111 shared provinces, median error ~21 px) maps EU4's 67 Serpentreach provinces onto
  the Serpentspine block inside impassable province 2426; floors keep 4 px of rock from every other province.
  67 counties (EU4 provinces), 19 duchies (EU4 areas), 3 kingdoms (`KINGDOMS`), `e_serpentreach`; 124 baronies (holds
  4, caverns 2, roads 1), new ids from 6944.
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
- **Terrain:** each floor gets its county type's material (`FLOOR_MATERIALS`: roads `imperial_road`, caverns
  `canyon_rough_rock`, holds `mayik_tiles_01`); the slope blends it into `WALL_MATERIAL` `mayik_cliff_01`. The four are
  Godherja's textures, appended to the end of `materials.settings` (existing indices unchanged) with blank masks
  `masks/aov_<id>_mask.png` (`GODHERJA_MATERIALS`, `build_map_graphics.godherja_materials`). Ask the Godherja team
  before a Workshop upload, as for the shaders.
- **People:** placeholder `stone_dwarvish` dwarves; per duchy an elder (holds from 860.1.1, dies 1000-1010) and his
  son; the emperor holds `d_arg_ordstun` himself. The 6 holds are in `tools/data/holds.py`.
- **Needs an in-game test:** the map loads with the new ids; locators, province terrain and region files are read;
  textures and wall heights look right (tune in `tools/data/serpentreach.py`).
