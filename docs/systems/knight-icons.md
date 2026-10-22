# Race knight badges

Knights of elven, dwarven, gnomish and kobold rulers show that race's EU4 Anbennar tech group icon, with its gear
removed, instead of the vanilla knight badge (`icon_knight_small.dds`).

## Generated files

| File | Generator | Why |
|---|---|---|
| `common/customizable_localization/aov_knight_icon_custom_loc.txt`, `common/scripted_triggers/aov_knight_icon_triggers.txt`, `common/culture/innovations/aov_knight_icon_innovations.txt`, `localization/english/aov_knight_icons_l_english.yml`, `gui/window_military.gui`, `gui/window_knights.gui`, `gui/window_army.gui`, `gui/window_battle_summary.gui` (whole-file overrides of the game's), `gui/shared/cooltip.gui` (whole-file override of Anbennar's) | `python -I tools/build_knight_icons.py` | Picks the badge by race (data in `tools/data/knight_icons.py`) and swaps it into the interface. Interface files can only be overridden whole, so each is the base file with its knight badge textures replaced, marked `# Anbennar Overhaul: race knight badge`; the generator stops if a file has a different number of badges than `GUI_TARGETS` expects. Rerun after an Anbennar update or a CK3 patch. `tools/tests/test_build_knight_icons.py` (`FreshnessTests`) fails when the files are stale. |
| `gfx/interface/icons/aov_knight_icons/<race>.dds` | `python -I tools/build_knight_icons.py --import [KEY]` (needs EU4 Anbennar) | Imported once and committed, like other EU4 art. Cut from `gfx/interface/tech_group_strip.dds`, gear cleared by the race's hand-tuned mask, 38 px Lanczos 2x up then down to 50 px (the vanilla badge size), pixels under the mask cleared again so resampling leaves no halo. |

## System

- **Races** (`RACES`, first match wins): moon, sun and wood elves (culture lineage triggers from the racial armies
  system), then `heritage_dwarven`, `heritage_gnomish`, `heritage_kobold`; anyone else keeps the vanilla badge.

  | Race | EU4 tech group | Icon in the strip |
  |---|---|---|
  | Moon elves | `tech_elven` | 20 |
  | Sun elves | `tech_east_elven` | 21 |
  | Wood elves | `tech_wood_elf` | 22 |
  | Dwarves | `tech_west_dwarven` | 18 |
  | Gnomes | `tech_gnomish` | 23 |
  | Kobolds | `tech_kobold` | 26 |

- **Whose race:** the ruler's. The custom loc `aov_knight_icon` (character scope) uses the character if they are a
  ruler, else their court owner (`aov_knight_icon_ruler_trigger`), and returns the name of a hidden innovation
  (`aov_knight_badge_<race>` loc = `aov_knight_icon_<race>`; `aov_knight_icon_default` holds the vanilla badge).
  An interface `texture` cannot take a loc string as a path (the first version showed no badge at all), so each badge is
  the `icon` of a never-available innovation (`potential = { always = no }`) and the interface reads
  `GetCultureInnovationType(<scope>.Custom('aov_knight_icon')).GetIcon`, the pattern Realms in Exile and Princes of
  Darkness use for script-chosen pictures.
- **Where:** the military window (the window's ruler), the knights window and battle summary (the knight, so their
  court owner), the army window and army tooltip (`Army.GetOwner`). Left vanilla: the `@knight_icon` text icon, the
  acclaimed-knight badge and the tournament knights view.
- **Gear masks:** the gear sits top left, behind the art, so a mask only has to clear it: `{row: last x}` clears x 0..last
  in that row (gear, its outline and its shadow), up to the art's edge. Edges were set by hand from per-pixel colour
  maps; gear colour varies (gold, blue, copper), so no shared template works.

## Adding a race (goblins, orcs)

1. Add a row to `RACES` in `tools/data/knight_icons.py`: key, name, EU4 icon number (the tech group's position in EU4
   Anbennar's `common/technology.txt` groups: 32 Orcish, 33 Black Orcish, 35 Goblin, 37 Cave Goblin), its tech group,
   the culture check (`("has_cultural_pillar", "heritage_<race>")` or a lineage trigger, `"yes"`) and the gear mask.
2. `python -I tools/build_knight_icons.py --import <key>` and look at the icon; adjust the mask until the gear is gone.
3. `python -I tools/build_knight_icons.py`, then the tests.

## In-game checks

1. The badges show the race icon in the military, knights, army and battle summary windows and the army tooltip.
   A vanilla badge on a racial ruler means the custom loc's trigger did not match; no badge at all means the
   innovation lookup failed.
2. A human ruler's knights keep the vanilla badge; a moon elf court's knights show the moon elf icon.
