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

CK3 picks a holding model by the holder culture's `building_gfx` list (first match wins) and the province's graphical
region. Anbennar gives all four groups vanilla gfx (mostly `western_building_gfx`), so each target culture gets a new
key **prepended** to its `building_gfx` list: `aov_high_elf_building_gfx`, `aov_wood_elf_building_gfx`,
`aov_dwarven_building_gfx`, `aov_castanorian_building_gfx`. The rest of the list stays as fallback.

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
asset: `type = pdxmesh`, `name` or `names` (variants), the original first asset's `illustration` and `soundeffect`,
and `graphical_cultures = { aov_<group>_building_gfx }` (dwarves also `graphical_regions = {
graphical_aov_dwarven_mountains }`).

| Building | High elves | Wood elves | Castanorians | Dwarves (mountains only) |
|---|---|---|---|---|
| `*_01` | `highelves_01_01/02` | `sindarin_sanctuary_01` | castle `building_dunedain_castle_01`, city `gondor_city_01`, temple `building_dunedain_temple_01_a/b` | castle/city `dwarven_holding_01` |
| `*_02` | `highelves_02_01/02` | `sindarin_sanctuary_02` | castle `…castle_02`, city `gondor_city_01`, temple `…temple_01_a/b` | `dwarven_holding_02` |
| `*_03` | `highelves_03_01/02` | `sindarin_sanctuary_03` | castle `…castle_03`, city `gondor_city_02`, temple `…temple_02_a/b` | `dwarven_holding_03` |
| `*_04` | `highelves_04_01/02` | `sindarin_sanctuary_03` | castle `…castle_04`, city `gondor_city_02`, temple `…temple_02_a/b` | `dwarven_holding_04` |

(All names with `_mesh`; temples for dwarves are unchanged. The table lives in the data file.)

### 3. Dwarven holds

`tools/build_holds.py` (generated `common/buildings/aov_dwarven_holds.txt`) adds, before each hold level's existing
castle asset, an asset `dwarven_holding_0N_mesh` with `graphical_cultures = { aov_dwarven_building_gfx }` (levels 1-2 →
01, 3-4 → 02, 5-6 → 03, 7-8 → 04, 9-10 → 05, as RiE's `dwarven_depths`), no region requirement (holds are in mountains).
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
