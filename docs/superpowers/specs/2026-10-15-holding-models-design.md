# RiE holding models for elves, dwarves and Castanorians — design

Date: 2026-10-15. Status: approved in conversation, awaiting written-spec review.

## Goal

Give Anbennar's elves, wood elves, dwarves and Castanorian (Escanni) cultures the holding models their counterparts
use in *Lord of the Rings: Realms in Exile* (RiE, Workshop 2291024373). Everything ships inside the Overhaul and is
rebuilt by a generator after Anbennar, RiE or CK3 updates. Players need only Anbennar and the Overhaul.

## Decisions (from the conversation)

| Group | Anbennar cultures | RiE counterpart | RiE models |
|---|---|---|---|
| High elves | `moon_elvish`, `sun_elvish` (heritage_elven) | Noldor, Sindar (`noldor_building_gfx`) | `highelves_01..04` (`highelves_0N_01_mesh`, `highelves_0N_02_mesh`) |
| Wood elves | `wood_elvish` | Lasgalendrim (Silvan, default elven settlement) | `sindarin_sanctuary_01..03_mesh` |
| Dwarves | the 11 heritage_dwarven cultures (`ruby_dwarvish` … `marble_dwarvish`) | dwarf cultures (`dwarven_depths` holding) | `dwarven_holding_01..05_mesh` |
| Castanorians | the 14 heritage_escanni cultures (adenner, white_reachman, black_castanorian, marcher, castellyrian, castanite, castanorian, adeanic, faranni, balmirish, patrician, merewoodian, trystanite, humacfelder) | Gondorian (`dunedain_building_gfx`) | `building_dunedain_castle_01..04_mesh`, `gondor_city_01/02_mesh`, `building_dunedain_temple_01/02_a/b_mesh` |

- Elves: castles, cities and temples all change.
- Dwarves: holdings **in mountain ranges** use RiE's dwarf models; dwarves on ordinary land keep vanilla's western
  models. The 10 `dwarven_hold` levels use the dwarf models for dwarf holders.
- Tribal holdings and every other culture are unchanged.

## Architecture

New generator `tools/build_holding_models.py`, data `tools/data/holding_models.py`, tests
`tools/tests/test_build_holding_models.py`. Standard library only (reuse the brace/parse helpers in `tools/`).
Without RiE installed it stops naming the missing path and writes nothing.

### 1. Culture keys (generated full-file overrides)

CK3 picks a holding asset by the province's graphical region first (`_buildings.info`: the most important criterion)
and then by the holder culture's `building_gfx` keys; the region outranks the culture. Anbennar gives all four groups
vanilla gfx (mostly `western_building_gfx`), so each target culture gets a new key **prepended** to its `building_gfx`
list: `aov_high_elf_building_gfx`, `aov_wood_elf_building_gfx`, `aov_dwarven_building_gfx`,
`aov_castanorian_building_gfx`. The rest of the list stays as fallback. `_cultures.info` requires every list that starts
with one key to continue identically, so a group gets one key per distinct existing list: its own key for the most
common list, `aov_<group>_<second key's stem>_building_gfx` for each other (dwarves: copper, gold and marble dwarvish
end in `mena_building_gfx` and get `aov_dwarven_mena_building_gfx`). A test checks that, with the overrides applied,
every first key has exactly one continuation across Anbennar's culture files.

Culture definitions are overridden as whole files: the generator copies each Anbennar culture file that contains a
target culture (`common/culture/cultures/anb_elven.txt`, `anb_dwarf.txt`, `anb_escanni.txt` today; derived from the
data, not hard-coded), keeps every byte except the target cultures' `building_gfx` lines (marked
`# Anbennar Overhaul`), and writes them under the same path in this mod. A target culture missing from Anbennar, or a
target culture without a `building_gfx` line, stops the generator. Created hybrid/divergent cultures inherit their
parents' gfx, as usual.

### 2. Holding buildings (generated single-object overrides)

`common/buildings/zz_aov_holding_models.txt` re-emits `castle_01..04`, `city_01..04` and `temple_01..04`: each
definition is copied from Anbennar when Anbennar defines it (`00_castle_buildings.txt`, `00_temple_buildings.txt`),
otherwise from the game (`city_*` from `game/common/buildings/00_city_buildings.txt`), byte-exact except new `asset`
blocks inserted **before** the first existing `asset` block, marked `# Anbennar Overhaul: RiE holding model`. Each new
asset: `type = pdxmesh`, `name` or `names` (variants), `illustration` and `soundeffect` copied from the first original
asset without `requires_dlc_flag` whose `graphical_cultures` include the group key's fallback (the second key of its
list, `western_building_gfx`; if none, the first asset without a DLC flag), `graphical_cultures = { <every key of the
group> }` and `graphical_regions = { <every region with graphical = yes in Anbennar's map_data/geographical_regions> }`
(read at build time, as vanilla's DLC culture assets list all regions; the region outranks the culture, so a bare
culture asset would lose to the region-matched western ones). Dwarf castle and city assets keep only
`graphical_regions = { graphical_aov_dwarven_mountains }`.

| Building | High elves | Wood elves | Castanorians | Dwarves (mountains only) |
|---|---|---|---|---|
| `*_01` | `highelves_01_01/02` | `sindarin_sanctuary_01` | castle `building_dunedain_castle_01`, city `gondor_city_01`, temple `building_dunedain_temple_01_a/b` | castle/city `dwarven_holding_01` |
| `*_02` | `highelves_02_01/02` | `sindarin_sanctuary_02` | castle `…castle_02`, city `gondor_city_01`, temple `…temple_01_a/b` | `dwarven_holding_02` |
| `*_03` | `highelves_03_01/02` | `sindarin_sanctuary_03` | castle `…castle_03`, city `gondor_city_02`, temple `…temple_02_a/b` | `dwarven_holding_03` |
| `*_04` | `highelves_04_01/02` | `sindarin_sanctuary_03` | castle `…castle_04`, city `gondor_city_02`, temple `…temple_02_a/b` | `dwarven_holding_04` |

(All names with `_mesh`; temples for dwarves are unchanged. The table lives in the data file.)

### 3. Dwarven holds

`tools/build_holds.py` (generated `common/buildings/aov_dwarven_holds.txt`) adds, before each hold level's existing
castle asset, an asset `dwarven_holding_0N_mesh` with `graphical_cultures` = both dwarven keys and `graphical_regions`
= every graphical region (levels 1-2 → 01, 3-4 → 02, 5-6 → 03, 7-8 → 04, 9-10 → 05, as RiE's `dwarven_depths`);
illustration and sound as in section 2 (the band's first castle asset without a DLC flag that serves `western_building_gfx`).
The castle asset stays as the fallback for non-dwarf holders.

### 4. Dwarves in mountains vs on land

A new graphical region in `map_data/geographical_regions/aov_graphical_regions.txt`:
`graphical_aov_dwarven_mountains = { graphical = yes color = {…} provinces = { … } }` listing every province whose
terrain (`common/province_terrain/00_province_terrain.txt`) is `mountains`, `desert_mountains`, `dwarven_hold`,
`dwarven_hold_surface`, `cavern` or `dwarven_road` (the set is `DWARF_MOUNTAIN_TERRAINS` in the data file).
Dwarf entries in castles/cities require this region, so dwarf holdings elsewhere fall back to their culture's
remaining gfx (western).

**Risk:** whether CK3 accepts a province in two graphical regions (ours and Anbennar's `graphical_western` etc.) is not
documented. If the dwarf mountain models do not show in game, the fallback is a generated copy of Anbennar's
`geographical_region.txt` with those provinces moved out of the other graphical regions; decided after the in-game
check.

### 5. Assets

RiE's `.asset`, `.mesh` and textures for the listed models are copied into
`gfx/models/buildings/aov_rie_holdings/<set>/` (assets verbatim; every texture the asset names copied beside it; a
missing file stops the generator). Pdxmesh names must not collide with Anbennar/vanilla names (check; prefix `aov_` in
regenerated asset text if they do). Art through Git LFS (`gfx/models/**/*.dds`, `*.mesh` already LFS). `credits.txt`
adds RiE's holding models.

## Testing

Tool tests (fixtures and real data):
- culture override: only target cultures' `building_gfx` lines change (new key first, rest unchanged); every other byte
  equals Anbennar's; unknown/missing target cultures stop the build;
- building override: each re-emitted building equals its source plus the inserted assets before the first original
  asset; the table's models per level; dwarf entries carry the region;
- holds: each level's dwarf asset and mesh by level; the castle asset still present;
- region: every province with a listed terrain is in it and no other province;
- assets: every mesh/texture each copied asset names exists in the output; no pdxmesh name collides with Anbennar's or
  the game's;
- generated files fresh; tiger clean.

In-game checklist:
- [ ] Moon/sun elf castles, cities and temples show the high-elf models at each level; wood elves show the Silvan
  sanctuaries.
- [ ] Escanni castles, cities and temples show Gondor's models.
- [ ] The 9 dwarven holds show RiE's dwarf models under dwarf holders and the castle models under others.
- [ ] Dwarf castles/cities in mountains show the dwarf models; dwarf holdings on ordinary land show vanilla's.
- [ ] Other cultures' holdings are unchanged; `error.log` has no missing mesh/texture/effect errors.

## Risks

1. Graphical-region overlap (above).
2. Culture files are whole-file overrides: rerun the generator after every Anbennar update (CLAUDE.md update steps).
3. RiE's shaders for these assets must exist in the ported `pdxmesh.shader` / `court_scene.shader` placeholders; the
   generator checks each asset's shader has its `_mapobject` variant, as the gate assets do.
4. Permission: RiE's assets, like the rest of the map graphics, need the RiE team's go-ahead before a Workshop upload.

## In-game fixes

First in-game test found three problems; the changes are generated by `tools/build_holding_models.py` and `tools/build_holds.py`.

Root causes:
1. Elven holdings kept vanilla walls. Those walls are not part of the holding model: they come from the background
   buildings `walls_01_tribal`, `walls_01..04` (`is_graphical_background = yes`, Anbennar's
   `99_background_graphics_buildings.txt`). RiE draws elven walls with its own background building `elven_walls`.
2. Wood elf holdings looked unchanged because every one starts as a tribal holding (Deepwoods: 29 `tribal_holding`), and
   only castle, city and temple had been changed. `tribe_01/02` come from the game's `00_tribal_buildings.txt`.
3. `error.log` showed 450 "Province ... lies in multiple graphical regions" (`graphical_western` and
   `graphical_aov_dwarven_mountains`): CK3 rejects the new graphical region, so the dwarf models never showed. This
   confirms and settles risk 1 above. Vanilla precedent for a culture- and province-limited asset: castle_01's
   Constantinople asset (`provinces` outranks the graphical region, `_buildings.info`).

Changes:
- New background building `aov_elven_walls` (`common/buildings/aov_holding_walls.txt`): `highelves_fort_wall_mesh` for
  the high elf keys and `sindarin_hedge_wall_01_mesh` for the wood elf keys, all graphical regions; enabled for an
  elf-culture holder on a county capital or with `fort_level > 0`. Anbennar's `walls_01_tribal`, `walls_01..04` are
  re-emitted byte-exact in `zz_aov_holding_walls.txt` with one inserted first line in `is_enabled` that excludes elf
  cultures. `walls_00` and Castanorian walls are untouched.
- `tribe_01/02` re-emitted from the game with `sindarin_sanctuary_01/02_mesh` first for the wood elf key.
- The graphical region and its file are removed. Dwarven-terrain provinces (`dwarven_hold`, `dwarven_hold_surface`,
  `cavern`, `dwarven_road`, minus 263) get the dwarf model in every castle and city for any holder (`provinces`, no
  `graphical_cultures`); dwarf cultures also get it in `mountains` and `desert_mountains` provinces. The dwarven hold
  levels lose `graphical_cultures` on their dwarf asset.

### Round 2

Evidence: CK3 scores assets rather than filtering them (RiE's `00_temple_buildings.txt`: graphical_faiths +1,
graphical_cultures +2, graphical_regions +4; `_buildings.info`: `provinces` outranks the region); ties go to the asset
listed first. Second in-game test:
1. Elven and Castanorian temples stayed vanilla: Venail's faith has `graphical_faith = orthodox_gfx`, so vanilla's
   temple asset scored 1 + 2 + 4 = 7 against our 6. Every new temple asset now also lists `graphical_faiths` = the
   distinct `graphical_faith` values of Anbennar's religion_types (`catholic_gfx dharmic_gfx islamic_gfx orthodox_gfx
   pagan_gfx sinitic_gfx`, read at build time): 7 and first, so ours wins; other cultures score 5 and keep vanilla.
2. Marrhold (a human-held dwarven hold) stayed vanilla: the hold-level dwarf asset had regions only (4) against the
   copied western castle asset (6). It now lists the same dwarven-terrain `provinces` as the castle and city asset
   (`dwarf_model_provinces`, shared code).
3. Dwarf models appeared in mountains without dwarves: `provinces` outranks `graphical_cultures`, so the mountain
   asset showed to every holder. It is removed (with `DWARF_MOUNTAIN_TERRAINS`). Dwarves outside dwarven terrain now
   keep vanilla models, because a province asset cannot be limited to a culture.
4. The fence and field around dwarf models were the vanilla wall backgrounds. New generated scripted trigger
   `aov_dwarven_model_province_trigger` (`common/scripted_triggers/aov_holding_model_triggers.txt`); `walls_01_tribal`,
   `walls_01..04` and now also `walls_00` (`western_walls_00_mesh`) are re-emitted with the inserted line `NOT = {
   aov_dwarven_model_province_trigger = yes }`, after the elven line, as the first lines of `is_enabled`.

### Round 3

1. Dwarf-model provinces showed no model at all (e.g. Midmarket): round 2 switched off every wall background there,
   `walls_00` included. A holding needs an active background building; RiE keeps `walls_00` ("no walls") on for its
   underground dwarves (`lotr_dwarven_underground_buildings_requirement_terrain`). `walls_00` is now ON in dwarf-model
   provinces: `aov_dwarven_model_province_trigger = yes` is the first child of its `is_enabled` `OR`. `walls_01_tribal`
   and `walls_01..04` keep their `NOT` line (no palisade or fields).
2. Castanorian (Escanni) holders get RiE's Gondor walls with gatehouses: `dunedain_walls_02/03/04_mesh` as the first
   asset of `walls_02/03/04` (`CASTANORIAN_WALLS`; castanorian keys, all graphical regions: score 6 ties the western
   wall assets and wins by order). RiE has no Dunedain model for `walls_00`, `walls_01_tribal` and `walls_01`. The assets,
   meshes and textures are copied into `gfx/models/buildings/aov_rie_holdings/castanorian/`.

### Round 4

1. Temples in dwarven terrain showed vanilla temples. RiE has no dwarf temple, so `temple_01..04` get the same first
   dwarf asset as castles and cities (`dwarven_holding_0N_mesh` for level N, the dwarven-terrain `provinces`, all
   graphical regions, no cultures, no faiths: a province outranks the faith), data-driven in `MODELS`.
2. Escanni early walls showed the vanilla palisade and field (RiE has no Gondor equivalent). `walls_01_tribal` and
   `walls_01` get an inserted first asset `western_walls_00_mesh` (vanilla's "no walls" mesh, the one `walls_00`
   uses; castanorian keys, all regions): it draws nothing but keeps a background active, so the building stays
   enabled and no `is_enabled` changes. Same table as the Gondor walls (`CASTANORIAN_WALLS`); the mesh is the game's
   (`GAME_MESHES`), so nothing is copied.

### Round 5

Escanni holdings never showed Gondor walls: the vanilla wall chain is driven by fortification buildings (`walls_02`
needs Curtain Walls 2 / Hill Forts 2 / ..., `walls_03` level 3, ...) and almost no holding has one at game start.
Walls now follow the HOLDING LEVEL for every culture (user decision), `WALL_LEVELS` in the data file:

1. Generated province triggers `aov_holding_walls_level_3_trigger` (`has_building` `castle_03`/`city_03`/`temple_03`) and
   `aov_holding_walls_level_4_trigger` (`has_building_or_higher` `castle_04`/`city_04`/`temple_04`; Anbennar and the game
   define no level 05+) in `aov_holding_model_triggers.txt`.
2. `walls_00` gets a new first-level child of its `OR`: level 1-2 holdings and tribal holders (`NOT = { OR = { level 3,
   level 4 } }` or a tribal holder), except an elf whose holding has elven walls. RiE keeps its `walls_00`
   (`fort_level < 1`, not capital) and `elven_walls` (`fort_level >= 1`) mutually exclusive, so the elf guard repeats the
   `aov_elven_walls` condition (elf culture and (county capital or fort level > 0)) instead of allowing both backgrounds.
3. `walls_01_tribal`, `walls_01`, `walls_02`: `always = no` as the first `is_enabled` line (they never show).
4. `walls_03`, `walls_04`: the fortification `OR` (curtain walls / hill forts / ramparts / watchtowers / temple citadel,
   plus the nomad `fort_level` alternative) is replaced by the level trigger. `walls_03`'s fortification `NOR` (levels
   06 and temple citadel 4) is dropped: with it a level-3 holding with a top fortification would have shown no wall
   background at all (`walls_04` needs level 4), and the two level triggers already exclude each other. The tribal
   exclusion and the elven and dwarven lines stay; a tribal holder with a level 3-4 holding gets `walls_00`.
5. The now unused Escanni entries are gone: `western_walls_00_mesh` in `walls_01_tribal`/`walls_01`, `dunedain_walls_02_mesh`
   in `walls_02` (`GAME_MESHES` removed, `dunedain_walls_02.asset/.mesh` no longer copied).

### Round 6

In game, Gondor walls showed on holdings of every culture at level 3-4. Vanilla's regional `walls_03`/`walls_04` assets
carry only `graphical_regions` (score 4) and no `graphical_cultures`, so the first-listed Dunedain asset (region 4 for any
culture) won the tie everywhere. The Dunedain asset is now inserted after the last original asset: the Escanni still
pick it (culture 2 + region 4 = 6), everyone else keeps vanilla's walls by order. The holding assets stay first: every
Anbennar `building_gfx` list matches a vanilla culture asset in `castle_01`, `city_01` and `temple_01`, so no culture
falls to a region-only tie there.

### Round 7

1. Every culture's tribal holdings showed the Silvan sanctuary. No vanilla `tribe_01/02` asset lists
   `graphical_regions`, so the all-regions wood elf asset scored 4 against at most 2 for any culture's own tribal
   model. A building whose source assets list no region now gets its new assets without regions and after its last
   asset: wood elves win on the culture (2), every other culture keeps vanilla's earlier assets on the 0-ties.
2. Every castle drew the elven walls. `aov_elven_walls` was on for every holder (and the elven exclusion switched
   `walls_03/04` off), so `scope:holder ?= { culture = { has_building_gfx = aov_high_elf_building_gfx ... } }` held for
   non-elves too, presumably through the elf keys' `western_building_gfx` fallback. The elf trigger (aov_elven_walls,
   the exclusion line of `walls_01_tribal`, `walls_01..04` and the elf guard of `walls_00`) now checks the holder's
   culture directly: `scope:holder ?= { OR = { culture = culture:moon_elvish culture = culture:sun_elvish
   culture = culture:wood_elvish } }` (the cultures of the high and wood elf groups).
