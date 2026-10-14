"""Tuned data for tools/build_map_graphics.py (map graphics ported from Realms in Exile).

Edit the values here, then rerun the generator. Spec: docs/superpowers/specs/2026-10-13-map-graphics-design.md.
"""

# Anbennar material id -> RiE material id. The RiE material's diffuse, normal and material paths replace the
# Anbennar material's; RiE-own files are copied. Tuned in game.
_GROUPS = [
    (("mountain_02", "mountain_02_b", "mountain_02_c", "mountain_03"),
     ("realms_mountains_01", "realms_mountains_02", "mountains", "realms_mountains_02")),
    (("mountain_02_d",), ("mountain_01_vertical",)),
    (("mountain_02_d_valleys",), ("rock_european",)),
    (("mountain_02_snow", "mountain_02_c_snow", "mountain_02_d_snow"),
     ("mountains_white", "mountains_white", "mountain_white_vertical")),
    (("mountain_02_desert_c",), ("mountains_desert",)),
    (("hills_01_rocks", "hills_01_rocks_small", "hills_01_rocks_medi"),
     ("boulders_grassy_01", "boulders_grassy_02", "boulders_european")),
    (("steppe_rocks", "desert_rocky"), ("rock_sandstone", "rock_desert")),
    (("coastline_cliff_grey", "coastline_cliff_desert"), ("rock_european", "rock_sandstone")),
    (("gen_central_mountain", "central_mountain", "gen_steppe_mountain", "gen_tropical_mountain",
      "gen_mediterranean_mountain", "gen_northern_mountain", "gen_desert_mountain", "gen_drylands_mountain"),
     ("realms_mountains_01", "realms_mountains_01", "realms_mountains_01", "realms_mountains_02",
      "mountains", "mountains_white", "mountains_desert", "rock_redstone")),
    (("gen_central_mountain_transition", "gen_mediterranean_mountain_transition",
      "gen_northern_mountain_transition", "gen_desert_mountain_transition", "gen_drylands_mountain_transition",
      "gen_steppe_mountain_transition", "gen_tropical_mountain_transition"),
     ("rock_european", "boulders_european", "rock_white", "rock_desert", "rock_sandstone", "rock_sandstone",
      "boulders_grassy_02")),
]
TEXTURE_MAP = {}
for _keys, _values in _GROUPS:
    assert len(_keys) == len(_values)
    TEXTURE_MAP.update(zip(_keys, _values))

# RiE versions of vanilla terrain files, copied under the same name (every material using them changes).
# Only snow_diffuse_for_combined_winter.dds is not a texture-array member as far as checks go (RiE's copy is
# 256x128): see build_map_graphics.NOT_ARRAY_MEMBERS.
DROP_INS = (
    "snow_diffuse.dds",
    "snow_diffuse_for_combined_winter.dds",
    "forest_pine_01_normal.dds",
    "forest_pine_01_properties.dds",
)

# RiE files copied verbatim. The textures the shaders reference (skybox.dds, gh_snow_layer_1.dds, cloud.dds) are
# copied by build_shaders, so they are not listed here.
COPY_FILES = (
    "gfx/map/environment/environment.txt",
    "gfx/models/mapitems/SKYX_skybox.mesh",
    "gfx/models/mapitems/SKYX_skybox.asset",
    "gfx/map/water/water.settings",
)

# --- Colour grading and shaders -----------------------------------------------------------------------------

# Colour grading: title key -> grade (empire covers its de jure kingdoms; a kingdom entry overrides, None removes).
# Every de jure duchy of a graded kingdom gets its own box with that grade.
GRADING = {
    "e_gerudia": "boreal",
    "e_salahad": "desert",
    "e_kheterata": "desert",
    "e_bulwar": "arid",
    "e_harpylen": "arid",
}
GRADING_MARGIN = 60
GRADING_FADE = 300  # the largest fade distance; a box's fade is also capped at GRADING_FADE_SHARE of its short side
GRADING_FADE_SHARE = 0.25
GRADING_OVERLAP_NOTE = 0.25  # boxes of different grades overlapping more than this share of the smaller are noted

# Provinces whose building locator is left out of the box measurement: province id -> reason.
GRADING_SKIP_PROVINCES = {
    6536: "b_obadel's building locator sits far from the rest of k_ginerdu",
}

# Shaders (RiE gfx/FX/ paths).
SHADER_ROOTS = (
    "pdxterrain.shader", "pdxwater.shader", "pdxmesh.shader", "pdxmesh_decal.shader", "tree.shader",
    "river_surface.shader", "pdxborder.shader", "mapname.shader", "clouds.fxh", "gh_atmospheric.fxh",
    "jomini/map_lighting.fxh", "jomini/jomini_province_overlays.fxh",
)
SHADER_KEEP_ANBENNAR = ("bordercolor.fxh", "gh_camera_utils.fxh", "dynamic_masks.fxh")
# RiE shader files that must never be pulled in (portrait and court scene code the map does not need); fnmatch
# patterns on the path relative to gfx/FX.
SHADER_NEVER = (
    "court_scene.shader", "lotr_event_shaders.shader", "jomini/portrait*", "jomini/texture_decals_base.fxh",
    "gh_portrait_*",
)

# Raised dwarven mountains (spec addendum 2026-10-13).
DWARVEN_TERRAINS = ("dwarven_hold_surface", "dwarven_hold", "cavern", "dwarven_road")  # province terrains that form ranges
GATE_EXCLUDE_REGIONS = ("e_dragon_coast", "e_harpylen")  # empires whose gate sites are left out
LIFT_PEAK = 50000  # height a range's highest point is lifted to
LIFT_MAX = 1.8  # largest lift factor on any pixel
LIFT_GROUND_RING = 24  # pixels around a range whose median height is the range's ground
SOFT_CEILING = 60000  # heights above this are compressed so they never clip at 65535
FADE_PX = 12  # pixels over which a lift fades at a range edge
GATE_MIN_SPACING = 16  # gate sites closer than this (map units) are merged, keeping the longer border
GATE_INSET = 2.0  # units a gate is moved along `inward` (into the mountain) from its site, so it sits in the slope
GATE_SCALE = 1.6  # scale of the gate mesh
# Per-gate tweaks, keyed by (dwarven county, normal county) ("sea" for a sea gate); a key that matches no gate stops
# the generator. Optional keys: scale, yaw (radians added), inset (replaces GATE_INSET), dx, dy (map units).
GATE_OVERRIDES = {}
# Hold counties whose land gate sites are replaced by one gate on the shore of the hold's province, facing the sea.
SEA_GATES = ("c_ovdal_tungr",)
GATE_YAW_OFFSET = 0.0  # extra yaw (radians) added to the gate mesh facing
# Gate massif: the ground around and behind each gate is raised until the mountain reaches the top of the gate model,
# so the gate looks carved out of the mountain. Measured from the gate position along its `inward` axis (t, px; the
# gate faces -t, the mountain is at +t) and sideways from that axis (l, px).
GATE_MODEL_HEIGHT = 11.59  # height of erebor_gate.mesh in mesh units (its bounding box)
GATE_MODEL_HALF_WIDTH = 3.92  # half the mesh's width, mesh units
GATE_MODEL_DEPTH = 3.25  # how far the mesh reaches behind its origin, mesh units
# Height units per world unit: RiE's Erebor gate (scale 0.704, 8.16 units tall) stands against a 14,345 rise.
HEIGHT_UNITS_PER_WORLD_UNIT = 1760  # measured from RiE's Erebor; tune in game
MASSIF_TOP_FACTOR = 1.0  # the massif top is foot + model height * scale * units per world unit * this
MASSIF_CORE_DEPTH = 8  # px behind the gate position that are raised to the top (the scaled slab is about 5.2 deep)
MASSIF_CORE_HALF_WIDTH = 8  # px either side of the axis that are raised to the top (the slab is about 6.3 wide)
MASSIF_FALLOFF = 20  # px (distance from the core rectangle) over which the massif eases from the top to nothing
MASSIF_EDGE_FADE = 8  # px from a pixel that may not change (normal land, water, no province) over which it eases out
MASSIF_STEP_LIMIT = 8000  # largest adjacent-pixel step allowed inside a massif beyond what the ground already had
PACK_TOLERANCE = 257  # largest height error allowed when repacking the heightmap

# Terrain blend-map gaps: Anbennar's detail_intensity.tga has pixels with no material (drawn black). Gaps smaller
# than TERRAIN_FILL_LARGE pixels copy a painted neighbour; larger ones get TERRAIN_FILL_MATERIAL at full weight.
TERRAIN_FILL_MATERIAL = "mountain_02"  # Anbennar material id; draws RiE's Mountains 01 rock through TEXTURE_MAP
TERRAIN_FILL_LARGE = 1000
