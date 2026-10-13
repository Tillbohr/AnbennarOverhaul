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
# The first two are not texture-array members as far as checks go: see build_map_graphics.NOT_ARRAY_MEMBERS.
DROP_INS = (
    "snow_diffuse.dds",
    "snow_diffuse_for_combined_winter.dds",
    "forest_pine_01_normal.dds",
    "forest_pine_01_properties.dds",
)

# --- Declared for later tasks -------------------------------------------------------------------------------

# Colour grading: title key -> grade (empire covers its de jure kingdoms; a kingdom entry overrides, None removes).
GRADING = {
    "e_gerudia": "boreal",
    "e_salahad": "desert",
    "e_kheterata": "desert",
    "e_bulwar": "arid",
    "e_harpylen": "arid",
}
GRADING_MARGIN = 60
GRADING_FADE = 300

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
