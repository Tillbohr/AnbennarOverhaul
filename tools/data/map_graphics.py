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
# the generator. Optional keys: scale, yaw (radians added to the gate mesh), inset (replaces GATE_INSET), dx, dy (map
# units). The transplant composition below follows the gate's position and scale, not its yaw.
GATE_OVERRIDES = {}
# Hold counties whose land gate sites are replaced by one gate on the shore of the hold's province, facing the sea.
SEA_GATES = ("c_ovdal_tungr",)
GATE_YAW_OFFSET = 0.0  # extra yaw (radians) added to the gate mesh facing

# Erebor transplant: Realms in Exile's Erebor gate sits in a small composition (a steep terrain cone starting at the
# gate face, ten draped mountain-piece skins and three mesa rocks). The generator extracts it from RiE's map data and
# stamps a scaled copy at every gate, varied per site so each conforms to its terrain (spec addendum 2026-10-14).
EREBOR_GATE_SCALE = 0.703864  # scale of RiE's Erebor gate mesh; a gate's size / this = the transplant scale k
EREBOR_GATE_MESH = "erebor_gate_mesh"
# Objects within COMPOSITION_RADIUS RiE map units of the Erebor gate form the composition, except these meshes.
COMPOSITION_RADIUS = 16
# Excluded: the gate itself and the Ravenhill building beside it (RiE's map data lists its transform right after the
# Rammas Echor block, which has no transform of its own). Effect entities (the waterfalls and river rapids at Erebor)
# are not meshes and never part of the composition.
COMPOSITION_EXCLUDE = ("erebor_gate_mesh", "rammas_echor_intact_mesh", "ravenhill_mesh")
TRANSPLANT_RADIUS = 18  # RiE px around the Erebor gate whose height delta is copied
TRANSPLANT_FADE = 4  # RiE px at the edge of the radius over which the stamped cone fades to zero
# Cone weight c (how far a pixel moves from its own height toward the cone's height): smoothstep of the delta between
# these fractions of the extracted peak, times a face weight (0 in front of the gate face, rising to 1 over the first
# TRANSPLANT_FACE_RAMP RiE px behind it), times the radius fade, times a water fade (distance in map px to the nearest
# water or unassigned pixel / TRANSPLANT_WATER_FADE, at most 1, so rivers never become canyons).
TRANSPLANT_CONE_MIN = 0.15
TRANSPLANT_CONE_FULL = 0.40
TRANSPLANT_FACE_RAMP = 1
TRANSPLANT_WATER_FADE = 6
TRANSPLANT_PIECE_MIN_WEIGHT = 0.3  # a mountain piece stays only where the cone weight at its centre is at least this
# Per-site variation (deterministic: seeded by a hash of the site key).
TRANSPLANT_MIRROR_CHANCE = 0.5  # probability of mirroring the composition left/right
TRANSPLANT_MAX_TURN = 25  # degrees the composition's axis may turn toward the uphill direction
TRANSPLANT_UPHILL_T = (4, 30)  # px behind the gate (along inward) whose terrain decides "uphill"
TRANSPLANT_UPHILL_L = 20  # px either side of the axis used for it
TRANSPLANT_PEAK_MARGIN = 2000  # the cone's peak should clear the highest lifted terrain in its footprint by this
TRANSPLANT_HEIGHT_MIN = 0.85  # clamp of the cone height factor
TRANSPLANT_HEIGHT_MAX = 1.25
TRANSPLANT_HEIGHT_JITTER = 0.05  # seeded +/- jitter of the height factor, within the clamp
TRANSPLANT_JITTER_POS = 0.6  # RiE units, each object's position, +/-
TRANSPLANT_JITTER_YAW = 15  # degrees, +/-
TRANSPLANT_JITTER_SCALE = (0.9, 1.1)  # each object's scale multiplier
# The range behind a cone joins its peak: dwarven or impassable land behind the gate (t >= 0) within RANGE_JOIN_RADIUS
# px of it, outside the cone core, is scaled up from the gate's foot by s = (cone peak - foot) / (range max - foot),
# clamped to [1, RANGE_JOIN_MAX], at full strength within RANGE_JOIN_FULL px and fading out (cosine) to the radius.
RANGE_JOIN_RADIUS = 60
RANGE_JOIN_FULL = 30
RANGE_JOIN_MAX = 2.0
RANGE_JOIN_CORE = 0.4  # pixels with at least this cone weight are the cone, not the range
# The gate model's footprint (px per unit of gate scale; the Erebor gate mesh is about 3.25 deep and 7.84 wide) and a
# front apron (px at gate scale 1.6): both are raised to at least the gate's foot, blending out over GATE_APRON_FADE px.
GATE_APRON = 4
GATE_APRON_FADE = 3
GATE_MODEL_DEPTH = 3.25
GATE_MODEL_HALF_WIDTH = 3.92
GATE_APRON_SCALE = 1.6
# A mountain piece whose footprint overlaps the gate's keep-out (the front apron up to PIECE_FACE_CLEARANCE px behind
# the face, and the model's width plus PIECE_KEEP_OUT_MARGIN px at the sides) is pushed back along the cone axis by at most PIECE_MAX_PUSH px, else dropped.
PIECE_MAX_PUSH = 12
PIECE_KEEP_OUT_MARGIN = 2
PIECE_FACE_CLEARANCE = 1.0  # the keep-out ends this many px behind the gate face: the body behind it may be overlapped
# Per-gate pins keyed like GATE_OVERRIDES: mirror (bool), turn (degrees), height (the height factor, used as is).
TRANSPLANT_OVERRIDES = {}
PACK_TOLERANCE = 257  # largest height error allowed when repacking the heightmap

# Terrain blend-map gaps: Anbennar's detail_intensity.tga has pixels with no material (drawn black). Gaps smaller
# than TERRAIN_FILL_LARGE pixels copy a painted neighbour; larger ones get TERRAIN_FILL_MATERIAL at full weight.
TERRAIN_FILL_MATERIAL = "mountain_02"  # Anbennar material id; draws RiE's Mountains 01 rock through TEXTURE_MAP
TERRAIN_FILL_LARGE = 1000
