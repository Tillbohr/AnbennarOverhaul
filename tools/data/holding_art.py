"""Pictures that replace a built holding's vanilla illustration in the county view.

tools/build_monuments.py turns each entry into a branch of the custom loc AovMonumentIllustration (after every monument
painting, so a monument painting always wins; then in list order, the first match wins) and a background that
tools/build_county_view_override.py inserts after the vanilla holding illustration, which is hidden while any entry
matches. Rerun both after editing.

Each entry:
- key: loc key aov_monument_art_<key> (unique, also among the EU4 monument keys)
- trigger: province-scope trigger (one or more lines); add `has_holding = yes` unless an empty holding should change too
- texture: the picture; must exist in this mod, Anbennar or the game (the build stops otherwise)
- style: "painting" (EU4 monument look: top-aligned, lighter mask, stops above the building slots) or "illustration"
  (vanilla's holding look: centre-cropped through vanilla's mask; the look of an empty holding's terrain picture)

To add pictures for another group (e.g. wood elves), append entries; the holder is `barony.holder` in province scope,
e.g. "has_holding = yes\nbarony.holder ?= { culture = { has_clothing_gfx = aov_lasgalendrim_clothing_gfx } }"
(the wood elf key of tools/data/portraits.py). Put an entry that should beat a broader one (a terrain) before it.
"""

from data import holds

# Anbennar ships an EU4 picture for each dwarven terrain (gfx/interface/illustrations/terrain_types/<terrain>.dds),
# shown for an empty holding; a built holding there shows it too instead of vanilla's castle or city art. Ours in
# aov_terrain/ are EU4's province-view terrain pictures (330x85) upscaled 4x outside (Upscayl standard 4x).
TERRAIN_ART = ("dwarven_hold", "dwarven_hold_surface", "cavern", "dwarven_road")
UPSCALED_TERRAIN = ("dwarven_hold_surface", "cavern", "dwarven_road")


def terrain_texture(terrain: str) -> str:
    folder = "aov_terrain" if terrain in UPSCALED_TERRAIN else "terrain_types"
    return f"gfx/interface/illustrations/{folder}/{terrain}.dds"


# EU4 terrains CK3 has no terrain for: the CK3 counties and baronies named like EU4's terrain_override provinces of
# that terrain (map/terrain.txt), matched once by name (accents folded; Hofoon, Drennenthille and Ddweynaile by
# spelling). A county covers all its baronies. 90 of EU4's 136 ancient forest provinces are not on the CK3 map or
# have no named title there; none of the 19 gladeway provinces (Vyr ...) is.
EU4_TERRAIN_TITLES = {
    "ancient_forest": (
        # Deepwoods
        "c_lake_grove_1_1", "c_lake_grove_1_2", "c_lake_grove_1_3", "c_lake_grove_1_4", "b_lake_grove_3",
        "b_lake_grove_4", "b_lake_grove_7", "b_lake_grove_9",
        "c_bone_grove_1_1", "c_bone_grove_1_3", "c_bone_grove_1_4",
        "c_thorn_grove_1_1", "c_thorn_grove_1_2", "c_thorn_grove_1_3", "c_thorn_grove_1_4",
        "c_mountain_grove_1_1", "c_mountain_grove_1_3", "c_mountain_grove_1_4", "b_mountain_grove_1",
        "b_mountain_grove_4", "b_mountain_grove_6", "b_mountain_grove_8",
        "c_hunter_grove_1_1", "c_hunter_grove_1_2", "c_hunter_grove_1_3",
        "c_flower_grove_1_1", "c_flower_grove_1_2",
        "c_arrow_grove_1_1", "c_arrow_grove_1_2", "c_arrow_grove_1_3",
        "c_river_grove_1_1", "c_river_grove_1_2", "c_river_grove_1_3",
        "c_shadow_grove_1_1", "c_shadow_grove_1_2",
        # Western Cannor
        "c_gladegate", "c_ioriellen", "c_autumnglade", "c_springlade", "c_summerglade", "c_winterglade",
        "c_carneter", "c_woodwell", "c_ancards_crossing", "c_ilvandet", "c_timberfort",
    ),
}


def titles_trigger(titles: tuple) -> str:
    """Province-scope trigger lines: the province is one of these baronies or in one of these counties."""
    kind = {"c": "county", "b": "barony"}
    return "\n".join(["OR = {", *[f"\t{kind[t[0]]} = title:{t}" for t in titles], "}"])


HOLDING_ART = [
    {"key": "ruined_hold", "trigger": "aov_hold_is_ruined = yes", "texture": holds.RUINED_ART, "style": "painting"},
] + [
    {"key": f"terrain_{t}", "trigger": f"has_holding = yes\nterrain = {t}",
     "texture": terrain_texture(t), "style": "illustration"}
    for t in TERRAIN_ART
] + [
    {"key": f"terrain_{t}", "trigger": f"has_holding = yes\n{titles_trigger(titles)}",
     "texture": f"gfx/interface/illustrations/aov_terrain/{t}.dds", "style": "illustration"}
    for t, titles in EU4_TERRAIN_TITLES.items()
]
