# Segbandal design

EU4 Anbennar's `middle_dwarovar_region` (Segbandal, 18 areas, 57 provinces) completed on the CK3 map: the provinces
Anbennar lacks are traced into the rock around Anbennar's own Segbandal, and the whole region gets Serpentreach's duchy
treatment (EU4 areas as duchies, a kingdom per hold, arms, colours, rulers, terrain styles).

## Intent

- **User asked:** compare CK3 Segbandal with EU4's; rework the region by adding the caves and missing provinces; give it
  the duchy treatment Serpentreach got. Segbandal was carved like Serpentreach earlier the same day
  (`tools/carved_ranges.py`, `CARVED_RANGES = ("c_seghdihr",)`).
- **User chose:**
  - *Add around Anbennar's:* Anbennar's 54 Segbandal provinces, ids, baronies and titles stay. Only the EU4 provinces
    Anbennar lacks are traced, into impassable province 2608. Counties are regrouped by history (`de_jure_liege`), never
    by overriding Anbennar's landed titles.
  - *Rulers follow each kingdom:* the new duchies of the held kingdoms (Seghdihr, Verkal Gulan) get a dwarf elder and his
    son as the king's vassals. The new duchies of the unheld kingdoms (Hehodovar, Gor Ozumbrog, Gor Vazumbrog) stay unheld.
  - *Gor Vazumbrog's arms* are EU4's I14 "Gor Vazumbrog" flag (`gfx/flags/I14.tga`).
- **Success:** the game loads; Segbandal has EU4's 57 provinces (Anbennar's 20 equivalents plus 37 new counties) in
  carved, flat-floored halls; every EU4 area is a duchy under its hold's kingdom; no Anbennar file is overridden for
  titles; the generators rebuild everything after an Anbennar update.

## The comparison

| | EU4 `middle_dwarovar_region` | CK3 Anbennar `e_middle_dwarovar` |
|---|---|---|
| Provinces | 57 in 18 areas | 54 in 10 duchies, 4 kingdoms |
| Holds | Gor Vazumbrog 4217, Hehodovar 4078, Seghdihr 4124, Verkal Gulan 2914, Gor Ozumbrog 4218 | the last four |
| Roads | Dwarovrod 25-44, Seghrod | Dwarovrod 30-44 (two baronies each), Seghrod |
| Caverns | 31 | none |
| Surface | | Hero's Vale (2915, 6770) |

An affine fit on 33 provinces both maps share (median error 22 px, max 56) puts EU4's roads 30-37 and holds on
Anbennar's, and every missing province on 2608 (Ulagom Canyon spills 106 px onto 2426, clipped). Overlay:
`art_work/segbandal_eu4_overlay.png` (git-ignored).

**Equivalents** (`EXISTING`, matched by name): EU4 `Dwarovrod | N |` -> `c_dwarovrodN` (N 30-44), Seghrod ->
`c_seghrod`, the four holds -> their `HOLDS` counties. **New (37 counties):** Gor Vazumbrog (hold), Dwarovrod 25-29
(roads), 31 caverns. Baronies as Serpentreach (`BARONIES`: hold 4, cavern 2, road 1): 4 + 5 + 62 = 71 new provinces.

## §1 Map (`tools/serpentreach_layout.py`, data `tools/data/segbandal.py`)

- **One tracer, two regions.** `serpentreach_layout.layout` takes the region's data module (`cfg`), defaulting to
  Serpentreach's, so both regions share the fit, smoothing, k-means barony split, ids, colours and openings. Segbandal's
  module sets `REGION = "middle_dwarovar_region"`, `SOURCE_PROVINCE = 2608`, its `FIT_BOX`/`CK3_FIT_BOX`, `AREA_ORDER`,
  `EXISTING`, and reuses Serpentreach's values elsewhere (imported, so the look stays the same).
- **Skip the equivalents:** EU4 provinces in `EXISTING` are not traced; their pixels stay 2608 rock (Anbennar's own
  provinces sit next to them already).
- **Clip and wall:** a pixel becomes floor only on 2608, and at least `WALL_MARGIN` (4) px from every other province
  **except** its *allowed neighbours*: the CK3 provinces of its EU4 neighbours' equivalents, and other new Segbandal
  provinces (whose shared borders come from the trace). So a cavern opens onto the road EU4 joins it to and onto nothing
  else.
- **Links:** a new county whose floor touches none of its EU4 neighbours (old or new) gets a corridor `OPENING_WIDTH`
  wide to the nearest of them (the same corridor code as openings, its pixels the county's capital barony). The build
  stops if Segbandal (old and new provinces) is not one connected piece.
- **Openings:** EU4 contacts with land outside the region that is not another Dwarovar region (West Dwarovar and
  Serpentreach are not linked, as decided for Serpentreach) get corridors and gates, as in Serpentreach;
  `OPENING_TARGETS` overrides the target.
- **Ids:** Segbandal's new provinces follow Serpentreach's last id, in `AREA_ORDER` (fixed) then EU4 province order,
  capital barony first. A Serpentreach barony change renumbers Segbandal; a test pins both id ranges.
- **Outputs:** `build_serpentreach.py` draws both regions into the one `provinces.png`, `definition.csv` and locator
  overrides it already writes.
- **Build stops on:** a changed pixel that was not 2608 (Segbandal) or 2426 (Serpentreach); a county under
  `MIN_BARONY_PX` per barony; a barony not 4-connected; a floor touching a province that is not an allowed neighbour;
  an `EXISTING` entry whose county Anbennar lacks.

## §2 Titles and history (new `tools/build_segbandal.py`)

**Duchies (18, one per EU4 area).** Anbennar duchies are reused where their capital county stays in them:

| EU4 area | Duchy | Kingdom |
|---|---|---|
| vazumbrog | `d_vazumbrog` (new; Gor Vazumbrog first) | `k_gor_vazumbrog` (new) |
| dwarovrod_27_29 | `d_dwarovrod_27_29` (new) | Gor Vazumbrog |
| misty_cave_trail | `d_misty_cave_trail` (new) | Gor Vazumbrog |
| hehos_legacy | `d_hehodovar` (Anbennar) | `k_hehodovar` |
| dwarovrod_30_32 | `d_hehorod` (Anbennar; gains `c_dwarovrod32`) | Hehodovar |
| deep_ones_lair | `d_deep_ones_lair` (new) | Hehodovar |
| diggers_road | `d_diggers_road` (new) | Hehodovar |
| seghdihr | `d_seghdihr` (Anbennar; gains `c_seghrod`) | `k_seghdihr` |
| dwarovrod_33_35 | `d_dwarovrod_33_35` (new; `c_dwarovrod33`-`35`) | Seghdihr |
| steamsource | `d_steamsource` (new) | Seghdihr |
| stunad_kradoz | `d_stunad_kradoz` (new) | Seghdihr |
| goblin_grotto | `d_goblin_grotto` (new) | Seghdihr |
| verkal_gulan | `d_verkal_gulan` (Anbennar; gains `c_dwarovrod36`, `37`) | `k_verkal_gulan` |
| greatcavern | `d_greatcavern` (new) | Verkal Gulan |
| xazor | `d_xazor` (new) | Verkal Gulan |
| dwarovrod_38_41 | `d_xazorod` (Anbennar; gains `c_dwarovrod38`, loses `42`) | `k_gor_ozumbrog` |
| ozumbrog | `d_gor_ozumbrog` (Anbennar; gains `c_dwarovrod42`-`44`) | Gor Ozumbrog |
| ulagom | `d_ulagom` (new) | Gor Ozumbrog |

`d_heros_vale` stays in Verkal Gulan. Anbennar's `d_seghrod`, `d_gulanrod` and `d_ozumrod` are left with no counties
(keys stay; they no longer show on the map).

- **`common/landed_titles/aov_segbandal.txt`:** `k_gor_vazumbrog` with its three duchies and their counties; every other
  new duchy at top level with its new counties; the new counties of reused Anbennar duchies (Stonewall, Easthollow,
  Hehogrim's Mausoleum, Bahged Breach) at top level. Keys `c_<slug of EU4 name>`, `b_<county slug>`, `_2`.. as
  Serpentreach. A key Anbennar already has stops the build. Each new duchy lists its capital county first (hold, else
  first in EU4 order).
- **`history/titles/aov_segbandal.txt`, at 1.1.1:** `de_jure_liege` links every new title to its Anbennar parent
  (`k_gor_vazumbrog` -> `e_middle_dwarovar`, new duchies -> their kingdom, top-level counties -> their reused duchy)
  and moves the Anbennar counties in the table.
- **Rulers:** new duchies in `k_seghdihr` and `k_verkal_gulan` get an elder (holds from 860.1.1, dies 1000-1010) and
  his son, holding the duchy and its new counties, `liege = k_seghdihr` / `k_verkal_gulan` (the kingdom's holder at
  the date). New counties added to a held Anbennar duchy go to that duchy's holder. Anbennar counties keep their
  holders. Everything in the unheld kingdoms stays unheld.
- **`history/provinces/aov_segbandal.txt`:** every new barony gets its kingdom hold's Anbennar culture (Gor Vazumbrog
  `titanium_dwarvish`, EU4 I14's `titanium_dwarf`; Hehodovar `pyrite_dwarvish`; Seghdihr `citrine_dwarvish`; Verkal
  Gulan `gold_dwarvish`; Gor Ozumbrog `topaz_dwarvish`) and `ancestor_worship`; holdings as Serpentreach.
- **Dynasties and characters:** `common/dynasties/aov_segbandal_dynasties.txt`, `history/characters/aov_segbandal.txt`,
  `az-<duchy>` dynasties, `race_dwarf`, names from `name_list_dwarven`, deterministic (Serpentreach's code).
- **Arms (`common/coat_of_arms/coat_of_arms/aov_segbandal.txt`), new titles only:** `k_gor_vazumbrog`, `d_vazumbrog`
  and `c_gor_vazumbrog` carry I14's flag as a textured emblem over the whole shield
  (`gfx/coat_of_arms/textured_emblems/aov_gor_vazumbrog.dds`, imported once with `eu4_import.py convert
  gfx/flags/I14.tga ... --upscale2x --mips`); other new duchies get composed dwarven arms (`DUCHY_CHARGES` per area,
  `DUCHY_PATTERNS` by key hash), as Serpentreach. Anbennar's titles keep their arms.
- **Colours, new titles only:** `k_gor_vazumbrog` takes I14's 146 160 161 (adjusted if too close to a neighbour);
  new duchies are `DUCHY_SHADES` of their kingdom's Anbennar colour (read from Anbennar's landed titles); counties
  jitter around their duchy's. Anbennar's titles keep their colours (changing them needs a landed-title override).
- **Also:** `common/province_terrain/aov_segbandal_terrain.txt`; region `world_segbandal` in
  `map_data/geographical_regions/aov_segbandal_regions.txt` (the 18 duchies); localization
  `aov_segbandal_l_english.yml` (EU4 names; `Dwarovrod | 27 |` -> `Dwarovrod 27`; area names from EU4, `|27-29|` ->
  `27-29`); `tools/data/holds.py` gains Gor Vazumbrog (4217, `c_gor_vazumbrog`, level 2, not ruined).

## §3 Look (`tools/build_map_graphics.py`)

- **Carving:** Segbandal's carve floor becomes Anbennar's range (as now) plus Segbandal's new floor from the layout;
  rock is 2608 (and any other impassable province within `CARVE_ROCK_RADIUS`). New openings ramp to the land as
  Serpentreach's corridors do; new gates join the gate list.
- **Terrain styles** (Serpentreach's `TERRAIN_STYLES`, Segbandal's `AREA_STYLES`): Steamsource `volcanic`; Deep One's
  Lair `mushroom` (moss, waterlogged); Ulagom `garnet` (red canyon stone); every other area `default`. Anbennar's
  floors keep the default style.

## §4 Order, tests, risks

- **Order:** `build_serpentreach.py` (both regions' map), `build_segbandal.py`, `build_holds.py`,
  `build_holding_models.py`, `build_map_graphics.py`. Recorded in `docs/systems/updating.md` and a new
  `docs/systems/segbandal.md`; CLAUDE.md's systems table gains a row.
- **Tests** (`tools/tests/test_segbandal.py`): `EXISTING` names match Anbennar counties; allowed-neighbour clipping on
  a synthetic map; every new county touches an EU4 neighbour; Segbandal connected; id ranges pinned; each new duchy
  lists its capital first; de jure table complete (every EU4 area's counties end in its duchy); no new key collides
  with Anbennar; Serpentreach's output unchanged apart from the shared map files; FreshnessTests entries.
- **Validation:** `python -I tools/validate.py`; `--all` grep for the new files.
- **Risks (test in game):**
  1. Top-level duchies and counties with their de jure parent set only in history: the game may reject or re-parent
     them. Fallback: wrap each in a hidden parent of ours and keep the history links.
  2. `de_jure_liege` on Anbennar counties applies in both bookmarks and the emptied Anbennar duchies vanish.
  3. Map loads with the new ids; locators sit on the floors; walls and floors look right.
