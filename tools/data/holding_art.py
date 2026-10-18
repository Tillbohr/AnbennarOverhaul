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
# shown for an empty holding; a built holding there shows it too instead of vanilla's castle or city art.
TERRAIN_ART = ("dwarven_hold", "dwarven_hold_surface", "cavern", "dwarven_road")

HOLDING_ART = [
    {"key": "ruined_hold", "trigger": "aov_hold_is_ruined = yes", "texture": holds.RUINED_ART, "style": "painting"},
] + [
    {"key": f"terrain_{t}", "trigger": f"has_holding = yes\nterrain = {t}",
     "texture": f"gfx/interface/illustrations/terrain_types/{t}.dds", "style": "illustration"}
    for t in TERRAIN_ART
]
