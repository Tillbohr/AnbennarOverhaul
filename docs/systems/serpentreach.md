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
- **Openings:** Shazstundihr -> Bazibar, Orlghelovar -> Grenwoud, Glogund Cave -> Rianelen (Azkasad is boxed in by
  its own county). Verkal Skomdihr has none: Deepwoods Wasteland (1782) lies between; add one with `OPENING_TARGETS`
  and a cut-through if wanted. No gate meshes at the openings yet.
- **Carving** (`build_map_graphics.py`, after the gate cones): floors flat at the surrounding ground (~27,250)
  +/- `TERRACE_STEP` by type; walls never lower rock and rise to at least `MIN_WALL` above the floor within
  `WALL_WIDTH`; floors painted `FLOOR_MATERIAL`, walls `WALL_MATERIAL`.
- **People:** placeholder `stone_dwarvish` dwarves; per duchy an elder (holds from 860.1.1, dies 1000-1010) and his
  son; the emperor holds `d_arg_ordstun` himself. The 6 holds are in `tools/data/holds.py`.
- **Needs an in-game test:** the map loads with the new ids; locators, province terrain and region files are read;
  textures and wall heights look right (tune in `tools/data/serpentreach.py`).
