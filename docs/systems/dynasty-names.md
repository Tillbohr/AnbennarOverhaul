# Dynasty names

CK3 names a new dynasty from its culture's name list (`dynasty_names`, and `cadet_dynasty_names` for cadet houses)
whenever a lowborn character gains land. At game start that happens to the 118 landed rulers Anbennar's history
leaves without a dynasty (48 of them Castanite). Anbennar ships 48 of its name lists with vanilla's English dynasty
names (de Bohun, de Vere, Holland, Butler, ...), marked `#TODO - replace placeholder dynasty names`, and the gnomish
and halfling lists with vanilla's Frisian ones (Abdena, Allena, ...), so those rulers, and every dynasty founded later
in those cultures, got English or Frisian names.

`build_dynasty_names.py` writes a copy of each of those 50 name lists into
`common/culture/name_lists/zz_aov_dynasty_names.txt` (a single-object override, loaded after Anbennar's `anb_*` files)
with both name blocks replaced by EU4 Anbennar's dynasty names. Everything else in each list (given names, mercenary
names, chances) is Anbennar's, copied verbatim; only the `#TODO - replace placeholder dynasty names` line is dropped.

| Generated file | Generator | Why generated |
|---|---|---|
| `common/culture/name_lists/zz_aov_dynasty_names.txt` | `build_dynasty_names.py` | single-object copies of Anbennar's name lists, rebuilt so Anbennar's given names stay current |
| `localization/english/aov_dynasty_names_l_english.yml` | `build_dynasty_names.py` | `dynn_` keys for the names no loaded loc already has |

## Names

`tools/data/dynasty_names.py` holds both halves:

- `NAME_LISTS`: each CK3 name list and the EU4 cultures or culture groups it takes names from, in order. A CK3
  culture with no EU4 namesake takes its parent's or neighbours' names (commented on its line), and small EU4 lists
  get their culture group's names too.
- `EU4_DYNASTY_NAMES`: those cultures' `dynasty_names`, imported once from EU4 Anbennar's
  `common/cultures/anb_cultures.txt` with `eu4_import.py`'s `culture_dynasty_names()` and committed. Edit names here;
  nothing is read from EU4 at build time. Two EU4 lists are left out on purpose: Havoric (a mis-encoded copy of the
  Esmari list, every accent turned into `í`) and Delta Gnome (a copy of the Kheteratan list), and Dhanaenno's
  duplicate `síl Dhanaenn` was dropped.

EU4 writes prefixes into the name; the build splits them into Anbennar's prefix keys: `síl na` `dynnp_sil_na`,
`sílna` `dynnp_silna`, `síl` `dynnp_sil`, `sína`/`sina` `dynnp_sina`, `of` `dynnp_of`, `az-` `dynnp_az`. Fused
forms (`Silurion`, `Silcalas`) stay whole. Each base name reuses any loaded `dynn_` key (Anbennar's first, then the
game's) that already shows it; otherwise it gets `dynn_<ascii name>`, or `dynn_aov_<ascii name>` when that key shows
something else (only `Rós`, since the game's `dynn_Ros` is "Ros").

A name already borne by an Anbennar game-start dynasty or house is left out, so the game never founds a second
"síl Vivin" next to Anbennar's. Every list keeps at least 15 names (a test checks it).

## Checks

- The tests (`test_build_dynasty_names.py`) check that the data covers exactly the name lists that still hold a
  placeholder, that every EU4 source is used, that each list keeps 15 names, that every key in the generated lists
  has loc and that new keys never shadow loaded ones, and that the generated files are fresh.
- The build stops if a listed name list is gone or no longer holds placeholders (Anbennar fixed it upstream: drop it
  from `NAME_LISTS`).
- One tiger warning is baselined: `name_list_wood_elven`'s `dynasty_of_location_prefix = "sil"` is Anbennar's line
  (a raw key, no loc), copied verbatim.

## In game

Not yet checked in game. To check: start a game and open a landed lowborn ruler at game start, e.g. a Castanite count
in Castanor; the dynasty should carry a Castellyrian or Escanni name (`síl Núrced`, `Elderlan`, ...), not an English
one. `database_conflicts.log` should list each `name_list_*` as overridden by `zz_aov_dynasty_names.txt`; if the
game instead reports duplicate name lists, name lists do not support single-object overrides and the build must
switch to same-path copies of Anbennar's `anb_*.txt` name list files.
