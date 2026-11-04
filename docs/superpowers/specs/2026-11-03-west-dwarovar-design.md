# West Dwarovar design

EU4 Anbennar's `west_dwarovar_region` (without the Krakdhum pocket) and `serpents_vale_region` added to the CK3 map
under one placeholder empire, `e_west_dwarovar`. The caves are traced and carved into the Serpentspine block (province
2426) like Serpentreach; Serpent's Vale is drawn as ordinary surface land in the low basin Anbennar's heightmap already
has there, with no carve.

## Intent

- **User asked:** implement the rest of the western Serpentspine that is on the map, besides Krakdhumvror, with
  Serpentreach's carve; one empire title holds all of it in this first iteration. Planning only for now.
- **User chose:**
  - *Scope:* West Dwarovar and Serpent's Vale. The Vale is **not carved**: its people live above ground. The Northern
    Pass (Logr valley, 2 of its 10 areas already Anbennar's `k_cagodor` in `e_gerudia`) waits for a later iteration.
  - *Fogged edge:* leave out the Krakdhum pocket (Krakdhum, Anvil's Horn, Dead End Tunnel: they reach the rest only
    through Krakdhum or the Northern Pass, and sit under the map-edge fog). Keep Dûr-Vazhatun and pull the fog back
    off it.
  - *Khugdihr:* Anbennar's `k_khugdihr` (de jure `e_castanor`) moves into the new empire by history. Its darkscale
    kobolds stay (no dwarf elder there), and Khugdihr is carved like the rest.
  - *Rulers:* dwarf elders as in Serpentreach (an elder and his son per duchy, an emperor on the capital hold).
- **Success:** the game loads; the West Dwarovar's caves are carved, flat-floored halls joined to Khugdihr, to the
  surface by gated corridors, to Segbandal by the Dwarovrod, and to Serpent's Vale by gates at the cave mouths; the Vale
  is open farmland and hills; every EU4 area is a duchy under its hold's kingdom under `e_west_dwarovar`; no Anbennar
  file is overridden for titles; the generators rebuild everything after an Anbennar update.

## What is on the map today

Measured with an affine fit like Serpentreach's (508 provinces both maps share, median error 16 px, max 48):

| EU4 | Lands on | Notes |
|---|---|---|
| `khugdihr_area` (Khugdihr, Khugscave, Outer Khugscave), Dwarovrod 1 | Anbennar's `k_khugdihr` (`c_khugdihr`, `c_khugscave`, `c_outerkhugscave`, `c_dwarovrod1`) | equivalents, not traced |
| the other 34 West Dwarovar areas | impassable 2426 (Big Waste) | spills: Dwarovrod 2-3 onto Khugdihr's baronies, Fallen Asra onto Angelsight and Steelhyl, Snotslair onto Faenrak, three caves onto Deepwoods Wasteland, Jorkad onto Ijenmyfor3 (all clipped) |
| `serpents_vale_region` (4 areas, 14 provinces) | 2426, in a basin Anbennar's heightmap already has (heights ~5,000-12,000; the holds around it stand at ~38,000-56,000) | |
| Krakdhum pocket (`krakdhum_area`, `anvils_horn_area`, `dead_end_tunnel_area`) | 2426 under the surround fog | left out |

Nothing traced comes within 6 px of Serpentreach's or Segbandal's floors. EU4 1444 has every hold fallen to
greenskins; the CK3 1022 start keeps them dwarven, as Serpentreach does.

**Counts.** 35 West Dwarovar areas (33 traced in full, `khugdihr_area` not traced, `dwarovrod_1_3_area` traced but for
Dwarovrod 1) and 4 Vale areas. About 110 new cave counties and 14 Vale counties; baronies as Serpentreach for caves
(hold 4, cavern 2, road 1) and 3 per Vale county: about 250 new provinces, ids from 7139 (after Segbandal's 7138).

## §1 Map (`tools/serpentreach_layout.py`, data `tools/data/west_dwarovar.py`)

The Serpentreach tracer runs a third time, with a new data module, as Segbandal's does. New tracer options, each off by
default so Serpentreach and Segbandal build byte-identical:

- **Several regions:** `REGIONS = ("west_dwarovar_region", "serpents_vale_region")` in place of `REGION`
  (`REGION` still accepted). `AREA_ORDER` and the kingdom table list exactly the regions' areas less `EXCLUDE_AREAS`.
- **Excluded areas:** `EXCLUDE_AREAS = ("krakdhum_area", "anvils_horn_area", "dead_end_tunnel_area")`. Their provinces
  are neither traced nor linked; EU4 contacts with them make no opening.
- **Surface provinces:** a province whose EU4 terrain override is none of `BARONIES`' kinds (holds, caverns, roads) is
  *surface* when its area is in `SURFACE_AREAS` (the Vale's four); the build stops on such a province anywhere else.
  Surface counties are traced, smoothed and split like the rest (`SURFACE_BARONIES` 3) but are never carved or walled,
  and they keep `WALL_MARGIN` only from provinces that are not their EU4 neighbours, like floors. The Vale's two
  `dwarven_road` provinces (Southern Entrance, Eastern Entrance) are ordinary cave floors: the Vale's tunnels.
- **Vale gates:** where a cave floor touches a surface province the contact is a *mouth*: the floor ramps to the
  surface height there (as an opening corridor does) and `build_map_graphics.py` puts a gate at it, facing the Vale.
  This gives Amldihr, which EU4 joins to the rest only through the Vale, its gates into the Vale.
- **Avoid earlier floors:** `layout(..., avoid=...)` takes the pixels of the layouts already drawn (Serpentreach's;
  Segbandal's) and keeps `WALL_MARGIN` from them like any other province. Today nothing comes close; the guard stops a
  later fit change from merging two regions' floors.
- **Equivalents:** `EXISTING = {2863: "c_khugdihr", 2896: "c_khugscave", 2897: "c_outerkhugscave", 2864:
  "c_dwarovrod1"}`, as Segbandal's.
- **Tunnel links from `adjacencies.csv`:** EU4 joins Dwarovrod 24 (2884) to Dwarovrod 25 (2885, Segbandal) only by an
  adjacency, not by touching pixels. `ADJACENCY_LINKS` reads EU4's `map/adjacencies.csv` for pairs with one end in the
  region and the other in an already drawn layout or an `EXISTING`/Anbennar county, and cuts a corridor `OPENING_WIDTH`
  wide from the new county to that province, through 2426 and Segbandal's rock 2608 (`LINK_CUT_THROUGH = (2608,)`).
  Measured: Dwarovrod 24 lands at (3371, 1972), Segbandal's `c_dwarovrod_25` provinces 7068/7069 at about (3490, 1805):
  ~170 px, so `LINK_REACH` is 220. Segbandal's `NO_LINK_REGIONS` keeps West Dwarovar (the link is made from this side).
- **Openings** (EU4 contacts with land outside the regions; `NO_LINK_REGIONS = ("serpentreach_region",
  "middle_dwarovar_region", "northern_pass_region", "east_deepwoods_region")`):

  | County (EU4 area) | EU4 neighbour | CK3 target |
  |---|---|---|
  | Fallen Asra | Steelhyl (860) | Steelhyl, same id |
  | Chainlink Mines | Fogwood (863) | Fogwood, same id |
  | Jorkad Junction | Ijenmyfor | nearest land (CK3 splits it as Ijenmyfor2/3) |
  | Eastnest | Damazgubli (West Forbidden Plains) | nearest land, else skipped (noted) |

  **No Deepwoods openings (user choice):** EU4's only East Deepwoods contacts, Azmak Quarry to Vyr Ghtarë and Kikkimig
  Outlet to Vyr Drava, make no opening (`east_deepwoods_region` in `NO_LINK_REGIONS`), so `OPENING_CUT_THROUGH` is
  empty (Serpentreach's Deepwoods Wasteland cut is not needed). Khugdihr's own exits (Dwarfvord and Huuriven, see
  Connections) are Anbennar's and unchanged. A target the build picks badly gets an `OPENING_TARGETS` entry.
- **Ids and outputs:** `build_serpentreach.layouts` returns three layouts; West Dwarovar's ids follow Segbandal's last
  and its colours avoid both. `AREA_ORDER` is fixed (west to east, as in the kingdom table below), so regrouping
  kingdoms keeps ids. `build_serpentreach.py` draws all three into `provinces.png`, `definition.csv` and the 8 locator
  files it already writes.
- **Build stops on:** everything Serpentreach's and Segbandal's tracer already checks (pixel not on 2426, barony under
  `MIN_BARONY_PX`, floor falling apart, floor touching a non-neighbour, lost `EXISTING` county); a surface province
  outside `SURFACE_AREAS`; an `EXCLUDE_AREAS` key not in the regions; an adjacency link with no corridor within
  `LINK_REACH`.

### Connections

Where the new caves meet anything else, as measured on the fit (a `px` figure is the distance from the EU4 contact to
the target on the CK3 map; corridors reach at most `OPENING_REACH` 160 px). Any of these can be dropped with
`NO_LINK_PAIRS` (EU4 province pairs) in the data module.

| Kind | From (EU4 area) | To (CK3) | How the target is found |
|---|---|---|---|
| Already in Anbennar | Khugdihr | Dwarfvord (2416, `c_khugsroad`, Castanor) | Anbennar's own border |
| Already in Anbennar | Khugdihr | Huuriven (6920, `c_cutback_valley`, `k_cagodor`, Gerudia) | Anbennar's own border |
| Surface opening | Bladebreaker Pass (Fallen Asra) | Steelhyl (860, `c_steelhyl`) | same id, ~1 px |
| Surface opening | Dwarfhope (Chainlink Mines) | Fogwood (863, `c_fogwood`) | same id, ~29 px |
| Surface opening | Hul-Jorkad (Jorkad Junction) | Ijenmyfor3 (3005, `c_ijenmyfor`) | nearest land to EU4's Ijenmyfor, ~3 px |
| None (user choice) | Azmak Quarry (Azmak) | (would have been Deepwoods120, `c_shadow_grove_1_2`) | `east_deepwoods_region` in `NO_LINK_REGIONS` |
| None (user choice) | Kikkimig Outlet (Zokkorna Caverns) | (would have been Deepwoods, `c_flower_grove_1_1`) | `east_deepwoods_region` in `NO_LINK_REGIONS` |
| None | Eastern Reach (Eastnest) | (EU4's Damazgubli, West Forbidden Plains, is off the CK3 map) | nearest land is over 200 px away: skipped |
| Tunnel to Segbandal | Dwarovrod 24 (Dwarovrod 21-24) | Dwarovrod 25 (7068/7069, `c_dwarovrod_25`) | EU4 `adjacencies.csv`, ~170 px |
| Vale mouths (internal) | Amldihr | Royal Terrace and Castle Hill areas | EU4 borders |
| Vale mouths (internal) | Dark Depths; Dwarfbreak; Orlazam | Castle Hill; Assembly Terrace; Common Terrace areas | EU4 borders |

Not connected: Serpentreach (EU4 has no border with it); the Northern Pass (Vazhatun to Tanning Valley, Castle Hill to
Copperwood and Upper Logr; left for the Northern Pass iteration); the excluded Krakdhum pocket.

## §2 Look (`tools/build_map_graphics.py`)

- **Carve, Khugdihr included:** the West Dwarovar is carved as Segbandal is, by `tools/carved_ranges.py`:
  `CARVED_RANGES` gains `c_khugdihr`, whose range is Anbennar's Khugdihr (`c_khugdihr`, `c_dwarovrod1`, `c_khugscave`,
  `c_outerkhugscave`, their Anbennar shapes) plus the West Dwarovar's new cave floors from the layout. The rock is 2426
  within `CARVE_ROCK_RADIUS`. One ground height for the whole range, the median of passable land within
  `CARVE_GROUND_RADIUS` of the floor (around Khugdihr and the openings; the Vale is still 2426 in Anbennar's map, so it
  does not count); terraces, walls, rim and fade as Serpentreach. Floors ramp (`CARVE_RAMP`) to the land's height
  wherever they touch passable land: Khugdihr's existing exits, the opening corridors' mouths, and the Vale, which the
  ramp must treat as land although it is new. Khugdihr's floor takes the `default` style. Any gate the map build
  already puts on Khugdihr's exits stays; its mountain pieces within `PIECE_FLOOR_CLEARANCE` of the floor are dropped,
  as for Segbandal.
- **Vale:** heights untouched. Each Vale county is painted at full weight with the material of its CK3 terrain
  (`farmlands` `farmland_01`, `plains` `plains_01`, `hills` `hills_01`, `wetlands` `wetlands_02`; all Anbennar
  materials), blended into the existing paint over 4 px at the Vale's edge.
- **Cave styles** (`AREA_STYLES`, Serpentreach's `TERRAIN_STYLES`): Westnest, Eastnest and Zokkorna Caverns
  `mushroom` (moss); every other area `default` (tiled roads and holds, granite caves, `rock_13_05_10` walls).
- **Gates:** every opening, the Dwarovrod 24-25 link's ends excluded, and every Vale mouth gets RiE's Erebor gate, as
  Serpentreach's (`serpentreach_sites`: turn pinned to 0, mountain pieces on the floor dropped). The gate notes list
  them.
- **Surround fog:** Dûr-Vazhatun sits at mask row ~397, just above `SURROUND_BOX`'s top edge (row 400). The top edge
  moves to 300 so the pull-back covers Vazhatun and Dagrinrod 16-17; Krakdhum (mask row ~185) stays fogged. A test
  checks the hold's mask pixel is clear and Krakdhum's is not.
- **Holding models:** every new cave province is dwarven terrain, so `build_holding_models.dwarf_model_provinces`
  picks it up from this mod's province terrain (rerun `build_holding_models.py`). The Vale keeps the normal models.

## §3 Titles, history and people (new `tools/build_west_dwarovar.py`)

**Empire:** `e_west_dwarovar` "West Dwarovar", capital `c_amldihr`, colour Amldihr's EU4 purple (60 40 80), lightened
if it merges with a neighbour on the map.

**Kingdoms**, one per EU4 hold, each a contiguous run of areas (checked by test). Duchies are one per EU4 area; the
hold's duchy is named like the kingdom and listed first:

| Kingdom | EU4 tag, colour | Areas (hold's first) |
|---|---|---|
| `k_khugdihr` (Anbennar's, moved in) | I07, Anbennar's colour kept | `khugdihr` (Anbennar's `d_khugdihr`), `dwarovrod_1_3` (gains `c_dwarovrod1`), `fallen_asra`, `snotslair` |
| `k_haraz_orldhum` | I08, 74 80 97 | `orldhum`, `dwarovrod_4_6`, `dwarfbreak`, `dark_depths`, `chainlink_mines` |
| `k_mithradhum` | I05, 81 231 213 | `mithradhum`, `dwarovrod_7_9`, `dwarovrod_10_12`, `riftway` |
| `k_er_natvir` | I06, 147 191 155 | `railyard`, `railyard_exchange`, `dagrite_depths`, `goblins_bypass`, `skulkers_lair` |
| `k_verkal_kozenad` | I09, 255 228 216 | `stunad_kozenad`, `dwarovrod_15_17`, `zokkorna_caverns`, `travelers_refuge`, `westnest`, `eastnest` |
| `k_hul_jorkad` | I10, 160 114 158 | `jorkad_junction`, `azmak`, `dwarovrod_21_24` |
| `k_orlazam_az_dihr` | I04, 74 111 121 | `orlazam`, `dagrinrod_4_6`, `dagrinrod_7_9`, `broken_dagger_pass`, `old_dagrinrod` |
| `k_dur_vazhatun` | I03, 0 25 119 | `vazhatun`, `dagrinrod_13_15` |
| `k_amldihr` | I01, 60 40 80 | `amldihr`, `royal_terrace`, `common_terrace`, `assembly_terrace`, `castle_hill` |

Kingdom colours that merge with a neighbour are shifted as Serpentreach shifted Arg-Ôrdstun's; duchies are
`DUCHY_SHADES` of their kingdom's colour, counties jitter around their duchy's.

- **Landed titles (`common/landed_titles/aov_west_dwarovar.txt`):** `e_west_dwarovar` holds its eight new kingdoms
  with their duchies and counties in place (a full chain, as Serpentreach). Only the three new duchies that join
  Anbennar's `k_khugdihr` (`d_dwarovrod_1_3`, `d_fallen_asra`, `d_snotslair`) are parked, in
  `k_aov_west_dwarovar_parking` inside `e_west_dwarovar`, so each title has a full chain at load (the Segbandal crash
  lesson); the parking kingdom ends with no de jure land and no holder. Keys free today (checked: `e_west_dwarovar` and
  the eight kingdoms); a key Anbennar already has stops the build. Each duchy lists its capital county (the hold, else
  first in EU4 order) first.
- **History (`history/titles/aov_west_dwarovar.txt`, at 1.1.1):** `de_jure_liege` puts `k_khugdihr` under
  `e_west_dwarovar`, the three parked duchies under `k_khugdihr` and `c_dwarovrod1` under `d_dwarovrod_1_3`. Parents of Anbennar titles are read from Anbennar's current titles, so an
  Anbennar change is followed on the next run.
- **Rulers:** per duchy an elder (holds from 860.1.1, dies 1000-1010) and his son, as Serpentreach. The emperor holds
  `k_amldihr` and `d_amldihr`; each other kingdom is held by its hold duchy's lord, the emperor's vassal; the other dukes
  are their king's vassals. **Khugdihr's kingdom stays kobold:** Anbennar's Khugdihr is darkscale kobold land
  (`culture = darkscale`, `religion = nimrithani` on all its baronies, no holder, a Nimrithan holy site), and it stays
  exactly so. `k_khugdihr` gets no elder; its new counties (Dwarovrod 2-3, Fallen Asra, Snotslair) get `darkscale` and
  `nimrithani` too (EU4 1444 has darkscale kobolds in Fallen Asra's Everwarren) and stay unheld like Khugdihr's. The
  build writes no province or title history for Anbennar's four Khugdihr counties beyond the de jure moves.
- **People:** dwarves as Serpentreach (`race_dwarf`, `name_list_dwarven`, `ancestor_worship`, `az-<duchy>`
  dynasties) in the eight dwarven kingdoms. CK3 has none of their holds' EU4
  cultures (kronium, platinum, mithril, dagrite, opal, lead, ramsteel, sapphire dwarves), so this iteration gives their
  kingdoms `silver_dwarvish` (EU4's dwarves of the fallen west) as a placeholder; the eight cultures are a follow-up
  spec like Serpentreach's cultures draft. The Vale is Amldihr's dwarves farming above ground (EU4's 1444 Mossmouth
  ogres have no CK3 culture).
- **Provinces (`history/provinces/aov_west_dwarovar.txt`):** culture and religion as above; cave holdings as
  Serpentreach's `HOLDINGS`; Vale counties castle, city, church.
- **Terrain (`common/province_terrain/aov_west_dwarovar_terrain.txt`):** caves by EU4 terrain as Serpentreach. Vale
  (`SURFACE_TERRAIN`): Royal, Common and Assembly Terrace `farmlands`; Porgir's Valley, Serpent's Vale, Terraceway,
  Hornriver `plains`; Lamb Hills, Kingsrock Hill, Northvale, Verkal Hul `hills`; Kheness Swamp `wetlands`.
- **Arms (`common/coat_of_arms/coat_of_arms/aov_west_dwarovar.txt`):** each new kingdom, its hold duchy and hold
  county carry its EU4 flag (I01, I03-I06, I08-I10) as a textured emblem over the whole shield, imported once with
  `python -I tools/eu4_import.py convert gfx/flags/<tag>.tga gfx/coat_of_arms/textured_emblems/aov_<kingdom>.dds
  --upscale2x --mips`; the build stops when one is missing. Anbennar scripts no arms for Khugdihr, so `k_khugdihr`,
  `d_khugdihr` and `c_khugdihr` get I07's flag the same way (as Segbandal did for Hehodovar); the build stops if
  Anbennar ever scripts arms for them. The other new duchies get one dwarven charge each on their map colour (`DUCHY_CHARGES`, `DUCHY_PATTERNS` by key hash),
  generic game and Anbennar emblems only, picked per area from its EU4 lore in the implementation plan. The empire gets
  generated arms (EU4 has no West Dwarovar tag).
- **Also:** region `world_west_dwarovar` in `map_data/geographical_regions/aov_west_dwarovar_regions.txt` (the nine
  kingdoms); localization `aov_west_dwarovar_l_english.yml` (EU4 names, `Dwarovrod | 2 |` -> `Dwarovrod 2`, area
  names from EU4); `tools/data/holds.py` gains the eight new holds, none ruined: Amldihr (4119, level 2, the old
  capital), Haraz Orldhûm (2868), Mithradhûm (4236), Er-Natvir (2931), Verkal Kozenad (4056), Hul-Jorkad (2963),
  Orlazam-az-dihr (4147) and Dûr-Vazhatun (4020) at level 1 (EU4 terrain: the first five `dwarven_hold`, the last three
  `dwarven_hold_surface`). Khugdihr stays as it is in the data (level 1, `ruined=True`: a hold the kobolds took). The Delve Deeper and ruin pickers get eight options copied from the last one, as Segbandal added
  Gor Vazumbrog's.

## §4 Order, tests, risks

- **Order:** `build_serpentreach.py` (all three regions' map), `build_segbandal.py`, `build_west_dwarovar.py`,
  `build_rie_elves.py`, `build_holds.py`, `build_holding_models.py`, `build_map_graphics.py`. Recorded in
  `docs/systems/updating.md` and a new `docs/systems/west-dwarovar.md`; CLAUDE.md's systems table gains a row.
- **Tests** (`tools/tests/test_west_dwarovar.py`, plus the tracer's tests):
  - Serpentreach's and Segbandal's layouts are unchanged by the new tracer options (ids, pixels, notes).
  - `EXISTING` counties exist in Anbennar; `EXCLUDE_AREAS` and `SURFACE_AREAS` name real areas; kingdoms list every
    kept area once and each kingdom is contiguous in EU4.
  - The West Dwarovar is one connected piece with Khugdihr; the Dwarovrod 24-25 link reaches Segbandal; no floor
    touches Serpentreach's or Segbandal's.
  - Surface provinces are never carved (their heights equal the input's) and every Vale-cave contact has a gate.
  - Khugdihr's floor is carved with the new floors; the build writes no culture, faith or holder for Anbennar's four
    Khugdihr counties, and every new county of `k_khugdihr` is `darkscale`/`nimrithani` and unheld.
  - The connections table holds: each opening reaches its listed target, Eastnest's is skipped, no new floor touches
    a Deepwoods province, and `NO_LINK_PAIRS` removes a link when set.
  - Id range pinned; each duchy lists its capital first; every title has a full chain at load; de jure table complete.
  - The surround mask is clear at Dûr-Vazhatun and fogged at Krakdhum.
  - `FreshnessTests` entries for the new files.
- **Validation:** `python -I tools/validate.py`; grep `--all` for the new files.
- **Risks (test in game):**
  1. ~250 more provinces in the shared map files: the map loads, locators sit on the floors and on the Vale.
  2. The cave floors' single ground height: Khugdihr stands ~50,000 after the raise and the outer land lower; the
     median may put floors well above or below the Vale. Tune `TERRACE`/ramp length; fallback, a fixed
     `GROUND_HEIGHT` for this region.
  3. Vale mouths ramp from the cave floor to the basin (~5,000-12,000); a steep ramp may look like a cliff. Lengthen
     the ramp or lower the floors near the Vale.
  4. The parked titles take their parents from history, and Khugdihr leaves `e_castanor` in both bookmarks.
  5. The Vale reads as a valley in its basin with the new paint; the Erebor gates face into it.
