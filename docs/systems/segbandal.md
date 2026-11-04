# Segbandal

## Generated files

| File | Generator | Why |
|---|---|---|
| Segbandal's provinces in `map_data/provinces.png`, `map_data/definition.csv` and the 8 locator files | `python -I tools/build_serpentreach.py` | The Serpentreach generator draws both regions into the shared map files (`layouts`: Segbandal's ids follow Serpentreach's). See `serpentreach.md`. |
| `common/landed_titles/aov_segbandal.txt`, `history/titles/aov_segbandal.txt`, `history/provinces/aov_segbandal.txt`, `history/characters/aov_segbandal.txt`, `common/dynasties/aov_segbandal_dynasties.txt`, `common/province_terrain/aov_segbandal_terrain.txt`, `map_data/geographical_regions/aov_segbandal_regions.txt`, `localization/english/aov_segbandal_l_english.yml`, `common/coat_of_arms/coat_of_arms/aov_segbandal.txt` | `python -I tools/build_segbandal.py` | EU4 Anbennar's `middle_dwarovar_region` completed around Anbennar's `e_middle_dwarovar` from `tools/data/segbandal.py`. Rerun after `build_serpentreach.py` and after any Anbennar title, title-history or map change; then `build_rie_elves.py`, `build_holds.py`, `build_holding_models.py` and `build_map_graphics.py` (the Elven Haven buildings and the holding models list the dwarf-model provinces, which include Segbandal's). |

Imported once (no generator): `gfx/coat_of_arms/textured_emblems/aov_gor_vazumbrog.dds`, EU4 I14 "Gor Vazumbrog"'s
flag (`python -I tools/eu4_import.py convert gfx/flags/I14.tga gfx/coat_of_arms/textured_emblems/aov_gor_vazumbrog.dds --upscale2x --mips`).

## System

- Spec `docs/superpowers/specs/2026-11-03-segbandal-design.md`, plan `docs/superpowers/plans/2026-11-03-segbandal.md`.
- **What changed:** Anbennar's Segbandal had 54 provinces (roads Dwarovrod 30-44, Seghrod, four holds, Hero's Vale);
  EU4 has 57 in 18 areas. Anbennar's provinces, ids, baronies and titles stay; the 37 EU4 provinces Anbennar lacks
  (Gor Vazumbrog, Dwarovrod 25-29, 31 caverns) are traced into the impassable rock around them (province 2608) as 37
  counties with 71 provinces (ids 7068-7138), by Serpentreach's tracer with `tools/data/segbandal.py`.
- **Tracing** (`serpentreach_layout.layout(..., cfg=segbandal)`): the affine fit, smoothing and barony split are
  Serpentreach's. `EXISTING` (20 EU4 ids -> Anbennar counties, matched by name) are not traced. A new floor keeps
  `WALL_MARGIN` (4) px of rock from every province except the Anbennar provinces of its EU4 neighbours
  (`allowed_neighbours`, `clip_floor`), so a cavern opens onto the road EU4 joins it to and onto nothing else. A county
  touching none of its EU4 neighbours gets a corridor to one (`_links`); a whole piece cut off from Anbennar's
  provinces gets the shortest corridor from any of its counties to an Anbennar province they neighbour (`_piece_link`:
  today Xazor Rift -> Dwarovrod 39, joining Xazor and Ulagom). The build stops if Segbandal (new and old provinces) is
  not one piece, or if an `EXISTING` county is gone. EU4 contacts with West Dwarovar and Serpentreach
  (`NO_LINK_REGIONS`) make no opening; Segbandal has no surface openings of its own (Anbennar's gates stay its exits).
- **Duchies** (`AREA_DUCHIES`, one per EU4 area): Anbennar's `d_hehodovar`, `d_hehorod` (Dwarovrod 30-32),
  `d_seghdihr`, `d_verkal_gulan`, `d_xazorod` (Dwarovrod 38-41) and `d_gor_ozumbrog` stand for their areas; 12 new
  duchies for the rest. Anbennar's `d_seghrod`, `d_gulanrod` and `d_ozumrod` end up with no counties (their keys stay);
  `d_heros_vale` is untouched. Dwarovrod 32 moves to Hehodovar's kingdom, 35 to Seghdihr's, 38 to Gor Ozumbrog's.
- **Kingdoms**, one per hold, west to east: `k_gor_vazumbrog` (new: Vazumbrog, Dwarovrod 27-29, Misty Cave Trail),
  `k_hehodovar` (+ Dwarovrod 30-32, Deep One's Lair, Digger's Road), `k_seghdihr` (+ Dwarovrod 33-35, Steamsource,
  Stunad Kradoz, Goblin Grotto), `k_verkal_gulan` (+ Greatcavern, Xazor), `k_gor_ozumbrog` (+ Dwarovrod 38-41, Ulagom).
- **No Anbennar file is overridden:** `aov_segbandal.txt` defines every new title under three parking titles
  (`PARKING`: `e_`, `k_` and `d_aov_segbandal_parking`): `k_gor_vazumbrog` with its duchies, every other new duchy in
  the parking kingdom, and the new counties of reused Anbennar duchies (Stonewall, Easthollow, Hehogrim's Mausoleum,
  Bahged Breach) in the parking duchy. `history/titles/aov_segbandal.txt` moves them to their real parents with
  `1.1.1 = { de_jure_liege = ... }` and moves Anbennar's counties, computed from Anbennar's current titles
  (`title_parents`), so an Anbennar change is followed on the next run. The parking titles end with no de jure land
  and no holder, like Anbennar's `e_test`, so they never show and cannot be created.
- **Why parking titles:** the first build put those titles at the top level of the landed titles and relied on the
  history alone for their parents. CK3 1.19 crashed (access violation, no log line) at "Start running through history"
  on every start. No vanilla or Anbennar landed title lacks a county -> duchy -> kingdom -> empire chain in the landed
  titles, and history de jure moves come too late. `TitleTests.test_every_title_has_a_full_chain_at_load` keeps every
  new title on a full chain.
- **Rulers:** the new duchies of `k_seghdihr` and `k_verkal_gulan` with new counties (Steamsource, Stunad Kradoz,
  Goblin Grotto, Greatcavern, Xazor) get an elder (from 860.1.1, dies 1000-1010) and his son (`aov_sb_*`, dynasties
  `az-<duchy>`), who become vassals of the king from the king's first holder date in Anbennar's history (Ungrim
  921.9.24, Girud 903.4.17). Stonewall and Easthollow go to `d_seghdihr`'s holder (Ungrim). Everything new in Hehodovar,
  Gor Ozumbrog and Gor Vazumbrog stays unheld, as Anbennar leaves those holds.
- **Cultures:** new baronies and characters take their kingdom hold's culture: Gor Vazumbrog `titanium_dwarvish`
  (EU4 I14's `titanium_dwarf`), Hehodovar `pyrite_dwarvish`, Seghdihr `citrine_dwarvish`, Verkal Gulan
  `gold_dwarvish`, Gor Ozumbrog `topaz_dwarvish`; `ancestor_worship`.
- **Arms and colours, new titles only:** Gor Vazumbrog's kingdom, duchy and hold county carry I14's flag; the other
  new duchies a charge from their lore (`DUCHY_CHARGES`) on their map colour, as Serpentreach's. `k_gor_vazumbrog` is
  I14's 146 160 161; new duchies are shades of their kingdom's Anbennar colour. Anbennar's titles keep theirs.
- **Gor Vazumbrog** is a dwarven hold (`tools/data/holds.py`, level 2, not ruined); its options 16 in the hand-written
  delve and ruin pickers (`events/aov_hold_delve_events.txt`, `events/aov_hold_ruin_events.txt`,
  `common/decisions/aov_hold_decisions.txt` and their loc) were added by copying option 15.
- **Look:** Segbandal's carve (`map-graphics.md`, carved ranges) covers the new floors too; Steamsource is painted
  `volcanic`, Deep One's Lair `mushroom` (moss), Ulagom `garnet` (red canyon), the rest Serpentreach's `default`
  (`AREA_STYLES`). Preview: `art_work/segbandal_reworked_preview.png` (git-ignored).
- **Needs an in-game test:**
  1. The map loads; the new provinces show in the caverns and their locators sit on the floors.
  2. The game starts from the 1022 bookmark (the history crash is gone) and the parked titles take their de jure
     parents from history: check the de jure kingdom map mode for five Segbandal kingdoms, Gor Vazumbrog's in the
     west, and that no "Segbandal Unsorted" title shows anywhere.
  3. `d_seghrod`, `d_gulanrod` and `d_ozumrod` no longer show; Dwarovrod 32, 35 and 38 sit in their new kingdoms.
  4. Elders hold Steamsource, Stunad Kradoz, Goblin Grotto, Greatcavern and Xazor as vassals of Ungrim and Girud.
  5. Gor Vazumbrog's arms show I14's flag; the hold appears in the Delve Deeper picker for its holder.
  6. Floors and walls look right; tune `AREA_STYLES` and the carve values.
