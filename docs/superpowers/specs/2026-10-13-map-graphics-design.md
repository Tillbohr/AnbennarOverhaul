# Map graphics from Realms in Exile — design

Date: 2026-10-13. Status: approved in conversation, awaiting written-spec review.

## Goal

Make Anbennar's map look closer to *Lord of the Rings: Realms in Exile* (RiE, Workshop 2291024373): its ground
textures on mountains and rocks, its lighting, colour grading, skybox, snowfall, fog of war and water settings, and
the map shaders that draw them. Everything ships inside this Overhaul; players need only Anbennar and the Overhaul.

Out of scope: army unit models (the user will give instructions later), RiE's height data, texture placement maps,
colour map, object placement and water textures (all drawn for Middle-earth's shape), the surround map, court-scene
and portrait shaders. (Anbennar's own height data is raised around the dwarven mountains: see the addendum
"Raised dwarven mountains and gates" at the end.)

## Decisions (from the conversation)

- Lives in this Overhaul, not a separate submod or repo.
- Ground textures: remap Anbennar's mountain, rock, hill and snow materials to RiE textures, plus RiE's same-name
  replacements for vanilla's snow and pine-forest textures. Lowlands stay vanilla.
- Colour grading by Anbennar region, one box per de jure duchy; the Middle Dwarovar gets no grade for now (a milder
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
| Colour grading | `gfx/map/post_effects/colorcorrection_*.{tga,dds}`, `gfx/map/post_effects/posteffect_volumes.txt` | Colour tables copied. The volumes file is generated: RiE's `posteffect_values` blocks and height volumes verbatim, then one box volume per de jure duchy of each graded kingdom of `GRADING` (below). RiE's Middle-earth boxes are dropped. |
| Camera tilt | `common/defines/graphic/aov_map_graphics_defines.txt` | Generated: an `NCamera` block holding only RiE's `ZOOM_STEPS_MIN_TILT` line (RiE lowers the first steps to `12 14 14 14`, vanilla and Anbennar have `40 41 43 44`), read from RiE's `common/defines/graphic/00_graphics.txt`; the generator stops if the line is missing. It lets the camera tilt up to the horizon, which is what shows the skybox. |
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
empire's (grade `None` removes the kingdom's box), for tuning. Every de jure duchy of a graded kingdom (the `d_` blocks directly inside the kingdom's block)
gets one `posteffect_volume` box with the kingdom's grade. Per-duchy boxes hug the land: a per-kingdom box for a
spread-out kingdom such as `k_ginerdu` covered most of its neighbours' differently graded boxes.

| Region (all de jure kingdoms of) | Grade |
|---|---|
| `e_gerudia` | `boreal` |
| `e_salahad`, `e_kheterata` | `desert` |
| `e_bulwar`, `e_harpylen` | `arid` |

No box (map-wide `standard` grade): `e_middle_dwarovar`, `e_deepwoods`, `e_dragon_coast` and the Cannor empires.
RiE's other grades (`tropical`, `savannah`, `tundra`, `artic`, `volcanic`, `ocean`, `cold`, `hot`) are copied and
stay available.

Box measurement: each duchy's provinces (the `province = N` lines of its baronies in Anbennar's landed titles)
are looked up in Anbennar's `gfx/map/map_object_data/building_locators.txt`, which gives one map position
`{ x 0 y }` per province (y counted from the bottom, the same convention as post-effect volumes). The box is the
bounding box of those points grown by `GRADING_MARGIN` (60) on every side, so it covers the provinces' area, not
only their centres: `position = { centre_x 400 centre_y }`, `size = { width 1600 height }` (400 and 1600 are RiE's
vertical values), `fade_distance = min(GRADING_FADE, GRADING_FADE_SHARE x the box's short side)` (300 and 0.25; a fixed 300 exceeded many duchy boxes). Numbers are written with one decimal. Each box carries `posteffect_values_day` and
`posteffect_values_night` set to the grade, as RiE's do. Volume names are the duchy keys. `GRADING_SKIP_PROVINCES` (province id to reason) leaves stray locators out of
the measurement (today b_obadel, province 6536, whose locator sits far from the rest of `k_ginerdu`). A province
without a locator is skipped and a duchy with no located province gets no box; the generator prints both (today
only `k_the_reach`, which has no duchies; `k_obrtrol` is commented out in Anbennar's landed titles, so it is not a
kingdom).

Overlaps: after measuring, every pair of boxes with different grades that overlap by more than
`GRADING_OVERLAP_NOTE` (0.25) of the smaller box's area is printed as a note (not an error). Today 9 pairs are noted;
three overlap by more than half (`d_ardu` / `d_hasr` 85%, `d_masusopot` / `d_sad_sur` 76%, `d_ardu` /
`d_eduz_vacyn` 67%, all desert Salahad boxes against arid Bulwar ones) and are left for in-game tuning: the margin,
`GRADING_SKIP_PROVINCES` or a kingdom override can resolve them. (The tools use the standard library only, so `provinces.png` is not decoded.)

## Lighting, skybox, snow, water, fog of war

- **Lighting:** RiE's `environment.txt`. Every file it names (e.g. its cubemap) must exist in the copied set,
  Anbennar or the game.
- **Skybox:** RiE places one mesh at `transform = "4104.55 1.74 2812.75 0 0 0 1 10000 1000 7000"` on its 8192×5632
  map. For Anbennar: position `(4096, 1.74, 2048)`; scale (`10000, 1000, 7000`) and rotation unchanged (the depth
  scale stays RiE's 7000 rather than shrinking with the map height). The asset and mesh are copied; the asset's shader `SKYX_sky` is in RiE's `pdxmesh.shader`. The skybox only shows when the camera can tilt to the horizon, so
  the generator also writes `aov_map_graphics_defines.txt` with RiE's lowered `ZOOM_STEPS_MIN_TILT` (see Outputs).
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

`dynamic_masks.fxh`: `gh_snowfall.fxh` includes it. Anbennar's `dynamic_masks.fxh` and `bordercolor.fxh` equal
vanilla's apart from line endings, so the check below guards future Anbennar edits. A check lists the
functions and constants `gh_snowfall.fxh` uses that are defined in RiE's `dynamic_masks.fxh` and requires each to
be defined in Anbennar's version too; the generator stops otherwise.

## Testing

Tool tests (`tools/tests/test_build_map_graphics.py`), on small fixtures and, where RiE and Anbennar are installed,
on the real files:

- `TEXTURE_MAP` keys and values exist; the generated `materials.settings` equals Anbennar's except the header and
  the mapped materials' three texture lines; order and masks unchanged.
- Copied terrain textures are 1024×1024 DXT5; drop-ins match `DROP_INS`.
- Every `GRADING` kingdom exists; one box per de jure duchy covers all its provinces' locators plus the margin
  (fixture); `GRADING_SKIP_PROVINCES` is honoured; fade follows the box size; different-grade overlaps are noted;
  numbers have one decimal; regions without a grade get no box; RiE's Middle-earth boxes are gone.
- The defines file carries RiE's `ZOOM_STEPS_MIN_TILT` line and the generator stops when it is missing.
- Shader include closure resolves; excluded and Anbennar-kept files are not in the output; the
  `dynamic_masks.fxh` check passes on Anbennar's file and fails on a fixture missing a function.
- Every texture path named by copied shaders, `environment.txt`, `water.settings` and the skybox asset exists.
- The skybox transform for Anbennar's map size (RiE's scales kept); `snow.settings` points at Anbennar's snow material.
- Generated files are fresh (skipped when RiE is not installed).

Validation: `python -I tools/validate.py` stays clean. Tiger does not check shaders.

In-game checklist (PR, unticked):

- [ ] The map renders: no black, pink or missing terrain; `error.log` has no shader compile errors.
- [ ] Mountains show RiE's rock (the Serpentspine, Gerudia's peaks, Salahad's desert mountains).
- [ ] Snowfall appears in winter; the snow textures look right.
- [ ] Fog of war shows the new clouds over unexplored land.
- [ ] At close zoom the camera tilts to the horizon and shows the skybox.
- [ ] Frost and snow do not reach Bulwar or Salahad (`snow.settings` hemisphere values were tuned for Middle-earth's taller map).
- [ ] The area past the map edges looks right (RiE's water shader makes everything outside the map water).
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

## Addendum (2026-10-13): Raised dwarven mountains and gates

Approved in conversation after a probe of Anbennar's packed height format. Same generator, same PR.

### Goal

Raise every dwarven mountain to about Erebor's height in RiE, and place RiE's Erebor gate where dwarven mountains meet
normal terrain, so the gates read as entrances into the mountain.

### Definitions

- **Dwarven province:** province terrain (`common/province_terrain/00_province_terrain.txt`) `dwarven_hold_surface`,
  `dwarven_hold`, `cavern` or `dwarven_road` (119 provinces today: 46 caverns, 36 roads, 22 surface holds, 15 holds).
- **Range:** a connected group of dwarven provinces (adjacent on `provinces.png`); 9 today (largest 52 and 31).
- **Normal land:** a province that is not dwarven, not water (`default.map` sea zones, lakes, river provinces), not
  impassable (`impassable_mountains`, `impassable_seas`) and not unassigned (id 0).
- **Gate site:** one per pair (dwarven county, normal-land county) whose provinces share a border on `provinces.png`,
  skipped when the dwarven province's empire is in `GATE_EXCLUDE_REGIONS = ("e_dragon_coast", "e_harpylen")`. At
  Rubyhold the sites are Redgate→Rewanfork (Lorent) and Rose Mines→Rivergate (Rivergate is normal terrain).

### Erebor reference (measured from RiE)

RiE's Erebor terrain rises from 22,102 at the gate to about 36,200 at the summit within 5–10 map units; its six
mountain models are only 0.5–1.6 units tall. The `erebor_gate_mesh` is 11.6 units tall (its own cliff backing),
placed at scale 0.7 (about 8 units). The towering look comes from that rise plus the gate's cliff, seen at RiE's low
camera tilt (already ported). Most of the Serpentspine already exceeds Erebor's terrain; Rubyhold (median 27,044, peak
40,982), Ovdal Tungr, Esmaria and the Harpylen cavern fall short.

### Raising rule (values in `tools/data/map_graphics.py`)

1. **Range lift:** for each range, `ground` = the median height of non-dwarven, non-water pixels within
   `LIFT_GROUND_RING` (24) pixels of the range. Factor `k = clamp((LIFT_PEAK - ground) / (peak - ground), 1,
   LIFT_MAX)` with `LIFT_PEAK = 50000` (Erebor's terrain summit, about 36,000, plus the height its gate model adds),
   `LIFT_MAX = 1.8` and `peak` the range's highest height (`k = 1` when `peak <= ground`). Every pixel of the range
   becomes `ground + (h - ground) * k` (never lower than `h`). Measured today: Rubyhold x1.37 (peak 40,982 -> 50,000),
   Esmaria, Ovdal Tungr, the Harpylen cavern (province 655) and province 912 x1.8 (Esmaria peak 27,866 -> 39,020, Ovdal
   Tungr 30,646 -> 37,316, Harpylen 45,316 -> 48,930), the Serpentspine, Dragon Coast and Khugdihr
   ranges x1.0 (already at or above the target, or ringed by higher ground); they are unchanged.
   (Decided after measurement: a 90th-percentile target of 36,000 would have raised Rubyhold only 3%.)
2. **Soft ceiling:** values above `SOFT_CEILING = 60000` are eased toward 65,535 (`60000 + (65535 - 60000) *
   (1 - exp(-(v - 60000) / (65535 - 60000)))`), never clipped.
3. **No gate pads, cliffs or skirts (redesign, see "Gate redesign" below):** the first version carved a flat pad and
   raised a 14,000 cliff at every gate site. In game that stretched the land into sheer, textured walls, so the
   constants `GATE_PAD`, `GATE_RISE`, `GATE_RISE_DIST` and `GATE_SKIRT` are gone and gate sites no longer change a
   single height of the ground in front of the gate (no carving). No pixel is ever lowered. A gentle shoulder behind
   each gate is added instead (rule 3b).
4. **Fade:** every change fades linearly to zero over `FADE_PX` (12) pixels outside the dwarven provinces; water and
   impassable provinces change only inside that fade.

### Pipeline

`build_heightmap(roots)` in `tools/build_map_graphics.py`, with a stdlib PNG reader/writer `tools/pngio.py`:

1. Read Anbennar's `map_data/heightmap.png` (16-bit grey, 8192×4096), `provinces.png`, `definition.csv`,
   `default.map`, province terrain, landed titles and its packed files.
2. Find dwarven provinces, ranges and gate sites; apply the raising rule.
3. **Repack** (format decoded by the probe): all three images run bottom-up (row 0 = south). The indirection image has
   one RGBA pixel per 32×32 block (256×128): tile column, tile row, step (1/2/4/8/16), level (0–4). A block's tile is
   `32 / step + 1` pixels square, sampled every `step` pixels from the heightmap (the extra pixel is the shared edge),
   stored in the packed image at `(column × size, level_offset_y + row × size)`. Levels occupy separate row bands whose
   starts are `level_offsets` in `heightmap.heightmap`; tile columns per level are `min(256, packed_width // size)`.
   Unchanged blocks keep Anbennar's level; a changed block gets the coarsest level whose sampled tile, interpolated
   back, matches the edited heights within `PACK_TOLERANCE` (257, one 8-bit grey step), else level 0. The
   `empty_tile_offset` tile is kept. `heightmap.heightmap` keeps every key except `level_offsets` (and
   `empty_tile_offset` if the empty tile moves).
4. Gates: one `erebor_gate_mesh` instance per site, moved `GATE_INSET` (2 units) along `inward` from the
   dwarven-side border pixel nearest the centroid of the pair's dwarven-side border pixels. The yaw is
   `atan2(inward_x, inward_y)` so the mesh's local +Z points along `inward`, into the mountain (as RiE's Erebor gate
   has the mountain behind it); its front faces the normal-land neighbour. Scale `GATE_SCALE` (1.6), yaw correction
   `GATE_YAW_OFFSET` (0; tuned in game), per-gate tweaks in `GATE_OVERRIDES`.

### Outputs

| Output | Notes |
|---|---|
| `map_data/heightmap.png`, `map_data/packed_heightmap.png`, `map_data/indirection_heightmap.png`, `map_data/heightmap.heightmap` | Whole-file overrides of Anbennar's; PNGs through Git LFS (~30 MB). |
| `gfx/map/map_object_data/aov_dwarven_gates.txt` | Generated header; one `object` with the gate instances; a map-object layer that Anbennar or vanilla defines. |
| `gfx/models/mapitems/aov_dwarven_gate/` (gate asset, mesh and textures; `aov_<piece>.asset`, `<piece>.mesh` for mountain_01..06 and rock_mesa_02 with the `mountains_mapobject_01_*` textures) | Copied from RiE (the `aov_` assets are rewritten), ~72 MB, mostly RiE's 4096² mountain textures. |
| `gfx/map/map_object_data/aov_dwarven_gate_overlays.txt` | The transplanted composition objects (item 5). |
| `gfx/FX/court_scene.shader` | Anbennar's file byte for byte plus RiE's placeholder map-object effects Anbennar lacks (see "Gate redesign"). |

The Rubyhold-only Erebor mountain cluster discussed earlier is dropped: the height data does that job.

### Gate redesign (2026-10-13, after the first in-game test)

In game the gates were too small, the pads and cliffs stretched the land into sheer textured walls, and the gate's
rock backing did not load. `error.log` said `Failed getting Effect [standard_winter_mapobject] in file
[gfx/FX/court_scene.shader] ... (requested by pdxmesh erebor_gate_mesh)` (also `standard_winter_selection_mapobject`)
and `Failed to create material with shader standard_colormap (in gfx/FX/court_scene.shader) for mesh [mountain]`.

1. **Court-scene placeholders.** CK3 looks the effects of map-object meshes up in `court_scene.shader`. RiE's own copy
   declares them as placeholders (`VertexShader = "VS_standard"`, `PixelShader = "PS_noop"`); Anbennar's lacks 19 of
   them (the build counts them). `build_court_scene` writes `gfx/FX/court_scene.shader` = Anbennar's file plus, after
   a `# Anbennar Overhaul` comment, every RiE effect whose body is exactly that pair and whose name Anbennar does not
   define, copied verbatim. RiE's file as a whole stays in `SHADER_NEVER` (its portrait and court code is not
   wanted). The build stops if Anbennar's file lacks `MainCode VS_standard` or `MainCode PS_noop`, or if
   `standard_winter_mapobject`, `standard_colormap` or `standard_colormap_mapobject` is still undefined.
2. **No carved terrain** (raising rule 3 above): the gate sits in the lifted slope instead. (A broad "shoulder" rise
   behind each gate was tried after the second in-game test and removed; its replacement is item 5, the Erebor
   transplant. The `SHOULDER_*` constants are gone.)
3. **Bigger gates set into the slope.** `GATE_SCALE = 1.6` (was 0.7), `GATE_INSET = 2.0` map units along `inward`,
   into the mountain. `GATE_OVERRIDES` is `{(dwarven county, normal county): {scale, yaw, inset, dx, dy}}` (yaw in
   radians added to the facing, dx and dy in map units); empty until in-game tuning needs it, and a key that matches no
   gate stops the build.
4. **Sea gates.** `SEA_GATES = ("c_ovdal_tungr",)`: Ovdal Tungr's gate should stand at the shore by the
   holding, facing the sea, so for each listed county the land sites are dropped and one sea site is made. The hold barony comes from
   `tools/data/holds.py` (`b_irovar`, province 526). Among that province's pixels that 4-touch a `sea_zones` pixel
   (lakes and rivers do not count) the one nearest the province's building locator is the site, and `inward` is the unit
   vector from the centroid of the touching sea pixels within 6 px to the site, so the gate faces the sea (its
   `normal_county` is `"sea"`, the key for overrides).
5. **Erebor transplant (2026-10-14, after the third in-game test).** Heightmap reshaping and stretched mountain pieces
   (three attempts) left the gates looking like slabs in front of the mountain. Measuring RiE's Erebor showed why:
   it is a small, specific composition and each of our attempts got one part wrong. The generator now extracts the
   composition from RiE at build time (`tools/gate_transplant.py`, `extract_composition`) and stamps a scaled, varied
   copy at every gate (all 12 incl. Ovdal Tungr's sea gate and Silverforge). The Moria comparison (`mesh` override,
   `GATE_MESH_BASE_SCALE`, Moria assets), the shoulder and the 3-crag layout (`GATE_OVERLAY_LAYOUT/OVERRIDES`) are gone.

   **Measured Erebor** (gate at (4334.83, 4747.21), scale 0.703864, yaw +11.6 degrees, local +Z = inward into the
   mountain; gate foot = the gate pixel's height, 22,102). Terrain delta D(t, l) = h - foot, with `t` along inward and
   `l` to the gate's right (`v = (inward_y, -inward_x)`), in RiE px, bilinear: along the axis t=0 -> ~0, t=2 -> +10.7k,
   t=4 -> +11.9k, t=6 -> +14.0k (peak, ~+14.0k by our sampling, ~+14.6k in the first measurement), t=10 -> +7.4k, t=14 ->
   +0.6k, t>=16 slightly below the foot; it falls off within ~8 px to the sides: a narrow steep cone that starts AT the
   gate face. Objects: every map object with a transform within `COMPOSITION_RADIUS` (16) map units of the gate except
   the gate, `rammas_echor_intact_mesh` and `ravenhill_mesh` (`COMPOSITION_EXCLUDE`): 10 mountain pieces (shader
   `snap_to_terrain_alpha_to_coverage_colormap`: vertex y = terrain height + mesh y x y-scale, a draped rock skin, not
   tall rock). (The first brief also listed 3 `rock_mesa_02` flank rocks. They are not rocks in RiE: its `env_effects.txt`
   lists those transforms in the `waterfall` effect-entity block, the Running River's source. The first transplant drew
   them as mesa rocks at k x scale; in game they were huge pale boulders on the lowland, so the substitutes, the
   `rock_mesa_02` asset and its textures are removed. Effect entities are never part of the composition.) The
   extracted pieces (t, l in RiE units, y offset, yaw relative to the gate, scale):

   | Mesh | t | l | y | yaw | scale |
   |---|---|---|---|---|---|
   | mountain_01 | 6.05 | 0.79 | 0 | 40.7 | 1.0 |
   | mountain_02 | 7.24 | 2.68 | 0 | -31.4 | 1.0 |
   | mountain_03 | 3.70 | -3.79 | 0 | 45.2 | 1.0 |
   | mountain_03 | 2.96 | -0.13 | 0 | 178.9 | 0.701 |
   | mountain_04 | -0.99 | -7.79 | 0 | 138.0 | 1.0 |
   | mountain_04 | 12.91 | -3.74 | 0 | 62.3 | 1.0 |
   | mountain_05 | 0.44 | 7.40 | 0 | 7.3 | 1.0 |
   | mountain_05 | 6.38 | -9.69 | 0 | -13.3 | 1.0 |
   | mountain_05 | 6.90 | 10.22 | 0 | -10.7 | 0.628 |
   | mountain_06 | 13.36 | 5.27 | 0 | -101.1 | 1.0 |

   **Transplant at a gate.** Scale `k = gate size / EREBOR_GATE_SCALE (0.703864)` (gate 1.6 -> k = 2.273); frame = the
   final gate position `P` (`dm.gate_position`, shared with the gate mesh) and `inward` axis `u`; the composition does not
   follow `GATE_YAW_OFFSET` or a gate yaw override. A point (t, l) is `P + k (t u + l v)`.
   - *Cone (second in-game test: the first stamp `max(cur, foot + k D f w)` lifted every low pixel of the patch to the
     foot, giving blocky plateaus in front of the gates and canyon walls at rivers):* the cone only blends up from the
     ground. At each pixel `p` within `k * TRANSPLANT_RADIUS (18)` of `P` (not water, not province 0) `(t, l)` is looked up in
     the Erebor delta `D(t / k, l' / k)` (l' = -l when mirrored). Cone weight `c` = smoothstep of `D` between
     `TRANSPLANT_CONE_MIN` (0.15) and `TRANSPLANT_CONE_FULL` (0.40) of the extracted peak x a face weight (0 for t < 0, a
     cosine up to 1 at t = `TRANSPLANT_FACE_RAMP` (1) RiE px) x the radius fade (cosine to 0 over the last
     `TRANSPLANT_FADE` (4) RiE px) x a water fade `min(1, d / TRANSPLANT_WATER_FADE (6))`, `d` the distance in map px to the
     nearest water or province-0 pixel. The pixel becomes `max(cur, round(cur + c (soft_ceiling(foot + k D f) - cur)))`,
     `f` the height factor, `foot` the height at `P` after the range lift. Pixels in front of the face, outside the cone
     (D < 0.15 peak), on water or on province 0 never change, and nothing is lowered. Gates apply in key order, each
     blending from what the previous left (no gates overlap since Old Passage's three were removed).
   - *Pieces:* each composition mountain piece becomes at most one instance per gate: position `P + k (t' u' + l' v')`,
     yaw = the composition's yaw + turn + the relative yaw (negated when mirrored) + jitter, uniform scale `k s` x jitter,
     ground offset y = the RiE offset x k. A piece is kept only if its centre (RiE units, after mirror, turn and jitter)
     has t >= 0 and cone weight `c` (shape, without the water fade) >= `TRANSPLANT_PIECE_MIN_WEIGHT` (0.3), and does not
     fall on water, province 0 or off the map. Of Erebor's 10 pieces, mountain_01, 02, 03 (both) and 06 survive; the two
     mountain_04 (one at t < 0) and three mountain_05 (beside the narrow cone) are dropped at every gate. One `object`
     per mesh type in `aov_dwarven_gate_overlays.txt`, layer `temp_layer`, meshes `aov_mountain_0N_mesh` (assets
     `aov_<piece>.asset`: only the pdxmesh and entity names gain the prefix; mesh and textures copied beside them; pieces
     that never survive are not copied). `build_all` stops if a shader named by a copied gate-folder asset lacks its
     `<shader>_mapobject` effect in the generated `court_scene.shader`.

   **Per-site variation** (deterministic; seed = first 8 bytes of SHA-256 of `"<dwarven county>/<normal county>"`; all
   bounds `TRANSPLANT_*` in `tools/data/map_graphics.py`; `TRANSPLANT_OVERRIDES[(dwarven, normal)]` pins `mirror`,
   `turn` (degrees) and `height`, and an unknown key stops the build):
   - *Mirror* left/right (l -> -l, relative yaws negated) with probability 0.5.
   - *Turn toward uphill:* the mean height gradient of the lifted terrain over pixels with 4 <= t <= 30 px and |l| <= 20
     px gives the uphill direction; the composition's axis (cone and objects, not the gate's own facing) rotates toward
     it by at most `TRANSPLANT_MAX_TURN` (25 degrees).
   - *Height factor* `f`: 1.0, raised so the cone's peak `foot + k * peak * f` clears the highest lifted terrain in the
     cone's footprint by `TRANSPLANT_PEAK_MARGIN` (2,000), clamped to [0.85, 1.25], then +-0.05 seeded jitter inside
     the clamp. Where the terrain is far above the foot the clamp wins, and the soft ceiling bounds the result.
   - *Object jitter:* position +-0.6 RiE units, yaw +-15 degrees, scale x 0.9 to 1.1.
   - *Drop* pieces as above. The random draws per piece are fixed, so dropping one never shifts the others.
   Each gate gets a build note: mirrored, turn, `f`, cone peak (foot, rise) and pieces kept/dropped (named).

6. **Transplant polish (2026-10-15, after the third in-game test: "much better").** Feedback: the Erebor peaks sloped
   down to the Serpentspine behind them, and some gates floated or were covered by pieces. After the cones, per gate in
   key order (each reading what the previous left):
   - *Range joins the cone peak.* Region = pixels at t >= 0 in the composition's (turned) frame within
     `RANGE_JOIN_RADIUS` (60) px of `P`, dwarven or impassable, not water or province 0, with own cone weight below
     `RANGE_JOIN_CORE` (0.4). `g` = the gate's foot, `peak` = the gate's cone peak (soft-ceilinged). A region pixel with
     `cur > g` becomes `max(cur, soft_ceiling(g + (cur - g)(1 + (s - 1) w)))`, `w` = 1 within `RANGE_JOIN_FULL` (30) px
     and a cosine fade to 0 at the radius, times the water fade. The scale `s` is clamped to [1, `RANGE_JOIN_MAX` (2)];
     the brief's `(peak - g) / (m - g)` for the region maximum `m` is exact when `m` stands within the full-weight
     radius, but a maximum in the fade (or beside water) would leave the range near the gate short, so `s` is solved
     (bisection) as the smallest scale with which the highest *scaled* pixel reaches the peak. Ridges keep their shape
     (their relative profile is multiplied, not flattened), nothing is lowered, the cone core is untouched.
   - *No floating gate.* In the gate's own frame (the gate's facing, not the composition's turn), pixels with
     `t` in [-`GATE_APRON` (4) x size / 1.6, `GATE_MODEL_DEPTH` (3.25) x size] and `|l|` <= `GATE_MODEL_HALF_WIDTH`
     (3.92) x size + 1 are raised to at least the foot, with a cosine blend over `GATE_APRON_FADE` (3) px outside the
     rectangle; land only (Ovdal Tungr's sea front stays water); never lowered.
   - *Pieces never cover the gate.* A piece's footprint is its mesh's bounding box (the `min`/`max` float3 properties
     of the pdxmesh, times the asset's scale 1.5, times the instance's scale), rotated by its yaw. The gate's keep-out
     is only the zone in front of and at the face (gate frame): t from -`GATE_APRON` x size / 1.6 to `PIECE_FACE_CLEARANCE` (1) px
     behind the face, |l| <= `GATE_MODEL_HALF_WIDTH` x size + `PIECE_KEEP_OUT_MARGIN` (2); pieces draping over the cone
     and the gate's body behind the face are allowed (a first, whole-footprint keep-out left only 1-2 pieces per gate
     and was too conservative). The piece's footprint is an oriented box (the bounding box corners rotated into the map).
     An overlapping piece moves back
     along the cone axis in 0.5 px steps by at most `PIECE_MAX_PUSH` (12) px, is filtered again at the new position
     (t >= 0, cone weight >= 0.3, land), else is dropped.
   The build note per gate adds: range join (m before -> after, s), apron pixels raised, pushed pieces by name.
   Measured (9 gates; Old Passage's three removed by `GATE_EXCLUDE_COUNTIES`): the range joins its cone's peak at every gate whose range stood lower; see the build notes for the pieces kept, pushed and dropped per gate.

### Testing

- `pngio` round-trips 8-bit RGB/RGBA and 16-bit grey.
- Repacking Anbennar's unchanged heightmap reproduces every tile's heights; level bands don't overlap; tiles stay in
  their band; `heightmap.heightmap` keeps every other key; every changed block decodes back within `PACK_TOLERANCE`.
- Raising: each range's peak ≥ 50,000, or its factor is at `LIFT_MAX`, or it was 1 (peak already ≥ 50,000 or ≤ ground); no height lowered anywhere; nothing over
  65,535; changes fade to zero within `FADE_PX` (gate sites included); water/impassable change only inside the fade.
- Transplant: the extraction yields the 10 pieces within tolerance (Rammas Echor, Ravenhill and the gate excluded);
  frame maths for north- and east-facing fixtures and mirroring; cone peak position, never lowered, water untouched,
  nothing changes in front of the face or outside the cone on ground lower than the foot, no canyon walls at a river,
  the piece filter, fade at the radius, overlap order-independence; seeded variation (determinism, uphill turn bounded by 25 degrees,
  height clamp, dropping on water); real build: 9 gates, 10 x 9 pieces minus the dropped, each cone peak at least
  `soft_ceiling(foot + 0.8 k peak)`, no changed pixel in front of any face, steps outside the cone core below 11,000
  (the face wall, t < 1.5 RiE units, is steep by design); polish: the join (a lower ridge rises to the cone peak with its
  profile scaled, cone and front untouched, water untouched, fade to zero at the radius, s clamp, key order), the apron
  (front raised to the foot on a slope, never lowered, water untouched, gate frame), piece push/drop/re-filter,
  `mesh_bounds` on a real RiE mesh; real build: every range's highest point after at least
  `min(peak - 2000, foot + 2 (m - foot))`, no pixel lowered, every footprint pixel at or above its foot, no piece
  overlaps its gate's keep-out; steps outside the core below 13,000 (the join scales ridges up to 2x).
- Gates: count equals the sites minus Dragon Coast and Harpylen; each sits inside its dwarven province and faces its
  neighbour; Rubyhold's two sites are as above; overrides apply and an unknown key stops the build; Ovdal Tungr's gate
  is a sea site (see below).
- Copied mesh/textures exist and every texture the asset names resolves; the freshness test covers the new outputs.

In-game checklist additions:

- [ ] The map loads with no holes, spikes or seams at 32-pixel block edges.
- [ ] Rubyhold, Ovdal Tungr and Esmaria stand clearly taller; the Serpentspine still looks right.
- [ ] Edges fade smoothly into nearby land, water and impassable mountains.
- [ ] Gates look built into the rock at their sites, face the normal land (Redgate, Rose Mines, the Serpentspine
  sites), and their rock backing shows.
- [ ] Rivers, borders, holdings and county names over raised terrain look right.
- [ ] Ovdal Tungr's gate stands at the shore by the holding, facing the sea; no river clips a gate.
- [ ] No stretched walls remain at former gate sites.
- [ ] Each gate stands at the foot of a steep cone with the mountain pieces draped over its slopes (rock, not stretched
  ground); no plateau on the lowland before the gate, no canyon walls where rivers cross a cone; none float, are buried or face wrongly; error.log has no "Failed getting
  Effect" or texture errors for the new meshes.
- [ ] The range behind each cone rises to the cone's peak (no downward slope from the Erebor peaks to the Serpentspine); the cone itself is not squished.
- [ ] No gate floats or overhangs lower ground; no mountain piece covers a gate.
- [ ] Mirrored and unmirrored gates both look right; the turn toward the uphill side follows the ridge; tall ranges
  (Marrhold, Outer Khug's Cave) still show a cone rising out of the slope.
- [ ] Old Passage has no gates and no cones; Ovdal Tungr's sea gate keeps its objects on land.

### Risks

1. **The game may reject our packed layout** (tile placement and level choice differ from Paradox's packer). The first
   build is checked in game before tuning; fallback: rebuild the packed files with CK3's map editor by hand.
2. **Anbennar map updates** must be followed by a rerun (the files are whole-file overrides); CLAUDE.md's update steps
   say so.
3. **Steep cliffs may stretch textures**; RiE's vertical rock textures help.
4. About 100 MB more LFS (~72 MB gate asset and textures, ~27 MB height files).

### Old Passage removed (2026-10-15)

At the user's request `GATE_EXCLUDE_COUNTIES = ("c_oldpassage",)` drops every gate site of that county (its three
sites overlapped into the steepest cluster); the generator stops if a listed county has no site. 9 gates remain.
