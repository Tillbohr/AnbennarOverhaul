# West Dwarovar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add EU4's West Dwarovar (without the Krakdhum pocket) and Serpent's Vale to the CK3 map under one
placeholder empire `e_west_dwarovar`: caves traced and carved into province 2426 together with Anbennar's Khugdihr,
the Vale drawn as uncarved surface land, Khugdihr's kobolds left as Anbennar has them.

**Architecture:** The Serpentreach tracer (`tools/serpentreach_layout.py`) gains options for several regions, excluded
areas, surface counties, Vale mouths, avoidance of earlier floors and EU4 tunnel links; it runs a third time with
`tools/data/west_dwarovar.py`, and `build_serpentreach.py` draws all three regions into the shared map files.
`build_serpentreach.py`'s `Realm`/`People`/renderers take a data module so a new `tools/build_west_dwarovar.py` writes
the titles, history, people, arms and loc from them, adding Khugdihr's de jure moves. `build_map_graphics.py` carves
the caves with Khugdihr as a second carved range, paints the Vale, gates every exit and Vale mouth, and pulls the fog
off Dûr-Vazhatun.

**Tech Stack:** Python 3 standard library only (`python -I`), CK3 script/loc files (UTF-8 BOM, LF, tabs), unittest.

**Spec:** `docs/superpowers/specs/2026-11-03-west-dwarovar-design.md` (read it first; its kingdom table and connections
table are normative).

**Execution:** Native (user choice, 2026-11-03): one session implements every task in order with
superpowers:executing-plans, then one fresh reviewer on the most capable model checks the whole branch. Start that
session on the most capable model at high effort (CLAUDE.md: new generator work).

## Global Constraints

- Never write to `../anbennar-ck3-dev-master`; no Anbennar landed-title, culture or history file is overridden.
- Generated files are never edited by hand; every value lives in `tools/data/west_dwarovar.py` (map values in
  `tools/data/map_graphics.py`).
- Script and loc files: UTF-8 with BOM, LF, tabs; generated files start with the generator's `header_lines()`.
- Serpentreach's and Segbandal's titles, history, people, arms and loc stay byte-identical; only the shared map files
  (`provinces.png`, `definition.csv`, 8 locator files) and the map-graphics outputs gain the West Dwarovar.
- West Dwarovar ids start at Segbandal's last id + 1 (7139 today); colours never repeat an existing one.
- Regions `("west_dwarovar_region", "serpents_vale_region")`; `EXCLUDE_AREAS = ("krakdhum_area", "anvils_horn_area",
  "dead_end_tunnel_area")`; `SURFACE_AREAS = ("royal_terrace_area", "common_terrace_area", "assembly_terrace_area",
  "castle_hill_area")`; `SURFACE_BARONIES = 3`.
- `EXISTING = {2863: "c_khugdihr", 2896: "c_khugscave", 2897: "c_outerkhugscave", 2864: "c_dwarovrod1"}`.
- `NO_LINK_REGIONS = ("serpentreach_region", "middle_dwarovar_region", "northern_pass_region",
  "east_deepwoods_region")`; `OPENING_CUT_THROUGH = ()`; `LINK_REACH = 220`; `LINK_CUT_THROUGH = (2608,)`.
- Empire `e_west_dwarovar` "West Dwarovar", capital `c_amldihr`, colour (60, 40, 80); kingdoms, areas, tags and colours
  exactly as the spec's kingdom table.
- Khugdihr: Anbennar's four counties get no culture, faith, holder or arms change beyond the de jure moves and the I07
  arms on `k_khugdihr`/`d_khugdihr`/`c_khugdihr`; `k_khugdihr`'s new counties are `darkscale`/`nimrithani`, unheld.
- The eight dwarven kingdoms: `silver_dwarvish`, `ancestor_worship`, elders from 860.1.1 (die 1000-1010) and sons.
- Run tests with `python -I -m unittest discover -s tools/tests -p "<pattern>"` (never `-v` on the whole suite).

## Review Focus

1. **The refactors change Serpentreach or Segbandal** (ids, colours, titles) — their committed outputs must stay
   byte-identical. (Tasks 1, 4: `test_outputs_current` in both existing test files, run after each task.)
2. **A cave floor reaches the Deepwoods or the Northern Pass anyway** (fit error up to 48 px; Zokkorna spills onto
   Deepwoods Wasteland) — no new floor may touch a province of a `NO_LINK_REGIONS` region. (Task 3,
   `test_no_floor_touches_deepwoods_or_northern_pass`.)
3. **The Vale gets carved or walled by the range carve** — Vale heights must equal the input heightmap's. (Task 8,
   `test_vale_heights_untouched`.)
4. **An Anbennar update gives Khugdihr a holder, arms or a new county** — the build must stop rather than overwrite or
   duplicate. (Task 5, `test_khugdihr_holder_appears_stops`; Task 3, `test_existing_county_missing_stops`.)
5. **Amldihr ends up unreachable** (its only EU4 borders are the Vale) — the whole cave-and-Vale system plus Khugdihr
   must be one connected piece. (Task 3, `test_west_dwarovar_connected`.)

---

### Task 1: Tracer options — several regions, excluded areas, surface counties, avoided floors

**Files:**
- Modify: `tools/serpentreach_layout.py` (`layout`, `clip_floor`)
- Test: `tools/tests/test_serpentreach.py` (new `OptionTests` class, synthetic data where possible)

**Interfaces:**
- Produces: `layout(anbennar, eu4, ck3=None, cfg=None, first_id=None, used=None, avoid=None) -> Layout`; `avoid` is a
  set of `(x, y)` pixels (earlier layouts' floors) kept `cfg.WALL_MARGIN` away like any other province.
- `cfg.REGIONS` (tuple) preferred over `cfg.REGION`; `cfg.EXCLUDE_AREAS`, `cfg.SURFACE_AREAS`, `cfg.SURFACE_BARONIES`
  optional (`getattr` defaults `()`, `()`, `3`).
- A surface county has `County.type == "surface"`. `AREA_ORDER`/`KINGDOMS` must list exactly the regions' areas less
  `EXCLUDE_AREAS`.

- [ ] **Step 1: Write the tests:**
  `test_regions_union` (`region_provinces` over both keys equals the union), `test_excluded_area_not_traced` (no county
  has an excluded area; an `EXCLUDE_AREAS` key outside the regions raises `GeneratorError`),
  `test_surface_type_only_in_surface_areas` (a province with no `BARONIES` terrain outside `SURFACE_AREAS` raises;
  inside it gives type `"surface"` and `SURFACE_BARONIES` baronies), `test_avoid_keeps_margin` (on a synthetic grid,
  `clip_floor` with an avoided pixel leaves no floor within `WALL_MARGIN` of it).
- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p "test_serpentreach.py"` — new tests FAIL.
- [ ] **Step 3: Implement** the options in `layout`/`clip_floor` (avoided pixels join the "other province" set the
  margin is measured from).
- [ ] **Step 4: Run** `test_serpentreach.py` and `test_segbandal.py` — all PASS, `test_outputs_current` included.
- [ ] **Step 5: Commit** `West Dwarovar tracer: several regions, excluded areas, surface counties, avoided floors`.

### Task 2: Tracer options — Vale mouths, EU4 tunnel links, dropped pairs

**Files:**
- Modify: `tools/serpentreach_layout.py` (`Layout`, `layout`, `_links`, `foreign_contacts`)
- Test: `tools/tests/test_serpentreach.py`

**Interfaces:**
- Produces: `Layout` gains trailing field `mouths` (list of `Opening`, default `()`): one per surface county a cave
  county touches, `target` = the surface county's capital barony id, `mouth` = a surface pixel at the contact, `start`
  = the floor pixel beside it, `pixels` = the floor pixels within `OPENING_WIDTH` of the mouth.
- `eu4_adjacencies(eu4: Path) -> set[tuple[int, int]]` reads `map/adjacencies.csv` (both directions).
- `layout(..., targets=None)`: `targets` maps EU4 id -> CK3 province ids of earlier layouts' counties (Segbandal's
  `c_dwarovrod_25` for 2885); an adjacency pair from a region province to a `targets`/`EXISTING` province gets a link
  corridor (`_corridor`, width `OPENING_WIDTH`) of at most `cfg.LINK_REACH` px through `cfg.SOURCE_PROVINCE` and
  `cfg.LINK_CUT_THROUGH`, appended to `Layout.links`; none within reach raises `GeneratorError`.
- `cfg.NO_LINK_PAIRS` (set of EU4 id pairs, default empty) removes an opening, link or mouth.

- [ ] **Step 1: Write the tests:** `test_eu4_adjacencies_reads_dwarovrod_tunnel` ((2884, 2885) present),
  `test_mouth_between_cave_and_surface` (synthetic layout: one mouth, target is the surface capital barony, `start`
  4-adjacent to `mouth`), `test_link_beyond_reach_stops`, `test_no_link_pairs_drops_opening`.
- [ ] **Step 2: Run** `test_serpentreach.py` — new tests FAIL.
- [ ] **Step 3: Implement** mouths, adjacency links and `NO_LINK_PAIRS`; surface/cave contacts are allowed neighbours
  only where EU4 makes them neighbours (`foreign_contacts` unchanged otherwise).
- [ ] **Step 4: Run** `test_serpentreach.py` and `test_segbandal.py` — all PASS.
- [ ] **Step 5: Commit** `West Dwarovar tracer: Vale mouths, adjacencies.csv tunnel links, dropped pairs`.

### Task 3: West Dwarovar data and trace into the shared map files

**Files:**
- Create: `tools/data/west_dwarovar.py`
- Modify: `tools/build_serpentreach.py` (`layouts`, `build_from_layout`), `tools/build_map_graphics.py`
  (`west_dwarovar_layout`, cached like `segbandal_layout`)
- Create: `tools/tests/test_west_dwarovar.py` (`DataTests`, `LayoutTests`, `MapTests`)
- Generated: `map_data/provinces.png`, `map_data/definition.csv`, the 8 locator files

**Interfaces:**
- Consumes: Tasks 1-2's `layout` options.
- Produces: `bs.layouts(anbennar, eu4, ck3=None) -> (serp, seg, wd)`; `wd` has `first_id = max(seg.provinces) + 1`,
  `used` = both earlier colour sets, `avoid = set(serp.owner) | set(seg.owner)`, `targets = {2885: seg ids of
  c_dwarovrod_25}`. `bmg.west_dwarovar_layout(roots, ck3=None) -> sl.Layout`.
- Data module (values from Global Constraints and the spec): `REGIONS`, `SOURCE_PROVINCE = 2426`, `FIT_BOX =
  (2870, 0, 3720, 790)` (the regions' EU4 bounding box 3122-3473 x 118-641, widened by 250/150 px as in the planning
  probe: 508 shared provinces, median 16 px, max 48) and `CK3_FIT_BOX = (1380, 1420, 4410, 4096)` (that box mapped
  through the fit); the note must report a median under 20 px, `EXISTING`, `EXCLUDE_AREAS`, `SURFACE_AREAS`, `SURFACE_BARONIES`,
  `SURFACE_TERRAIN` (spec §3 list), `NO_LINK_REGIONS`, `NO_LINK_PAIRS = set()`, `OPENING_CUT_THROUGH`, `LINK_REACH`,
  `LINK_CUT_THROUGH`, `AREA_ORDER` (the kingdom table's areas top to bottom, `khugdihr_area` included), `KINGDOMS`,
  everything else imported from `data.serpentreach` as `data.segbandal` does.

- [ ] **Step 1: Write the tests:**
  - `DataTests.test_areas_cover_regions` (`AREA_ORDER` = regions' areas less `EXCLUDE_AREAS`; every area in one
    kingdom; each kingdom contiguous by EU4 area adjacency), `test_existing_names_match_anbennar`.
  - `LayoutTests` (real EU4, skipped when absent): `test_first_id_follows_segbandal` (`min(wd.provinces) ==
    max(seg.provinces) + 1`), `test_counts` (no county in an excluded area; 14 surface counties; Dwarovrod 1,
    Khugdihr, Khugscave, Outer Khugscave not traced), `test_existing_county_missing_stops`,
    `test_west_dwarovar_connected` (new floors, Vale and Khugdihr's Anbennar provinces form one 4-connected piece),
    `test_no_floor_touches_deepwoods_or_northern_pass`, `test_no_floor_near_earlier_regions` (no `wd` pixel within
    `WALL_MARGIN` of `serp`/`seg` floors), `test_connections` (openings exactly: Fallen Asra -> 860, Chainlink Mines ->
    863, Jorkad Junction -> 3005; no opening from Azmak, Zokkorna or Eastnest; one link reaching a `c_dwarovrod_25`
    province; mouths from Amldihr, Dark Depths, Dwarfbreak and Orlazam into the Vale and from no other cave area).
  - `MapTests.test_map_files_hold_three_regions` (as Segbandal's two-region test, with `wd` appended).
- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p "test_west_dwarovar.py"` — FAIL (no module).
- [ ] **Step 3: Write the data module and wire `layouts`**; run `python -I tools/build_serpentreach.py`, read its notes
  (fit residual, clipped spills, openings, link length) and tune `FIT_BOX`/`CK3_FIT_BOX`/`OPENING_TARGETS` only if a
  test fails.
- [ ] **Step 4: Run** `test_west_dwarovar.py`, `test_serpentreach.py`, `test_segbandal.py` — PASS (the latter two's
  `test_outputs_current` must still pass; only the shared map files change, and Segbandal's map test is updated to
  expect three layouts).
- [ ] **Step 5: Commit** the data module, `build_serpentreach.py`, `build_map_graphics.py`, the tests and the
  regenerated map files: `West Dwarovar: trace caves and Serpent's Vale into the Serpentspine`.

### Task 4: Serpentreach's realm and renderers take a data module

**Files:**
- Modify: `tools/build_serpentreach.py` (`Realm`, `People`, `render_*`, `duchy_arms`, `missing_charges`)
- Test: `tools/tests/test_serpentreach.py`

**Interfaces:**
- Produces: `Realm(lay, cfg=None)`, `People(realm, names, cfg=None)` and every `render_*(..., cfg=None)` read `cfg`
  (default `data.serpentreach`) instead of the module global. `Realm` gains `existing_kingdoms` (from
  `cfg.EXISTING_KINGDOMS`, default `()`): kingdoms not rendered as titles, whose new duchies `render_titles` puts under
  `cfg.PARKING_KINGDOM`; `Realm.county` skips `type == "surface"` only where a renderer asks (`cave_counties()`).
  Character id prefix comes from `cfg.CHARACTER_PREFIX` (Serpentreach `"aov_sr"`).

- [ ] **Step 1: Run** `test_serpentreach.py` — PASS before the refactor (pins today's output).
- [ ] **Step 2: Thread `cfg` through**; Serpentreach's data module gets `CHARACTER_PREFIX = "aov_sr"`.
- [ ] **Step 3: Run** `test_serpentreach.py`, `test_serpentreach_cultures.py`, `test_segbandal.py` — PASS unchanged.
- [ ] **Step 4: Commit** `Serpentreach generator: realm, people and renderers take a data module`.

### Task 5: `build_west_dwarovar.py` — titles, de jure moves, rulers, people, provinces, terrain, regions, loc

**Files:**
- Create: `tools/build_west_dwarovar.py`
- Modify: `tools/data/west_dwarovar.py` (titles and people values)
- Test: `tools/tests/test_west_dwarovar.py` (`TitleTests`)
- Generated: `common/landed_titles/aov_west_dwarovar.txt`, `history/titles/aov_west_dwarovar.txt`,
  `history/provinces/aov_west_dwarovar.txt`, `history/characters/aov_west_dwarovar.txt`,
  `common/dynasties/aov_west_dwarovar_dynasties.txt`, `common/province_terrain/aov_west_dwarovar_terrain.txt`,
  `map_data/geographical_regions/aov_west_dwarovar_regions.txt`, `localization/english/aov_west_dwarovar_l_english.yml`

**Interfaces:**
- Consumes: `bs.Realm/People/render_*` with `cfg` (Task 4); `bsb.title_parents`, `bsb.title_holder`,
  `bsb._read_titles`, `bsb._read_history`, `bsb._scripted_arms` from `build_segbandal.py`; `bs.layouts(...)[2]`.
- Produces: `build_from_layout(anbennar, lay, eu4=EU4) -> dict[str, bytes]`, `build_all(anbennar=ANBENNAR, eu4=EU4)`,
  `main()`; data values `EMPIRE = ("e_west_dwarovar", "West Dwarovar")`, `EMPIRE_CAPITAL = "c_amldihr"`,
  `EMPIRE_COLOUR = (60, 40, 80)`, `EXISTING_KINGDOMS = ("k_khugdihr",)`, `PARKING_KINGDOM =
  "k_aov_west_dwarovar_parking"` (defined inside `e_west_dwarovar`, ends with no de jure land),
  `KINGDOM_CAPITALS` (hold counties), `KINGDOM_CULTURES` (`silver_dwarvish` for the eight, `darkscale` for
  `k_khugdihr`), `KOBOLD_KINGDOMS = {"k_khugdihr": ("darkscale", "nimrithani")}` (no rulers), `CHARACTER_PREFIX =
  "aov_wd"`, `SURFACE_HOLDINGS = ["castle_holding", "city_holding", "church_holding"]`.
- Title layout: `e_west_dwarovar` holds the eight new kingdoms in place (full chain) plus `PARKING_KINGDOM`, which holds
  `d_dwarovrod_1_3`, `d_fallen_asra`, `d_snotslair`. History at `1.1.1`: `k_khugdihr` -> `e_west_dwarovar`, the three
  parked duchies -> `k_khugdihr`, `c_dwarovrod1` -> `d_dwarovrod_1_3`.

- [ ] **Step 1: Write `TitleTests`:** `test_every_title_has_a_full_chain_at_load`, `test_de_jure_matches_areas` (every
  kept EU4 area's counties end in its duchy, every duchy in the table's kingdom, `k_khugdihr` in `e_west_dwarovar`,
  parking kingdom empty), `test_duchies_list_capital_first`, `test_holders` (emperor holds `k_amldihr`/`d_amldihr`;
  each dwarven kingdom's holder is its hold duke; no holder line for any `k_khugdihr` title or county),
  `test_khugdihr_untouched` (no province history for Khugdihr's Anbennar baronies; new `k_khugdihr` baronies are
  `darkscale`/`nimrithani`), `test_khugdihr_holder_appears_stops` (a fake Anbennar history giving `c_khugdihr` a
  holder raises `GeneratorError`), `test_vale_terrain_and_holdings` (spec §3 terrain per Vale county; castle, city,
  church), `test_every_new_key_has_loc`, `test_outputs_current`.
- [ ] **Step 2: Run** `test_west_dwarovar.py` — FAIL.
- [ ] **Step 3: Implement** the generator; `check_new_keys` stops on a key Anbennar has; the Khugdihr guard reads
  `title_holder` for every `k_khugdihr` title.
- [ ] **Step 4: Run** `python -I tools/build_west_dwarovar.py`, then `test_west_dwarovar.py` — PASS.
- [ ] **Step 5: Commit** generator, data, tests and generated files: `West Dwarovar: titles, history,
  people and loc under e_west_dwarovar`.

### Task 6: Arms

**Files:**
- Create (imported once): `gfx/coat_of_arms/textured_emblems/aov_{amldihr,dur_vazhatun,orlazam_az_dihr,mithradhum,
  er_natvir,khugdihr,haraz_orldhum,verkal_kozenad,hul_jorkad}.dds`
- Modify: `tools/data/west_dwarovar.py` (`KINGDOM_ARMS`, `DUCHY_CHARGES`), `tools/build_west_dwarovar.py`
- Test: `tools/tests/test_west_dwarovar.py` (`TitleTests.test_arms`)
- Generated: `common/coat_of_arms/coat_of_arms/aov_west_dwarovar.txt`

**Interfaces:**
- `KINGDOM_ARMS`: kingdom -> (EU4 tag, map colour, flag's most common colour): I01 Amldihr, I03 Dûr-Vazhatun, I04
  Orlazam-az-dihr, I05 Mithradhûm, I06 Er-Natvir, I07 Khugdihr (arms only; map colour stays Anbennar's), I08 Haraz
  Orldhûm, I09 Verkal Kozenad, I10 Hul-Jorkad; colours from the spec table.
- `DUCHY_CHARGES` (area -> charge, centred, as Serpentreach's): dwarovrod_1_3 `ce_anb_bridge_two_arch`, fallen_asra
  `ce_swords_crossed`, snotslair `ce_bat`, dwarovrod_4_6 `ce_wheel`, dwarfbreak `ce_india_small_dagger`, dark_depths
  `ce_wyvern`, chainlink_mines `ce_chains`, dwarovrod_7_9 `ce_anb_bridge_one_arch`, dwarovrod_10_12 `ce_pagan_wheel`,
  riftway `ce_india_small_arched_hill`, railyard_exchange `ce_anb_waterwheel`, dagrite_depths `ce_anb_crystal`,
  goblins_bypass `ce_portcullis`, skulkers_lair `ce_snake`, dwarovrod_15_17 `ce_anb_bridge_three_arch`,
  zokkorna_caverns `ce_wyvern_rising`, travelers_refuge `ce_anb_lamp`, westnest `ce_african_snake`, eastnest
  `ce_snake_fylfot`, azmak `ce_anb_skull`, dwarovrod_21_24 `ce_key`, dagrinrod_4_6 `ce_anb_aramari_horseshoe`,
  dagrinrod_7_9 `ce_bull_horn`, broken_dagger_pass `ce_india_small_dagger_02`, old_dagrinrod `ce_ram_horn`,
  dagrinrod_13_15 `ce_tower`, royal_terrace `ce_crown`, common_terrace `ce_sheep`, assembly_terrace `ce_bell`,
  castle_hill `ce_castle` (all `.dds`; 30 = every new non-hold duchy).

- [ ] **Step 1: Import the nine flags:** `python -I tools/eu4_import.py convert gfx/flags/<tag>.tga
  gfx/coat_of_arms/textured_emblems/aov_<kingdom key without k_>.dds --upscale2x --mips` for each tag above.
- [ ] **Step 2: Write `test_arms`:** each dwarven kingdom, its hold duchy and hold county use its flag emblem;
  `k_khugdihr`, `d_khugdihr`, `c_khugdihr` use I07's; each of the 30 duchies its charge; the build stops when Anbennar
  scripts arms for any of these keys or a charge is found nowhere (`bs.missing_charges`).
- [ ] **Step 3: Run** — FAIL; **implement** the arms renderer (Serpentreach's `render_arms` with `cfg`, plus the
  Khugdihr keys); rerun the generator; **run** — PASS.
- [ ] **Step 4: Commit** emblems, data, generator, tests, arms file: `West Dwarovar: EU4 hold flags and duchy arms`.

### Task 7: Holds

**Files:**
- Modify: `tools/data/holds.py`, `events/aov_hold_delve_events.txt`, `events/aov_hold_ruin_events.txt`,
  `common/decisions/aov_hold_decisions.txt` and their loc (options 17-24 copied from option 16)
- Test: `tools/tests/test_build_holds.py`

**Interfaces:**
- New `_hold` entries (name, EU4 id, county, barony = the county's capital barony key from the layout, level):
  Amldihr 4119 `c_amldihr` 2; Haraz Orldhûm 2868 `c_haraz_orldhum` 1; Mithradhûm 4236 `c_mithradhum` 1; Er-Natvir 2931
  `c_er_natvir` 1; Verkal Kozenad 4056 `c_verkal_kozenad` 1; Hul-Jorkad 2963 `c_hul_jorkad` 1; Orlazam-az-dihr 4147
  `c_orlazam_az_dihr` 1; Dûr-Vazhatun 4020 `c_dur_vazhatun` 1; none ruined. Khugdihr unchanged (`ruined=True`).

- [ ] **Step 1: Extend the holds tests** so each new hold's county and barony exist in the generated titles and the
  pickers have 24 options.
- [ ] **Step 2: Run** `test_build_holds.py` — FAIL; **add** the entries and picker options; run
  `python -I tools/build_holds.py`; **run** — PASS.
- [ ] **Step 3: Commit** `West Dwarovar: eight holds join the dwarven holds`.

### Task 8: Look — carve with Khugdihr, Vale paint, gates, fog

**Files:**
- Modify: `tools/carved_ranges.py` (`carve`), `tools/serpentreach_layout.py` (`paint_surface`),
  `tools/build_map_graphics.py` (`carved_ranges`, `build_terrain_fill`, `serpentreach_sites`, gate sites for mouths),
  `tools/data/map_graphics.py` (`CARVED_RANGES = ("c_seghdihr", "c_khugdihr")`, `SURROUND_BOX = (1400, 300, 2540,
  1350)`), `tools/data/west_dwarovar.py` (`AREA_STYLES = {"westnest_area": "mushroom", "eastnest_area": "mushroom",
  "zokkorna_caverns_area": "mushroom"}`, `SURFACE_MATERIALS = {"farmlands": "farmland_01", "plains": "plains_01",
  "hills": "hills_01", "wetlands": "wetlands_02"}`, `SURFACE_FEATHER = 4`)
- Test: `tools/tests/test_build_map_graphics.py`, `tools/tests/test_carved_ranges.py`
- Generated: every `build_map_graphics.py` output (heightmap files, blend maps, gates, surround mask)

**Interfaces:**
- `cr.carve(grid, floor, terrain, rock, pm, water, ramp, ground_radius=None, land=None)`: `land` ({(x, y): province})
  counts as passable land for the ramp (the Vale's pixels).
- `carved_ranges()`: for `c_khugdihr`, the floor adds `wd.owner` minus surface counties' pixels; kinds add their
  county types; `land` = the Vale's pixels.
- `sl.paint_surface(index, intensity, lay, materials, feather) -> (index, intensity)`: surface counties at full weight,
  feathered into the existing paint over `feather` px.
- Gate sites: `gate_sites_for_openings(wd, titles)` plus one per `wd.mouths` (normal county = the Vale county's key,
  read from the layout since Anbennar's titles lack it); all pinned to turn 0 like Serpentreach's.

- [ ] **Step 1: Write the tests:** `test_khugdihr_range_carved` (Khugdihr's Anbennar floor pixels and the new cave
  floors are flat at the range base +/- terraces), `test_vale_heights_untouched` (every surface pixel's height equals
  the pre-carve grid's), `test_vale_mouth_ramps` (floor pixels within `CARVE_RAMP` of a Vale pixel lie between floor and
  Vale height), `test_vale_painted` (surface pixels carry their `SURFACE_MATERIALS` material),
  `test_west_dwarovar_gates` (a gate per opening and per mouth; none on the Dwarovrod 24-25 link),
  `test_surround_clears_vazhatun` (mask fog channel 0 at Dûr-Vazhatun's hold pixel, still > 0 at Krakdhum's), and
  `cr.carve` with `land` on a synthetic grid.
- [ ] **Step 2: Run** `test_build_map_graphics.py` and `test_carved_ranges.py` — new tests FAIL.
- [ ] **Step 3: Implement**; run `python -I tools/build_holding_models.py` then `python -I tools/build_map_graphics.py`
  and read the notes (range base for `c_khugdihr`, gate count 13 + new, fog px).
- [ ] **Step 4: Run** both test files — PASS; Segbandal's carve tests still PASS.
- [ ] **Step 5: Commit** code, data, tests and generated map files: `West Dwarovar: carve with Khugdihr, paint the Vale,
  gates, fog pulled off Dûr-Vazhatun`.

### Task 9: Docs, full rebuild, validation

**Files:**
- Create: `docs/systems/west-dwarovar.md` (generated-files table, system notes, in-game checklist from the spec's risks)
- Modify: `docs/systems/updating.md` (order: `build_serpentreach.py`, `build_segbandal.py`, `build_west_dwarovar.py`,
  `build_rie_elves.py`, `build_holds.py`, `build_holding_models.py`, `build_map_graphics.py`), `CLAUDE.md` (systems
  row), `docs/systems/map-graphics.md` (carved ranges, fog box), `docs/systems/serpentreach.md` (three layouts),
  `docs/systems/dwarven-holds.md` (24 holds)

- [ ] **Step 1: Rerun the chain** in the order above; `git status` shows no change after a second full run.
- [ ] **Step 2: Run all tool tests** `python -I -m unittest discover -s tools/tests` — PASS.
- [ ] **Step 3: Validate** `python -I tools/validate.py` — no new reports for the `aov_west_dwarovar` files (anything
  else is checked against `docs/systems/validation-baseline.md`, never baselined unasked).
- [ ] **Step 4: Write the docs**, then commit: `West Dwarovar: docs, full rebuild`.
- [ ] **Step 5: In-game checklist** (for the user): map loads with the new ids; locators on floors and in the Vale;
  `e_west_dwarovar` with nine kingdoms in the de jure map mode, no parking title visible; Khugdihr kobold and unheld;
  floors versus the Vale (ramp, risk 2-3); gates face the right way; Dûr-Vazhatun out of the fog.
