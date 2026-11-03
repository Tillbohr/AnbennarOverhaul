# Segbandal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Anbennar's Segbandal (`e_middle_dwarovar`) with EU4's 37 missing provinces traced into the rock
around it, and regroup the whole region into EU4-area duchies under one kingdom per hold.

**Architecture:** The Serpentreach tracer (`tools/serpentreach_layout.py`) is parameterised by a region data module,
learns to skip provinces Anbennar already has and to let new floors touch only their EU4 neighbours; `build_serpentreach.py`
draws both regions into the shared map files; a new `build_segbandal.py` writes Segbandal's titles, history, people,
arms and localization, linking to Anbennar's titles only through history `de_jure_liege`; `build_map_graphics.py`
carves and paints the new floors with the existing Segbandal carve.

**Tech Stack:** Python 3 standard library only (`python -I`), CK3 script/loc files (UTF-8 BOM, LF, tabs), unittest.

**Spec:** `docs/superpowers/specs/2026-11-03-segbandal-design.md` (read it first; the duchy table there is normative).

## Global Constraints

- Never write to `../anbennar-ck3-dev-master`; no landed-title, culture or history file of Anbennar is overridden.
- Generated files are never edited by hand; every value lives in `tools/data/segbandal.py`.
- Script and loc files: UTF-8 with BOM, LF, tabs; generated files start with the generator's `header_lines()`.
- Serpentreach's own titles, history, people and arms stay byte-identical; only the shared map files
  (`provinces.png`, `definition.csv`, 8 locator files) gain Segbandal.
- Segbandal's province ids start right after Serpentreach's last id; colours never repeat an existing one.
- New keys: `k_gor_vazumbrog`; duchies `d_<slug of EU4 area name>`; counties `c_<slug of EU4 name>`; baronies
  `b_<county slug>`, `_2`..; a key Anbennar already has stops the build.
- Reused Anbennar duchies: `d_hehodovar`, `d_hehorod`, `d_seghdihr`, `d_verkal_gulan`, `d_xazorod`, `d_gor_ozumbrog`;
  emptied: `d_seghrod`, `d_gulanrod`, `d_ozumrod`; `d_heros_vale` untouched.
- Cultures: Gor Vazumbrog `titanium_dwarvish`, Hehodovar `pyrite_dwarvish`, Seghdihr `citrine_dwarvish`, Verkal Gulan
  `gold_dwarvish`, Gor Ozumbrog `topaz_dwarvish`; religion `ancestor_worship`.
- `k_gor_vazumbrog` colour (146, 160, 161), arms EU4 I14 flag; Seghdihr and Verkal Gulan's new duchies held by
  elders, the other kingdoms' new land unheld.
- Run tests with `python -I -m unittest discover -s tools/tests -p "<pattern>"` (never `-v` on the whole suite).

## Review Focus

1. **An Anbennar update renames or moves a Segbandal road county** — the build must stop naming the `EXISTING` entry,
   not trace a duplicate. (Task 2, `test_existing_county_missing_stops`.)
2. **A traced cavern grazes a road EU4 does not join it to** (fit error is up to 56 px) — it must keep 4 px of rock, or
   players get a passage EU4 lacks. (Task 2, `test_floor_keeps_margin_from_non_neighbours`.)
3. **A new county ends up touching nothing it can reach** — the build must add a link corridor or stop, never ship an
   unreachable county. (Task 2, `test_every_new_county_reaches_a_neighbour`.)
4. **Serpentreach silently renumbered or recoloured** by the refactor — its outputs must stay byte-identical.
   (Task 1, `test_serpentreach_unchanged`.)
5. **A de jure move leaves a county in the wrong duchy or an Anbennar duchy half-emptied** — every EU4 area's counties
   end in its duchy; the three emptied duchies end with none. (Task 4, `test_de_jure_matches_areas`.)

---

### Task 1: Tracer takes a region data module

**Files:**
- Modify: `tools/serpentreach_layout.py` (every `data.` read inside `layout`, `_opening`, `rock_provinces`,
  `check_terrain_data`, `province_materials`, `used_materials`, `floor_heights`, `carve`, `paint`)
- Test: `tools/tests/test_serpentreach.py`

**Interfaces:**
- Produces: `layout(anbennar, eu4, ck3=None, cfg=None, first_id=None, used=None) -> Layout` — `cfg` defaults to
  `data.serpentreach`; `first_id` defaults to `max(definition ids) + 1`; `used` (set of RGB tuples) is added to the
  colours already in `definition.csv`. `Layout` gains a trailing field `links` (list of `Opening`, default `()`).
  `rock_provinces(cfg=None)`, `province_materials(lay, cfg=None)`, `used_materials(cfg=None)`; all other helpers take
  `cfg` where they read data.
- Every other caller keeps working unchanged (defaults = Serpentreach).

- [ ] **Step 1: Write `test_serpentreach_unchanged`** in `RealLayoutTests` (skip when EU4 is not installed, as the
  file's other real tests do): `build_serpentreach.build_all()` equals the committed files byte for byte for every
  path it returns.
- [ ] **Step 2: Run it before the refactor:** `python -I -m unittest discover -s tools/tests -p "test_serpentreach.py"`
  — expect PASS (it pins today's output).
- [ ] **Step 3: Thread `cfg`, `first_id`, `used` through the tracer**; add `links` to `Layout` with
  `namedtuple(..., defaults=((),))`.
- [ ] **Step 4: Rerun** the same command — expect PASS (29 + 1 tests).
- [ ] **Step 5: Commit** `git add tools/serpentreach_layout.py tools/tests/test_serpentreach.py` /
  `git commit -m "Serpentreach tracer: region data module as a parameter"`

### Task 2: Segbandal data and trace

**Files:**
- Create: `tools/data/segbandal.py`
- Modify: `tools/serpentreach_layout.py` (`layout`, new helpers below)
- Test: `tools/tests/test_segbandal.py`

**Interfaces:**
- Consumes: Task 1's `layout(..., cfg=...)`.
- Produces in `tools/data/segbandal.py` (Serpentreach's values imported where the spec says "as Serpentreach":
  `WALL_MARGIN`, `SMOOTH_*`, `OPENING_WIDTH`, `OPENING_REACH`, `MIN_BARONY_PX`, `MIN_FRAGMENT_PX`, `BARONIES`,
  `BARONY_SUFFIXES`, `HOLDINGS`, `TERRACE*`, `WALL_*`, `MIN_WALL`, `CARVE_GROUND_RADIUS`, `TERRAIN_STYLES`,
  `DUCHY_SHADES`, `COUNTY_JITTER`, `DUCHY_PATTERNS`, `CHARGE_*`, `PALE_FIELD`, `ELDER_*`, `SON_BIRTH`, `START`,
  `RELIGION`):
  - `REGION = "middle_dwarovar_region"`, `SOURCE_PROVINCE = 2608`, `FIT_BOX = (3300, 560, 3950, 860)`,
    `CK3_FIT_BOX = (3300, 1250, 5200, 2150)`, `OPENING_CUT_THROUGH = ()`, `BARONY_OVERRIDES = {}`,
    `OPENING_TARGETS = {}`;
  - `NO_LINK_REGIONS = ("west_dwarovar_region", "serpentreach_region")` — contacts with these make no opening;
  - `EXISTING`: EU4 id -> Anbennar county: 2889..2895, 4027, 4231, 4091, 4111..4114, 4090 as `c_dwarovrodN` by their
    EU4 number (`Dwarovrod | N |`), 4082 `c_seghrod`, 4078 `c_hehodovar`, 4124 `c_seghdihr`, 2914 `c_verkal_gulan`,
    4218 `c_gor_ozumbrog` (20 entries);
  - `AREA_ORDER`: the 18 areas west to east as in the spec's duchy table;
  - `AREA_DUCHIES`: area -> (duchy key, kingdom key, reused: bool), exactly the spec's table;
  - `KINGDOMS`: kingdom -> (name, [areas]) derived from `AREA_DUCHIES` (the tracer's area check reads it).
- Produces in the tracer: `county_provinces(titles_text) -> {county key: set of province ids}` (from
  `dm.province_titles`); `allowed_neighbours(eu4_adjacency, existing, county_provinces) -> {eu4 id: set of CK3
  province ids}`; Layout `links` (corridors from a new county to a CK3 province of an existing EU4 neighbour, built
  with `_opening`, pixels added to the county's capital barony).

- [ ] **Step 1: Write the failing tests** in `tools/tests/test_segbandal.py`:
  - `test_existing_names_match_anbennar`: every `EXISTING` county exists in Anbennar's landed titles under
    `e_middle_dwarovar`, and the EU4 name of each id slugs to it (holds via `HOLDS`).
  - `test_area_duchies_cover_region`: `AREA_DUCHIES` keys == the region's 18 areas; reused duchies are exactly the
    six of Global Constraints.
  - `test_existing_county_missing_stops`: `layout` with an `EXISTING` naming `c_nowhere` raises `GeneratorError`
    whose message contains `c_nowhere`.
  - `test_floor_keeps_margin_from_non_neighbours` (synthetic map: rock id 9, road A id 1, road B id 2; one EU4 label
    adjacent to A only, covering pixels next to both): floor touches A, and no floor pixel is within
    `WALL_MARGIN` of B.
  - Real (skip without EU4): `test_every_new_county_reaches_a_neighbour` (each new county's pixels 4-touch a province of
    an allowed neighbour or another new county); `test_segbandal_connected` (new floors ∪ Anbennar Segbandal
    provinces form one 4-connected piece); `test_counts` (37 counties, 71 provinces, ids contiguous from
    `first_id`); `test_only_rock_changes` (every floor pixel was 2608 on Anbennar's map).
- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p "test_segbandal*.py"` — expect FAIL/ERROR
  (no module `data.segbandal`).
- [ ] **Step 3: Write `tools/data/segbandal.py`** with the values above.
- [ ] **Step 4: Extend `layout`:** skip `EXISTING` ids when tracing; collect EU4 adjacency between region provinces
  while scanning contacts; replace the single "near any other province" margin with a per-label test: a pixel
  labelled `a` is floor only if every non-source province within `WALL_MARGIN` of it is in `allowed[a]`; contacts with
  `EXISTING` provinces or `NO_LINK_REGIONS` provinces make no opening; after the split, a new county that 4-touches no
  allowed province and no other new county gets a link corridor to its nearest allowed province (stop if none within
  `OPENING_REACH`); the connectivity check covers new floor ∪ the pixels of `EXISTING` counties' provinces (Serpentreach,
  with `EXISTING = {}`, keeps today's check). Serpentreach's data gains `EXISTING = {}` and `NO_LINK_REGIONS = ()`.
- [ ] **Step 5: Run** the Segbandal tests and `test_serpentreach.py` — expect PASS (Serpentreach unchanged).
- [ ] **Step 6: Commit** `git add tools/data/segbandal.py tools/data/serpentreach.py tools/serpentreach_layout.py tools/tests/test_segbandal.py` /
  `git commit -m "Segbandal: trace EU4's missing provinces around Anbennar's"`

### Task 3: Both regions on the map

**Files:**
- Modify: `tools/build_serpentreach.py` (`build_all`, `build_from_layout`, `main`, `render_definition`,
  `render_provinces`, `render_locators`)
- Create (imported once): `gfx/coat_of_arms/textured_emblems/aov_gor_vazumbrog.dds`
- Test: `tools/tests/test_segbandal.py`

**Interfaces:**
- Consumes: Task 2's `layout(..., cfg=segbandal, first_id=..., used=...)`.
- Produces: `layouts(anbennar, eu4, ck3=None) -> (serpentreach Layout, segbandal Layout)` in `build_serpentreach.py`
  (Segbandal's `first_id` = Serpentreach's max id + 1, `used` = Serpentreach's colours); `render_definition(original,
  lays)`, `render_provinces(png, lays)`, `render_locators(anbennar, lays)` take a list of layouts.

- [ ] **Step 1: Write the failing tests:** `test_map_files_hold_both_regions` (generated `definition.csv` rows after
  Anbennar's are Serpentreach's ids then Segbandal's, no colour repeated in the whole file; each locator file has one
  instance per new province of both regions); `test_serpentreach_ids_unchanged` (Serpentreach's first and last id equal
  the committed `definition.csv`'s).
- [ ] **Step 2: Run** the Segbandal tests — expect FAIL.
- [ ] **Step 3: Import the flag:** `python -I tools/eu4_import.py convert gfx/flags/I14.tga gfx/coat_of_arms/textured_emblems/aov_gor_vazumbrog.dds --upscale2x --mips`.
- [ ] **Step 4: Implement `layouts` and the list-taking renderers**; `main` prints both layouts' notes.
- [ ] **Step 5: Run** `python -I tools/build_serpentreach.py`, then the Segbandal and Serpentreach tests — expect PASS.
- [ ] **Step 6: Commit** the generator, the emblem and the regenerated map files /
  `git commit -m "Serpentreach generator draws Segbandal into the shared map files"`

### Task 4: Segbandal titles, history and people (`tools/build_segbandal.py`)

**Files:**
- Create: `tools/build_segbandal.py`; outputs `common/landed_titles/aov_segbandal.txt`,
  `history/titles/aov_segbandal.txt`, `history/provinces/aov_segbandal.txt`, `history/characters/aov_segbandal.txt`,
  `common/dynasties/aov_segbandal_dynasties.txt`, `common/province_terrain/aov_segbandal_terrain.txt`,
  `map_data/geographical_regions/aov_segbandal_regions.txt`, `localization/english/aov_segbandal_l_english.yml`,
  `common/coat_of_arms/coat_of_arms/aov_segbandal.txt`
- Modify: `tools/data/segbandal.py` (add `KINGDOM_CULTURES`, `NEW_KINGDOM = ("k_gor_vazumbrog", "Gor Vazumbrog",
  "I14", (146, 160, 161), <I14 flag's most common colour>)`, `DUCHY_CHARGES` for the 11 new duchies other than
  `d_vazumbrog` (12 new duchies in all), `ELDER_KINGDOMS = ("k_seghdihr", "k_verkal_gulan")`)
- Test: `tools/tests/test_segbandal.py`

**Interfaces:**
- Consumes: `build_serpentreach.layouts`, and its helpers `header_lines`, `_text`, `_hash`, `life_date`, `rgb_text`,
  `shade`, `male_names`, `check_new_keys`, `duchy_arms` (give `duchy_arms` a `charges` parameter, default Serpentreach's).
- Produces: `anbennar_county_duchies(titles_text) -> {county: duchy}`; `title_holder(history_text, title) -> (date,
  holder id)` (first holder entry; stops when absent); `build_all(anbennar=ANBENNAR, eu4=EU4) -> {rel path: bytes}`.

- [ ] **Step 1: Write the failing tests:**
  - `test_de_jure_matches_areas`: applying the generated `de_jure_liege` lines to Anbennar's county -> duchy map puts
    every Segbandal county (old and new) in its EU4 area's duchy; `d_seghrod`, `d_gulanrod`, `d_ozumrod` end with no
    county; `d_heros_vale` keeps `c_heros_vale`.
  - `test_new_duchies_list_capital_first`: each new duchy's first county is its hold (Gor Vazumbrog) or its first
    county in EU4 order.
  - `test_new_titles_link_by_history`: every top-level duchy/county in `aov_segbandal.txt` (and `k_gor_vazumbrog`) has
    a `1.1.1 = { de_jure_liege = ... }` in the title history; no Anbennar key is redefined.
  - `test_holders`: elders hold exactly the new duchies with new counties in `ELDER_KINGDOMS` (`d_steamsource`,
    `d_stunad_kradoz`, `d_goblin_grotto`, `d_greatcavern`, `d_xazor`) from 860.1.1, become `liege` of their kingdom
    at that kingdom holder's first date (`title_holder`); Stonewall and Easthollow are held by `d_seghdihr`'s holder
    from its date; nothing in Hehodovar, Gor Ozumbrog or Gor Vazumbrog is held.
  - `test_cultures`: every new barony's culture is its kingdom's from Global Constraints.
  - `test_arms`: `k_gor_vazumbrog`, `d_vazumbrog`, `c_gor_vazumbrog` use `aov_gor_vazumbrog.dds`; the other new
    duchies have a `DUCHY_CHARGES` entry; no Anbennar title appears.
  - `FreshnessTests.test_outputs_current`: `build_all()` equals the committed files.
- [ ] **Step 2: Run** the Segbandal tests — expect FAIL.
- [ ] **Step 3: Implement `build_segbandal.py`** following `build_serpentreach.py`'s structure: titles (spec §2: new
  kingdom block; other new duchies and the reused duchies' new counties at top level), title history (de jure moves of
  Anbennar counties computed from `anbennar_county_duchies` vs `AREA_DUCHIES`, so an Anbennar change follows
  automatically), people for the elder duchies (prefix `aov_sb_`), province history, terrain, region
  `world_segbandal` (the 18 duchies), loc (EU4 names; `Dwarovrod | 27 |` -> `Dwarovrod 27`; area `|27-29|` ->
  `27-29`), arms, colours (new duchies shade their kingdom's Anbennar colour, parsed from Anbennar's landed titles).
- [ ] **Step 4: Run** `python -I tools/build_segbandal.py`, then the tests — expect PASS.
- [ ] **Step 5: Commit** generator, data, outputs, tests / `git commit -m "Segbandal: EU4-area duchies, Gor Vazumbrog and rulers"`

### Task 5: Gor Vazumbrog joins the dwarven holds

**Files:**
- Modify: `tools/data/holds.py` (`_hold("Gor Vazumbrog", 4217, "c_gor_vazumbrog", "b_gor_vazumbrog", 2)` after the
  Serpentreach holds, under a `# Segbandal (tools/build_segbandal.py makes these titles)` comment; docstring 16 holds)
- Regenerate: `python -I tools/build_holds.py`, `python -I tools/build_holding_models.py`
- Test: the existing `test_build_holds*.py`, `test_build_holding_models*.py`

- [ ] **Step 1: Add the hold and rerun both generators.**
- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p "test_build_hold*.py"` — expect PASS (fix
  count assertions that pin 15 holds to 16, nothing else).
- [ ] **Step 3: Commit** / `git commit -m "Dwarven holds: Gor Vazumbrog"`

### Task 6: Carve, paint and gate the new floors

**Files:**
- Modify: `tools/build_map_graphics.py` (`carved_ranges`, `build_heightmap`, `build_terrain_fill`, a cached
  `segbandal_layout(roots)` from `build_serpentreach.layouts`), `tools/data/segbandal.py` (`AREA_STYLES =
  {"steamsource_area": "volcanic", "deep_ones_lair_area": "mushroom", "ulagom_area": "garnet"}`)
- Test: `tools/tests/test_build_map_graphics.py`, `tools/tests/test_carved_ranges.py`

**Interfaces:**
- Consumes: Segbandal `Layout` (`owner`, `counties`, `openings`), `sl.province_materials(lay, cfg)`.
- Produces: `carved_ranges` entries whose floor is Anbennar's range ∪ Segbandal's `owner` and whose terrain maps the
  new province ids to their county type; materials per province (new ones by `AREA_STYLES`, Anbennar's `default`).

- [ ] **Step 1: Write the failing tests:** `test_segbandal_floor_carved` (in `HeightOutputsTests`: every Segbandal new
  floor pixel sits at the carved ground +/- one terrace step); `test_segbandal_gates` (one gate note per Segbandal
  opening); `test_segbandal_floors_painted` (a Steamsource floor pixel carries `hardened_lava`'s index).
- [ ] **Step 2: Run** `python -I -m unittest discover -s tools/tests -p "test_build_map_graphics*.py"` — expect FAIL.
- [ ] **Step 3: Implement:** union the floors in `carved_ranges`; Segbandal openings join `sr_sites` (gate sites,
  turn pinned 0, `drop_pieces_on_floor`); paint by area style.
- [ ] **Step 4: Run** `python -I tools/build_map_graphics.py` (background, ~5 min), then the map-graphics and
  carved-range tests — expect PASS; update `test_notes_cover_ranges_and_sites`' gate count by Segbandal's openings.
- [ ] **Step 5: Render a before/after preview** of the carved region into `art_work/segbandal_reworked_preview.png`
  (the scratch renderer from the carve preview) and look at it.
- [ ] **Step 6: Commit** / `git commit -m "Map graphics: carve and paint Segbandal's new caverns"`

### Task 7: Docs, full rebuild, validation

**Files:**
- Create: `docs/systems/segbandal.md` (generated-file table, system notes, in-game checklist from the spec's risks)
- Modify: `docs/systems/updating.md` (order: `build_serpentreach.py`, `build_segbandal.py`, then holds, holding
  models, map graphics), `docs/systems/map-graphics.md` (carved ranges include Segbandal's new floors),
  `docs/systems/serpentreach.md` (the generator also draws Segbandal), `CLAUDE.md` (systems row for Segbandal)

- [ ] **Step 1: Write the docs.**
- [ ] **Step 2: Rebuild in order and confirm nothing else changes:** `build_serpentreach.py`, `build_segbandal.py`,
  `build_holds.py`, `build_holding_models.py`, `build_map_graphics.py`; `git status` shows only expected paths.
- [ ] **Step 3: Validate:** `python -I tools/validate.py` — expect no new reports; read any that name `aov_segbandal`.
- [ ] **Step 4: Run all tool tests:** `python -I -m unittest discover -s tools/tests` — expect OK.
- [ ] **Step 5: Commit** / `git commit -m "Segbandal: docs and full rebuild"`
