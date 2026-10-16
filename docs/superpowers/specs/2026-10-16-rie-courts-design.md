# RiE backgrounds and royal courts for dwarves and elves (design)

Date: 2026-10-16. Status: implemented in `tools/build_rie_courts.py` (data `tools/data/rie_courts.py`).

## Goal

The character window's background picture (by realm level) and the royal court scene come from Realms in Exile:

| Who | Backgrounds (realm level) | Royal court (RiE scene culture) |
|---|---|---|
| dwarves (`aov_dwarf_clothing_gfx`) whose capital is on `dwarven_hold`, `dwarven_hold_surface` or `dwarven_road` terrain | `throneroom_dwarf_highest` (empire), `_high` (kingdom), `_mid` (duchy), `_low` (county and below) | `dwarven` (Durin's Folk hall) |
| wood elves (`aov_lasgalendrim_clothing_gfx`) | Thranduil's halls (kingdom and above), the Greenwood tree hall (below) | `moriquendi` (Lasgalen tree hall) |
| moon elves (`aov_noldor_clothing_gfx`) | `throneroom_noldor_high` (kingdom and above), `_mid` (duchy), `_low` (county and below): RiE's Lindon/Falathrim thronerooms | `noldor` (Lindon hall, 2 layouts x 3 grandeur levels) |

User choices: dwarves only in dwarven terrain (holds and dwarven roads; caverns are not listed), Lasgalendrim for wood
elves, Falathrim (RiE's Noldor thronerooms and court) for moon elves, backgrounds by realm level. RiE has only two
Greenwood pictures, so wood elves get two levels.

## Backgrounds

Scripted illustration `character_view_bg` returns its first valid entry (`_scripted_illustrations.info`); Anbennar
defines it in `gfx/interface/illustrations/scripted_illustrations/ingame.txt`. The generated override is Anbennar's file
with our `texture`/`environment` pairs inserted right before Anbennar's first throneroom
(`character_view/fp1_throneroom_nontribal.dds`), where RiE puts its race thronerooms too: death, prison, activity,
travel and camp entries above it keep winning. Each entry tests `aov_rie_court_view_<group>_<tier>_trigger`: the
character, else a non-ruling spouse, the betrothed or the host (RiE's and vanilla's pattern) holds such a court at that
tier. Pictures are copied from RiE at their paths; the Noldor and dwarf portrait environments are copied into
`gfx/portraits/environments/aov_rie_environments.txt`, the two Greenwood ones are vanilla's.

## Royal courts

A court picks a culture set (`gfx/court_scene/scene_cultures`) by trigger; vanilla writes its sets to exclude each
other, so the order is not relied on. The generated override of Anbennar's `00_default_cultures.txt` puts our three
sets first and adds `NOT = { aov_rie_court_scene_trigger = yes }` to every Anbennar set. RiE's scene files are copied
verbatim (their `culture=` names our sets), with the scene environment and court models they use (copied block by block
like the portraits; vanilla `ep1_*` props and `roco_*` effects stay vanilla's). The game's
`grandeur_levels.txt` (Anbennar ships none) is overridden with RiE's entries for the three scene cultures.

## Risks to confirm in game

1. Several RiE pictures are compressed DDS with sizes not divisible by 4 (tiger reports one); RiE ships them.
2. The court scene culture choice with our exclusions; the Noldor court's grandeur levels.
3. The dwarf court only for dwarven-terrain capitals; elsewhere dwarves keep Anbennar's court and backgrounds.
