# Map graphics from Realms in Exile — design

Date: 2026-10-13. Status: approved in conversation, awaiting written-spec review.

## Goal

Make Anbennar's map look closer to *Lord of the Rings: Realms in Exile* (RiE, Workshop 2291024373): its ground
textures on mountains and rocks, its lighting, colour grading, skybox, snowfall, fog of war and water settings, and
the map shaders that draw them. Everything ships inside this Overhaul; players need only Anbennar and the Overhaul.

Out of scope: army unit models (the user will give instructions later), RiE's height data, texture placement maps,
colour map, object placement and water textures (all drawn for Middle-earth's shape), the surround map, court-scene
and portrait shaders.

## Decisions (from the conversation)

- Lives in this Overhaul, not a separate submod or repo.
- Ground textures: remap Anbennar's mountain, rock, hill and snow materials to RiE textures, plus RiE's same-name
  replacements for vanilla's snow and pine-forest textures. Lowlands stay vanilla.
- Colour grading by Anbennar region, one box per kingdom; the Middle Dwarovar gets no grade for now (a milder
  "deep" grade may come later).
- Permission: port now, credit RiE, Godherja and Victoria 3 in `credits.txt`, and ask the RiE and Godherja teams
  whether the `gh_` shaders may be reused before the next Workshop upload. This blocks publishing only.

## Architecture

One generator, `tools/build_map_graphics.py`, builds every output from the installed RiE (default
`C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/2291024373`, `--rie PATH` to override), Anbennar
(`../anbennar-ck3-dev-master`) and the game. One data file, `tools/data/map_graphics.py`, holds what is tuned: the
texture mapping, the drop-in list, the grading region table, the shader roots and exclusions. Rerun the generator
after an RiE update, an Anbennar update or a CK3 patch. Without RiE installed it stops with an error naming the
missing path and writes nothing.

The outputs are committed. `.gitattributes` sends `gfx/map/**/*.dds`, `*.mesh` and `gfx/map/post_effects/*.tga`
through Git LFS (git-lfs 3.3 is installed; the account has 10 GB storage and 10 GB transfer a month). The existing
`*.dds binary` rule stays for the monument, spell and invention art outside `gfx/map/`.

### Outputs

| Part | Output | Source and rule |
|---|---|---|
| Ground textures | `gfx/map/terrain/<name>_{diffuse,normal,properties}.dds` | RiE's own textures used by `TEXTURE_MAP`, copied byte for byte. |
| Drop-ins | `gfx/map/terrain/snow_diffuse.dds`, `snow_diffuse_for_combined_winter.dds`, `forest_pine_01_normal.dds`, `forest_pine_01_properties.dds` | RiE's versions of vanilla files (`DROP_INS`); same names, so every material using them changes. |
| Material list | `gfx/map/terrain/materials.settings` | Generated full-file override: Anbennar's file with the `diffuse`, `normal` and `material` lines of each mapped material replaced by the RiE material's three paths. Name, id, mask, order and `tile_factor` unchanged. Header and changed lines marked `# Anbennar Overhaul`. |
| Lighting | `gfx/map/environment/environment.txt` | RiE's, copied. |
| Skybox | `gfx/map/environment/skybox.dds`, `gfx/models/mapitems/SKYX_skybox.mesh`, `gfx/models/mapitems/SKYX_skybox.asset`, `gfx/map/map_object_data/SKYX_skybox.txt` | RiE's; the placement's transform is rewritten for Anbennar's map (below). |
| Snow | `gfx/map/environment/snow.settings`, `gfx/map/environment/gh_snow_layer_1.dds` | RiE's, copied. |
| Colour grading | `gfx/map/post_effects/colorcorrection_*.{tga,dds}`, `gfx/map/post_effects/posteffect_volumes.txt` | Colour tables copied. The volumes file is generated: RiE's `posteffect_values` blocks and height volumes verbatim, then one box volume per kingdom of `GRADING` (below). RiE's Middle-earth boxes are dropped. |
| Water | `gfx/map/water/water.settings` | RiE's settings. Anbennar's flow map, foam map and water colour stay. |
| Fog of war | `gfx/map/fog_of_war/cloud.dds` | RiE's tiling 4096×4096 cloud texture. |
| Shaders | `gfx/FX/...` | RiE's map shaders and every RiE file they include (below). |
| Credit | `credits.txt` | RiE (with Workshop link, as their terms ask), Godherja (the `gh_` shaders), Victoria 3 (the fog of war is based on its shader). Hand-written. |

## Ground textures

`TEXTURE_MAP` maps an Anbennar material id to an RiE material id; the RiE material's `diffuse`, `normal` and
`material` paths are read from RiE's `materials.settings`, and those files (when they are RiE's own, not vanilla's)
are copied. Initial mapping, tuned in game:

| Anbennar id | RiE id |
|---|---|
| `mountain_02`, `mountain_02_b`, `mountain_02_c`, `mountain_03` | `realms_mountains_01`, `realms_mountains_02`, `mountains`, `realms_mountains_02` |
| `mountain_02_d` | `mountain_01_vertical` |
| `mountain_02_d_valleys` | `rock_european` |
| `mountain_02_snow`, `mountain_02_c_snow`, `mountain_02_d_snow` | `mountains_white`, `mountains_white`, `mountain_white_vertical` |
| `mountain_02_desert_c` | `mountains_desert` |
| `hills_01_rocks`, `hills_01_rocks_small`, `hills_01_rocks_medi` | `boulders_grassy_01`, `boulders_grassy_02`, `boulders_european` |
| `steppe_rocks`, `desert_rocky` | `rock_sandstone`, `rock_desert` |
| `coastline_cliff_grey`, `coastline_cliff_desert` | `rock_european`, `rock_sandstone` |
| `gen_central_mountain`, `central_mountain`, `gen_steppe_mountain`, `gen_tropical_mountain`, `gen_mediterranean_mountain`, `gen_northern_mountain`, `gen_desert_mountain`, `gen_drylands_mountain` | `realms_mountains_01`, `realms_mountains_01`, `realms_mountains_01`, `realms_mountains_02`, `mountains`, `mountains_white`, `mountains_desert`, `rock_redstone` |
| `gen_central_mountain_transition`, `gen_mediterranean_mountain_transition`, `gen_northern_mountain_transition`, `gen_desert_mountain_transition`, `gen_drylands_mountain_transition`, `gen_steppe_mountain_transition`, `gen_tropical_mountain_transition` | `rock_european`, `boulders_european`, `rock_white`, `rock_desert`, `rock_sandstone`, `rock_sandstone`, `boulders_grassy_02` |

RiE textures left unused for now: lava, hardened lava, salt flats, moss, lichen, gravel, coral, birch, snowy pine,
white boulders, RiE's steppe grass.

Checks (the generator stops on any): every `TEXTURE_MAP` key is an Anbennar material id and every value an RiE
material id; every texture a mapped material names exists (in RiE or the game); every copied texture is 1024×1024
DXT5 like vanilla's set (a texture array needs one size and format); every `DROP_INS` name exists in the game.

## Colour grading

`GRADING` maps a title key to a grade. An empire entry covers its de jure kingdoms; a kingdom entry overrides its
empire's (grade `None` removes the kingdom's box), for tuning spread-out kingdoms such as `k_ginerdu`, whose box
spans much of the south. Each graded kingdom gets one `posteffect_volume` box:

| Region (all de jure kingdoms of) | Grade |
|---|---|
| `e_gerudia` | `boreal` |
| `e_salahad`, `e_kheterata` | `desert` |
| `e_bulwar`, `e_harpylen` | `arid` |

No box (map-wide `standard` grade): `e_middle_dwarovar`, `e_deepwoods`, `e_dragon_coast` and the Cannor empires.
RiE's other grades (`tropical`, `savannah`, `tundra`, `artic`, `volcanic`, `ocean`, `cold`, `hot`) are copied and
stay available.

Box measurement: each kingdom's provinces (the `province = N` lines of its baronies in Anbennar's landed titles)
are looked up in Anbennar's `gfx/map/map_object_data/building_locators.txt`, which gives one map position
`{ x 0 y }` per province (y counted from the bottom, the same convention as post-effect volumes). The box is the
bounding box of those points grown by `GRADING_MARGIN` (60) on every side, so it covers the provinces' area, not
only their centres: `position = { centre_x 400 centre_y }`, `size = { width 1600 height }` (400 and 1600 are RiE's
vertical values), `fade_distance = GRADING_FADE` (300). Each box carries `posteffect_values_day` and
`posteffect_values_night` set to the grade, as RiE's do. Volume names are the kingdom keys. A province without a
locator is skipped and a kingdom with no located province gets no box; the generator prints both (today
`k_obrtrol`'s 5 provinces have no locator and `k_the_reach` has no baronies). (The tools use the standard library only, so `provinces.png` is not decoded.)

## Lighting, skybox, snow, water, fog of war

- **Lighting:** RiE's `environment.txt`. Every file it names (e.g. its cubemap) must exist in the copied set,
  Anbennar or the game.
- **Skybox:** RiE places one mesh at `transform = "4104.55 1.74 2812.75 0 0 0 1 10000 1000 7000"` on its 8192×5632
  map. For Anbennar: position `(4096, 1.74, 2048)`, scale `(10000, 1000, 7000 × 4096 / 5632)` (≈ 5091), rotation
  unchanged. The asset and mesh are copied; the asset's shader `SKYX_sky` is in RiE's `pdxmesh.shader`.
- **Snow:** `snow.settings` and the snow layer texture; drawn by `gh_snowfall.fxh`. Its `"Texture_Index"` is the
  position of the snow material in the terrain texture array (54 in RiE's material list); the generator rewrites it
  to the 0-based position of the material with id `snow` in Anbennar's `materials.settings`.
- **Water:** `water.settings`; every texture it names must exist in Anbennar's `gfx/map/water/` or the game.
- **Fog of war:** `cloud.dds`, used by `gh_vic3_fog_of_war.fxh`.

## Shaders

`SHADER_ROOTS` (RiE `gfx/FX/` paths): `pdxterrain.shader`, `pdxwater.shader`, `pdxmesh.shader`,
`pdxmesh_decal.shader`, `tree.shader`, `river_surface.shader`, `pdxborder.shader`, `mapname.shader`,
`clouds.fxh`, `gh_atmospheric.fxh`, `jomini/map_lighting.fxh`, `jomini/jomini_province_overlays.fxh`.

The generator follows each copied file's `Includes`/`includes` blocks. An include is resolved in order: RiE's
`gfx/FX/` (copied), then Anbennar's `gfx/FX/`, then the game's `game/gfx/FX/`, `jomini/gfx/FX/` and
`clausewitz/gfx/FX/` (the engine's `jomini/` and `cw/` includes live in the last two). Files in
`SHADER_KEEP_ANBENNAR` (`bordercolor.fxh`, `gh_camera_utils.fxh`, `dynamic_masks.fxh`) are never copied from RiE
even when included; Anbennar's version is used. Never copied: `court_scene.shader`, `lotr_event_shaders.shader`,
anything under `jomini/` named `portrait*` or `texture_decals_base.fxh`, `gh_portrait_*`. The generator stops if a
root would pull one of these in, or if an include resolves nowhere.

Checked against RiE today, the closure is 16 RiE files: the 12 roots plus `gh_snowfall.fxh`, `gh_utils.fxh`,
`gh_vic3_fog_of_war.fxh` and `gh_vic3_fog_of_war_settings.fxh`; every other include resolves to Anbennar or the
game.

Texture references: every `File = "..."` path in a copied shader must exist in the copied set, Anbennar or the
game. A texture found only in RiE is copied (today: the skybox, the snow layer and the fog-of-war cloud); one that
Anbennar or the game has (e.g. `surround_mask.dds`, the environment cubemaps) is not.

`dynamic_masks.fxh`: `gh_snowfall.fxh` includes it, and Anbennar's version is heavily rewritten. A check lists the
functions and constants `gh_snowfall.fxh` uses that are defined in RiE's `dynamic_masks.fxh` and requires each to
be defined in Anbennar's version too; the generator stops otherwise.

## Testing

Tool tests (`tools/tests/test_build_map_graphics.py`), on small fixtures and, where RiE and Anbennar are installed,
on the real files:

- `TEXTURE_MAP` keys and values exist; the generated `materials.settings` equals Anbennar's except the header and
  the mapped materials' three texture lines; order and masks unchanged.
- Copied terrain textures are 1024×1024 DXT5; drop-ins match `DROP_INS`.
- Every `GRADING` kingdom exists; a box covers all its provinces' locators plus the margin (fixture);
  regions without a grade get no box; RiE's Middle-earth boxes are gone.
- Shader include closure resolves; excluded and Anbennar-kept files are not in the output; the
  `dynamic_masks.fxh` check passes on Anbennar's file and fails on a fixture missing a function.
- Every texture path named by copied shaders, `environment.txt`, `water.settings` and the skybox asset exists.
- The skybox transform for Anbennar's map size; `snow.settings` points at Anbennar's snow material.
- Generated files are fresh (skipped when RiE is not installed).

Validation: `python -I tools/validate.py` stays clean. Tiger does not check shaders.

In-game checklist (PR, unticked):

- [ ] The map renders: no black, pink or missing terrain; `error.log` has no shader compile errors.
- [ ] Mountains show RiE's rock (the Serpentspine, Gerudia's peaks, Salahad's desert mountains).
- [ ] Snowfall appears in winter; the snow textures look right.
- [ ] Fog of war shows the new clouds over unexplored land.
- [ ] Tilting the camera shows the skybox at the horizon.
- [ ] Salahad, Kheterata, Bulwar, Harpylen and Gerudia get their grades, with soft edges and no hard box outlines.
- [ ] Water looks right along Anbennar's coasts.
- [ ] Performance is about the same as before (FPS on the full map).

## Risks

1. **CK3 patches:** RiE's shaders replace vanilla files and can break after a patch until RiE updates; then rerun
   the generator and test. Added to CLAUDE.md's "After a CK3 patch" steps.
2. **Shader compile failure** can leave the map black. The include, texture and `dynamic_masks` checks catch the
   likely causes; only a game launch proves it.
3. **Rectangular tint boxes** spill across borders; fade and the region table are tunable.
4. **Permission** for the `gh_` shaders is unresolved until RiE and Godherja reply; it blocks publishing only.

## Docs

CLAUDE.md: a generated-files row for `tools/build_map_graphics.py`, a "Map graphics" systems entry, the generator in
the command table, and the rerun in "Updating to a new Anbennar version" and "After a CK3 patch".
