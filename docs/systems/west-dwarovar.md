# West Dwarovar

## Generated files

| File | Generator | Why |
|---|---|---|
| West Dwarovar's provinces in `map_data/provinces.png`, `map_data/definition.csv` and the 8 locator files | `python -I tools/build_serpentreach.py` | The Serpentreach generator draws all three regions into the shared map files (`layouts`: West Dwarovar's ids follow Segbandal's). See `serpentreach.md`. |
| `common/landed_titles/aov_west_dwarovar.txt`, `history/titles/aov_west_dwarovar.txt`, `history/provinces/aov_west_dwarovar.txt`, `history/characters/aov_west_dwarovar.txt`, `common/dynasties/aov_west_dwarovar_dynasties.txt`, `common/province_terrain/aov_west_dwarovar_terrain.txt`, `map_data/geographical_regions/aov_west_dwarovar_regions.txt`, `localization/english/aov_west_dwarovar_l_english.yml`, `common/coat_of_arms/coat_of_arms/aov_west_dwarovar.txt` | `python -I tools/build_west_dwarovar.py` | EU4 Anbennar's `west_dwarovar_region` (without the Krakdhum pocket) and `serpents_vale_region` under `e_west_dwarovar`, from `tools/data/west_dwarovar.py`, with `build_serpentreach.py`'s `Realm`, `People` and renderers. Rerun after `build_serpentreach.py` and `build_segbandal.py` and after any Anbennar title, title-history or map change; then `build_rie_elves.py`, `build_holds.py`, `build_holding_models.py` and `build_map_graphics.py`. |

Imported once (no generator): `gfx/coat_of_arms/textured_emblems/aov_{amldihr,dur_vazhatun,orlazam_az_dihr,mithradhum,
er_natvir,khugdihr,haraz_orldhum,verkal_kozenad,hul_jorkad}.dds`, the flags of EU4 I01, I03, I04, I05, I06, I07, I08,
I09 and I10 (`python -I tools/eu4_import.py convert gfx/flags/<tag>.tga gfx/coat_of_arms/textured_emblems/aov_<kingdom>.dds --upscale2x --mips`).

## System

- Spec `docs/superpowers/specs/2026-11-03-west-dwarovar-design.md`, plan `docs/superpowers/plans/2026-11-03-west-dwarovar.md`.
- **Map:** the Serpentreach tracer runs a third time (`build_serpentreach.west_dwarovar_layout`) with
  `REGIONS` (both EU4 regions), `EXCLUDE_AREAS` (Krakdhum, Anvil's Horn, Dead End Tunnel: neither traced nor linked),
  `EXISTING` (Anbennar's Khugdihr, Khugscave, Outer Khugscave, Dwarovrod 1: not traced) and `avoid` (Serpentreach's
  and Segbandal's floors read as other provinces, so the new floors keep `WALL_MARGIN` from them and no corridor runs
  into them). Fit on 527 provinces, residual median 15.7 px, max 47.8. 128 counties, 245 provinces (ids 7139-7383).
- **Serpent's Vale** is surface land: a province whose EU4 terrain is no cave kind is type `surface` in
  `SURFACE_AREAS` (12 counties, 3 baronies each; the build stops on one anywhere else). Its two `dwarven_road`
  provinces (Southern and Eastern Entrance) are cave floors: Amldihr's tunnels into the Vale. Where a cave floor
  touches a surface county the layout records a **mouth** (`Layout.mouths`): Southern Entrance -> Terraceway, Eastern
  Entrance -> Hornriver and Lamb Hills, Longneck Cave (Dark Depths) -> Northvale, Orcsbreach (Dwarfbreak) -> Kheness
  Swamp, Orlazam-az-dihr -> Lamb Hills.
- **Openings** (EU4 contacts outside the regions; `NO_LINK_REGIONS` drops Serpentreach, Middle Dwarovar, the Northern
  Pass and East Deepwoods): Bladebreaker Pass -> Steelhyl (860), Dwarfhope -> Glimmerfoe (2556; EU4's Fogwood lies
  behind Glimmerfoe on the CK3 map), Hul-Jorkad -> Ijenmyfor3 (3005). Eastern Reach's neighbour (Damazgubli) is off the
  CK3 map: skipped (noted). `NO_LINK_PAIRS` drops any opening, tunnel or mouth by EU4 pair.
- **Tunnel to Segbandal:** EU4 joins Dwarovrod 24 to Dwarovrod 25 only through `map/adjacencies.csv`
  (`eu4_adjacencies`, `adjacency_links`, `LINK_TARGETS = (2885,)`, `LINK_REACH` 220, through 2426 and Segbandal's
  rock 2608). Anbennar's Bezhetsk and Khinkeion poke into the rock on the straight line, so the tunnel is routed
  around them through the rock (`_routed_corridor`, BFS keeping the corridor's clearance): 121 steps, 1,526 px. EU4's
  other tunnel to an earlier region, Gorrod 2 -> Serpentreach's Gorrod 1, is left out (spec: Serpentreach stays
  unconnected).
- **Seams:** Dwarovrod 12 and Massive Shaft are a pixel apart in EU4 and merged once scaled; `SEPARATE_NON_NEIGHBOURS`
  cuts a `WALL_MARGIN` rock seam between labels EU4 does not make neighbours (West Dwarovar only).
- **Titles:** each new kingdom's hold duchy is named like the kingdom (`HOLD_DUCHIES_NAMED_LIKE_KINGDOM`; the keys
  keep EU4's area names, e.g. `d_orldhum` "Haraz Orldhûm"). `e_west_dwarovar` (capital Amldihr, colour 60 40 80) holds eight new kingdoms in place (a full chain at
  load) and `k_aov_west_dwarovar_parking`, which holds the three new duchies of Anbennar's `k_khugdihr`
  (Dwarovrod 1-3, Fallen Asra, Snotslair). History at 1.1.1 moves `k_khugdihr` into the empire, the parked duchies
  into `k_khugdihr` and `c_dwarovrod1` into Dwarovrod 1-3; the moves are computed from Anbennar's current titles. The
  parking kingdom ends empty and unheld. Each duchy lists its capital county first (a kingdom capital, else its hold).
- **Khugdihr stays kobold:** Anbennar's four counties get no culture, faith, holder or province history; the new
  counties of `k_khugdihr` are `darkscale`/`nimrithani` and unheld (`KOBOLD_KINGDOMS`). `check_khugdihr` stops the
  build when Anbennar gives any `k_khugdihr` title a holder or adds a county under it.
- **People:** per duchy of the eight dwarven kingdoms an elder (from 860.1.1, dies 1000-1010) and his son (`aov_wd_*`,
  dynasties `aov_wd_dynasty_*` named `az-<duchy>`); the emperor holds Amldihr; each other kingdom is held by its hold
  duke under him. `silver_dwarvish` stands in for the holds' EU4 cultures (kronium, platinum, mithril, dagrite, opal,
  lead, ramsteel, sapphire), `ancestor_worship`. Vale counties: castle, city, church; terrain from `SURFACE_TERRAIN`.
- **Arms:** each kingdom, its hold duchy and hold county carry its EU4 flag on the flag's commonest colour
  (`KINGDOM_ARMS`; `k_khugdihr`, `d_khugdihr`, `c_khugdihr` I07's, Anbennar scripting none; the build stops if it
  ever does); the 30 other new duchies a charge from their lore (`DUCHY_CHARGES`).
- **Holds:** eight new dwarven holds in `tools/data/holds.py` (Amldihr level 2; Haraz Orldhûm, Mithradhûm, Er-Natvir,
  Verkal Kozenad, Hul-Jorkad, Orlazam-az-dihr, Dûr-Vazhatun level 1), options 17-24 in the hand-written pickers, copied
  from option 16 (see `dwarven-holds.md`).
- **Look** (`map-graphics.md`): `CARVED_RANGES` `c_khugdihr` carves Khugdihr's Anbennar floors and the new caves as one
  range (ground ~28,400); Serpent's Vale and the earlier regions' floors are `land` to that carve (never walled; floors
  ramp to them over `CARVE_RAMP`). The Vale is painted by terrain (`SURFACE_MATERIALS`, feathered over 4 px).
  Westnest, Eastnest and Zokkorna are `mushroom` (moss). Every opening and Vale mouth gets an Erebor gate (turn
  pinned to 0); the tunnel gets none. The Vale is still 2426 on Anbennar's map, so the gate transplant treats it as
  range: `build_heightmap` restores its heights after the transplant (`vale_pixels`, `restore_land`) and drops gate
  pieces within `PIECE_FLOOR_CLEARANCE` of it. `SURROUND_BOX` starts at mask row 300, clearing the fog off Dûr-Vazhatun;
  Krakdhum stays fogged.
- **Needs an in-game test:**
  1. The map loads with the new ids; locators sit on the floors and in the Vale.
  2. The de jure map mode shows `e_west_dwarovar` with nine kingdoms (Khugdihr included) and no "West Dwarovar
     Unsorted"; Khugdihr has left `e_castanor` in both bookmarks.
  3. Khugdihr is kobold and unheld; the eight dwarven kingdoms have their elders.
  4. Cave floors versus the Vale: the floors stand ~28,400 and the Vale ~5,000-12,000, so the mouths ramp steeply
     over 12 px (risk: a cliff). Fixes: a longer `CARVE_RAMP` for this range, or a fixed ground height.
  5. Gates face the right way (out of the caves; into the Vale at the mouths). A mouth gate's direction is one of
     the four axes (its `start` is a 4-neighbour of the mouth), and its cone stops at the Vale's edge.
  6. Dûr-Vazhatun is out of the fog; the tunnel from Dwarovrod 24 reads as a tunnel into Segbandal.
